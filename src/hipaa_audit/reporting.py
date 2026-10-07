"""Write access review results as JSON, CSV, Markdown, or a self-contained HTML report with a timeline."""

from __future__ import annotations

import csv
import io
import json
from html import escape

from .engine import SEV, Result

DISCLAIMER = (
    "Flags identify access that warrants review; they are not findings of wrongdoing. Many flagged accesses have "
    "legitimate explanations. Review each with the user's manager and document the outcome. This tool supports, and "
    "does not replace, your HIPAA risk analysis, policies, and legal counsel."
)
SEV_COLOR = {"critical": "#b91c1c", "high": "#c2410c", "medium": "#a16207", "low": "#6b7280"}

TIMELINE_CSS = """
.tlx{font:14px/1.5 "Segoe UI",Roboto,Arial,sans-serif;color:#1e1530}
.tlx .day{margin:0 0 6px;font-weight:700;color:#6d28d9;font-size:13px;letter-spacing:.04em;text-transform:uppercase}
.tlx .items{border-left:3px solid #ddd3f5;margin:0 0 18px 7px;padding-left:18px}
.tlx .it{position:relative;margin:0 0 12px}
.tlx .it:before{content:"";position:absolute;left:-26px;top:5px;width:13px;height:13px;border-radius:50%;background:var(--c);border:2px solid #fff;box-shadow:0 0 0 1px var(--c)}
.tlx .hd{font-weight:600}
.tlx .tm{color:#6b5b86;font-variant-numeric:tabular-nums;margin-right:6px}
.tlx .chip{display:inline-block;font-size:11px;font-weight:700;color:#fff;background:var(--c);border-radius:3px;padding:0 6px;margin-left:6px;text-transform:uppercase}
.tlx .dt{color:#4b3d63;font-size:13px}
.tlx .ref{color:#7c6d96;font-size:12px}
"""


def timeline_html(r: Result, limit: int | None = None) -> str:
    e = escape
    parts, shown = ['<div class="tlx">'], 0
    for day, flags in r.by_day().items():
        parts.append(f'<p class="day">{e(day)}</p><div class="items">')
        for f in flags:
            if limit is not None and shown >= limit:
                break
            shown += 1
            who = e(f.user) + (f" → patient {e(f.patient)}" if f.patient else "")
            time = f.when[11:] if len(f.when) > 10 else "all day"
            parts.append(f'<div class="it" style="--c:{SEV_COLOR[f.severity]}"><div class="hd"><span class="tm">{e(time)}</span>'
                         f'{e(f.title)}<span class="chip">{e(f.severity)}</span></div>'
                         f'<div class="dt">{who}. {e(f.detail)}</div>'
                         f'<div class="ref">{e(f.rule_id)} · HIPAA {e(", ".join(f.hipaa))} · {e(", ".join(f.controls))}</div></div>')
        parts.append("</div>")
    parts.append("</div>")
    return "".join(parts)


def to_json(r: Result) -> str:
    return json.dumps(r.to_dict(), indent=2, default=str)


def to_csv(r: Result) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["when", "rule_id", "title", "severity", "user", "patient", "detail", "hipaa", "controls", "review"])
    for f in r.flags:
        w.writerow([f.when, f.rule_id, f.title, f.severity, f.user, f.patient, f.detail, "; ".join(f.hipaa),
                    "; ".join(f.controls), f.review])
    return buf.getvalue()


