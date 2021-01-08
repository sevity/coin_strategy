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

# param #######################################################################
BETTING = 1000
MAX_TICKER = 20  # 한턴에 보는 코인수(너무 많으면 느려지니 고정으로..) 
MAX_TICK = 100 # 몇틱기다리는지 설정(이 안에 급상승해야함)
THRESHOLD = 0.015  # 1.5%상승하면 올라탐
PROFIT_CUT = 0.3  # 30%이상 상승하면 익절하고 스톱함
LOSS_CUT = 0.05  # 수익률이 5%이하로 떨어지면 손절함
ban_tickers = []  # 떡상 직후등 피해야할코인들 나열
COOL_TIME = 30
###############################################################################
total_tickers = [
    'MFT','IQ','CRE','MBL','STMX','SC','MED','EDR','TSHP','SPND','TT', 'IOST', 'AHT', 'QKC', 'ANKR', 'TFUEL', 'OST', 'PXL',
    'SRN', 'CHZ', 'GTO', 'ORBS', 'UPP', 'MOC', 'STPT', 'VET', 'TRX', 'ZIL', 'LOOM', 'IGNIS', 'SNT', 'CVC', 'POLY', 
    'BORA', 'HBAR', 'AERGO', 'DKA', 'WAXP', 'EMC2', 'XEM', 'MANA', 'ARDR', 'POWR', 'XLM', 'ELF', 'SOLVE', 'ADA', 'DMT',
    'ONG', 'STORJ', 'MLK', 'ENJ', 'GRS', 'STEEM', 'ADX', 'HIVE', 'BAT', 'THETA', 'IOTA', 'MTL', 'ICX', 'ZRX', 'ARK',
    'KMD', 'ONT', 'SBD', 'LSK', 'KNC', 'OMG', 'GAS', 'WAVES', 'QTUM', 'EOS', 'XTZ', 'KAVA', 'ATOM', 'ETC',
    'LINK', 'BTG', 'NEO', 'REP', 'LTC', 'JST', 'CRO', 'TON', 'SXP', 'LAMB', 'HUNT', 'MARO', 'PLA', 'DOT', 'QTCON', 'MVL', 'BCHA'
    ]
FEE = 0.0005  # 0.05%, 위아래 해서 0.1%인듯
###############################################################################
f = open("../upbit_api_key.txt", 'r')
access_key = f.readline().rstrip()
secret_key = f.readline().rstrip()
f.close()
coin = Coin('upbit',access_key,secret_key)
def tick_round(price):
    t = coin.get_tick_size(price)
    return int(price / t) * t
def fsame(a, b, diff=0.0001):  # default: 0.01%이내로 같으면 true 리턴
    a = float(a)
    b = float(b)
    if abs(a-b)<diff:
        return True
    return False

for ticker in ban_tickers:
    total_tickers.remove(ticker)
print('BETTING:{}, THRESHOLD:{:.2f}%'.format(BETTING, THRESHOLD*100))
hit_prices={}
hit_cnts={}
while True:
    cnt = min(MAX_TICKER, len(total_tickers))
    random.shuffle(total_tickers)
    tickers = total_tickers[:cnt]
    print('\ntickers: {}'.format(tickers))
    prices = {}
    n = datetime.now()
    out = False
    while (datetime.now() - n).seconds < COOL_TIME:
        for ticker in tickers:
            if ticker not in prices: prices[ticker] = deque(maxlen=MAX_TICK)
            prices[ticker].append(coin.get_price(ticker, 'KRW'))
            # print(ticker, prices[ticker])
            # if len(prices[ticker]) >= MAX_TICK:
            pt = prices[ticker]
            ratio = pt[-1]/pt[0]-1.0
            if pt[0] < pt[-1] and ratio >= THRESHOLD:
                if ticker not in hit_cnts: hit_cnts[ticker] = 0
                hit_cnts[ticker] += 1
                print(ticker, prices[ticker])
                print('! {} hit.. up_ratio = {:.2f}%(from {} to {})'.
                    format(ticker, ratio*100, pt[0], pt[-1]))
                if hit_cnts[ticker] > 1:
                    print('out..')
                    continue
                if ticker in hit_prices and hit_prices[ticker] < pt[-1]:
                    print('11')
                    coin.market_buy(ticker, BETTING * 100)
                else:
                    print('22')
                    coin.market_buy(ticker, BETTING)
                    hit_cnts[ticker] = 0
                time.sleep(5)  # wait market buy to be filled(it took some time sometime)
                for ix in range(0, 5):
                    info = coin.get_asset_info(ticker)
                    print('33', info)
                    if 'free' in info:
                        cnt = info['free']
                        coin.limit_sell(ticker, tick_round(pt[-1] * 1.02), cnt)
                        hit_prices[ticker] = pt[-1]
                        break
                out = True
        if out: break
        print(".", end="", flush=True)




























