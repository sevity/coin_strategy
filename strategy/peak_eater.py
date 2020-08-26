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

# param #######################################################################
total_tickers = [
    'MFT','IQ','CRE','MBL','STMX','SC','MED','EDR','TSHP','SPND','TT', 'IOST', 'AHT', 'QKC', 'ANKR', 'TFUEL', 'OST', 'PXL',
    'SRN', 'CHZ', 'GTO', 'ORBS', 'UPP', 'MOC', 'STPT', 'VET', 'TRX', 'ZIL', 'LOOM', 'IGNIS', 'TTC', 'SNT', 'CVC', 'POLY', 
    'BORA', 'HBAR', 'AERGO', 'DKA', 'WAXP', 'EMC2', 'XEM', 'GNT', 'MANA', 'ARDR', 'POWR', 'XLM', 'ELF', 'SOLVE', 'ADA', 'DMT',
    'ONG', 'STORJ', 'MLK', 'ENJ', 'GRS', 'STEEM', 'ADX', 'HIVE', 'BAT', 'VTC', 'XRP', 'THETA', 'IOTA', 'MTL', 'ICX', 'ZRX', 'ARK',
    'STRAT', 'KMD', 'ONT', 'SBD', 'LSK', 'KNC', 'OMG', 'GAS', 'WAVES', 'QTUM', 'EOS', 'XTZ', 'KAVA', 'ATOM', 'ETC',
    'LINK', 'BTG', 'NEO', 'DCR', 'REP', 'LTC', 'ETH', 'JST', 'CRO', 'TON'
    ]

# MANA는 틱갭이 너무 커서 UP해도 가격 같은경우가 생김
# KAVA는 가격변화가 심해서 peak eat가 아니라 다른 경우가 자주 생김
ban_tickers = []

FEE = 0.0005  # 0.05%
DOWN = 0.0
UP   = 0.0
RESET_DOWN = 0.018
LIMIT_DOWN = 0.014
BETTING = 50000
COOL_TIME_ORDER = 60 * 1.5
COOL_CNT_ORDER = 25
COOL_TIME_HIT = 60 * 3.0
CV_CNT = 5
CV_THRESHOLD = 0.007
MAX_TICKER = 30
###############################################################################

token = '1267448247:AAE7QjHpSijbtNS9_dnaLm6zfUGX3FhmF78'
bot = telegram.Bot(token=token)

def send_telegram(msg):
    print(msg)
    try:
        bot.sendMessage(chat_id=170583240, text=msg)
    except:
        pass

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
    for i in range(int(COOL_TIME_HIT/10)):
        l = coin.get_live_orders(ticker, 'KRW')
        found = False
        for (oid, askbid, price, cnt, odt) in l:
            if askbid == 'bid':
                continue
            found = True
            if i == 0:
                print('waiting..', oid, askbid, '{:,.2f}'.format(float(price)), odt)
            break
        if found == False:
            return True
        time.sleep(10)
    return False

def cancel_pending_bids(bLog=True):
    l = coin.get_live_orders('KRW')
    if bLog: print(' cancel pending bids..')
    for (ticker, oid, askbid, price, cnt, odt) in l:
        if ticker=='BTC' or askbid == 'ask':
            continue
        r = coin.cancel(oid, False)

def cancel_pending_asks(bLog=True):
    l = coin.get_live_orders('KRW')
    if bLog:print(' cancel pending asks..')
    for (ticker, oid, askbid, price, cnt, odt) in l:
        if ticker=='BTC' or askbid == 'bid':
            continue
        r = coin.cancel(oid)

def market_sell(tickers, bLog=True):
    if bLog: print(' clear {} tickers with market sell'.format(len(tickers)))
    for ticker in tickers:
        ass = coin.get_asset_info(ticker)
        if 'free' in ass and ass['free'] > 0:
            coin.market_sell(ticker, ass['free'])

def fsame(a, b, diff=0.0001):  # default: 0.01%이내로 같으면 true 리턴
    a = float(a)
    b = float(b)
    if abs(a-b)<diff:
        return True
    return False

