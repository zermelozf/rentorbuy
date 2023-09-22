from collections import defaultdict

import streamlit as st
import numpy as np
import pandas as pd

import plotly.express as px

from models import Bank, Loan, RealEstate, Rent, Salary


n = st.sidebar.slider("Timeline (years)", value=35, max_value=50)

st.sidebar.markdown('# Economic conditions')
market_rate = st.sidebar.number_input('Stock Market return', value=0.05, format='%f')
appreciation_rate = st.sidebar.number_input('House Market return', value=0.02, format='%f', key=10)
rent_increase_rate = st.sidebar.number_input('Rent increase rate', value=0.02)
inflation_rate = st.sidebar.number_input('Inflation rate', value=0.0, format='%f')
monthly_salary = st.sidebar.number_input('Monthly budget (万円)', value=30)
starting_balance = st.sidebar.number_input('Starting bank balance (万円)', value=3000)
salary_increase_rate = st.sidebar.number_input('Monthly budget increase rate', value=0.0, format='%f')

tabs = st.tabs(["Summary", "Rent", "Buy #1", "Buy #2"])

salary = Salary(
    monthly_salary=monthly_salary,
    yearly_bonus=0,
    increase_rate=salary_increase_rate,
    inflation_rate=inflation_rate
)

with tabs[1]:
    st.markdown('## Rent')
    monthtly_rent = st.number_input('Monthly rent (万円)', value=12, key='1')
    renewal_fee = st.number_input('Renewal fee (万円)', value=24, key='4')

    bank_rent = Bank(
        initial_deposit=starting_balance,
        interest_rate=market_rate,
        inflation_rate=inflation_rate
    )
    rent = Rent(
        monthly_rent=monthtly_rent, 
        renewal_fee=renewal_fee,
        rent_increase_rate=rent_increase_rate,
        inflation_rate=inflation_rate
    )
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
    
    rent_data = pd.DataFrame(data)
    fig = px.bar(rent_data, x="year", y="cashflow", color="source", barmode='group', title="Cashflow (万円)")
    st.plotly_chart(fig, use_container_width=True)

    fig = px.line(rent_data, x="year", y="value", color="source", title="Net Worth (万円)")
    st.plotly_chart(fig, use_container_width=True)
    

with tabs[2]:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Property details")
        property_type = st.selectbox(
            'House or appartment?',
            ('House', 'Appartment')
        )
        house_price = st.number_input(f'{property_type} price (万円)', value=2000, key=7)
        land_price = st.number_input('Land price (万円)', value=5000, key=8)
        broker_fee = st.number_input('Broker fee', format='%f', value=0.07, key=9)

    
    with col2:
        st.subheader('Loan details')
        principal2 = st.number_input('Mortgage amount (万円)', value=int(0.9 * (house_price + land_price)), key=11)
        mortage_period2 = st.number_input('Mortgage period', value=25, key=12)
        mortgage_rate2 = st.number_input('Mortgage rate', format='%f', value=0.005, key=13)

    bank_buy = Bank(
        initial_deposit=starting_balance, 
        interest_rate=market_rate,
        inflation_rate=inflation_rate
    )
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
    data = []
    for year in range(n):
        cashflow = house.cashflow(year) + loan.cashflow(year) + salary.cashflow(year)
        bank_buy.add_cash(cashflow)
        assets = house.value_at_year(year) + bank_buy.value_at_year(year)
        liabilities = loan.value_at_year(year)
        
        data.append({
            'year': year,
            'cashflow': cashflow,
            'value': assets + liabilities,
            'source': 'Buy #1'
        })
    buy1_data = pd.DataFrame(data)
    fig = px.bar(buy1_data, x="year", y="cashflow", color="source", barmode='group', title="Cashflow (万円)")
    st.plotly_chart(fig, use_container_width=True)

    fig = px.line(buy1_data, x="year", y="value", color="source", title="Net Worth (万円)")
    st.plotly_chart(fig, use_container_width=True)

with tabs[3]:
    st.markdown('# House')
    house_price = st.number_input('House price (万円)', value=4000, key=27)
    land_price = st.number_input('Land price (万円)', value=6000, key=28)
    broker_fee = st.number_input('Broker fee', format='%f', value=0.07, key=29)

    st.markdown('# Financing')
    principal2 = st.number_input('Mortgage amount (万円)', value=int(0.9 * (house_price + land_price)), key=211)
    mortage_period2 = st.number_input('Mortgage period', value=25, key=212)
    mortgage_rate2 = st.number_input('Mortgage rate', format='%f', value=0.005, key=213)

    bank_buy = Bank(
        initial_deposit=starting_balance, 
        interest_rate=market_rate,
        inflation_rate=inflation_rate
    )
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
    data = []
    for year in range(n):
        cashflow = house.cashflow(year) + loan.cashflow(year) + salary.cashflow(year)
        bank_buy.add_cash(cashflow)
        assets = house.value_at_year(year) + bank_buy.value_at_year(year)
        liabilities = loan.value_at_year(year)
        
        data.append({
            'year': year,
            'cashflow': cashflow,
            'value': assets + liabilities,
            'source': 'Buy #2'
        })
    buy2_data = pd.DataFrame(data)
    fig = px.bar(buy2_data, x="year", y="cashflow", color="source", barmode='group', title="Cashflow (万円)")
    st.plotly_chart(fig, use_container_width=True)

    fig = px.line(buy2_data, x="year", y="value", color="source", title="Net Worth (万円)")
    st.plotly_chart(fig, use_container_width=True)


with tabs[0]:
    st.subheader("Rent Or Buy")

    
    data = pd.concat([rent_data, buy1_data, buy2_data])
    fig = px.bar(data, x="year", y="cashflow", color="source", barmode='group', title="Cashflow (万円)")
    st.plotly_chart(fig, use_container_width=True)

    fig = px.line(data, x="year", y="value", color="source", title="Net Worth (万円)")
    st.plotly_chart(fig, use_container_width=True)
    
