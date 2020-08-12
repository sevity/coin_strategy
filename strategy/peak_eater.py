import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from coin import *
import time
import math
import random
import copy
from datetime import datetime, timezone, timedelta

# param #######################################################################
total_tickers = [
    'MFT','IQ','CRE','MBL','STMX','SC','MED','EDR','TSHP','SPND','TT', 'IOST', 'AHT', 'QKC', 'ANKR', 'TFUEL', 'OST', 'PXL',
    'SRN', 'CHZ', 'GTO', 'ORBS', 'UPP', 'MOC', 'STPT', 'VET', 'TRX', 'ZIL', 'LOOM', 'IGNIS', 'TTC', 'SNT', 'CVC', 'POLY', 
    'BORA', 'HBAR', 'AERGO', 'DKA', 'WAXP', 'EMC2', 'XEM', 'GNT', 'MANA', 'ARDR', 'POWR', 'XLM', 'ELF', 'SOLVE', 'ADA', 'DMT',
    'ONG', 'STORJ', 'MLK', 'ENJ', 'GRS', 'STEEM', 'ADX', 'HIVE', 'BAT', 'VTC', 'XRP', 'THETA', 'IOTA', 'MTL', 'ICX', 'ZRX', 'ARK',
    'STRAT', 'KMD', 'ONT', 'SBD', 'LSK', 'KNC', 'OMG', 'GAS', 'WAVES', 'QTUM', 'EOS', 'XTZ', 'KAVA', 'ATOM', 'MCO', 'ETC',
    'LINK', 'BTG', 'NEO', 'DCR', 'REP', 'LTC', 'ETH',
    ]

# MANA는 틱갭이 너무 커서 UP해도 가격 같은경우가 생김
# KAVA는 가격변화가 심해서 peak eat가 아니라 다른 경우가 자주 생김
ban_tickers = []

FEE = 0.0005  # 0.05%
DOWN = 0.02   # 4%
UP   = 0.02
BETTING = 40000
COOL_TIME_ORDER = 60 * 2
COOL_TIME_HIT = 60 * 1.5
###############################################################################

for ticker in ban_tickers:
    total_tickers.remove(ticker)

f = open("../upbit_api_key.txt", 'r')
access_key = f.readline().rstrip()
secret_key = f.readline().rstrip()
f.close()
coin = Coin('upbit',access_key,secret_key)

total_gain = 0

def format_numbers(dict, rnd):
    for key, val in dict.items():
        dict[key] = '{:,}'.format(round(val, rnd) if rnd!=0 else int(val))

# return price multiple of ticksize
def tick_round(price):
    t = coin.get_tick_size(price)
    return int(price / t) * t

def on_hit_check_fill(ticker):
    print("check fill..", ticker)
    for i in range(int(COOL_TIME_HIT/10)):
        l = coin.get_live_orders(ticker, 'KRW')
        found = False
        for (oid, askbid, price, odt) in l:
            if askbid == 'bid':
                continue
            found = True
            if i == 0:
                print('waiting..', oid, askbid, '{:,}'.format(int(float(price))), odt)
            break
        if found == False:
            return True
        time.sleep(10)
    return False

def cancel_pending_bids():
    l = coin.get_live_orders('KRW')
    print('cancel pending bids..')
    for (ticker, oid, askbid, price, odt) in l:
        if ticker=='BTC' or askbid == 'ask':
            continue
        r = coin.cancel(oid)

def sell(pd):
    global total_gain
    for t,price in pd.items():
        print('selling..', t)
        bid_price = base_price_dict[t] - base_price_dict[t] * DOWN;bid_price = tick_round(bid_price)
        ask_price = price - price * UP;ask_price = tick_round(ask_price)
        bid_price_plus1 = tick_round(bid_price + bid_price*FEE*2 + coin.get_tick_size(bid_price))
        ask_price=max(ask_price, bid_price_plus1)
        oid = coin.limit_sell(t, ask_price, cnt_dict[t])
        r = on_hit_check_fill(t)
        gain = 0
        if r:
            gain = int(ask_price*cnt_dict[t]*(1.0-FEE) - bid_price*cnt_dict[t]*(1.0+FEE))
            print("!*!*!*!*!*!*!*!*!", t, "sold!", "buy:", bid_price, "sell:", ask_price,
                    "<< gain:{} >>".format(gain))
        else:
            coin.cancel(oid)
            f = 0
            while f == 0:
                ass = coin.get_asset_info(t)
                if 'free' not in ass:
                    break;
                f = ass['free']
            if f > 0:
                r = coin.market_sell(t, f)
                ask_amount = r['final_amount']
                gain = int(ask_amount - bid_price*cnt_dict[t]*(1.0+FEE))
                print('debug info..', 'ask_amount..', ask_amount, 'cnt..', cnt_dict[t])
                print(t, "limit order fail!", "buy:", bid_price, "market sell:", r['price'],
                        "<< gain:{} >>".format(gain))
        total_gain += gain

