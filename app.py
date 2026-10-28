
from flask import Flask, request, redirect, url_for, session, render_template_string
import os
import psycopg2
from decimal import Decimal, InvalidOperation
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")
DATABASE_URL = os.environ.get("DATABASE_URL")

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
YEARS = list(range(2023, 2031))

CATEGORIES = [
    ("rent", "Home Rent"),
    ("electricity", "Electricity"),
    ("medical", "Hospital / Medical"),
    ("travel", "Travelling"),
    ("food", "Food"),
    ("shopping", "Shopping"),
    ("education", "Education"),
    ("mobile", "Mobile / Internet"),
    ("entertainment", "Entertainment"),
    ("others", "Others")
]

def get_db():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable is missing.")
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            year INTEGER NOT NULL DEFAULT 2026,
            month VARCHAR(20) NOT NULL,
            monthly_income NUMERIC DEFAULT 0,
            rent NUMERIC DEFAULT 0,
            electricity NUMERIC DEFAULT 0,
            medical NUMERIC DEFAULT 0,
            travel NUMERIC DEFAULT 0,
            food NUMERIC DEFAULT 0,
            shopping NUMERIC DEFAULT 0,
            education NUMERIC DEFAULT 0,
            mobile NUMERIC DEFAULT 0,
            entertainment NUMERIC DEFAULT 0,
            others NUMERIC DEFAULT 0,
            saved_money NUMERIC DEFAULT 0,
            UNIQUE(user_id, year, month)
        )
    """)

    cur.execute("""
        ALTER TABLE expenses
        ADD COLUMN IF NOT EXISTS year INTEGER DEFAULT 2026
    """)

    conn.commit()
    cur.close()
    conn.close()

STYLE = """
<style>
*{box-sizing:border-box}
body{font-family:Arial,sans-serif;background:#f3f6fb;color:#222;margin:0;padding:12px}
.container{max-width:1100px;margin:auto}
.card{background:white;padding:22px;border-radius:14px;margin-bottom:18px;box-shadow:0 3px 15px #00000010}
h1,h2,h3{text-align:center}
label{display:block;font-weight:bold;margin-top:12px}
input,select{width:100%;padding:12px;border:1px solid #ccd2dc;border-radius:8px;margin:7px 0;font-size:16px}
button,.btn{display:inline-block;padding:12px 16px;background:#2563eb;color:white;border:0;border-radius:8px;text-decoration:none;cursor:pointer;margin:4px}
.green{background:#16a34a}.red{background:#dc2626}.gray{background:#555}.orange{background:#d97706}
.center{text-align:center}.message{background:#eef6ff;padding:12px;border-radius:8px;margin:10px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}
.stat{background:#f7f9fc;padding:15px;border-radius:10px;text-align:center;overflow-wrap:anywhere}
.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;min-width:900px;background:white}
th,td{padding:9px;border:1px solid #ddd;text-align:center}
th{background:#eef2ff}
@media(max-width:600px){body{padding:8px}.card{padding:14px}}
</style>
"""

def page(title, body, **kwargs):
    template = """
    <!doctype html>
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>{{ title }}</title>
      {{ style|safe }}
    </head>
    <body><div class="container">
    <div class="card">
      <div style="text-align:right">
        <a href="/language/English">English</a> |
        <a href="/language/Telugu">తెలుగు</a> |
        <a href="/language/Hindi">हिंदी</a>
      </div>
    </div>
    """ + body + """
    </div></body></html>
    """
    return render_template_string(
        template, title=title, style=STYLE, **kwargs
    )

def logged_in():
    return "user_id" in session

def parse_amount(value):
    amount = Decimal(value or "0")
    if not amount.is_finite() or amount < 0:
        raise ValueError("Invalid amount")
    return amount

def fmt(value):
    return "{:,.2f}".format(float(value or 0))

# ---------------- DATABASE LOGIN / REGISTER ----------------

@app.route("/")
def home():
    return redirect(url_for("dashboard" if logged_in() else "login"))

@app.route("/language/<lang>")
def language(lang):
    if lang in ("English", "Telugu", "Hindi"):
        session["lang"] = lang
    return redirect(request.referrer or url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    message = ""

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            message = "Enter username and password."
        else:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE username=%s", (username,))
            exists = cur.fetchone()

            if exists:
                message = "Username already exists."
            else:
                cur.execute(
                    "INSERT INTO users(username,password_hash) VALUES(%s,%s)",
                    (username, generate_password_hash(password))
                )
                conn.commit()
                cur.close()
                conn.close()
                return redirect(url_for("login"))

            cur.close()
            conn.close()

    body = """
    <div class="card">
      <h2>Create Account</h2>
      {% if message %}<div class="message">{{ message }}</div>{% endif %}
      <form method="post">
        <label>Username</label>
        <input name="username" maxlength="100" required>
        <label>Password</label>
        <input type="password" name="password" required>
        <button>Create Account</button>
      </form>
      <a class="btn gray" href="/login">Login</a>
    </div>
    """
    return page("Register", body, message=message)

@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT id,password_hash FROM users WHERE username=%s",
            (username,)
        )
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user[1], password):
            session.clear()
            session["user_id"] = user[0]
            session["username"] = username
            return redirect(url_for("dashboard"))

        message = "Invalid username or password."

    body = """
    <div class="card">
      <h2>Login</h2>
      {% if message %}<div class="message">{{ message }}</div>{% endif %}
      <form method="post">
        <label>Username</label>
        <input name="username" required>
        <label>Password</label>
        <input type="password" name="password" required>
        <button>Login</button>
      </form>
      <a class="btn green" href="/register">Create Account</a>
    </div>
    """
    return page("Login", body, message=message)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if not logged_in():
        return redirect(url_for("login"))

    body = """
    <div class="card center">
      <h2>Welcome, {{ username }}</h2>
      <div class="grid">
        <a class="btn" href="/income">💰 Income Tax Calculator</a>
        <a class="btn green" href="/expenses">📊 Expenditure</a>
      </div>
      <a class="btn red" href="/logout">Logout</a>
    </div>
    """
    return page("Dashboard", body, username=session["username"])

# ---------------- INCOME TAX CALCULATOR ----------------

def calculate_tax(income):
    # Decimal is used throughout to prevent Decimal/float errors.
    if income <= Decimal("400000"):
        tax = Decimal("0")
        slab = "Income up to ₹4,00,000: 0%"
        explanation = "Tax = ₹0"
    elif income <= Decimal("800000"):
        tax = (income - Decimal("400000")) * Decimal("0.05")
        slab = "₹4,00,001–₹8,00,000: 5%"
        explanation = (
            "Tax = (Annual income − ₹4,00,000) × 5%"
        )
    elif income <= Decimal("1200000"):
        tax = Decimal("20000") + (
            income - Decimal("800000")
        ) * Decimal("0.10")
        slab = "₹8,00,001–₹12,00,000: 10% on excess"
        explanation = (
            "Tax = ₹20,000 + (Annual income − ₹8,00,000) × 10%"
        )
    elif income <= Decimal("1600000"):
        tax = Decimal("60000") + (
            income - Decimal("1200000")
        ) * Decimal("0.15")
        slab = "₹12,00,001–₹16,00,000: 15% on excess"
        explanation = (
            "Tax = ₹60,000 + (Annual income − ₹12,00,000) × 15%"
        )
    elif income <= Decimal("2000000"):
        tax = Decimal("120000") + (
            income - Decimal("1600000")
        ) * Decimal("0.20")
        slab = "₹16,00,001–₹20,00,000: 20% on excess"
        explanation = (
            "Tax = ₹1,20,000 + (Annual income − ₹16,00,000) × 20%"
        )
    elif income <= Decimal("2400000"):
        tax = Decimal("200000") + (
            income - Decimal("2000000")
        ) * Decimal("0.25")
        slab = "₹20,00,001–₹24,00,000: 25% on excess"
        explanation = (
            "Tax = ₹2,00,000 + (Annual income − ₹20,00,000) × 25%"
        )
    else:
        tax = Decimal("300000") + (
            income - Decimal("2400000")
        ) * Decimal("0.30")
        slab = "Above ₹24,00,000: 30% on excess"
        explanation = (
            "Tax = ₹3,00,000 + (Annual income − ₹24,00,000) × 30%"
        )

    return tax, slab, explanation

@app.route("/income", methods=["GET", "POST"])
def income():
    if not logged_in():
        return redirect(url_for("login"))

    result = None
    error = ""

    if request.method == "POST":
        try:
            annual_income = parse_amount(
                request.form.get("annual_income", "")
            )
            tax, slab, explanation = calculate_tax(annual_income)

            result = {
                "income": annual_income,
                "tax": tax,
                "monthly": (annual_income - tax) / Decimal("12"),
                "slab": slab,
                "explanation": explanation
            }
        except (ValueError, InvalidOperation):
            error = "Please enter a valid non-negative income."

    body = """
    <div class="card">
      <h2>INCOME TAX CALCULATOR</h2>
      {% if error %}<div class="message">{{ error }}</div>{% endif %}
      <form method="post">
        <label>ENTER ANNUAL INCOME (₹)</label>
        <input type="number" min="0" step="0.01"
               name="annual_income"
               value="{{ request.form.get('annual_income','') }}" required>
        <button type="submit">Calculate Tax</button>
      </form>
    </div>

    {% if result %}
    <div class="card">
      <div class="stat">
        <h2>Tax = ₹{{ '{:,.2f}'.format(result.tax) }}</h2>
      </div>

      <div class="grid">
        <div class="stat">
          <b>Annual Income</b>
          <h3>₹{{ '{:,.2f}'.format(result.income) }}</h3>
        </div>
        <div class="stat">
          <b>Monthly Income After Tax</b>
          <h3>₹{{ '{:,.2f}'.format(result.monthly) }}</h3>
        </div>
      </div>

      <h2>How was tax calculated?</h2>
      <p><b>Annual income:</b> ₹{{ '{:,.2f}'.format(result.income) }}</p>
      <p><b>Applicable slab:</b> {{ result.slab }}</p>
      <p>{{ result.explanation }}</p>
      <p><b>Total tax: ₹{{ '{:,.2f}'.format(result.tax) }}</b></p>
    </div>
    {% endif %}

    <div class="center">
      <a class="btn gray" href="/dashboard">Back to Dashboard</a>
    </div>
    """
    return page("Income Tax Calculator", body, result=result, error=error)

# ---------------- EXPENDITURE MANAGEMENT ----------------

def fetch_expenses(year):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, year, month, monthly_income, rent, electricity,
               medical, travel, food, shopping, education, mobile,
               entertainment, others
        FROM expenses
        WHERE user_id=%s AND year=%s
        ORDER BY array_position(
            %s::varchar[], month
        )
    """, (session["user_id"], year, MONTHS))

    records = cur.fetchall()
    cur.close()
    conn.close()

    rows = []
    for r in records:
        row = {
            "id": r[0], "year": r[1], "month": r[2],
            "monthly_income": Decimal(str(r[3] or 0))
        }
        for i, (key, _) in enumerate(CATEGORIES, start=4):
            row[key] = Decimal(str(r[i] or 0))

        row["total_expense"] = sum(
            (row[key] for key, _ in CATEGORIES), Decimal("0")
        )
        row["saved_money"] = row["monthly_income"] - row["total_expense"]
        rows.append(row)

    return rows

@app.route("/expenses", methods=["GET", "POST"])
def expenses():
    if not logged_in():
        return redirect(url_for("login"))

    message = request.args.get("message", "")
    error = ""
    try:
        selected_year = int(request.values.get("year", "2026"))
        if selected_year not in YEARS:
            selected_year = 2026
    except ValueError:
        selected_year = 2026

    if request.method == "POST":
        conn = None
        cur = None
        try:
            year = int(request.form.get("year", "2026"))
            month = request.form.get("month", "")

            if year not in YEARS or month not in MONTHS:
                raise ValueError("Invalid year or month")

            monthly_income = parse_amount(
                request.form.get("monthly_income", "")
            )
            amounts = {
                key: parse_amount(request.form.get(key, ""))
                for key, _ in CATEGORIES
            }
            total_expenses = sum(amounts.values(), Decimal("0"))
            saved = monthly_income - total_expenses

            conn = get_db()
            cur = conn.cursor()

            columns = (
                ["user_id", "year", "month", "monthly_income"]
                + [key for key, _ in CATEGORIES]
                + ["saved_money"]
            )
            placeholders = ", ".join(["%s"] * len(columns))
            updates = (
                ["monthly_income=EXCLUDED.monthly_income"]
                + [f"{key}=EXCLUDED.{key}" for key, _ in CATEGORIES]
                + ["saved_money=EXCLUDED.saved_money"]
            )
            values = (
                [session["user_id"], year, month, monthly_income]
                + [amounts[key] for key, _ in CATEGORIES]
                + [saved]
            )

            cur.execute(
                f"""INSERT INTO expenses ({", ".join(columns)})
                    VALUES ({placeholders})
                    ON CONFLICT (user_id, year, month)
                    DO UPDATE SET {", ".join(updates)}""",
                values
            )
            conn.commit()
            selected_year = year
            message = "Record saved successfully."

        except (ValueError, InvalidOperation):
            error = "Enter valid non-negative amounts."
        except Exception as exc:
            if conn:
                conn.rollback()
            error = "Could not save record. Check database configuration."
            print("Expense save error:", exc)
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    rows = fetch_expenses(selected_year)

    total_income = sum(
        (r["monthly_income"] for r in rows), Decimal("0")
    )
    total_expenses = sum(
        (r["total_expense"] for r in rows), Decimal("0")
    )
    total_savings = total_income - total_expenses

    category_totals = {
        key: sum((r[key] for r in rows), Decimal("0"))
        for key, _ in CATEGORIES
    }

    body = """
    <div class="card">
      <h2>MONTHLY EXPENDITURE</h2>
      {% if message %}<div class="message">{{ message }}</div>{% endif %}
      {% if error %}<div class="message">{{ error }}</div>{% endif %}

      <form method="post">
        <div class="grid">
          <div>
            <label>Year</label>
            <select name="year">
              {% for y in years %}
              <option value="{{ y }}" {% if y==selected_year %}selected{% endif %}>{{ y }}</option>
              {% endfor %}
            </select>
          </div>
          <div>
            <label>Month</label>
            <select name="month" required>
              {% for m in months %}
              <option value="{{ m }}">{{ m }}</option>
              {% endfor %}
            </select>
          </div>
          <div>
            <label>Monthly Income (₹)</label>
            <input type="number" min="0" step="0.01"
                   name="monthly_income" placeholder="Enter monthly income" required>
          </div>
          {% for key,label in categories %}
          <div>
            <label>{{ label }} (₹)</label>
            <input type="number" min="0" step="0.01"
                   name="{{ key }}" placeholder="Enter {{ label }} amount" required>
          </div>
          {% endfor %}
        </div>
        <button type="submit">Save Month</button>
      </form>
    </div>

    <div class="card">
      <form method="get">
        <label>Select Year</label>
        <select name="year">
          {% for y in years %}
          <option value="{{ y }}" {% if y==selected_year %}selected{% endif %}>{{ y }}</option>
          {% endfor %}
        </select>
        <button type="submit">View Records</button>
      </form>

      <h2>{{ selected_year }} Monthly Comparison</h2>
      {% if rows %}
      <div class="grid">
        <div class="stat"><b>Total Income</b><h3>₹{{ '{:,.2f}'.format(total_income) }}</h3></div>
        <div class="stat"><b>Total Expenditure</b><h3>₹{{ '{:,.2f}'.format(total_expenses) }}</h3></div>
        <div class="stat"><b>Total Savings</b><h3>₹{{ '{:,.2f}'.format(total_savings) }}</h3></div>
      </div>

      <h3>Saved Records</h3>
      <div class="table-wrap">
      <table>
        <tr>
          <th>Month</th><th>Income</th>
          {% for key,label in categories %}<th>{{ label }}</th>{% endfor %}
          <th>Total Expense</th><th>Saved</th><th>Actions</th>
        </tr>
        {% for r in rows %}
        <tr>
          <td>{{ r.month }}</td>
          <td>₹{{ '{:,.2f}'.format(r.monthly_income) }}</td>
          {% for key,label in categories %}
          <td>₹{{ '{:,.2f}'.format(r[key]) }}</td>
          {% endfor %}
          <td>₹{{ '{:,.2f}'.format(r.total_expense) }}</td>
          <td>₹{{ '{:,.2f}'.format(r.saved_money) }}</td>
          <td>
            <a class="btn orange" href="/expenses/edit/{{ r.id }}">Edit</a>
            <form method="post" action="/expenses/delete/{{ r.id }}"
                  onsubmit="return confirm('Delete this record?');">
              <button class="red">Delete</button>
            </form>
          </td>
        </tr>
        {% endfor %}
      </table>
      </div>

      <h3>Category-wise Yearly Expenses</h3>
      <div class="table-wrap">
      <table>
        <tr><th>Category</th><th>Total</th></tr>
        {% for key,label in categories %}
        <tr><td>{{ label }}</td><td>₹{{ '{:,.2f}'.format(category_totals[key]) }}</td></tr>
        {% endfor %}
      </table>
      </div>
      {% else %}
      <p class="center">No saved records for this year.</p>
      {% endif %}
    </div>

    <div class="center"><a class="btn gray" href="/dashboard">Back to Dashboard</a></div>
    """
    return page(
        "Expenditure", body, rows=rows, years=YEARS, months=MONTHS,
        categories=CATEGORIES, selected_year=selected_year,
        message=message, error=error, total_income=total_income,
        total_expenses=total_expenses, total_savings=total_savings,
        category_totals=category_totals
    )

@app.route("/expenses/edit/<int:record_id>", methods=["GET", "POST"])
def edit_expense(record_id):
    if not logged_in():
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, year, month, monthly_income, rent, electricity,
               medical, travel, food, shopping, education, mobile,
               entertainment, others
        FROM expenses WHERE id=%s AND user_id=%s
    """, (record_id, session["user_id"]))
    record = cur.fetchone()

    if not record:
        cur.close()
        conn.close()
        return redirect(url_for("expenses"))

    error = ""

    if request.method == "POST":
        try:
            year = int(request.form.get("year", "2026"))
            month = request.form.get("month", "")
            if year not in YEARS or month not in MONTHS:
                raise ValueError()

            monthly_income = parse_amount(request.form.get("monthly_income", ""))
            amounts = {
                key: parse_amount(request.form.get(key, ""))
                for key, _ in CATEGORIES
            }
            total = sum(amounts.values(), Decimal("0"))
            saved = monthly_income - total

            cur.execute("""
                UPDATE expenses SET
                    year=%s, month=%s, monthly_income=%s,
                    rent=%s, electricity=%s, medical=%s, travel=%s,
                    food=%s, shopping=%s, education=%s, mobile=%s,
                    entertainment=%s, others=%s, saved_money=%s
                WHERE id=%s AND user_id=%s
            """, (
                year, month, monthly_income,
                amounts["rent"], amounts["electricity"], amounts["medical"],
                amounts["travel"], amounts["food"], amounts["shopping"],
                amounts["education"], amounts["mobile"],
                amounts["entertainment"], amounts["others"],
                saved, record_id, session["user_id"]
            ))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for("expenses", year=year,
                                    message="Record updated successfully.")
                            )
        except (ValueError, InvalidOperation):
            error = "Enter valid amounts and select a valid year/month."
        except Exception as exc:
            conn.rollback()
            error = "Could not update. This month may already exist."
            print("Expense update error:", exc)

    cur.close()
    conn.close()

    data = {
        "id": record[0], "year": record[1], "month": record[2],
        "monthly_income": record[3]
    }
    for i, (key, _) in enumerate(CATEGORIES, start=4):
        data[key] = record[i]

    body = """
    <div class="card">
      <h2>Edit Monthly Record</h2>
      {% if error %}<div class="message">{{ error }}</div>{% endif %}
      <form method="post">
        <label>Year</label>
        <select name="year">
          {% for y in years %}
          <option value="{{ y }}" {% if y==data.year %}selected{% endif %}>{{ y }}</option>
          {% endfor %}
        </select>
        <label>Month</label>
        <select name="month">
          {% for m in months %}
          <option value="{{ m }}" {% if m==data.month %}selected{% endif %}>{{ m }}</option>
          {% endfor %}
        </select>
        <label>Monthly Income (₹)</label>
        <input type="number" min="0" step="0.01" name="monthly_income"
               value="{{ data.monthly_income }}" required>
        {% for key,label in categories %}
        <label>{{ label }} (₹)</label>
        <input type="number" min="0" step="0.01" name="{{ key }}"
               value="{{ data[key] }}" required>
        {% endfor %}
        <button>Update</button>
        <a class="btn gray" href="/expenses">Cancel</a>
      </form>
    </div>
    """
    return page("Edit Expense", body, data=data, error=error,
                years=YEARS, months=MONTHS, categories=CATEGORIES)

@app.route("/expenses/delete/<int:record_id>", methods=["POST"])
def delete_expense(record_id):
    if not logged_in():
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM expenses WHERE id=%s AND user_id=%s",
        (record_id, session["user_id"])
    )
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("expenses", message="Record deleted successfully."))

# ---------------- START APPLICATION ----------------

try:
    init_db()
except Exception as exc:
    print("Database initialization error:", exc)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
