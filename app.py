from flask import Flask, request, render_template_string

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Indian Income Tax Calculator</title>

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <style>
        body {
            font-family: Arial;
            background: #f2f2f2;
            margin: 0;
            padding: 20px;
        }

        .box {
            max-width: 500px;
            margin: auto;
            background: white;
            padding: 25px;
            border-radius: 15px;
        }

        h1, h2 {
            text-align: center;
        }

        input {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            font-size: 16px;
            box-sizing: border-box;
        }

        button {
            width: 100%;
            padding: 13px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 17px;
        }

        .result {
            background: #e8f5e9;
            padding: 15px;
            margin-top: 20px;
            border-radius: 8px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }

        th, td {
            border: 1px solid #ccc;
            padding: 9px;
            text-align: center;
        }

        th {
            background: #007bff;
            color: white;
        }

        .rule {
            background: #fff3cd;
            padding: 15px;
            margin-top: 20px;
            border-radius: 8px;
        }

        .note {
            font-size: 13px;
            color: #555;
            margin-top: 15px;
        }
    </style>
</head>

<body>

<div class="box">

    <h1>🇮🇳 Income Tax Calculator</h1>

    <form method="POST">

        <input
            type="number"
            name="income"
            placeholder="Enter taxable annual income"
            min="0"
            required
        >

        <button type="submit">
            Calculate Tax
        </button>

    </form>

    {% if tax is not none %}

    <div class="result">
        <h2>Tax Result</h2>

        <p>
            <b>Annual Income:</b>
            ₹{{ "{:,.2f}".format(income) }}
        </p>

        <p>
            <b>Income Tax:</b>
            ₹{{ "{:,.2f}".format(tax) }}
        </p>

        {% if rebate %}
        <p>
            <b>Section 87A Rebate:</b>
            Applied
        </p>
        {% endif %}
    </div>

    {% endif %}


    <h2>New Tax Regime Slabs</h2>

    <table>
        <tr>
            <th>Income Range</th>
            <th>Tax Rate</th>
        </tr>

        <tr>
            <td>Up to ₹4,00,000</td>
            <td>Nil</td>
        </tr>

        <tr>
            <td>₹4,00,001 – ₹8,00,000</td>
            <td>5%</td>
        </tr>

        <tr>
            <td>₹8,00,001 – ₹12,00,000</td>
            <td>10%</td>
        </tr>

        <tr>
            <td>₹12,00,001 – ₹16,00,000</td>
            <td>15%</td>
        </tr>

        <tr>
            <td>₹16,00,001 – ₹20,00,000</td>
            <td>20%</td>
        </tr>

        <tr>
            <td>₹20,00,001 – ₹24,00,000</td>
            <td>25%</td>
        </tr>

        <tr>
            <td>Above ₹24,00,000</td>
            <td>30%</td>
        </tr>
    </table>


    <div class="rule">

        <h2>Section 87A Rebate</h2>

        <p>
            Under the new tax regime, an eligible
            <b>resident individual</b> can get a rebate
            of up to <b>₹60,000</b>.
        </p>

        <p>
            The rebate is available when taxable income
            does not exceed <b>₹12,00,000</b>.
        </p>

        <p>
            Therefore, eligible income up to ₹12 lakh
            can have <b>zero income tax</b> after the
            applicable rebate.
        </p>

    </div>


    <p class="note">
        This calculator is for educational purposes.
        It calculates tax on the taxable income entered
        by the user and does not cover every special-rate
        income, deduction or surcharge situation.
    </p>

</div>

</body>
</html>
"""


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

    rebate = False

    # Section 87A rebate
    if income <= 1200000:
        rebate = True
        tax = 0

    # 4% Health and Education Cess
    tax = tax * 1.04

    return round(tax, 2), rebate


@app.route("/", methods=["GET", "POST"])
def home():

    tax = None
    income = None
    rebate = False

    if request.method == "POST":

        income = float(request.form["income"])

        tax, rebate = calculate_tax(income)

    return render_template_string(
        HTML,
        tax=tax,
        income=income,
        rebate=rebate
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )
