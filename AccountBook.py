import re
import pandas as pd
from datetime import datetime
import pytz
from google.oauth2.service_account import Credentials
import gspread
from tools import ExchangeRate

# google authentication and operations
class GoogleSheet():

    def __init__(self, scope, creds, sheet_url):
        self.scope = scope
        self.creds = creds
        # self.gs = gs
        self.gs = gspread.authorize(creds)
        # self.sheet = sheet
        self.sheet = self.gs.open_by_url(sheet_url)
        # self.worksheet = worksheet
        self.worksheet = self.sheet.get_worksheet_by_id(0)

    # parse text messages to structured lists
    @staticmethod
    def convertText(text_string):
        """
        This function input a string, and then output a list
        All input message should be seperated by spaces
        e.g. 支出 100 早餐 信用卡 無 
        ideal format would be: 支出 金額 項目 支付方式 備註
        """
        text_list = text_string.split(" ")
        text_list = list(filter(None, text_list)) # remove empty elements when space occurs at the end

        # check validity
        if text_list[0] not in ["支出", "收入"]:
            raise ValueError("輸入文字開頭為 '{foo}' ，格式不正確，請輸入'支出'或'收入' ".format(foo=text_list[0]))
        elif len(text_list) < 3:
            raise ValueError("輸入文字為\n '{foo}'\n請至少輸入: \n支出/收入 項目名稱 金額 \n三項訊息 ".format(foo = " ".join(text_list)))
        elif len(text_list) > 6:
            raise ValueError("輸入文字為\n '{foo}' \n請至多輸入: \n支出/收入 項目名稱 金額 支付方式 備註 貨幣 \n六項訊息 ".format(foo = " ".join(text_list)))
        elif len(re.findall("\s\d+\s|\s\d+", text_string)) == 0:
            raise ValueError("輸入文字為\n '{foo}' \n找不到金額數字，請重新輸入 ".format(foo = " ".join(text_list)))

        # find currency
        if re.search("美元|美金|usd|USD", text_string):
            currency = "USD"
        elif re.search("台幣|新台幣|NTD|ntd", text_string):
            currency = "NTD"
        elif re.search("日圓|YEN|yen|JPY", text_string):
            currency = "JPY"
        elif re.search("人民幣|RMB|rmb", text_string):
            currency = "CNY"
        elif re.search("歐元|歐|EUR", text_string):
            currency = "EUR"
        else:
            currency = "USD"


        # find 金額
        dollarAmount = re.findall("\s\d+\s|\s\d+", text_string)[0].replace(" ", "")
        text_list.remove(dollarAmount)
        dollarAmount = int(dollarAmount)

        # make the list structured
        while len(text_list) < 4:
            text_list.append("NA")
        text_list.append(currency)
        text_list.append(dollarAmount)
        

        return text_list


    # add records
    @staticmethod
    def createRecord(text_list):
        """
        This function input the structured list parsed from the message text
        and then create a pandas dataframe to store the list values
        Format: ["支出", "項目", "支付方式", "備註", 金額]
        """
        tz = pytz.timezone('Asia/Taipei') 
        now = datetime.now(tz)

        newRecord = pd.DataFrame(
            {
                "Date"     : now.strftime("%Y-%m-%d"),
                "Time"     : now.strftime("%H:%M:%S"),
                "CashFlow" : text_list[0],
                "Amount"   : text_list[len(text_list)-1],
                "Title"    : text_list[1],
                "Method"   : text_list[2],
                "Note"     : text_list[3],
                "Currency" : text_list[len(text_list)-2],
            }, 
            index = [1]
        )

        return newRecord    

    # write dataframe to google sheet
    def writeRecod(self, df_newRecord):
        df_current = pd.DataFrame(self.worksheet.get_all_records())
        df = pd.concat([df_current, df_newRecord], axis=0)
        # update the whole worksheet
        print(df)
        self.worksheet.update([df.columns.values.tolist()] + df.values.tolist())


    # read past records
    def readRecord(self, length = 10):
        df_current = pd.DataFrame(self.worksheet.get_all_records())

        if df_current.shape[0] == 0:
            raise Exception("Current sheet has 0 rows, cannot display any record")
        else:
            df_current = df_current[["CashFlow", "Amount", "Title"]]
        return df_current.tail(length)


    # delete last entry
    def deleteRecord(self):
        df_current = pd.DataFrame(self.worksheet.get_all_records())
        
        toDel = df_current.tail(1)
        if df_current.shape[0] == 0:
            raise Exception("Current sheet has 0 rows, cannot remove any row")
        else:
            self.worksheet.delete_row(df_current.shape[0]+1)
            df_current = pd.DataFrame(self.worksheet.get_all_records())
            # print(df_current.shape)
        return toDel.iloc[0]     





class CurrencyConverter(ExchangeRate):
    def __init__(self, country1, country2):
        self.rate = ExchangeRate(country1).getRate(country2)

    def convertText(text_string):
        if not re.search("美金|美元|USD|台幣|新台幣|NTD|TWD|日幣|日圓|JPY|YEN|人民幣|RMB|CNY|EUR|歐元|歐", text_string):
            raise Exception("當前搜尋字串內無常用貨幣，請輸入 '台幣兌換美金' 或日圓/歐元/人民幣")
        elif re.search("美金|美元|USD", text_string) and re.search("台幣|新台幣|NTD|TWD", text_string):
            return ("TWD", "USD")
        elif re.search("台幣|新台幣|NTD|TWD", text_string) and re.search("YEN|JPY|日圓|日幣", text_string):
            return ("TWD", "JPY")
        elif re.search("台幣|新台幣|NTD|TWD", text_string) and re.search("RMB|CNY|人民幣", text_string):
            return ("TWD", "CNY") 
        elif re.search("台幣|新台幣|NTD|TWD", text_string) and re.search("EUR|歐元|歐", text_string):
            return ("TWD", "EUR")
        elif re.search("美金|美元|USD", text_string) and re.search("EUR|歐元|歐", text_string):
            return ("USD", "EUR")
        else:
            raise Exception("目前不支援這組貨幣兌換查詢")

# Testing

if __name__ == "__main__":
    # test_string = "支出 100 早餐 linepay100 餐費"
    test_string = "支出 測試 12"
    # test_string = "支出 100 早餐 "
    # test_string = "支 100 早餐 linepay"
    # test_string = "支出 100 "
    # test_string = "支出 一百 早餐 linepay50 "
    # test_string = "收入 1 抽獎 "
    print(GoogleSheet.convertText(test_string))
    
    # df = createRecord(convertText(test_string))
    # print(df)

    # writeRecod(df)
    # readRecord()    