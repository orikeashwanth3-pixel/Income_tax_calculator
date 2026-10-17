
import os
import sqlite3
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from flask import (
    Flask, request, redirect, url_for, session,
    render_template_string, flash
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")
DB_PATH = os.environ.get("DB_PATH", "tax.db")

LANGUAGES = {
    "English": {
        "title": "Income Tax Calculator",
        "login": "Login", "register": "Register", "logout": "Logout",
        "username": "Username", "password": "Password",
        "dashboard": "Dashboard", "income": "Annual Income",
        "calculate": "Calculate Tax", "tax": "Income Tax",
        "cess": "4% Cess", "total": "Total Tax",
        "monthly": "Monthly Income After Tax",
        "expenses": "Monthly Expenditure", "year": "Year",
        "month": "Month", "rent": "House Rent",
        "electricity": "Electricity", "medical": "Hospital / Medical",
        "travel": "Travelling", "food": "Food", "shopping": "Shopping",
        "education": "Education", "mobile": "Mobile / Internet",
        "entertainment": "Entertainment", "others": "Others",
        "saved": "Saved Money", "save": "Save Expenses",
        "records": "Expense Records", "delete": "Delete",
        "clear": "Clear Records", "welcome": "Welcome",
        "total_expenses": "Total Expenses", "required": "Please enter valid values.",
        "exists": "Username already exists.", "invalid": "Invalid username or password.",
        "login_first": "Please login first.", "no_records": "No records yet.",
        "income_page": "Income Tax", "expense_page": "Expenditure",
        "amount": "Amount (₹)", "home": "Home"
    },
    "Telugu": {
        "title": "ఆదాయపు పన్ను కాలిక్యులేటర్",
        "login": "లాగిన్", "register": "రిజిస్టర్", "logout": "లాగౌట్",
        "username": "యూజర్ పేరు", "password": "పాస్‌వర్డ్",
        "dashboard": "డాష్‌బోర్డ్", "income": "వార్షిక ఆదాయం",
        "calculate": "పన్ను లెక్కించండి", "tax": "ఆదాయపు పన్ను",
        "cess": "4% సెస్", "total": "మొత్తం పన్ను",
        "monthly": "పన్ను తర్వాత నెలవారీ ఆదాయం",
        "expenses": "నెలవారీ ఖర్చులు", "year": "సంవత్సరం",
        "month": "నెల", "rent": "ఇంటి అద్దె",
        "electricity": "విద్యుత్", "medical": "ఆసుపత్రి / వైద్యం",
        "travel": "ప్రయాణం", "food": "ఆహారం", "shopping": "షాపింగ్",
        "education": "విద్య", "mobile": "మొబైల్ / ఇంటర్నెట్",
        "entertainment": "వినోదం", "others": "ఇతర ఖర్చులు",
        "saved": "మిగిలిన డబ్బు", "save": "ఖర్చులను సేవ్ చేయండి",
        "records": "ఖర్చుల వివరాలు", "delete": "తొలగించు",
        "clear": "అన్ని వివరాలు తొలగించు", "welcome": "స్వాగతం",
        "total_expenses": "మొత్తం ఖర్చులు", "required": "సరైన విలువలను నమోదు చేయండి.",
        "exists": "ఈ యూజర్ పేరు ఇప్పటికే ఉంది.", "invalid": "యూజర్ పేరు లేదా పాస్‌వర్డ్ తప్పు.",
        "login_first": "ముందుగా లాగిన్ అవ్వండి.", "no_records": "ఇంకా వివరాలు లేవు.",
        "income_page": "ఆదాయపు పన్ను", "expense_page": "ఖర్చులు",
        "amount": "మొత్తం (₹)", "home": "హోమ్"
    },
    "Hindi": {
        "title": "आयकर कैलकुलेटर",
        "login": "लॉगिन", "register": "रजिस्टर", "logout": "लॉगआउट",
        "username": "यूज़रनेम", "password": "पासवर्ड",
        "dashboard": "डैशबोर्ड", "income": "वार्षिक आय",
        "calculate": "टैक्स की गणना करें", "tax": "आयकर",
        "cess": "4% उपकर", "total": "कुल टैक्स",
        "monthly": "टैक्स के बाद मासिक आय",
        "expenses": "मासिक खर्च", "year": "वर्ष",
        "month": "महीना", "rent": "घर का किराया",
        "electricity": "बिजली", "medical": "अस्पताल / चिकित्सा",
        "travel": "यात्रा", "food": "भोजन", "shopping": "खरीदारी",
        "education": "शिक्षा", "mobile": "मोबाइल / इंटरनेट",
        "entertainment": "मनोरंजन", "others": "अन्य",
        "saved": "बची हुई राशि", "save": "खर्च सेव करें",
        "records": "खर्च रिकॉर्ड", "delete": "हटाएं",
        "clear": "सभी रिकॉर्ड हटाएं", "welcome": "स्वागत है",
        "total_expenses": "कुल खर्च", "required": "कृपया सही मान दर्ज करें।",
        "exists": "यूज़रनेम पहले से मौजूद है।", "invalid": "गलत यूज़रनेम या पासवर्ड।",
        "login_first": "कृपया पहले लॉगिन करें।", "no_records": "अभी कोई रिकॉर्ड नहीं है।",
        "income_page": "आयकर", "expense_page": "खर्च",
        "amount": "राशि (₹)", "home": "होम"
    }
}

EXPENSE_FIELDS = [
    ("rent", "rent"), ("electricity", "electricity"),
    ("medical", "medical"), ("travel", "travel"),
    ("food", "food"), ("shopping", "shopping"),
    ("education", "education"), ("mobile", "mobile"),
    ("entertainment", "entertainment"), ("others", "others")
]


def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_database():
    with connect_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                year INTEGER NOT NULL,
                month TEXT NOT NULL,
                monthly_income REAL NOT NULL DEFAULT 0,
                rent REAL NOT NULL DEFAULT 0,
                electricity REAL NOT NULL DEFAULT 0,
                medical REAL NOT NULL DEFAULT 0,
                travel REAL NOT NULL DEFAULT 0,
                food REAL NOT NULL DEFAULT 0,
                shopping REAL NOT NULL DEFAULT 0,
                education REAL NOT NULL DEFAULT 0,
                mobile REAL NOT NULL DEFAULT 0,
                entertainment REAL NOT NULL DEFAULT 0,
                others REAL NOT NULL DEFAULT 0,
                saved_money REAL NOT NULL DEFAULT 0,
                UNIQUE(user_id, year, month),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)


