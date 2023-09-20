
import pandas as pd
import numpy as np

import mortgage


class RealEstate:

    def __init__(
            self, 
            house_value, 
            land_value, 
            down_payment=0, 
            property_type='HOUSE',
            broker_fee=0.07, 
            market_rate=0.02,
            inflation_rate=0
        ):
        self.house_value = house_value
        self.land_value = land_value
        self.down_payment = down_payment
        self.property_type = property_type
        self.broker_fee = broker_fee
        self.market_rate = market_rate
        self.inflation_rate = inflation_rate

    @property
    def total_cost(self):
        return (self.house_value + self.land_value) * (1 + self.broker_fee)

    @property
    def amortization_period(self):
        return 26 if self.property_type == 'HOUSE' else 45

    def value_at_year(self, n):
        value = self.land_value + self.house_value * (1 - min(1, n / self.amortization_period))
        value = (1 - self.broker_fee) * value * (1 + self.market_rate)**n 
        return value / (1 + self.inflation_rate)**n

    def cashflow(self, year):
        return -self.down_payment if year == 0 else 0 / (1 + self.inflation_rate)**year


class Bank:

    def __init__(self, initial_deposit, interest_rate=0, inflation_rate=0):
        self.initial_deposit = initial_deposit
        self.interest_rate = interest_rate
        self.cashflows = []
        self.inflation_rate = inflation_rate

    def add_cash(self, amount):
        self.cashflows.append(amount)

    def value_at_year(self, year):
        value = 0
        for cf in self.cashflows[:year+1]:
            value += cf
            if value > 0:
                value *= (1 + self.interest_rate)
        return value / (1 + self.inflation_rate)**year

    def cashflow(self, year):
        return 0 / (1 + self.inflation_rate)**year


class Rent:

    def __init__(self, monthly_rent, renewal_fee, inflation_rate=0):
        self.monthly_rent = monthly_rent
        self.inflation_rate = inflation_rate
        self.renewal_fee = renewal_fee

    def cashflow(self, year):
        value = self.monthly_rent * 12 
        if year % 2 == 0:
            value += self.renewal_fee
        return -value / (1 + self.inflation_rate)**year

    def value_at_year(self, year):
        return 0


class Loan:

    def __init__(self, principal, yearly_interest, term, inflation_rate=0):
        self.loan = mortgage.Loan(
            principal=principal,
            interest=yearly_interest,
            term=term
        )
        self.monthly_payment = float(self.loan.monthly_payment)
        self.principal = principal
        self.interest = yearly_interest
        self.term = term
        self.inflation_rate = inflation_rate

    def cashflow(self, year):
        value = -self.monthly_payment * 12 if year < self.term else 0
        return value / (1 + self.inflation_rate)**year

    def value_at_year(self, year):
        value =  -(float(self.loan.total_paid) - self.monthly_payment * 12 * (year + 1))
        return min(value, 0) / (1 + self.inflation_rate)**year


class Salary:

    def __init__(self, monthly_salary, yearly_bonus=0, increase_rate=0, inflation_rate=0):
        self.monthly_salary = monthly_salary
        self.yearly_bonus = yearly_bonus
        self.increase_rate = increase_rate
        self.inflation_rate = inflation_rate

    def cashflow(self, year):
        value = self.monthly_salary * 12 + self.yearly_bonus 
        return value * ((1 + self.increase_rate)/ (1 + self.inflation_rate))**year


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