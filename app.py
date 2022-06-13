# import requests
import re
# from datetime import datetime

from flask import Flask, request, abort
# import json, time
import pandas as pd

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

# use flex message
# from linebot.models import FlexSendMessage
from linebot.models.flex_message import (
    BubbleContainer, ImageComponent
)
from linebot.models.actions import URIAction

from config import *
# from AccountBook import worksheet
from AccountBook import GoogleSheet
from AccountBook import CurrencyConverter
from tools import Analysis

app = Flask(__name__)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'



@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # Account Book Part
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file("./credentials/gs_credentials.json", scopes=scope)
    sheet_url = 'YOUR_GOOGLE_SHEET_URL'
    accountBook = GoogleSheet(scope, creds, sheet_url)

    # expense or income
    if event.message.text[:2] in ["支出", "收入"]:
        try:
            # add record
            record = accountBook.convertText(event.message.text)
            df = accountBook.createRecord(record)
            accountBook.writeRecod(df)
            message = TextSendMessage(text = "Successfully add record!!")
            line_bot_api.reply_message(event.reply_token, message)
        except ValueError as e:
            message = TextSendMessage(text = str(e))
            line_bot_api.reply_message(event.reply_token, message) 
            

    # list the 10 latest records
    elif event.message.text[:2] == "查詢":
        df = accountBook.readRecord(length = 10)
        message = TextSendMessage(text=str(df)) # make the text string become a certain class that can be passed by the API
        line_bot_api.reply_message(event.reply_token, message)

    # delete the last record
    elif event.message.text[:5] == "刪除上一筆":
        try:
            df = accountBook.deleteRecord()
            message = TextSendMessage(text="已經刪除此筆紀錄:\n {foo} ".format(foo=str(df))) # make the text string become a certain class that can be passed by the API
            line_bot_api.reply_message(event.reply_token, message)
        except Exception as e:
            message = TextSendMessage(text = str(e))
            line_bot_api.reply_message(event.reply_token, message)


    # look up for exchange rate
    elif re.search("換|兌換", event.message.text):
        try:
            # get the wanted currencies
            country1, country2 = CurrencyConverter.convertText(text_string = event.message.text)
            # find the rate
            rate = CurrencyConverter(country1, country2).rate
            rate_inv = CurrencyConverter(country2, country1).rate 
            # return result
            message = TextSendMessage(text = f"{country1}兌換{country2}匯率為 1 : {rate} \n{country2}兌換{country1}匯率為 1 : {rate_inv}")
            line_bot_api.reply_message(event.reply_token, message)
        except Exception as e:
            message = TextSendMessage(text = str(e))
            line_bot_api.reply_message(event.reply_token, message)

    
    elif event.message.text[:2] == "餘額":
        monthlyBalance = Analysis.balance(accountBook.worksheet)
        message = TextSendMessage(text = f"Statistics from {str(monthlyBalance['start_date'])} to {str(monthlyBalance['end_date'])} \nCurrent balance is: {monthlyBalance['balance']} NTD\nAverage daily cost is about {monthlyBalance['average_daily_cost']} NTD")
        line_bot_api.reply_message(event.reply_token, message)

    elif event.message.text == "總餘額":
        monthlyBalance = Analysis.totalBalance(accountBook.worksheet)
        message = TextSendMessage(text = f"Statistics from {str(monthlyBalance['start_date'])} to {str(monthlyBalance['end_date'])} \nCurrent balance is: {monthlyBalance['balance']} NTD\nAverage daily cost is about {monthlyBalance['average_daily_cost']} NTD")
        line_bot_api.reply_message(event.reply_token, message)

    elif event.message.text == "測試":
        flex_message = FlexSendMessage(
            alt_text='我的部落格',
            contents=BubbleContainer(
                direction='ltr',
                hero=ImageComponent(
                    url='https://i0.wp.com/boyie.net/wp-content/uploads/2020/08/cropped-14717253_1452837184729843_8645981290308045583_n.jpg?w=664&ssl=1',
                    size='full',
                    aspect_ratio='20:13',
                    aspect_mode='cover',
                    action=actions.URIAction(uri='https://boyie.net', label='label')
                )
            )
        )
        line_bot_api.reply_message(event.reply_token, flex_message)

    elif event.message.text == "表單":
        flex_message = FlexSendMessage(
            alt_text='記帳本 google sheet 連結',
            contents=BubbleContainer(
                direction='ltr',
                hero=ImageComponent(
                    url='https://i0.wp.com/boyie.net/wp-content/uploads/2020/08/cropped-14717253_1452837184729843_8645981290308045583_n.jpg?w=664&ssl=1',
                    size='full',
                    aspect_ratio='20:13',
                    aspect_mode='cover',
                    action=actions.URIAction(uri='YOUR_GOOGLE_SHEET_URL', label='label')
                )
            )
        )
        line_bot_api.reply_message(event.reply_token, flex_message)
    
    else:
        content = TextSendMessage(text = "記帳本格式範例：\n支出 60 早餐 信用卡 台幣\n\n快速記帳格式範例：\n收入 薪水 1000\n或：\n支出 10 午餐\n\n刪除紀錄：刪除上一筆\n\n查詢帳本：清單")
        line_bot_api.reply_message(event.reply_token, content)


if __name__ == "__main__":
    # app.run()
    app.run(port=5001, debug=True)