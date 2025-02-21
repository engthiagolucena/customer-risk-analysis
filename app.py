import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from fpdf import FPDF

def classify_risk(employment_length, employment_type, age, income, net_income, car_payment, bankruptcy_count, repossession_count, downpayment, trade_in):
    if net_income > 0:
        payment_ratio = car_payment / net_income
    else:
        payment_ratio = 1
    
    risk_score = 0
    risk_factors = []
    
    if employment_length < 6:
        risk_score += 2
        risk_factors.append("Short employment history")
    elif employment_length < 12:
        risk_score += 1
        risk_factors.append("Less than 1 year in current job")
    
    if employment_type == "Cash Paid" or employment_type == "1099":
        risk_score += 2
        risk_factors.append("Unstable income source (Cash Paid/1099)")
    elif employment_type == "Self-Employed":
        risk_score += 1
        risk_factors.append("Self-Employed - Moderate risk")
    elif employment_type == "W2":
        risk_factors.append("Stable employment (W2)")
    
    if payment_ratio > 0.4:
        risk_score += 3
        risk_factors.append("High payment-to-net-income ratio (>40%)")
    elif payment_ratio > 0.3:
        risk_score += 2
        risk_factors.append("Moderate-high payment-to-net-income ratio (30-40%)")
    elif payment_ratio > 0.25:
        risk_score += 1
        risk_factors.append("Moderate payment-to-net-income ratio (25-30%)")
    elif payment_ratio <= 0.25:
        risk_factors.append("Optimal payment-to-net-income ratio (≤25%) - Financially stable")
    
    if bankruptcy_count > 0 and repossession_count > 0:
        return 10, ["High risk due to bankruptcy and repossession history"]
    risk_score += bankruptcy_count * 2
    if bankruptcy_count > 0:
        risk_factors.append(f"{bankruptcy_count} past bankruptcy record(s)")
    risk_score += repossession_count * 3
    if repossession_count > 0:
        risk_factors.append(f"{repossession_count} past repossession(s)")
    
    if downpayment > 3000:
        risk_score -= 2
        risk_factors.append("High downpayment reducing risk")
    elif downpayment > 1500:
        risk_score -= 1
        risk_factors.append("Moderate downpayment reducing risk")
    
    if age <= 24:
        risk_score += 3
        risk_factors.append("High risk for younger customers (<=24 years old)")
    elif 25 <= age <= 30:
        risk_score += 2
        risk_factors.append("Moderate-high risk for customers aged 25-30")
    elif 31 <= age <= 40:
        risk_score += 1
        risk_factors.append("Moderate risk for customers aged 31-40")
    elif age > 40:
        risk_score -= 2
        risk_factors.append("Lower risk for older customers (>40 years old)")
    
    if trade_in > 0:
        risk_score -= 1
        risk_factors.append("Trade-in provided, reducing risk")
    
    return risk_score, risk_factors

st.title("Customer Risk Evaluation System")

def applicant_form(prefix):
    st.subheader(f"{prefix} Applicant Information")
    first_name = st.text_input(f"{prefix} First Name", "")
    last_name = st.text_input(f"{prefix} Last Name", "")
    employment_length = st.number_input(f"{prefix} Employment Length (months)", min_value=0, value=0)
    employment_type = st.selectbox(f"{prefix} Employment Type", ["W2", "Self-Employed", "Cash Paid", "1099"], index=0)
    age = st.number_input(f"{prefix} Age", min_value=18, value=18)
    pay_frequency = st.selectbox(f"{prefix} Pay Frequency", ["Weekly", "Bi-Weekly", "Monthly"], index=0)
    
    st.subheader(f"{prefix} Income Details")
    paycheck_count = st.number_input(f"{prefix} Number of Paychecks Provided", min_value=1, max_value=6, value=3)
    paychecks = [st.number_input(f"{prefix} Paycheck {i+1} ($)", min_value=0.0, value=0.0) for i in range(paycheck_count)]
    avg_paycheck = np.mean(paychecks) if paychecks else 0.0
    
    if pay_frequency == "Weekly":
        monthly_income = avg_paycheck * 4
    elif pay_frequency == "Bi-Weekly":
        monthly_income = avg_paycheck * 2
    else:
        monthly_income = avg_paycheck * 1
    
    has_other_income = st.checkbox(f"{prefix} Other Income?")
    other_income_total = 0.0
    if has_other_income:
        other_income_count = st.number_input(f"{prefix} Number of Other Income Sources", min_value=1, max_value=5, value=1)
        other_incomes = [st.number_input(f"{prefix} Other Income {i+1} ($)", min_value=0.0, value=0.0) for i in range(other_income_count)]
        other_income_total = sum(other_incomes)
    
    total_income = monthly_income + other_income_total
    car_payment = st.number_input(f"{prefix} Monthly Car Payment ($)", min_value=0.0, value=0.0)
    total_expenses = st.number_input(f"{prefix} Total Monthly Expenses ($)", min_value=0.0, value=0.0)
    downpayment = st.number_input(f"{prefix} Downpayment ($)", min_value=0.0, value=0.0)

    st.subheader(f"{prefix} Credit History")
    has_bankruptcy = st.checkbox(f"{prefix} Has Bankruptcy?")
    bankruptcy_count = st.number_input(f"{prefix} Number of Bankruptcies", min_value=0, value=0) if has_bankruptcy else 0

    has_repossession = st.checkbox(f"{prefix} Has Repossessions?")
    repossession_count = st.number_input(f"{prefix} Number of Repossessions", min_value=0, value=0) if has_repossession else 0

    return {
        "employment_length": employment_length,
        "employment_type": employment_type,
        "age": age,
        "monthly_income": total_income,
        "car_payment": car_payment,
        "total_expenses": total_expenses,
        "downpayment": downpayment,
        "bankruptcy_count": bankruptcy_count,
        "repossession_count": repossession_count
    }

applicant_data = applicant_form("Primary")

has_cobuyer = st.checkbox("Is there a Co-Buyer?")
cobuyer_data = applicant_form("Co-Buyer") if has_cobuyer else None

if st.button("Evaluate Risk"):
    total_income = applicant_data["monthly_income"] + (cobuyer_data["monthly_income"] if cobuyer_data else 0)
    total_expenses = applicant_data["total_expenses"] + (cobuyer_data["total_expenses"] if cobuyer_data else 0)
    car_payment = applicant_data["car_payment"] + (cobuyer_data["car_payment"] if cobuyer_data else 0)
    
    risk_score, risk_factors = classify_risk(
        applicant_data["employment_length"],
        applicant_data["employment_type"],
        applicant_data["age"],
        total_income,
        total_income - total_expenses,
        car_payment,
        applicant_data["bankruptcy_count"] + (cobuyer_data["bankruptcy_count"] if cobuyer_data else 0),
        applicant_data["repossession_count"] + (cobuyer_data["repossession_count"] if cobuyer_data else 0),
        applicant_data["downpayment"],
        0
    )
    
    st.subheader("Risk Evaluation")
    st.write(f"Risk Score: {risk_score}")

    if risk_score >= 8:
        st.write("🔴 **High Risk:** High probability of repossession with less than 25% payments.")
    elif risk_score >= 5:
        st.write("🟡 **Moderate Risk:** Repossession risk after more than 50% payments.")
    else:
        st.write("🟢 **Low Risk:** High chance of full payoff.")

    for factor in risk_factors:
        st.write(f"- {factor}")
