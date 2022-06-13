from time import strptime
import requests
import config
import pandas as pd
from datetime import datetime
# from AccountBook import worksheet
import AccountBook

class Analysis():
    # """
    # tools for analysis and graphical reports
    # """

    def __init__(self):
        pass

    # def summary():
    #     df = self.worksheet
    #     print(df.info)

    def balance(worksheet):
        """
        get balance of this month
        """
        df = pd.DataFrame(worksheet.get_all_records())
        
        # df["Date"] = datetime.strptime(df["Date"], "%Y-%m-%d")
        # modify the data type
        df["Date"] = df["Date"].apply(lambda x : datetime.strptime(x, "%Y-%m-%d").date())
        
        # the first day of this month
        firstDay = datetime.today().date().replace(day=1)
        today = datetime.today().date()
        # filter rows
        df = df[ (df["Date"] >= firstDay) & (df['Date'] <= today) ]
        # reset the index to prevent multiplication problem
        df = df.reset_index(drop=True)

        # convert currencies
        rate_USD_TWD = ExchangeRate("USD").getRate("TWD")
        rate_JPY_TWD = ExchangeRate("JPY").getRate("TWD")
        rate_CNY_TWD = ExchangeRate("CNY").getRate("TWD")
        rate_EUR_TWD = ExchangeRate("EUR").getRate("TWD")
        isUSD = pd.Series([ rate_USD_TWD if item == "USD" else 1 for item in df["Currency"]])
        isJPY = pd.Series([ rate_JPY_TWD if item == "JPY" else 1 for item in df["Currency"]])
        isCNY = pd.Series([ rate_CNY_TWD if item == "CNY" else 1 for item in df["Currency"]])
        isEUR = pd.Series([ rate_EUR_TWD if item == "EUR" else 1 for item in df["Currency"]])
        df["Amount_TWD"] = df["Amount"].multiply(isUSD).multiply(isJPY).multiply(isCNY).multiply(isEUR)
        print(df)

        # usage of list comprehension
        # [f(x) if condition else g(x) for x in sequence]
        sign = pd.Series([1 if item == "收入" else -1 for item in df["CashFlow"]])
        balance = sum(df["Amount_TWD"].multiply(sign))
        print(balance)
        
        return {
            'balance' : balance,
            'start_date' : firstDay,
            'end_date'   : today,
            'average_daily_cost' : round( balance / ( (today - firstDay).days + 1 ) )
        }

    def totalBalance(worksheet):
        """
        get total balance from the very beginning
        """
        df = pd.DataFrame(worksheet.get_all_records())
        firstDay = datetime.strptime(df["Date"][0], "%Y-%m-%d").date()
        today = datetime.today().date()
        df = df.reset_index(drop=True)

        # convert currencies
        rate_USD_TWD = ExchangeRate("USD").getRate("TWD")
        rate_JPY_TWD = ExchangeRate("JPY").getRate("TWD")
        rate_CNY_TWD = ExchangeRate("CNY").getRate("TWD")
        rate_EUR_TWD = ExchangeRate("EUR").getRate("TWD")
        isUSD = pd.Series([ rate_USD_TWD if item == "USD" else 1 for item in df["Currency"]])
        isJPY = pd.Series([ rate_JPY_TWD if item == "JPY" else 1 for item in df["Currency"]])
        isCNY = pd.Series([ rate_CNY_TWD if item == "CNY" else 1 for item in df["Currency"]])
        isEUR = pd.Series([ rate_EUR_TWD if item == "EUR" else 1 for item in df["Currency"]])
        df["Amount_TWD"] = df["Amount"].multiply(isUSD).multiply(isJPY).multiply(isCNY).multiply(isEUR)

        # usage of list comprehension
        # [f(x) if condition else g(x) for x in sequence]
        sign = pd.Series([1 if item == "收入" else -1 for item in df["CashFlow"]])
        balance = sum(df["Amount_TWD"].multiply(sign))
        print(balance)
        
        return {
            'balance' : balance,
            'start_date' : firstDay,
            'end_date'   : today,
            'average_daily_cost' : round( balance / ( (today - firstDay).days + 1 ) )
        }


class ExchangeRate():
    """
    frequently used currencies:
    TWD, CNY, USD, JPY, EUR
    """
    def __init__(self, base_country_name):
        self.base_country_name = base_country_name
        self.url = f"https://v6.exchangerate-api.com/v6/{config.exchange_rate_API_key}/latest/{base_country_name}"
        self.response = requests.get(self.url)
        self.data = self.response.json()

    def getRate(self, country_name):
        return self.data['conversion_rates'][country_name]


if __name__ == "__main__":
    # 1 NTD to how many JPY
    # print(ExchangeRate("TWD").getRate("JPY"))

    monthlyBalance = Analysis.balance(AccountBook.worksheet)
    print(monthlyBalance)