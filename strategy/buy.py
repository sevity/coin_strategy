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

# param #######################################################################
total_tickers = [
    # 'GRS', 'LAMB', 'IGNIS', 'BCH', 'POLY', 'EMC2', 'DCR', 'DMT'
    'XRP'
    ]
BUY_DOWN   = 0.015
BUY_AMOUNT = 1000

###############################################################################
# legacy or fixed parameters
# 얘네들은 클리어대상에서 제외
zonber_tickers = ['BTC']

BOT_DOWN  = 0.015
BOT_UP    = 0.010
ZONBER_UP = 0.002  
MAX_BETTING = 2000000

COOL_TIME_ORDER = 40
COOL_TIME_HIT = 2 * 10 * 60.0
FEE = 0.0005  # 0.05%, 위아래 해서 0.1%인듯
DOWN = 0.0
UP   = 0.0
RESET_DOWN = BOT_DOWN
LIMIT_DOWN = BOT_DOWN
BETTING = 0
MAX_TICKER = len(total_tickers)
COOL_CNT_ORDER = 150
MIN_CV_CNT = 1
MAX_CV_CNT = 25
CV_THRESHOLD = 0.098
###############################################################################

# TODO: 최근가격만 쓰면 변동성 심할때문제가 되니 최근 3번 평균이라던가 써보자  


token = '1267448247:AAE7QjHpSijbtNS9_dnaLm6zfUGX3FhmF78'
bot = telegram.Bot(token=token)

def send_telegram(msg):
    print(msg)
    try:
        bot.sendMessage(chat_id=170583240, text=msg)
    except:
        pass


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

def fsame(a, b, diff=0.0001):  # default: 0.01%이내로 같으면 true 리턴
    a = float(a)
    b = float(b)
    if abs(a-b)<diff:
        return True
    return False


def cancel_pending_bids(bLog=True):
    l = coin.get_live_orders('KRW')
    if bLog: print(' cancel pending bids..')
    for (ticker, oid, askbid, price, cnt, odt) in l:
        if ticker in zonber_tickers or askbid == 'ask':
            continue
        if ticker not in total_tickers:
            continue
        r = coin.cancel(oid, False)

def cancel_pending_asks(bLog=True):
    l = coin.get_live_orders('KRW')
    if bLog:print(' cancel pending asks..')
    for (ticker, oid, askbid, price, cnt, odt) in l:
        if ticker in zonber_tickers or askbid == 'bid':
            continue
        if ticker not in total_tickers:
            continue
        r = coin.cancel(oid)



tickers = []
prices = {}
krw = -1
prev_btc_total = -1
gain = 0
total_gain = 0
while True:
    if RESET_DOWN < LIMIT_DOWN : RESET_DOWN = LIMIT_DOWN

    DOWN = RESET_DOWN
    # UP = DOWN * 7.0 / 10
    UP = DOWN * 0.0 / 10
    print(datetime.now().strftime("%m-%d %H:%M:%S"), 'cancel pending orders (ask/bid), clear tickers')
    cancel_pending_bids(False)
    cancel_pending_asks(False)
    tr_krw = coin.get_asset_info('KRW')['free']
    btc_total = coin.get_asset_info('BTC')['total']
    print('btc_total', btc_total)
    real_gain =  tr_krw - krw
    total_gain += real_gain if krw!=-1 and abs(real_gain) < 7000 else gain
    gain = 0
    krw = tr_krw
    prev_btc_total = btc_total
    if BETTING == 0:
        bet = round((krw - 0) / MAX_TICKER, 0)
        cnt = (min(MAX_TICKER, len(total_tickers)))
    else:
        bet = BETTING
        cnt = (min(MAX_TICKER, int((krw - 0)/ bet), len(total_tickers)))
    bet = min(bet, MAX_BETTING)


    send_telegram('\n-= DOWN:-{:.4f}, 잔액:{:,}원, 배팅:{:,}원  =-'.
                  format(BUY_DOWN, int(krw), int(bet)))
    if bet < 550:
        print("betting too small!")
        time.sleep(COOL_TIME_ORDER)
        continue

    random.shuffle(total_tickers)
    tickers = total_tickers[:cnt]
    print('tickers: {}'.format(tickers))

    base_prices = {}
    bid_prices = {}
    bid_oids = {}
    money = coin.get_asset_info('KRW')  # to float

    # TODO:
    # 이렇게 주기적으로 샘플링하는 방식으로는 순간적인 피크를 검출 못해서
    # cv값이 작게 나와서 걸러야 하는 순간 매수를 하게 될 수 있다. OHLC를 쓰던가, 전체 틱을 보는 식으로 보완필요
    for ticker in total_tickers:
        price = tick_round(coin.get_price(ticker, 'KRW'))
        if ticker not in prices: prices[ticker] = deque(maxlen=MAX_CV_CNT)
        prices[ticker].append(price)

    for ticker in tickers:
        cp = tick_round(coin.get_price(ticker, 'KRW'))
        bid_price = tick_round(cp - cp * DOWN)
        bid_prices[ticker] = bid_price
        bid_cnt = float(bet) / bid_price

        if money['free'] < bid_price * bid_cnt:
            print(ticker, 'not enough KRW!')
            continue
        cv = np.std(prices[ticker]) / np.mean(prices[ticker])
        if cv <= CV_THRESHOLD and len(prices[ticker]) >= MIN_CV_CNT:
            if ticker not in zonber_tickers:
                oid = coin.limit_buy(ticker, bid_price, bid_cnt, False)
                base_prices[ticker] = cp
                bid_oids[ticker] = oid
                #print(ticker, 'oid:{}'.format(oid))
        else:
            print('{:<5} cv : {:.5f}, prices: {}'.format(ticker, cv, [ast.literal_eval("{:.2f}".format(i)) for i in list(prices[ticker])]))

    # for i in range(int(COOL_TIME_ORDER/10)):
    # for i in range(COOL_CNT_ORDER):
    n = datetime.now()
    while (datetime.now() - n).seconds < COOL_TIME_ORDER:
        l = coin.get_live_orders('KRW')

        pd = copy.deepcopy(base_prices)  
        for (ticker, oid, askbid, price, cnt, odt) in l:
            if ticker not in pd or askbid != 'bid': continue
            del pd[ticker]

        if len(pd) > 0:
            send_telegram("\n!-=-= {} buy hits... {}=-=-".format(len(pd), list(pd.keys())))
            # sell(pd)
            break
    RESET_DOWN -= 0.0005
