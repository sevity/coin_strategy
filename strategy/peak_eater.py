import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from coin import *
import time
from datetime import datetime, timezone, timedelta

# param #######################################################################
tickers = ['XRP', 'XLM', 'ADA', 'MLK', 'POWR', 'ONG', 'VTC', 'STEEM', 'ICX', 'HIVE']
# tickers = ['XRP']
FEE = 0.003
DOWN = 0.03
UP = 0.01
BETTING = 100000
COOL_TIME = 60 * 2
ASK_TIME = 60 * 30
###############################################################################

f = open("../upbit_api_key.txt", 'r')
access_key = f.readline().rstrip()
secret_key = f.readline().rstrip()
f.close()
coin = Coin('upbit',access_key,secret_key)

while True:
    price_dict = {}
    for ticker in tickers:
        a = coin.get_price(ticker, 'KRW')
        money = coin.get_asset_info('KRW')

        print('KRW..', money)
        print(datetime.now().strftime("%m-%d %H:%M:%S"), ticker, 'price..', 'upbit', '{:,}'.format(a))

        ask_price = a + a * DOWN;ask_price = round(ask_price, 0) # minimum 1 won
        bid_price = a - a * DOWN;bid_price = round(bid_price, 0) # minimum 1 won
        ask_cnt = float(BETTING) / ask_price 
        bid_cnt = float(BETTING) / bid_price
        if money['free'] > bid_price * bid_cnt :
            oid = coin.limit_buy(ticker, bid_price, bid_cnt)
            print("oid:", oid)
            price_dict[ticker] = bid_price
        else:
            print('not enough KRW!')

    time.sleep(COOL_TIME)

    l = coin.get_live_orders('KRW')
    KST = timezone(timedelta(hours=9))
    print("{} orders alive...".format(len(l)))
    for (ticker, oid, askbid, price, odt) in l:
        if ticker not in price_dict:
            continue
        now = datetime.now(KST)
        date_diff = (now-odt).days
        hour_diff = int(date_diff*24 + (now-odt).seconds/3600)
        price = coin.get_price(ticker, 'KRW')
        price = int(float(price))
        price_dict[ticker] = int(float(price_dict[ticker]))
        print(oid, askbid, '{:,}'.format(int(float(price))), odt, 'price change..', (price-price_dict[ticker])*100.0/price_dict[ticker])
        del price_dict[ticker]
        r = coin.cancel(oid)
        print(r)
    if len(price_dict)>0:
        print("{} hits...".format(len(price_dict)))
        for ticker,price in price_dict.items():
            print('selling..', ticker)
            ask_price = price + price * UP;ask_price = round(ask_price, 0) # minimum 1 won
            oid = coin.limit_sell(ticker, ask_price, bid_cnt)
            print("oid:", oid)
        time.sleep(ASK_TIME)
        l = coin.get_live_orders('KRW')
        assert len(l)==0
