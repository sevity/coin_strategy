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

TICKER      = 'BTC'
DELTA       = 500000
BETTING     = 1000000

MAX_BETTING = 5000000

FEE           = 0.0005
MINOR_DELTA   = 0  # sholud be multiple of 1000
TIME_INTERVAL = 30 * 60  # 60 min.

parser = argparse.ArgumentParser(description='increase KRW')
parser.add_argument('--ticker', '-t', required=True, default=TICKER, help='coin name ex)ETH')
parser.add_argument('--delta', '-d', required=True, default=DELTA, help='delta KRW amount a time')
parser.add_argument('--betting', '-b', required=True, default=BETTING, help='betting KRW amount a time')

args = parser.parse_args()
TICKER = args.ticker.upper()
DELTA = int(args.delta)
BETTING = int(args.betting)

def fsame(a, b, diff=0.0001):
    a = float(a)
    b = float(b)
    if abs(a-b)<diff:
        return True
    return False

print('TICKER:{} DELTA:{:,} BETTING:{:,}'.format(TICKER, DELTA, BETTING))

f = open("../upbit_api_key.txt", 'r')
access_key = f.readline().rstrip()
secret_key = f.readline().rstrip()
f.close()

coin = Coin('upbit',access_key,secret_key)

bid_prices={}
bid_volume={}
bid_gop={}
ask_prices={}
total_gain = 0
l = coin.get_live_orders_ext(TICKER, 'KRW')
for (oid, askbid, price, order_cnt, remain_cnt, odt) in l:
    print(oid, askbid, price, order_cnt, remain_cnt, odt)
    if askbid=='bid':
        if price % 100000 != 0: continue
        if fsame(order_cnt, remain_cnt):
            r = coin.cancel(oid)
    else:
        ask_prices[oid] = (int(float(price)), 0, 0)

print('ask_prices:', ask_prices)

