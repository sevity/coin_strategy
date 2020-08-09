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
    'LINK', 'BTG', 'NEO', 'DCR', 'REP', 'LTC', 
    ]

FEE = 0.0005  # 0.05%
DOWN = 0.01   # 2%
UP = 0.0005
BETTING = 50000
COOL_TIME_ORDER = 60 * 2
COOL_TIME_HIT = 60 * 1
###############################################################################

f = open("../upbit_api_key.txt", 'r')
access_key = f.readline().rstrip()
secret_key = f.readline().rstrip()
f.close()
coin = Coin('upbit',access_key,secret_key)
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

total_gain = 0
while True:
    print('-=-=-= new start.. total_gain: {:,} =-=-=-'.format(int(total_gain)))
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
            print("-=-= {} hits... =-=-".format(len(pd)))
            print("cancel pending bids before selling..")
            for (ticker, oid, askbid, price, odt) in l:
                if ticker == 'BTC' or askbid == 'ask':
                    continue
                r = coin.cancel(oid)

            for t,price in pd.items():
                print('selling..', t)
                ask_price = price - price * UP;ask_price = tick_round(ask_price)
                oid = coin.limit_sell(t, ask_price, cnt_dict[t])
                r = on_hit_check_fill(t)
                bid_price = price_dict[t] - price_dict[t] * DOWN;bid_price = tick_round(bid_price)
                gain = 0
                if r:
                    gain = int(ask_price*cnt_dict[t]*(1.0-FEE) - bid_price*cnt_dict[t]*(1.0+FEE))
                    print(ticker, "sold!", "buy:", bid_price, "sell:", ask_price,
                          "<< gain:{} >>".format(gain))
                else:
                    coin.cancel(oid)
                    f = 0
                    while f == 0:
                        ass = coin.get_asset_info(t)
                        f = ass['free']
                    ask_amount = coin.market_sell(t, ass['free'])
                    gain = int(ask_amount - bid_price*cnt_dict[t]*(1.0+FEE))
                    print(ticker, "limit order fail!", "buy:", bid_price, "market sell:", ask_price,
                          "<< gain:{} >>".format(gain))
                total_gain += gain

            break

        for (ticker, oid, askbid, price, odt) in l:
            if ticker not in price_dict or askbid == 'ask':
                continue
            price = tick_round(coin.get_price(ticker, 'KRW'))
            change = round((price-price_dict[ticker])*100.0/price_dict[ticker],1)
            if change < -0.5:
                print(ticker, 'price from:{:,.2f} to:{:,.2f}, change:{}%'.format(price_dict[ticker], price, change))
        time.sleep(10)

