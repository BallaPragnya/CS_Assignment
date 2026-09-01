from flask import Flask, request, render_template, redirect, session, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = "lab_secret_key_123"  # Fixed key for local educational testing

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            role TEXT
        )
    """)
    # VULNERABILITY (Minimization): Database schema includes non-essential sensitive fields
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            grade TEXT,
            ssn_or_passport TEXT,
            home_address TEXT,
            is_public INTEGER DEFAULT 1,
            approved INTEGER DEFAULT 0
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            [
                ("admin", "admin123", "admin"),
                ("teacher", "teacher123", "teacher"),
                ("student", "student123", "student")
            ]
        )
        cursor.executemany(
            "INSERT INTO students (name, grade, ssn_or_passport, home_address, is_public, approved) VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("Alice Smith", "A", "SSN-111-22-3333", "123 Main St", 1, 1),
                ("Bob Jones", "B", "SSN-444-55-6666", "456 Oak Ave", 1, 1),
                ("Charlie Brown", "C", "SSN-777-88-9999", "789 Pine Rd", 1, 1)
            ]
        )
        conn.commit()
    conn.close()

init_db()

# DEMONSTRATION (Keep It Simple & Straight): Linear request flow, no complex ORM or middleware

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
        conn.close()
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))
        return "Invalid Credentials", 401
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    students = conn.execute("SELECT * FROM students").fetchall()
    conn.close()
    return render_template("dashboard.html", students=students)

# VULNERABILITY (SQL Injection): Unsanitized string formatting directly in SQL query
@app.route("/search")
def search():
    if "user_id" not in session:
        return redirect(url_for("login"))
    q = request.args.get("q", "")
    conn = get_db()
    # Direct string concatenation allows SQL injection (e.g., ' OR '1'='1)
    query = f"SELECT * FROM students WHERE name LIKE '%{q}%'"
    students = conn.execute(query).fetchall()
    conn.close()
    return render_template("dashboard.html", students=students, query=q)

# VULNERABILITY (Segmentation / Minimization): IDOR + unnecessary PII exposure
@app.route("/student/<int:id>")
def view_student(id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    # VULNERABILITY (Segmentation): Any user can view record of any ID (no user boundary check)
    student = conn.execute("SELECT * FROM students WHERE id = ?", (id,)).fetchone()
    conn.close()
    if not student:
        return "Student not found", 404
    # VULNERABILITY (Minimization): Displays unnecessary SSN & Address fields
    return render_template("student.html", student=student, mode="view")

# VULNERABILITY (Secure by Default / Segregation of Duties / Minimization)
@app.route("/student/create", methods=["GET", "POST"])
def create_student():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        name = request.form.get("name")
        grade = request.form.get("grade")
        ssn = request.form.get("ssn_or_passport", "")  # VULNERABILITY (Minimization): Excessive PII collection
        address = request.form.get("home_address", "")
        
        conn = get_db()
        # VULNERABILITY (Secure by Default): Defaults to public (is_public=1) instead of restrictive default (0)
        # VULNERABILITY (Segregation of Duties): Creator immediately sets approved=1 without 2nd person verification
        conn.execute(
            "INSERT INTO students (name, grade, ssn_or_passport, home_address, is_public, approved) VALUES (?, ?, ?, ?, 1, 1)",
            (name, grade, ssn, address)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("dashboard"))
    return render_template("student.html", mode="create")

# VULNERABILITY (Least Privilege / Fail Safe / Usability)
@app.route("/student/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    # VULNERABILITY (Fail Safe): Error check defaults to allowing access on exception
    try:
        # Intentionally checking missing dictionary key to trigger exception
        required_role = session["non_existent_auth_key"]
    except Exception:
        # FAIL SAFE VIOLATION: Default-allow access on error instead of deny
        access_granted = True

    # VULNERABILITY (Least Privilege): No role check performed — student role can edit any record
    if request.method == "POST":
        # VULNERABILITY (Usability): Annoying re-entry of fixed CAPTCHA text causes security friction
        captcha = request.form.get("captcha_verification")
        if captcha != "CONFIRM_SECURITY_CHECK_12345":
            return "Security Check Failed: You must enter 'CONFIRM_SECURITY_CHECK_12345' exactly.", 400

        name = request.form.get("name")
        grade = request.form.get("grade")
        conn = get_db()
        conn.execute("UPDATE students SET name = ?, grade = ? WHERE id = ?", (name, grade, id))
        conn.commit()
        conn.close()
        return redirect(url_for("dashboard"))
        
    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (id,)).fetchone()
    conn.close()
    return render_template("student.html", student=student, mode="edit")

# VULNERABILITY (Defense in Depth / Keep It Open)
@app.route("/student/delete/<int:id>")
def delete_student(id):
    if "user_id" not in session:
        return redirect(url_for("login"))
        
    # VULNERABILITY (Keep It Open): Relies on secret hidden URL parameter instead of open RBAC authorization
    secret_key = request.args.get("secret_key")
    if secret_key != "hidden_admin_token":
        # VULNERABILITY (Defense in Depth): UI hides delete link from non-admins, but backend route proceeds regardless!
        pass

    conn = get_db()
    conn.execute("DELETE FROM students WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
