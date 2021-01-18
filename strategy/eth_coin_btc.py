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
# BTC개수를 늘리는걸 최우선으로 하여, BTC로 bid후 ask하는 전략
# param #######################################################################
BTC_DELTA = 0.0004  # 이걸 기준으로 촘촘하게 주문을 낸다.
BETTING = 0.0300    # 초기버전은 고정배팅으로 가보자
# BETTING = 0  # AUTO
###############################################################################
# legacy or fixed
FEE = 0.0025
MIN_BET_FOR_AUTO = 0.0006
MINOR_DELTA = 0  # sholud be multiple of 1000
###############################################################################




f = open("../upbit_api_key.txt", 'r')      
access_key = f.readline().rstrip()         
secret_key = f.readline().rstrip()         
f.close()                                  
coin = Coin('upbit',access_key,secret_key) 
token = '1267448247:AAE7QjHpSijbtNS9_dnaLm6zfUGX3FhmF78'
bot = telegram.Bot(token=token)
def send_telegram(msg):
    # print(msg)
    try:
        bot.sendMessage(chat_id=170583240, text=msg)
    except:
        pass
def fsame(a, b, diff=0.00000001):  # default: 0.01%이내로 같으면 true 리턴
    a = float(a)
    b = float(b)
    if abs(a-b)<diff:
        return True
    return False

print('BTC_DELTA:{:,}'.format(BTC_DELTA), 'BETTING:{:,}'.format(BETTING))

bid_prices={}
bid_volume={}
bid_gop={}  # 이가격대 bid낸 횟수, 횟수가 오를수록 돈도 많이 건다
ask_prices={}
total_gain = 0
l = coin.get_live_orders('ETH', 'BTC')
for (oid, askbid, price, cnt, odt) in l:
    if askbid=='bid':
        coin.cancel(oid)
    else:
        ask_prices[oid] = ((float(price)), 0, 0)
# print('ask_prices:', ask_prices)

bAuto = False
if BETTING == 0:
    bAuto = True
    BETTING = max(MIN_BET_FOR_AUTO, (coin.get_asset_info('BTC')['free'] / 20))
    print('auto BETTING start from: {:.8f} BTC'.format(BETTING))
pmsg = ""
while True:
    if bAuto:
        BETTING = max(MIN_BET_FOR_AUTO, coin.get_asset_info('BTC')['free'] / 20)

    # 먼저 현재 BTC_DELTA간격에 놓여있는 bid-ask pair를 확인한다.
    cp = float(coin.get_price('ETH', 'BTC'))  # coin price
    bp = int(cp  / BTC_DELTA) * BTC_DELTA + MINOR_DELTA # bid price
    ap = bp + BTC_DELTA - MINOR_DELTA * 2  # ask price
    bp = round(bp, len(str(BTC_DELTA))-2)
    ap = round(ap, len(str(BTC_DELTA))-2)
    # print(cp, bp, ap)
    btckrw = coin.get_price('BTC', 'KRW')

    # check ask fill
    aps = copy.deepcopy(ask_prices)
    l = coin.get_live_orders('ETH', 'BTC')
    for (oid, askbid, price, cnt, odt) in l:
        if askbid=='ask' and oid in aps:
            del aps[oid]
    # 체결된 ask에 대해 gain기록
    for oid, (price, gain, btc) in aps.items():
        total_gain += gain
        if gain > 0:
            print(fg.green + '! ask filled({:,}), gain: {:.8f}BTC({:,}KRW), '.
                format(float(price), gain, int(gain*btckrw),total_gain,int(total_gain*btckrw)) + fg.li_yellow + 
                'total_gain:{:.8f}BTC({:,}KRW)'.
                format(total_gain, (int(total_gain*btckrw)))+ fg.rs)
            send_telegram('[ETH-BTC] ask filled({:,}), gain: {:.8f}BTC({:,}KRW), total_gain:{:.8f}BTC({:,}KRW)'.
                format((float(price)), gain, int(gain*btckrw), total_gain, int(total_gain*btckrw), 
                total_gain, (int(total_gain*btckrw))))
        else:
            print(fg.green + '! prev ask filled({:,}), gain:? total_gain:?'. format((float(price))))
        del ask_prices[oid]
    if len(aps) > 0: continue
    
    # check bid fill
    bps = copy.deepcopy(bid_prices)
    l = coin.get_live_orders('ETH', 'BTC')
    for (oid, askbid, price, cnt, odt) in l:
        if askbid=='bid' and oid in bps:
            del bps[oid]

    # 체결된 bid에 대해 ask걸기 
    for oid, price in bps.items():
        ap = float(price) + BTC_DELTA - MINOR_DELTA * 2
        ap = round(ap, len(str(BTC_DELTA))-2)
        # bet = price * bid_volume[oid] * (1.0 + FEE) / (1.0 - FEE)
        # gain = bid_volume[oid] - bet / ap
        gain = ap * bid_volume[oid] * (1.0 - FEE) - price * bid_volume[oid] * (1.0 + FEE)
        print(fg.green + '! bid filled({:.8f}BTC). '.format(price)+fg.blue+
            'placing ask({:.8f}).. gain will be: {:.8f}BTC({:,}KRW)'.
			format((ap), gain, int(gain * btckrw))+ fg.rs)
        aoid = coin.limit_sell_btc('ETH', ap, bid_volume[oid])
        ask_prices[aoid] = (ap, gain, (gain * ap))
        del bid_prices[oid]
        if bid_gop[price] < 1: bid_gop[price] *= 2
        else: bid_gop[price] += 1
        # time.sleep(5)
    if len(bps) > 0: continue



    bfound = False
    afound = False
    for (oid, askbid, price, cnt, odt) in l:
        if askbid=='bid' and fsame(price, bp):
            bfound = True
        if askbid=='ask' and fsame(price, ap):
            afound = True
    msg = 'bfound:{}, afound:{}'.format(bfound, afound)
    if pmsg != msg: print(msg)
    pmsg = msg
    # ask없는 bid에 대해 주문
    if abs(cp - bp) > BTC_DELTA/4 and bfound is False and afound is False:
        free_btc = (coin.get_asset_info('BTC')['free'])
        print('\n' + datetime.now().strftime("%m-%d %H:%M:%S") + fg.li_yellow + 
            ' free BTC:{:.8f},'.format(free_btc)+fg.rs+'current ETH price:{:.8f}BTC, bid:{:.8f}, ask:{:.8f}'.
            format(cp, bp, ap) + fg.rs)
        bps = copy.deepcopy(bid_prices)
        for oid, price in bps.items():
            if price <= bp:
                coin.cancel(oid)
                del bid_prices[oid]

        if bp not in  bid_gop: bid_gop[bp] = 1
        bid_gop[bp] = max(1, bid_gop[bp])

        bet = BETTING * bid_gop[bp] / (1.0 + FEE)
        oid = coin.limit_buy_btc('ETH', bp, bet / bp)
        while oid == -1:
            bid_gop[bp] /= 2
            if bid_gop[bp] < 0.1:
                print('!!! no money!. will have 30 secs break..')
                bid_gop[bp] = 1
                time.sleep(30)
            bet = BETTING * bid_gop[bp] / (1.0 + FEE)
            oid = coin.limit_buy('ETH', bp, bet / bp)
            time.sleep(2)
        bid_prices[oid] = bp
        bid_volume[oid] = bet / bp
        print(fg.red + '! bid placed({:.8f}), bet:{:.8f}BTC, bid_gop:{}, bid_prices:{}'.
            format(bp, (bet), bid_gop[bp], list(bid_prices.values())) + fg.rs)
        # time.sleep(5)





















