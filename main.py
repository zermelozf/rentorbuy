from collections import defaultdict

import streamlit as st
import numpy as np
import pandas as pd

import plotly.express as px

from models import Bank, Loan, RealEstate, Rent, Salary


n = st.sidebar.slider("Timeline (years)", value=35, max_value=50)

st.sidebar.markdown('# Economic conditions')
appreciation_rate = st.sidebar.number_input(
    'Housing Market return', 
    value=0.02, 
    format='%f',
    help='This return is used on the house and land.'
)
inflation_rate = st.sidebar.number_input(
    'Inflation rate', 
    value=0.02, 
    format='%f',
    help='Used to discount the future value of future payments. It will affect the real NPV of the project.'
)
invest_difference = st.sidebar.checkbox(
    "Invest difference in the stock market", 
    value=False, 
    help="Each year one project has a cost bigger than the other, the second project will invest the difference in the stock market."
)
market_rate = 0
if invest_difference:
    market_rate = st.sidebar.number_input(
        'Stock Market return', 
        value=0.05, 
        format='%f',
        help='This return is used for inveting any cash left after paying the rent and/or loan into the stock market.'
    )

tabs = st.tabs(["Summary", "Rent", "Buy"])


with tabs[1]:
    st.markdown('## Rent')
    monthtly_rent = st.number_input('Monthly rent (万円)', value=24)
    renewal_fee = st.number_input('Renewal fee (万円)', value=24)
    rent_increase_rate = st.number_input('Yearly rent increase', value=0.01)
    rent = Rent(
        monthly_rent=monthtly_rent,
        renewal_fee=renewal_fee,
        rent_increase_rate=rent_increase_rate
    )
    rent_bank = Bank(initial_deposit=0, interest_rate=market_rate)



with tabs[2]:
    col1, col2 = st.columns(2)
    st.subheader("Property details")
    house_price = st.number_input('House price (万円)', value=3500)
    land_price = st.number_input('Land price (万円)', value=7500)
    current_age = st.number_input('Current age of the house', value=0)
    max_age = st.number_input(
        'Amortization period',
        value=22,
        help='Different property type can have different amortization period. For example, a wooden house will be amortized over 22 years.'
    )
    broker_fee = st.number_input('Broker fee', format='%f', value=0.07)
    include_maintainance_cost = st.checkbox(
        "Discount maintanance cost when selling", 
        value=False, 
        help="Whether or not to devalue by the maintenance cost that is due every ~15 years (roof, paint, etc) when selling the house."
    )

    st.subheader('Loan details')
    principal = st.number_input('Mortgage amount (万円)', value=int(0.9 * (house_price + land_price)), key=11)
    mortgage_rate = st.number_input('Mortgage rate', format='%f', value=0.01, key=92)
    mortage_period = st.number_input('Mortgage period', value=30, key=12)

    house = RealEstate(
        house_value=house_price,
        house_age=current_age,
        fully_amortized_age=max_age,
        land_value=land_price,
        down_payment=(house_price + land_price) * (1 + broker_fee) - principal,
        broker_fee=broker_fee,
        market_rate=appreciation_rate
    )
    loan = Loan(
        principal=principal,
        yearly_interest=mortgage_rate,
        term=mortage_period
    )
    buy_bank = Bank(initial_deposit=0, interest_rate=market_rate)


# Initialize cashflows
for year in range(n + 1):
    
    rent_cashflow = rent.cashflow(year)
    buy_cashflow = house.cashflow(year) + loan.cashflow(year)
    
    # Rent
    amount_invested_in_stocks = max(0, abs(buy_cashflow) - abs(rent_cashflow))
    rent_bank.add_cash(amount_invested_in_stocks)

    # Buy
    amount_invested_in_stocks = max(0, abs(rent_cashflow) - abs(buy_cashflow))
    buy_bank.add_cash(amount_invested_in_stocks)

# Compute value
rdata, bdata = [], []
for year in range(n + 1):
    # Rent
    npv = sum(rent.cashflow(y, discount_rate=inflation_rate) for y in range(year + 1))
    if invest_difference:
        npv += rent_bank.value_at_year(year, discount_rate=inflation_rate)
    rdata.append({
        'year': year,
        'total_cost': rent.cashflow(year),
        'rent_cost': rent.cashflow(year),
        'loan_cost': 0,
        'house_cost': 0,
        'loan_value': 0,
        'house_value': 0,
        'bank_cashflow': rent_bank.cashflow(year),
        'npv': npv,
        'invested': rent_bank.cashflow(year),
        'source': 'Rent'
    })
    
    # Buy
    npv = loan.value_at_year(year) + house.value_at_year(year, max_year=n, include_maintainance_cost=include_maintainance_cost)
    for y in range(year + 1):
        npv += loan.cashflow(y, discount_rate=inflation_rate)
        npv += house.cashflow(y, discount_rate=inflation_rate)
    if invest_difference:
        npv += buy_bank.value_at_year(year, discount_rate=inflation_rate)
    bdata.append({
        'year': year,
        'total_cost': loan.cashflow(year) + house.cashflow(year),
        'rent_cost': 0,
        'loan_cost': loan.cashflow(year),
        'house_cost': house.cashflow(year),
        'loan_value': loan.value_at_year(year),
        'house_value': house.value_at_year(year),
        'bank_cashflow': buy_bank.cashflow(year),
        'npv': npv,        
        'source': 'Buy'
    })


with tabs[1]:
    st.subheader("Cashflow and value table")
    rent_data = pd.DataFrame(rdata)
    st.dataframe(rent_data, use_container_width=True, hide_index=True)

with tabs[2]:
    st.subheader("Cashflow and value table")
    buy_data = pd.DataFrame(bdata)
    st.dataframe(buy_data, use_container_width=True, hide_index=True)


with tabs[0]:
    st.subheader("Rent Or Buy")

    data = pd.concat([rent_data, buy_data])
    fig = px.bar(data, x="year", y="total_cost", color="source", barmode='group', title="Project cost (nominal 万円)")
    st.plotly_chart(fig, use_container_width=True)

    fig = px.line(data, x="year", y="npv", color="source", title=f"Project Net Present Value (real 万円)")
    st.plotly_chart(fig, use_container_width=True)  
