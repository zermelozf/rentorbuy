from collections import defaultdict

import streamlit as st
import numpy as np
import pandas as pd

import plotly.express as px

from models import Bank, Loan, RealEstate, Rent, Salary


n = st.sidebar.slider("Timeline (years)", value=35, max_value=50)

st.sidebar.markdown('# Economic conditions')
market_rate = st.sidebar.number_input('Stock Market return', value=0.05, format='%f', help='This return is used for inveting any cash left after paying the rent and/or loan into the stock market.')
appreciation_rate = st.sidebar.number_input('House Market return', value=0.02, format='%f', key=10, help='This return is used on the house and land.')
rent_increase_rate = st.sidebar.number_input('Rent increase rate', value=0.01, help='The yearly rate at which the rent increases.')
inflation_rate = st.sidebar.number_input('Inflation rate', value=0.02, format='%f', help='The inflation will not affect the value of available cash to invest after all payments. However, it will affect the value of the net worth. Setting the inflation rate to zero will make the Net Value be nominal, anything else will show real net worth.')
monthly_salary = st.sidebar.number_input('Monthly budget (万円)', value=30, help='This the amount of cash available to pay the rent or loan. If some cash is left after the rent or loan is paid, it will be invested in the stock market.')
starting_balance = st.sidebar.number_input('Starting bank balance (万円)', value=0, help='This is the balance of your bank account before you buy a house or start renting. This balance can be used to pay the first down payment on the house. Otherwise, it will be invested in the stock market entirely.')
salary_increase_rate = st.sidebar.number_input('Monthly budget increase rate', value=0.0, format='%f', help=' The yearly rate at which you increase your budget.')
year_until_retirement = st.sidebar.number_input('Years until retirement', value=30, help='After you retire, your budget will be automatically set to zero.')

tabs = st.tabs(["Summary", "Rent", "Buy"])

salary = Salary(
    monthly_salary=monthly_salary,
    yearly_bonus=0,
    increase_rate=salary_increase_rate,
    years_until_retirement=year_until_retirement,
    inflation_rate=inflation_rate
)

salaries = [salary.cashflow(year) for year in range(n)]
salaries[0] += starting_balance

with tabs[1]:
    st.markdown('## Rent')
    monthtly_rent = st.number_input('Monthly rent (万円)', value=24, key='1')
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
            'salaries': np.sum(salaries[:year + 1]),
            'source': 'Rent'
        })
    
    st.subheader("Cashflow and value table")
    rent_data = pd.DataFrame(data)
    st.dataframe(rent_data, use_container_width=True, hide_index=True)
    
    
    

with tabs[2]:
    col1, col2 = st.columns(2)
    st.subheader("Property details")
    house_price = st.number_input(f'House price (万円)', value=2000, key=7)
    land_price = st.number_input('Land price (万円)', value=5000, key=8)
    current_age = st.number_input(f'Current age of the house', value=0, key=72)
    max_age = st.number_input(f'Fully amortized age of the house', value=22, key=73, help='Different property type can have different amortization period. For example, a wooden house will be amortized over 22 years.')
    broker_fee = st.number_input('Broker fee', format='%f', value=0.07, key=9)

    st.subheader('Loan details')
    principal2 = st.number_input('Mortgage amount (万円)', value=int(0.9 * (house_price + land_price)), key=11)
    mortgage_rate2 = st.number_input('Mortgage rate', format='%f', value=0.01, key=92)
    mortage_period2 = st.number_input('Mortgage period', value=25, key=12)

    bank_buy = Bank(
        initial_deposit=starting_balance, 
        interest_rate=market_rate,
        inflation_rate=inflation_rate
    )
    house = RealEstate(
        house_value=house_price,
        house_age=current_age,
        fully_amortized_age=max_age,
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
            'salaries': np.sum(salaries[:year + 1]),
            'source': 'Buy'
        })

    st.subheader("Cashflow and value table")
    buy1_data = pd.DataFrame(data)
    st.dataframe(buy1_data, use_container_width=True, hide_index=True)


with tabs[0]:
    st.subheader("Rent Or Buy")

    
    data = pd.concat([rent_data, buy1_data])
    fig = px.bar(data, x="year", y="cashflow", color="source", barmode='group', title="Cash to invest (万円)")
    st.plotly_chart(fig, use_container_width=True)

    nominal_or_real = 'Real' if inflation_rate > 0 else 'Nominal'
    fig = px.line(data, x="year", y="value", color="source", title=f"{nominal_or_real} Net Worth (万円)")
    st.plotly_chart(fig, use_container_width=True)

