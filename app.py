from flask import Flask, request, redirect, url_for, session, render_template_string
import sqlite3
import hashlib

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

DB = "finance.db"


# ================= DATABASE =================

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = db()

    con.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS income(
            user_id INTEGER PRIMARY KEY,
            annual_income REAL
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS expenses(
            user_id INTEGER,
            month INTEGER,
            monthly_income REAL,
            rent REAL,
            electricity REAL,
            medical REAL,
            travel REAL,
            others REAL,
            PRIMARY KEY(user_id, month)
        )
    """)

    con.commit()
    con.close()


def password_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ================= TAX CALCULATION =================

def calculate_tax(income):

    tax = 0

    if income > 400000:
        tax += (min(income, 800000) - 400000) * 0.05

    if income > 800000:
        tax += (min(income, 1200000) - 800000) * 0.10

    if income > 1200000:
        tax += (min(income, 1600000) - 1200000) * 0.15

    if income > 1600000:
        tax += (min(income, 2000000) - 1600000) * 0.20

    if income > 2000000:
        tax += (min(income, 2400000) - 2000000) * 0.25

    if income > 2400000:
        tax += (income - 2400000) * 0.30

    rebate = income <= 1200000

    if rebate:
        tax = 0

    cess = tax * 0.04

    total_tax = tax + cess

    return tax, cess, total_tax, rebate


# ================= DESIGN =================

BASE = """
<!DOCTYPE html>
<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1">

<title>Personal Finance Calculator</title>

<style>

body{
    font-family:Arial,sans-serif;
    background:#f2f5f9;
    margin:0;
    padding:15px;
}

.box{
    max-width:650px;
    margin:auto;
    background:white;
    padding:25px;
    border-radius:20px;
    box-shadow:0 4px 18px #ccc;
}

h1{
    text-align:center;
    font-size:32px;
}

h2{
    margin-top:25px;
}

.nav{
    display:flex;
    gap:10px;
    margin:20px 0;
}

.nav button{
    flex:1;
    padding:14px 5px;
    border:none;
    border-radius:10px;
    background:#eeeeee;
    color:#111;
    font-size:17px;
    cursor:pointer;
}

.nav button:hover{
    background:#dddddd;
}

input,select{
    width:100%;
    box-sizing:border-box;
    padding:14px;
    margin:7px 0;
    border:1px solid #bbb;
    border-radius:10px;
    font-size:16px;
}

.main-button{
    width:100%;
    padding:15px;
    margin:10px 0;
    background:#1769e0;
    color:white;
    border:none;
    border-radius:10px;
    font-size:17px;
    font-weight:bold;
}

.result{
    background:#eef6ff;
    padding:18px;
    margin-top:18px;
    border-radius:12px;
}

.saved{
    background:#e8f7e8;
    padding:18px;
    margin-top:18px;
    border-radius:12px;
}

table{
    width:100%;
    border-collapse:collapse;
    margin-top:15px;
    font-size:12px;
}

th,td{
    border:1px solid #ccc;
    padding:8px;
    text-align:center;
}

.logout{
    background:#eeeeee;
}

</style>

</head>

<body>

<div class="box">

{{ body|safe }}

</div>

</body>

</html>
"""


# ================= HOME =================

@app.route("/")
def home():

    if "user_id" in session:
        return redirect(url_for("income"))

    return redirect(url_for("login"))


# ================= REGISTER =================

@app.route("/register", methods=["GET", "POST"])
def register():

    message = ""

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        try:

            con = db()

            con.execute(
                """
                INSERT INTO users(username,password)
                VALUES(?,?)
                """,
                (username, password_hash(password))
            )

            con.commit()
            con.close()

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            message = "User ID already exists."

    body = f"""

    <h1>CREATE ACCOUNT</h1>

    <p>{message}</p>

    <form method="POST">

        <input
        name="username"
        placeholder="Create User ID"
        required>

        <input
        name="password"
        type="password"
        placeholder="Create Password"
        required>

        <button class="main-button">
        CREATE ACCOUNT
        </button>

    </form>

    <button
    class="main-button"
    onclick="location.href='/login'">
    LOGIN
    </button>

    """

    return render_template_string(
        BASE,
        body=body
    )


# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():

    message = ""

    if request.method == "POST":

        username = request.form["username"]
        password = password_hash(
            request.form["password"]
        )

        con = db()

        user = con.execute(
            """
            SELECT * FROM users
            WHERE username=? AND password=?
            """,
            (username, password)
        ).fetchone()

        con.close()

        if user:

            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return redirect(
                url_for("income")
            )

        message = "Invalid User ID or Password."

    body = f"""

    <h1>🔐 LOGIN</h1>

    <p>{message}</p>

    <form method="POST">

        <input
        name="username"
        placeholder="User ID"
        required>

        <input
        name="password"
        type="password"
        placeholder="Password"
        required>

        <button class="main-button">
        LOGIN
        </button>

    </form>

    <button
    class="main-button"
    onclick="location.href='/register'">
    CREATE NEW ACCOUNT
    </button>

    """

    return render_template_string(
        BASE,
        body=body
    )


# ================= NAVIGATION =================

def navigation():

    return """

    <div class="nav">

        <button onclick="location.href='/income'">
        💰 Income
        </button>

        <button onclick="location.href='/expenses'">
        📊 Expenditure
        </button>

        <button onclick="location.href='/logout'">
        Logout
        </button>

    </div>

    """


# ================= INCOME PAGE =================

@app.route("/income", methods=["GET", "POST"])
def income():

    if "user_id" not in session:
        return redirect(url_for("login"))

    con = db()

    saved = con.execute(
        """
        SELECT annual_income
        FROM income
        WHERE user_id=?
        """,
        (session["user_id"],)
    ).fetchone()

    result = ""

    if request.method == "POST":

        annual_income = float(
            request.form["annual_income"]
        )

        con.execute(
            """
            INSERT OR REPLACE INTO income
            VALUES(?,?)
            """,
            (
                session["user_id"],
                annual_income
            )
        )

        con.commit()

        tax, cess, total_tax, rebate = calculate_tax(
            annual_income
        )

        monthly_after_tax = (
            annual_income - total_tax
        ) / 12

        result = f"""

        <div class="result">

        <h2>Tax Calculation</h2>

        <p>
        Annual Income:
        <b>₹{annual_income:,.2f}</b>
        </p>

        <p>
        Tax:
        <b>₹{tax:,.2f}</b>
        </p>

        <p>
        Section 87A:
        <b>
        {"Applied" if rebate else "Not Applied"}
        </b>
        </p>

        <p>
        4% Cess:
        <b>₹{cess:,.2f}</b>
        </p>

        <h2>
        Total Tax:
        ₹{total_tax:,.2f}
        </h2>

        <h2>
        Monthly Income After Tax:
        ₹{monthly_after_tax:,.2f}
        </h2>

        </div>

        """

        saved = {
            "annual_income": annual_income
        }

    value = (
        saved["annual_income"]
        if saved else ""
    )

    con.close()

    body = f"""

    <h1>💰 INCOME</h1>

    <p>
    Welcome,
    <b>{session["username"]}</b>
    </p>

    {navigation()}

    <form method="POST">

        <input
        name="annual_income"
        type="number"
        value="{value}"
        placeholder="ENTER ANNUAL INCOME (₹)"
        required>

        <button class="main-button">
        CALCULATE TAX
        </button>

    </form>

    {result}

    """

    return render_template_string(
        BASE,
        body=body
    )


# ================= EXPENDITURE PAGE =================

@app.route("/expenses", methods=["GET", "POST"])
def expenses():

    if "user_id" not in session:
        return redirect(url_for("login"))

    months = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December"
    ]

    con = db()

    saved_result = ""

    if request.method == "POST":

        month = int(
            request.form["month"]
        )

        monthly_income = float(
            request.form.get(
                "monthly_income", 0
            ) or 0
        )

        rent = float(
            request.form.get(
                "rent", 0
            ) or 0
        )

        electricity = float(
            request.form.get(
                "electricity", 0
            ) or 0
        )

        medical = float(
            request.form.get(
                "medical", 0
            ) or 0
        )

        travel = float(
            request.form.get(
                "travel", 0
            ) or 0
        )

        others = float(
            request.form.get(
                "others", 0
            ) or 0
        )

        total_expenses = (
            rent +
            electricity +
            medical +
            travel +
            others
        )

        saved_money = (
            monthly_income -
            total_expenses
        )

        con.execute(
            """
            INSERT OR REPLACE INTO expenses
            VALUES(?,?,?,?,?,?,?,?)
            """,
            (
                session["user_id"],
                month,
                monthly_income,
                rent,
                electricity,
                medical,
                travel,
                others
            )
        )

        con.commit()

        saved_result = f"""

        <div class="saved">

        <h2>💰 Monthly Summary</h2>

        <p>
        Monthly Income:
        <b>₹{monthly_income:,.2f}</b>
        </p>

        <p>
        Total Expenditure:
        <b>₹{total_expenses:,.2f}</b>
        </p>

        <h2>
        Saved Money:
        ₹{saved_money:,.2f}
        </h2>

        </div>

        """

    rows = con.execute(
        """
        SELECT *
        FROM expenses
        WHERE user_id=?
        ORDER BY month
        """,
        (session["user_id"],)
    ).fetchall()

    con.close()

    data = {
        row["month"]: row
        for row in rows
    }

    options = ""

    for i in range(1, 13):

        options += f"""

        <option value="{i}">
        {months[i-1]}
        </option>

        """

    table = """

    <table>

    <tr>
        <th>Month</th>
        <th>Income</th>
        <th>Rent</th>
        <th>Electricity</th>
        <th>Medical</th>
        <th>Travel</th>
        <th>Others</th>
        <th>Saved</th>
    </tr>

    """

    for i in range(1, 13):

        row = data.get(i)

        if row:

            expenses_total = (
                row["rent"] +
                row["electricity"] +
                row["medical"] +
                row["travel"] +
                row["others"]
            )

            saved = (
                row["monthly_income"] -
                expenses_total
            )

            table += f"""

            <tr>

            <td>{months[i-1]}</td>

            <td>
            ₹{row["monthly_income"]:.0f}
            </td>

            <td>
            ₹{row["rent"]:.0f}
            </td>

            <td>
            ₹{row["electricity"]:.0f}
            </td>

            <td>
            ₹{row["medical"]:.0f}
            </td>

            <td>
            ₹{row["travel"]:.0f}
            </td>

            <td>
            ₹{row["others"]:.0f}
            </td>

            <td>
            ₹{saved:.0f}
            </td>

            </tr>

            """

    table += "</table>"

    body = f"""

    <h1>📊 EXPENDITURE</h1>

    <p>
    Private records for:
    <b>{session["username"]}</b>
    </p>

    {navigation()}

    <form method="POST">

        <select name="month">

        {options}

        </select>

        <input
        name="monthly_income"
        type="number"
        placeholder="MONTHLY INCOME (₹)"
        required>

        <input
        name="rent"
        type="number"
        placeholder="Home Rent (₹)">

        <input
        name="electricity"
        type="number"
        placeholder="Electricity (₹)">

        <input
        name="medical"
        type="number"
        placeholder="Hospital / Medical (₹)">

        <input
        name="travel"
        type="number"
        placeholder="Travelling (₹)">

        <input
        name="others"
        type="number"
        placeholder="Others (₹)">

        <button class="main-button">
        SAVE MONTH
        </button>

    </form>

    {saved_result}

    <h2>
    Saved Monthly Expenditure
    </h2>

    {table}

    """

    return render_template_string(
        BASE,
        body=body
    )


# ================= LOGOUT =================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ================= START =================

init_db()

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )
