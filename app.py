import os
from flask import Flask, request, redirect, url_for, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "change-this-secret-key"
)

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing.")


# =========================================================
# DATABASE
# =========================================================

def get_db():
    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )


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
            user_id INTEGER NOT NULL
                REFERENCES users(id) ON DELETE CASCADE,

            month VARCHAR(20) NOT NULL,

            monthly_income NUMERIC(15,2) DEFAULT 0,

            rent NUMERIC(15,2) DEFAULT 0,
            electricity NUMERIC(15,2) DEFAULT 0,
            medical NUMERIC(15,2) DEFAULT 0,
            travel NUMERIC(15,2) DEFAULT 0,

            food NUMERIC(15,2) DEFAULT 0,
            shopping NUMERIC(15,2) DEFAULT 0,
            education NUMERIC(15,2) DEFAULT 0,
            mobile NUMERIC(15,2) DEFAULT 0,
            entertainment NUMERIC(15,2) DEFAULT 0,

            others NUMERIC(15,2) DEFAULT 0,

            saved_money NUMERIC(15,2) DEFAULT 0,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(user_id, month)
        )
    """)

    # -----------------------------------------------------
    # Migration for an older expenses table
    # -----------------------------------------------------

    columns = [
        ("food", "NUMERIC(15,2) DEFAULT 0"),
        ("shopping", "NUMERIC(15,2) DEFAULT 0"),
        ("education", "NUMERIC(15,2) DEFAULT 0"),
        ("mobile", "NUMERIC(15,2) DEFAULT 0"),
        ("entertainment", "NUMERIC(15,2) DEFAULT 0")
    ]

    for column, datatype in columns:
        cur.execute(
            f"""
            ALTER TABLE expenses
            ADD COLUMN IF NOT EXISTS {column} {datatype}
            """
        )

    conn.commit()

    cur.close()
    conn.close()


# =========================================================
# LANGUAGE
# =========================================================

TEXT = {

    "en": {

        "login": "LOGIN",
        "create_account": "CREATE ACCOUNT",
        "username": "USERNAME",
        "password": "PASSWORD",
        "confirm_password": "CONFIRM PASSWORD",
        "register": "REGISTER",

        "dashboard": "DASHBOARD",
        "welcome": "Welcome",
        "income": "INCOME",
        "expenditure": "EXPENDITURE",
        "logout": "LOGOUT",

        "enter_income": "ENTER ANNUAL INCOME",
        "calculate_tax": "CALCULATE TAX",

        "annual_income": "Annual Income",
        "annual_tax": "Annual Tax",
        "monthly_after_tax": "Monthly Income After Tax",

        "tax_calculation":
        "HOW WAS THE TAX CALCULATED BASED ON YOUR ANNUAL INCOME",

        "tax_slabs": "TAX SLABS",

        "month": "MONTH",
        "monthly_income": "MONTHLY INCOME",

        "rent": "HOME RENT",
        "electricity": "ELECTRICITY",
        "medical": "HOSPITAL / MEDICAL",
        "travel": "TRAVELLING",

        "food": "FOOD",
        "shopping": "SHOPPING",
        "education": "EDUCATION",
        "mobile": "MOBILE / INTERNET",
        "entertainment": "ENTERTAINMENT",
        "others": "OTHERS",

        "save_month": "SAVE MONTH",

        "total_expenditure": "TOTAL EXPENDITURE",
        "saved_money": "SAVED MONEY",

        "saved_months": "SAVED MONTHS",

        "expense_analysis": "EXPENSE ANALYSIS",
        "highest_expense": "Highest Expense",
        "expense_percentage": "Expense Percentage",
        "saving_percentage": "Savings Percentage",
        "comparison": "MONTHLY COMPARISON",
        "suggestion": "SUGGESTION",

        "increased": "Spending increased compared with the previous month.",
        "decreased": "Spending decreased compared with the previous month.",
        "same": "Spending is almost the same as the previous month.",

        "reduce":
        "This is your highest expense category. Consider reducing unnecessary spending in this category.",

        "good_saving":
        "Your savings are a good portion of your monthly income. Keep tracking your expenses.",

        "low_saving":
        "Your expenses are taking a large portion of your income. Review the highest expense categories.",

        "account_created":
        "Account created successfully. Please login.",

        "wrong_login":
        "Invalid username or password.",

        "username_exists":
        "Username already exists.",

        "password_mismatch":
        "Passwords do not match.",

        "no_records":
        "No saved records yet.",

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

        "login": "లాగిన్",
        "create_account": "అకౌంట్ సృష్టించండి",
        "username": "యూజర్ పేరు",
        "password": "పాస్‌వర్డ్",
        "confirm_password": "పాస్‌వర్డ్ నిర్ధారించండి",
        "register": "రిజిస్టర్",

        "dashboard": "డ్యాష్‌బోర్డ్",
        "welcome": "స్వాగతం",
        "income": "ఆదాయం",
        "expenditure": "ఖర్చులు",
        "logout": "లాగ్ అవుట్",

        "enter_income": "వార్షిక ఆదాయాన్ని నమోదు చేయండి",
        "calculate_tax": "పన్ను లెక్కించండి",

        "annual_income": "వార్షిక ఆదాయం",
        "annual_tax": "వార్షిక పన్ను",
        "monthly_after_tax": "పన్ను తర్వాత నెలవారీ ఆదాయం",

        "tax_calculation":
        "మీ వార్షిక ఆదాయం ఆధారంగా పన్ను ఎలా లెక్కించబడింది",

        "tax_slabs": "పన్ను స్లాబ్స్",

        "month": "నెల",
        "monthly_income": "నెలవారీ ఆదాయం",

        "rent": "ఇంటి అద్దె",
        "electricity": "కరెంట్",
        "medical": "హాస్పిటల్ / మెడికల్",
        "travel": "ప్రయాణం",

        "food": "ఆహారం",
        "shopping": "షాపింగ్",
        "education": "విద్య",
        "mobile": "మొబైల్ / ఇంటర్నెట్",
        "entertainment": "వినోదం",
        "others": "ఇతరాలు",

        "save_month": "నెలను సేవ్ చేయండి",

        "total_expenditure": "మొత్తం ఖర్చు",
        "saved_money": "మిగిలిన డబ్బు",

        "saved_months": "సేవ్ చేసిన నెలలు",

        "expense_analysis": "ఖర్చుల విశ్లేషణ",
        "highest_expense": "అత్యధిక ఖర్చు",
        "expense_percentage": "ఖర్చు శాతం",
        "saving_percentage": "పొదుపు శాతం",
        "comparison": "నెలవారీ పోలిక",
        "suggestion": "సూచన",

        "increased": "గత నెలతో పోలిస్తే ఖర్చు పెరిగింది.",
        "decreased": "గత నెలతో పోలిస్తే ఖర్చు తగ్గింది.",
        "same": "గత నెలతో పోలిస్తే ఖర్చు దాదాపు ఒకే విధంగా ఉంది.",

        "reduce":
        "ఇది మీ అత్యధిక ఖర్చు కేటగిరీ. అవసరం లేని ఖర్చులను తగ్గించడానికి ప్రయత్నించండి.",

        "good_saving":
        "మీ నెలవారీ ఆదాయంలో మంచి భాగం పొదుపు చేస్తున్నారు. ఖర్చులను ట్రాక్ చేస్తూ ఉండండి.",

        "low_saving":
        "మీ ఆదాయంలో ఎక్కువ భాగం ఖర్చవుతోంది. అత్యధిక ఖర్చు కేటగిరీలను పరిశీలించండి.",

        "account_created":
        "అకౌంట్ విజయవంతంగా సృష్టించబడింది. ఇప్పుడు లాగిన్ చేయండి.",

        "wrong_login":
        "యూజర్ పేరు లేదా పాస్‌వర్డ్ తప్పు.",

        "username_exists":
        "ఈ యూజర్ పేరు ఇప్పటికే ఉంది.",

        "password_mismatch":
        "పాస్‌వర్డ్‌లు సరిపోలడం లేదు.",

        "no_records":
        "ఇంకా రికార్డులు లేవు.",

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

        "login": "लॉगिन",
        "create_account": "अकाउंट बनाएं",
        "username": "यूज़रनेम",
        "password": "पासवर्ड",
        "confirm_password": "पासवर्ड की पुष्टि करें",
        "register": "रजिस्टर",

        "dashboard": "डैशबोर्ड",
        "welcome": "स्वागत है",
        "income": "आय",
        "expenditure": "खर्च",
        "logout": "लॉगआउट",

        "enter_income": "वार्षिक आय दर्ज करें",
        "calculate_tax": "टैक्स कैलकुलेट करें",

        "annual_income": "वार्षिक आय",
        "annual_tax": "वार्षिक टैक्स",
        "monthly_after_tax": "टैक्स के बाद मासिक आय",

        "tax_calculation":
        "आपकी वार्षिक आय के आधार पर टैक्स की गणना",

        "tax_slabs": "टैक्स स्लैब",

        "month": "महीना",
        "monthly_income": "मासिक आय",

        "rent": "घर का किराया",
        "electricity": "बिजली",
        "medical": "अस्पताल / मेडिकल",
        "travel": "यात्रा",

        "food": "खाना",
        "shopping": "शॉपिंग",
        "education": "शिक्षा",
        "mobile": "मोबाइल / इंटरनेट",
        "entertainment": "मनोरंजन",
        "others": "अन्य",

        "save_month": "महीना सेव करें",

        "total_expenditure": "कुल खर्च",
        "saved_money": "बची हुई राशि",

        "saved_months": "सेव किए गए महीने",

        "expense_analysis": "खर्च विश्लेषण",
        "highest_expense": "सबसे अधिक खर्च",
        "expense_percentage": "खर्च प्रतिशत",
        "saving_percentage": "बचत प्रतिशत",
        "comparison": "मासिक तुलना",
        "suggestion": "सुझाव",

        "increased":
        "पिछले महीने की तुलना में खर्च बढ़ा है.",

        "decreased":
        "पिछले महीने की तुलना में खर्च कम हुआ है.",

        "same":
        "पिछले महीने की तुलना में खर्च लगभग समान है.",

        "reduce":
        "यह आपका सबसे अधिक खर्च वाला वर्ग है। अनावश्यक खर्च कम करने पर विचार करें.",

        "good_saving":
        "आप अपनी मासिक आय का अच्छा हिस्सा बचा रहे हैं। खर्चों को ट्रैक करते रहें.",

        "low_saving":
        "आपकी आय का बड़ा हिस्सा खर्च हो रहा है। सबसे अधिक खर्च वाले वर्गों की समीक्षा करें.",

        "account_created":
        "अकाउंट सफलतापूर्वक बन गया। अब लॉगिन करें.",

        "wrong_login":
        "यूज़रनेम या पासवर्ड गलत है.",

        "username_exists":
        "यह यूज़रनेम पहले से मौजूद है.",

        "password_mismatch":
        "पासवर्ड मेल नहीं खाते.",

        "no_records":
        "अभी कोई रिकॉर्ड नहीं है.",

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

    return TEXT.get(
        lang,
        TEXT["en"]
    ).get(
        key,
        TEXT["en"].get(key, key)
    )


# =========================================================
# CSS
# =========================================================

STYLE = """

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: linear-gradient(135deg,#eef2ff,#f8fafc);
    color: #111827;
}

