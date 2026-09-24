from flask import Flask, request, redirect, url_for, session, render_template_string
import psycopg2
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")

DATABASE_URL = os.environ.get("DATABASE_URL")


# =========================================================
# DATABASE
# =========================================================

def get_db():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_db()
    cur = conn.cursor()

    # USERS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # EXPENSES
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, year, month)
        )
    """)

    # Migration
    cur.execute("""
        ALTER TABLE expenses
        ADD COLUMN IF NOT EXISTS year INTEGER DEFAULT 2026
    """)

    cur.execute("""
        UPDATE expenses
        SET year = 2026
        WHERE year IS NULL
    """)

    # Remove old unique constraint
    cur.execute("""
        ALTER TABLE expenses
        DROP CONSTRAINT IF EXISTS expenses_user_id_month_key
    """)

    # Correct unique constraint
    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'expenses_user_year_month_key'
            ) THEN
                ALTER TABLE expenses
                ADD CONSTRAINT expenses_user_year_month_key
                UNIQUE(user_id, year, month);
            END IF;
        END $$;
    """)

    conn.commit()
    cur.close()
    conn.close()


# =========================================================
# LANGUAGE
# =========================================================

TEXTS = {

    "English": {
        "dashboard": "Dashboard",
        "income": "Income",
        "expenses": "Expenditure",
        "logout": "Logout",
        "login": "Login",
        "register": "Create Account",
        "username": "Username",
        "password": "Password",
        "annual_income": "ENTER ANNUAL INCOME",
        "calculate": "Calculate Tax",
        "tax": "Total Tax",
        "monthly_after_tax": "Monthly Income After Tax",
        "back": "Back to Dashboard",
        "year": "Year",
        "month": "Month",
        "monthly_income": "Income",
        "save_month": "Save Month",
        "home": "Home Rent",
        "electricity": "Electricity",
        "hospital": "Hospital / Medical",
        "travel": "Travelling",
        "food": "Food",
        "shopping": "Shopping",
        "education": "Education",
        "mobile": "Mobile / Internet",
        "entertainment": "Entertainment",
        "others": "Others",
        "total_expense": "Total Expenditure",
        "saved": "Saved Money",
        "analysis": "Financial Analysis",
        "highest_expense": "Highest Expense",
        "highest_month": "Highest Expenditure Month",
        "highest_saving_month": "Highest Saving Month",
        "expense_percent": "Expense Percentage",
        "saving_percent": "Savings Percentage",
        "comparison": "Monthly Comparison",
        "suggestion": "Suggestion",
        "year_summary": "Year Summary",
        "total_income": "Total Income",
        "total_savings": "Total Savings",
        "no_data": "No data available for this year.",
        "select_year": "Select Year",
        "select_month": "Select Month",
        "invalid_login": "Invalid username or password.",
        "account_exists": "Username already exists.",
        "account_created": "Account created successfully. Please login.",
        "welcome": "Welcome",
        "edit": "Edit",
        "update": "Update",
        "cancel": "Cancel"
    },

    "Telugu": {
        "dashboard": "డాష్‌బోర్డ్",
        "income": "ఆదాయం",
        "expenses": "ఖర్చులు",
        "logout": "లాగ్ అవుట్",
        "login": "లాగిన్",
        "register": "అకౌంట్ క్రియేట్ చేయండి",
        "username": "యూజర్‌నేమ్",
        "password": "పాస్‌వర్డ్",
        "annual_income": "వార్షిక ఆదాయం నమోదు చేయండి",
        "calculate": "ట్యాక్స్ లెక్కించండి",
        "tax": "మొత్తం ట్యాక్స్",
        "monthly_after_tax": "ట్యాక్స్ తర్వాత నెలవారీ ఆదాయం",
        "back": "డాష్‌బోర్డ్‌కు తిరిగి వెళ్ళండి",
        "year": "సంవత్సరం",
        "month": "నెల",
        "monthly_income": "ఆదాయం",
        "save_month": "నెలను సేవ్ చేయండి",
        "home": "ఇంటి అద్దె",
        "electricity": "కరెంట్",
        "hospital": "హాస్పిటల్ / మెడికల్",
        "travel": "ప్రయాణం",
        "food": "ఆహారం",
        "shopping": "షాపింగ్",
        "education": "విద్య",
        "mobile": "మొబైల్ / ఇంటర్నెట్",
        "entertainment": "ఎంటర్‌టైన్‌మెంట్",
        "others": "ఇతరాలు",
        "total_expense": "మొత్తం ఖర్చు",
        "saved": "మిగిలిన డబ్బు",
        "analysis": "ఆర్థిక విశ్లేషణ",
        "highest_expense": "అత్యధిక ఖర్చు",
        "highest_month": "అత్యధిక ఖర్చు చేసిన నెల",
        "highest_saving_month": "అత్యధిక సేవింగ్ ఉన్న నెల",
        "expense_percent": "ఖర్చు శాతం",
        "saving_percent": "సేవింగ్ శాతం",
        "comparison": "నెలవారీ పోలిక",
        "suggestion": "సూచన",
        "year_summary": "సంవత్సర సారాంశం",
        "total_income": "మొత్తం ఆదాయం",
        "total_savings": "మొత్తం సేవింగ్స్",
        "no_data": "ఈ సంవత్సరానికి డేటా లేదు.",
        "select_year": "సంవత్సరం ఎంచుకోండి",
        "select_month": "నెల ఎంచుకోండి",
        "invalid_login": "యూజర్‌నేమ్ లేదా పాస్‌వర్డ్ తప్పు.",
        "account_exists": "ఈ యూజర్‌నేమ్ ఇప్పటికే ఉంది.",
        "account_created": "అకౌంట్ విజయవంతంగా క్రియేట్ అయింది. ఇప్పుడు లాగిన్ చేయండి.",
        "welcome": "స్వాగతం",
        "edit": "ఎడిట్",
        "update": "అప్‌డేట్",
        "cancel": "రద్దు చేయండి"
    },

    "Hindi": {
        "dashboard": "डैशबोर्ड",
        "income": "आय",
        "expenses": "खर्च",
        "logout": "लॉग आउट",
        "login": "लॉगिन",
        "register": "अकाउंट बनाएं",
        "username": "यूज़रनेम",
        "password": "पासवर्ड",
        "annual_income": "वार्षिक आय दर्ज करें",
        "calculate": "टैक्स कैलकुलेट करें",
        "tax": "कुल टैक्स",
        "monthly_after_tax": "टैक्स के बाद मासिक आय",
        "back": "डैशबोर्ड पर वापस जाएं",
        "year": "वर्ष",
        "month": "महीना",
        "monthly_income": "आय",
        "save_month": "महीना सेव करें",
        "home": "घर का किराया",
        "electricity": "बिजली",
        "hospital": "अस्पताल / मेडिकल",
        "travel": "यात्रा",
        "food": "भोजन",
        "shopping": "शॉपिंग",
        "education": "शिक्षा",
        "mobile": "मोबाइल / इंटरनेट",
        "entertainment": "मनोरंजन",
        "others": "अन्य",
        "total_expense": "कुल खर्च",
        "saved": "बचत",
        "analysis": "वित्तीय विश्लेषण",
        "highest_expense": "सबसे अधिक खर्च",
        "highest_month": "सबसे अधिक खर्च वाला महीना",
        "highest_saving_month": "सबसे अधिक बचत वाला महीना",
        "expense_percent": "खर्च प्रतिशत",
        "saving_percent": "बचत प्रतिशत",
        "comparison": "मासिक तुलना",
        "suggestion": "सुझाव",
        "year_summary": "वार्षिक सारांश",
        "total_income": "कुल आय",
        "total_savings": "कुल बचत",
        "no_data": "इस वर्ष का कोई डेटा नहीं है।",
        "select_year": "वर्ष चुनें",
        "select_month": "महीना चुनें",
        "invalid_login": "यूज़रनेम या पासवर्ड गलत है।",
        "account_exists": "यूज़रनेम पहले से मौजूद है।",
        "account_created": "अकाउंट सफलतापूर्वक बन गया। अब लॉगिन करें।",
        "welcome": "स्वागत है",
        "edit": "एडिट",
        "update": "अपडेट",
        "cancel": "रद्द करें"
    }
}


