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
    ('MFT', 0.01),
    ('IQ', 0.01),
    ('CRE', 0.01),
    ('MBL', 0.01),
    ('STMX', 0.01),
    ('SC', 0.01),
    ('MED', 0.01),
    ('EDR', 0.01),
    ('TSHP', 0.01),
    ('SPND', 0.01),
    ('TT', 0.01),
    ('IOST', 0.01),
    ('AHT', 0.01),
    ('QKC', 0.01),
    ('ANKR', 0.1),
    ('TFUEL', 0.1),
    ('OST', 0.1),
    ('PXL', 0.1),
    ('SRN', 0.1),
    ('CHZ', 0.1),
    ('GTO', 0.1),
    ('ORBS', 0.1),
    ('UPP', 0.1),
    ('MOC', 0.1),
    ('STPT', 0.1),
    ('VET', 0.1),
    ('TRX', 0.1),
    ('ZIL', 0.1),
    ('LOOM', 0.1),
    ('IGNIS', 0.1),
    ('TTC', 0.1),
    ('SNT', 0.1),
    ('CVC', 0.1),
    ('POLY', 0.1),
    ('BORA', 0.1),
    ('HBAR', 0.1),
    ('AERGO', 0.1),
    ('DKA', 0.1),
    ('WAXP', 0.1),
    ('EMC2', 0.1),
    ('XEM', 0.1),
    ('GNT', 0.1),
    ('MANA', 0.1),
    ('ARDR', 0.1),
    ]

FEE = 0.003
DOWN = 0.025  # 2%
UP = 0.015
BETTING = 100000
COOL_TIME_ORDER = 60 * 2
COOL_TIME_HIT = 60 * 20
###############################################################################

f = open("../upbit_api_key.txt", 'r')
access_key = f.readline().rstrip()
secret_key = f.readline().rstrip()
f.close()
coin = Coin('upbit',access_key,secret_key)

def format_numbers(dict, rnd):
    for key, val in dict.items():
        dict[key] = '{:,}'.format(round(val, rnd) if rnd!=0 else int(val))

# get fee and tick_size
#for ticker in tickers:
#    info = coin.get_info(ticker, 'KRW')
#    print(ticker, info)


while True:
    print('cancel pending bids..')
    l = coin.get_live_orders('KRW')
    for (ticker, oid, askbid, price, odt) in l:
        if ticker=='BTC' or askbid == 'ask':
            continue
        r = coin.cancel(oid)

    krw = coin.get_asset_info('KRW')['free']
    cnt = int(krw / BETTING *4 / 5)
    print('free krw..', '{:,}'.format(krw), 'cnt of tickers this time..', cnt)
    tickers = []
    tick_sizes = []
    random.shuffle(total_tickers)
    for i in range(cnt):
        tickers.append(total_tickers[i][0])
        tick_sizes.append(total_tickers[i][1])
    z = dict(zip(tickers,  [-int(math.log(x, 10) + (-0.5 if x<1 else 0.5)) for x in tick_sizes]))
    print('pick random tickers..', tickers)

    print('cancel pending ask orders and clear them with market sell')
    l = coin.get_live_orders('KRW')
    for (ticker, oid, askbid, price, odt) in l:
        if ticker == 'BTC' or askbid == 'bid':
            continue
        r = coin.cancel(oid)
    for ticker, tick_size in total_tickers:
        ass = coin.get_asset_info(ticker)
        if 'free' in ass and ass['free'] > 0:
            coin.market_sell(ticker, ass['free'])
    price_dict = {}
    cnt_dict = {}
    money = coin.get_asset_info('KRW')  # to float

    for ticker in tickers:
        cp = round(coin.get_price(ticker, 'KRW'), z[ticker])
        print(datetime.now().strftime("%m-%d %H:%M:%S"), ticker, 'price..', cp)

        bid_price = cp - cp * DOWN;bid_price = round(bid_price, z[ticker])
        bid_cnt = float(BETTING) / bid_price
        if money['free'] > bid_price * bid_cnt :
            oid = coin.limit_buy(ticker, bid_price, bid_cnt)
            price_dict[ticker] = cp
            cnt_dict[ticker] = bid_cnt
        else:
            print('not enough KRW!')

    for i in range(int(COOL_TIME_ORDER/10)):
        l = coin.get_live_orders('KRW')
        print("orders alive...")
        pd = copy.deepcopy(price_dict)
        for (ticker, oid, askbid, price, odt) in l:
            if ticker not in pd or askbid == 'ask':
                continue
            del pd[ticker]
        if len(pd) > 0:
            print("{} hits...".format(len(pd)))
            print("cancel pending bids..")
            for (ticker, oid, askbid, price, odt) in l:
                if ticker == 'BTC' or askbid == 'ask':
                    continue
                r = coin.cancel(oid)

            for ticker,price in pd.items():
                print('selling..', ticker)
                ask_price = price - price * UP;ask_price = round(ask_price, z[ticker])
                oid = coin.limit_sell(ticker, ask_price, cnt_dict[ticker])
            time.sleep(COOL_TIME_HIT)
            break

        for (ticker, oid, askbid, price, odt) in l:
            if ticker not in price_dict or askbid == 'ask':
                continue
            price = round(coin.get_price(ticker, 'KRW'), z[ticker])
            change = round((price-price_dict[ticker])*100.0/price_dict[ticker],1)
            if change < -0.5:
                print(ticker, 'price from..', price_dict[ticker], 'price now..', price, 'price change..', change)
        time.sleep(10)