.container {
    width: 94%;
    max-width: 850px;
    margin: 25px auto;
}

.card {
    background: white;
    border-radius: 18px;
    padding: 22px;
    margin-bottom: 20px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.08);
}

h1,h2,h3 {
    text-align: center;
}

input,select {
    width: 100%;
    padding: 13px;
    margin: 7px 0 15px;
    border: 1px solid #d1d5db;
    border-radius: 10px;
    font-size: 16px;
}

button,.btn {
    display: block;
    width: 100%;
    padding: 13px;
    border: none;
    border-radius: 10px;
    background: #2563eb;
    color: white;
    font-size: 16px;
    text-decoration: none;
    text-align: center;
    cursor: pointer;
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
    padding: 18px;
    border-radius: 15px;
    margin-top: 20px;
}

.big {
    font-size: 26px;
    font-weight: bold;
    text-align: center;
}

.menu {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}

.expense-table-wrapper {
    overflow-x: auto;
    width: 100%;
}

.expense-table {
    min-width: 850px;
    border-collapse: collapse;
    width: 100%;
}

.expense-table th {
    background: #f3f4f6;
}

.expense-table th,
.expense-table td {
    border: 1px solid #e5e7eb;
    padding: 10px;
    text-align: center;
    white-space: nowrap;
}

