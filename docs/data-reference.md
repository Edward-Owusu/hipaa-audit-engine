# Input reference

Templates are in `samples/`. Column names are not case-sensitive.

## Access log

| Column | Required | Notes |
|---|---|---|
| `timestamp` | Yes | For example `2026-09-21 14:05` |
| `user` | Yes | Account name, matching the workforce roster |
| `action` | Yes | `view`, `edit`, `print`, `export`, `login`, or `login_failed` |
| `patient_id` | For record actions | Matching the patient roster |
| `role` | No | Used only if the account is not on the roster |
| `break_glass` | No | `true` when an emergency override was used |

## Workforce roster

| Column | Required | Notes |
|---|---|---|
| `user` | Yes | Account name |
| `role` | Yes | For example `physician`, `nurse`, `medical_assistant`, `front_desk`, `billing`, `scheduling` |
| `status` | Yes | `active` or `terminated` |
| `name`, `last_name`, `department` | No | Improve matching and reporting |
| `termination_date` | No | `YYYY-MM-DD` |
| `household_id` | No | An address or household key, more reliable than last name for detecting family access |

## Patient roster

| Column | Required | Notes |
|---|---|---|
| `patient_id` | Yes | |
| `department` | No | Department or clinic responsible for the patient |
| `care_team` | No | Semicolon-separated account names |
| `last_name`, `household_id` | No | For family relationship checks |
| `employee_user` | No | The account name if the patient is also an employee |
| `high_profile` | No | `true` for patients whose records warrant extra protection |

## Handling real data

These files contain protected health information. **Run the tool on your own computer or server inside your organization's environment, and never upload real data to the public demo.** The tool makes no network connections and writes reports only where you tell it to. Store reports as securely as the records themselves.
