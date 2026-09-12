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
        body {
            font-family: Arial;
            background: #f2f2f2;
            text-align: center;
            padding: 30px;
        }

        .box {
            max-width: 400px;
            margin: auto;
            background: white;
            padding: 25px;
            border-radius: 12px;
        }

        input {
            width: 90%;
            padding: 12px;
            margin: 10px;
            font-size: 16px;
            box-sizing: border-box;
        }

        button {
            width: 90%;
            padding: 12px;
            margin: 10px;
            font-size: 16px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 6px;
        }

        .result {
            margin-top: 20px;
            font-size: 18px;
        }
    </style>
</head>

<body>

<div class="box">

    <h1>Income Tax Calculator</h1>

    <form method="POST">

        <input type="number"
               name="income"
               placeholder="Enter annual income"
               min="0"
               required>

        <button type="submit">
            Calculate Tax
        </button>

    </form>

    {% if tax is not none %}

    <div class="result">
        <p>Annual Income: ₹{{ income }}</p>
        <p><b>Income Tax: ₹{{ tax }}</b></p>
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

    # Section 87A rebate
    if income <= 1200000:
        tax = 0

    # 4% Health and Education Cess
    tax = tax * 1.04

    return round(tax, 2)


@app.route("/", methods=["GET", "POST"])
def home():

    tax = None
    income = None

    if request.method == "POST":

        income = float(request.form["income"])

        tax = calculate_tax(income)

    return render_template_string(
        HTML,
        tax=tax,
        income=income
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )
