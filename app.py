import os
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, redirect, url_for, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# --------------------------------------------------
# SECURITY
# --------------------------------------------------

app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is missing. Add your Render PostgreSQL connection URL "
        "in Environment Variables."
    )


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

def get_db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            month VARCHAR(20) NOT NULL,
            monthly_income NUMERIC(15,2) NOT NULL,
            rent NUMERIC(15,2) DEFAULT 0,
            electricity NUMERIC(15,2) DEFAULT 0,
            medical NUMERIC(15,2) DEFAULT 0,
            travel NUMERIC(15,2) DEFAULT 0,
            others NUMERIC(15,2) DEFAULT 0,
            saved_money NUMERIC(15,2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, month)
        )
    """)

    conn.commit()
    cur.close()
    conn.close()


# --------------------------------------------------
# TRANSLATIONS
# --------------------------------------------------

TEXT = {
    "en": {
        "app_title": "PERSONAL FINANCE & INCOME TAX CALCULATOR",
        "login": "LOGIN",
        "create_account": "CREATE ACCOUNT",
        "username": "USERNAME",
        "password": "PASSWORD",
        "confirm_password": "CONFIRM PASSWORD",
        "register": "REGISTER",
        "already_account": "Already have an account?",
        "no_account": "Don't have an account?",
        "dashboard": "DASHBOARD",
        "income": "INCOME",
        "expenditure": "EXPENDITURE",
        "logout": "LOGOUT",
        "welcome": "Welcome",
        "enter_income": "ENTER ANNUAL INCOME",
        "calculate_tax": "CALCULATE TAX",
        "annual_income": "Annual Income",
        "annual_tax": "Annual Tax",
        "monthly_after_tax": "Monthly Income After Tax",
        "tax_calculation": "HOW WAS THE TAX CALCULATED BASED ON YOUR ANNUAL INCOME",
        "tax_slabs": "TAX SLABS",
        "slab1": "Up to ₹4,00,000",
        "slab2": "₹4,00,001 – ₹8,00,000",
        "slab3": "₹8,00,001 – ₹12,00,000",
        "slab4": "₹12,00,001 – ₹16,00,000",
        "slab5": "₹16,00,001 – ₹20,00,000",
        "slab6": "₹20,00,001 – ₹24,00,000",
        "slab7": "Above ₹24,00,000",
        "rate1": "0%",
        "rate2": "5%",
        "rate3": "10%",
        "rate4": "15%",
        "rate5": "20%",
        "rate6": "25%",
        "rate7": "30%",
        "rebate": "Section 87A rebate applied when annual income is up to ₹12 lakh.",
        "cess": "4% Health & Education Cess included.",
        "month": "MONTH",
        "monthly_income": "MONTHLY INCOME",
        "rent": "HOME RENT",
        "electricity": "ELECTRICITY",
        "medical": "HOSPITAL / MEDICAL",
        "travel": "TRAVELLING",
        "others": "OTHERS",
        "save_month": "SAVE MONTH",
        "total_expenditure": "TOTAL EXPENDITURE",
        "saved_money": "SAVED MONEY",
        "previous_months": "SAVED MONTHS",
        "no_records": "No saved records yet.",
        "account_created": "Account created successfully. Please login.",
        "wrong_login": "Invalid username or password.",
        "username_exists": "Username already exists.",
        "password_mismatch": "Passwords do not match.",
        "fill_fields": "Please fill all required fields.",
        "month_exists": "This month is already saved. It has been updated.",
        "login_required": "Please login first.",
        "language": "LANGUAGE",
        "jan": "January",
        "feb": "February",
        "mar": "March",
        "apr": "April",
        "may": "May",
        "jun": "June",
        "jul": "July",
        "aug": "August",
        "sep": "September",
        "oct": "October",
        "nov": "November",
        "dec": "December"
    },

    "te": {
        "app_title": "వ్యక్తిగత ఆర్థిక & ఆదాయ పన్ను కాలిక్యులేటర్",
        "login": "లాగిన్",
        "create_account": "అకౌంట్ సృష్టించండి",
        "username": "యూజర్ పేరు",
        "password": "పాస్‌వర్డ్",
        "confirm_password": "పాస్‌వర్డ్ నిర్ధారించండి",
        "register": "రిజిస్టర్",
        "already_account": "ఇప్పటికే అకౌంట్ ఉందా?",
        "no_account": "అకౌంట్ లేదా?",
        "dashboard": "డ్యాష్‌బోర్డ్",
        "income": "ఆదాయం",
        "expenditure": "ఖర్చులు",
        "logout": "లాగ్ అవుట్",
        "welcome": "స్వాగతం",
        "enter_income": "వార్షిక ఆదాయాన్ని నమోదు చేయండి",
        "calculate_tax": "పన్ను లెక్కించండి",
        "annual_income": "వార్షిక ఆదాయం",
        "annual_tax": "వార్షిక పన్ను",
        "monthly_after_tax": "పన్ను తర్వాత నెలవారీ ఆదాయం",
        "tax_calculation": "మీ వార్షిక ఆదాయం ఆధారంగా పన్ను ఎలా లెక్కించబడింది",
        "tax_slabs": "పన్ను స్లాబ్స్",
        "slab1": "₹4,00,000 వరకు",
        "slab2": "₹4,00,001 – ₹8,00,000",
        "slab3": "₹8,00,001 – ₹12,00,000",
        "slab4": "₹12,00,001 – ₹16,00,000",
        "slab5": "₹16,00,001 – ₹20,00,000",
        "slab6": "₹20,00,001 – ₹24,00,000",
        "slab7": "₹24,00,000 పైన",
        "rate1": "0%",
        "rate2": "5%",
        "rate3": "10%",
        "rate4": "15%",
        "rate5": "20%",
        "rate6": "25%",
        "rate7": "30%",
        "rebate": "వార్షిక ఆదాయం ₹12 లక్షల వరకు ఉంటే Section 87A రిబేట్ వర్తిస్తుంది.",
        "cess": "4% Health & Education Cess చేర్చబడింది.",
        "month": "నెల",
        "monthly_income": "నెలవారీ ఆదాయం",
        "rent": "ఇంటి అద్దె",
        "electricity": "కరెంట్",
        "medical": "హాస్పిటల్ / మెడికల్",
        "travel": "ప్రయాణం",
        "others": "ఇతరాలు",
        "save_month": "నెలను సేవ్ చేయండి",
        "total_expenditure": "మొత్తం ఖర్చు",
        "saved_money": "మిగిలిన డబ్బు",
        "previous_months": "సేవ్ చేసిన నెలలు",
        "no_records": "ఇంకా రికార్డులు లేవు.",
        "account_created": "అకౌంట్ విజయవంతంగా సృష్టించబడింది. ఇప్పుడు లాగిన్ చేయండి.",
        "wrong_login": "యూజర్ పేరు లేదా పాస్‌వర్డ్ తప్పు.",
        "username_exists": "ఈ యూజర్ పేరు ఇప్పటికే ఉంది.",
        "password_mismatch": "పాస్‌వర్డ్‌లు సరిపోలడం లేదు.",
        "fill_fields": "అవసరమైన అన్ని వివరాలను నమోదు చేయండి.",
        "month_exists": "ఈ నెల ఇప్పటికే సేవ్ చేయబడింది. అది అప్‌డేట్ చేయబడింది.",
        "login_required": "ముందుగా లాగిన్ చేయండి.",
        "language": "భాష",
        "jan": "జనవరి",
        "feb": "ఫిబ్రవరి",
        "mar": "మార్చి",
        "apr": "ఏప్రిల్",
        "may": "మే",
        "jun": "జూన్",
        "jul": "జూలై",
        "aug": "ఆగస్టు",
        "sep": "సెప్టెంబర్",
        "oct": "అక్టోబర్",
        "nov": "నవంబర్",
        "dec": "డిసెంబర్"
    },

    "hi": {
        "app_title": "व्यक्तिगत वित्त और आयकर कैलकुलेटर",
        "login": "लॉगिन",
        "create_account": "अकाउंट बनाएं",
        "username": "यूज़रनेम",
        "password": "पासवर्ड",
        "confirm_password": "पासवर्ड की पुष्टि करें",
        "register": "रजिस्टर",
        "already_account": "पहले से अकाउंट है?",
        "no_account": "अकाउंट नहीं है?",
        "dashboard": "डैशबोर्ड",
        "income": "आय",
        "expenditure": "खर्च",
        "logout": "लॉगआउट",
        "welcome": "स्वागत है",
        "enter_income": "वार्षिक आय दर्ज करें",
        "calculate_tax": "टैक्स कैलकुलेट करें",
        "annual_income": "वार्षिक आय",
        "annual_tax": "वार्षिक टैक्स",
        "monthly_after_tax": "टैक्स के बाद मासिक आय",
        "tax_calculation": "आपकी वार्षिक आय के आधार पर टैक्स की गणना",
        "tax_slabs": "टैक्स स्लैब",
        "slab1": "₹4,00,000 तक",
        "slab2": "₹4,00,001 – ₹8,00,000",
        "slab3": "₹8,00,001 – ₹12,00,000",
        "slab4": "₹12,00,001 – ₹16,00,000",
        "slab5": "₹16,00,001 – ₹20,00,000",
        "slab6": "₹20,00,001 – ₹24,00,000",
        "slab7": "₹24,00,000 से अधिक",
        "rate1": "0%",
        "rate2": "5%",
        "rate3": "10%",
        "rate4": "15%",
        "rate5": "20%",
        "rate6": "25%",
        "rate7": "30%",
        "rebate": "₹12 लाख तक की वार्षिक आय पर Section 87A rebate लागू किया गया है।",
        "cess": "4% Health & Education Cess शामिल है।",
        "month": "महीना",
        "monthly_income": "मासिक आय",
        "rent": "घर का किराया",
        "electricity": "बिजली",
        "medical": "अस्पताल / मेडिकल",
        "travel": "यात्रा",
        "others": "अन्य",
        "save_month": "महीना सेव करें",
        "total_expenditure": "कुल खर्च",
        "saved_money": "बची हुई राशि",
        "previous_months": "सेव किए गए महीने",
        "no_records": "अभी कोई रिकॉर्ड नहीं है।",
        "account_created": "अकाउंट सफलतापूर्वक बन गया। अब लॉगिन करें।",
        "wrong_login": "यूज़रनेम या पासवर्ड गलत है।",
        "username_exists": "यह यूज़रनेम पहले से मौजूद है।",
        "password_mismatch": "पासवर्ड मेल नहीं खाते।",
        "fill_fields": "सभी आवश्यक जानकारी भरें।",
        "month_exists": "यह महीना पहले से सेव है। इसे अपडेट कर दिया गया है।",
        "login_required": "पहले लॉगिन करें।",
        "language": "भाषा",
        "jan": "जनवरी",
        "feb": "फरवरी",
        "mar": "मार्च",
        "apr": "अप्रैल",
        "may": "मई",
        "jun": "जून",
        "jul": "जुलाई",
        "aug": "अगस्त",
        "sep": "सितंबर",
        "oct": "अक्टूबर",
        "nov": "नवंबर",
        "dec": "दिसंबर"
    }
}


def t(key):
    lang = session.get("lang", "en")
    return TEXT.get(lang, TEXT["en"]).get(key, key)


# --------------------------------------------------
# COMMON HTML
# --------------------------------------------------

STYLE = """
<style>
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: linear-gradient(135deg, #eef2ff, #f8fafc);
    min-height: 100vh;
    color: #111827;
}

.container {
    width: 94%;
    max-width: 650px;
    margin: 30px auto;
}

.card {
    background: white;
    border-radius: 18px;
    padding: 25px;
    margin-bottom: 20px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.08);
}

h1, h2, h3 {
    text-align: center;
}

input, select {
    width: 100%;
    padding: 13px;
    margin: 7px 0 14px;
    border: 1px solid #d1d5db;
    border-radius: 10px;
    font-size: 16px;
}

button, .btn {
    display: inline-block;
    width: 100%;
    padding: 13px;
    border: none;
    border-radius: 10px;
    background: #2563eb;
    color: white;
    font-size: 16px;
    cursor: pointer;
    text-decoration: none;
    text-align: center;
    margin-top: 8px;
}

.btn-green {
    background: #16a34a;
}

.btn-red {
    background: #dc2626;
}

.btn-gray {
    background: #4b5563;
}

.lang {
    margin-bottom: 20px;
}

.error {
    background: #fee2e2;
    color: #991b1b;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 15px;
}

.success {
    background: #dcfce7;
    color: #166534;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 15px;
}

.result {
    background: #eff6ff;
    border-radius: 14px;
    padding: 18px;
    margin-top: 20px;
}

.big {
    font-size: 25px;
    font-weight: bold;
    text-align: center;
}

