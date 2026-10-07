# Patient record access review: Lakeside Family Clinic (fictional)

Period 2026-09-21 to 2026-10-02 | 2061 record accesses by 18 accounts | Generated 2026-10-06 19:21 UTC

- Flags for review: **22** (critical 7, high 8, medium 4, low 3)
- Accounts flagged: **10** | Patients whose records were involved: **14**

## Accounts to review first

| Account | Name | Role | Flags | Risk points | Rules |
|---|---|---|---|---|---|
| i.reed | Irene Reed | medical_assistant | 7 | 70 | HA-12, HA-05 |
| e.brooks | Elena Brooks | nurse | 2 | 12 | HA-03 |
| j.diaz | James Diaz | front_desk | 2 | 12 | HA-02 |
| l.ward | Luis Ward | billing | 2 | 12 | HA-08, HA-04 |
| h.nguyen | Hector Nguyen | medical_assistant | 3 | 9 | HA-01 |
| b.kim | Ben Kim | physician | 1 | 6 | HA-04 |
| frontdesk | Unknown | unknown | 1 | 6 | HA-10 |
| n.moore | Noah Moore | scheduling | 1 | 3 | HA-11 |
| m.ellis | Maya Ellis | billing | 2 | 2 | HA-06 |
| f.shah | Frank Shah | nurse | 1 | 1 | HA-09 |

## Timeline

### 2026-09-21

- **08:02 [HIGH] HA-10 Shared, generic, or unknown account used to access records**: frontdesk. Account 'frontdesk' is not on the workforce roster; it accessed records 5 time(s) in this period. _(HIPAA 164.312(a)(2)(i), 164.312(d); IA-2, AC-2)_

### 2026-09-22

- **12:41 [HIGH] HA-03 Access to a coworker's medical record**: e.brooks → P1005. Opened the record of coworker 'c.lopez' without being on their care team. _(HIPAA 164.308(a)(1)(ii)(D), 164.502(b); AU-6, AC-6)_

### 2026-09-23

- **all day [CRITICAL] HA-12 Account still active after termination**: i.reed. Left on 2026-09-23 but the account is still marked active. _(HIPAA 164.308(a)(3)(ii)(C); AC-2, PS-4)_
- **09:07 [HIGH] HA-02 Access to a possible family member's record**: j.diaz → P1011. User and patient share a household or address on file. _(HIPAA 164.308(a)(1)(ii)(D), 164.502(b); AU-6, AC-6)_
- **09:09 [HIGH] HA-02 Access to a possible family member's record**: j.diaz → P1011. User and patient share a household or address on file. _(HIPAA 164.308(a)(1)(ii)(D), 164.502(b); AU-6, AC-6)_

### 2026-09-24

- **12:15 [HIGH] HA-03 Access to a coworker's medical record**: e.brooks → P1005. Opened the record of coworker 'c.lopez' without being on their care team. _(HIPAA 164.308(a)(1)(ii)(D), 164.502(b); AU-6, AC-6)_

### 2026-09-25

- **20:05 [CRITICAL] HA-05 Access by an account after the person left**: i.reed → P1040. View on 2026-09-25 after termination on 2026-09-23. _(HIPAA 164.308(a)(3)(ii)(C), 164.312(a)(1); AC-2, PS-4)_
- **20:08 [CRITICAL] HA-05 Access by an account after the person left**: i.reed → P1041. View on 2026-09-25 after termination on 2026-09-23. _(HIPAA 164.308(a)(3)(ii)(C), 164.312(a)(1); AC-2, PS-4)_
- **20:11 [CRITICAL] HA-05 Access by an account after the person left**: i.reed → P1042. View on 2026-09-25 after termination on 2026-09-23. _(HIPAA 164.308(a)(3)(ii)(C), 164.312(a)(1); AC-2, PS-4)_
- **20:14 [CRITICAL] HA-05 Access by an account after the person left**: i.reed → P1043. View on 2026-09-25 after termination on 2026-09-23. _(HIPAA 164.308(a)(3)(ii)(C), 164.312(a)(1); AC-2, PS-4)_
- **20:17 [CRITICAL] HA-05 Access by an account after the person left**: i.reed → P1044. View on 2026-09-25 after termination on 2026-09-23. _(HIPAA 164.308(a)(3)(ii)(C), 164.312(a)(1); AC-2, PS-4)_
- **20:20 [CRITICAL] HA-05 Access by an account after the person left**: i.reed → P1045. View on 2026-09-25 after termination on 2026-09-23. _(HIPAA 164.308(a)(3)(ii)(C), 164.312(a)(1); AC-2, PS-4)_

### 2026-09-26

- **02:33 [LOW] HA-09 Emergency (break-the-glass) access needs review**: f.shah → P1001. Emergency override used to view this record. _(HIPAA 164.312(a)(2)(ii); AC-3, AU-6)_

### 2026-09-27

- **13:00 [MEDIUM] HA-01 Clinical access with no treatment relationship**: h.nguyen → P1002. Medical Assistant from Family Medicine opened a patient assigned to Urgent Care. _(HIPAA 164.308(a)(4), 164.502(b); AC-6, AU-6)_
- **13:04 [MEDIUM] HA-01 Clinical access with no treatment relationship**: h.nguyen → P1008. Medical Assistant from Family Medicine opened a patient assigned to Urgent Care. _(HIPAA 164.308(a)(4), 164.502(b); AC-6, AU-6)_
- **13:08 [MEDIUM] HA-01 Clinical access with no treatment relationship**: h.nguyen → P1011. Medical Assistant from Family Medicine opened a patient assigned to Urgent Care. _(HIPAA 164.308(a)(4), 164.502(b); AC-6, AU-6)_

### 2026-09-28

- **16:52 [HIGH] HA-04 Access to a high-profile patient's record without a treatment relationship**: b.kim → P1077. High-profile record opened by someone outside the care team. _(HIPAA 164.308(a)(1)(ii)(D), 164.502(b); AU-6, AC-6)_

### 2026-09-29

- **00:00 [HIGH] HA-08 Bulk printing or exporting of records**: l.ward. 28 records printed or exported on 2026-09-29 (threshold 10). _(HIPAA 164.308(a)(1)(ii)(D), 164.312(b); AU-6, AC-6)_
- **14:17 [HIGH] HA-04 Access to a high-profile patient's record without a treatment relationship**: l.ward → P1077. High-profile record opened by someone outside the care team. _(HIPAA 164.308(a)(1)(ii)(D), 164.502(b); AU-6, AC-6)_

### 2026-09-30

- **23:10 [LOW] HA-06 Access outside normal working hours**: m.ellis → P1090. Billing account active at Wed 23:10. _(HIPAA 164.308(a)(1)(ii)(D); AU-6)_
- **23:14 [LOW] HA-06 Access outside normal working hours**: m.ellis → P1091. Billing account active at Wed 23:14. _(HIPAA 164.308(a)(1)(ii)(D); AU-6)_

### 2026-10-01

- **06:54 [MEDIUM] HA-11 Repeated failed sign-in attempts**: n.moore. 5 failed sign-ins between 06:50 and 06:54. _(HIPAA 164.308(a)(5)(ii)(C); AC-7, AU-6)_

_Flags identify access that warrants review; they are not findings of wrongdoing. Many flagged accesses have legitimate explanations. Review each with the user's manager and document the outcome. This tool supports, and does not replace, your HIPAA risk analysis, policies, and legal counsel._
