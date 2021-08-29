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
def save_obj(obj, name):
    Path("../obj").mkdir(parents=True, exist_ok=True)
    with open('../obj/coin_btc_'+ name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name):
    with open('../obj/coin_btc_' + name + '.pkl', 'rb') as f:
        return pickle.load(f)

# 설명 ########################################################################
# BTC개수를 늘리는걸 최우선으로 하여, BTC로 bid후 ask하는 전략
# param #######################################################################
DELTA = { # 이걸 기준으로 촘촘하게 주문을 낸다.
    'ETH':0.00160000, # 80000 
    'BFC':0.00000120,  # 5
    'ZRX':0.00000120,  
    'LRC':0.00000150,  
    'OBSR':0.00000002,  # 
    'TRX':0.00000008,  # 5
    'CHZ':0.00000100,  # 30
    'GLM':0.00000030,  # 
    'MED':0.00000030,  # 5
    'SNT':0.00000080,  # 20
    'GOM2':0.00000005,
    'XRP':0.00000240,  # 80
    'XLM':0.00000040,  # 40
    'PUNDIX':0.00000150,
    'EOS':0.00001600,  # 800
    'OMG':0.00001600,  # 800
    'ADA':0.00000200,  # 50
    'LOOM':0.00000030, # 10
    'CRO':0.00000020,  # 10
    'ENJ':0.00000150,  # 100
    'MANA':0.00000240,  # 80
    'DOGE':0.00000090,  # 15
    'VET':0.00000010,  # 10
    'PLA':0.00000200,  # 100
    'IGNIS':0.00000020,
    'LINK' :0.00002000,  # 2000
    'CRV' :0.00000200,  
    'UNI' :0.00002000,
    'LTC' :0.00020000,  # 10000
    'STX' :0.00000100,  # 100
    'BAT' :0.00000200,  # 100
    'SYS' :0.00000200,  # 100
    'COMP' :0.00080000, # 40000
    'BTT' :0.00000001,
    'DENT' :0.00000002,
    'NCASH' :0.00000002,
    'FLOW' :0.00002000,
    'PICA' :0.00000010,  # 20
    'XEM' :0.00000040,  # 40
    'STORJ' :0.00000200,  # 250
    'GRT' :0.00000100,  # 100
    'DOT' :0.00006000,  # 2000
    'REP' :0.00002000,  
    'ETC' :0.00018000,  # 3000
    'RVN' :0.00000010,  
    'FIL' :0.00020000,  # 10000
    'BSV' :0.00030000,  
    'BCH' :0.00200000, # 50000 
    'WAVE' :0.00005000,  
    'MKR' :0.00300000,  
    'SRM' :0.00001000,  # 500
    'XTZ' :0.00001000,  # 500
    'SXP' :0.00000200,  
    'ALGO' :0.00000100,    # 50
    'PSG' :0.00008000,    # 2000
    'ATOM' :0.00006000,  # 1500
    'SAND' :0.00000050,  
    'POWR' :0.00000030,  
    'NEAR' :0.00000500,  
    }
BETTING = 0.007    # 초기버전은 고정배팅으로 가보자(200만원 정도 된다)
# BETTING = 0  # AUTO
###############################################################################
# legacy or fixed
FEE = 0.0025
MIN_BET_FOR_AUTO = 0.0006
MINOR_DELTA = 0  # sholud be multiple of 1000
BID_OFFSET = -0.1  # -0.1 means 10%(of BTC_DELTA) lower price
ASK_OFFSET = 0.1

parser = argparse.ArgumentParser(description='btc coin increase strategy for BTC market')
parser.add_argument('--ticker', '-t', required=True, help='coin name ex)ETH')
parser.add_argument('--betting', '-b', required=False, default=BETTING, help='betting BTC amount a time')
parser.add_argument('--collect', '-c', required=False, action='store_true', help='cancel parital pending bid to gather token')
parser.add_argument('--buying_start', '-bs', required=False, action='store_true', help='first bid will not be asked')
args = parser.parse_args()
TICKER = args.ticker.upper()
BETTING = float(args.betting)
COLLECT = args.collect  # True or False
if COLLECT: print('collect token option is ON!')
BUYING_START = args.buying_start
if BUYING_START: print('buying start option is ON!')
BTC_DELTA = float(DELTA[TICKER])
TIME_INTERVAL = 20 * 60  # 30 min.
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

