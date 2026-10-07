# Methodology

## Purpose

The HIPAA Security Rule requires covered entities and business associates to record and examine activity in systems that contain electronic protected health information (audit controls, 45 CFR 164.312(b)) and to regularly review records of that activity (information system activity review, 45 CFR 164.308(a)(1)(ii)(D)). Small practices often collect access logs but rarely review them. This tool performs a first-pass review and lists the accesses that most deserve human follow-up.

## Inputs

- **Access log:** one row per event (view, edit, print, export, sign-in, failed sign-in), exported from the electronic health record or practice management system.
- **Workforce roster:** every account, with role, department, employment status, termination date, last name, and an optional household identifier.
- **Patient roster:** patient identifiers with department, care team, and markers for patients who are employees or high-profile individuals.

## Rules

| Rule | Flag | Severity | HIPAA | NIST SP 800-53 |
|---|---|---|---|---|
| HA-01 | Clinical user opens a patient outside their department and not on the care team | Medium | 164.308(a)(4), 164.502(b) | AC-6, AU-6 |
| HA-02 | Access to a record sharing the user's household or last name | High | 164.308(a)(1)(ii)(D), 164.502(b) | AU-6, AC-6 |
| HA-03 | Access to a coworker's record without being on their care team | High | 164.308(a)(1)(ii)(D), 164.502(b) | AU-6, AC-6 |
| HA-04 | Access to a high-profile patient's record without being on the care team | High | 164.308(a)(1)(ii)(D), 164.502(b) | AU-6, AC-6 |
| HA-05 | Access by an account after the person's termination date | Critical | 164.308(a)(3)(ii)(C), 164.312(a)(1) | AC-2, PS-4 |
| HA-06 | Office roles accessing records outside business hours or on weekends | Low | 164.308(a)(1)(ii)(D) | AU-6 |
| HA-07 | More than 30 different patients opened within 60 minutes | High | 164.308(a)(1)(ii)(D), 164.312(b) | AU-6, SI-4 |
| HA-08 | More than 10 records printed or exported in one day | High | 164.308(a)(1)(ii)(D), 164.312(b) | AU-6, AC-6 |
| HA-09 | Emergency (break-the-glass) access | Low | 164.312(a)(2)(ii) | AC-3, AU-6 |
| HA-10 | Shared, generic, or unknown account accessing records | High | 164.312(a)(2)(i), 164.312(d) | IA-2, AC-2 |
| HA-11 | Five or more failed sign-ins within 15 minutes | Medium | 164.308(a)(5)(ii)(C) | AC-7, AU-6 |
| HA-12 | Account marked active after the person's termination date | Critical | 164.308(a)(3)(ii)(C) | AC-2, PS-4 |

Rules HA-02 to HA-04 and HA-01 are evaluated in that order for each access and only one applies, so a single access is not counted several times. Access by a member of the patient's care team is not flagged for these relationship rules. Thresholds, role groups, business hours, and generic account names are set in `src/hipaa_audit/data/config.json` and can be changed with `--config`.

## Prioritization

Each flag carries a severity weight (critical 10, high 6, medium 3, low 1). Accounts are ranked by total weight so reviewers can start with the accounts most likely to need action.

## Limitations

- A flag is a prompt for review, not a finding of wrongdoing. Billing, scheduling, coverage, and consultations often explain flagged access.
- Results depend on accurate care team, department, and roster data.
- Matching on last name produces false positives for common names; a household or address identifier is more reliable.
- The tool does not decide whether a breach occurred. Breach determinations follow the risk assessment in 45 CFR 164.402 and your policies.
