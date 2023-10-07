import uuid

import streamlit as st
import numpy_financial as npf
import numpy as np
import pandas as pd

import plotly.express as px
import plotly.graph_objects as go


from models import Loan, RealEstate, Rent

if "costs" not in st.session_state:
    st.session_state["costs"] = []


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
    help=('What is the minimum return on investment you require? For example, it could be the rate of an '
          'alternative investment, like the interest rate on a cash account, or the bond or stocks market.')
)
inflation_rate = 0.02

tabs = st.tabs(["Summary", "Rent", "Buy"])


with tabs[1]:
    st.markdown('## Rent')
    monthtly_rent = st.number_input('Monthly rent (万円)', value=18)
    renewal_fee = st.number_input('Renewal fee (万円)', value=monthtly_rent)
    rent_increase_rate = st.number_input('Yearly rent increase', value=0.01)
    
    rent = Rent(
        monthly_rent=monthtly_rent,
        renewal_fee=renewal_fee,
        rent_increase_rate=rent_increase_rate
    )



with tabs[2]:
    col1, col2 = st.columns(2)
    st.subheader("Property details")
    house_price = st.number_input('House price (万円)', value=1000)
    land_price = st.number_input('Land price (万円)', value=8500)
    current_age = st.number_input('Current age of the house', value=0)
    max_age = st.number_input(
        'Amortization period',
        value=15,
        help=("Different property type can have different amortization period. For example, a wooden "
              "house will be amortized over 22 years.")
    )
    surface = st.number_input('Surface (m^2)', value=100)
    broker_fee = st.number_input('Broker fee', format='%f', value=0.07)
    
    st.subheader("Maintenance costs")
    col1, col2 = st.columns(2)
    tt, vv = [], []

    def add_cost():
        element_id = uuid.uuid4()
        st.session_state["costs"].append(str(element_id))

    def remove_cost(row_id):
        st.session_state["costs"].remove(str(row_id))

    def generate_cost(cost_id):
        cost_container = st.empty()
        cost_columns = cost_container.columns((3, 2, 1))
        cost_value = cost_columns[0].number_input("Amount", value=0, key=f"txt_{cost_id}")
        cost_time = cost_columns[1].number_input("When", step=1, value=0, key=f"nbr_{cost_id}")
        cost_columns[2].button("🗑️", key=f"del_{cost_id}", on_click=remove_cost, args=[cost_id])
        return {"value": cost_value, "time": cost_time}
    
    costs, c = [], [0] * (n + 1)
    for row in st.session_state["costs"]:
        cost_data = generate_cost(row)
        costs.append(cost_data)
        c[cost_data['time']] += cost_data['value']

    st.button("Add cost", on_click=add_cost)

    include_maintainance_cost = True
    
    house = RealEstate(
        house_value=house_price,
        house_age=current_age,
        fully_amortized_age=max_age,
        land_value=land_price,
        costs=c,
        broker_fee=broker_fee,
        market_rate=appreciation_rate
    )

    st.subheader('Loan details')
    principal = st.number_input('Mortgage amount (%)', value=0.9) * house.buy_cost()
    mortgage_rate = st.number_input('Mortgage rate', format='%f', value=0.01)
    mortage_period = st.number_input('Mortgage period', value=30)

    
    loan = Loan(
        principal=principal or 1,
        yearly_interest=mortgage_rate,
        term=mortage_period,
        first_payment=house.buy_cost() - principal
    )


# Initialize cashflows
data = {
    'year': [],
    'saved_rent': [],
    'cashflow (万円)': [],
    'house value': [],
    'loan value': [],
    'npv (万円)': [],
    'irr (%)': [],
    'total cost': [],
    'total revenue': []
}
cost = []
for year in range(n + 1):
    data['year'].append(year)
    data['saved_rent'].append(-rent.cashflow(year))
    data['cashflow (万円)'].append(house.cashflow(year) + loan.cashflow(year))
    cashflow_with_sale = np.array(data['cashflow (万円)']) + np.array(data['saved_rent'])
    data['total cost'].append(np.sum(cashflow_with_sale))
    data['house value'].append(house.value_at_year(year))
    data['loan value'].append(loan.value_at_year(year))
    sale_revenue = house.value_at_year(year) + loan.value_at_year(year)
    if include_maintainance_cost:
        for y in range(year + 1, n + 1):
            sale_revenue += house.cashflow(y, discount_rate=inflation_rate)
    data['total revenue'].append(sale_revenue)
    cost.append({'year': year, 'cashflow (万円)': rent.cashflow(year), 'revenue': 0, 'source': 'rent'})
    cost.append({'year': year, 'cashflow (万円)': loan.cashflow(year) + house.cashflow(year), 'revenue': sale_revenue, 'source': 'buy & sell'})

    cashflow_with_sale[-1] += sale_revenue
    data['npv (万円)'].append(npf.npv(discount_rate, cashflow_with_sale))
    data['irr (%)'].append(round(npf.irr(cashflow_with_sale) * 100, 2))
data = pd.DataFrame(data)
cost = pd.DataFrame(cost)


with tabs[0]:
    st.subheader("Rent Or Buy?")

    if (house_price == 0) or (land_price == 0):
        st.info("Please start by **setting your rent price and the price of the house and land** in the `Rent` and `Buy` "
                "tabs respectively. to set the characteristics of you project. You can then come back here to "
                "visualize the results.")
    else:
        should_buy = False
        for y, v in enumerate(data['npv (万円)']):
            if v >= 0:
                should_buy = True
                break
        
        if should_buy:
            st.info(
                f"Buying a house is more interesting if you intend to :orange[**stay in it for more than {y} years**]. "
                "For a shorter period of time, renting is more interesting financially.", icon="ℹ️")
        else:
            st.warning(
                f":orange[**You should rent.**] Buying a house is not an interesting compared to an alternative "
                f"that can deliver a {int(discount_rate * 100):.0f}% return on investment.", icon="ℹ️")
        
        fig = px.line(data, x="year", y="npv (万円)", title=f"Net Present Value of buying a house")
        st.plotly_chart(fig, use_container_width=True)
        
        b = np.argmax(data['irr (%)'])
        c = -int(data['total cost'][b] * 10000)
        st.info(f"If you buy a house, in order to maximize your investment's rate of return, you should :orange[**resell "
                f"it after {b} years.**] This will get you a :orange[**{data['irr (%)'][b]:.2f}% annualized rate of "
                f"return.**]", icon="ℹ️")
       
        fig = px.line(data, x="year", y="irr (%)", title="Internal Rate of Return of buying a house")
        st.plotly_chart(fig, use_container_width=True)


        st.info(f"Overall, the investment over {b} years will cost you {c:,} JPY {'more' if c > 0 else 'less'} than renting "
                f"{'but' if c > 0 else 'and'} :orange[**you will pocket {int((data['total revenue'][b] +  data['cashflow (万円)'][b])* 10000):,} JPY when "
                f"selling the house.**]", icon="ℹ️")
        

        data = cost.loc[cost['year'] <= b, :]
        data.loc[data['year'] != b, 'revenue'] = 0
        data['cashflow (万円)'] += data['revenue']
        fig = px.bar(data, x="year", y="cashflow (万円)", color="source", barmode="group", title="Yearly Cashflow")
        st.plotly_chart(fig, use_container_width=True)
    