print('BTC_DELTA:{:.8f}'.format(BTC_DELTA), 'BETTING:{:.4f}'.format(BETTING))


try:
    bid_prices=load_obj(TICKER+'_bid_prices')
    bid_volume=load_obj(TICKER+'_bid_volume')
    ask_prices=load_obj(TICKER+'_ask_prices')
    total_gain=load_obj(TICKER+'_total_gain')
except:
    bid_prices={}
    bid_volume={}
    ask_prices={}
    total_gain = 0
btckrw = coin.get_price('BTC', 'KRW')
print('total_gain:{:.8f}BTC({:,}KRW)'.format(total_gain, (int(total_gain*btckrw))))
bid_gop={}  # 이가격대 bid낸 횟수, 횟수가 오를수록 돈도 많이 건다
l = coin.get_live_orders_ext(TICKER, 'BTC')
# print(':l', l)
for (oid, askbid, price, order_cnt, remain_cnt, odt) in l:
    if askbid=='bid':
        if oid in bid_prices: continue
        if fsame(order_cnt, remain_cnt):
            r = coin.cancel(oid)
        else:
            # TODO: bid부분체결 수량만큼 ask잡아줌
            r = coin.cancel(oid)  # 지금은 임시로 collect처리함
            bp = price
            bet = bp * (order_cnt - remain_cnt)
            cp = float(coin.get_price(TICKER, 'BTC'))  # coin price
            msg = '[{}-BTC] {:.2f}{} collected_0!({:.8f}BTC, {:,}KRW) price:{:.8f}BTC'.format(
                    TICKER, bet/bp, TICKER, bet/bp*cp, int(bet/bp*cp*btckrw), bp)
            send_telegram(msg)
            print(bg.magenta + msg + bg.rs)
    else:
        if oid in ask_prices: continue
        ask_prices[oid] = ((float(price)), 0, 0)
print('prev ask_prices:', ask_prices)

bAuto = False
if BETTING == 0:
    bAuto = True
    BETTING = max(MIN_BET_FOR_AUTO, (coin.get_asset_info('BTC')['free'] / 20))
    print('auto BETTING start from: {:.8f} BTC'.format(BETTING))
