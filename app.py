from flask import Flask, request, render_template_string

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>

    <title>Income Tax Calculator</title>

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <style>

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            padding: 20px;
            font-family: Arial, sans-serif;
            background: #f2f5f9;
            color: #102a43;
        }

        .container {
            max-width: 550px;
            margin: auto;
            background: white;
            padding: 25px;
            border-radius: 18px;
        }

        .header {
            text-align: center;
            margin-bottom: 25px;
        }

        .money {
            font-size: 60px;
        }

        h1 {
            font-size: 36px;
            margin: 5px 0 20px;
        }

        label {
            display: block;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 8px;
        }

        input {
            width: 100%;
            padding: 15px;
            border: 2px solid #b7c9dd;
            border-radius: 8px;
            font-size: 18px;
            outline: none;
        }

        input:focus {
            border-color: #1677ff;
        }

        button {
            width: 100%;
            padding: 15px;
            margin-top: 15px;
            border: none;
            border-radius: 8px;
            background: #1677ff;
            color: white;
            font-size: 19px;
            font-weight: bold;
            cursor: pointer;
        }

        button:hover {
            background: #0866e5;
        }

        .result {
            margin-top: 25px;
            padding: 20px;
            background: #eaf8ef;
            border: 1px solid #b9ebca;
            border-radius: 14px;
        }

        .result h2 {
            margin-top: 0;
            font-size: 24px;
        }

        .result p {
            font-size: 18px;
            margin: 12px 0;
        }

        .tax {
            color: #16803c;
            font-size: 22px !important;
            font-weight: bold;
        }

        .calculation {
            margin-top: 30px;
            padding: 20px;
            background: #eef6ff;
            border: 1px solid #d3e7ff;
            border-radius: 14px;
        }

        .calculation-title {
            font-size: 22px;
            font-weight: bold;
            margin-bottom: 20px;
            text-transform: uppercase;
        }

        .section-title {
            font-size: 20px;
            font-weight: bold;
            margin-top: 20px;
            margin-bottom: 12px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
        }

        th {
            background: #1677ff;
            color: white;
            padding: 12px;
            font-size: 16px;
        }

        td {
            border: 1px solid #d0d7de;
            padding: 12px 8px;
            text-align: center;
            font-size: 15px;
        }

        .rebate {
            margin-top: 20px;
            padding: 18px;
            background: #fff4cf;
            border-radius: 12px;
        }

        .rebate h2 {
            margin-top: 0;
            font-size: 21px;
        }

        .rebate p {
            font-size: 16px;
            line-height: 1.5;
        }

        @media (max-width: 500px) {

            body {
                padding: 10px;
            }

            .container {
                padding: 20px;
            }

            h1 {
                font-size: 32px;
            }

            .calculation-title {
                font-size: 19px;
            }

            td, th {
                font-size: 13px;
                padding: 10px 5px;
            }
        }

    </style>

</head>

<body>

<div class="container">

    <div class="header">

        <div class="money">💰</div>

        <h1>Income Tax Calculator</h1>

    </div>


    <form method="POST">

        <label>ANNUAL INCOME (₹)</label>

        <input
            type="number"
            name="income"
            placeholder="ENTER ANNUAL INCOME"
            min="0"
            step="1"
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
            Annual Income:
            <b>₹{{ "{:,.2f}".format(income) }}</b>
        </p>

        <p class="tax">
            Income Tax:
            ₹{{ "{:,.2f}".format(tax) }}
        </p>

        {% if rebate %}

        <p>
            Section 87A Rebate:
            <b>Applied</b>
        </p>

        {% endif %}

    </div>


    <div class="calculation">

        <div class="calculation-title">
            HOW WAS THE TAX CALCULATED BASED ON YOUR ANNUAL INCOME
        </div>


        <div class="section-title">
            New Tax Regime Slabs
        </div>

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


        <div class="rebate">

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

    </div>

    {% endif %}

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
        tax = 0
        rebate = True


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
