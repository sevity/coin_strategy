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

# 설명 ########################################################################
# BTC개수를 늘리는걸 최우선으로 하여, KRW로 bid후 ask하는 전략
# param #######################################################################
KRW_DELTA = 1000000  # 이걸 기준으로 촘촘하게 주문을 낸다.
# BETTING = 10000    # 초기버전은 고정배팅으로 가보자
BETTING = 8000000  # AUTO if 0
MAX_BETTING = 8000000
###############################################################################
# legacy or fixed
FEE = 0.0005
MIN_BET_FOR_AUTO = 200000
MINOR_DELTA = 0  # sholud be multiple of 1000
TIME_INTERVAL = 60 * 10  # 60 min.
###############################################################################


parser = argparse.ArgumentParser(description='btc coin strategy')
parser.add_argument('--verbose', '-v', required=False, action='store_true', help='print debug messages.')
parser.add_argument('--betting', '-b', required=False, default=BETTING, help='betting BTC amount a time')
parser.add_argument('--krw_delta', '-d', required=False, default=KRW_DELTA, help='KRW Delta')
parser.add_argument('--reverse', '-r', required=False, action='store_true', help='이 옵션주면 하방봇이된다.')
args = parser.parse_args()
VERBOSE = args.verbose
if VERBOSE: print('verbose option is ON!')
BETTING = int(args.betting)
KRW_DELTA = int(args.krw_delta)
REVERSE = args.reverse
if REVERSE: print('reverse option is ON!')


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
def fsame(a, b, diff=0.0001):  # default: 0.01%이내로 같으면 true 리턴
    a = float(a)
    b = float(b)
    if abs(a-b)<diff:
        return True
    return False

print('KRW_DELTA:{:,}'.format(KRW_DELTA), 'BETTING:{:,}'.format(BETTING))

total_gain = 0

#l = coin.get_live_orders_ext('BTC', 'KRW')
#for (oid, askbid, price, order_cnt, remain_cnt, odt) in l:
#    if askbid=='bid':
#        if price % 100000 != 0: continue  # btc_regulate에서 건건 취소하지 않는다.
#        if fsame(order_cnt, remain_cnt):
#            r = coin.cancel(oid)
#    else:
#        ask_prices[oid] = (int(float(price)), 0, 0)
# print('ask_prices:', ask_prices)


def get_filled_list(askbid):
    # check fill
    if REVERSE:
        orders = first_orders if askbid=='ask' else second_orders
    else:
        orders = first_orders if askbid=='bid' else second_orders

    ps = copy.deepcopy(orders)
    l = coin.get_live_orders('BTC', 'KRW')
    for (oid, _askbid, price, cnt, odt) in l:
        if askbid==askbid and oid in ps:
            del ps[oid]
    return ps

first_orders = {}
second_orders = {}
#####################################
bAuto = False
if BETTING == 0:
    bAuto = True
    BETTING = max(MIN_BET_FOR_AUTO, int(coin.get_asset_info('KRW')['free'] / 10))
    print('auto BETTING start from: {:,} KRW'.format(BETTING))
