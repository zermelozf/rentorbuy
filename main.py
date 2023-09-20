from collections import defaultdict

import streamlit as st
import numpy as np
import pandas as pd

import plotly.express as px

from models import Bank, Loan, RealEstate, Rent, Salary


n = st.sidebar.slider("Timeline (years)", value=35, max_value=50)

st.sidebar.markdown('# Economic conditions')
market_rate = st.sidebar.number_input('Stock Market rate', value=0.05, format='%f')
appreciation_rate = st.sidebar.number_input('House Market rate', value=0.02, format='%f', key=10)
inflation_rate = st.sidebar.number_input('Inflation rate', value=0.02, format='%f')
monthly_salary = st.sidebar.number_input('Available money', value=300_000)
salary_increase_rate = st.sidebar.number_input('Available money increase rate', value=0.0, format='%f')

tabs = st.tabs(["Summary", "Rent", "Buy"])

with tabs[1]:
    st.markdown('# Rent')
    monthtly_rent = st.number_input('Monthly rent', value=120000, key='1')
    renewal_fee = st.number_input('Renewal fee', value=240000, key='4')

    bank_rent = Bank(initial_deposit=0, interest_rate=market_rate)
    rent = Rent(
        monthly_rent=monthtly_rent, 
        renewal_fee=renewal_fee,
        inflation_rate=inflation_rate
    )

with tabs[2]:
    st.markdown('# House')
    house_price = st.number_input('House price', value=40_000_000, key=7)
    land_price = st.number_input('Land price', value=60_000_000, key=8)
    broker_fee = st.number_input('Broker fee', value=0.07, key=9)

    st.markdown('# Financing')
    principal2 = st.number_input('Mortgage amount', value=int(0.9 * (house_price + land_price)), key=11)
    mortage_period2 = st.number_input('Mortgage period', value=25, key=12)
    mortgage_rate2 = st.number_input('Mortgage rate', value=0.005, key=13)

    bank_buy = Bank(initial_deposit=0, interest_rate=market_rate)
    house = RealEstate(
        house_value=house_price,
        land_value=land_price,
        down_payment=(house_price + land_price) * (1 + broker_fee) - principal2,
        broker_fee=broker_fee,
        market_rate=appreciation_rate,
        inflation_rate=inflation_rate
    )
    loan = Loan(
        principal=principal2,
        yearly_interest=mortgage_rate2,
        term=mortage_period2,
        inflation_rate=inflation_rate
    )

salary = Salary(
    monthly_salary=monthly_salary,
    yearly_bonus=0,
    increase_rate=salary_increase_rate,
    inflation_rate=inflation_rate
)


with tabs[0]:
    st.subheader("Rent Or Buy")

    data = []
    for year in range(n):
        cashflow = rent.cashflow(year) + salary.cashflow(year)
        bank_rent.add_cash(cashflow)
        assets = bank_rent.value_at_year(year)
        data.append({
            'year': year,
            'cashflow': cashflow,
            'value': assets,
            'source': 'Rent'
        })
        cashflow = house.cashflow(year) + loan.cashflow(year) + salary.cashflow(year)
        bank_buy.add_cash(cashflow)
        assets = house.value_at_year(year) + bank_buy.value_at_year(year)
        liabilities = loan.value_at_year(year)
        
        data.append({
            'year': year,
            'cashflow': cashflow,
            'value': assets + liabilities,
            'source': 'Buy'
        })

    
    data = pd.DataFrame(data)
    fig = px.bar(data, x="year", y="cashflow", color="source", barmode='group', title="Cashflow")
    st.plotly_chart(fig, use_container_width=True)

    fig = px.line(data, x="year", y="value", color="source", title="Net Worth")
    st.plotly_chart(fig, use_container_width=True)
    
