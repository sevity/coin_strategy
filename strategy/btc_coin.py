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
# 설명 ########################################################################
# BTC개수를 늘리는걸 최우선으로 하여, KRW로 bid후 ask하는 전략
# param #######################################################################
KRW_DELTA = 200000  # 이걸 기준으로 촘촘하게 주문을 낸다.
BETTING = 10000    # 초기버전은 고정배팅으로 가보자
###############################################################################
# legacy or fixed
FEE = 0.0005
###############################################################################
f = open("../upbit_api_key.txt", 'r')      
access_key = f.readline().rstrip()         
secret_key = f.readline().rstrip()         
f.close()                                  
coin = Coin('upbit',access_key,secret_key) 

print('KRW_DELTA:{:,}'.format(KRW_DELTA), 'BETTING:{:,}'.format(BETTING))

prev_msg = ''
def print_msg(msg):  # 중복 제거 print
    global prev_msg
    if prev_msg == msg: return
    prev_msg = msg
    print(msg)

bid_prices={}
bid_cnt={}  # 이가격대 bid낸 횟수, 횟수가 오를수록 돈도 많이 건다
l = coin.get_live_orders('BTC', 'KRW')
for (oid, askbid, price, cnt, odt) in l:
    if askbid=='bid':
        # bid_prices[oid] = price
        coin.cancel(oid)

while True:
    # 먼저 현재 KRW_DELTA간격에 놓여있는 bid-ask pair를 확인한다.
    cp = coin.get_price('BTC', 'KRW')  # coin price
    bp = int((cp - (KRW_DELTA/2)) / KRW_DELTA) * KRW_DELTA + 1000 # bid price
    ap = bp + KRW_DELTA - 2000# ask price
    
    # check fill
    bps = copy.deepcopy(bid_prices)
    l = coin.get_live_orders('BTC', 'KRW')
    for (oid, askbid, price, cnt, odt) in l:
        if askbid=='bid':
            if oid in bps:
                del bps[oid]
    # 체결된 bid에 대해 ask걸기 
    for oid, price in bps.items():
        print('! {} bid filled. placing ask..'.format(price))
        ap = float(price) + KRW_DELTA - 2000
        bet = BETTING * bid_cnt[price] / (1.0 - FEE)
        coin.limit_sell('BTC', ap, bet / ap)
        del bid_prices[oid]
        # time.sleep(5)
        continue

    bfound = False
    afound = False
    for (oid, askbid, price, cnt, odt) in l:
        if askbid=='bid' and int(float(price)) == bp:
            bfound = True
        if askbid=='ask' and int(float(price)) == ap:
            afound = True
    # ask없는 bid에 대해 주문
    if bfound is False and afound is False:
        print_msg('current BTC price:{:,}, bid price:{:,}, ask price:{:,}'.format(cp, bp, ap))
        bps = copy.deepcopy(bid_prices)
        for oid, price in bps.items():
            if price < bp:
                coin.cancel(oid)
                del bid_prices[oid]

        if bp not in  bid_cnt: bid_cnt[bp] = 0
        bid_cnt[bp] += 1

        bet = BETTING * bid_cnt[bp] / (1.0 + FEE)
        oid = coin.limit_buy('BTC', bp, bet / bp)
        if oid != -1:
            bid_prices[oid] = bp
            print('! bid_prices:', bid_prices, 'bid_cnt({:,}):{}'.format(bp, bid_cnt[bp]))
            # time.sleep(5)
        else:
            bid_cnt[bp] /= 2





















