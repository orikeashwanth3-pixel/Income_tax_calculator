from flask import Flask, request, redirect
import sqlite3
import os
from html import escape

app = Flask(__name__)

DATABASE = "tax.db"

# Supported languages
TEXT = {
    "English": {
        "title": "Income Tax Calculator",
        "subtitle": "Python Flask Web Application",
        "calculator": "Calculate Income Tax",
        "name": "Name",
        "name_placeholder": "Enter your name",
        "income": "Annual Total Income (₹)",
        "income_placeholder": "Enter annual income",
        "calculate": "Calculate & Save",
        "result_title": "Tax Calculation Result",
        "annual_income": "Annual Income",
        "tax": "Income Tax",
        "saved": "Record saved successfully.",
        "slabs": "Tax Slabs",
        "regime": "New Tax Regime - AY 2026-27",
        "cess": "Health & Education Cess: 4%",
        "no_rebate": "Section 87A rebate is not applied in this calculator.",
        "records": "Saved Records",
        "id": "ID",
        "action": "Action",
        "delete": "Delete",
        "no_records": "No records found",
        "clear": "Clear All Records",
        "footer": "Final Year CSE Project",
        "name_error": "Please enter your name.",
        "income_error": "Income cannot be negative.",
        "valid_error": "Please enter a valid income.",
        "slab_rows": [
            ("Up to ₹4,00,000", "Nil"),
            ("₹4,00,001–₹8,00,000", "5%"),
            ("₹8,00,001–₹12,00,000", "10%"),
            ("₹12,00,001–₹16,00,000", "15%"),
            ("₹16,00,001–₹20,00,000", "20%"),
            ("₹20,00,001–₹24,00,000", "25%"),
            ("Above ₹24,00,000", "30%"),
        ],
    },
    "Telugu": {
        "title": "ఆదాయపు పన్ను కాలిక్యులేటర్",
        "subtitle": "పైథాన్ ఫ్లాస్క్ వెబ్ అప్లికేషన్",
        "calculator": "ఆదాయపు పన్ను లెక్కించండి",
        "name": "పేరు",
        "name_placeholder": "మీ పేరు నమోదు చేయండి",
        "income": "మొత్తం వార్షిక ఆదాయం (₹)",
        "income_placeholder": "వార్షిక ఆదాయం నమోదు చేయండి",
        "calculate": "లెక్కించి సేవ్ చేయండి",
        "result_title": "పన్ను లెక్కింపు ఫలితం",
        "annual_income": "వార్షిక ఆదాయం",
        "tax": "ఆదాయపు పన్ను",
        "saved": "వివరాలు విజయవంతంగా సేవ్ అయ్యాయి.",
        "slabs": "పన్ను స్లాబులు",
        "regime": "కొత్త పన్ను విధానం - AY 2026-27",
        "cess": "హెల్త్ & ఎడ్యుకేషన్ సెస్: 4%",
        "no_rebate": "ఈ కాలిక్యులేటర్‌లో సెక్షన్ 87A రిబేట్ వర్తించదు.",
        "records": "సేవ్ చేసిన వివరాలు",
        "id": "ఐడి",
        "action": "చర్య",
        "delete": "తొలగించు",
        "no_records": "వివరాలు ఏవీ లేవు",
        "clear": "అన్ని వివరాలను తొలగించండి",
        "footer": "చివరి సంవత్సరం CSE ప్రాజెక్ట్",
        "name_error": "దయచేసి మీ పేరు నమోదు చేయండి.",
        "income_error": "ఆదాయం నెగటివ్‌గా ఉండకూడదు.",
        "valid_error": "దయచేసి సరైన ఆదాయం నమోదు చేయండి.",
        "slab_rows": [
            ("₹4,00,000 వరకు", "లేదు"),
            ("₹4,00,001–₹8,00,000", "5%"),
            ("₹8,00,001–₹12,00,000", "10%"),
            ("₹12,00,001–₹16,00,000", "15%"),
            ("₹16,00,001–₹20,00,000", "20%"),
            ("₹20,00,001–₹24,00,000", "25%"),
            ("₹24,00,000 కంటే ఎక్కువ", "30%"),
        ],
    },
    "Hindi": {
        "title": "आयकर कैलकुलेटर",
        "subtitle": "पायथन फ्लास्क वेब एप्लिकेशन",
        "calculator": "आयकर की गणना करें",
        "name": "नाम",
        "name_placeholder": "अपना नाम दर्ज करें",
        "income": "कुल वार्षिक आय (₹)",
        "income_placeholder": "वार्षिक आय दर्ज करें",
        "calculate": "गणना करें और सेव करें",
        "result_title": "टैक्स गणना परिणाम",
        "annual_income": "वार्षिक आय",
        "tax": "आयकर",
        "saved": "रिकॉर्ड सफलतापूर्वक सेव हुआ।",
        "slabs": "टैक्स स्लैब",
        "regime": "नई टैक्स व्यवस्था - AY 2026-27",
        "cess": "हेल्थ और एजुकेशन सेस: 4%",
        "no_rebate": "इस कैलकुलेटर में सेक्शन 87A रिबेट लागू नहीं है।",
        "records": "सेव किए गए रिकॉर्ड",
        "id": "आईडी",
        "action": "कार्रवाई",
        "delete": "हटाएँ",
        "no_records": "कोई रिकॉर्ड नहीं मिला",
        "clear": "सभी रिकॉर्ड हटाएँ",
        "footer": "अंतिम वर्ष CSE प्रोजेक्ट",
        "name_error": "कृपया अपना नाम दर्ज करें।",
        "income_error": "आय ऋणात्मक नहीं हो सकती।",
        "valid_error": "कृपया सही आय दर्ज करें।",
        "slab_rows": [
            ("₹4,00,000 तक", "शून्य"),
            ("₹4,00,001–₹8,00,000", "5%"),
            ("₹8,00,001–₹12,00,000", "10%"),
            ("₹12,00,001–₹16,00,000", "15%"),
            ("₹16,00,001–₹20,00,000", "20%"),
            ("₹20,00,001–₹24,00,000", "25%"),
            ("₹24,00,000 से अधिक", "30%"),
        ],
    },
}


