# Intentionally Vulnerable Student Management System (Security Lab)

## 1. Project Overview
This project is a minimal, intentionally insecure Student Management System created exclusively for educational testing and cybersecurity viva preparation. Built with Flask, SQLite, and Jinja templates, it provides a lightweight platform to demonstrate fundamental secure coding principles, identify vulnerabilities, validate them locally, and explain corresponding defense mechanisms without complex frameworks or external dependencies.

---

## 2. How to Run It

```bash
# 1. Navigate to the project directory
cd security_lab

# 2. Install dependencies (Flask)
pip install -r requirements.txt

# 3. Run the application
python app.py
```
Open your browser and navigate to: `http://127.0.0.1:5000`

---

## 3. User Accounts (Fake Lab Credentials)

| Role | Username | Password | Intended Permissions |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Full access: View, Edit, Delete, Create all student records. |
| **Teacher** | `teacher` | `teacher123` | View and Edit student grades, Create new records (pending admin approval). |
| **Student** | `student` | `student123` | Read-only access to their own profile record. |

---

## 4. Vulnerability Map

| Vulnerability | Security Principle | Location (`app.py`) | Why It Is Wrong |
| :--- | :--- | :--- | :--- |
| **SQL Injection** | Input Sanitization / Security Boundaries | `search()` (`line 80`) | String formatting directly embeds un-escaped user input into the SQL query statement. |
| **Missing Role Check on Edit** | **1. Least Privilege** | `edit_student()` (`line 128`) | Logged-in users with `student` role are permitted to edit any student record without restriction. |
| **Backend Unprotected Delete** | **2. Defense in Depth** | `delete_student()` (`line 155`) | The UI hides the delete button from students, but the backend route executes deletions without role verification. |
| **Allow-on-Error Access Check** | **3. Fail Safe** | `edit_student()` (`line 120`) | An exception during the authorization check sets `access_granted = True`, granting access by default. |
| **Teacher Self-Approval** | **4. Segregation of Duties** | `create_student()` (`line 104`) | A single user creates a student record and immediately sets `approved = 1` without independent review. |
| **IDOR Profile Access** | **5. Segmentation** | `view_student()` (`line 90`) | User data boundaries are not enforced; changing the URL ID parameter allows viewing any student record. |
| **Excessive Sensitive Data** | **6. Minimization** | `init_db()` & `student.html` | Collects and displays unnecessary PII (`ssn_or_passport` and `home_address`) not required by the app. |
| **Public Default Access** | **7. Secure by Default** | `create_student()` (`line 104`) | Newly created student records default to public shared access (`is_public = 1`) rather than private. |
| **Traceable Linear Control Flow** | **8. Keep It Simple & Straight** | Entire `app.py` | Built using simple procedural code without heavy abstraction, allowing easy manual logic auditing. |
| **Secret Parameter Authorization** | **9. Keep It Open** | `delete_student()` (`line 152`) | Relies on a hidden URL parameter (`?secret_key=...`) for security rather than explicit, verifiable RBAC. |
| **Annoying CAPTCHA Friction** | **10. Usability** | `edit_student()` (`line 131`) | Demands exact typing of a long fixed string on every edit, annoying users into seeking security bypasses. |

---

## 5. Local Validation Procedures (Safe & Harmless)

1. **SQL Injection**:
   - Log in as any user.
   - In the search bar on `/dashboard`, enter `' OR '1'='1` and click **Search**.
   - *Result*: All student records in the database are returned, bypassing search filtering.

