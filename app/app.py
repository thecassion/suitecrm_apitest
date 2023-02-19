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
                "name",
                "email1",
                "phone_mobile"
            ],
            "link_name_to_fields_array": [],
            "max_results": "50",
            "deleted": "0",
            "Favorites": "false"
        }
        response = restRequest(method, arguments)
        next_offset = response.get('next_offset')
        if response.get('next_offset') == int(response.get('total_count')):
            next_offset = None
        leads.append(response.get('entry_list'))

        #Connect to MySQL with pymysql
        connect_string =  settings.db_url
        
        connection = pymysql.connect(host=settings.db_host, user=settings.db_user, password=settings.db_password, db=settings.db_database, charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
        conn = connection.cursor()
        #Create table leads if leads table exists truncate it
        conn.execute("CREATE TABLE IF NOT EXISTS leads (id VARCHAR(255), name VARCHAR(255), email1 VARCHAR(255), phone_mobile VARCHAR(255))")
        conn.execute("TRUNCATE TABLE leads")
        #Insert data to MySQL
        for lead in leads[0]:
            conn.execute("INSERT INTO leads (id, name, email1, phone_mobile) VALUES (%s, %s, %s, %s)", (lead['id'], lead['name_value_list']['name']['value'], lead['name_value_list']['email1']['value'], lead['name_value_list']['phone_mobile']['value']))
        connection.commit()
        conn.close()

    return leads