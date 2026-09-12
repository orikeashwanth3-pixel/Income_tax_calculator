from flask import Flask, request

app = Flask(__name__)


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

    # Rebate for eligible income up to ₹12 lakh
    if income <= 1200000:
        tax = 0

    # 4% Health and Education Cess
    tax += tax * 0.04

    return tax


@app.route("/", methods=["GET", "POST"])
def home():

    result = ""

    if request.method == "POST":
        name = request.form["name"]
        income = float(request.form["income"])

        tax = calculate_tax(income)

        result = f"""
        <div class="result">
            <h2>Tax Calculation Result</h2>
            <p><b>Name:</b> {name}</p>
            <p><b>Annual Income:</b> ₹{income:,.2f}</p>
            <p><b>Income Tax:</b> ₹{tax:,.2f}</p>
        </div>
        """

    return f"""
<!DOCTYPE html>
<html>
<head>

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Income Tax Calculator</title>

<style>

body {{
    font-family: Arial;
    