def money(value):
    return Decimal(str(value)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def calculate_tax(income):
    """Illustrative slab calculation; no Section 87A rebate."""
    income = money(income)

    if income <= 400000:
        tax = Decimal("0")
    elif income <= 800000:
        tax = (income - Decimal("400000")) * Decimal("0.05")
    elif income <= 1200000:
        tax = Decimal("20000") + (
            income - Decimal("800000")
        ) * Decimal("0.10")
    elif income <= 1600000:
        tax = Decimal("60000") + (
            income - Decimal("1200000")
        ) * Decimal("0.15")
    elif income <= 2000000:
        tax = Decimal("120000") + (
            income - Decimal("1600000")
        ) * Decimal("0.20")
    elif income <= 2400000:
        tax = Decimal("200000") + (
            income - Decimal("2000000")
        ) * Decimal("0.25")
    else:
        tax = Decimal("300000") + (
            income - Decimal("2400000")
        ) * Decimal("0.30")

    tax = money(tax)
    cess = money(tax * Decimal("0.04"))
    total = money(tax + cess)
    return tax, cess, total


BASE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ t.title }}</title>
<style>
* { box-sizing: border-box; }
body {
  font-family: Arial, sans-serif; background: #f3f6fb;
  margin: 0; color: #222;
}
header {
  background: #153e75; color: white; padding: 16px;
  display: flex; flex-wrap: wrap; gap: 12px;
  justify-content: space-between; align-items: center;
}
header a { color: white; margin-right: 12px; }
main {
  max-width: 760px; margin: 22px auto; padding: 18px;
}
.card {
  background: white; padding: 20px; margin-bottom: 18px;
  border-radius: 12px; box-shadow: 0 2px 9px #0001;
}
label { display: block; margin: 14px 0 6px; font-weight: bold; }
input, select {
  width: 100%; padding: 11px; border: 1px solid #bbb;
  border-radius: 7px; font-size: 16px; background: white;
}
button, .btn {
  display: inline-block; border: 0; border-radius: 7px;
  padding: 11px 16px; margin-top: 15px; background: #1769aa;
  color: white; font-size: 15px; cursor: pointer; text-decoration: none;
}
.danger { background: #b42318; }
nav { padding-top: 6px; }
.result { background: #eaf5ff; padding: 14px; border-radius: 8px; }
table { width: 100%; border-collapse: collapse; }
td, th { border-bottom: 1px solid #ddd; padding: 8px; text-align: left; }
.notice { padding: 10px; background: #fff4ce; border-radius: 7px; }
</style>
</head>
<body>
<header>
  <div><strong>{{ t.title }}</strong></div>
  <div>
    <form method="get" action="{{ request.path }}" style="display:inline">
      {% for key, value in request.args.items() if key != 'lang' %}
        <input type="hidden" name="{{ key }}" value="{{ value }}">
      {% endfor %}
      <select name="lang" onchange="this.form.submit()" aria-label="Language">
        {% for name in languages %}
        <option value="{{ name }}" {% if name == lang %}selected{% endif %}>{{ name }}</option>
        {% endfor %}
      </select>
    </form>
  </div>
  <nav>
    {% if session.get('user_id') %}
      <a href="{{ url_for('dashboard', lang=lang) }}">{{ t.home }}</a>
      <a href="{{ url_for('income_page', lang=lang) }}">{{ t.income_page }}</a>
      <a href="{{ url_for('expenses_page', lang=lang) }}">{{ t.expense_page }}</a>
      <a href="{{ url_for('logout', lang=lang) }}">{{ t.logout }}</a>
    {% endif %}
  </nav>
</header>
<main>
{% with messages = get_flashed_messages() %}
  {% for message in messages %}<p class="notice">{{ message }}</p>{% endfor %}
{% endwith %}
{{ content|safe }}
</main>
</body>
</html>
"""


def page(content):
    lang = request.values.get("lang", "English")
    if lang not in LANGUAGES:
        lang = "English"
    return render_template_string(
        BASE, content=content, lang=lang, t=LANGUAGES[lang],
        languages=list(LANGUAGES.keys()), request=request, session=session
    )


def tr():
    lang = request.values.get("lang", "English")
    return LANGUAGES.get(lang, LANGUAGES["English"])


def logged_in():
    if not session.get("user_id"):
        flash(tr()["login_first"])
        return False
    return True


@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard", lang=request.args.get("lang", "English")))
    return redirect(url_for("login", lang=request.args.get("lang", "English")))


@app.route("/register", methods=["GET", "POST"])
def register():
    t = tr()
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash(t["required"])
        else:
            try:
                with connect_db() as db:
                    db.execute(
                        "INSERT INTO users(username,password) VALUES(?,?)",
                        (username, generate_password_hash(password))
                    )
                flash("Account created. Please login.")
                return redirect(url_for("login", lang=request.form.get("lang", "English")))
            except sqlite3.IntegrityError:
                flash(t["exists"])

    content = """
    <div class="card"><h2>{{ t.register }}</h2>
    <form method="post">
      <input type="hidden" name="lang" value="{{ lang }}">
      <label>{{ t.username }}</label><input name="username" required>
      <label>{{ t.password }}</label><input type="password" name="password" required>
      <button>{{ t.register }}</button>
    </form><p><a href="{{ url_for('login', lang=lang) }}">{{ t.login }}</a></p></div>
    """
    return page(render_template_string(content, t=t, lang=request.values.get("lang", "English")))


@app.route("/login", methods=["GET", "POST"])
def login():
    t = tr()
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with connect_db() as db:
            user = db.execute(
                "SELECT * FROM users WHERE username=?", (username,)
            ).fetchone()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard", lang=request.form.get("lang", "English")))
        flash(t["invalid"])

    content = """
    <div class="card"><h2>{{ t.login }}</h2>
    <form method="post">
      <input type="hidden" name="lang" value="{{ lang }}">
      <label>{{ t.username }}</label><input name="username" required>
      <label>{{ t.password }}</label><input type="password" name="password" required>
      <button>{{ t.login }}</button>
    </form><p><a href="{{ url_for('register', lang=lang) }}">{{ t.register }}</a></p></div>
    """
    return page(render_template_string(content, t=t, lang=request.values.get("lang", "English")))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login", lang=request.args.get("lang", "English")))


@app.route("/dashboard")
def dashboard():
    if not logged_in():
        return redirect(url_for("login", lang=request.args.get("lang", "English")))
    t = tr()
    content = """
    <div class="card">
      <h2>{{ t.welcome }}, {{ session.get('username') }}!</h2>
      <p>Select an option:</p>
      <a class="btn" href="{{ url_for('income_page', lang=lang) }}">{{ t.income_page }}</a>
      <a class="btn" href="{{ url_for('expenses_page', lang=lang) }}">{{ t.expense_page }}</a>
    </div>
    """
    return page(render_template_string(content, t=t, lang=request.args.get("lang", "English"), session=session))


@app.route("/income", methods=["GET", "POST"])
def income_page():
    if not logged_in():
        return redirect(url_for("login", lang=request.args.get("lang", "English")))
    t = tr()
    result = None
    if request.method == "POST":
        try:
            income = money(request.form.get("income", ""))
            if income < 0:
                raise InvalidOperation
            tax, cess, total = calculate_tax(income)
            result = {
                "income": income, "tax": tax, "cess": cess, "total": total,
                "monthly": money((income - total) / Decimal("12"))
            }
        except (InvalidOperation, ValueError, TypeError):
            flash(t["required"])

    content = """
    <div class="card">
      <h2>{{ t.income_page }}</h2>
      <form method="post">
        <input type="hidden" name="lang" value="{{ lang }}">
        <label>{{ t.income }} (₹)</label>
        <input type="number" name="income" min="0" step="0.01" required>
        <button>{{ t.calculate }}</button>
      </form>
      {% if result %}
      <div class="result">
        <p>{{ t.income }}: ₹{{ "%.2f"|format(result.income) }}</p>
        <p>{{ t.tax }}: ₹{{ "%.2f"|format(result.tax) }}</p>
        <p>{{ t.cess }}: ₹{{ "%.2f"|format(result.cess) }}</p>
        <h3>{{ t.total }}: ₹{{ "%.2f"|format(result.total) }}</h3>
        <p>{{ t.monthly }}: ₹{{ "%.2f"|format(result.monthly) }}</p>
      </div>
      {% endif %}
    </div>
    """
    return page(render_template_string(
        content, t=t, result=result, lang=request.values.get("lang", "English")
    ))


@app.route("/expenses", methods=["GET", "POST"])
def expenses_page():
    if not logged_in():
        return redirect(url_for("login", lang=request.args.get("lang", "English")))
    t = tr()
    uid = session["user_id"]

    if request.method == "POST":
        try:
            year = int(request.form.get("year", "2026"))
            month = request.form.get("month", "January")
            if month not in [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ]:
                raise ValueError

            income = money(request.form.get("monthly_income", "0"))
            values = {}
            for key, _ in EXPENSE_FIELDS:
                values[key] = money(request.form.get(key, "0"))
                if values[key] < 0:
                    raise ValueError
            if income < 0:
                raise ValueError

            total_expenses = sum(values.values(), Decimal("0"))
            saved = money(income - total_expenses)
            if year < 2000 or year > 2100:
                raise ValueError

            with connect_db() as db:
                db.execute("""
                    INSERT INTO expenses (
                      user_id, year, month, monthly_income, rent, electricity,
                      medical, travel, food, shopping, education, mobile,
                      entertainment, others, saved_money
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(user_id,year,month) DO UPDATE SET
                      monthly_income=excluded.monthly_income,
                      rent=excluded.rent, electricity=excluded.electricity,
                      medical=excluded.medical, travel=excluded.travel,
                      food=excluded.food, shopping=excluded.shopping,
                      education=excluded.education, mobile=excluded.mobile,
                      entertainment=excluded.entertainment, others=excluded.others,
                      saved_money=excluded.saved_money
                """, (
                    uid, year, month, float(income),
                    *[float(values[key]) for key, _ in EXPENSE_FIELDS],
                    float(saved)
                ))
            flash("Expenses saved successfully.")
            return redirect(url_for("expenses_page", lang=request.form.get("lang", "English")))
        except (InvalidOperation, ValueError, TypeError):
            flash(t["required"])

    with connect_db() as db:
        records = db.execute(
            "SELECT * FROM expenses WHERE user_id=? ORDER BY year DESC, id DESC",
            (uid,)
        ).fetchall()

    content = """
    <div class="card">
      <h2>{{ t.expenses }}</h2>
      <form method="post">
        <input type="hidden" name="lang" value="{{ lang }}">
        <label>{{ t.year }}</label><input type="number" name="year" value="2026" min="2000" max="2100" required>
        <label>{{ t.month }}</label>
        <select name="month">
        {% for m in months %}<option>{{ m }}</option>{% endfor %}
        </select>
        <label>{{ t.income }} (₹)</label><input type="number" name="monthly_income" min="0" step="0.01" value="0" required>
        {% for key, label in expense_fields %}
          <label>{{ t[label] }} (₹)</label>
          <input type="number" name="{{ key }}" min="0" step="0.01" value="0" required>
        {% endfor %}
        <button>{{ t.save }}</button>
      </form>
    </div>
    <div class="card">
      <h2>{{ t.records }}</h2>
      {% if records %}
      <table>
        <tr><th>{{ t.year }}</th><th>{{ t.month }}</th><th>{{ t.income }}</th>
        <th>{{ t.total_expenses }}</th><th>{{ t.saved }}</th><th></th></tr>
        {% for r in records %}
        <tr>
          <td>{{ r.year }}</td><td>{{ r.month }}</td>
          <td>₹{{ "%.2f"|format(r.monthly_income) }}</td>
          <td>₹{{ "%.2f"|format(r.rent+r.electricity+r.medical+r.travel+r.food+r.shopping+r.education+r.mobile+r.entertainment+r.others) }}</td>
          <td>₹{{ "%.2f"|format(r.saved_money) }}</td>
          <td><form method="post" action="{{ url_for('delete_expense', record_id=r.id, lang=lang) }}">
            <button class="danger" type="submit">{{ t.delete }}</button>
          </form></td>
        </tr>
        {% endfor %}
      </table>
      <form method="post" action="{{ url_for('clear_expenses', lang=lang) }}"
            onsubmit="return confirm('Delete all your expense records?')">
        <button class="danger">{{ t.clear }}</button>
      </form>
      {% else %}<p>{{ t.no_records }}</p>{% endif %}
    </div>
    """
    return page(render_template_string(
        content, t=t, records=records, lang=request.values.get("lang", "English"),
        months=[
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ],
        expense_fields=EXPENSE_FIELDS
    ))


@app.route("/expense/delete/<int:record_id>", methods=["POST"])
def delete_expense(record_id):
    if not logged_in():
        return redirect(url_for("login", lang=request.args.get("lang", "English")))
    with connect_db() as db:
        db.execute(
            "DELETE FROM expenses WHERE id=? AND user_id=?",
            (record_id, session["user_id"])
        )
    return redirect(url_for("expenses_page", lang=request.args.get("lang", "English")))


@app.route("/expenses/clear", methods=["POST"])
def clear_expenses():
    if not logged_in():
        return redirect(url_for("login", lang=request.args.get("lang", "English")))
    with connect_db() as db:
        db.execute("DELETE FROM expenses WHERE user_id=?", (session["user_id"],))
    return redirect(url_for("expenses_page", lang=request.args.get("lang", "English")))


# Create tables when the app starts, including when launched by Gunicorn on Render.
create_database()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