.menu {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}

.month-card {
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 15px;
    margin-top: 12px;
}

.small {
    color: #6b7280;
    font-size: 14px;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
}

td, th {
    padding: 10px;
    border-bottom: 1px solid #e5e7eb;
    text-align: left;
}

@media(max-width: 500px) {
    .menu {
        grid-template-columns: 1fr;
    }
}
</style>
"""


def page(title, body):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        {STYLE}
    </head>
    <body>
        <div class="container">
            {body}
        </div>
    </body>
    </html>
    """


# --------------------------------------------------
# LANGUAGE
# --------------------------------------------------

@app.route("/language", methods=["POST"])
def language():
    selected = request.form.get("language", "en")

    if selected not in TEXT:
        selected = "en"

    session["lang"] = selected

    return redirect(request.referrer or url_for("dashboard"))


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# --------------------------------------------------
# REGISTER
# --------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    message = ""

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not username or not password or not confirm:
            message = f'<div class="error">{t("fill_fields")}</div>'

        elif password != confirm:
            message = f'<div class="error">{t("password_mismatch")}</div>'

        else:
            conn = get_db()
            cur = conn.cursor()

            cur.execute(
                "SELECT id FROM users WHERE username = %s",
                (username,)
            )

            existing = cur.fetchone()

            if existing:
                message = f'<div class="error">{t("username_exists")}</div>'

            else:
                password_hash = generate_password_hash(password)

                cur.execute(
                    """
                    INSERT INTO users (username, password_hash)
                    VALUES (%s, %s)
                    """,
                    (username, password_hash)
                )

                conn.commit()

                cur.close()
                conn.close()

                return redirect(
                    url_for("login", created="1")
                )

            cur.close()
            conn.close()

    body = f"""
    <div class="card">

        <form method="POST" action="{url_for('language')}" class="lang">
            <select name="language" onchange="this.form.submit()">
                <option value="en" {"selected" if session.get("lang","en")=="en" else ""}>
                    English
                </option>
                <option value="te" {"selected" if session.get("lang")=="te" else ""}>
                    తెలుగు
                </option>
                <option value="hi" {"selected" if session.get("lang")=="hi" else ""}>
                    हिंदी
                </option>
            </select>
        </form>

        <h1>{t("create_account")}</h1>

        {message}

        <form method="POST">

            <label>{t("username")}</label>
            <input
                type="text"
                name="username"
                required
                autocomplete="username"
            >

            <label>{t("password")}</label>
            <input
                type="password"
                name="password"
                required
                autocomplete="new-password"
            >

            <label>{t("confirm_password")}</label>
            <input
                type="password"
                name="confirm_password"
                required
                autocomplete="new-password"
            >

            <button type="submit">
                {t("register")}
            </button>

        </form>

        <p style="text-align:center">
            {t("already_account")}
        </p>

        <a class="btn btn-gray" href="{url_for('login')}">
            {t("login")}
        </a>

    </div>
    """

    return page(t("create_account"), body)


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    message = ""

    if request.args.get("created") == "1":
        message = f'<div class="success">{t("account_created")}</div>'

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT id, username, password_hash
            FROM users
            WHERE username = %s
            """,
            (username,)
        )

        user = cur.fetchone()

        cur.close()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):

            session.clear()

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["lang"] = "en"

            return redirect(url_for("dashboard"))

        message = f'<div class="error">{t("wrong_login")}</div>'

    body = f"""
    <div class="card">

        <form method="POST" action="{url_for('language')}" class="lang">
            <select name="language" onchange="this.form.submit()">
                <option value="en" {"selected" if session.get("lang","en")=="en" else ""}>
                    English
                </option>
                <option value="te" {"selected" if session.get("lang")=="te" else ""}>
                    తెలుగు
                </option>
                <option value="hi" {"selected" if session.get("lang")=="hi" else ""}>
                    हिंदी
                </option>
            </select>
        </form>

        <h1>{t("login")}</h1>

        {message}

        <form method="POST">

            <label>{t("username")}</label>
            <input
                type="text"
                name="username"
                required
                autocomplete="username"
            >

            <label>{t("password")}</label>
            <input
                type="password"
                name="password"
                required
                autocomplete="current-password"
            >

            <button type="submit">
                {t("login")}
            </button>

        </form>

        <p style="text-align:center">
            {t("no_account")}
        </p>

        <a class="btn btn-green" href="{url_for('register')}">
            {t("create_account")}
        </a>

    </div>
    """

    return page(t("login"), body)


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    body = f"""
    <div class="card">

        <form method="POST" action="{url_for('language')}" class="lang">
            <select name="language" onchange="this.form.submit()">
                <option value="en" {"selected" if session.get("lang","en")=="en" else ""}>
                    English
                </option>
                <option value="te" {"selected" if session.get("lang")=="te" else ""}>
                    తెలుగు
                </option>
                <option value="hi" {"selected" if session.get("lang")=="hi" else ""}>
                    हिंदी
                </option>
            </select>
        </form>

        <h1>{t("dashboard")}</h1>

        <p style="text-align:center">
            {t("welcome")}, <b>{session.get("username")}</b> 👋
        </p>

        <div class="menu">

            <a class="btn" href="{url_for('income')}">
                💰 {t("income")}
            </a>

            <a class="btn btn-green" href="{url_for('expenses')}">
                🧾 {t("expenditure")}
            </a>

        </div>

        <br>

        <a class="btn btn-red" href="{url_for('logout')}">
            {t("logout")}
        </a>

    </div>
    """

    return page(t("dashboard"), body)


# --------------------------------------------------
# INCOME TAX CALCULATOR
# --------------------------------------------------

def calculate_tax(income):

    if income <= 400000:
        tax = 0

    elif income <= 800000:
        tax = (income - 400000) * 0.05

    elif income <= 1200000:
        tax = 20000 + (income - 800000) * 0.10

    elif income <= 1600000:
        tax = 60000 + (income - 1200000) * 0.15

    elif income <= 2000000:
        tax = 120000 + (income - 1600000) * 0.20

    elif income <= 2400000:
        tax = 200000 + (income - 2000000) * 0.25

    else:
        tax = 300000 + (income - 2400000) * 0.30

    # Simplified 87A rule used by this project
    if income <= 1200000:
        tax = 0

    cess = tax * 0.04
    total_tax = tax + cess

    return tax, cess, total_tax


@app.route("/income", methods=["GET", "POST"])
def income():

    if "user_id" not in session:
        return redirect(url_for("login"))

    result = ""

    if request.method == "POST":

        try:
            annual_income = float(request.form.get("annual_income", 0))

            if annual_income < 0:
                annual_income = 0

            basic_tax, cess, total_tax = calculate_tax(
                annual_income
            )

            monthly_after_tax = (
                annual_income - total_tax
            ) / 12

            result = f"""
            <div class="result">

                <h2>{t("tax_calculation")}</h2>

                <p>
                    <b>{t("annual_income")}:</b>
                    ₹{annual_income:,.2f}
                </p>

                <p>
                    <b>{t("annual_tax")}:</b>
                    ₹{total_tax:,.2f}
                </p>

                <p>
                    <b>{t("monthly_after_tax")}:</b>
                </p>

                <div class="big">
                    ₹{monthly_after_tax:,.2f}
                </div>

                <hr>

                <h3>{t("tax_slabs")}</h3>

                <table>
                    <tr>
                        <th>{t("slab1")}</th>
                        <td>{t("rate1")}</td>
                    </tr>
                    <tr>
                        <th>{t("slab2")}</th>
                        <td>{t("rate2")}</td>
                    </tr>
                    <tr>
                        <th>{t("slab3")}</th>
                        <td>{t("rate3")}</td>
                    </tr>
                    <tr>
                        <th>{t("slab4")}</th>
                        <td>{t("rate4")}</td>
                    </tr>
                    <tr>
                        <th>{t("slab5")}</th>
                        <td>{t("rate5")}</td>
                    </tr>
                    <tr>
                        <th>{t("slab6")}</th>
                        <td>{t("rate6")}</td>
                    </tr>
                    <tr>
                        <th>{t("slab7")}</th>
                        <td>{t("rate7")}</td>
                    </tr>
                </table>

                <p class="small">
                    {t("rebate")}
                </p>

                <p class="small">
                    {t("cess")}
                </p>

            </div>
            """

        except ValueError:
            result = '<div class="error">Please enter a valid income.</div>'

    body = f"""
    <div class="card">

        <form method="POST" action="{url_for('language')}" class="lang">
            <select name="language" onchange="this.form.submit()">
                <option value="en" {"selected" if session.get("lang","en")=="en" else ""}>
                    English
                </option>
                <option value="te" {"selected" if session.get("lang")=="te" else ""}>
                    తెలుగు
                </option>
                <option value="hi" {"selected" if session.get("lang")=="hi" else ""}>
                    हिंदी
                </option>
            </select>
        </form>

        <h1>💰 {t("income")}</h1>

        <form method="POST">

            <label>{t("enter_income")}</label>

            <input
                type="number"
                name="annual_income"
                min="0"
                step="0.01"
                placeholder="₹"
                required
            >

            <button type="submit">
                {t("calculate_tax")}
            </button>

        </form>

        {result}

        <a class="btn btn-gray" href="{url_for('dashboard')}">
            ← {t("dashboard")}
        </a>

    </div>
    """

    return page(t("income"), body)


# --------------------------------------------------
# EXPENDITURE
# --------------------------------------------------

@app.route("/expenses", methods=["GET", "POST"])
def expenses():

    if "user_id" not in session:
        return redirect(url_for("login"))

    message = ""

    if request.method == "POST":

        try:
            month = request.form.get("month")

            monthly_income = float(
                request.form.get("monthly_income", 0)
            )

            rent = float(request.form.get("rent", 0) or 0)
            electricity = float(
                request.form.get("electricity", 0) or 0
            )
            medical = float(
                request.form.get("medical", 0) or 0
            )
            travel = float(
                request.form.get("travel", 0) or 0
            )
            others = float(
                request.form.get("others", 0) or 0
            )

            total = (
                rent
                + electricity
                + medical
                + travel
                + others
            )

            saved_money = monthly_income - total

            conn = get_db()
            cur = conn.cursor()

            cur.execute(
                """
                INSERT INTO expenses
                (
                    user_id,
                    month,
                    monthly_income,
                    rent,
                    electricity,
                    medical,
                    travel,
                    others,
                    saved_money
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)

                ON CONFLICT (user_id, month)
                DO UPDATE SET
                    monthly_income = EXCLUDED.monthly_income,
                    rent = EXCLUDED.rent,
                    electricity = EXCLUDED.electricity,
                    medical = EXCLUDED.medical,
                    travel = EXCLUDED.travel,
                    others = EXCLUDED.others,
                    saved_money = EXCLUDED.saved_money
                """,
                (
                    session["user_id"],
                    month,
                    monthly_income,
                    rent,
                    electricity,
                    medical,
                    travel,
                    others,
                    saved_money
                )
            )

            conn.commit()

            cur.close()
            conn.close()

            message = f"""
            <div class="success">
                {t("month_exists")}
            </div>
            """

        except ValueError:
            message = """
            <div class="error">
                Please enter valid numbers.
            </div>
            """

    # Get ONLY this user's records
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM expenses
        WHERE user_id = %s
        ORDER BY id DESC
        """,
        (session["user_id"],)
    )

    records = cur.fetchall()

    cur.close()
    conn.close()

    records_html = ""

    if records:

        for row in records:

            total = (
                float(row["rent"])
                + float(row["electricity"])
                + float(row["medical"])
                + float(row["travel"])
                + float(row["others"])
            )

            records_html += f"""
            <div class="month-card">

                <h3>{row["month"]}</h3>

                <p>
                    <b>{t("monthly_income")}:</b>
                    ₹{float(row["monthly_income"]):,.2f}
                </p>

                <p>
                    <b>{t("total_expenditure")}:</b>
                    ₹{total:,.2f}
                </p>

                <p>
                    <b>{t("saved_money")}:</b>
                    ₹{float(row["saved_money"]):,.2f}
                </p>

            </div>
            """

    else:
        records_html = f"""
        <p style="text-align:center">
            {t("no_records")}
        </p>
        """

    body = f"""
    <div class="card">

        <form method="POST" action="{url_for('language')}" class="lang">
            <select name="language" onchange="this.form.submit()">
                <option value="en" {"selected" if session.get("lang","en")=="en" else ""}>
                    English
                </option>
                <option value="te" {"selected" if session.get("lang")=="te" else ""}>
                    తెలుగు
                </option>
                <option value="hi" {"selected" if session.get("lang")=="hi" else ""}>
                    हिंदी
                </option>
            </select>
        </form>

        <h1>🧾 {t("expenditure")}</h1>

        {message}

        <form method="POST">

            <label>{t("month")}</label>

            <select name="month" required>
                <option value="January">{t("jan")}</option>
                <option value="February">{t("feb")}</option>
                <option value="March">{t("mar")}</option>
                <option value="April">{t("apr")}</option>
                <option value="May">{t("may")}</option>
                <option value="June">{t("jun")}</option>
                <option value="July">{t("jul")}</option>
                <option value="August">{t("aug")}</option>
                <option value="September">{t("sep")}</option>
                <option value="October">{t("oct")}</option>
                <option value="November">{t("nov")}</option>
                <option value="December">{t("dec")}</option>
            </select>

            <label>{t("monthly_income")}</label>
            <input
                type="number"
                name="monthly_income"
                min="0"
                step="0.01"
                required
            >

            <label>{t("rent")}</label>
            <input
                type="number"
                name="rent"
                min="0"
                step="0.01"
                value="0"
            >

            <label>{t("electricity")}</label>
            <input
                type="number"
                name="electricity"
                min="0"
                step="0.01"
                value="0"
            >

            <label>{t("medical")}</label>
            <input
                type="number"
                name="medical"
                min="0"
                step="0.01"
                value="0"
            >

            <label>{t("travel")}</label>
            <input
                type="number"
                name="travel"
                min="0"
                step="0.01"
                value="0"
            >

            <label>{t("others")}</label>
            <input
                type="number"
                name="others"
                min="0"
                step="0.01"
                value="0"
            >

            <button class="btn-green" type="submit">
                {t("save_month")}
            </button>

        </form>

    </div>

    <div class="card">

        <h2>{t("previous_months")}</h2>

        {records_html}

    </div>

    <div class="card">

        <a class="btn btn-gray" href="{url_for('dashboard')}">
            ← {t("dashboard")}
        </a>

    </div>
    """

    return page(t("expenditure"), body)


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# --------------------------------------------------
# START
# --------------------------------------------------

init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
