
import pandas as pd
import numpy as np

import mortgage


class RealEstate:

    def __init__(
            self, 
            house_value, 
            house_age,
            fully_amortized_age,
            land_value,
            costs=[],
            house_surface=100,
            broker_fee=0.07, 
            market_rate=0.02
        ):
        self.house_value = house_value
        self.house_age = house_age
        self.house_surface = house_surface
        self.fully_amortized_age = fully_amortized_age
        self.land_value = land_value
        self.costs = costs
        self.broker_fee = broker_fee
        self.market_rate = market_rate

    @property
    def total_cost(self):
        return (self.house_value + self.land_value) * (1 + self.broker_fee)

    def buy_cost(self):
        value = self.land_value + self.house_value * (1 - min(1, self.house_age / self.fully_amortized_age))
        return value * (1 + self.broker_fee)

    def maintenance_cost(self, year):
        print(self.costs, year)
        return -self.costs[year]
    
    def taxe_cost(self, year):
        return -self.value_at_year(year) * (.04 / 6 *  + .03 / 3)

    def value_at_year(self, year, discount_rate=0.0):
        value = self.land_value + self.house_value * (1 - min(1, (year + self.house_age) / self.fully_amortized_age))
        value *= (1 - self.broker_fee) * (1 + self.market_rate)**year
        return value / (1 + discount_rate)**year

    def cashflow(self, year, discount_rate=0.0):
        flow = self.taxe_cost(year)
        flow += self.maintenance_cost(year)
        return flow / (1 + discount_rate)**year


class Bank:

    def __init__(self, initial_deposit, interest_rate=0):
        self.initial_deposit = initial_deposit
        self.interest_rate = interest_rate
        self.cashflows = []

    def add_cash(self, amount):
        self.cashflows.append(amount)

    def value_at_year(self, year, discount_rate=0.0):
        value = self.initial_deposit
        for cf in self.cashflows[:year + 1]:
            value += cf
            if value > 0:
                value *= (1 + self.interest_rate)
        return value / (1 + discount_rate)**year

    def cashflow(self, year, discount_rate=0.0):
        return self.cashflows[year]


class Rent:

    def __init__(self, monthly_rent, renewal_fee, rent_increase_rate):
        self.monthly_rent = monthly_rent
        self.renewal_fee = renewal_fee
        self.rent_increase_rate = rent_increase_rate

    def cashflow(self, year, discount_rate=0.0):
        flow = -self.monthly_rent * 12 
        if year % 2 == 0:
            flow -= self.renewal_fee
        flow *= (1 + self.rent_increase_rate)**year
        return flow / (1 + discount_rate)**year

    def value_at_year(self, year, discount_rate=0.0):
        return 0


class Loan:

    def __init__(self, principal, yearly_interest, term, first_payment):
        self.loan = mortgage.Loan(
            principal=principal,
            interest=yearly_interest,
            term=term
        )
        self.monthly_payment = float(self.loan.monthly_payment)
        self.principal = principal
        self.interest = yearly_interest
        self.term = term
        self.first_payment = first_payment

    def down_payment(self, year):
        if year == 0:
            return -self.first_payment
        return 0

    def cashflow(self, year, discount_rate=0.0):
        flow = -self.monthly_payment * 12 if year < self.term else 0
        flow += self.down_payment(year)
        return flow / (1 + discount_rate)**year

    def value_at_year(self, year, discount_rate=0.0):
        value =  -(float(self.loan.total_paid) - self.monthly_payment * 12 * year)
        return min(value, 0) / (1 + discount_rate)**year

class Salary:

    def __init__(self, monthly_salary, yearly_bonus=0, years_until_retirement=30, increase_rate=0):
        self.monthly_salary = monthly_salary
        self.yearly_bonus = yearly_bonus
        self.increase_rate = increase_rate
        self.years_until_retirement = years_until_retirement

    def cashflow(self, year, discount_rate=0.0):
        if year >= self.years_until_retirement:
            return 0
        flow = self.monthly_salary * 12 + self.yearly_bonus 
        flow *= (1 + self.increase_rate)**year
        return flow / (1 + discount_rate)**year


if __name__ == '__main__':
    salary = Salary(monthly_salary=600_000)
    rent = Rent(monthly_rent=120_000)
    bank = Bank(initial_deposit=30_000_000, interest_rate=0.07)
    house = RealEstate(
        house_value=40_000_000,
        land_value=60_000_000,
        down_payment=30_000_000,
        broker_fee=0.07,
        market_rate=0.02
    )
    loan = Loan(
        principal=70_000_000,
        yearly_interest=0.005,
        term=10
    )

    n = 30
    for year in range(n):
        cashflow = house.cashflow(year) + loan.cashflow(year)
        assets = bank.value_at_year(year) + house.value_at_year(year)
        liabilities = loan.value_at_year(year)
        bank.add_cash(cashflow)
        record = {
            'year': year,
            'cashflow': cashflow,
            'assets': assets,
            'liabilities': liabilities,
            'net_worth': assets + liabilities
        }
        print(record)
