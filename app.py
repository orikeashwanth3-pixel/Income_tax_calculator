from flask import Flask, request, redirect
import sqlite3

app = Flask(__name__)
DATABASE = "tax.db"

# ---------------- DATABASE ----------------

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


# ---------------- TAX CALCULATION ----------------

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

    # Section 87A rebate removed.
    # Apply 4% Health and Education Cess.
    tax = tax * 1.04

    return round(tax, 2)


# ---------------- LANGUAGE TEXT ----------------

TEXT = {
    "English": {
        "title": "Income Tax Calculator",
        "name": "Enter Your Name",
        "income": "Enter Annual Income (₹)",
        "calculate": "Calculate Tax",
        "records": "Saved Records",
        "person": "Name",
        "annual": "Annual Income",
        "tax": "Tax Payable",
        "delete": "Delete",
        "clear": "Clear All Records",
        "slabs": "Income Tax Slabs",
        "result": "Your calculated tax is",
        "cess": "Includes 4% Health & Education Cess. Section 87A rebate is not applied.",
        "required": "Please enter a valid name and income.",
        "empty": "No saved records yet."
    },
    "Telugu": {
        "title": "ఆదాయపు పన్ను కాలిక్యులేటర్",
        "name": "మీ పేరు నమోదు చేయండి",
        "income": "వార్షిక ఆదాయం నమోదు చేయండి (₹)",
        "calculate": "పన్ను లెక్కించండి",
        "records": "సేవ్ చేసిన వివరాలు",
        "person": "పేరు",
        "annual": "వార్షిక ఆదాయం",
        "tax": "చెల్లించాల్సిన పన్ను",
        "delete": "తొలగించు",
        "clear": "అన్ని వివరాలను తొలగించు",
        "slabs": "ఆదాయపు పన్ను స్లాబులు",
        "result": "మీరు చెల్లించాల్సిన పన్ను",
        "cess": "4% హెల్త్ అండ్ ఎడ్యుకేషన్ సెస్ కలిపి ఉంటుంది. సెక్షన్ 87A రిబేట్ వర్తించదు.",
        "required": "దయచేసి సరైన పేరు మరియు ఆదాయం నమోదు చేయండి.",
        "empty": "ఇంకా వివరాలు సేవ్ చేయలేదు."
    },
    "Hindi": {
        "title": "आयकर कैलकुलेटर",
        "name": "अपना नाम दर्ज करें",
        "income": "वार्षिक आय दर्ज करें (₹)",
        "calculate": "टैक्स की गणना करें",
        "records": "सेव किए गए रिकॉर्ड",
        "person": "नाम",
        "annual": "वार्षिक आय",
        "tax": "देय टैक्स",
        "delete": "हटाएँ",
        "clear": "सभी रिकॉर्ड हटाएँ",
        "slabs": "आयकर स्लैब",
        "result": "आपका गणना किया गया टैक्स",
        "cess": "इसमें 4% हेल्थ और एजुकेशन सेस शामिल है। सेक्शन 87A रिबेट लागू नहीं है।",
        "required": "कृपया सही नाम और आय दर्ज करें।",
        "empty": "अभी कोई रिकॉर्ड सेव नहीं है।"
    }
}


# ---------------- DATABASE RECORDS ----------------

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


# ---------------- WEB PAGE ----------------

