"""Review EHR access logs for suspicious access to patient records."""

from __future__ import annotations

import csv
import io
import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DATA = Path(__file__).parent / "data"
SEV = ["critical", "high", "medium", "low"]
WEIGHT = {"critical": 10, "high": 6, "medium": 3, "low": 1}
RECORD_ACTIONS = {"view", "edit", "print", "export"}
ACTIONS = RECORD_ACTIONS | {"login_failed", "login"}
_T = {"true", "yes", "y", "1"}


class DataError(ValueError):
    """Raised when an input file cannot be read."""


def load_config(path: str | Path | None = None) -> dict:
    c = json.loads((DATA / "config.json").read_text(encoding="utf-8"))
    if path:
        c.update(json.loads(Path(path).read_text(encoding="utf-8")))
    return c


def _rules() -> dict[str, dict]:
    return {r["id"]: r for r in json.loads((DATA / "rules.json").read_text(encoding="utf-8"))["rules"]}


def _rows(text: str, required: list[str], label: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
    cols = [(c or "").strip().lower() for c in (reader.fieldnames or [])]
    missing = [c for c in required if c not in cols]
    if missing:
        raise DataError(f"The {label} file is missing required column(s): {', '.join(missing)}.")
    out = []
    for raw in reader:
        r = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
        if any(r.values()):
            out.append(r)
    return out


@dataclass
class Event:
    when: datetime
    user: str
    role: str
    patient: str
    action: str
    break_glass: bool


def parse_log(text: str) -> list[Event]:
    events = []
    for i, r in enumerate(_rows(text, ["timestamp", "user", "action"], "access log"), start=2):
        try:
            when = datetime.fromisoformat(r["timestamp"].replace("Z", ""))
        except ValueError as exc:
            raise DataError(f"Access log row {i}: timestamp must look like 2026-09-21 14:05, got '{r['timestamp']}'.") from exc
        action = r["action"].lower()
        if action not in ACTIONS:
            raise DataError(f"Access log row {i}: action must be one of {', '.join(sorted(ACTIONS))}, got '{action}'.")
        if action in RECORD_ACTIONS and not r.get("patient_id"):
            raise DataError(f"Access log row {i}: a '{action}' action needs a patient_id.")
        events.append(Event(when, r["user"].lower(), r.get("role", "").lower(), r.get("patient_id", ""), action,
                            r.get("break_glass", "").lower() in _T))
    if not events:
        raise DataError("The access log has a header but no rows.")
    return sorted(events, key=lambda e: e.when)


def parse_users(text: str) -> dict[str, dict]:
    users = {}
    for i, r in enumerate(_rows(text, ["user", "role", "status"], "workforce"), start=2):
        term = r.get("termination_date", "")
        try:
            r["termination_date"] = date.fromisoformat(term) if term else None
        except ValueError as exc:
            raise DataError(f"Workforce row {i}: termination_date must look like 2026-09-20, got '{term}'.") from exc
        r["user"] = r["user"].lower()
        r["role"] = r["role"].lower()
        r["status"] = r["status"].lower()
        users[r["user"]] = r
    return users


def parse_patients(text: str) -> dict[str, dict]:
    patients = {}
    for r in _rows(text, ["patient_id"], "patients"):
        r["care_team"] = {u.strip().lower() for u in r.get("care_team", "").split(";") if u.strip()}
        r["employee_user"] = r.get("employee_user", "").lower()
        r["high_profile"] = r.get("high_profile", "").lower() in _T
        patients[r["patient_id"]] = r
    return patients


def load_files(log: str | Path, users: str | Path, patients: str | Path):
    rd = lambda p: Path(p).read_text(encoding="utf-8-sig")  # noqa: E731
    return parse_log(rd(log)), parse_users(rd(users)), parse_patients(rd(patients))


@dataclass
class Flag:
    rule_id: str
    title: str
    severity: str
    when: str
    user: str
    patient: str
    detail: str
    hipaa: list[str]
    controls: list[str]
    review: str


@dataclass
class UserSummary:
    user: str
    name: str
    role: str
    flags: int
    risk_points: int
    worst: str
    rules: list[str] = field(default_factory=list)


@dataclass
class Result:
    organization: str
    period_start: str
    period_end: str
    generated_at: str
    tool_version: str
    events: int
    record_accesses: int
    users_seen: int
    patients_seen: int
    flags: list[Flag]
    users: list[UserSummary]

    def counts(self) -> dict[str, Any]:
        by_sev = {s: 0 for s in SEV}
        by_rule: dict[str, int] = defaultdict(int)
        for f in self.flags:
            by_sev[f.severity] += 1
            by_rule[f.rule_id] += 1
        return {"flags": len(self.flags), "by_severity": by_sev, "by_rule": dict(by_rule),
                "users_flagged": sum(1 for u in self.users if u.flags),
                "patients_affected": len({f.patient for f in self.flags if f.patient})}

    def by_day(self) -> dict[str, list[Flag]]:
        out: dict[str, list[Flag]] = defaultdict(list)
        for f in sorted(self.flags, key=lambda f: f.when):
            out[f.when[:10]].append(f)
        return dict(out)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["counts"] = self.counts()
        return d


def _is_generic(user: str, cfg: dict) -> bool:
    base = "".join(ch for ch in user if ch.isalpha())
    return base in cfg["generic_account_names"]


def review(events: list[Event], users: dict[str, dict], patients: dict[str, dict], organization: str = "Unnamed organization",
           config: dict | None = None) -> Result:
    from . import __version__

    cfg = config or load_config()
    rules = _rules()
    flags: list[Flag] = []
    start_h, end_h = cfg["business_hours"]

    def flag(rid: str, when: datetime | date | None, user: str, patient: str, detail: str) -> None:
        r = rules[rid]
        stamp = when.strftime("%Y-%m-%d %H:%M") if isinstance(when, datetime) else (when.isoformat() if when else "")
        flags.append(Flag(rid, r["title"], r["severity"], stamp, user, patient, detail, r["hipaa"], r["controls"], r["review"]))

    seen_once: set[tuple] = set()
    for e in events:
        if e.action not in RECORD_ACTIONS:
            continue
        u = users.get(e.user)
        role = (u or {}).get("role") or e.role
        p = patients.get(e.patient, {})
        on_team = e.user in p.get("care_team", set())
        same_dept = bool(u and p.get("department") and u.get("department") == p.get("department"))

        if u is None or _is_generic(e.user, cfg):
            key = ("HA-10", e.user)
            if key not in seen_once:
                seen_once.add(key)
                n = sum(1 for x in events if x.user == e.user and x.action in RECORD_ACTIONS)
                why = "is not on the workforce roster" if u is None else "is a shared or generic login"
                flag("HA-10", e.when, e.user, "", f"Account '{e.user}' {why}; it accessed records {n} time(s) in this period.")
            continue
        term = u.get("termination_date")
        if term and e.when.date() > term:
            flag("HA-05", e.when, e.user, e.patient, f"{e.action.title()} on {e.when:%Y-%m-%d} after termination on {term}.")
            continue
        if e.break_glass:
            flag("HA-09", e.when, e.user, e.patient, f"Emergency override used to {e.action} this record.")
            continue
        if role in cfg["business_hours_roles"] and not (start_h <= e.when.hour < end_h and e.when.weekday() < 5):
            flag("HA-06", e.when, e.user, e.patient, f"{role.replace('_', ' ').title()} account active at {e.when:%a %H:%M}.")
        if on_team:
            continue
        emp = p.get("employee_user")
        if emp and emp != e.user:
            flag("HA-03", e.when, e.user, e.patient, f"Opened the record of coworker '{emp}' without being on their care team.")
        elif u.get("household_id") and u.get("household_id") == p.get("household_id"):
            flag("HA-02", e.when, e.user, e.patient, "User and patient share a household or address on file.")
        elif u.get("last_name") and u["last_name"].lower() == p.get("last_name", "").lower():
            flag("HA-02", e.when, e.user, e.patient, f"User and patient share the last name '{p.get('last_name')}'.")
        elif p.get("high_profile"):
            flag("HA-04", e.when, e.user, e.patient, "High-profile record opened by someone outside the care team.")
        elif role in cfg["clinical_roles"] and not same_dept:
            flag("HA-01", e.when, e.user, e.patient,
                 f"{role.replace('_', ' ').title()} from {u.get('department') or 'another unit'} opened a patient assigned to "
                 f"{p.get('department') or 'another unit'}.")

    by_user: dict[str, list[Event]] = defaultdict(list)
    for e in events:
        by_user[e.user].append(e)
    for user, evs in by_user.items():
        recs = [e for e in evs if e.action in RECORD_ACTIONS]
        # Bulk viewing: distinct patients in any 60-minute window.
        flagged_days = set()
        j = 0
        for i, e in enumerate(recs):
            while recs[j].when < e.when - timedelta(hours=1):
                j += 1
            distinct = {x.patient for x in recs[j:i + 1]}
            if len(distinct) > cfg["bulk_distinct_patients_per_hour"] and e.when.date() not in flagged_days:
                flagged_days.add(e.when.date())
                flag("HA-07", e.when, user, "", f"{len(distinct)} different patients opened between "
                     f"{recs[j].when:%H:%M} and {e.when:%H:%M} (threshold {cfg['bulk_distinct_patients_per_hour']}).")
        per_day: dict[date, int] = defaultdict(int)
        for e in recs:
            if e.action in ("print", "export"):
                per_day[e.when.date()] += 1
        for d, n in sorted(per_day.items()):
            if n > cfg["bulk_exports_per_day"]:
                flag("HA-08", datetime.combine(d, datetime.min.time()), user, "",
                     f"{n} records printed or exported on {d} (threshold {cfg['bulk_exports_per_day']}).")
        fails = [e for e in evs if e.action == "login_failed"]
        window = timedelta(minutes=cfg["failed_logins_window_minutes"])
        k, last = 0, None
        for i, e in enumerate(fails):
            while fails[k].when < e.when - window:
                k += 1
            if i - k + 1 >= cfg["failed_logins_threshold"] and (last is None or e.when - last > window):
                last = e.when
                flag("HA-11", e.when, user, "", f"{i - k + 1} failed sign-ins between {fails[k].when:%H:%M} and {e.when:%H:%M}.")

    period_end = events[-1].when.date()
    for u in users.values():
        if u.get("termination_date") and u["status"] == "active":
            flag("HA-12", u["termination_date"], u["user"], "",
                 f"Left on {u['termination_date']} but the account is still marked active.")

    flags.sort(key=lambda f: (f.when, SEV.index(f.severity)))
    summaries: dict[str, UserSummary] = {}
    for f in flags:
        u = users.get(f.user, {})
        s = summaries.setdefault(f.user, UserSummary(f.user, u.get("name", "Unknown"), u.get("role", "unknown"), 0, 0, "low"))
        s.flags += 1
        s.risk_points += WEIGHT[f.severity]
        if SEV.index(f.severity) < SEV.index(s.worst):
            s.worst = f.severity
        if f.rule_id not in s.rules:
            s.rules.append(f.rule_id)
    ranked = sorted(summaries.values(), key=lambda s: (-s.risk_points, s.user))
    recs = [e for e in events if e.action in RECORD_ACTIONS]
    return Result(organization, events[0].when.date().isoformat(), period_end.isoformat(),
                  datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), __version__, len(events), len(recs),
                  len({e.user for e in events}), len({e.patient for e in recs}), flags, ranked)
