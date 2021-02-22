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

# 설명 ########################################################################
# ETH개수를 늘리는걸 최우선으로 하여, KRW로 bid후 ask하는 전략
# param #######################################################################
KRW_DELTA = 10000  # 이걸 기준으로 촘촘하게 주문을 낸다.
# BETTING = 10000    # 초기버전은 고정배팅으로 가보자
BETTING = 0  # AUTO
MAX_BETTING = 1000000
###############################################################################
# legacy or fixed
FEE = 0.0005
MIN_BET_FOR_AUTO = 200000
MINOR_DELTA = 0  # sholud be multiple of 1000
###############################################################################






f = open("../upbit_api_key.txt", 'r')      
access_key = f.readline().rstrip()         
secret_key = f.readline().rstrip()         
f.close()                                  
coin = Coin('upbit',access_key,secret_key) 
token = '1604518349:AAFoH7TE40SaoegpSGBd5Oe4NsceqH78JTI'
bot = telegram.Bot(token=token)
def send_telegram(msg):
    # print(msg)
    try:
        bot.sendMessage(chat_id=170583240, text=msg)
    except:
        pass

print('KRW_DELTA:{:,}'.format(KRW_DELTA), 'BETTING:{:,}'.format(BETTING))

bid_prices={}
bid_volume={}
bid_gop={}  # 이가격대 bid낸 횟수, 횟수가 오를수록 돈도 많이 건다
ask_prices={}
total_gain = 0
l = coin.get_live_orders('ETH', 'KRW')
for (oid, askbid, price, cnt, odt) in l:
    if askbid=='bid':
        pass
        # coin.cancel(oid)
    else:
        ask_prices[oid] = (int(float(price)), 0, 0)
# print('ask_prices:', ask_prices)

bAuto = False
if BETTING == 0:
    bAuto = True
    BETTING = max(MIN_BET_FOR_AUTO, int(coin.get_asset_info('KRW')['free'] / 10))
    print('auto BETTING start from: {:,} KRW'.format(BETTING))

while True:
    if bAuto:
        BETTING = max(MIN_BET_FOR_AUTO, coin.get_asset_info('KRW')['free'] / 10)
        # print('auto BETTING: {:,} KRW'.format(BETTING))
    BETTING = min(BETTING, MAX_BETTING)

    # 먼저 현재 KRW_DELTA간격에 놓여있는 bid-ask pair를 확인한다.
    cp = int(coin.get_price('ETH', 'KRW'))  # coin price
    bp = int(cp  / KRW_DELTA) * KRW_DELTA + MINOR_DELTA # bid price
    ap = bp + KRW_DELTA - MINOR_DELTA * 2  # ask price

    # check ask fill
    aps = copy.deepcopy(ask_prices)
    l = coin.get_live_orders('ETH', 'KRW')
    for (oid, askbid, price, cnt, odt) in l:
        if askbid=='ask' and oid in aps:
            del aps[oid]
    # 체결된 ask에 대해 gain기록
    for oid, (price, gain, krw) in aps.items():
        total_gain += gain
        if gain > 0:
            print(fg.green + '! ask filled({:,}), gain: {:.8f}({:,}KRW), '.
                format(int(float(price)), gain, krw, total_gain, int(total_gain*price)) + fg.li_yellow + 
                'total_gain:{:.8f}({:,}KRW)'.
                format(total_gain, int(float(total_gain*price)))+ fg.rs)
            send_telegram('[ETH] ask filled({:,}), gain: {:.8f}({:,}KRW), total_gain:{:.8f}({:,}KRW)'.
                format(int(float(price)), gain, krw, total_gain, int(total_gain*price), 
                total_gain, int(float(total_gain*price))))
        else:
            print(fg.green + '! prev ask filled({:,}), gain:? total_gain:?'. format(int(float(price))))
        del ask_prices[oid]
    if len(aps) > 0: continue
    
    # check bid fill
    bps = copy.deepcopy(bid_prices)
    l = coin.get_live_orders('ETH', 'KRW')
    for (oid, askbid, price, cnt, odt) in l:
        if askbid=='bid' and oid in bps:
            del bps[oid]

    # 체결된 bid에 대해 ask걸기 
    for oid, price in bps.items():
        ap = float(price) + KRW_DELTA - MINOR_DELTA * 2
        bet = price * bid_volume[oid] * (1.0 + FEE) / (1.0 - FEE)
        gain = bid_volume[oid] - bet / ap
        print(fg.green + '! bid filled({:,}). '.format(price)+fg.blue+
            'placing ask({:,}).. gain will be: {:.8f}({:,}KRW)'.
			format(int(ap), gain, int(gain * ap))+ fg.rs)
        aoid = coin.limit_sell('ETH', ap, bet / ap)
        ask_prices[aoid] = (ap, gain, int(gain * ap))
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
    if abs(cp - bp) > KRW_DELTA/4 and bfound is False and afound is False:
        free_krw = int(coin.get_asset_info('KRW')['free'])
        print('\n' + datetime.now().strftime("%m-%d %H:%M:%S") + fg.li_yellow + 
            ' free KRW:{:,},'.format(free_krw) + fg.rs + 'current ETH price:{:,} KRW, bid:{:,}, ask:{:,}'.
            format(cp, bp, ap) + fg.rs)
        bps = copy.deepcopy(bid_prices)
        for oid, price in bps.items():
            if price <= bp:
                coin.cancel(oid)
                del bid_prices[oid]

        if bp not in  bid_gop: bid_gop[bp] = 1
        bid_gop[bp] = max(1, bid_gop[bp])
        bid_gop[bp] = min(5, bid_gop[bp])

        bet = BETTING * bid_gop[bp] / (1.0 + FEE)
        oid = coin.limit_buy('ETH', bp, bet / bp)
        while oid == -1:
            bid_gop[bp] /= 2
            if bid_gop[bp] < 0.1:
                print('!!! no money!. will have 30 secs break..')
                bid_gop[bp] = 1
                time.sleep(30)
                break
            bet = BETTING * bid_gop[bp] / (1.0 + FEE)
            oid = coin.limit_buy('ETH', bp, bet / bp)
            time.sleep(2)
        if oid != -1:
            bid_prices[oid] = bp
            bid_volume[oid] = bet / bp
            print(fg.red + '! bid placed({:,}), bet:{:,}KRW, bid_gop:{}, bid_prices:{}'.
                format(bp, int(bet), bid_gop[bp], list(bid_prices.values())) + fg.rs)





















