"""Interactive dashboard for the HIPAA Audit Engine.

Run locally:   streamlit run app/streamlit_app.py

Layout: no sidebar. The main screen is a case queue: accounts ranked by risk on the left, and the case
file for the selected account on the right, the way a privacy officer works through a review.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import ui  # noqa: E402
from hipaa_audit import __version__, parse_log, parse_patients, parse_users, review  # noqa: E402
from hipaa_audit.engine import SEV, DataError  # noqa: E402
from hipaa_audit.reporting import DISCLAIMER, TIMELINE_CSS, timeline_html, to_csv, to_html, to_json, to_markdown  # noqa: E402

S = ROOT / "samples"
SAMPLES = {
    "Family clinic with several concerns (fictional)": ("Lakeside Family Clinic (fictional)", "lakeside_family_clinic"),
    "Clinic with clean access patterns (fictional)": ("Cedar Valley Health (fictional)", "cedar_valley_health"),
}
UPLOADS = ("Access log (.csv)", "Workforce roster (.csv)", "Patient roster (.csv)")

PAL = ui.Palette(accent="#6D28D9", band="#1E1530", band_text="#FFFFFF", band_sub="#C9BCE6",
                 card="#FFFFFF", line="#E4DCF5", ink="#1E1530", muted="#6B5F80")
ui.setup("Patient record access review", "HIPAA Security Rule · 45 CFR 164.312(b) audit controls",
         "Review electronic health record access logs: find staff opening records they have no reason to see, "
         "accounts used after someone left, bulk exports and shared logins, then work through them as cases.",
         "🩺", PAL)

# ---- Top row: data -----------------------------------------------------------------------------------
t1, t2 = st.columns([1.5, 4], vertical_alignment="top")
texts, org = None, "My organization"
with t1:
    st.caption("Data")
    source = ui.choose("Data", ["Use a sample", "Upload my own files"], key="source", format_func=ui.source_label)
with t2:
    if source == "Use a sample":
        st.caption("Sample organization")
        org, key = SAMPLES[st.selectbox("Sample organization", list(SAMPLES), label_visibility="collapsed")]
        texts = [(S / f"{key}_{n}.csv").read_text(encoding="utf-8") for n in ("access_log", "workforce", "patients")]
    else:
        st.warning("**Do not upload real patient data to this public demo.** To review real logs, download the tool "
                   "from GitHub and run it on your own computer, inside your organization's network.")
if source != "Use a sample":
    u1, u2, u3, u4 = st.columns([1, 1, 1, 1])
    ups = [col.file_uploader(label, type=["csv"]) for col, label in zip((u1, u2, u3), UPLOADS)]
    org = u4.text_input("Organization name", "My organization")
    if all(ups):
        texts = [u.getvalue().decode("utf-8-sig", errors="replace") for u in ups]

if texts is None:
    st.info("Upload all three files above, or switch to a sample, to see the case queue.")
    ui.footer("hipaa_audit", __version__, "hipaa-audit-engine", DISCLAIMER)
    st.stop()
try:
    r = review(parse_log(texts[0]), parse_users(texts[1]), parse_patients(texts[2]), org)
except DataError as exc:
    st.error(f"The files could not be read. {exc} Fix the file and upload it again.")
    st.stop()

c = r.counts()
st.markdown(f"<div class='g-sec'>{escape(r.organization)}</div>", unsafe_allow_html=True)
st.caption(f"{r.period_start} to {r.period_end} · {r.record_accesses:,} record accesses by {r.users_seen} accounts "
           f"across {r.patients_seen} patients")
ui.tiles([(c["flags"], "Accesses flagged for review"),
          (c["by_severity"]["critical"], "Critical", ui.SEV_COLORS["critical"]),
          (c["users_flagged"], "Accounts to review", ui.SEV_COLORS["high"]),
          (c["patients_affected"], "Patients involved")], PAL)

view = ui.choose("View", ["Case queue", "Timeline", "Patterns"], key="view")

if view == "Case queue":
    if not r.users:
        st.success("No accounts were flagged. Nothing to review.")
    else:
        q, case = st.columns([1.15, 2], gap="large")
        with q:
            ui.section("Case queue", "Highest risk first. Select an account to open its case file.")
            if st.session_state.get("case") not in [u.user for u in r.users]:
                st.session_state["case"] = r.users[0].user
            for i, u in enumerate(r.users, 1):
                st.button(f"#{i}  {u.name or u.user} · {u.risk_points} pts · {u.worst} · {u.flags} flag(s)",
                          key=f"case_{u.user}", use_container_width=True,
                          type="primary" if u.user == st.session_state["case"] else "secondary",
                          on_click=st.session_state.__setitem__, args=("case", u.user))
            pick = st.session_state["case"]
        with case:
            u = next(x for x in r.users if x.user == pick)
            mine = [f for f in r.flags if f.user == u.user]
            col = ui.SEV_COLORS.get(u.worst, PAL.accent)
            st.markdown(f"<div style='background:#1E1530;color:#fff;border-radius:12px;padding:14px 18px;"
                        f"border-left:8px solid {col};margin-bottom:12px'>"
                        f"<div style='font:600 21px Georgia,serif'>Case: {escape(u.name or u.user)}</div>"
                        f"<div style='color:#C9BCE6;font-size:13px'>Account {escape(u.user)} · "
                        f"{escape(u.role.replace('_', ' '))} · worst finding {escape(u.worst)} · {u.risk_points} "
                        f"risk points · rules {escape(', '.join(u.rules))}</div></div>", unsafe_allow_html=True)
            patients = sorted({f.patient for f in mine if f.patient})
            st.caption(f"{len(mine)} flagged access(es) involving {len(patients)} patient(s).")
            groups: dict[str, list] = {}
            for f in mine:
                groups.setdefault(f.rule_id, []).append(f)
            for rid, fs in groups.items():
                f = fs[0]
                hits = "".join(f"<li>{escape(x.when)} · patient {escape(x.patient or 'n/a')}"
                               + (f" · {escape(x.detail)}" if x.detail != f.detail else "") + "</li>" for x in fs)
                ui.card(f"<div class='h'>{ui.sev_pill(f.severity)}{escape(rid)} · {escape(f.title)}"
                        f"<span class='s' style='float:right'>{len(fs)} event(s)</span></div>",
                        f"<div class='d'>{escape(f.detail)}</div>"
                        f"<ul class='s' style='margin:4px 0 6px 18px;padding:0'>{hits}</ul>"
                        f"<div class='s'>HIPAA {escape(', '.join(f.hipaa))} · NIST {escape(', '.join(f.controls))}</div>"
                        f"<div class='f'><b>How to review:</b> {escape(f.review)}</div>",
                        accent=ui.SEV_COLORS.get(f.severity))

elif view == "Timeline":
    t1, t2 = st.columns([1, 2])
    with t1:
        st.caption("Severity")
        sev_filter = ui.multi("Severity", SEV, key="sev", format_func=str.title)
    with t2:
        user_filter = st.multiselect("Show only these accounts", [u.user for u in r.users])
    shown = [f for f in r.flags if f.severity in sev_filter and (not user_filter or f.user in user_filter)]
    ui.section(f"Timeline of flagged access ({len(shown)})")
    if shown:
        st.markdown(f"<style>{TIMELINE_CSS}</style>{timeline_html(replace(r, flags=shown))}", unsafe_allow_html=True)
    else:
        st.success("Nothing to show for the selected filters.")

else:
    left, right = st.columns([3, 2])
    with left:
        ui.section("Flags by day")
        days = r.by_day()
        if days:
            st.bar_chart(pd.DataFrame({"Flags": {d: len(f) for d, f in days.items()}}), color="#6D28D9")
        else:
            st.caption("No flags.")
    with right:
        ui.section("Flags by type")
        titles = {f.rule_id: f.title for f in r.flags}
        st.dataframe(pd.DataFrame([{"Rule": k, "Finding": titles[k], "Count": v}
                                   for k, v in sorted(c["by_rule"].items())]), hide_index=True)
    ui.section("All accounts flagged")
    st.dataframe(pd.DataFrame([{"Account": u.user, "Name": u.name, "Role": u.role.replace("_", " "), "Flags": u.flags,
                                "Worst": u.worst.title(), "Risk points": u.risk_points, "Rules": ", ".join(u.rules)}
                               for u in r.users]), hide_index=True, use_container_width=True)

ui.downloads([("HTML report", to_html(r), "access_review.html", "text/html"),
              ("Markdown", to_markdown(r), "access_review.md", "text/markdown"),
              ("CSV flags", to_csv(r), "access_flags.csv", "text/csv"),
              ("JSON results", to_json(r), "access_review.json", "application/json")])
ui.footer("hipaa_audit", __version__, "hipaa-audit-engine", DISCLAIMER)
