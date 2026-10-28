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
    ("rent", "Home Rent"), ("electricity", "Electricity"),
    ("medical", "Hospital / Medical"), ("travel", "Travelling"),
    ("food", "Food"), ("shopping", "Shopping"),
    ("education", "Education"), ("mobile", "Mobile / Internet"),
    ("entertainment", "Entertainment"), ("others", "Others")
]

TEXTS = {
    "English": {
        "login": "Login", "register": "Create Account", "username": "Username",
        "password": "Password", "dashboard": "Dashboard", "income": "Income",
        "expenses": "Expenditure", "logout": "Logout",
        "annual_income": "ENTER ANNUAL INCOME", "calculate": "Calculate Tax",
        "tax": "Tax", "back": "Back to Dashboard", "month": "Month",
        "monthly_income": "Monthly Income", "save_month": "Save Month",
        "total_expense": "Total Expenditure", "saved": "Saved Money",
        "analysis": "Financial Analysis", "highest_expense": "Highest Expense Category",
        "highest_month": "Highest Expense Month",
        "highest_saving_month": "Highest Saving Month",
        "expense_percent": "Expense Percentage", "saving_percent": "Savings Percentage",
        "comparison": "Monthly Comparison", "suggestion": "Suggestion",
        "total_income": "Total Income", "total_savings": "Total Savings",
        "no_data": "No records found for this year.",
        "select_year": "Select Year", "invalid_login": "Invalid username or password.",
        "account_exists": "Username already exists.", "welcome": "Welcome",
        "edit": "Edit", "update": "Update", "cancel": "Cancel",
        "delete": "Delete", "language": "Language", "income_tax_title": "INCOME TAX CALCULATOR",
        "income_result": "Tax Result", "expense_title": "MONTHLY EXPENDITURE",
        "saved_success": "Record saved successfully.",
        "deleted_success": "Record deleted successfully.",
        "invalid_amount": "Please enter valid non-negative amounts.",
        "recommendation": "Try to keep your expenses within your income.",
        "no_expenses": "No expenditure records yet.", "year": "Year",
        "total": "Total", "save": "Save", "actions": "Actions",
        "slab_heading": "How was tax calculated?"
    },
    "Telugu": {
        "login": "లాగిన్", "register": "అకౌంట్ క్రియేట్ చేయండి",
        "username": "యూజర్‌నేమ్", "password": "పాస్‌వర్డ్",
        "dashboard": "డాష్‌బోర్డ్", "income": "ఆదాయం",
        "expenses": "ఖర్చులు", "logout": "లాగ్ అవుట్",
        "annual_income": "వార్షిక ఆదాయం నమోదు చేయండి",
        "calculate": "ట్యాక్స్ లెక్కించండి", "tax": "ట్యాక్స్",
        "back": "డాష్‌బోర్డ్‌కు తిరిగి వెళ్ళండి", "month": "నెల",
        "monthly_income": "నెలవారీ ఆదాయం", "save_month": "నెలను సేవ్ చేయండి",
        "total_expense": "మొత్తం ఖర్చు", "saved": "మిగిలిన డబ్బు",
        "analysis": "ఆర్థిక విశ్లేషణ", "highest_expense": "అత్యధిక ఖర్చు కేటగిరీ",
        "highest_month": "అత్యధిక ఖర్చు చేసిన నెల",
        "highest_saving_month": "అత్యధిక సేవింగ్ ఉన్న నెల",
        "expense_percent": "ఖర్చు శాతం", "saving_percent": "సేవింగ్ శాతం",
        "comparison": "నెలవారీ పోలిక", "suggestion": "సూచన",
        "total_income": "మొత్తం ఆదాయం", "total_savings": "మొత్తం సేవింగ్స్",
        "no_data": "ఈ సంవత్సరానికి రికార్డులు లేవు.",
        "select_year": "సంవత్సరం ఎంచుకోండి",
        "invalid_login": "యూజర్‌నేమ్ లేదా పాస్‌వర్డ్ తప్పు.",
        "account_exists": "ఈ యూజర్‌నేమ్ ఇప్పటికే ఉంది.", "welcome": "స్వాగతం",
        "edit": "ఎడిట్", "update": "అప్‌డేట్", "cancel": "రద్దు",
        "delete": "డిలీట్", "language": "భాష",
        "income_tax_title": "ఇన్‌కమ్ ట్యాక్స్ కాలిక్యులేటర్",
        "income_result": "ట్యాక్స్ ఫలితం", "expense_title": "నెలవారీ ఖర్చులు",
        "saved_success": "రికార్డు సేవ్ అయింది.",
        "deleted_success": "రికార్డు డిలీట్ అయింది.",
        "invalid_amount": "సున్నా లేదా అంతకంటే ఎక్కువ సరైన మొత్తాలు నమోదు చేయండి.",
        "recommendation": "ఖర్చులను ఆదాయంలోపే ఉంచడానికి ప్రయత్నించండి.",
        "no_expenses": "ఇంకా ఖర్చుల రికార్డులు లేవు.", "year": "సంవత్సరం",
        "total": "మొత్తం", "save": "సేవ్", "actions": "చర్యలు",
        "slab_heading": "ట్యాక్స్ ఎలా లెక్కించారు?"
    },
    "Hindi": {
        "login": "लॉगिन", "register": "अकाउंट बनाएं", "username": "यूज़रनेम",
        "password": "पासवर्ड", "dashboard": "डैशबोर्ड", "income": "आय",
        "expenses": "खर्च", "logout": "लॉग आउट", "annual_income": "वार्षिक आय दर्ज करें",
        "calculate": "टैक्स कैलकुलेट करें", "tax": "टैक्स",
        "back": "डैशबोर्ड पर वापस जाएं", "month": "महीना",
        "monthly_income": "मासिक आय", "save_month": "महीना सेव करें",
        "total_expense": "कुल खर्च", "saved": "बचत", "analysis": "वित्तीय विश्लेषण",
        "highest_expense": "सबसे अधिक खर्च की श्रेणी",
        "highest_month": "सबसे अधिक खर्च वाला महीना",
        "highest_saving_month": "सबसे अधिक बचत वाला महीना",
        "expense_percent": "खर्च प्रतिशत", "saving_percent": "बचत प्रतिशत",
        "comparison": "मासिक तुलना", "suggestion": "सुझाव",
        "total_income": "कुल आय", "total_savings": "कुल बचत",
        "no_data": "इस वर्ष कोई रिकॉर्ड नहीं है।", "select_year": "वर्ष चुनें",
        "invalid_login": "यूज़रनेम या पासवर्ड गलत है।",
        "account_exists": "यूज़रनेम पहले से मौजूद है।", "welcome": "स्वागत है",
        "edit": "एडिट", "update": "अपडेट", "cancel": "रद्द करें",
        "delete": "डिलीट", "language": "भाषा", "income_tax_title": "इनकम टैक्स कैलकुलेटर",
        "income_result": "टैक्स परिणाम", "expense_title": "मासिक खर्च",
        "saved_success": "रिकॉर्ड सेव हुआ।", "deleted_success": "रिकॉर्ड डिलीट हुआ।",
        "invalid_amount": "शून्य या उससे अधिक सही राशि दर्ज करें।",
        "recommendation": "अपने खर्चों को आय के भीतर रखने की कोशिश करें।",
        "no_expenses": "अभी कोई खर्च रिकॉर्ड नहीं है।", "year": "वर्ष",
        "total": "कुल", "save": "सेव", "actions": "कार्यवाही",
        "slab_heading": "टैक्स की गणना कैसे हुई?"
    }
}

STYLE = """
<style>
*{box-sizing:border-box}
body{font-family:Arial,sans-serif;background:#f3f6fb;color:#222;margin:0;padding:16px}
.container{max-width:1100px;margin:auto}
.card{background:white;padding:22px;border-radius:14px;margin-bottom:18px;box-shadow:0 3px 15px #00000010}
h1,h2,h3{text-align:center}
label{display:block;font-weight:bold;margin-top:10px}
input,select{width:100%;padding:12px;border:1px solid #ccd2dc;border-radius:8px;margin:7px 0;font-size:16px}
button,.btn{display:inline-block;padding:11px 16px;background:#2563eb;color:white;border:0;border-radius:8px;text-decoration:none;cursor:pointer;margin:4px;font-size:16px}
.green{background:#16a34a}.red{background:#dc2626}.gray{background:#555}.orange{background:#d97706}
.center{text-align:center}.message{background:#eef6ff;padding:12px;border-radius:8px;margin:10px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}
.stat{background:#f7f9fc;padding:18px;border-radius:10px;text-align:center;min-width:0}
.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;min-width:1000px;background:white}
th,td{padding:10px;border:1px solid #ddd;text-align:center}
th{background:#eef2ff}
.comparison-row{display:flex;flex-wrap:nowrap;gap:12px;overflow-x:auto;padding-bottom:10px}
.comparison-row .stat{flex:0 0 190px;min-width:190px}
@media(max-width:600px){body{padding:8px}.card{padding:14px}.stat h3{font-size:20px}}
</style>
"""

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
            rent NUMERIC DEFAULT 0, electricity NUMERIC DEFAULT 0,
            medical NUMERIC DEFAULT 0, travel NUMERIC DEFAULT 0,
            food NUMERIC DEFAULT 0, shopping NUMERIC DEFAULT 0,
            education NUMERIC DEFAULT 0, mobile NUMERIC DEFAULT 0,
            entertainment NUMERIC DEFAULT 0, others NUMERIC DEFAULT 0,
            saved_money NUMERIC DEFAULT 0,
            UNIQUE(user_id, year, month)
        )
    """)
    cur.execute("ALTER TABLE expenses ADD COLUMN IF NOT EXISTS year INTEGER DEFAULT 2026")
    # Older versions may have had UNIQUE(user_id, month), which blocks storing
    # the same month in multiple years. Remove that legacy constraint if present.
    cur.execute("""
        ALTER TABLE expenses DROP CONSTRAINT IF EXISTS expenses_user_id_month_key
    """)
    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS expenses_user_year_month_unique
        ON expenses(user_id, year, month)
    """)
    conn.commit()
    cur.close()
    conn.close()