pmsg = ""
pbp = -1  # previous bid price
pbt = -1  # previous bid time
while True:
    if bAuto:
        BETTING = max(MIN_BET_FOR_AUTO, coin.get_asset_info('BTC')['free'] / 20)

    # 먼저 현재 BTC_DELTA간격에 놓여있는 bid-ask pair를 확인한다.
    cp = float(coin.get_price(TICKER, 'BTC'))  # coin price
    bp = int(cp  / BTC_DELTA) * BTC_DELTA + MINOR_DELTA + BID_OFFSET * BTC_DELTA # bid price
    ap = bp + BTC_DELTA - MINOR_DELTA * 2 + (ASK_OFFSET - BID_OFFSET) * BTC_DELTA # ask price
    btckrw = coin.get_price('BTC', 'KRW')

    # check ask fill
    aps = copy.deepcopy(ask_prices)
    l = coin.get_live_orders(TICKER, 'BTC')
    for (oid, askbid, price, cnt, odt) in l:
        if askbid=='ask' and oid in aps:
            del aps[oid]
    # 체결된 ask에 대해 gain기록
    for oid, (price, gain, btc) in aps.items():
        total_gain += gain
        if gain > 0:
            print(bg.da_blue+fg.white + '! ask filled({:.8f}BTC).'.format(float(price))
                +bg.blue+fg.black+
                ' gain: {:.8f}BTC({:,}KRW), '.
                format(gain, int(gain*btckrw),total_gain,int(total_gain*btckrw))+bg.li_yellow+fg.black+
                'total_gain:{:.8f}BTC({:,}KRW)'.
                format(total_gain, (int(total_gain*btckrw)))+ bg.rs+fg.rs)
            send_telegram('[{}-BTC] ask filled({:.8f}BTC), gain: {:.8f}BTC({:,}KRW), total_gain:{:.8f}BTC({:,}KRW)'.
                format(TICKER, (float(price)), gain, int(gain*btckrw), total_gain, int(total_gain*btckrw), 
                total_gain, (int(total_gain*btckrw))))
        else:
            print(bg.da_blue+fg.white + '! prev ask filled({:.8f}BTC).'.format(float(price))+bg.blue+
                'gain:? total_gain:?'+bg.rs+fg.rs)
            send_telegram('[{}-BTC] ask filled({:.8f}BTC), gain:?, total_gain:?)'.
                format(TICKER, float(price)))
        del ask_prices[oid]
    save_obj(ask_prices, TICKER+'_ask_prices')
    save_obj(total_gain, TICKER+'_total_gain')
    if len(aps) > 0: 
        # print('aa')
        continue
    
    # check bid fill
    bps = copy.deepcopy(bid_prices)
    l = coin.get_live_orders(TICKER, 'BTC')
    for (oid, askbid, price, cnt, odt) in l:
        if askbid=='bid' and oid in bps:
            del bps[oid]

    # 체결된 bid에 대해 ask걸기 
    for oid, price in bps.items():
        if BUYING_START is True:
            # BUYING_START = False  # temp
            bp = price
            bet = bp*bid_volume[oid]
            msg = '[{}-BTC] {:.2f}{} collected_bs!({:.8f}BTC, {:,}KRW) price:{:.8f}BTC'.format(
                    TICKER, bet/bp, TICKER, bet/bp*cp, int(bet/bp*cp*btckrw), bp)
            send_telegram(msg)
            print(bg.magenta + msg + bg.rs)
            ap = bp * 2
        else:
            ap = float(price) + BTC_DELTA - MINOR_DELTA * 2 + (ASK_OFFSET-BID_OFFSET) * BTC_DELTA

        gain = ap * bid_volume[oid] * (1.0 - FEE) - price * bid_volume[oid] * (1.0 + FEE)
        print(bg.da_red + fg.white + '! bid filled({:.8f}BTC).'.format(price)+bg.rs+fg.blue+
            ' placing ask({:.8f}).. gain will be: {:.8f}BTC({:,}KRW)'.
                        format((ap), gain, int(gain * btckrw))+ fg.rs + bg.rs)
        aoid = coin.limit_sell_btc(TICKER, ap, bid_volume[oid], True, True)
        while aoid == -1:
            aoid = coin.limit_sell_btc(TICKER, ap, bid_volume[oid], True, True)
        ask_prices[aoid] = (ap, gain, (gain * ap))

        del bid_prices[oid]
        #if bid_gop[price] < 1: bid_gop[price] *= 2
        #else: bid_gop[price] += 1
        # time.sleep(5)
    save_obj(bid_prices, TICKER+'_bid_prices')
    save_obj(ask_prices, TICKER+'_ask_prices')
    if len(bps) > 0:
        # print('bb')
        continue



    bfound = False
    afound = False
    for (oid, askbid, price, cnt, odt) in l:
        if askbid=='bid' and fsame(price, bp):
            bfound = True
        if askbid=='ask' and fsame(price, ap):
            afound = True
    msg = 'bp:{:.8f}, ap:{:.8f}, cp:{:.8f}, bfound:{}, afound:{}, cp-bp({:.8f})>{:.8f}:{}'. format(
            bp, ap, cp, bfound, afound, abs(cp-bp), BTC_DELTA/4, abs(cp-bp)>BTC_DELTA/4)
    if pmsg != msg: print(msg)
    pmsg = msg
    # ask없는 bid에 대해 주문
    if abs(cp - bp) > BTC_DELTA/4 and bfound is False and afound is False:
        free_btc = (coin.get_asset_info('BTC')['free'])
        print('\n' + datetime.now().strftime("%m-%d %H:%M:%S") + fg.li_yellow + 
            ' free BTC:{:.8f},'.format(free_btc)+fg.rs+'current {} price:{:.8f}BTC, bid:{:.8f}, ask:{:.8f}'.
            format(TICKER, cp, bp, ap) + fg.rs)
        bps = copy.deepcopy(bid_prices)
        for oid, price in bps.items():
            os = coin.get_order_state(oid)
            if os == 'ack':
                r = coin.cancel(oid)
                if r.ok: del bid_prices[oid]
            else:
                if COLLECT is True:
                    l = coin.get_live_orders_ext(TICKER, 'BTC')
                    for (oid_, askbid, price, order_cnt, remain_cnt, odt) in l:
                        fc = order_cnt - remain_cnt  # filled cnt
                        if oid_ == oid and fc > 0:
                            msg = '[{}-BTC] {:.2f}{} collected_c!({:.8f}BTC, {:,}KRW) price:{:.8f}BTC, {}'.format(
                                    TICKER, fc, TICKER, fc*cp, int(fc*cp*btckrw), price, odt)
                            send_telegram(msg)
                            print(bg.green + msg + bg.rs)
                    r = coin.cancel(oid)
                    if r.ok: del bid_prices[oid]

        save_obj(bid_prices, TICKER+'_bid_prices')
            # if price < bp:
            # l = coin.get_live_orders_ext(TICKER, 'BTC')
            # for (oid_, askbid, price, order_cnt, remain_cnt, odt) in l:
            #    if oid_ == oid:
            #        if fsame(order_cnt, remain_cnt):  # 부분체결이 없는것만 골라서 취소해준다는거
            #            r = coin.cancel(oid)
            #            if r.ok: del bid_prices[oid]

        if bp not in bid_gop: bid_gop[bp] = 1
        bid_gop[bp] = max(1, bid_gop[bp])
        bid_gop[bp] = min(1, bid_gop[bp])

        bet = BETTING * bid_gop[bp] / (1.0 + FEE)
        ct = datetime.now()
        if pbt == -1:
            td = TIME_INTERVAL
            pbt = datetime.now() - timedelta(seconds=td)
        else:
            td = min(TIME_INTERVAL * 2, (ct - pbt).seconds)  # time diff
        br = min(1.0, td / TIME_INTERVAL)  # bet ratio
        # if bp < pbp:
        #     br = 1.0
        #     print('new bid price is lower than previous. so bet ratio will be 1.0(full bet)')
        nb = bet * br  # new bet
        print('time diff:{:,}s, bet ratio:{:.4f}, bet:{:.8f}BTC, new bet:{:.8f}BTC'.format(td, br, bet, nb))
        bet = max(bet / 10,  nb)  # set min bet according to bet size
        bet = max(MIN_BET_FOR_AUTO, bet)  # min bet for BTC market in UPBIT
        pbp = bp
        # pbt = datetime.now()
        oid = coin.limit_buy_btc(TICKER, bp, bet / bp, True, True)
        if oid == -1:
            print('!!! no money!({:.8}BTC)'.format(bet))
            pbt += timedelta(seconds=td/2)
            if fsame(bet, MIN_BET_FOR_AUTO):
                time.sleep(60)
            else:
                time.sleep(10)
        else:
            bid_prices[oid] = bp
            bid_volume[oid] = bet / bp
            save_obj(bid_prices, TICKER+'_bid_prices')
            save_obj(bid_volume, TICKER+'_bid_volume')

            print(fg.red + '! bid placed({:.8f}), bet:{:.8f}btc, bid_gop:{}, bid_prices:{}'.
                format(bp, (bet), bid_gop[bp], list(format_8f(bid_prices).values())) + fg.rs)
            # time.sleep(5)
            pbt = datetime.now()





















