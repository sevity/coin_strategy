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
# BETTING = 0  # AUTO
###############################################################################
# legacy or fixed
FEE = 0.0005
MIN_BET_FOR_AUTO = 20000
###############################################################################
f = open("../upbit_api_key.txt", 'r')      
access_key = f.readline().rstrip()         
secret_key = f.readline().rstrip()         
f.close()                                  
coin = Coin('upbit',access_key,secret_key) 

print('KRW_DELTA:{:,}'.format(KRW_DELTA), 'BETTING:{:,}'.format(BETTING))

bid_prices={}
bid_volume={}
bid_gop={}  # 이가격대 bid낸 횟수, 횟수가 오를수록 돈도 많이 건다
l = coin.get_live_orders('BTC', 'KRW')
for (oid, askbid, price, cnt, odt) in l:
    if askbid=='bid':
        coin.cancel(oid)

bAuto = False
if BETTING == 0:
    bAuto = True
    BETTING = max(MIN_BET_FOR_AUTO, int(coin.get_asset_info('KRW')['free'] / 10))
    print('auto BETTING start from: {:,} KRW'.format(BETTING))

while True:
    if bAuto:
        BETTING = max(MIN_BET_FOR_AUTO, coin.get_asset_info('KRW')['free'] / 10)
        # print('auto BETTING: {:,} KRW'.format(BETTING))

    # 먼저 현재 KRW_DELTA간격에 놓여있는 bid-ask pair를 확인한다.
    cp = int(coin.get_price('BTC', 'KRW'))  # coin price
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
        ap = float(price) + KRW_DELTA - 2000
        bet = price * bid_volume[oid] * (1.0 + FEE) / (1.0 - FEE)
        gain = bid_volume[oid] - bet / ap
        print('!! {} bid filled. placing ask..'.format(price),
            'gain after ask: {:.8f}({:,}KRW)'.format(gain, int(gain * ap)))
        coin.limit_sell('BTC', ap, bet / ap)
        del bid_prices[oid]
        if bid_gop[price] < 1: bid_gop[price] *= 2
        else: bid_gop[price] += 1
        # time.sleep(5)
    if len(bps) > 0: continue

    bfound = False
    afound = False
    for (oid, askbid, price, cnt, odt) in l:
        if askbid=='bid' and int(float(price)) == bp:
            bfound = True
        if askbid=='ask' and int(float(price)) == ap:
            afound = True
    # ask없는 bid에 대해 주문
    if bfound is False and afound is False:
        print('current BTC price:{:,} KRW, bid price:{:,}, ask price:{:,}'.format(cp, bp, ap))
        bps = copy.deepcopy(bid_prices)
        for oid, price in bps.items():
            if price < bp:
                coin.cancel(oid)
                bid_gop[price] -= 1
                del bid_prices[oid]

        if bp not in  bid_gop: bid_gop[bp] = 1
        bid_gop[bp] = max(1, bid_gop[bp])

        bet = BETTING * bid_gop[bp] / (1.0 + FEE)
        oid = coin.limit_buy('BTC', bp, bet / bp)
        while oid == -1:
            bid_gop[bp] /= 2
            if bid_gop[bp] < 0.1:
                print('!!! no money!. will have 30 secs break..')
                bid_gop[bp] = 1
                time.sleep(30)
            bet = BETTING * bid_gop[bp] / (1.0 + FEE)
            oid = coin.limit_buy('BTC', bp, bet / bp)
            time.sleep(2)
        bid_prices[oid] = bp
        bid_volume[oid] = bet / bp
        print('! bid_prices:', bid_prices, 'bid_gop({:,}):{}'.format(bp, bid_gop[bp]))
        # time.sleep(5)





















