import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hipaa_audit import load_files, parse_log, parse_patients, parse_users, review  # noqa: E402
from hipaa_audit.cli import main  # noqa: E402
from hipaa_audit.engine import DataError  # noqa: E402
from hipaa_audit.reporting import WRITERS  # noqa: E402

S = ROOT / "samples"
USERS = """user,name,last_name,role,department,status,termination_date,household_id
a.nurse,Ann Nurse,Nurse,nurse,Pediatrics,active,,H1
b.doc,Bob Doc,Doc,physician,Family Medicine,active,,H2
c.desk,Cal Desk,Rivera,front_desk,Front Office,active,,H3
d.gone,Dee Gone,Gone,medical_assistant,Pediatrics,active,2026-09-22,H4
"""
PATIENTS = """patient_id,last_name,household_id,department,care_team,employee_user,high_profile
P1,Smith,PH1,Pediatrics,a.nurse,,false
P2,Jones,PH2,Family Medicine,b.doc,,false
P3,Doc,PH9,Family Medicine,,b.doc,false
P4,Rivera,H3,Pediatrics,a.nurse,,false
P5,Star,PH5,Family Medicine,b.doc,,true
"""
HEAD = "timestamp,user,role,patient_id,action,break_glass\n"


def run(log_rows: str, config=None):
    return review(parse_log(HEAD + log_rows), parse_users(USERS), parse_patients(PATIENTS), "T", config)


def rules(result):
    return [f.rule_id for f in result.flags]


class TestParsing(unittest.TestCase):
    def test_rejects_bad_input(self):
        with self.assertRaisesRegex(DataError, "missing required"):
            parse_log("when,who\n1,2\n")
        with self.assertRaisesRegex(DataError, "timestamp"):
            parse_log(HEAD + "yesterday,a.nurse,,P1,view,false\n")
        with self.assertRaisesRegex(DataError, "action must be"):
            parse_log(HEAD + "2026-09-21 09:00,a.nurse,,P1,delete,false\n")
        with self.assertRaisesRegex(DataError, "needs a patient_id"):
            parse_log(HEAD + "2026-09-21 09:00,a.nurse,,,view,false\n")


class TestRules(unittest.TestCase):
    def test_normal_access_is_not_flagged(self):
        r = run("2026-09-21 09:00,a.nurse,,P1,view,false\n2026-09-21 10:00,b.doc,,P2,edit,false\n")
        self.assertEqual(rules(r), ["HA-12"])  # only the roster issue for d.gone

    def test_coworker_family_vip_and_outside_department(self):
        r = run("2026-09-21 09:00,a.nurse,,P3,view,false\n"   # coworker b.doc's record
                "2026-09-21 09:05,c.desk,,P4,view,false\n"    # shares household H3
                "2026-09-21 09:10,a.nurse,,P5,view,false\n"   # high-profile
                "2026-09-21 09:15,a.nurse,,P2,view,false\n")  # pediatrics nurse, family medicine patient
        self.assertTrue({"HA-03", "HA-02", "HA-04", "HA-01"} <= set(rules(r)))

    def test_terminated_account(self):
        r = run("2026-09-25 21:00,d.gone,,P1,view,false\n")
        self.assertIn("HA-05", rules(r))
        self.assertIn("HA-12", rules(r))

    def test_shared_and_unknown_accounts(self):
        r = run("2026-09-21 09:00,frontdesk,,P1,view,false\n2026-09-21 09:01,frontdesk,,P2,view,false\n"
                "2026-09-21 09:02,x.ghost,,P2,view,false\n")
        self.assertEqual(rules(r).count("HA-10"), 2)  # once per account, not per access

    def test_after_hours_only_for_office_roles(self):
        r = run("2026-09-21 23:00,c.desk,,P2,view,false\n2026-09-21 23:00,a.nurse,,P1,view,false\n")
        after = [f for f in r.flags if f.rule_id == "HA-06"]
        self.assertEqual([f.user for f in after], ["c.desk"])

    def test_break_glass(self):
        r = run("2026-09-21 03:00,b.doc,,P1,view,true\n")
        self.assertIn("HA-09", rules(r))
        self.assertNotIn("HA-01", rules(r))

    def test_bulk_view_export_and_failed_logins(self):
        views = "".join(f"2026-09-22 10:{i:02d},c.desk,,P{i},view,false\n" for i in range(35))
        exports = "".join(f"2026-09-23 14:{i:02d},c.desk,,P{i},export,false\n" for i in range(12))
        fails = "".join(f"2026-09-24 06:{50 + i},b.doc,,,login_failed,false\n" for i in range(6))
        r = run(views + exports + fails)
        self.assertIn("HA-07", rules(r))
        self.assertIn("HA-08", rules(r))
        self.assertEqual(rules(r).count("HA-11"), 1)


class TestSamples(unittest.TestCase):
    def test_samples(self):
        bad = review(*load_files(S / "lakeside_family_clinic_access_log.csv", S / "lakeside_family_clinic_workforce.csv",
                                 S / "lakeside_family_clinic_patients.csv"), "L")
        good = review(*load_files(S / "cedar_valley_health_access_log.csv", S / "cedar_valley_health_workforce.csv",
                                  S / "cedar_valley_health_patients.csv"), "C")
        self.assertGreaterEqual(bad.counts()["by_severity"]["critical"], 1)
        self.assertGreaterEqual(len(bad.counts()["by_rule"]), 8)
        self.assertEqual(good.counts()["by_severity"]["critical"] + good.counts()["by_severity"]["high"], 0)
        self.assertEqual(bad.users, sorted(bad.users, key=lambda u: (-u.risk_points, u.user)))


class TestOutput(unittest.TestCase):
    def test_writers_and_escaping(self):
        r = review(parse_log(HEAD + "2026-09-21 09:00,a.nurse,,P3,view,false\n"), parse_users(USERS),
                   parse_patients(PATIENTS), "<script>x</script>")
        for fmt, w in WRITERS.items():
            self.assertTrue(w(r).strip(), fmt)
        self.assertNotIn("<script>x</script>", WRITERS["html"](r))
        json.loads(WRITERS["json"](r))

    def test_cli(self):
        L = S / "lakeside_family_clinic"
        C = S / "cedar_valley_health"
        with tempfile.TemporaryDirectory() as tmp:
            args = lambda p: [f"{p}_access_log.csv", "--workforce", f"{p}_workforce.csv", "--patients", f"{p}_patients.csv",  # noqa: E731
                              "--out", tmp]
            self.assertEqual(main(args(L) + ["--fail-on", "critical"]), 2)
            self.assertEqual(main(args(C) + ["--fail-on", "high"]), 0)
            bad = Path(tmp) / "bad.csv"
            bad.write_text("x\n1\n", encoding="utf-8")
            self.assertEqual(main([str(bad), "--workforce", str(bad), "--patients", str(bad), "--out", tmp]), 1)


if __name__ == "__main__":
    unittest.main()
