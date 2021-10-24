#TODO: 400원에 팔고 다시 400원에 사는경우 매수 금액을 1/3로 줄이는거 검토해보자#..
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from coin import *
import time
import math
import random
import copy
from datetime import datetime, timezone, timedelta
import telegram
import numpy as np
from collections import deque
import ast
from sty import fg, bg, ef, rs
import argparse

import pickle
from pathlib import Path

# 설명 ########################################################################
# 분할매도 주문 내줌 
# param #######################################################################
###############################################################################
parser = argparse.ArgumentParser(description='spread sell for BTC market')
parser.add_argument('--verbose', '-v', required=False, action='store_true', help='print debug messages.')
parser.add_argument('--ticker', '-t', required=True, help='coin name ex)ETH')
parser.add_argument('--spread_top', '-st', required=False, default=0, help='top most sell price')
parser.add_argument('--spread_cnt', '-sc', required=False, default=10, help='how many spread sell order do you want?')
args = parser.parse_args()
VERBOSE = args.verbose
if VERBOSE: print('verbose option is ON!')
TICKER = args.ticker.upper()
SPREAD_TOP = float(args.spread_top)
SPREAD_CNT = int(args.spread_cnt)
###############################################################################
f = open("../upbit_api_key.txt", 'r')      
access_key = f.readline().rstrip()         
secret_key = f.readline().rstrip()         
token = f.readline().rstrip()
chat_id = f.readline().rstrip()
f.close()                                  
coin = Coin('upbit',access_key,secret_key) 
bot = telegram.Bot(token=token)
def send_telegram(msg):
    # print(msg)
    try:
        bot.sendMessage(chat_id=chat_id, text=msg)
    except:
        pass
def fsame(a, b, diff=0.00000001):  # default: 0.01%이내로 같으면 true 리턴
    return True if abs(float(a)-float(b))<diff else False
def format_8f(dict):
    d = copy.deepcopy(dict)
    for key, val in d.items():
        d[key] = '{:.8f}'.format(val) 
    return d

ticker_free_cnt = coin.get_asset_info(TICKER)['free']
print('to sell: '+fg.li_blue+'{}'.format(ticker_free_cnt)+fg.rs+'{}'.format(TICKER))
cp = float(coin.get_price(TICKER, 'BTC'))  # coin price
print('current price:'+fg.yellow+'{:.8f}'.format(cp)+fg.rs+'BTC') 
if fsame(SPREAD_TOP, 0): SPREAD_TOP=cp*2
print('SPREAD_TOP:'+fg.yellow+'{:.8f}'.format(SPREAD_TOP)+fg.rs+'BTC('+fg.red+'{:.2f}X'.format(SPREAD_TOP/cp)+fg.rs+'), SPREAD_CNT:'+fg.green+'{}'.format(SPREAD_CNT)+fg.rs)
gap = (SPREAD_TOP - cp) / SPREAD_CNT
for ix in range(SPREAD_CNT-1):
    coin.limit_sell_btc(TICKER, cp+gap*(ix+1), ticker_free_cnt/SPREAD_CNT, True, True)
remain = coin.get_asset_info(TICKER)['free']
coin.limit_sell_btc(TICKER, SPREAD_TOP, remain, True, True)