pbt = -1  # previous bid time
while True:
    if bAuto:
        BETTING = max(MIN_BET_FOR_AUTO, coin.get_asset_info('KRW')['free'] / 10)
        # print('auto BETTING: {:,} KRW'.format(BETTING))
    BETTING = min(BETTING, MAX_BETTING)

    # 먼저 현재 KRW_DELTA간격에 놓여있는 bid-ask pair를 확인한다.
    cp = int(coin.get_price('BTC', 'KRW'))  # coin price
    bp = int(cp  / KRW_DELTA) * KRW_DELTA + MINOR_DELTA # bid price
    ap = bp + KRW_DELTA - MINOR_DELTA * 2  # ask price

    # check second order fill
    ps = get_filled_list('bid' if REVERSE else 'ask')
    # 체결된 ask에 대해 gain기록
    for oid, (askbid, price, volume, gain, krw) in ps.items():
        total_gain += gain
        if REVERSE:
            if gain > 0:
                print(bg.da_red+fg.white + '! bid filled({:,}).'.format(int(float(price)))
                    +bg.blue+fg.black+
                    ', gain: {:.8f}({:,}KRW).'.
                    format(gain, krw, total_gain, int(total_gain*price))+bg.li_yellow+fg.black + 
                    'total_gain:{:.8f}({:,}KRW)'.
                    format(total_gain, int(float(total_gain*price)))+ bg.rs+fg.rs)
                send_telegram('[BTC] bid filled({:,}), gain: {:.8f}({:,}KRW), total_gain:{:.8f}({:,}KRW)'.
                    format(int(float(price)), gain, krw, total_gain, int(total_gain*price), 
                    total_gain, int(float(total_gain*price))))
            else:
                print(bg.da_red + fg.white + '! prev bid filled({:,}), gain:? total_gain:?'.
                    format(int(float(price))) + bg.rs + fg.rs)
        else:
            if gain > 0:
                print(bg.da_blue+fg.white + '! ask filled({:,}).'.format(int(float(price)))
                    +bg.blue+fg.black+
                    ', gain: {:.8f}({:,}KRW).'.
                    format(gain, krw, total_gain, int(total_gain*price))+bg.li_yellow+fg.black + 
                    'total_gain:{:.8f}({:,}KRW)'.
                    format(total_gain, int(float(total_gain*price)))+ bg.rs+fg.rs)
                send_telegram('[BTC] ask filled({:,}), gain: {:.8f}({:,}KRW), total_gain:{:.8f}({:,}KRW)'.
                    format(int(float(price)), gain, krw, total_gain, int(total_gain*price), 
                    total_gain, int(float(total_gain*price))))
            else:
                print(bg.da_blue + fg.white + '! prev ask filled({:,}), gain:? total_gain:?'.
                    format(int(float(price))) + bg.rs + fg.rs)
        del second_orders[oid]
    if len(ps) > 0: continue

    
    # check first order fill
    ps = get_filled_list('ask' if REVERSE else 'bid')
    # 체결된 bid에 대해 ask걸기 
    for oid, (askbid, price, volume) in ps.items():
        if REVERSE:
            bp = float(price) - KRW_DELTA + MINOR_DELTA * 2
            bet = price * volume / (1.0 + FEE) * (1.0 - FEE)
            #bet = bet * (1.0 - FEE)
            gain = bet / bp - volume
            print(bg.da_blue + fg.white + '! ask filled({:,}).'.format(price)+bg.rs+fg.red+
                ' placing bid({:,}).. gain will be: {:.8f}({:,}KRW)'.
                            format(int(bp), gain, int(gain * bp)) + bg.rs+fg.rs)
            boid = -1
            while boid == -1:
                boid = coin.limit_buy('BTC', bp, bet / bp, True, True)

            # askbid, price, volume, gain, gain_krw
            second_orders[boid] = ('bid', bp, bet / bp, gain, int(gain * bp))  
        else:
            ap = float(price) + KRW_DELTA - MINOR_DELTA * 2
            bet = price * volume * (1.0 + FEE) / (1.0 - FEE)
            gain = volume - bet / ap
            print(bg.da_red + fg.white + '! bid filled({:,}).'.format(price)+bg.rs+fg.blue+
                ' placing ask({:,}).. gain will be: {:.8f}({:,}KRW)'.
                            format(int(ap), gain, int(gain * ap)) + bg.rs+fg.rs)
            aoid = -1
            while aoid == -1:
                aoid = coin.limit_sell('BTC', ap, bet / ap, True, True) 

            # askbid, price, volume, gain, gain_krw
            second_orders[aoid] = ('ask', ap, bet / ap, gain, int(gain * ap))  

        del first_orders[oid]

        # time.sleep(5)
    if len(ps) > 0: continue

    bfound = False
    afound = False
    l = coin.get_live_orders('BTC', 'KRW')
    for (oid, askbid, price, cnt, odt) in l:
        if askbid=='bid' and int(float(price)) == bp:
            bfound = True
        if askbid=='ask' and int(float(price)) == ap:
            afound = True
    # ask없는 bid에 대해 주문
    # bfound면 이미 bid place 상태라 다시 bid를 걸 필요가 없고.
    # afound면 이미 bid체결되고 ask기다리는 상태라 다시 bid할 필요가 없다

    # 사고 판후에 아래 c1이 없으면 너무 바로 다시 판가격에 사게된다. 그래서 둔 완화장치
    c1 = (abs(cp - bp) > KRW_DELTA/4) if REVERSE==False else (abs(ap-cp) > KRW_DELTA/4)  # condition 1
    # print(afound, bfound, ap, bp, c1)
    if c1 and bfound is False and afound is False:
        if REVERSE == False:
            free_krw = int(coin.get_asset_info('KRW')['free'])
            print('\n' + datetime.now().strftime("%m-%d %H:%M:%S") + fg.li_yellow + 
                ' free KRW:{:,},'.format(free_krw) + fg.rs + 'current BTC price:{:,} KRW, bid:{:,}, ask:{:,}'.
                format(cp, bp, ap) + fg.rs)

        else:
            free_btc = coin.get_asset_info('BTC')['free']
            print('\n' + datetime.now().strftime("%m-%d %H:%M:%S") + fg.li_yellow + 
                ' free BTC:{:.8f},'.format(free_btc) + fg.rs + 'current BTC price:{:,} KRW, bid:{:,}, ask:{:,}'.
                format(cp, bp, ap) + fg.rs)

        # 과거 first  주문중 부분체결된걸 제외하고는 지워준다.
        # 이때 싹다 지우는게 아니라, 딥바잉된것만 지워준다.
        ps = get_filled_list('ask' if REVERSE else 'bid')
        for oid, (askbid, price, volume) in ps.items():
            if (REVERSE and price > ap) or (REVERSE == False and price < bp):
                l = coin.get_live_orders_ext('BTC', 'KRW')
                for (oid_, askbid, price, order_cnt, remain_cnt, odt) in l:
                    if oid_ == oid:
                        if fsame(order_cnt, remain_cnt):
                        # if fsame(order_cnt, volue):
                            r = coin.cancel(oid)
                            if r.ok: del first_orders[oid]
                            break


        bet = BETTING * (1.0 + FEE) if REVERSE else BETTING / (1.0 + FEE)
        ct = datetime.now()
        if pbt == -1:
            td = TIME_INTERVAL
            pbt = datetime.now() - timedelta(seconds=td)
        else:
            td = min(TIME_INTERVAL * 2, (ct - pbt).seconds)  # time diff
        br = min(1.0, td / TIME_INTERVAL)  # bet ratio
        nb = bet * br  # new bet
        print('time diff: {}s, bet ratio: {}, bet:{}, new bet:{}'.format(td, br, bet, nb))
        # bet = max(500000 if REVERSE==False else 40000, nb)  # min bet for BTC market in UPBIT
        pbp = bp
        # pbt = datetime.now()

        if REVERSE:
            oid = coin.limit_sell('BTC', ap, bet / ap, True, True)
            if oid == -1:
                print('!!! no BTC!({:,}KRW)'.format(int(bet)))
                pbt += timedelta(seconds=td/2)
                # time.sleep(60)
            else:
                first_orders[oid] = ('ask', ap, bet / ap)  # askbid, price, volume
                print(fg.blue + '! ask placed({:,}), bet:{:,}KRW, first_orders:{}'.
                    format(ap, int(bet), list(first_orders.values())) + fg.rs)
        else:
            oid = coin.limit_buy('BTC', bp, bet / bp, True, True)
            if oid == -1:
                print('!!! no money!({:,}KRW)'.format(int(bet)))
                pbt += timedelta(seconds=td/2)
                # time.sleep(60)
            else:
                first_orders[oid] = ('bid', bp, bet / bp)  # askbid, price, volume
                print(fg.red + '! bid placed({:,}), bet:{:,}KRW, first_orders:{}'.
                    format(bp, int(bet), list(first_orders.values())) + fg.rs)
        pbt = datetime.now()


