def get_lang():
    return session.get("lang", "English")


def T(key):
    return TEXTS[get_lang()].get(key, key)


# =========================================================
# COMMON HTML
# =========================================================

STYLE = """
<style>
body {
    font-family: Arial, sans-serif;
    background: #f4f7fb;
    margin: 0;
    padding: 20px;
    color: #222;
}

.container {
    max-width: 1100px;
    margin: auto;
}

.card {
    background: white;
    padding: 22px;
    border-radius: 15px;
    box-shadow: 0 3px 15px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}

h1, h2, h3 {
    text-align: center;
}

input, select {
    width: 100%;
    padding: 12px;
    margin: 7px 0 14px;
    border: 1px solid #ccc;
    border-radius: 8px;
    box-sizing: border-box;
}

button, .btn {
    display: inline-block;
    padding: 12px 18px;
    border: none;
    border-radius: 8px;
    background: #2563eb;
    color: white;
    cursor: pointer;
    text-decoration: none;
    margin: 4px;
}

.btn-green {
    background: #16a34a;
}

.btn-red {
    background: #dc2626;
}

.btn-gray {
    background: #555;
}

.btn-edit {
    background: #f59e0b;
    color: white;
    padding: 8px 12px;
}

.center {
    text-align: center;
}

.message {
    padding: 12px;
    background: #eef6ff;
    border-radius: 8px;
    margin-bottom: 15px;
}

.summary {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.summary-box {
    flex: 1;
    min-width: 180px;
    background: #f8fafc;
    padding: 15px;
    border-radius: 10px;
    text-align: center;
}

.table-wrap {
    overflow-x: auto;
}

table {
    width: 100%;
    min-width: 1450px;
    border-collapse: collapse;
    background: white;
}

th, td {
    padding: 10px;
    border: 1px solid #ddd;
    text-align: center;
    white-space: nowrap;
}

th {
    background: #eef2ff;
}

.analysis {
    background: #f8fafc;
    padding: 15px;
    border-radius: 10px;
    margin-top: 15px;
}

.high {
    font-weight: bold;
}

@media(max-width:600px) {
    body {
        padding: 10px;
    }
}
</style>
"""


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# =========================================================
# LANGUAGE
# =========================================================

