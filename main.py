import numpy as np
import pandas as pd
import streamlit as st

import plotly.express as px

from mortgage import Loan


st.title('Rent or Buy')

n = st.sidebar.slider("Max. number of years", value=12)

st.sidebar.markdown('# Rent')
monthly_rent = st.sidebar.number_input('Montly rent', value=120000)
renewal_money = st.sidebar.number_input('Renewal money', value=120000)

st.sidebar.markdown('# Buy')
property_price = st.sidebar.number_input('Property price', value=40000000)
land_price = st.sidebar.number_input('Land price', value=60000000)
broker_fee = st.sidebar.number_input('Broker fee', value=12000)

st.sidebar.markdown('# Financing')
mortgage_value = (property_price + land_price) * \
    st.sidebar.number_input('Mortgage rate', value=0.9)
inflation_rate = st.sidebar.number_input('Inflation rate', value=12000)
mortage_period = st.sidebar.number_input('Mortgage period', value=25)
mortgage_rate = st.sidebar.number_input('Mortgage rate', value=0.005)
market_rate = st.sidebar.number_input('Market rate', value=0.05)
appreciation_rate = st.sidebar.number_input('Appreciation rate', value=0.02)


mv = Loan(principal=mortgage_value, interest=0.0375, term=30)

records = []
for year in range(n):
    rent = monthly_rent * 12 + renewal_money * (year % 2)
    loan = float(mv.monthly_payment * 12) if year < n else 0
    if year == 0:
        loan += (property_price + land_price) - mortgage_value
    records.append({
        'year': year,
        'cash': -rent,
        'source': 'rent'
    })
    records.append({
        'year': year,
        'cash': -loan,
        'source': 'buy'
    })
    records.append({
        'year': year,
        'cash': loan - rent,
        'source': 'rent surplus'
    })

cashflow = pd.DataFrame(records)
fig = px.bar(cashflow, x="year", y="cash", color="source",
             barmode="group", title="Cashflow")
st.plotly_chart(fig, use_container_width=True)

asset = 0
records = [{
    'year': 0,
    'assets': 0,
    'source': 'rent'
}, {
    'year': 0,
    'assets': land_price + property_price,
    'source': 'buy'
}]
for row in cashflow[cashflow['source'] == 'rent surplus'].to_dict(orient="records"):
    asset = (asset + row['cash']) * (1 + market_rate)
    records.append({
        'year': row['year'] + 1,
        'assets': asset,
        'source': 'rent'
    })

    records.append({
        'year': row['year'] + 1,
        'assets': land_price * (1 + appreciation_rate)**int(row['year']) + property_price * (n - row['year']) / 26,
        'source': 'buy'
    })

assets = pd.DataFrame(records)
fig = px.line(assets, x="year", y="assets", color="source", title="Assets")
st.plotly_chart(fig, use_container_width=True)
