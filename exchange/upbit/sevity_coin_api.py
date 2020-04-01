# -*- coding: utf-8 -*-
#! /usr/bin/env python
from __future__ import absolute_import
import sys
import pprint
import time
import json
import requests
import os
import jwt
import uuid
import hashlib
from urllib.parse import urlencode

server_url = 'https://api.upbit.com'

g_api_key = ""
g_secret_key = ""

def set_key(api_key, secret_key):
    global g_api_key, g_api_secret
    g_api_key = api_key
    g_secret_key = secret_key


def get_price(ticker, currency):
    url = server_url + "/v1/orderbook"
    querystring = {"markets":"{}-{}".format(currency, ticker)}
    response = requests.request("GET", url, params=querystring)
    j = json.loads(response.text)
    ask1 = float(j[0]["orderbook_units"][0]["ask_price"])
    bid1 = float(j[0]["orderbook_units"][0]["bid_price"])
    return (ask1+bid1)/2

def get_asset_info(currency):
    url = server_url + "/v1/accounts"

    payload = {
        'access_key': g_api_key,
        'nonce': str(uuid.uuid4()),
    }

    jwt_token = jwt.encode(payload, g_secret_key).decode('utf-8')
    authorize_token = 'Bearer {}'.format(jwt_token)
    headers = {"Authorization": authorize_token}
    res = requests.get(url, headers=headers)

    print(res.json())

    rk = get_balance_info()
    r = {}
    r['total'] = round(float(rk['data']['total_' + currency.lower()]), 4)
    r['inuse'] = round(float(rk['data']['in_use_' + currency.lower()]), 4)
    r['free'] = round(float(rk['data']['available_' + currency.lower()]), 4)
    return r
