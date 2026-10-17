
from flask import (
    Flask, request, redirect, url_for, session,
    render_template_string, flash
)
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")

DATABASE_URL = os.environ.get("DATABASE_URL", "")

EXPENSES = [
    "House rent", "Electricity", "Medical / hospital",
    "Travel", "Food", "Shopping", "Education",
    "Mobile / internet", "Entertainment", "Others"
]

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

def get_db():
    if not DATABASE_URL:
        raise RuntimeError("Set DATABASE_URL in your Render environment variables.")
    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor,
        sslmode="require"
    )

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            year INTEGER NOT NULL,
            month VARCHAR(20) NOT NULL,
            monthly_income NUMERIC(14,2) DEFAULT 0,
            rent NUMERIC(14,2) DEFAULT 0,
            electricity NUMERIC(14,2) DEFAULT 0,
            medical NUMERIC(14,2) DEFAULT 0,
            travel NUMERIC(14,2) DEFAULT 0,
            food NUMERIC(14,2) DEFAULT 0,
            shopping NUMERIC(14,2) DEFAULT 0,
            education NUMERIC(14,2) DEFAULT 0,
            mobile NUMERIC(14,2) DEFAULT 0,
            entertainment NUMERIC(14,2) DEFAULT 0,
            others NUMERIC(14,2) DEFAULT 0,
            UNIQUE(user_id, year, month)
        )
    """)

    conn.commit()
    cur.close()
    conn.close()

def db_ready():
    try:
        init_db()
        return True
    except Exception:
        app.logger.exception("Database initialization failed")
        return False

def money(value):
    return float(value or 0)

def calculate_tax(income):
    """Illustrative slab calculation; no cess and no 87A rebate."""
    income = max(0, float(income))
    tax = 0

    slabs = [
        (400000, 0.00),
        (800000, 0.05),
        (1200000, 0.10),
        (1600000, 0.15),
        (2000000, 0.20),
        (2400000, 0.25),
        (float("inf"), 0.30)
    ]

    previous_limit = 0
    for limit, rate in slabs:
        taxable_amount = max(0, min(income, limit) - previous_limit)
        tax += taxable_amount * rate
        previous_limit = limit
        if income <= limit:
            break

    return round(tax, 2)

def expense_total(record):
    fields = [
        "rent", "electricity", "medical", "travel", "food",
        "shopping", "education", "mobile", "entertainment", "others"
    ]
    return sum(money(record.get(field)) for field in fields)

def current_user():
    return session.get("user_id")

BASE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Income Tax & Expenditure Manager</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#f0f5ff;color:#263247;
font-family:Arial,sans-serif;font-size:14px}
nav{background:#172650;color:white;padding:16px 4%;
display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
nav a{color:white;text-decoration:none;margin:0 5px}
.brand{font-size:16px;font-weight:bold}
main{max-width:1050px;margin:18px auto;padding:0 12px}
.card{background:white;border-radius:13px;padding:20px;margin-bottom:16px;
box-shadow:0 3px 12px #1726500a;overflow-wrap:anywhere}
h2{font-size:19px;margin:4px 0 18px}
h3{font-size:16px}
label{display:block;margin:12px 0 6px;color:#39465a}
input,select{width:100%;padding:11px;border:1px solid #d9dfe8;
border-radius:8px;background:white;color:#263247}
button,.btn{background:#2864db;color:white;border:0;border-radius:7px;
padding:10px 14px;cursor:pointer;text-decoration:none;display:inline-block}
button{margin-top:14px}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.stats{background:#eff5ff;padding:15px;border-radius:9px}
.amount{font-size:19px;font-weight:bold;margin-top:7px}
table{width:100%;border-collapse:collapse;margin-top:10px}
th,td{text-align:left;padding:10px 7px;border-bottom:1px solid #e6eaf0}
.small{font-size:12px;color:#778197}
.msg{padding:10px;background:#eaf3ff;border-radius:7px;margin:10px 0}
.actions{display:flex;gap:8px;flex-wrap:wrap}
.danger{background:#c43b46}
@media(max-width:650px){
 .grid{grid-template-columns:repeat(2,minmax(0,1fr))}
 nav{align-items:flex-start}
 nav .links{display:flex;flex-wrap:wrap;gap:10px}
 .card{padding:15px}
 table{font-size:12px}
 th,td{padding:8px 4px}
}
@media(max-width:400px){.grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<nav>
 <span class="brand">Income Tax & Expenditure Manager</span>
 <div class="links">
 {% if session.get('user_id') %}
 <a href="{{ url_for('income') }}">Income</a>
 <a href="{{ url_for('expenditure') }}">Expenditure</a>
 <a href="{{ url_for('logout') }}">Logout</a>
 {% endif %}
 <form method="get" style="display:inline">
 <select name="lang" onchange="this.form.submit()" style="width:auto;padding:7px">
 <option value="English" {% if lang=='English' %}selected{% endif %}>English</option>
 <option value="Telugu" {% if lang=='Telugu' %}selected{% endif %}>తెలుగు</option>
 <option value="Hindi" {% if lang=='Hindi' %}selected{% endif %}>हिन्दी</option>
 </select>
 </form>
 </div>
</nav>
<main>
{% with messages = get_flashed_messages() %}
 {% for message in messages %}
 <div class="msg">{{ message }}</div>
 {% endfor %}
{% endwith %}
{{ content|safe }}
</main>
</body>
</html>
"""

def page(content, **kwargs):
    return render_template_string(
        BASE, content=render_template_string(content, **kwargs),
        lang=request.values.get("lang", "English")
    )

@app.route("/")
def home():
    if current_user():
        return redirect(url_for("income"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Enter username and password.")
        else:
            try:
                conn = get_db()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO users(username,password) VALUES(%s,%s)",
                    (username, generate_password_hash(password))
                )
                conn.commit()
                cur.close()
                conn.close()
                flash("Registration successful. Please log in.")
                return redirect(url_for("login"))
            except psycopg2.IntegrityError:
                conn.rollback()
                cur.close()
                conn.close()
                flash("Username already exists.")
            except Exception:
                app.logger.exception("Registration failed")
                flash("Registration failed. Check your database settings.")

    content = """
    <section class="card">
    <h2>Create account</h2>
    <form method="post">
    <label>Username</label><input name="username" required>
    <label>Password</label><input type="password" name="password" required>
    <button type="submit">Register</button>
    </form>
    <p>Already registered? <a href="{{ url_for('login') }}">Login</a></p>
    </section>
    """
    return page(content)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username=%s", (username,))
            user = cur.fetchone()
            cur.close()
            conn.close()

            if user and check_password_hash(user["password"], password):
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                return redirect(url_for("income"))

            flash("Invalid username or password.")
        except Exception:
            app.logger.exception("Login failed")
            flash("Unable to connect to the database.")

    content = """
    <section class="card">
    <h2>Login</h2>
    <form method="post">
    <label>Username</label><input name="username" required>
    <label>Password</label><input type="password" name="password" required>
    <button type="submit">Login</button>
    </form>
    <p>New user? <a href="{{ url_for('register') }}">Create account</a></p>
    </section>
    """
    return page(content)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/income", methods=["GET", "POST"])
def income():
    if not current_user():
        return redirect(url_for("login"))

    tax = None
    income_amount = None

    if request.method == "POST":
        try:
            income_amount = float(request.form.get("income", ""))
            if income_amount < 0:
                raise ValueError
            tax = calculate_tax(income_amount)
        except (ValueError, TypeError):
            flash("Enter a valid non-negative annual income.")

    content = """
    <section class="card">
      <form method="post">
        <label>Annual income (₹)</label>
        <input type="number" name="income" min="0" step="0.01"
               placeholder="Enter annual income" required>
        <button type="submit">Calculate tax</button>
      </form>
    </section>

    {% if tax is not none %}
    <section class="card">
      <h2>Income tax result</h2>
      <div class="stats">
        <div>Annual income</div>
        <div class="amount">₹{{ "{:,.2f}".format(income_amount) }}</div>
      </div>
      <div class="stats" style="margin-top:12px">
        <div>Tax payable (illustrative)</div>
        <div class="amount">₹{{ "{:,.2f}".format(tax) }}</div>
      </div>
    </section>
    {% endif %}
    """
    return page(content, tax=tax, income_amount=income_amount)

@app.route("/expenditure", methods=["GET", "POST"])
def expenditure():
    if not current_user():
        return redirect(url_for("login"))

    uid = current_user()

    if request.method == "POST":
        try:
            year = int(request.form.get("year", "2026"))
            month = request.form.get("month", "January")
            if year < 2000 or year > 2100 or month not in MONTHS:
                raise ValueError

            monthly_income = float(request.form.get("monthly_income") or 0)
            if monthly_income < 0:
                raise ValueError

            values = {}
            field_map = {
                "rent": "rent",
                "electricity": "electricity",
                "medical": "medical",
                "travel": "travel",
                "food": "food",
                "shopping": "shopping",
                "education": "education",
                "mobile": "mobile",
                "entertainment": "entertainment",
                "others": "others"
            }

            for field in field_map:
                value = request.form.get(field, "").strip()
                amount = float(value) if value else 0
                if amount < 0:
                    raise ValueError
                values[field] = amount

            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO expenses (
                    user_id, year, month, monthly_income,
                    rent, electricity, medical, travel, food,
                    shopping, education, mobile, entertainment, others
                ) VALUES (
                    %(uid)s, %(year)s, %(month)s, %(income)s,
                    %(rent)s, %(electricity)s, %(medical)s, %(travel)s,
                    %(food)s, %(shopping)s, %(education)s, %(mobile)s,
                    %(entertainment)s, %(others)s
                )
                ON CONFLICT (user_id, year, month)
                DO UPDATE SET
                    monthly_income=EXCLUDED.monthly_income,
                    rent=EXCLUDED.rent,
                    electricity=EXCLUDED.electricity,
                    medical=EXCLUDED.medical,
                    travel=EXCLUDED.travel,
                    food=EXCLUDED.food,
                    shopping=EXCLUDED.shopping,
                    education=EXCLUDED.education,
                    mobile=EXCLUDED.mobile,
                    entertainment=EXCLUDED.entertainment,
                    others=EXCLUDED.others
            """, {
                "uid": uid, "year": year, "month": month,
                "income": monthly_income, **values
            })
            conn.commit()
            cur.close()
            conn.close()
            flash("Expenditure saved successfully.")
            return redirect(url_for("expenditure", year=year, lang=request.values.get("lang", "English")))

        except (ValueError, TypeError):
            flash("Enter valid non-negative amounts and a valid year.")
        except Exception:
            app.logger.exception("Saving expenditure failed")
            flash("Unable to save expenditure. Check your database.")

    try:
        selected_year = int(request.args.get("year", "2026"))
        if selected_year < 2000 or selected_year > 2100:
            selected_year = 2026
    except ValueError:
        selected_year = 2026

    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM expenses
            WHERE user_id=%s
            ORDER BY year DESC,
            CASE month
                WHEN 'January' THEN 1 WHEN 'February' THEN 2
                WHEN 'March' THEN 3 WHEN 'April' THEN 4
                WHEN 'May' THEN 5 WHEN 'June' THEN 6
                WHEN 'July' THEN 7 WHEN 'August' THEN 8
                WHEN 'September' THEN 9 WHEN 'October' THEN 10
                WHEN 'November' THEN 11 WHEN 'December' THEN 12
            END DESC
        """, (uid,))
        records = cur.fetchall()
        cur.close()
        conn.close()
    except Exception:
        app.logger.exception("Loading expenditure failed")
        records = []
        flash("Could not load saved records. Check your database.")

    prepared = []
    for record in records:
        item = dict(record)
        item["total"] = expense_total(item)
        item["balance"] = money(item["monthly_income"]) - item["total"]
        prepared.append(item)

    total_income = sum(money(r["monthly_income"]) for r in prepared)
    total_expenses = sum(r["total"] for r in prepared)
    balance = total_income - total_expenses

    if not prepared:
        suggestion = "Save your first monthly expenditure record to see suggestions."
    elif balance < 0:
        suggestion = "Your expenses exceed your recorded income. Review non-essential spending."
    elif total_income > 0 and total_expenses / total_income > 0.8:
        suggestion = "More than 80% of your recorded income is spent. Review shopping and entertainment costs."
    else:
        suggestion = "Your recorded income covers your expenses. Keep tracking monthly costs and savings."

    content = """
    <section class="card">
      <h2>Monthly expenditure</h2>
      <p class="small">Leave a field blank if you did not spend money in that category.
      Saving the same month/year updates that record.</p>

      <form method="post">
        <div class="grid">
          <div>
            <label>Year</label>
            <select name="year" onchange="this.form.year_changed.value='1'">
              {% for y in range(2026, 2019, -1) %}
              <option value="{{ y }}" {% if y==selected_year %}selected{% endif %}>{{ y }}</option>
              {% endfor %}
            </select>
          </div>
          <div>
            <label>Month</label>
            <select name="month">
              {% for m in months %}
              <option value="{{ m }}">{{ m }}</option>
              {% endfor %}
            </select>
          </div>
          <div>
            <label>Monthly income (₹)</label>
            <input type="number" name="monthly_income" min="0" step="0.01"
                   placeholder="Enter monthly income">
          </div>
        </div>

        <h3>Enter each bill or expense</h3>
        {% for field, label in fields %}
          <label>{{ label }} (₹)</label>
          <input type="number" name="{{ field }}" min="0" step="0.01"
                 placeholder="Enter amount">
        {% endfor %}
        <input type="hidden" name="year_changed" value="0">
        <button type="submit">Save expenditure</button>
      </form>
    </section>

    <section class="card">
      <h2>Previously saved expenditure records</h2>
      {% if records %}
      <div style="overflow-x:auto">
      <table>
        <tr><th>Month / Year</th><th>Income</th><th>Total expenses</th><th>Balance</th></tr>
        {% for r in records %}
        <tr>
          <td>{{ r.month }} {{ r.year }}</td>
          <td>₹{{ "{:,.2f}".format(r.monthly_income|float) }}</td>
          <td>₹{{ "{:,.2f}".format(r.total) }}</td>
          <td>₹{{ "{:,.2f}".format(r.balance) }}</td>
        </tr>
        {% endfor %}
      </table>
      </div>
      {% else %}
      <p class="small">No saved expenditure records yet. Add expenses above.</p>
      {% endif %}
    </section>

    <section class="card">
      <h2>Income and expenditure comparison</h2>
      {% if records %}
      <div class="grid">
        <div class="stats"><div>Total recorded income</div>
          <div class="amount">₹{{ "{:,.2f}".format(total_income) }}</div></div>
        <div class="stats"><div>Total recorded expenses</div>
          <div class="amount">₹{{ "{:,.2f}".format(total_expenses) }}</div></div>
        <div class="stats"><div>Remaining balance</div>
          <div class="amount">₹{{ "{:,.2f}".format(balance) }}</div></div>
      </div>
      <h3>Income vs expenditure</h3>
      <canvas id="comparison" height="150" style="width:100%"></canvas>
      {% else %}
      <p class="small">Save your first expenditure record to see the comparison.</p>
      {% endif %}
    </section>

    <section class="card">
      <h2>Saving suggestions</h2>
      <p>{{ suggestion }}</p>
    </section>

    {% if records %}
    <script>
    const values = [
      {{ total_income|round(2) }},
      {{ total_expenses|round(2) }},
      {{ balance|round(2) }}
    ];
    const canvas = document.getElementById('comparison');
    const ctx = canvas.getContext('2d');
    function drawChart(){
      const w = canvas.clientWidth;
      const h = 150;
      canvas.width = w * devicePixelRatio;
      canvas.height = h * devicePixelRatio;
      ctx.scale(devicePixelRatio, devicePixelRatio);
      const max = Math.max(...values.map(Math.abs), 1);
      const labels = ['Income', 'Expenses', 'Balance'];
      const barWidth = Math.min(65, w / 5);
      const gap = w / 3;
      labels.forEach((label, i) => {
        const barHeight = Math.abs(values[i]) / max * 90;
        const x = gap * i + gap / 2 - barWidth / 2;
        const y = 110 - barHeight;
        ctx.fillStyle = i === 1 ? '#e0a13a' : (i === 2 ? '#3d9b76' : '#2864db');
        ctx.fillRect(x, y, barWidth, barHeight);
        ctx.fillStyle = '#263247';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(label, x + barWidth / 2, 130);
        ctx.fillText('₹' + values[i].toLocaleString('en-IN'), x + barWidth / 2, Math.max(12, y - 5));
      });
    }
    drawChart();
    window.addEventListener('resize', drawChart);
    </script>
    {% endif %}
    """

    fields = [
        ("rent", "House rent"),
        ("electricity", "Electricity"),
        ("medical", "Medical / hospital"),
        ("travel", "Travel"),
        ("food", "Food"),
        ("shopping", "Shopping"),
        ("education", "Education"),
        ("mobile", "Mobile / internet"),
        ("entertainment", "Entertainment"),
        ("others", "Others")
    ]

    return page(
        content,
        records=prepared,
        months=MONTHS,
        fields=fields,
        selected_year=selected_year,
        total_income=total_income,
        total_expenses=total_expenses,
        balance=balance,
        suggestion=suggestion
    )

@app.route("/health")
def health():
    return "App is running", 200

if __name__ == "__main__":
    if not DATABASE_URL:
        print("WARNING: Set DATABASE_URL before using the app.")
    else:
        try:
            init_db()
            print("Database initialized.")
        except Exception:
            app.logger.exception("Database initialization failed")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
