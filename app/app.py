from fastapi import FastAPI
import requests
from bs4 import BeautifulSoup
import hashlib
import json
import pymysql
from .config import settings
from sqlalchemy import create_engine
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
# do request to SuiteCRM , url: https://suitecrmdemo.dtbc.eu/service/v4/rest.php
def restRequest(method,arguments):
    url = "https://suitecrmdemo.dtbc.eu/service/v4/rest.php"
    #url = "https://suite8demo.suiteondemand.com/service/v4/rest.php"
    payload = {
        "method": method,
        "input_type": "JSON",
        "response_type": "JSON",
        "rest_data": json.dumps(arguments)
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        # 'accept': 'application/json'
    }
    response = requests.request("POST", url,headers=headers, data=payload)
    return response.json()

"""
     Get all leads
"""
@app.get("/leads")
def get_leads():
    # login to SuiteCRM
    password = hashlib.md5()
    password.update('Demo'.encode('utf-8')) # password is Demo
    __auth = {'user_name':'Demo', 'password':password.hexdigest(),'version':'1'}
    args = {'user_auth':__auth, 'application_name':'RestTest', 'name_value_list':[]}
    response = restRequest('login',args)


    session_id = response.get('id')
    if session_id is None:
        print("Login failed")
        print(response)
        return {"response":response,"status":"failed","password":password.hexdigest()}

    method = "get_entry_list"
    next_offset = 0
    leads = []
    while next_offset is not None:
        arguments = {
            "session": session_id,
            "module_name": "Leads",
            "query": "",
            "order_by": "",
            "offset": next_offset,
            "select_fields": [
                "id",
                "first_name",
                "last_name",
                "phone_work",

            ],
            "link_name_to_fields_array": [],
            "max_results": "50",
            "deleted": "0",
            "Favorites": "false"
        }
        response = restRequest(method, arguments)
        next_offset = response.get('next_offset')
        if response.get('next_offset') == int(response.get('total_count')):
            print("next_offset is equal to total_count",  response.get('next_offset'))
            next_offset = None
        print("next_offset", next_offset)
        leads +=response.get('entry_list')
    #Connect to MySQL with pymysql
    connection = pymysql.connect(host=settings.db_host, user=settings.db_user, password=settings.db_password, db=settings.db_database, charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
    conn = connection.cursor()
    #Drop table leads if exists
    conn.execute("DROP TABLE IF EXISTS leads")
    #Create table leads if leads table exists truncate it
    conn.execute("CREATE TABLE IF NOT EXISTS leads (id VARCHAR(255), first_name VARCHAR(255), last_name VARCHAR(255), phone_work VARCHAR(255))")
    #Insert data to MySQL
    for lead in leads:
        conn.execute("INSERT INTO leads (id, first_name, last_name, phone_work) VALUES (%s, %s, %s, %s)", (lead['id'], lead['name_value_list']['first_name']['value'], lead['name_value_list']['last_name']['value'], lead['name_value_list']['phone_work']['value']))
    connection.commit()
    conn.close()

    return leads


"""
        Get Bitcoin USD price
"""
@app.get("/bitcoinusd")
def get_bitcoin():
    #Get Bitcoin USD prices from coinapi.io with trade historical data
    url = "https://rest.coinapi.io/v1/trades/BITSTAMP_SPOT_BTC_USD/history?period_id=1DAY&time_start=2023-02-18T00:00:00"
    apiKey="ADFE5322-81FD-47AA-8350-A39076E9F03B"
    headers = {
        'X-CoinAPI-Key': apiKey
    }
    response = requests.request("GET", url, headers=headers)
    print(response.json())
    #Connect to MySQL with pymysql
    connection = pymysql.connect(host=settings.db_host, user=settings.db_user, password=settings.db_password, db=settings.db_database, charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
    conn = connection.cursor()
    #Drop table bitcoin if exists
    conn.execute("DROP TABLE IF EXISTS bitcoin")
    #Create table bitcoin if bitcoin table exists truncate it
    conn.execute("CREATE TABLE IF NOT EXISTS bitcoin (symbol_id VARCHAR(255), time_exchange VARCHAR(255), time_coinapi VARCHAR(255), uuid VARCHAR(255), price VARCHAR(255), size VARCHAR(255), taker_side VARCHAR(255))")
    #Insert data to MySQL
    for data in response.json():
        conn.execute("INSERT INTO bitcoin (symbol_id, time_exchange, time_coinapi, uuid, price, size, taker_side) VALUES (%s, %s, %s, %s, %s, %s, %s)", (data['symbol_id'], data['time_exchange'], data['time_coinapi'], data['uuid'], data['price'], data['size'], data['taker_side']))
    connection.commit()
    conn.close()

    return response.json()