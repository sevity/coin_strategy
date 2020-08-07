import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from coin import *
import time
import math
from datetime import datetime, timezone, timedelta

# param #######################################################################
tickers = ['MOC', 'ORBS', 'GTO', 'BORA', 'WAVES', 'EMC2', 'MTL', 'SC', 'SPND','CVC']
tick_sizes = [0.1, 0.1, 0.1, 0.1, 10, 0.1, 1, 0.01, 0.01, 0.1]
# tickers = ['RP']
FEE = 0.003
DOWN = 0.010
UP = 0.005
BETTING = 100000
COOL_TIME_ORDER = 60 * 2
COOL_TIME_HIT = 60 * 5
ASK_TIME = 60 * 5
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

print('cancel possible pending bid orders of previous run')
l = coin.get_live_orders('KRW')
for (ticker, oid, askbid, price, odt) in l:
    if ticker not in tickers or askbid == 'ask':
        continue
    r = coin.cancel(oid)

while True:
    print('cancel pending ask orders and clear them with market sell')
    l = coin.get_live_orders('KRW')
    for (ticker, oid, askbid, price, odt) in l:
        if ticker not in tickers or askbid == 'bid':
            continue
        r = coin.cancel(oid)
    for ticker in tickers:
        ass = coin.get_asset_info(ticker)
        if 'free' in ass and ass['free'] > 0:
            coin.market_sell(ticker, ass['free'])

    z = dict(zip(tickers,  [-int(math.log(x, 10) + (-0.5 if x<1 else 0.5)) for x in tick_sizes]))
    price_dict = {}
    money = coin.get_asset_info('KRW')
    format_numbers(money, 0)
    print('KRW..', money)
    money = coin.get_asset_info('KRW')  # to float

    for ticker in tickers:
        cp = round(coin.get_price(ticker, 'KRW'), z[ticker])
        print(datetime.now().strftime("%m-%d %H:%M:%S"), ticker, 'price..', cp)

        bid_price = cp - cp * DOWN;bid_price = round(bid_price, z[ticker])
        bid_cnt = float(BETTING) / bid_price
        if money['free'] > bid_price * bid_cnt :
            oid = coin.limit_buy(ticker, bid_price, bid_cnt)
            price_dict[ticker] = cp
        else:
            print('not enough KRW!')

    time.sleep(COOL_TIME_ORDER)

    l = coin.get_live_orders('KRW')
    KST = timezone(timedelta(hours=9))
    print("{} orders alive...".format(len(l)))
    for (ticker, oid, askbid, price, odt) in l:
        if ticker not in price_dict or askbid == 'ask':
            continue
        now = datetime.now(KST)
        date_diff = (now-odt).days
        hour_diff = int(date_diff*24 + (now-odt).seconds/3600)
        price = round(coin.get_price(ticker, 'KRW'), z[ticker])
        print(ticker, 'price from..', price_dict[ticker], 'price now..', price, 
              'price change..', round((price-price_dict[ticker])*100.0/price_dict[ticker],1))
        del price_dict[ticker]
        r = coin.cancel(oid)
        print(r)

    if len(price_dict)>0:
        print("{} hits...".format(len(price_dict)))
        for ticker,price in price_dict.items():
            print('selling..', ticker)
            price = price_dict[ticker]
            ask_price = price - price * UP;ask_price = round(ask_price, z[ticker])
            oid = coin.limit_sell(ticker, ask_price, bid_cnt)
        time.sleep(COOL_TIME_HIT)