def get_lang():
    lang = session.get("lang", "English")
    return lang if lang in TEXTS else "English"

def T(key):
    return TEXTS[get_lang()].get(key, TEXTS["English"].get(key, key))

def page(title, body, **kwargs):
    template = """
    <!doctype html><html><head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ title }}</title>{{ style|safe }}</head>
    <body><div class="container">
    <div class="card">
      <div style="display:flex;justify-content:flex-end;align-items:center;gap:8px;flex-wrap:wrap">
        <span style="font-weight:bold">{{ t('language') }}</span>
        <select style="width:140px;margin:0" onchange="location.href='/language/'+this.value">
          {% for l in languages %}
          <option value="{{ l }}" {% if l==lang %}selected{% endif %}>{{ l }}</option>
          {% endfor %}
        </select>
      </div>
    </div>
    """ + body + """
    </div></body></html>
    """
    return render_template_string(template, title=title, style=STYLE, t=T,
                                  languages=list(TEXTS.keys()), lang=get_lang(),
                                  **kwargs)

def logged_in():
    return "user_id" in session

def parse_amount(value):
    try:
        amount = Decimal((value or "").strip() or "0")
    except (InvalidOperation, AttributeError):
        raise ValueError("Invalid amount")
    if not amount.is_finite() or amount < 0:
        raise ValueError("Amount must be non-negative")
    return amount

def money(value):
    return float(value or 0)

def fetch_expenses(year):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, year, month, monthly_income, rent, electricity, medical,
               travel, food, shopping, education, mobile, entertainment,
               others, saved_money
        FROM expenses WHERE user_id=%s AND year=%s
        ORDER BY CASE month
          WHEN 'January' THEN 1 WHEN 'February' THEN 2 WHEN 'March' THEN 3
          WHEN 'April' THEN 4 WHEN 'May' THEN 5 WHEN 'June' THEN 6
          WHEN 'July' THEN 7 WHEN 'August' THEN 8 WHEN 'September' THEN 9
          WHEN 'October' THEN 10 WHEN 'November' THEN 11 WHEN 'December' THEN 12
          ELSE 13 END
    """, (session["user_id"], year))
    records = cur.fetchall()
    cur.close()
    conn.close()
    result = []
    for r in records:
        row = {"id": r[0], "year": r[1], "month": r[2],
               "monthly_income": money(r[3])}
        for i, (key, _) in enumerate(CATEGORIES, start=4):
            row[key] = money(r[i])
        row["total_expense"] = sum(row[k] for k, _ in CATEGORIES)
        # Calculate savings from current income and category expenses.
        row["saved_money"] = row["monthly_income"] - row["total_expense"]
        result.append(row)
    return result

@app.route("/")
def home():
    return redirect(url_for("dashboard" if logged_in() else "login"))

@app.route("/language/<lang>")
def language(lang):
    if lang in TEXTS:
        session["lang"] = lang
    return redirect(request.referrer or url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    message = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            message = "Please enter username and password."
        else:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE username=%s", (username,))
            if cur.fetchone():
                message = T("account_exists")
            else:
                cur.execute("INSERT INTO users(username,password_hash) VALUES(%s,%s)",
                            (username, generate_password_hash(password)))
                conn.commit()
                cur.close()
                conn.close()
                return redirect(url_for("login"))
            cur.close()
            conn.close()
    body = """
    <div class="card"><h2>{{ t('register') }}</h2>
    {% if message %}<div class="message">{{ message }}</div>{% endif %}
    <form method="post">
      <label>{{ t('username') }}</label><input name="username" required maxlength="100">
      <label>{{ t('password') }}</label><input type="password" name="password" required>
      <button>{{ t('register') }}</button>
    </form>
    <div class="center"><a class="btn gray" href="/login">{{ t('login') }}</a></div></div>
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
        cur.execute("SELECT id,password_hash FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user and check_password_hash(user[1], password):
            language = get_lang()
            session.clear()
            session["user_id"] = user[0]
            session["username"] = username
            session["lang"] = language
            return redirect(url_for("dashboard"))
        message = T("invalid_login")
    body = """
    <div class="card"><h2>{{ t('login') }}</h2>
    {% if message %}<div class="message">{{ message }}</div>{% endif %}
    <form method="post">
      <label>{{ t('username') }}</label><input name="username" required>
      <label>{{ t('password') }}</label><input type="password" name="password" required>
      <button>{{ t('login') }}</button>
    </form>
    <div class="center"><a class="btn green" href="/register">{{ t('register') }}</a></div>
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
      <h2>{{ t('welcome') }}, {{ session_username }}</h2>
      <div class="grid">
        <a class="btn" href="/income" style="padding:30px">💰 {{ t('income') }}</a>
        <a class="btn green" href="/expenses" style="padding:30px">📊 {{ t('expenses') }}</a>
      </div>
      <p><a class="btn red" href="/logout">{{ t('logout') }}</a></p>
    </div>
    """
    return page("Dashboard", body, session_username=session.get("username"))

# Income tax calculator. This is a simplified slab calculator, not official tax advice.
def calculate_tax(income):
    if income <= Decimal("400000"):
        tax = Decimal("0")
        slab = "Up to ₹4,00,000: 0%"
        formula = "Tax = ₹0"
    elif income <= Decimal("800000"):
        tax = (income - Decimal("400000")) * Decimal("0.05")
        slab = "₹4,00,001–₹8,00,000: 5%"
        formula = "(Income − ₹4,00,000) × 5%"
    elif income <= Decimal("1200000"):
        tax = Decimal("20000") + (income - Decimal("800000")) * Decimal("0.10")
        slab = "₹8,00,001–₹12,00,000: 10%"
        formula = "₹20,000 + (Income − ₹8,00,000) × 10%"
    elif income <= Decimal("1600000"):
        tax = Decimal("60000") + (income - Decimal("1200000")) * Decimal("0.15")
        slab = "₹12,00,001–₹16,00,000: 15%"
        formula = "₹60,000 + (Income − ₹12,00,000) × 15%"
    elif income <= Decimal("2000000"):
        tax = Decimal("120000") + (income - Decimal("1600000")) * Decimal("0.20")
        slab = "₹16,00,001–₹20,00,000: 20%"
        formula = "₹1,20,000 + (Income − ₹16,00,000) × 20%"
    elif income <= Decimal("2400000"):
        tax = Decimal("200000") + (income - Decimal("2000000")) * Decimal("0.25")
        slab = "₹20,00,001–₹24,00,000: 25%"
        formula = "₹2,00,000 + (Income − ₹20,00,000) × 25%"
    else:
        tax = Decimal("300000") + (income - Decimal("2400000")) * Decimal("0.30")
        slab = "Above ₹24,00,000: 30%"
        formula = "₹3,00,000 + (Income − ₹24,00,000) × 30%"
    return tax, slab, formula

@app.route("/income", methods=["GET", "POST"])
def income():
    if not logged_in():
        return redirect(url_for("login"))
    result = None
    error = ""
    if request.method == "POST":
        try:
            annual_income = parse_amount(request.form.get("annual_income", ""))
            tax, slab, formula = calculate_tax(annual_income)
            result = {"tax": float(tax), "slab": slab, "formula": formula}
        except (ValueError, InvalidOperation):
            error = T("invalid_amount")
    body = """
    <div class="card">
      <h2>{{ t('income_tax_title') }}</h2>
      {% if error %}<div class="message">{{ error }}</div>{% endif %}
      <form method="post">
        <label>{{ t('annual_income') }} (₹)</label>
        <input type="number" min="0" step="0.01" name="annual_income"
               value="{{ request.form.get('annual_income','') }}" required>
        <button type="submit">{{ t('calculate') }}</button>
      </form>
    </div>
    {% if result %}
    <div class="card">
      <div class="stat"><h1>Tax = ₹{{ '{:,.2f}'.format(result.tax) }}</h1></div>
      <h2>{{ t('slab_heading') }}</h2>
      <p><b>Applicable Tax Slab:</b></p>
      <p>{{ result.slab }}</p>
      <p><b>Calculation Formula:</b></p>
      <p>{{ result.formula }}</p>
      <p><b>Tax = ₹{{ '{:,.2f}'.format(result.tax) }}</b></p>
      <p style="font-size:13px;color:#666">Simplified educational estimate; actual tax depends on applicable tax rules and deductions.</p>
    </div>
    {% endif %}
    <div class="center"><a class="btn gray" href="/dashboard">{{ t('back') }}</a></div>
    """
    return page("Income Tax Calculator", body, result=result, error=error)

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
    except (ValueError, TypeError):
        selected_year = 2026

    if request.method == "POST":
        conn = None
        cur = None
        try:
            year = int(request.form.get("year", "2026"))
            month = request.form.get("month", "")
            if year not in YEARS or month not in MONTHS:
                raise ValueError("Invalid year or month")
            income_amount = parse_amount(request.form.get("monthly_income", ""))
            amounts = {key: parse_amount(request.form.get(key, ""))
                       for key, _ in CATEGORIES}
            total_expenses = sum(amounts.values(), Decimal("0"))
            saved = income_amount - total_expenses
            conn = get_db()
            cur = conn.cursor()
            columns = ["user_id", "year", "month", "monthly_income"] + [
                key for key, _ in CATEGORIES
            ] + ["saved_money"]
            placeholders = ", ".join(["%s"] * len(columns))
            updates = [f"{key}=EXCLUDED.{key}" for key, _ in CATEGORIES]
            updates += ["monthly_income=EXCLUDED.monthly_income",
                        "saved_money=EXCLUDED.saved_money"]
            values = [session["user_id"], year, month, income_amount]
            values += [amounts[key] for key, _ in CATEGORIES] + [saved]
            cur.execute(
                f"INSERT INTO expenses ({', '.join(columns)}) VALUES ({placeholders}) "
                f"ON CONFLICT (user_id, year, month) DO UPDATE SET {', '.join(updates)}",
                values
            )
            conn.commit()
            return redirect(url_for("expenses", year=year, message=T("saved_success")))
        except (ValueError, InvalidOperation):
            error = T("invalid_amount")
        except Exception as exc:
            if conn:
                conn.rollback()
            app.logger.exception("Unable to save expenditure record: %s", exc)
            error = "Could not save record. Please check your database configuration."
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    rows = fetch_expenses(selected_year)
    total_income = sum(r["monthly_income"] for r in rows)
    total_expenses = sum(r["total_expense"] for r in rows)
    total_savings = total_income - total_expenses
    expense_pct = total_expenses / total_income * 100 if total_income else 0
    saving_pct = total_savings / total_income * 100 if total_income else 0
    category_totals = {key: sum(r[key] for r in rows) for key, _ in CATEGORIES}
    highest_category = max(category_totals, key=category_totals.get) if rows else None
    highest_category_label = dict(CATEGORIES).get(highest_category) if highest_category else None
    highest_expense_row = max(rows, key=lambda r: r["total_expense"]) if rows else None
    highest_saving_row = max(rows, key=lambda r: r["saved_money"]) if rows else None

    body = """
    <div class="card">
      <h2>{{ t('expense_title') }}</h2>
      {% if message %}<div class="message">{{ message }}</div>{% endif %}
      {% if error %}<div class="message">{{ error }}</div>{% endif %}
      <form method="post">
        <div class="grid">
          <div>
            <label>{{ t('year') }}</label>
            <select name="year">
              {% for y in years %}<option value="{{ y }}" {% if y==selected_year %}selected{% endif %}>{{ y }}</option>{% endfor %}
            </select>
          </div>
          <div>
            <label>{{ t('month') }}</label>
            <select name="month" required>
              {% for m in months %}<option value="{{ m }}">{{ m }}</option>{% endfor %}
            </select>
          </div>
          <div>
            <label>{{ t('monthly_income') }} (₹)</label>
            <input type="number" min="0" step="0.01" name="monthly_income" placeholder="Enter monthly income" required>
          </div>
          {% for key, label in categories %}
          <div>
            <label>{{ label }} (₹)</label>
            <input type="number" min="0" step="0.01" name="{{ key }}" placeholder="Enter {{ label|lower }} amount">
          </div>
          {% endfor %}
        </div>
        <button type="submit">{{ t('save_month') }}</button>
      </form>
    </div>

    <!-- Saved records are shown before the comparison section. -->
    <div class="card">
      <h2>Saved Records — {{ selected_year }}</h2>
      <form method="get">
        <label>{{ t('select_year') }}</label>
        <select name="year">
          {% for y in years %}<option value="{{ y }}" {% if y==selected_year %}selected{% endif %}>{{ y }}</option>{% endfor %}
        </select>
        <button type="submit">View Records</button>
      </form>
      {% if rows %}
      <div class="table-wrap"><table>
        <tr>
          <th>{{ t('month') }}</th><th>{{ t('monthly_income') }}</th>
          {% for key,label in categories %}<th>{{ label }}</th>{% endfor %}
          <th>{{ t('total_expense') }}</th><th>{{ t('saved') }}</th><th>{{ t('actions') }}</th>
        </tr>
        {% for r in rows %}
        <tr>
          <td>{{ r.month }}</td>
          <td>₹{{ '{:,.2f}'.format(r.monthly_income) }}</td>
          {% for key,label in categories %}<td>₹{{ '{:,.2f}'.format(r[key]) }}</td>{% endfor %}
          <td>₹{{ '{:,.2f}'.format(r.total_expense) }}</td>
          <td>₹{{ '{:,.2f}'.format(r.saved_money) }}</td>
          <td>
            <a class="btn orange" href="/expenses/edit/{{ r.id }}">{{ t('edit') }}</a>
            <form method="post" action="/expenses/delete/{{ r.id }}"
                  onsubmit="return confirm('Delete this monthly record?');" style="display:inline">
              <button class="red" type="submit">{{ t('delete') }}</button>
            </form>
          </td>
        </tr>
        {% endfor %}
      </table></div>
      <h3>Category-wise Yearly Expenses</h3>
      <div class="table-wrap"><table>
        <tr><th>Category</th><th>Total</th></tr>
        {% for key,label in categories %}
        <tr><td>{{ label }}</td><td>₹{{ '{:,.2f}'.format(category_totals[key]) }}</td></tr>
        {% endfor %}
      </table></div>
      {% else %}
      <p class="center">{{ t('no_data') }}</p>
      {% endif %}
    </div>

    <div class="card">
      <h2>{{ selected_year }} {{ t('comparison') }}</h2>
      {% if rows %}
      <div class="comparison-row">
        <div class="stat"><b>{{ t('total_income') }}</b><h3>₹{{ '{:,.2f}'.format(total_income) }}</h3></div>
        <div class="stat"><b>{{ t('total_expense') }}</b><h3>₹{{ '{:,.2f}'.format(total_expenses) }}</h3></div>
        <div class="stat"><b>{{ t('total_savings') }}</b><h3>₹{{ '{:,.2f}'.format(total_savings) }}</h3></div>
        <div class="stat"><b>{{ t('expense_percent') }}</b><h3>{{ '{:.2f}'.format(expense_pct) }}%</h3></div>
        <div class="stat"><b>{{ t('saving_percent') }}</b><h3>{{ '{:.2f}'.format(saving_pct) }}%</h3></div>
      </div>
      <div class="message">
        <p><b>{{ t('highest_expense') }}:</b> {{ highest_category_label or 'N/A' }}</p>
        <p><b>{{ t('highest_month') }}:</b>
          {% if highest_expense_row %}{{ highest_expense_row.month }} (₹{{ '{:,.2f}'.format(highest_expense_row.total_expense) }}){% else %}N/A{% endif %}
        </p>
        <p><b>{{ t('highest_saving_month') }}:</b>
          {% if highest_saving_row %}{{ highest_saving_row.month }} (₹{{ '{:,.2f}'.format(highest_saving_row.saved_money) }}){% else %}N/A{% endif %}
        </p>
        <p><b>{{ t('suggestion') }}:</b>
          {% if total_savings < 0 %}Your expenditure is higher than your income. Review your expenses.{% else %}{{ t('recommendation') }}{% endif %}
        </p>
      </div>
      {% else %}
      <p class="center">{{ t('no_data') }}</p>
      {% endif %}
    </div>
    <div class="center"><a class="btn gray" href="/dashboard">{{ t('back') }}</a></div>
    """
    return page(
        "Expenditure", body, rows=rows, years=YEARS, months=MONTHS,
        categories=CATEGORIES, selected_year=selected_year, message=message,
        error=error, total_income=total_income, total_expenses=total_expenses,
        total_savings=total_savings, expense_pct=expense_pct, saving_pct=saving_pct,
        highest_category_label=highest_category_label,
        highest_expense_row=highest_expense_row,
        highest_saving_row=highest_saving_row, category_totals=category_totals
    )

@app.route("/expenses/edit/<int:record_id>", methods=["GET", "POST"])
def edit_expense(record_id):
    if not logged_in():
        return redirect(url_for("login"))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, year, month, monthly_income, rent, electricity, medical,
               travel, food, shopping, education, mobile, entertainment, others
        FROM expenses WHERE id=%s AND user_id=%s
    """, (record_id, session["user_id"]))
    record = cur.fetchone()
    if not record:
        cur.close()
        conn.close()
        return redirect(url_for("expenses"))

    error = ""
    current = record
    if request.method == "POST":
        try:
            year = int(request.form.get("year", "2026"))
            month = request.form.get("month", "")
            if year not in YEARS or month not in MONTHS:
                raise ValueError("Invalid year/month")
            income_amount = parse_amount(request.form.get("monthly_income", ""))
            amounts = {key: parse_amount(request.form.get(key, ""))
                       for key, _ in CATEGORIES}
            total = sum(amounts.values(), Decimal("0"))
            saved = income_amount - total
            cur.execute("""
                UPDATE expenses SET year=%s, month=%s, monthly_income=%s,
                    rent=%s, electricity=%s, medical=%s, travel=%s, food=%s,
                    shopping=%s, education=%s, mobile=%s, entertainment=%s,
                    others=%s, saved_money=%s
                WHERE id=%s AND user_id=%s
            """, (
                year, month, income_amount, amounts["rent"], amounts["electricity"],
                amounts["medical"], amounts["travel"], amounts["food"],
                amounts["shopping"], amounts["education"], amounts["mobile"],
                amounts["entertainment"], amounts["others"], saved,
                record_id, session["user_id"]
            ))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for("expenses", year=year, message=T("saved_success")))
        except (ValueError, InvalidOperation):
            error = T("invalid_amount")
        except Exception:
            conn.rollback()
            error = "Unable to update. This year/month may already have a record."

    data = {
        "id": current[0], "year": current[1], "month": current[2],
        "monthly_income": current[3]
    }
    for index, (key, _) in enumerate(CATEGORIES, start=4):
        data[key] = current[index]

    body = """
    <div class="card">
      <h2>Edit Monthly Record</h2>
      {% if error %}<div class="message">{{ error }}</div>{% endif %}
      <form method="post">
        <label>{{ t('year') }}</label>
        <select name="year">{% for y in years %}<option value="{{ y }}" {% if y==data.year %}selected{% endif %}>{{ y }}</option>{% endfor %}</select>
        <label>{{ t('month') }}</label>
        <select name="month">{% for m in months %}<option value="{{ m }}" {% if m==data.month %}selected{% endif %}>{{ m }}</option>{% endfor %}</select>
        <label>{{ t('monthly_income') }}</label>
        <input type="number" min="0" step="0.01" name="monthly_income" value="{{ data.monthly_income }}" required>
        {% for key,label in categories %}
        <label>{{ label }}</label>
        <input type="number" min="0" step="0.01" name="{{ key }}" value="{{ data[key] }}" placeholder="Enter amount">
        {% endfor %}
        <button>{{ t('update') }}</button>
        <a class="btn gray" href="/expenses?year={{ data.year }}">{{ t('cancel') }}</a>
      </form>
    </div>
    """
    response = page("Edit Expense", body, data=data, error=error,
                    years=YEARS, months=MONTHS, categories=CATEGORIES)
    cur.close()
    conn.close()
    return response

@app.route("/expenses/delete/<int:record_id>", methods=["POST"])
def delete_expense(record_id):
    if not logged_in():
        return redirect(url_for("login"))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM expenses WHERE id=%s AND user_id=%s",
                (record_id, session["user_id"]))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("expenses", message=T("deleted_success")))

try:
    init_db()
except Exception as exc:
    print("Database initialization error:", exc)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
