import streamlit as st
import numpy_financial as npf
import numpy as np
import pandas as pd

import plotly.express as px
import plotly.graph_objects as go


from models import Bank, Loan, RealEstate, Rent


n = st.sidebar.slider("Timeline (years)", value=35, max_value=50)

st.sidebar.markdown('# Economic conditions')
appreciation_rate = st.sidebar.number_input(
    'Housing Market return', 
    value=0.02, 
    format='%f',
    help='How much do you expect the value of your house to grow over time?'
)
discount_rate = st.sidebar.number_input(
    'Minimum expected return', 
    value=0.05, 
    format='%f',
    help='What is the minimum return on investment you require? For example, it could be the rate of an alternative investment, like the interest rate on a cash account, or the bond or stocks market.'
)
inflation_rate = 0.02

tabs = st.tabs(["Summary", "Rent", "Buy"])


with tabs[1]:
    st.markdown('## Rent')
    monthtly_rent = st.number_input('Monthly rent (万円)', value=12)
    renewal_fee = st.number_input('Renewal fee (万円)', value=12)
    rent_increase_rate = st.number_input('Yearly rent increase', value=0.01)
    
    rent = Rent(
        monthly_rent=monthtly_rent,
        renewal_fee=renewal_fee,
        rent_increase_rate=rent_increase_rate
    )



with tabs[2]:
    col1, col2 = st.columns(2)
    st.subheader("Property details")
    house_price = st.number_input('House price (万円)', value=3000)
    land_price = st.number_input('Land price (万円)', value=9500)
    current_age = st.number_input('Current age of the house', value=24)
    max_age = st.number_input(
        'Amortization period',
        value=22,
        help='Different property type can have different amortization period. For example, a wooden house will be amortized over 22 years.'
    )
    surface = st.number_input('Surface (m^2)', value=100)
    maintenance_fee = st.number_input('Maintenance fee (万円)', value=5 * surface)
    maintenance_frequency = st.number_input('Maintenance frequency (in years)', value=15)
    include_maintainance_cost = st.checkbox(
        "Seller discounts future costs", 
        value=True, 
        help="If selling a house that must have maintenance work done soon, the value of the house should go down. Inflation is used to compute how much devalue to incur."
    )
    broker_fee = st.number_input('Broker fee', format='%f', value=0.07)

    house = RealEstate(
        house_value=house_price,
        house_age=current_age,
        fully_amortized_age=max_age,
        land_value=land_price,
        broker_fee=broker_fee,
        market_rate=appreciation_rate,
        maintenance_fee=maintenance_fee,
        maintenance_frequency=maintenance_frequency
    )

    st.subheader('Loan details')
    principal = st.number_input('Mortgage amount (%)', value=0.9) * house.buy_cost()
    mortgage_rate = st.number_input('Mortgage rate', format='%f', value=0.01)
    mortage_period = st.number_input('Mortgage period', value=30)

    
    loan = Loan(
        principal=principal,
        yearly_interest=mortgage_rate,
        term=mortage_period,
        first_payment=house.buy_cost() - principal
    )


# Initialize cashflows
data = {
    'year': [],
    'saved_rent': [],
    'cashflow': [],
    'house value': [],
    'loan value': [],
    'npv': [],
    'irr': [],
    'total cost': [],
    'total revenue': []
}
cost = []
for year in range(n + 1):
    cost.append({'year': year, 'cost': loan.down_payment(year), 'source': 'down payment'})
    cost.append({'year': year, 'cost': loan.cashflow(year) - loan.down_payment(year), 'source': 'loan'})
    cost.append({'year': year, 'cost': house.maintenance_cost(year), 'source': 'maintenance cost'})
    cost.append({'year': year, 'cost': house.taxe_cost(year), 'source': 'taxes'})
    data['year'].append(year)
    data['saved_rent'].append(-rent.cashflow(year))
    data['cashflow'].append(house.cashflow(year) + loan.cashflow(year))
    cashflow_with_sale = np.array(data['cashflow']) + np.array(data['saved_rent'])
    data['total cost'].append(np.sum(cashflow_with_sale))
    data['house value'].append(house.value_at_year(year))
    data['loan value'].append(loan.value_at_year(year))
    sale_revenue = house.value_at_year(year) + loan.value_at_year(year)
    if include_maintainance_cost:
        for y in range(year + 1, n + 1):
            sale_revenue += house.cashflow(y, discount_rate=inflation_rate)
    data['total revenue'].append(sale_revenue)

    cashflow_with_sale[-1] += sale_revenue
    data['npv'].append(npf.npv(discount_rate, cashflow_with_sale))
    data['irr'].append(round(npf.irr(cashflow_with_sale), year))
data = pd.DataFrame(data)


with tabs[0]:
    st.subheader("Rent Or Buy?")

    should_buy = False
    for y, v in enumerate(data['npv']):
        if v >= 0:
            should_buy = True
            break
    
    if should_buy:
        st.info(f"Buying a house is more interesting if you intend to :orange[**stay for more than {y} years**]. For shorter periods, renting is more interesting financially.", icon="ℹ️")
    else:
        st.warning(f":orange[**You should rent.**] Buying a house is not an interesting compared to an alternative that can deliver a {int(discount_rate * 100):.0f}% return on investment.", icon="ℹ️")
    
    fig = px.line(data, x="year", y="npv", title=f"Net Present Value of buying a house (real 万円)")
    st.plotly_chart(fig, use_container_width=True)

    if should_buy:
        st.info(f"Your :orange[**loan will cost {int(loan.monthly_payment * 10000):,} JPY/month**] or {int(loan.monthly_payment * 12 * 10000):,} JPY/year. You will also need to pay for the maintenance cost, and taxes for your home.", icon="ℹ️")
    else:
        st.warning(f"If you still want to buy, your :orange[**loan will cost {int(loan.monthly_payment * 10000):,} JPY/month**] or {int(loan.monthly_payment * 12 * 10000):,} JPY/year. You will also need to pay for the maintenance cost, and taxes for your home.", icon="ℹ️")
    
    fig = px.bar(cost, x="year", y="cost", color="source", title="Yearly Cashflow if buying a house (nominal 万円)")
    st.plotly_chart(fig, use_container_width=True)

    b = np.argmax(data['irr'])
    c = -int(data['total cost'][b] * 10000)
    
    if should_buy:
        st.info(f"In order to maximize your investment's rate of return, you should :orange[**sell after {b} years.**] The investment will have cost you {c:,} JPY {'more' if c > 0 else 'less'} than renting {'but' if c > 0 else 'and'} you will pocket {int(data['total revenue'][b] * 10000):,} JPY when selling the house. That represents a :orange[**{data['irr'][b] * 100:.2f}% yearly rate of return**] on your cashflow.", icon="ℹ️")
    else:
        st.info(f"You can {'still' if data['irr'][b] > 0 else ''} expect a :orange[**{data['irr'][b] * 100:.2f}% return on investment**] if you :orange[**resell your house after {b} years.**] The investment will have cost you {c:,} JPY {'more' if c > 0 else 'less'} than renting {'but' if c > 0 else 'and'} you will pocket {int(data['total revenue'][b] * 10000):,} JPY when selling the house.", icon="ℹ️")
    fig = px.line(data, x="year", y="irr", title="Internal Rate of Return if buying a house")
    st.plotly_chart(fig, use_container_width=True)