@app.route("/language/<lang>")
def language(lang):

    if lang in TEXTS:
        session["lang"] = lang

    return redirect(request.referrer or url_for("login"))


# =========================================================
# REGISTER
# =========================================================

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

            cur.execute(
                "SELECT id FROM users WHERE username=%s",
                (username,)
            )

            existing = cur.fetchone()

            if existing:
                message = T("account_exists")

            else:

                password_hash = generate_password_hash(password)

                cur.execute("""
                    INSERT INTO users(username, password_hash)
                    VALUES(%s, %s)
                """, (username, password_hash))

                conn.commit()

                cur.close()
                conn.close()

                return redirect(url_for("login"))

            cur.close()
            conn.close()

    return render_template_string("""
    {{ style|safe }}

    <div class="container">
        <div class="card">
            <h2>{{ t("register") }}</h2>

            {% if message %}
            <div class="message">{{ message }}</div>
            {% endif %}

            <form method="POST">

                <label>{{ t("username") }}</label>
                <input name="username" required>

                <label>{{ t("password") }}</label>
                <input type="password" name="password" required>

                <button type="submit">{{ t("register") }}</button>

            </form>

            <div class="center">
                <a class="btn btn-gray" href="{{ url_for('login') }}">
                    {{ t("login") }}
                </a>
            </div>

        </div>
    </div>
    """,
    style=STYLE,
    t=T,
    message=message)


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    message = ""

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, password_hash
            FROM users
            WHERE username=%s
        """, (username,))

        user = cur.fetchone()

        cur.close()
        conn.close()

        if user and check_password_hash(user[1], password):

            session["user_id"] = user[0]
            session["username"] = username

            return redirect(url_for("dashboard"))

        message = T("invalid_login")

    return render_template_string("""
    {{ style|safe }}

    <div class="container">
        <div class="card">
            <h2>{{ t("login") }}</h2>

            {% if message %}
            <div class="message">{{ message }}</div>
            {% endif %}

            <form method="POST">

                <label>{{ t("username") }}</label>
                <input name="username" required>

                <label>{{ t("password") }}</label>
                <input type="password" name="password" required>

                <button type="submit">{{ t("login") }}</button>

            </form>

            <div class="center">
                <a class="btn btn-green" href="{{ url_for('register') }}">
                    {{ t("register") }}
                </a>
            </div>

        </div>
    </div>
    """,
    style=STYLE,
    t=T,
    message=message)


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template_string("""
    {{ style|safe }}

    <div class="container">

        <div class="card center">

            <h2>{{ t("welcome") }}, {{ username }} 👋</h2>

            <a class="btn" href="{{ url_for('income') }}">
                💰 {{ t("income") }}
            </a>

            <a class="btn btn-green" href="{{ url_for('expenses') }}">
                📊 {{ t("expenses") }}
            </a>

            <br>

            <a class="btn btn-red" href="{{ url_for('logout') }}">
                {{ t("logout") }}
            </a>

        </div>

        <div class="card center">

            <a href="{{ url_for('language', lang='English') }}">English</a> |
            <a href="{{ url_for('language', lang='Telugu') }}">తెలుగు</a> |
            <a href="{{ url_for('language', lang='Hindi') }}">हिन्दी</a>

        </div>

    </div>
    """,
    style=STYLE,
    t=T,
    username=session.get("username"))


# =========================================================
# INCOME TAX
# =========================================================

@app.route("/income", methods=["GET", "POST"])
def income():

    if "user_id" not in session:
        return redirect(url_for("login"))

    tax = None
    monthly_after_tax = None
    annual_income = None

    if request.method == "POST":

        annual_income = float(
            request.form.get("annual_income", 0)
        )

        if annual_income <= 400000:
            tax = 0

        elif annual_income <= 800000:
            tax = (annual_income - 400000) * 0.05

        elif annual_income <= 1200000:
            tax = 20000 + (annual_income - 800000) * 0.10

        elif annual_income <= 1600000:
            tax = 60000 + (annual_income - 1200000) * 0.15

        elif annual_income <= 2000000:
            tax = 120000 + (annual_income - 1600000) * 0.20

        elif annual_income <= 2400000:
            tax = 200000 + (annual_income - 2000000) * 0.25

        else:
            tax = 300000 + (annual_income - 2400000) * 0.30

        if annual_income <= 1200000:
            tax = 0
        else:
            tax = tax * 1.04

        monthly_after_tax = (
            annual_income - tax
        ) / 12

    return render_template_string("""
    {{ style|safe }}

    <div class="container">

        <div class="card">

            <h2>{{ t("income") }}</h2>

            <form method="POST">

                <label>{{ t("annual_income") }}</label>

                <input
                    type="number"
                    name="annual_income"
                    placeholder="Enter annual income"
                    min="0"
                    step="0.01"
                    required
                >

                <button type="submit">
                    {{ t("calculate") }}
                </button>

            </form>

            {% if tax is not none %}

            <div class="summary">

                <div class="summary-box">
                    <b>Annual Income</b>
                    <h3>
                        ₹{{ "%.2f"|format(annual_income) }}
                    </h3>
                </div>

                <div class="summary-box">
                    <b>{{ t("tax") }}</b>
                    <h3>
                        ₹{{ "%.2f"|format(tax) }}
                    </h3>
                </div>

                <div class="summary-box">
                    <b>{{ t("monthly_after_tax") }}</b>
                    <h3>
                        ₹{{ "%.2f"|format(monthly_after_tax) }}
                    </h3>
                </div>

            </div>

            <br>

            <div class="analysis">

                <h3>
                    HOW WAS THE TAX CALCULATED BASED ON YOUR ANNUAL INCOME
                </h3>

                <p>₹0 – ₹4,00,000 → Nil</p>
                <p>₹4,00,001 – ₹8,00,000 → 5%</p>
                <p>₹8,00,001 – ₹12,00,000 → 10%</p>
                <p>₹12,00,001 – ₹16,00,000 → 15%</p>
                <p>₹16,00,001 – ₹20,00,000 → 20%</p>
                <p>₹20,00,001 – ₹24,00,000 → 25%</p>
                <p>Above ₹24,00,000 → 30%</p>

                <p>
                    <b>87A rebate:</b>
                    Applied in this simplified calculator
                    when annual income is up to ₹12,00,000.
                </p>

                <p>
                    <b>Health & Education Cess:</b> 4%
                </p>

            </div>

            {% endif %}

            <br>

            <a class="btn btn-gray"
               href="{{ url_for('dashboard') }}">
               {{ t("back") }}
            </a>

        </div>

    </div>
    """,
    style=STYLE,
    t=T,
    tax=tax,
    monthly_after_tax=monthly_after_tax,
    annual_income=annual_income)


# =========================================================
# EXPENDITURE
# =========================================================

@app.route("/expenses", methods=["GET", "POST"])
def expenses():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    selected_year = request.args.get(
        "year",
        request.form.get("year", "2026")
    )

    try:
        selected_year = int(selected_year)
    except:
        selected_year = 2026

    months = [
        "Jan", "Feb", "Mar", "Apr",
        "May", "Jun", "Jul", "Aug",
        "Sep", "Oct", "Nov", "Dec"
    ]

    categories = [
        ("rent", T("home")),
        ("electricity", T("electricity")),
        ("medical", T("hospital")),
        ("travel", T("travel")),
        ("food", T("food")),
        ("shopping", T("shopping")),
        ("education", T("education")),
        ("mobile", T("mobile")),
        ("entertainment", T("entertainment")),
        ("others", T("others"))
    ]

    # =====================================================
    # SAVE / UPDATE MONTH
    # =====================================================

    if request.method == "POST":

        month = request.form.get("month")

        def amount(name):

            value = request.form.get(
                name, ""
            ).strip()

            if value == "":
                return 0

            try:
                return float(value)
            except:
                return 0

        monthly_income = amount("monthly_income")

        rent = amount("rent")
        electricity = amount("electricity")
        medical = amount("medical")
        travel = amount("travel")
        food = amount("food")
        shopping = amount("shopping")
        education = amount("education")
        mobile = amount("mobile")
        entertainment = amount("entertainment")
        others = amount("others")

        total_expense = (
            rent +
            electricity +
            medical +
            travel +
            food +
            shopping +
            education +
            mobile +
            entertainment +
            others
        )

        saved_money = (
            monthly_income - total_expense
        )

        conn = get_db()
        cur = conn.cursor()

        # IMPORTANT:
        # Same USER + YEAR + MONTH = UPDATE
        # It will NOT create another January.
        cur.execute("""
            INSERT INTO expenses (
                user_id,
                year,
                month,
                monthly_income,
                rent,
                electricity,
                medical,
                travel,
                food,
                shopping,
                education,
                mobile,
                entertainment,
                others,
                saved_money
            )
            VALUES (
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s
            )

            ON CONFLICT(user_id, year, month)

            DO UPDATE SET
                monthly_income = EXCLUDED.monthly_income,
                rent = EXCLUDED.rent,
                electricity = EXCLUDED.electricity,
                medical = EXCLUDED.medical,
                travel = EXCLUDED.travel,
                food = EXCLUDED.food,
                shopping = EXCLUDED.shopping,
                education = EXCLUDED.education,
                mobile = EXCLUDED.mobile,
                entertainment = EXCLUDED.entertainment,
                others = EXCLUDED.others,
                saved_money = EXCLUDED.saved_money
        """, (
            user_id,
            selected_year,
            month,
            monthly_income,
            rent,
            electricity,
            medical,
            travel,
            food,
            shopping,
            education,
            mobile,
            entertainment,
            others,
            saved_money
        ))

        conn.commit()

        cur.close()
        conn.close()

        return redirect(
            url_for(
                "expenses",
                year=selected_year
            )
        )

    # =====================================================
    # GET DATA
    # =====================================================

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            month,
            monthly_income,
            rent,
            electricity,
            medical,
            travel,
            food,
            shopping,
            education,
            mobile,
            entertainment,
            others,
            saved_money
        FROM expenses
        WHERE user_id=%s
        AND year=%s
        ORDER BY
            CASE month
                WHEN 'Jan' THEN 1
                WHEN 'Feb' THEN 2
                WHEN 'Mar' THEN 3
                WHEN 'Apr' THEN 4
                WHEN 'May' THEN 5
                WHEN 'Jun' THEN 6
                WHEN 'Jul' THEN 7
                WHEN 'Aug' THEN 8
                WHEN 'Sep' THEN 9
                WHEN 'Oct' THEN 10
                WHEN 'Nov' THEN 11
                WHEN 'Dec' THEN 12
            END
    """, (
        user_id,
        selected_year
    ))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    # =====================================================
    # ANALYSIS
    # =====================================================

    total_income = 0
    total_expenses = 0
    total_savings = 0

    category_totals = {
        "Home Rent": 0,
        "Electricity": 0,
        "Hospital / Medical": 0,
        "Travelling": 0,
        "Food": 0,
        "Shopping": 0,
        "Education": 0,
        "Mobile / Internet": 0,
        "Entertainment": 0,
        "Others": 0
    }

    month_expenses = {}
    month_savings = {}

    for row in rows:

        (
            record_id,
            month,
            income_value,
            rent,
            electricity,
            medical,
            travel,
            food,
            shopping,
            education,
            mobile,
            entertainment,
            others,
            saved
        ) = row

        income_value = float(
            income_value or 0
        )

        rent = float(rent or 0)
        electricity = float(electricity or 0)
        medical = float(medical or 0)
        travel = float(travel or 0)
        food = float(food or 0)
        shopping = float(shopping or 0)
        education = float(education or 0)
        mobile = float(mobile or 0)
        entertainment = float(
            entertainment or 0
        )
        others = float(others or 0)

        saved = float(saved or 0)

        expense = (
            rent +
            electricity +
            medical +
            travel +
            food +
            shopping +
            education +
            mobile +
            entertainment +
            others
        )

        total_income += income_value
        total_expenses += expense
        total_savings += saved

        category_totals["Home Rent"] += rent
        category_totals["Electricity"] += electricity
        category_totals["Hospital / Medical"] += medical
        category_totals["Travelling"] += travel
        category_totals["Food"] += food
        category_totals["Shopping"] += shopping
        category_totals["Education"] += education
        category_totals["Mobile / Internet"] += mobile
        category_totals["Entertainment"] += entertainment
        category_totals["Others"] += others

        month_expenses[month] = expense
        month_savings[month] = saved

    # =====================================================
    # HIGHEST CATEGORY
    # =====================================================

    highest_expense_category = "None"
    highest_expense_value = 0

    if category_totals:

        highest_expense_category = max(
            category_totals,
            key=category_totals.get
        )

        highest_expense_value = (
            category_totals[
                highest_expense_category
            ]
        )

    # =====================================================
    # HIGHEST MONTH
    # =====================================================

    highest_expense_month = "None"
    highest_expense_month_value = 0

    if month_expenses:

        highest_expense_month = max(
            month_expenses,
            key=month_expenses.get
        )

        highest_expense_month_value = (
            month_expenses[
                highest_expense_month
            ]
        )

    # =====================================================
    # HIGHEST SAVING MONTH
    # =====================================================

    highest_saving_month = "None"
    highest_saving_value = 0

    if month_savings:

        highest_saving_month = max(
            month_savings,
            key=month_savings.get
        )

        highest_saving_value = (
            month_savings[
                highest_saving_month
            ]
        )

    # =====================================================
    # PERCENTAGES
    # =====================================================

    expense_percentage = 0
    saving_percentage = 0

    if total_income > 0:

        expense_percentage = (
            total_expenses /
            total_income
        ) * 100

        saving_percentage = (
            total_savings /
            total_income
        ) * 100

    # =====================================================
    # SUGGESTION
    # =====================================================

    suggestion = (
        "Your spending pattern is recorded for this year."
    )

    if total_income > 0:

        if saving_percentage < 10:

            suggestion = (
                "Your savings percentage is below 10%. "
                "Review your highest expense categories "
                "and look for areas where spending can be reduced."
            )

        elif saving_percentage < 20:

            suggestion = (
                "Your savings are between 10% and 20%. "
                "Review your largest expense category "
                "to identify possible savings."
            )

        else:

            suggestion = (
                "Your savings percentage is 20% or more. "
                "Continue monitoring your expenses and "
                "compare each month to maintain your savings."
            )

    if highest_expense_value > 0:

        suggestion += (
            f" Your highest yearly expense category is "
            f"{highest_expense_category} "
            f"(₹{highest_expense_value:,.2f})."
        )

    # =====================================================
    # MONTHLY COMPARISON
    # =====================================================

    comparison = (
        "Add at least two months to see a monthly comparison."
    )

    if len(rows) >= 2:

        previous_month = rows[-2][1]
        current_month = rows[-1][1]

        previous_expense = month_expenses.get(
            previous_month,
            0
        )

        current_expense = month_expenses.get(
            current_month,
            0
        )

        difference = (
            current_expense -
            previous_expense
        )

        if difference > 0:

            comparison = (
                f"{current_month} spending is "
                f"₹{difference:,.2f} higher than "
                f"{previous_month}."
            )

        elif difference < 0:

            comparison = (
                f"{current_month} spending is "
                f"₹{abs(difference):,.2f} lower than "
                f"{previous_month}."
            )

        else:

            comparison = (
                f"{current_month} and "
                f"{previous_month} have the same "
                f"expenditure."
            )

    # =====================================================
    # PAGE
    # =====================================================

    return render_template_string("""
    {{ style|safe }}

    <div class="container">

        <!-- YEAR -->

        <div class="card">

            <h2>📊 {{ t("expenses") }}</h2>

            <form method="GET">

                <label>{{ t("select_year") }}</label>

                <select
                    name="year"
                    onchange="this.form.submit()"
                >

                    {% for y in years %}

                    <option
                        value="{{ y }}"
                        {% if y == selected_year %}
                        selected
                        {% endif %}
                    >
                        {{ y }}
                    </option>

                    {% endfor %}

                </select>

            </form>

        </div>


        <!-- ADD / UPDATE MONTH -->

        <div class="card">

            <h3>{{ t("save_month") }}</h3>

            <form method="POST">

                <input
                    type="hidden"
                    name="year"
                    value="{{ selected_year }}"
                >

                <label>{{ t("select_month") }}</label>

                <select name="month" required>

                    {% for m in months %}

                    <option value="{{ m }}">
                        {{ m }}
                    </option>

                    {% endfor %}

                </select>


                <label>{{ t("monthly_income") }}</label>

                <input
                    type="number"
                    name="monthly_income"
                    placeholder="Enter amount"
                    min="0"
                    step="0.01"
                >


                {% for field, label in categories %}

                <label>{{ label }}</label>

                <input
                    type="number"
                    name="{{ field }}"
                    placeholder="Enter amount"
                    min="0"
                    step="0.01"
                >

                {% endfor %}


                <button
                    type="submit"
                    class="btn-green"
                >
                    {{ t("save_month") }}
                </button>

            </form>

        </div>


        <!-- ONE YEAR TABLE -->

        <div class="card">

            <h3>
                {{ selected_year }} -
                {{ t("expenses") }}
            </h3>

            {% if rows %}

            <div class="table-wrap">

                <table>

                    <tr>

                        <th>{{ t("month") }}</th>

                        <th>
                            {{ t("monthly_income") }}
                        </th>

                        {% for field, label in categories %}

                        <th>{{ label }}</th>

                        {% endfor %}

                        <th>
                            {{ t("total_expense") }}
                        </th>

                        <th>
                            {{ t("saved") }}
                        </th>

                        <th>
                            Action
                        </th>

                    </tr>


                    {% for row in rows %}

                    <tr>

                        <!-- Month -->

                        <td>
                            <b>{{ row[1] }}</b>
                        </td>


                        <!-- Income -->

                        <td>
                            ₹{{ "%.2f"|format(
                                row[2] or 0
                            ) }}
                        </td>


                        <!-- Rent -->

                        <td>
                            ₹{{ "%.2f"|format(
                                row[3] or 0
                            ) }}
                        </td>


                        <!-- Electricity -->

                        <td>
                            ₹{{ "%.2f"|format(
                                row[4] or 0
                            ) }}
                        </td>


                        <!-- Medical -->

                        <td>
                            ₹{{ "%.2f"|format(
                                row[5] or 0
                            ) }}
                        </td>


                        <!-- Travel -->

                        <td>
                            ₹{{ "%.2f"|format(
                                row[6] or 0
                            ) }}
                        </td>


                        <!-- Food -->

                        <td>
                            ₹{{ "%.2f"|format(
                                row[7] or 0
                            ) }}
                        </td>


                        <!-- Shopping -->

                        <td>
                            ₹{{ "%.2f"|format(
                                row[8] or 0
                            ) }}
                        </td>


                        <!-- Education -->

                        <td>
                            ₹{{ "%.2f"|format(
                                row[9] or 0
                            ) }}
                        </td>


                        <!-- Mobile -->

                        <td>
                            ₹{{ "%.2f"|format(
                                row[10] or 0
                            ) }}
                        </td>


                        <!-- Entertainment -->

                        <td>
                            ₹{{ "%.2f"|format(
                                row[11] or 0
                            ) }}
                        </td>


                        <!-- Others -->

                        <td>
                            ₹{{ "%.2f"|format(
                                row[12] or 0
                            ) }}
                        </td>


                        <!-- Total Expense -->

                        <td>

                            ₹{{
                                "%.2f"|format(
                                    (row[3] or 0) +
                                    (row[4] or 0) +
                                    (row[5] or 0) +
                                    (row[6] or 0) +
                                    (row[7] or 0) +
                                    (row[8] or 0) +
                                    (row[9] or 0) +
                                    (row[10] or 0) +
                                    (row[11] or 0) +
                                    (row[12] or 0)
                                )
                            }}

                        </td>


                        <!-- Saved -->

                        <td>

                            ₹{{ "%.2f"|format(
                                row[13] or 0
                            ) }}

                        </td>


                        <!-- EDIT -->

                        <td>

                            <a
                                class="btn btn-edit"
                                href="{{
                                    url_for(
                                        'edit_expense',
                                        expense_id=row[0]
                                    )
                                }}"
                            >
                                ✏️ {{ t("edit") }}
                            </a>

                        </td>

                    </tr>

                    {% endfor %}

                </table>

            </div>


            <!-- YEAR SUMMARY -->

            <div class="summary">

                <div class="summary-box">

                    <b>{{ t("total_income") }}</b>

                    <h3>
                        ₹{{ "%.2f"|format(
                            total_income
                        ) }}
                    </h3>

                </div>


                <div class="summary-box">

                    <b>{{ t("total_expense") }}</b>

                    <h3>
                        ₹{{ "%.2f"|format(
                            total_expenses
                        ) }}
                    </h3>

                </div>


                <div class="summary-box">

                    <b>{{ t("total_savings") }}</b>

                    <h3>
                        ₹{{ "%.2f"|format(
                            total_savings
                        ) }}
                    </h3>

                </div>

            </div>


            <!-- ANALYSIS -->

            <div class="analysis">

                <h3>
                    📊 {{ t("analysis") }}
                </h3>

                <p>

                    <b>
                        {{ t("highest_expense") }}:
                    </b>

                    {{ highest_expense_category }}

                    —
                    ₹{{ "%.2f"|format(
                        highest_expense_value
                    ) }}

                </p>


                <p>

                    <b>
                        {{ t("highest_month") }}:
                    </b>

                    {{ highest_expense_month }}

                    —
                    ₹{{ "%.2f"|format(
                        highest_expense_month_value
                    ) }}

                </p>


                <p>

                    <b>
                        {{ t("highest_saving_month") }}:
                    </b>

                    {{ highest_saving_month }}

                    —
                    ₹{{ "%.2f"|format(
                        highest_saving_value
                    ) }}

                </p>


                <p>

                    <b>
                        {{ t("expense_percent") }}:
                    </b>

                    {{ "%.2f"|format(
                        expense_percentage
                    ) }}%

                </p>


                <p>

                    <b>
                        {{ t("saving_percent") }}:
                    </b>

                    {{ "%.2f"|format(
                        saving_percentage
                    ) }}%

                </p>

            </div>


            <!-- COMPARISON -->

            <div class="analysis">

                <h3>
                    📈 {{ t("comparison") }}
                </h3>

                <p>
                    {{ comparison }}
                </p>

            </div>


            <!-- SUGGESTION -->

            <div class="analysis">

                <h3>
                    💡 {{ t("suggestion") }}
                </h3>

                <p>
                    {{ suggestion }}
                </p>

            </div>


            <!-- CATEGORY COMPARISON -->

            <div class="analysis">

                <h3>
                    📊 Category-wise Comparison
                </h3>

                <div class="table-wrap">

                    <table>

                        <tr>

                            <th>Category</th>

                            <th>Total</th>

                            <th>
                                Percentage of Expenses
                            </th>

                        </tr>


                        {% for name, value
                           in category_totals.items() %}

                        <tr>

                            <td>
                                {{ name }}
                            </td>

                            <td>
                                ₹{{ "%.2f"|format(
                                    value
                                ) }}
                            </td>

                            <td>

                                {% if total_expenses > 0 %}

                                {{
                                    "%.2f"|format(
                                        (value /
                                        total_expenses)
                                        * 100
                                    )
                                }}%

                                {% else %}

                                0%

                                {% endif %}

                            </td>

                        </tr>

                        {% endfor %}

                    </table>

                </div>

            </div>


            {% else %}

            <div class="message">

                {{ t("no_data") }}

            </div>

            {% endif %}

        </div>


        <div class="center">

            <a
                class="btn btn-gray"
                href="{{ url_for('dashboard') }}"
            >
                {{ t("back") }}
            </a>

        </div>

    </div>
    """,
    style=STYLE,
    t=T,
    selected_year=selected_year,
    years=list(range(2023, 2031)),
    months=months,
    categories=categories,
    rows=rows,
    total_income=total_income,
    total_expenses=total_expenses,
    total_savings=total_savings,
    category_totals=category_totals,
    highest_expense_category=highest_expense_category,
    highest_expense_value=highest_expense_value,
    highest_expense_month=highest_expense_month,
    highest_expense_month_value=highest_expense_month_value,
    highest_saving_month=highest_saving_month,
    highest_saving_value=highest_saving_value,
    expense_percentage=expense_percentage,
    saving_percentage=saving_percentage,
    comparison=comparison,
    suggestion=suggestion)


# =========================================================
# EDIT EXPENDITURE
# =========================================================

@app.route("/edit_expense/<int:expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()

    # Get only logged-in user's record
    cur.execute("""
        SELECT
            id,
            year,
            month,
            monthly_income,
            rent,
            electricity,
            medical,
            travel,
            food,
            shopping,
            education,
            mobile,
            entertainment,
            others
        FROM expenses
        WHERE id=%s
        AND user_id=%s
    """, (
        expense_id,
        session["user_id"]
    ))

    row = cur.fetchone()

    if not row:

        cur.close()
        conn.close()

        return "Expense record not found."

    # =====================================================
    # UPDATE
    # =====================================================

    if request.method == "POST":

        def amount(name):

            value = request.form.get(
                name,
                ""
            ).strip()

            if value == "":
                return 0

            try:
                return float(value)
            except:
                return 0

        monthly_income = amount(
            "monthly_income"
        )

        rent = amount("rent")
        electricity = amount("electricity")
        medical = amount("medical")
        travel = amount("travel")
        food = amount("food")
        shopping = amount("shopping")
        education = amount("education")
        mobile = amount("mobile")
        entertainment = amount(
            "entertainment"
        )
        others = amount("others")

        total_expense = (
            rent +
            electricity +
            medical +
            travel +
            food +
            shopping +
            education +
            mobile +
            entertainment +
            others
        )

        saved_money = (
            monthly_income -
            total_expense
        )

        cur.execute("""
            UPDATE expenses

            SET
                monthly_income=%s,
                rent=%s,
                electricity=%s,
                medical=%s,
                travel=%s,
                food=%s,
                shopping=%s,
                education=%s,
                mobile=%s,
                entertainment=%s,
                others=%s,
                saved_money=%s

            WHERE id=%s
            AND user_id=%s
        """, (
            monthly_income,
            rent,
            electricity,
            medical,
            travel,
            food,
            shopping,
            education,
            mobile,
            entertainment,
            others,
            saved_money,
            expense_id,
            session["user_id"]
        ))

        conn.commit()

        year = row[1]

        cur.close()
        conn.close()

        return redirect(
            url_for(
                "expenses",
                year=year
            )
        )

    # =====================================================
    # EDIT FORM
    # =====================================================

    cur.close()
    conn.close()

    return render_template_string("""
    {{ style|safe }}

    <div class="container">

        <div class="card">

            <h2>
                ✏️ Edit {{ row[2] }} {{ row[1] }}
            </h2>

            <form method="POST">

                <label>
                    {{ t("monthly_income") }}
                </label>

                <input
                    type="number"
                    name="monthly_income"
                    value="{{ row[3] if row[3] is not none else '' }}"
                    placeholder="Enter amount"
                    min="0"
                    step="0.01"
                >


                <label>
                    {{ t("home") }}
                </label>

                <input
                    type="number"
                    name="rent"
                    value="{{ row[4] if row[4] is not none else '' }}"
                    placeholder="Enter amount"
                    min="0"
                    step="0.01"
                >


                <label>
                    {{ t("electricity") }}
                </label>

                <input
                    type="number"
                    name="electricity"
                    value="{{ row[5] if row[5] is not none else '' }}"
                    placeholder="Enter amount"
                    min="0"
                    step="0.01"
                >


                <label>
                    {{ t("hospital") }}
                </label>

                <input
                    type="number"
                    name="medical"
                    value="{{ row[6] if row[6] is not none else '' }}"
                    placeholder="Enter amount"
                    min="0"
                    step="0.01"
                >


                <label>
                    {{ t("travel") }}
                </label>

                <input
                    type="number"
                    name="travel"
                    value="{{ row[7] if row[7] is not none else '' }}"
                    placeholder="Enter amount"
                    min="0"
                    step="0.01"
                >


                <label>
                    {{ t("food") }}
                </label>

                <input
                    type="number"
                    name="food"
                    value="{{ row[8] if row[8] is not none else '' }}"
                    placeholder="Enter amount"
                    min="0"
                    step="0.01"
                >


                <label>
                    {{ t("shopping") }}
                </label>

                <input
                    type="number"
                    name="shopping"
                    value="{{ row[9] if row[9] is not none else '' }}"
                    placeholder="Enter amount"
                    min="0"
                    step="0.01"
                >


                <label>
                    {{ t("education") }}
                </label>

                <input
                    type="number"
                    name="education"
                    value="{{ row[10] if row[10] is not none else '' }}"
                    placeholder="Enter amount"
                    min="0"
                    step="0.01"
                >


                <label>
                    {{ t("mobile") }}
                </label>

                <input
                    type="number"
                    name="mobile"
                    value="{{ row[11] if row[11] is not none else '' }}"
                    placeholder="Enter amount"
                    min="0"
                    step="0.01"
                >


                <label>
                    {{ t("entertainment") }}
                </label>

                <input
                    type="number"
                    name="entertainment"
                    value="{{ row[12] if row[12] is not none else '' }}"
                    placeholder="Enter amount"
                    min="0"
                    step="0.01"
                >


                <label>
                    {{ t("others") }}
                </label>

                <input
                    type="number"
                    name="others"
                    value="{{ row[13] if row[13] is not none else '' }}"
                    placeholder="Enter amount"
                    min="0"
                    step="0.01"
                >


                <button
                    type="submit"
                    class="btn-green"
                >
                    💾 {{ t("update") }}
                </button>


                <a
                    class="btn btn-gray"
                    href="{{
                        url_for(
                            'expenses',
                            year=row[1]
                        )
                    }}"
                >
                    {{ t("cancel") }}
                </a>

            </form>

        </div>

    </div>
    """,
    style=STYLE,
    t=T,
    row=row)


# =========================================================
# START
# =========================================================

try:
    init_db()
except Exception as e:
    print(
        "Database initialization error:",
        e
    )


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        )
    )