bid_cont = 0
cb = None  # circuit break
pbt = -1  # previous bid time
while True:
    BETTING = min(BETTING, MAX_BETTING)

    # make bid & ask price by current coin price
    cp = int(coin.get_price(TICKER, 'KRW'))  # coin price
    bp = int(cp / DELTA) * DELTA + MINOR_DELTA # bid price
    ap = bp + DELTA - MINOR_DELTA * 2  # ask price
    #print('coin price:', cp, 'bid price:', bp, 'ask price:', ap)

    # check ask fill
    aps = copy.deepcopy(ask_prices)
    l = coin.get_live_orders(TICKER, 'KRW')
    for (oid, askbid, price, cnt, odt) in l:
        if askbid=='ask' and oid in aps:
            del aps[oid]

    # record gain for ask done
    for oid, (price, gain, krw) in aps.items():
        #print(oid, (price, gain, krw))
        bid_cont -= 1
        total_gain += gain
        if gain > 0:
            print(bg.da_blue + fg.white +
                  '! ask filled({:,}).'.format(int(float(price)))
                  + bg.blue + fg.black +
                  ', gain: {:,}KRW.'.format(int(gain))
                  + bg.li_yellow + fg.black +
                  'total_gain:{:,}KRW'.format(int(total_gain))
                  + bg.rs + fg.rs)
        else:
            print(bg.da_blue + fg.white +
                  '! prev ask filled({:,}), gain:? total_gain:?'.format(int(float(price)))
                  + bg.rs + fg.rs)
        del ask_prices[oid]

    if len(aps) > 0:
        print('aps:{}'.format(aps))
        continue

    if cb is not None:
        print('cb:{}'.format(cb))
        if bid_cont <= 0 or (datetime.now() - cb).seconds > 60*60:
            cb = None
            bid_cont = 0
        continue

    #print('bid_prices:', bid_prices)
    # check bid fill
    bps = copy.deepcopy(bid_prices)
    l = coin.get_live_orders(TICKER, 'KRW')
    #print('get_live_orders:', l)
    for (oid, askbid, price, cnt, odt) in l:
        #print(oid, askbid, price, cnt, odt)
        if askbid=='bid' and oid in bps:
            del bps[oid]

    # make ask for bid done
    for oid, price in bps.items():
        bid_cont += 1

        ap = int(price) + DELTA - MINOR_DELTA * 2
        gain = ap * bid_volume[oid] * (1.0 - FEE) - price * bid_volume[oid] * (1.0 + FEE)
        #bet = price * bid_volume[oid] * (1.0 + FEE) / (1.0 - FEE)
        #gain = bid_volume[oid] - bet / ap
        print(bg.da_red + fg.white + '! bid filled({:,}).'.format(price)+bg.rs+fg.blue+
              ' placing ask({:,}).. gain will be: {:,}KRW'.format(int(ap), int(gain)) + bg.rs+fg.rs)
        aoid = coin.limit_sell(TICKER, ap, bid_volume[oid], True, True)
        #aoid = coin.limit_sell(TICKER, ap, bet / ap, True, True)
        print('{} = limit_sell({}, {:,}, {})'.format(aoid, TICKER, ap, bid_volume[oid]))
        while aoid == -1:
            aoid = coin.limit_sell(TICKER, ap, bid_volume[oid], True, True)
            print('{} = limit_sell({}, {:,}, {})'.format(aoid, TICKER, ap, bid_volume[oid]))
            #cnt = bet / ap
            #cnt = min(cnt, coin.get_asset_info(TICKER)['free'])
            #aoid = coin.limit_sell(TICKER, ap, cnt, True, True)
        ask_prices[aoid] = (ap, gain, int(gain * ap))
        del bid_prices[oid]
        if bid_gop[price] < 1: bid_gop[price] *= 2
        else: bid_gop[price] += 1
    if bid_cont >= 3:
        print('bid_cont:{}'.format(bid_cont))
        time.sleep(10)
        continue
        print(fg.red + 'circuit break!' + fg.rs)
        send_telegram('circuit break!')
        cb = datetime.now()
        bid_cont = 2
        continue
    if len(bps) > 0:
        print('bps:{}'.format(bps))
        continue

    bfound = False
    afound = False
    for (oid, askbid, price, cnt, odt) in l:
        #print(oid, askbid, price, cnt, odt)
        if askbid=='bid' and int(float(price)) == bp:
            bfound = True
        if askbid=='ask' and int(float(price)) == ap:
            afound = True
    # make bid for no-ask
    if abs(cp - bp) > DELTA/4 and bfound is False and afound is False:
        free_krw = int(coin.get_asset_info('KRW')['free'])
        print('\n' + datetime.now().strftime("%m-%d %H:%M:%S")
              + ' free KRW:{:,},'.format(free_krw)
              + 'current {} price:{:,} KRW, bid:{:,}, ask:{:,}'.format(TICKER, cp, bp, ap))
        bps = copy.deepcopy(bid_prices)
        for oid, price in bps.items():
            if price < bp:
                l = coin.get_live_orders_ext(TICKER, 'KRW')
                for (oid_, askbid, price, order_cnt, remain_cnt, odt) in l:
                    if oid_ == oid:
                        if fsame(order_cnt, remain_cnt):
                            r = coin.cancel(oid)
                            if r.ok: del bid_prices[oid]
                            break

        if bp not in  bid_gop: bid_gop[bp] = 1
        bid_gop[bp] = max(1, bid_gop[bp])
        bid_gop[bp] = min(1, bid_gop[bp])

        bet = BETTING * bid_gop[bp] / (1.0 + FEE)
        ct = datetime.now()
        if pbt == -1:
            td = TIME_INTERVAL
            pbt = datetime.now() - timedelta(seconds=td)
        else:
            td = min(TIME_INTERVAL * 2, (ct - pbt).seconds)  # time diff
        br = 1 #min(1.0, td / TIME_INTERVAL)  # bet ratio
        nb = bet * br  # new bet
        print('time diff: {}s, bet ratio: {}, bet:{}, new bet:{}'.format(td, br, bet, nb))
        bet = max(10000, nb)  # min bet for BTC market in UPBIT
        pbp = bp
        oid = coin.limit_buy(TICKER, bp, bet / bp, True, True)
        print('{} = limit_buy({}, {:,}, {})'.format(oid, TICKER, bp, bet / bp))
        if oid == -1:
            print('!!! no money!({:,}KRW)'.format(bet))
            pbt += timedelta(seconds=td/2)
        else:
            bid_prices[oid] = bp
            bid_volume[oid] = bet / bp
            print(fg.red + '! bid placed({:,}), bet:{:,}KRW, bid_gop:{}, bid_prices:{}'.
                format(bp, int(bet), bid_gop[bp], list(bid_prices.values())) + fg.rs)
            pbt = datetime.now()