def sell(pd, bPartial = False):
    global total_gain, bid_oids, RESET_DOWN
    ask_oid_dict = {}

    # 1. ask first
    for t, price in pd.items():
        cv = np.std(prices[t]) / np.mean(prices[t])
        print('selling..', t, 'cv..{:.5f}'.format(cv)) if bPartial == False else print('partial selling..', t, 'cv..{:.5f}'.format(cv))
        #bid fill 상황체크
        rb = coin.get_fill_order(bid_oids[t])
        bid_price = rb['price']
        bid_volume = rb['volume']
        bid_amount = rb['final_amount']
        # bid_price = base_price_dict[t] - base_price_dict[t] * DOWN;bid_price = tick_round(bid_price)
        ask_price = price - price * UP;ask_price = tick_round(ask_price)
        bid_price_plus1 = tick_round(bid_price + bid_price*FEE*2 + coin.get_tick_size(bid_price))
        ask_price=max(ask_price, bid_price_plus1)
        ask_oid_dict[t] = coin.limit_sell(t, ask_price, bid_volume)

    # 2. cancel bid
    cancel_pending_bids()

    # 3. check ask fill
    bSuccess = False
    for t, price in pd.items():
        oid = ask_oid_dict[t]
        r = on_hit_check_fill(t)
        gain = 0
        if r:
            r2 = coin.get_fill_order(oid)
            ask_price = r2['price']
            gain = int(r2['final_amount'] - bid_amount)
            print("==============>", t, "sold!", "buy:", bid_price, "sell:", ask_price,
                    "<< gain:{} >>".format(gain))
            bSuccess = True
        else:
            RESET_DOWN += 0.005
            # check partial fills
            r = coin.get_fill_order(oid)
            ask_amount = 0
            if 'final_amount' in r:
                ask_amount = r['final_amount']
            coin.cancel(oid)
            f = 0
            while f == 0:
                ass = coin.get_asset_info(t)
                if 'free' not in ass:
                    break;
                f = ass['free']
            if f > 0:
                r = coin.market_sell(t, f)
                if 'final_amount' in r:
                    ask_amount += r['final_amount']
                    gain = int(ask_amount - bid_amount)
                    print('debug info..', 'ask_amount..', ask_amount, 'cnt..', bid_volume)
                    print(t, "limit order fail!", "buy:", bid_price, "market sell:", r['price'],
                            "<< gain:{} >>".format(gain))
                    if fsame(bid_volume, r['volume'], 0.1) == False:
                        send_telegram('gain fail!')
                        gain = 0
        if bSuccess: RESET_DOWN += 0.0028
        total_gain += gain
        if t in bid_oids:
            del bid_oids[t]  # 완판 했기 때문에 지워줌

cancel_pending_asks()
market_sell(total_tickers)

tickers = []
prices = {}
while True:
    if RESET_DOWN < LIMIT_DOWN : RESET_DOWN = LIMIT_DOWN
    DOWN = RESET_DOWN
    UP = DOWN * 3.0 / 4
    print(datetime.now().strftime("%m-%d %H:%M:%S"), 'cancel pending orders (ask/bid), clear tickers')
    cancel_pending_bids(False)
    cancel_pending_asks(False)
    market_sell(tickers, False)
    krw = coin.get_asset_info('KRW')['free']
    cnt = (min(MAX_TICKER, int((krw - 110000)/ BETTING), len(total_tickers)))
    send_telegram('\n-= DOWN:{:.4f}, 총수익:{:,}원, cnt:{}, 잔액:{:,}원, 배팅:{:,}원  =-'.
                  format(DOWN, int(total_gain), cnt, int(krw), BETTING))
    random.shuffle(total_tickers)
    tickers = total_tickers[:cnt]
    print('tickers: {}'.format(tickers))

    base_prices = {}
    bid_oids = {}
    money = coin.get_asset_info('KRW')  # to float

    for ticker in total_tickers:
        price = tick_round(coin.get_price(ticker, 'KRW'))
        if ticker not in prices: prices[ticker] = deque(maxlen=CV_CNT)
        prices[ticker].append(price)

    for ticker in tickers:
        cp = tick_round(coin.get_price(ticker, 'KRW'))
        bid_price = tick_round(cp - cp * DOWN)
        bid_cnt = float(BETTING) / bid_price

        if money['free'] < bid_price * bid_cnt:
            print(ticker, 'not enough KRW!')
            continue
        cv = np.std(prices[ticker]) / np.mean(prices[ticker])
        if cv <= CV_THRESHOLD and len(prices[ticker]) >= CV_CNT:
            oid = coin.limit_buy(ticker, bid_price, bid_cnt, False)
            base_prices[ticker] = cp
            bid_oids[ticker] = oid
        else:
            print('{} 변동계수 : {:.5f}, prices: {}'.format(ticker, cv, list(prices[ticker])))

    # for i in range(int(COOL_TIME_ORDER/10)):
    for i in range(COOL_CNT_ORDER):
        l = coin.get_live_orders('KRW')

        pd = base_prices
        for (ticker, oid, askbid, price, cnt, odt) in l:
            if ticker not in pd or askbid != 'bid': continue
            del pd[ticker]

        if len(pd) > 0:
            send_telegram("-=-= {} hits... {}=-=-".format(len(pd), pd))
            sell(pd)
            break

        # print("orders alive...")
        for (ticker, oid, askbid, price, cnt, odt) in l:
            if ticker not in base_prices or askbid == 'ask':
                continue
            price = tick_round(coin.get_price(ticker, 'KRW'))
            change = round((price-base_prices[ticker])*100.0/base_prices[ticker],1)
            if change <= -1.0:
                print(ticker, 'price from:{:,.2f} to:{:,.2f}, change:{}%, cv:{:.5f}'.
                      format(base_prices[ticker], price, change, np.std(prices[ticker])/np.mean(prices[ticker])))
        # time.sleep(10)

    cancel_pending_bids(False)
    pd = {}
    for t in tickers:
        ass = coin.get_asset_info(t)
        if 'free' in ass and ass['free'] > 0: pd[t] = base_prices[t]
    if len(pd) > 0:
        print("-=-= {} partial hits... =-=-".format(len(pd)))
        sell(pd, True)

    RESET_DOWN -= 0.0002

