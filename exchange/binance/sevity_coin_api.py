# -*- coding: utf-8 -*-
#! /usr/bin/env python
from __future__ import absolute_import
import sys
import pprint
import time

from binance.client import Client
from .sevity_key import *


api = Client(api_key, api_secret);


def get_price(ticker, currency):
    a = api.get_all_tickers()
    b = [x for x in a if x['symbol']==ticker+currency]
    return float(b[0]['price'])
