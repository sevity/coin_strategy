# -*- coding: utf-8 -*-
#! /usr/bin/env python
from __future__ import absolute_import
import sys
import pprint
import time
import json

import requests
url = "https://api.upbit.com/v1/orderbook"

g_api_key = ""
g_secret_key = ""

def set_key(api_key, secret_key):
    global g_api_key, g_api_secret
    g_api_key = api_key
    g_secret_key = secret_key


def get_price(ticker, currency):
    url = "https://api.upbit.com/v1/orderbook"
    querystring = {"markets":"{}-{}".format(currency, ticker)}
    response = requests.request("GET", url, params=querystring)
    j = json.loads(response.text)
    ask1 = float(j[0]["orderbook_units"][0]["ask_price"])
    bid1 = float(j[0]["orderbook_units"][0]["bid_price"])
    return (ask1+bid1)/2