def to_markdown(r: Result) -> str:
    c = r.counts()
    lines = [f"# Patient record access review: {r.organization}", "",
             f"Period {r.period_start} to {r.period_end} | {r.record_accesses} record accesses by {r.users_seen} accounts | "
             f"Generated {r.generated_at}", "",
             f"- Flags for review: **{c['flags']}** (critical {c['by_severity']['critical']}, high {c['by_severity']['high']}, "
             f"medium {c['by_severity']['medium']}, low {c['by_severity']['low']})",
             f"- Accounts flagged: **{c['users_flagged']}** | Patients whose records were involved: **{c['patients_affected']}**", "",
             "## Accounts to review first", "", "| Account | Name | Role | Flags | Risk points | Rules |", "|---|---|---|---|---|---|"]
    lines += [f"| {u.user} | {u.name} | {u.role} | {u.flags} | {u.risk_points} | {', '.join(u.rules)} |" for u in r.users]
    lines += ["", "## Timeline", ""]
    for day, flags in r.by_day().items():
        lines += [f"### {day}", ""]
        for f in flags:
            lines.append(f"- **{f.when[11:] or 'all day'} [{f.severity.upper()}] {f.rule_id} {f.title}**: {f.user}"
                         f"{' → ' + f.patient if f.patient else ''}. {f.detail} _(HIPAA {', '.join(f.hipaa)}; {', '.join(f.controls)})_")
        lines.append("")
    lines += [f"_{DISCLAIMER}_", ""]
    return "\n".join(lines)


_CSS = """
*{box-sizing:border-box}
body{margin:0;background:#faf8ff;color:#1e1530;font:15px/1.55 "Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
.top{background:linear-gradient(120deg,#4c1d95,#7c3aed);color:#fff}
.top .in{max-width:1040px;margin:0 auto;padding:30px 24px}
.top p{margin:0;opacity:.9}.top h1{margin:6px 0;font-size:28px}
.kick{text-transform:uppercase;letter-spacing:.14em;font-size:12px}
main{max-width:1040px;margin:0 auto;padding:24px 24px 60px}
h2{font-size:19px;color:#6d28d9;margin:34px 0 12px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-top:-34px}
.kpi{background:#fff;border:1px solid #e4dcf7;border-radius:12px;padding:14px 16px;box-shadow:0 2px 8px rgba(76,29,149,.06)}
.kpi b{display:block;font-size:28px}.kpi span{color:#6b5b86;font-size:13px}
.panel{background:#fff;border:1px solid #e4dcf7;border-radius:12px;padding:18px 22px}
.table-wrap{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{border-bottom:1px solid #eee8fb;padding:8px 10px;text-align:left}
th{color:#6b5b86}
.sev{font-weight:700}
.note{color:#6b5b86;font-size:13px;margin-top:28px}
"""


def to_html(r: Result) -> str:
    e = escape
    c = r.counts()
    rows = "".join(f'<tr><td>{e(u.user)}</td><td>{e(u.name)}</td><td>{e(u.role.replace("_", " "))}</td><td>{u.flags}</td>'
                   f'<td class="sev" style="color:{SEV_COLOR[u.worst]}">{e(u.worst.title())}</td><td>{u.risk_points}</td>'
                   f'<td>{e(", ".join(u.rules))}</td></tr>' for u in r.users)
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Patient record access review: {e(r.organization)}</title><style>{_CSS}{TIMELINE_CSS}</style></head><body>
<div class="top"><div class="in"><p class="kick">Patient record access review</p><h1>{e(r.organization)}</h1>
<p>{e(r.period_start)} to {e(r.period_end)} · {r.record_accesses:,} record accesses by {r.users_seen} accounts · generated {e(r.generated_at)} by hipaa_audit {e(r.tool_version)}</p><br></div></div>
<main><div class="kpis">
<div class="kpi"><b>{c['flags']}</b><span>Accesses flagged for review</span></div>
<div class="kpi"><b style="color:{SEV_COLOR['critical']}">{c['by_severity']['critical']}</b><span>Critical (for example, access after someone left)</span></div>
<div class="kpi"><b>{c['users_flagged']}</b><span>Accounts to review</span></div>
<div class="kpi"><b>{c['patients_affected']}</b><span>Patients whose records were involved</span></div></div>
<h2>Accounts to review first</h2><div class="panel table-wrap"><table><thead><tr><th>Account</th><th>Name</th><th>Role</th><th>Flags</th><th>Worst</th><th>Risk points</th><th>Rules</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>Timeline of flagged access</h2><div class="panel">{timeline_html(r) if r.flags else '<p>No access was flagged.</p>'}</div>
<p class="note">{e(DISCLAIMER)}</p></main></body></html>"""


WRITERS = {"json": to_json, "csv": to_csv, "md": to_markdown, "html": to_html}