hit=False
while True:
    if hit or DOWN<0.01:
        DOWN=0.02
        hit = False
    #DOWN-=0.003
    DOWN *= (1-0.2)
    UP=DOWN*2/3
    print('-=-=-= new start.. DOWN:{:.3f}, UP:{:.3f}, total_gain KRW: {:,} =-=-=-'.format(DOWN, UP, int(total_gain)))
    cancel_pending_bids()

    krw = coin.get_asset_info('KRW')['free']
    cnt = len(total_tickers)
    BETTING = int((krw - 60000)/ cnt)
    print('free krw..', '{:,}'.format(krw), 'cnt..' , cnt, 'betting..', BETTING)
    tickers = []
    random.shuffle(total_tickers)
    for i in range(cnt):
        tickers.append(total_tickers[i])
    print('pick random tickers..', tickers)

    print('cancel pending ask orders and clear them with market sell')
    l = coin.get_live_orders('KRW')
    for (ticker, oid, askbid, price, odt) in l:
        if ticker == 'BTC' or askbid == 'bid':
            continue
        r = coin.cancel(oid)
    for ticker in total_tickers:
        ass = coin.get_asset_info(ticker)
        if 'free' in ass and ass['free'] > 0:
            coin.market_sell(ticker, ass['free'])
    base_price_dict = {}
    cnt_dict = {}
    bid_oid_dict = {}
    money = coin.get_asset_info('KRW')  # to float

    for ticker in tickers:
        cp = tick_round(coin.get_price(ticker, 'KRW'))
        print(datetime.now().strftime("%m-%d %H:%M:%S"), ticker, 'market mid price..', cp)

        bid_price = cp - cp * DOWN;bid_price = tick_round(bid_price)
        bid_cnt = float(BETTING) / bid_price
        if money['free'] > bid_price * bid_cnt :
            oid = coin.limit_buy(ticker, bid_price, bid_cnt)
            base_price_dict[ticker] = cp
            cnt_dict[ticker] = bid_cnt
            bid_oid_dict[ticker] = oid
        else:
            print('not enough KRW!')

    for i in range(int(COOL_TIME_ORDER/10)):
        l = coin.get_live_orders('KRW')

        pd = copy.deepcopy(base_price_dict)
        for (ticker, oid, askbid, price, odt) in l:
            if ticker not in pd or askbid == 'ask':
                continue
            del pd[ticker]

        if len(pd) > 0:
            print("-=-= {} hits... =-=-".format(len(pd)))
            hit = True
            print("cancel pending bids before selling..")
            for (ticker, oid, askbid, price, odt) in l:
                if ticker == 'BTC' or askbid == 'ask':
                    continue
                r = coin.cancel(oid)
            sell(pd)
            break

        print("orders alive...")
        for (ticker, oid, askbid, price, odt) in l:
            if ticker not in base_price_dict or askbid == 'ask':
                continue
            price = tick_round(coin.get_price(ticker, 'KRW'))
            change = round((price-base_price_dict[ticker])*100.0/base_price_dict[ticker],1)
            if change < -0.5:
                print(ticker, 'price from:{:,.2f} to:{:,.2f}, change:{}%'.format(base_price_dict[ticker], price, change))
        time.sleep(10)

    cancel_pending_bids()
    print("check parial fills...")
    pd = {}
    for t, oid in bid_oid_dict.items():
        r = coin.get_fill_order(oid)
        if 'final_amount' in r:
            cnt_dict[t]-=r['volume']
            cnt_dict[t] = round(cnt_dict[t], 5)
            if cnt_dict[t] > 0:
                pd[t] = base_price_dict[t]
    sell(pd)
