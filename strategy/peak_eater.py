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
    'ONG', 'STORJ', 'MLK', 'ENJ', 'GRS', 'STEEM', 'ADX', 'HIVE', 'BAT', 'VCT', 'XRP', 'THETA', 'IOTA', 'MTL', 'ICX', 'ZRX', 'ARK',
    'STRAT', 'KMD', 'ONT', 'SBD', 'LSK', 'KNC', 'OMG', 'GAS', 'WAVES', 'QTUM', 'EOS', 'XTZ', 'KAVA', 'ATOM', 'MCO', 'ETC',
    'LINK', 'BTG', 'NEO', 'DCR', 'REP', 'LTC', 
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

def get_tick_size(price):
    if price < 10: return 0.01
    if price < 100: return 0.1
    if price < 1000: return 1
    if price < 10000: return 5
    if price < 100000: return 10
    if price < 1000000: return 50
    return 1000 # BTC

# return price multiple of ticksize
def tick_round(price):
    t = get_tick_size(price)
    return int(price / t) * t

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
    price_dict = {}
    cnt_dict = {}
    money = coin.get_asset_info('KRW')  # to float

    for ticker in tickers:
        cp = tick_round(coin.get_price(ticker, 'KRW'))
        print(datetime.now().strftime("%m-%d %H:%M:%S"), ticker, 'price..', cp)

        bid_price = cp - cp * DOWN;bid_price = tick_round(bid_price)
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
                ask_price = price - price * UP;ask_price = tick_round(ask_price)
                oid = coin.limit_sell(ticker, ask_price, cnt_dict[ticker])
            time.sleep(COOL_TIME_HIT)
            break

        for (ticker, oid, askbid, price, odt) in l:
            if ticker not in price_dict or askbid == 'ask':
                continue
            price = tick_round(coin.get_price(ticker, 'KRW'))
            change = round((price-price_dict[ticker])*100.0/price_dict[ticker],1)
            if change < -0.5:
                print(ticker, 'price from..', price_dict[ticker], 'price now..', price, 'price change..', change)
        time.sleep(10)