def get_language():
    lang = request.values.get("lang", "English")
    return lang if lang in TEXT else "English"


# =====================================================
# DATABASE
# =====================================================

def create_database():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tax_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            income REAL NOT NULL,
            tax REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# =====================================================
# TAX CALCULATION - SLABS AS SHOWN ON THE WEBSITE
# Section 87A rebate is removed.
# =====================================================

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

    # No Section 87A rebate.
    # Add 4% Health & Education Cess.
    return round(tax * 1.04, 2)


# =====================================================
# GET RECORDS
# =====================================================

def get_records():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, income, tax
        FROM tax_records
        ORDER BY id DESC
    """)
    records = cursor.fetchall()
    conn.close()
    return records


# =====================================================
# HTML PAGE
# =====================================================

def create_page(result="", message=""):
    lang = get_language()
    t = TEXT[lang]
    records = get_records()

    rows = ""
    for record in records:
        safe_name = escape(str(record[1]))
        rows += f"""
        <tr>
            <td>{record[0]}</td>
            <td>{safe_name}</td>
            <td>₹{record[2]:,.2f}</td>
            <td>₹{record[3]:,.2f}</td>
            <td>
                <form method="POST" action="/delete/{record[0]}">
                    <input type="hidden" name="lang" value="{lang}">
                    <button class="delete-button" type="submit">{t['delete']}</button>
                </form>
            </td>
        </tr>
        """

    if not rows:
        rows = f"""
        <tr><td colspan="5">{t['no_records']}</td></tr>
        """

    slab_rows = ""
    for income_range, rate in t["slab_rows"]:
        slab_rows += f"<tr><td>{income_range}</td><td>{rate}</td></tr>"

    result_html = ""
    if result:
        result_html = result

    message_html = (
        f'<div class="message">{escape(message)}</div>' if message else ""
    )

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{t['title']}</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0; padding: 0; font-family: Arial, sans-serif;
            background: #f2f2f2;
        }}
        .header {{
            background: #1565c0; color: white; text-align: center;
            padding: 22px 10px; position: relative;
        }}
        .header h1 {{ margin: 0; font-size: 26px; }}
        .header p {{ margin: 8px 0 0; }}
        .language-form {{
            position: absolute; top: 12px; right: 12px;
        }}
        .language-form select {{
            width: auto; max-width: 125px; padding: 8px;
            border: none; border-radius: 5px; font-size: 14px;
        }}
        .container {{ width: 95%; max-width: 800px; margin: 25px auto; }}
        .card {{
            background: white; padding: 22px; margin-bottom: 20px;
            border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h2 {{ margin-top: 0; color: #1565c0; }}
        label {{ display: block; margin-top: 15px; font-weight: bold; }}
        input {{
            width: 100%; padding: 12px; margin-top: 6px;
            border: 1px solid #ccc; border-radius: 5px; font-size: 16px;
        }}
        button {{
            width: 100%; padding: 12px; margin-top: 18px;
            border: none; border-radius: 5px; background: #1565c0;
            color: white; font-size: 16px; cursor: pointer;
        }}
        button:hover {{ background: #0d47a1; }}
        .result {{
            margin-top: 20px; padding: 18px; background: #e8f5e9;
            border-radius: 7px; border-left: 5px solid #2e7d32;
            overflow-wrap: anywhere;
        }}
        .result h3 {{ color: #2e7d32; }}
        .message {{
            padding: 12px; margin-bottom: 15px; background: #e3f2fd;
            border-radius: 5px; text-align: center;
        }}
        .table-container {{ overflow-x: auto; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{
            padding: 10px; border-bottom: 1px solid #ddd;
            text-align: center; white-space: nowrap;
        }}
        th {{ background: #1565c0; color: white; }}
        .delete-button {{
            width: auto; margin: 0; padding: 7px 12px; background: #d32f2f;
        }}
        .delete-button:hover {{ background: #b71c1c; }}
        .clear-button {{ background: #555; }}
        .info {{
            background: #fff3cd; padding: 15px; border-radius: 7px;
            font-size: 14px; line-height: 1.7;
        }}
        .footer {{ text-align: center; color: #777; padding: 20px; }}
        @media(max-width: 600px) {{
            .header {{ padding-top: 55px; }}
            .header h1 {{ font-size: 22px; }}
            .card {{ padding: 16px; }}
            th, td {{ font-size: 13px; }}
            .language-form {{ top: 8px; right: 8px; }}
        }}
    </style>
</head>
<body>
<div class="header">
    <form class="language-form" method="GET">
        <select name="lang" onchange="this.form.submit()" aria-label="Choose language">
            <option value="English" {"selected" if lang == "English" else ""}>English</option>
            <option value="Telugu" {"selected" if lang == "Telugu" else ""}>తెలుగు</option>
            <option value="Hindi" {"selected" if lang == "Hindi" else ""}>हिन्दी</option>
        </select>
    </form>
    <h1>{t['title']}</h1>
    <p>{t['subtitle']}</p>
</div>

<div class="container">
    {message_html}

    <div class="card">
        <h2>{t['calculator']}</h2>
        <form method="POST" action="/">
            <input type="hidden" name="lang" value="{lang}">
            <label>{t['name']}</label>
            <input type="text" name="name" maxlength="100"
                   placeholder="{t['name_placeholder']}" required>
            <label>{t['income']}</label>
            <input type="number" name="income" placeholder="{t['income_placeholder']}"
                   min="0" step="0.01" required>
            <button type="submit">{t['calculate']}</button>
        </form>
        {result_html}
    </div>

    <div class="card">
        <h2>{t['slabs']}</h2>
        <div class="info">
            <b>{t['regime']}</b>
            <div class="table-container">
                <table>
                    <tr><th>Annual Income</th><th>Tax Rate</th></tr>
                    {slab_rows}
                </table>
            </div>
            <p>{t['no_rebate']}</p>
            <p>{t['cess']}</p>
        </div>
    </div>

    <div class="card">
        <h2>{t['records']}</h2>
        <div class="table-container">
            <table>
                <tr>
                    <th>{t['id']}</th><th>{t['name']}</th>
                    <th>{t['annual_income']}</th><th>{t['tax']}</th>
                    <th>{t['action']}</th>
                </tr>
                {rows}
            </table>
        </div>
        <form method="POST" action="/clear"
              onsubmit="return confirm('Clear all saved records?')">
            <input type="hidden" name="lang" value="{lang}">
            <button class="clear-button" type="submit">{t['clear']}</button>
        </form>
    </div>
</div>

<div class="footer">
    {t['title']}<br>{t['footer']}
</div>
</body>
</html>
"""


