# -*- coding: utf-8 -*-
#! /usr/bin/env python
from __future__ import absolute_import
import sys
import pprint
import time

from binance.client import Client
g_api_key = ""
g_secret_key = ""

def set_key(api_key, secret_key):
    global g_api_key, g_api_secret
    g_api_key = api_key
    g_secret_key = secret_key

api = Client(g_api_key, g_secret_key);


def get_price(ticker, currency):
    a = api.get_all_tickers()
    b = [x for x in a if x['symbol']==ticker+currency]
    return float(b[0]['price'])
