"""Interactive dashboard for the HIPAA Audit Engine.

Run locally:   streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hipaa_audit import __version__, parse_log, parse_patients, parse_users, review  # noqa: E402
from hipaa_audit.engine import SEV, DataError  # noqa: E402
from hipaa_audit.reporting import DISCLAIMER, TIMELINE_CSS, timeline_html, to_csv, to_html, to_json, to_markdown  # noqa: E402

S = ROOT / "samples"
SAMPLES = {
    "Family clinic with several concerns (fictional)": ("Lakeside Family Clinic (fictional)", "lakeside_family_clinic"),
    "Clinic with clean access patterns (fictional)": ("Cedar Valley Health (fictional)", "cedar_valley_health"),
}

st.set_page_config(page_title="HIPAA Audit Engine", page_icon="🩺", layout="wide")
st.title("🩺 Patient record access review")
st.write("Review electronic health record access logs the way the HIPAA Security Rule expects: find staff opening records "
         "they have no reason to see, accounts used after someone left, bulk exports, shared logins, and more, laid out "
         "on a timeline for follow-up.")

with st.sidebar:
    st.header("1. Choose data")
    source = st.radio("Data", ["Use a sample", "Upload my own files"], label_visibility="collapsed")
    texts, org = None, "My organization"
    if source == "Use a sample":
        org, key = SAMPLES[st.selectbox("Sample organization", list(SAMPLES))]
        texts = [(S / f"{key}_{n}.csv").read_text(encoding="utf-8") for n in ("access_log", "workforce", "patients")]
    else:
        st.warning("**Do not upload real patient data to this public demo.** To review real logs, download the tool from "
                   "GitHub and run it on your own computer, inside your organization's network.")
        ups = [st.file_uploader(label, type=["csv"]) for label in
               ("Access log (.csv)", "Workforce roster (.csv)", "Patient roster (.csv)")]
        org = st.text_input("Organization name", "My organization")
        if all(ups):
            texts = [u.getvalue().decode("utf-8-sig", errors="replace") for u in ups]
    st.header("2. Filter the timeline")
    sev_filter = st.multiselect("Severity", SEV, default=SEV, format_func=str.title)
    st.caption(f"hipaa_audit {__version__}. Runs entirely in this session; files are not stored.")

if texts is None:
    st.info("Upload all three files in the sidebar, or switch to a sample, to see results.")
    st.stop()
try:
    r = review(parse_log(texts[0]), parse_users(texts[1]), parse_patients(texts[2]), org)
except DataError as exc:
    st.error(f"The files could not be read. {exc} Fix the file and upload it again.")
    st.stop()

c = r.counts()
st.subheader(r.organization)
st.caption(f"{r.period_start} to {r.period_end} · {r.record_accesses:,} record accesses by {r.users_seen} accounts "
           f"across {r.patients_seen} patients")
m = st.columns(4)
m[0].metric("Accesses flagged for review", c["flags"])
m[1].metric("Critical", c["by_severity"]["critical"])
m[2].metric("Accounts to review", c["users_flagged"])
m[3].metric("Patients involved", c["patients_affected"])

left, right = st.columns([3, 2])
with left:
    st.markdown("#### Accounts to review first")
    if r.users:
        st.dataframe(pd.DataFrame([{"Account": u.user, "Name": u.name, "Role": u.role.replace("_", " "), "Flags": u.flags,
                                    "Worst": u.worst.title(), "Risk points": u.risk_points, "Rules": ", ".join(u.rules)}
                                   for u in r.users]), hide_index=True)
    else:
        st.success("No accounts were flagged.")
with right:
    st.markdown("#### Flags by day")
    days = r.by_day()
    if days:
        st.bar_chart(pd.DataFrame({"Flags": {d: len(f) for d, f in days.items()}}), color="#6D28D9")
    st.markdown("#### Flags by type")
    titles = {f.rule_id: f.title for f in r.flags}
    st.dataframe(pd.DataFrame([{"Rule": k, "Finding": titles[k], "Count": v} for k, v in sorted(c["by_rule"].items())]),
                 hide_index=True)

user_filter = st.multiselect("Show only these accounts", [u.user for u in r.users])
shown = [f for f in r.flags if f.severity in sev_filter and (not user_filter or f.user in user_filter)]
st.markdown(f"### Timeline of flagged access ({len(shown)})")
if shown:
    st.markdown(f"<style>{TIMELINE_CSS}</style>{timeline_html(replace(r, flags=shown))}", unsafe_allow_html=True)
    with st.expander("How to review each type of flag"):
        seen = set()
        for f in shown:
            if f.rule_id not in seen:
                seen.add(f.rule_id)
                st.markdown(f"**{f.rule_id} {f.title}.** {f.review}")
else:
    st.success("Nothing to show for the selected filters.")

st.markdown("#### Download the report")
d = st.columns(4)
d[0].download_button("HTML report", to_html(r), "access_review.html", "text/html")
d[1].download_button("Markdown", to_markdown(r), "access_review.md", "text/markdown")
d[2].download_button("CSV flags", to_csv(r), "access_flags.csv", "text/csv")
d[3].download_button("JSON results", to_json(r), "access_review.json", "application/json")
st.caption(DISCLAIMER)