# =====================================================
# HOME
# =====================================================

@app.route("/", methods=["GET", "POST"])
def home():
    lang = get_language()
    t = TEXT[lang]
    result = ""
    message = ""

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        income_text = request.form.get("income", "").strip()

        if not name:
            message = t["name_error"]
        else:
            try:
                income = float(income_text)
                if income < 0:
                    message = t["income_error"]
                else:
                    tax = calculate_tax(income)

                    conn = sqlite3.connect(DATABASE)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO tax_records (name, income, tax)
                        VALUES (?, ?, ?)
                    """, (name, income, tax))
                    conn.commit()
                    conn.close()

                    result = f"""
                    <div class="result">
                        <h3>{t['result_title']}</h3>
                        <p><b>{t['name']}:</b> {escape(name)}</p>
                        <p><b>{t['annual_income']}:</b> ₹{income:,.2f}</p>
                        <p><b>{t['tax']}:</b> ₹{tax:,.2f}</p>
                        <p>{t['saved']}</p>
                    </div>
                    """
            except (ValueError, TypeError):
                message = t["valid_error"]

    return create_page(result, message)


# =====================================================
# DELETE ONE RECORD
# =====================================================

@app.route("/delete/<int:record_id>", methods=["POST"])
def delete_record(record_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tax_records WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()

    lang = request.form.get("lang", "English")
    if lang not in TEXT:
        lang = "English"
    return redirect("/?lang=" + lang)


# =====================================================
# CLEAR ALL RECORDS
# =====================================================

@app.route("/clear", methods=["POST"])
def clear_records():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tax_records")
    conn.commit()
    conn.close()

    lang = request.form.get("lang", "English")
    if lang not in TEXT:
        lang = "English"
    return redirect("/?lang=" + lang)


# =====================================================
# START SERVER
# =====================================================

create_database()

if __name__ == "__main__":
    # Render provides PORT automatically; local use defaults to 5000.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