2. **Least Privilege Violation**:
   - Log in as `student` / `student123`.
   - Navigate directly to `/student/edit/1` (Alice Smith's record).
   - Modify the name/grade and submit.
   - *Result*: The student role successfully modifies another user's record.

3. **Defense in Depth Violation**:
   - Log in as `student` / `student123`. Note that the "Delete" link is missing from the table.
   - Type `/student/delete/1` directly into your browser address bar.
   - *Result*: Alice Smith's record is deleted because the backend lacks independent role checking.

4. **Fail Safe Violation**:
   - Inspect `edit_student()` in `app.py`. Note how the missing dictionary key causes an exception that triggers `access_granted = True`.
   - Any user accessing the route is granted access due to fail-open logic.

5. **Segregation of Duties Violation**:
   - Log in as `teacher` / `teacher123`.
   - Click **Create New Student**, fill in student details, and submit.
   - View the record; observe `approved` status is automatically set to `Approved` without secondary approval.

6. **Segmentation Violation (IDOR)**:
   - Log in as `student` / `student123`.
   - Access `/student/1`, `/student/2`, `/student/3`.
   - *Result*: The student can view confidential profile data of all other students.

7. **Minimization Violation**:
   - Access `/student/1`.
   - *Result*: Displays full SSN/Passport numbers and Home Addresses, which are unnecessary for simple grade tracking.

8. **Secure by Default Violation**:
   - Create a new student via `/student/create`.
   - *Result*: Database sets `is_public = 1` by default, exposing the record publicly immediately.

9. **Keep It Open Violation**:
   - Inspect `delete_student()` route. Observe that providing `?secret_key=hidden_admin_token` is treated as security authentication.

10. **Usability Friction Violation**:
    - Attempt to edit a student record. Notice the required re-entry of `CONFIRM_SECURITY_CHECK_12345`.
    - Demonstrates how tedious security steps encourage users to share admin credentials or script workarounds.

---

## 6. Vulnerability Fixes & Code Snippets

### 1. SQL Injection Fix
- **Fix**: Use parameterized queries (`?`) instead of string concatenation.
```python
# SECURE FIX:
query = "SELECT * FROM students WHERE name LIKE ?"
students = conn.execute(query, (f"%{q}%",)).fetchall()
```

### 2. Least Privilege & Defense in Depth Fix
- **Fix**: Perform server-side role validation in backend routes.
```python
# SECURE FIX:
if session.get("role") not in ["admin", "teacher"]:
    return "Forbidden: Insufficient privileges", 403
```

### 3. Fail Safe Fix
- **Fix**: Default to deny access (`access_granted = False`) in exception handlers.
```python
# SECURE FIX:
access_granted = False
try:
    access_granted = check_user_permissions(session.get("user_id"))
except Exception:
    access_granted = False  # Deny by default
```

### 4. Segregation of Duties Fix
- **Fix**: Set `approved = 0` on creation, requiring a separate user (e.g. `admin`) to approve.
```python
# SECURE FIX:
conn.execute(
    "INSERT INTO students (name, grade, approved) VALUES (?, ?, 0)",
    (name, grade)
)
```

### 5. Segmentation (IDOR) Fix
- **Fix**: Ensure students can only access records matching their own user ID.
```python
# SECURE FIX:
if session.get("role") == "student" and session.get("user_id") != id:
    return "Unauthorized data access", 403
```

---

## 7. Before vs After Comparison

| Security Principle | Vulnerable Behavior (Before) | Secure Behavior (After) |
| :--- | :--- | :--- |
| **Least Privilege** | Student role can edit all student records. | Student role is restricted to read-only access on their own record. |
| **Defense in Depth** | Hides delete button in UI; backend route is completely open. | Frontend hides button AND backend independently checks `session['role'] == 'admin'`. |
| **Fail Safe** | Authorization check error defaults to `access_granted = True`. | Authorization check error defaults to `access_granted = False` (Deny-by-default). |
| **Segregation of Duties** | Creator creates and self-approves grade records in one step. | Creator creates pending record (`approved=0`); distinct Admin role must approve (`approved=1`). |
| **Segmentation** | Any student accesses `/student/<id>` for any ID. | Backend enforces user boundary checks (`session['user_id'] == requested_id`). |
| **Minimization** | Collects and displays full SSN and home address. | Collects only student name and academic grade. |
| **Secure by Default** | New records default to `is_public = 1`. | New records default to `is_public = 0` (Private). |
| **Keep It Open** | Security relies on secret hidden URL parameter (`secret_key`). | Security relies on open, audited role-based authorization checks. |
| **Usability** | Requires re-typing 25-character captcha on every edit. | Seamless session-based auth without unnecessary user friction. |

---

# Viva Preparation Guide

## Structured 10-Point Analysis for Each Vulnerability

### Vulnerability 1: SQL Injection in Search
1. **What is it?**: Unsanitized user input inserted directly into a SQL command string.
2. **Where is it in the code?**: `app.py` in the `/search` route (`line 80`).
3. **Why does it happen?**: Python f-string concatenation (`f"SELECT ... '{q}'"`) treats user input as code.
4. **How to validate it?**: Enter `' OR '1'='1` in the search box; all table rows return.
5. **Principle violated**: Input Sanitization & Security Boundaries.
6. **Impact**: Unauthorized data extraction, data exposure, or authentication bypass.
7. **How to fix it?**: Use parameterized SQL queries with placeholder `?`.
8. **Why does the fix work?**: The database engine treats the input strictly as literal parameter data, not executable SQL syntax.
9. **Alternative fix**: Use an Object-Relational Mapper (ORM) like SQLAlchemy or input sanitization/whitelisting.
10. **Examiner follow-up question**: *"Can parameterized queries prevent all SQL injections?"* -> **Answer**: Yes, for values inside WHERE/INSERT/UPDATE clauses, though dynamic column/table names still require strict whitelisting.

---

### Vulnerability 2: Missing Authorization on Edit (Least Privilege)
1. **What is it?**: Broken Function Level Access Control / Missing Role Verification.
2. **Where is it in the code?**: `app.py` in `edit_student()` (`line 128`).
3. **Why does it happen?**: The backend verifies `user_id in session` (authentication) but fails to verify if `role` is permitted to perform updates (authorization).
4. **How to validate it?**: Log in as `student` and issue POST request to `/student/edit/1`.
5. **Principle violated**: Principle of Least Privilege.
6. **Impact**: Unauthorized modification of critical student records by unauthorized users.
7. **How to fix it?**: Add `if session.get('role') not in ['admin', 'teacher']: return "Forbidden", 403`.
8. **Why does the fix work?**: Explicitly rejects HTTP requests originating from low-privilege sessions before executing database operations.
9. **Alternative fix**: Implement role-based decorator wrappers (`@requires_role('admin')`).
10. **Examiner follow-up question**: *"What is the difference between Authentication and Authorization?"* -> **Answer**: Authentication verifies *who you are*; Authorization verifies *what you are allowed to do*.

---

### Vulnerability 3: Hidden Delete Link with Unprotected Backend (Defense in Depth)
1. **What is it?**: Security through UI obfuscation without backend authorization enforcement.
2. **Where is it in the code?**: `dashboard.html` (`{% if role == 'admin' %}`) and `app.py` (`delete_student()`).
3. **Why does it happen?**: The developer assumed that hiding the HTML link prevented users from calling the route.
4. **How to validate it?**: Log in as `student` and type `/student/delete/1` in the browser address bar.
5. **Principle violated**: Defense in Depth.
6. **Impact**: Unprivileged users can delete database records simply by guessing or knowing the URL endpoint.
7. **How to fix it?**: Perform role validation inside `delete_student()` route on the server side.
8. **Why does the fix work?**: Ensures security controls exist at both the presentation layer and the application business logic layer.
9. **Alternative fix**: Use POST/DELETE HTTP methods with CSRF tokens and server-side session permission checks.
10. **Examiner follow-up question**: *"Why is client-side validation or UI hiding insufficient for security?"* -> **Answer**: Client-side UI controls can be completely bypassed by manually crafting HTTP requests.

---

### Vulnerability 4: Error Handling Access Bypass (Fail Safe)
1. **What is it?**: Fail-Open logic in error exception handling.
2. **Where is it in the code?**: `app.py` inside `edit_student()` (`line 120`).
3. **Why does it happen?**: The `except` block catches an intentional `KeyError` and sets `access_granted = True`.
4. **How to validate it?**: Trigger an exception during execution; notice access is granted rather than denied.
5. **Principle violated**: Fail Safe (Deny by Default).
6. **Impact**: System errors or unexpected exceptions lead to privilege escalation.
7. **How to fix it?**: Set `access_granted = False` inside error handling blocks and return 500/403.
8. **Why does the fix work?**: Ensures that if a security verification fails or throws an unexpected error, access remains strictly denied.
9. **Alternative fix**: Centralized error middleware that catches unhandled errors and returns an HTTP 500 error page without executing the action.
10. **Examiner follow-up question**: *"What does 'Fail-Safe' mean in software engineering?"* -> **Answer**: Systems should default to a secure, safe state (denying access) whenever an unexpected failure or exception occurs.

---

### Vulnerability 5: Self-Approved Student Records (Segregation of Duties)
1. **What is it?**: Lack of multi-person control over sensitive workflow state changes.
2. **Where is it in the code?**: `app.py` in `create_student()` (`line 104`).
3. **Why does it happen?**: The database query directly sets `approved = 1` during creation by a teacher.
4. **How to validate it?**: Log in as `teacher`, create a student, and observe `approved` status is immediately `1`.
5. **Principle violated**: Segregation of Duties.
6. **Impact**: Malicious or accidental insertion of unverified academic records without supervisor review.
7. **How to fix it?**: Insert records with `approved = 0`, requiring an `admin` user to execute a separate `/approve/<id>` route.
8. **Why does the fix work?**: Forces two separate authorization steps by two distinct user roles.
9. **Alternative fix**: Implement dual-authorization audit logging and approval queues.
10. **Examiner follow-up question**: *"Where is Segregation of Duties critical in real-world software?"* -> **Answer**: Financial transactions (wire transfers), grade approvals, deployment pipelines, and access grant requests.

---

### Vulnerability 6: Broken Object Level Authorization / IDOR (Segmentation)
1. **What is it?**: Insecure Direct Object Reference (IDOR) allowing cross-account data leaks.
2. **Where is it in the code?**: `app.py` in `view_student()` (`line 90`).
3. **Why does it happen?**: The route fetches student data purely based on URL parameter `id` without checking if `session['user_id']` owns that record.
4. **How to validate it?**: Log in as student 1, navigate to `/student/2`, and view student 2's details.
5. **Principle violated**: Segmentation (Data Isolation).
6. **Impact**: Exposure of private data belonging to all users across tenant boundaries.
7. **How to fix it?**: Verify `if session['role'] == 'student' and session['user_id'] != student_id: return 403`.
8. **Why does the fix work?**: Enforces strict horizontal access control boundaries between users.
9. **Alternative fix**: Use non-sequential random UUIDs instead of auto-incrementing integer IDs and map requests to logged-in user tokens.
10. **Examiner follow-up question**: *"Why are auto-incrementing database IDs risky?"* -> **Answer**: They are easily guessable and enumerable, making IDOR vulnerabilities trivial to exploit.

---

### Vulnerability 7: Excessive Sensitive PII Collection (Minimization)
1. **What is it?**: Storing and exposing personally identifiable information (PII) beyond application scope.
2. **Where is it in the code?**: `app.py` schema (`init_db`) and `student.html`.
3. **Why does it happen?**: Fields `ssn_or_passport` and `home_address` were added without a valid business requirement.
4. **How to validate it?**: View any student record; note full SSN and address details displayed.
5. **Principle violated**: Minimization (Data Minimization).
6. **Impact**: Increased privacy violation risk and regulatory compliance breach (e.g. GDPR) during a data leak.
7. **How to fix it?**: Remove `ssn_or_passport` and `home_address` columns from database schema and UI.
8. **Why does the fix work?**: Data that is not collected or stored cannot be compromised.
9. **Alternative fix**: Mask or encrypt sensitive attributes and restrict viewing to authorized compliance officers.
10. **Examiner follow-up question**: *"What is the core idea of Data Minimization under GDPR?"* -> **Answer**: Collect only the personal data that is strictly necessary for specified, legitimate processing purposes.

---

### Vulnerability 8: Default Public Access on Record Creation (Secure by Default)
1. **What is it?**: Insecure initial configuration defaults.
2. **Where is it in the code?**: `app.py` in `create_student()` (`line 104`).
3. **Why does it happen?**: The `INSERT` query hardcodes `is_public = 1` for all new student records.
4. **How to validate it?**: Create a student record; observe that it is visible publicly by default.
5. **Principle violated**: Secure by Default.
6. **Impact**: Sensitive user data is publicly exposed unless the user manually finds and changes setting.
7. **How to fix it?**: Set default value `is_public = 0` (Private) upon creation.
8. **Why does the fix work?**: Ensures that resources start in a safe state and require explicit intent to broaden access.
9. **Alternative fix**: Enforce privacy policy configuration during resource initialization.
10. **Examiner follow-up question**: *"Give an example of Secure by Default in operating systems."* -> **Answer**: Disabling root remote SSH login by default or enabling host firewalls out of the box.

---

### Vulnerability 9: Secret URL Parameter for Delete Authorization (Keep It Open)
1. **What is it?**: Security through obscurity / hidden parameter authorization.
2. **Where is it in the code?**: `app.py` in `delete_student()` (`line 152`).
3. **Why does it happen?**: The code checks `if secret_key == 'hidden_admin_token'` instead of session role authorization.
4. **How to validate it?**: Append `?secret_key=hidden_admin_token` to delete URL as a normal student.
5. **Principle violated**: Keep It Open (Kerckhoffs's Principle).
6. **Impact**: Hardcoded secrets are easily discovered via source code leaks, browser history, or referrer logs.
7. **How to fix it?**: Replace secret string check with explicit session-based role authorization (`session['role'] == 'admin'`).
8. **Why does the fix work?**: Security relies on authenticated identity and permissions, not secret URL strings.
9. **Alternative fix**: Standard RBAC middleware and cryptographically signed session tokens.
10. **Examiner follow-up question**: *"What is Kerckhoffs's Principle?"* -> **Answer**: A system should be secure even if everything about the system (except the key) is public knowledge.

---

### Vulnerability 10: Tedious Security CAPTCHA Step (Usability)
1. **What is it?**: Excessive security friction leading to user non-compliance.
2. **Where is it in the code?**: `app.py` in `edit_student()` (`line 131`) and `student.html`.
3. **Why does it happen?**: Forcing the user to manually type `CONFIRM_SECURITY_CHECK_12345` on every single edit form submission.
4. **How to validate it?**: Attempt to submit an edit without typing the exact 25-character string.
5. **Principle violated**: Usability / Psychological Acceptability.
6. **Impact**: Frustrated users write browser scripts to bypass checks or share master admin credentials to avoid annoying friction.
7. **How to fix it?**: Remove fixed text re-entry; rely on session authentication and standard CSRF tokens.
8. **Why does the fix work?**: Provides strong background security without burdening the end user with repetitive friction.
9. **Alternative fix**: Risk-based authentication (only prompt re-authentication for high-risk sensitive operations).
10. **Examiner follow-up question**: *"How does poor security usability lead to security breaches?"* -> **Answer**: Users bypass inconvenient controls via unauthorized workarounds, password post-it notes, or automation scripts.

---

## 25 Essential Viva Questions & Concise Answers

1. **Q: What is the main goal of this security lab?**
   *A*: To demonstrate 10 fundamental cybersecurity principles and basic vulnerabilities (like SQLi and IDOR) in a simple, traceable Flask application for learning and defense analysis.

2. **Q: What is SQL Injection (SQLi)?**
   *A*: A vulnerability where untrusted user input is directly concatenated into database queries, allowing attackers to manipulate query structure and execute arbitrary SQL commands.

3. **Q: How does string concatenation cause SQL Injection?**
   *A*: It mixes SQL commands and user data together into a single string parser, allowing special SQL characters (like `'`, `--`, `OR`) in user input to alter statement logic.

4. **Q: Why do parameterized queries prevent SQL Injection?**
   *A*: Parameterized queries separate the query structure from the data parameters. The database treats input purely as literal values, never executable code.

5. **Q: What is Insecure Direct Object Reference (IDOR)?**
   *A*: An access control vulnerability occurring when an application uses user-supplied input (like database IDs in URLs) to access objects directly without verification.

6. **Q: Which security principle does IDOR violate?**
   *A*: **Segmentation** (or Data Isolation) and **Least Privilege**, because user boundaries are not enforced.

7. **Q: What is the Principle of Least Privilege?**
   *A*: Users and systems should be granted only the minimum level of access and permissions necessary to perform their legitimate job functions.

8. **Q: Give an example of Least Privilege violation in our app.**
   *A*: Allowing the `student` role to edit other student records on `/student/edit/<id>`.

9. **Q: What is Defense in Depth?**
   *A*: Layering multiple redundant security controls throughout an IT system so that if one layer fails, subsequent layers prevent a breach.

10. **Q: How does hiding a button violate Defense in Depth?**
    *A*: Hiding a button is only a UI convenience. The backend route must independently verify permissions, acting as a second security layer.

11. **Q: What is the Fail-Safe (Deny-by-Default) principle?**
    *A*: If a system control fails or encounters an exception, its safe state must be to deny access rather than grant it.

12. **Q: What is Segregation of Duties?**
    *A*: Dividing critical tasks among multiple individuals or roles to prevent fraud, error, or unauthorized self-approval.

13. **Q: Give an example of Segregation of Duties violation in our app.**
    *A*: A teacher creating a new grade record and setting `approved = 1` in a single step without supervisor sign-off.

14. **Q: What is Data Minimization?**
    *A*: Collecting, storing, and processing only the minimum personal data necessary to achieve a specific, legitimate purpose.

15. **Q: Why is storing SSN in our Student System a Minimization flaw?**
    *A*: High-risk PII like SSNs are not required for basic student management and increase exposure risk during data breaches.

16. **Q: What does Secure by Default mean?**
    *A*: Default settings of a system should provide the highest level of security out of the box, requiring explicit action to lower security.

17. **Q: Give an example of Secure by Default in web application design.**
    *A*: Setting user profile visibility or new files to "Private" by default instead of "Public".

18. **Q: What is Kerckhoffs's Principle / Keep It Open?**
    *A*: A system should remain secure even if its design and source code are entirely public; security must not rely on keeping mechanism details secret.

19. **Q: Why is "Security through Obscurity" dangerous?**
    *A*: Hidden parameters or URLs can easily be reverse-engineered, leaked in logs, or guessed, leaving the system completely exposed.

20. **Q: How does Usability impact Security?**
    *A*: Complex or overly tedious security controls frustrate users, causing them to create unsafe workarounds that bypass security entirely.

21. **Q: What is Keep It Simple & Straight (KISS) in secure design?**
    *A*: Unnecessary complexity in software architecture creates hidden edge cases, bugs, and audit difficulties where security flaws can hide.

22. **Q: What is the purpose of Flask's `session` object?**
    *A*: It stores cryptographically signed user data in client cookies, preserving state (like logged-in user identity and role) across HTTP requests.

23. **Q: Why is `app.secret_key` critical in Flask?**
    *A*: It signs session cookies to prevent users from tampering with cookie values (like changing `role` from `student` to `admin`).

24. **Q: What HTTP status code should be returned when authorization fails?**
    *A*: **HTTP 403 Forbidden** (or 401 Unauthorized if unauthenticated).

25. **Q: How can we summarize the vulnerability identification process for a viva?**
    *A*: Trace request execution from Browser -> Route -> Input -> Database -> Response, checking at each step for missing validation, missing authorization, and insecure defaults.

---

# Code Walkthrough

Below is the execution flow of `app.py` in chronological order:

### 1. Imports (`lines 1–2`)
Import Flask modules for web routing (`Flask`), parameter extraction (`request`), template rendering (`render_template`), redirecting (`redirect`), session management (`session`), and SQLite driver (`sqlite3`).

### 2. Flask Initialization & Database Helper (`lines 4–11`)
- Creates Flask application instance `app`.
- Defines `get_db()` helper to establish connection to `database.db` and set `row_factory = sqlite3.Row` for dictionary-like column access.

### 3. Database Initialization (`lines 13–50`)
- `init_db()` executes table creation SQL for `users` and `students`.
- Inserts dummy data (`admin`, `teacher`, `student`) if table is empty.
- *Security Flaw*: Schema includes non-essential sensitive fields (`ssn_or_passport`, `home_address`), violating **Minimization**.

### 4. Login Route (`/login` - `lines 54–69`)
- **HTTP**: `POST /login`
- **Data**: Form parameters `username` and `password`.
- **Query**: `SELECT * FROM users WHERE username = ? AND password = ?`
- **Logic**: Validates credentials. On success, populates `session['user_id']`, `session['username']`, and `session['role']`.

### 5. Session Handling & Dashboard (`/dashboard` - `lines 71–82`)
- **HTTP**: `GET /dashboard`
- **Logic**: Checks `if 'user_id' not in session: return redirect('/login')`. Fetches all student records from DB and passes them to `dashboard.html`.

### 6. Search Route (`/search` - `lines 84–95`)
- **HTTP**: `GET /search?q=input`
- **Query**: `SELECT * FROM students WHERE name LIKE '%{q}%'`
- **Vulnerability**: Direct string formatting of `q` allows **SQL Injection**.

### 7. Student Profile Lookup (`/student/<id>` - `lines 97–109`)
- **HTTP**: `GET /student/1`
- **Query**: `SELECT * FROM students WHERE id = 1`
- **Vulnerability**: **Segmentation / IDOR** (no user boundary verification) and **Minimization** (displays SSN & Address).

### 8. Creating Students (`/student/create` - `lines 111–131`)
- **HTTP**: `POST /student/create`
- **Query**: `INSERT INTO students (...) VALUES (?, ?, ?, ?, 1, 1)`
- **Vulnerability**: **Secure by Default** (`is_public=1`), **Segregation of Duties** (`approved=1`), and **Minimization** (collects SSN/address).

### 9. Editing Students (`/student/edit/<id>` - `lines 133–161`)
- **HTTP**: `POST /student/edit/1`
- **Vulnerability**: **Fail Safe** (try-except exception defaults to access granted), **Least Privilege** (no role authorization check), and **Usability** (forces typing `CONFIRM_SECURITY_CHECK_12345`).

### 10. Deleting Students (`/student/delete/<id>` - `lines 163–178`)
- **HTTP**: `GET /student/delete/1?secret_key=hidden_admin_token`
- **Vulnerability**: **Defense in Depth** (UI hides link but backend accepts all calls) and **Keep It Open** (checks secret URL key instead of proper role authentication).
