"""Command-line interface.

Example:
    hipaa-audit samples/lakeside_family_clinic_access_log.csv --workforce samples/lakeside_family_clinic_workforce.csv \
        --patients samples/lakeside_family_clinic_patients.csv --org "Lakeside Family Clinic"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .engine import SEV, DataError, load_config, load_files, review
from .reporting import WRITERS


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="hipaa-audit", description="Review EHR access logs for suspicious access to patient records.")
    p.add_argument("log", help="Access log CSV")
    p.add_argument("--workforce", required=True, help="Workforce roster CSV")
    p.add_argument("--patients", required=True, help="Patient roster CSV")
    p.add_argument("--org", help="Organization name for the report")
    p.add_argument("--format", nargs="+", choices=sorted(WRITERS), default=["html", "csv"])
    p.add_argument("--out", default="reports", help="Output directory (default: reports)")
    p.add_argument("--config", help="JSON file overriding organization-defined parameters")
    p.add_argument("--fail-on", choices=SEV, help="Exit with code 2 if any flag at or above this severity exists")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        events, users, patients = load_files(args.log, args.workforce, args.patients)
        r = review(events, users, patients, args.org or Path(args.log).stem.replace("_", " "), load_config(args.config))
    except (OSError, DataError, ValueError) as exc:
        print(f"Could not read input: {exc}", file=sys.stderr)
        return 1
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stem = Path(args.log).stem
    for fmt in args.format:
        path = out / f"{stem}.{fmt}"
        path.write_text(WRITERS[fmt](r), encoding="utf-8")
        print(f"Wrote {path}")
    c = r.counts()
    print(f"\n{r.organization} | {r.period_start} to {r.period_end} | {r.record_accesses} record accesses by {r.users_seen} accounts")
    s = c["by_severity"]
    print(f"Flags: {c['flags']} (critical {s['critical']}, high {s['high']}, medium {s['medium']}, low {s['low']}) | "
          f"accounts to review {c['users_flagged']}")
    for u in r.users[:5]:
        print(f"  {u.worst:<9} {u.user:<12} {u.role:<18} {u.flags} flag(s): {', '.join(u.rules)}")
    if args.fail_on and any(SEV.index(f.severity) <= SEV.index(args.fail_on) for f in r.flags):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