.summary {
    display: grid;
    grid-template-columns: repeat(3,1fr);
    gap: 10px;
    margin-top: 15px;
}

.summary-box {
    background: #f8fafc;
    border-radius: 12px;
    padding: 15px;
    text-align: center;
}

.analysis {
    background: #fff7ed;
    border-radius: 14px;
    padding: 18px;
    margin-top: 15px;
}

.analysis p {
    margin: 9px 0;
}

@media(max-width:600px) {

    .menu {
        grid-template-columns: 1fr;
    }

    .summary {
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

        <meta name="viewport"
              content="width=device-width, initial-scale=1.0">

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


# =========================================================
# LANGUAGE ROUTE
# =========================================================

@app.route("/language", methods=["POST"])
def language():

    lang = request.form.get(
        "language",
        "en"
    )

    if lang not in TEXT:
        lang = "en"

    session["lang"] = lang

    return redirect(
        request.referrer or url_for("dashboard")
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    if "user_id" in session:
        return redirect(
            url_for("dashboard")
        )

    return redirect(
        url_for("login")
    )


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET","POST"])
def register():

    message = ""

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        confirm = request.form.get(
            "confirm_password",
            ""
        )

        if password != confirm:

            message = f"""
            <div class="error">
                {t("password_mismatch")}
            </div>
            """

        else:

            conn = get_db()
            cur = conn.cursor()

            cur.execute(
                "SELECT id FROM users WHERE username=%s",
                (username,)
            )

            existing = cur.fetchone()

            if existing:

                message = f"""
                <div class="error">
                    {t("username_exists")}
                </div>
                """

            else:

                password_hash = generate_password_hash(
                    password
                )

                cur.execute(
                    """
                    INSERT INTO users
                    (username,password_hash)
                    VALUES (%s,%s)
                    """,
                    (
                        username,
                        password_hash
                    )
                )

                conn.commit()

                cur.close()
                conn.close()

                return redirect(
                    url_for(
                        "login",
                        created="1"
                    )
                )

            cur.close()
            conn.close()

    body = f"""

    <div class="card">

        <h1>{t("create_account")}</h1>

        <form method="POST">

            <label>{t("username")}</label>

            <input
                name="username"
                required
            >

            <label>{t("password")}</label>

            <input
                type="password"
                name="password"
                required
            >

            <label>{t("confirm_password")}</label>

            <input
                type="password"
                name="confirm_password"
                required
            >

            <button>
                {t("register")}
            </button>

        </form>

        {message}

        <a class="btn btn-gray"
           href="{url_for('login')}">

            {t("login")}

        </a>

    </div>

    """

    return page(
        t("create_account"),
        body
    )


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET","POST"])
def login():

    message = ""

    if request.args.get("created") == "1":

        message = f"""
        <div class="success">
            {t("account_created")}
        </div>
        """

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT *
            FROM users
            WHERE username=%s
            """,
            (username,)
        )

        user = cur.fetchone()

        cur.close()
        conn.close()

        if user and check_password_hash(
            user["password_hash"],
            password
        ):

            session.clear()

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["lang"] = "en"

            return redirect(
                url_for("dashboard")
            )

        message = f"""
        <div class="error">
            {t("wrong_login")}
        </div>
        """

    body = f"""

    <div class="card">

        <h1>{t("login")}</h1>

        {message}

        <form method="POST">

            <label>{t("username")}</label>

            <input
                name="username"
                required
            >

            <label>{t("password")}</label>

            <input
                type="password"
                name="password"
                required
            >

            <button>
                {t("login")}
            </button>

        </form>

        <a class="btn btn-green"
           href="{url_for('register')}">

            {t("create_account")}

        </a>

    </div>

    """

    return page(
        t("login"),
        body
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(
            url_for("login")
        )

    body = f"""

    <div class="card">

        <h1>{t("dashboard")}</h1>

        <p style="text-align:center">

            {t("welcome")},
            <b>{session.get("username")}</b>

        </p>

        <form method="POST"
              action="{url_for('language')}">

            <label>{t("language")}</label>

            <select
                name="language"
                onchange="this.form.submit()"
            >

                <option value="en">English</option>

                <option value="te">తెలుగు</option>

                <option value="hi">हिंदी</option>

            </select>

        </form>

        <div class="menu">

            <a class="btn"
               href="{url_for('income')}">

                💰 {t("income")}

            </a>

            <a class="btn btn-green"
               href="{url_for('expenses')}">

                🧾 {t("expenditure")}

            </a>

        </div>

        <br>

        <a class="btn btn-red"
           href="{url_for('logout')}">

            {t("logout")}

        </a>

    </div>

    """

    return page(
        t("dashboard"),
        body
    )


# =========================================================
# TAX CALCULATION
# =========================================================

def calculate_tax(income):

    if income <= 400000:
        tax = 0

    elif income <= 800000:
        tax = (
            income - 400000
        ) * 0.05

    elif income <= 1200000:
        tax = (
            20000
            + (income - 800000) * 0.10
        )

    elif income <= 1600000:
        tax = (
            60000
            + (income - 1200000) * 0.15
        )

    elif income <= 2000000:
        tax = (
            120000
            + (income - 1600000) * 0.20
        )

    elif income <= 2400000:
        tax = (
            200000
            + (income - 2000000) * 0.25
        )

    else:

        tax = (
            300000
            + (income - 2400000) * 0.30
        )

    # Simplified 87A rule for this project
    if income <= 1200000:
        tax = 0

    cess = tax * 0.04

    total_tax = tax + cess

    return (
        tax,
        cess,
        total_tax
    )


# =========================================================
# INCOME
# =========================================================

@app.route("/income", methods=["GET","POST"])
def income():

    if "user_id" not in session:
        return redirect(
            url_for("login")
        )

    result = ""

    if request.method == "POST":

        try:

            annual_income = float(
                request.form.get(
                    "annual_income",
                    0
                )
            )

            basic_tax, cess, total_tax = calculate_tax(
                annual_income
            )

            monthly_after_tax = (
                annual_income - total_tax
            ) / 12

            result = f"""

            <div class="result">

                <h2>
                    {t("tax_calculation")}
                </h2>

                <p>
                    <b>{t("annual_income")}:</b>
                    ₹{annual_income:,.2f}
                </p>

                <p>
                    <b>{t("annual_tax")}:</b>
                    ₹{total_tax:,.2f}
                </p>

                <p>
                    <b>
                        {t("monthly_after_tax")}:
                    </b>
                </p>

                <div class="big">
                    ₹{monthly_after_tax:,.2f}
                </div>

            </div>

            """

        except ValueError:

            result = """
            <div class="error">
                Please enter a valid amount.
            </div>
            """

    body = f"""

    <div class="card">

        <h1>
            💰 {t("income")}
        </h1>

        <form method="POST">

            <label>
                {t("enter_income")}
            </label>

            <input
                type="number"
                name="annual_income"
                min="0"
                step="0.01"
                required
            >

            <button>
                {t("calculate_tax")}
            </button>

        </form>

        {result}

        <a class="btn btn-gray"
           href="{url_for('dashboard')}">

            ← {t("dashboard")}

        </a>

    </div>

    """

    return page(
        t("income"),
        body
    )


# =========================================================
# EXPENDITURE
# =========================================================

@app.route("/expenses", methods=["GET","POST"])
def expenses():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    message = ""

    if request.method == "POST":

        try:

            month = request.form.get(
                "month"
            )

            monthly_income = float(
                request.form.get(
                    "monthly_income"
                )
            )

            def number(name):

                value = request.form.get(
                    name,
                    ""
                ).strip()

                if value == "":
                    return 0

                return float(value)

            rent = number("rent")
            electricity = number("electricity")
            medical = number("medical")
            travel = number("travel")
            food = number("food")
            shopping = number("shopping")
            education = number("education")
            mobile = number("mobile")
            entertainment = number("entertainment")
            others = number("others")

            expenses_dict = {

                "Home Rent": rent,
                "Electricity": electricity,
                "Hospital": medical,
                "Travelling": travel,
                "Food": food,
                "Shopping": shopping,
                "Education": education,
                "Mobile / Internet": mobile,
                "Entertainment": entertainment,
                "Others": others

            }

            total = sum(
                expenses_dict.values()
            )

            saved_money = (
                monthly_income - total
            )

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
                    food,
                    shopping,
                    education,
                    mobile,
                    entertainment,
                    others,
                    saved_money
                )
                VALUES
                (
                    %s,%s,%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,%s,%s
                )

                ON CONFLICT(user_id,month)
                DO UPDATE SET

                    monthly_income =
                        EXCLUDED.monthly_income,

                    rent =
                        EXCLUDED.rent,

                    electricity =
                        EXCLUDED.electricity,

                    medical =
                        EXCLUDED.medical,

                    travel =
                        EXCLUDED.travel,

                    food =
                        EXCLUDED.food,

                    shopping =
                        EXCLUDED.shopping,

                    education =
                        EXCLUDED.education,

                    mobile =
                        EXCLUDED.mobile,

                    entertainment =
                        EXCLUDED.entertainment,

                    others =
                        EXCLUDED.others,

                    saved_money =
                        EXCLUDED.saved_money
                """,

                (
                    session["user_id"],
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
            )

            conn.commit()

            cur.close()
            conn.close()

            message = """
            <div class="success">
                Month saved successfully.
            </div>
            """

        except ValueError:

            message = """
            <div class="error">
                Please enter valid numbers.
            </div>
            """

    # -----------------------------------------------------
    # GET USER'S RECORDS
    # -----------------------------------------------------

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM expenses
        WHERE user_id=%s
        ORDER BY id DESC
        """,
        (session["user_id"],)
    )

    records = cur.fetchall()

    cur.close()
    conn.close()

    records_html = ""

    # -----------------------------------------------------
    # DISPLAY SAVED MONTHS
    # -----------------------------------------------------

    if records:

        for index, row in enumerate(records):

            categories = {

                "Home": float(row["rent"]),
                "Electricity": float(row["electricity"]),
                "Hospital": float(row["medical"]),
                "Travel": float(row["travel"]),
                "Food": float(row["food"]),
                "Shopping": float(row["shopping"]),
                "Education": float(row["education"]),
                "Mobile": float(row["mobile"]),
                "Entertainment": float(row["entertainment"]),
                "Others": float(row["others"])

            }

            total = sum(
                categories.values()
            )

            income_value = float(
                row["monthly_income"]
            )

            saved = float(
                row["saved_money"]
            )

            if income_value > 0:

                expense_percentage = (
                    total / income_value
                ) * 100

                saving_percentage = (
                    saved / income_value
                ) * 100

            else:

                expense_percentage = 0
                saving_percentage = 0

            highest_name = max(
                categories,
                key=categories.get
            )

            highest_value = categories[
                highest_name
            ]

            # -------------------------------------------------
            # PREVIOUS MONTH COMPARISON
            # -------------------------------------------------

            comparison_text = ""

            if index < len(records) - 1:

                previous = records[
                    index + 1
                ]

                previous_total = sum([

                    float(previous["rent"]),
                    float(previous["electricity"]),
                    float(previous["medical"]),
                    float(previous["travel"]),
                    float(previous["food"]),
                    float(previous["shopping"]),
                    float(previous["education"]),
                    float(previous["mobile"]),
                    float(previous["entertainment"]),
                    float(previous["others"])

                ])

                if total > previous_total:

                    comparison_text = t(
                        "increased"
                    )

                elif total < previous_total:

                    comparison_text = t(
                        "decreased"
                    )

                else:

                    comparison_text = t(
                        "same"
                    )

            # -------------------------------------------------
            # SUGGESTION
            # -------------------------------------------------

            if saving_percentage >= 30:

                suggestion = t(
                    "good_saving"
                )

            else:

                suggestion = t(
                    "low_saving"
                )

            records_html += f"""

            <div class="card">

                <h2>
                    📅 {row["month"]}
                </h2>

                <div class="expense-table-wrapper">

                    <table class="expense-table">

                        <tr>

                            <th>Home</th>
                            <th>Electricity</th>
                            <th>Hospital</th>
                            <th>Travel</th>
                            <th>Food</th>
                            <th>Shopping</th>
                            <th>Education</th>
                            <th>Mobile</th>
                            <th>Entertainment</th>
                            <th>Others</th>

                        </tr>

                        <tr>

                            <td>₹{categories["Home"]:,.0f}</td>
                            <td>₹{categories["Electricity"]:,.0f}</td>
                            <td>₹{categories["Hospital"]:,.0f}</td>
                            <td>₹{categories["Travel"]:,.0f}</td>
                            <td>₹{categories["Food"]:,.0f}</td>
                            <td>₹{categories["Shopping"]:,.0f}</td>
                            <td>₹{categories["Education"]:,.0f}</td>
                            <td>₹{categories["Mobile"]:,.0f}</td>
                            <td>₹{categories["Entertainment"]:,.0f}</td>
                            <td>₹{categories["Others"]:,.0f}</td>

                        </tr>

                    </table>

                </div>

                <div class="summary">

                    <div class="summary-box">

                        <b>
                            {t("monthly_income")}
                        </b>

                        <br>

                        ₹{income_value:,.2f}

                    </div>

                    <div class="summary-box">

                        <b>
                            {t("total_expenditure")}
                        </b>

                        <br>

                        ₹{total:,.2f}

                    </div>

                    <div class="summary-box">

                        <b>
                            {t("saved_money")}
                        </b>

                        <br>

                        ₹{saved:,.2f}

                    </div>

                </div>

                <div class="analysis">

                    <h3>
                        💡 {t("expense_analysis")}
                    </h3>

                    <p>
                        🔴 <b>
                        {t("highest_expense")}:
                        </b>

                        {highest_name}
                        —
                        ₹{highest_value:,.2f}
                    </p>

                    <p>
                        📊 <b>
                        {t("expense_percentage")}:
                        </b>

                        {expense_percentage:.1f}%
                    </p>

                    <p>
                        💰 <b>
                        {t("saving_percentage")}:
                        </b>

                        {saving_percentage:.1f}%
                    </p>

                    <p>
                        💡 <b>
                        {t("suggestion")}:
                        </b>

                        {suggestion}
                    </p>

                    {
                        f'''
                        <p>
                            📈 <b>
                            {t("comparison")}:
                            </b>

                            {comparison_text}
                        </p>
                        '''
                        if comparison_text
                        else ""
                    }

                </div>

            </div>

            """

    else:

        records_html = f"""

        <div class="card">

            <p style="text-align:center">

                {t("no_records")}

            </p>

        </div>

        """

    # =====================================================
    # FORM
    # =====================================================

    body = f"""

    <div class="card">

        <h1>
            🧾 {t("expenditure")}
        </h1>

        {message}

        <form method="POST">

            <label>{t("month")}</label>

            <select name="month">

                <option>January</option>
                <option>February</option>
                <option>March</option>
                <option>April</option>
                <option>May</option>
                <option>June</option>
                <option>July</option>
                <option>August</option>
                <option>September</option>
                <option>October</option>
                <option>November</option>
                <option>December</option>

            </select>

            <label>
                {t("monthly_income")}
            </label>

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
                placeholder="Enter amount"
            >

            <label>{t("electricity")}</label>

            <input
                type="number"
                name="electricity"
                min="0"
                step="0.01"
                placeholder="Enter amount"
            >

            <label>{t("medical")}</label>

            <input
                type="number"
                name="medical"
                min="0"
                step="0.01"
                placeholder="Enter amount"
            >

            <label>{t("travel")}</label>

            <input
                type="number"
                name="travel"
                min="0"
                step="0.01"
                placeholder="Enter amount"
            >

            <label>{t("food")}</label>

            <input
                type="number"
                name="food"
                min="0"
                step="0.01"
                placeholder="Enter amount"
            >

            <label>{t("shopping")}</label>

            <input
                type="number"
                name="shopping"
                min="0"
                step="0.01"
                placeholder="Enter amount"
            >

            <label>{t("education")}</label>

            <input
                type="number"
                name="education"
                min="0"
                step="0.01"
                placeholder="Enter amount"
            >

            <label>{t("mobile")}</label>

            <input
                type="number"
                name="mobile"
                min="0"
                step="0.01"
                placeholder="Enter amount"
            >

            <label>{t("entertainment")}</label>

            <input
                type="number"
                name="entertainment"
                min="0"
                step="0.01"
                placeholder="Enter amount"
            >

            <label>{t("others")}</label>

            <input
                type="number"
                name="others"
                min="0"
                step="0.01"
                placeholder="Enter amount"
            >

            <button class="btn-green">
                {t("save_month")}
            </button>

        </form>

    </div>

    <h2>
        {t("saved_months")}
    </h2>

    {records_html}

    <div class="card">

        <a class="btn btn-gray"
           href="{url_for('dashboard')}">

            ← {t("dashboard")}

        </a>

    </div>

    """

    return page(
        t("expenditure"),
        body
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# START
# =========================================================

init_db()


if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