def create_page(result="", message=""):
    lang = request.args.get(
        "lang",
        request.form.get("lang", "English")
    )

    if lang not in TEXT:
        lang = "English"

    t = TEXT[lang]
    records = get_records()

    result_html = ""
    if result != "":
        result_html = f"""
        <div class="result">
            <h3>{t['result']}</h3>
            <h2>₹{result:,.2f}</h2>
            <p>{t['cess']}</p>
        </div>
        """

    message_html = ""
    if message:
        message_html = f'<p class="message">{message}</p>'

    rows = ""
    for record in records:
        rows += f"""
        <tr>
            <td>{record[1]}</td>
            <td>₹{record[2]:,.2f}</td>
            <td>₹{record[3]:,.2f}</td>
            <td>
                <form method="POST" action="/delete/{record[0]}">
                    <input type="hidden" name="lang" value="{lang}">
                    <button class="delete" type="submit">
                        {t['delete']}
                    </button>
                </form>
            </td>
        </tr>
        """

    if not rows:
        rows = f'<tr><td colspan="4">{t["empty"]}</td></tr>'

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport"
              content="width=device-width, initial-scale=1.0">

        <title>{t['title']}</title>

        <style>
            * {{
                box-sizing: border-box;
            }}

            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background: #f2f5fa;
                color: #222;
            }}

            header {{
                background: #0755a5;
                color: white;
                text-align: center;
                padding: 25px 12px;
            }}

            .language {{
                display: block;
                margin: 12px auto;
                padding: 10px;
                border-radius: 6px;
                border: none;
                font-size: 15px;
            }}

            .container {{
                max-width: 900px;
                width: 94%;
                margin: 22px auto;
            }}

            .card {{
                background: white;
                padding: 22px;
                margin-bottom: 20px;
                border-radius: 12px;
                box-shadow: 0 3px 12px #00000012;
            }}

            input, select {{
                width: 100%;
                padding: 12px;
                margin: 8px 0 16px;
                border: 1px solid #ccc;
                border-radius: 6px;
                font-size: 16px;
            }}

            button {{
                background: #0755a5;
                color: white;
                border: none;
                padding: 12px 18px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 15px;
            }}

            button:hover {{
                opacity: 0.9;
            }}

            .result {{
                background: #e8f4ff;
                padding: 18px;
                margin-top: 18px;
                border-radius: 8px;
                overflow-wrap: anywhere;
            }}

            .result h2 {{
                color: #0755a5;
            }}

            .message {{
                color: #b00020;
            }}

            .table-wrap {{
                overflow-x: auto;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                min-width: 560px;
            }}

            th, td {{
                padding: 11px;
                border-bottom: 1px solid #ddd;
                text-align: left;
            }}

            th {{
                background: #0755a5;
                color: white;
            }}

            .delete {{
                background: #c62828;
                padding: 8px 12px;
            }}

            .clear {{
                background: #c62828;
                margin-top: 12px;
            }}

            @media(max-width: 500px) {{
                .card {{
                    padding: 15px;
                }}

                header h1 {{
                    font-size: 23px;
                }}
            }}
        </style>
    </head>

    <body>
        <header>
            <h1>{t['title']}</h1>

            <form method="GET">
                <select class="language"
                        name="lang"
                        onchange="this.form.submit()"
                        aria-label="Choose language">
                    <option value="English"
                        {"selected" if lang == "English" else ""}>
                        English
                    </option>

                    <option value="Telugu"
                        {"selected" if lang == "Telugu" else ""}>
                        తెలుగు
                    </option>

                    <option value="Hindi"
                        {"selected" if lang == "Hindi" else ""}>
                        हिन्दी
                    </option>
                </select>
            </form>
        </header>

        <main class="container">

            <section class="card">
                <h2>{t['calculate']}</h2>

                {message_html}

                <form method="POST" action="/">
                    <input type="hidden" name="lang" value="{lang}">

                    <label>{t['name']}</label>
                    <input type="text" name="name"
                           maxlength="100" required>

                    <label>{t['income']}</label>
                    <input type="number" name="income"
                           min="0" step="0.01" required>

                    <button type="submit">{t['calculate']}</button>
                </form>

                {result_html}
            </section>

            <section class="card">
                <h2>{t['slabs']}</h2>

                <div class="table-wrap">
                    <table>
                        <tr>
                            <th>Annual Income</th>
                            <th>Tax Rate</th>
                        </tr>
                        <tr><td>₹0 – ₹4,00,000</td><td>0%</td></tr>
                        <tr><td>₹4,00,001 – ₹8,00,000</td><td>5%</td></tr>
                        <tr><td>₹8,00,001 – ₹12,00,000</td><td>10%</td></tr>
                        <tr><td>₹12,00,001 – ₹16,00,000</td><td>15%</td></tr>
                        <tr><td>₹16,00,001 – ₹20,00,000</td><td>20%</td></tr>
                        <tr><td>₹20,00,001 – ₹24,00,000</td><td>25%</td></tr>
                        <tr><td>Above ₹24,00,000</td><td>30%</td></tr>
                    </table>
                </div>

                <p>{t['cess']}</p>
            </section>

            <section class="card">
                <h2>{t['records']}</h2>

                <div class="table-wrap">
                    <table>
                        <tr>
                            <th>{t['person']}</th>
                            <th>{t['annual']}</th>
                            <th>{t['tax']}</th>
                            <th>{t['delete']}</th>
                        </tr>
                        {rows}
                    </table>
                </div>

                <form method="POST" action="/clear"
                      onsubmit="return confirm('Clear all saved records?')">
                    <input type="hidden" name="lang" value="{lang}">
                    <button class="clear" type="submit">
                        {t['clear']}
                    </button>
                </form>
            </section>
        </main>
    </body>
    </html>
    """


# ---------------- ROUTES ----------------

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        income_text = request.form.get("income", "").strip()
        lang = request.form.get("lang", "English")

        if lang not in TEXT:
            lang = "English"

        if not name or not income_text:
            return create_page(message=TEXT[lang]["required"])

        try:
            income = float(income_text)
            if income < 0:
                raise ValueError
        except ValueError:
            return create_page(message=TEXT[lang]["required"])

        tax = calculate_tax(income)

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tax_records (name, income, tax) VALUES (?, ?, ?)",
            (name, income, tax)
        )
        conn.commit()
        conn.close()

        return create_page(result=tax)

    return create_page()


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


# ---------------- START APP ----------------

create_database()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)