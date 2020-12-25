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
BTC_UP            = 0.003
BTC_DOWN          = 0.001
BTC_BETTING_RATIO = 0.001  # 총 BTC자산의 0.1%를한번에 배팅
BTC_MAX_BETTING   = 500000

BTC_MAX_UP = BTC_UP * 2
BTC_MIN_UP = BTC_UP
BTC_MAX_DOWN = BTC_UP / 2
BTC_MIN_DOWN = BTC_DOWN
BTC_DELTA_UP = 0.001  # BTC_UP이 상승하는비율

COOL_TIME_ORDER = 60
COOL_TIME_HIT = 1 * 5 * 60.0
###############################################################################
# legacy or fixed parameters
total_tickers = ['BTC']
zonber_tickers = []
FEE = 0.0005  # 0.05%, 위아래 해서 0.1%인듯
DOWN = 0.0
UP   = 0.0
BETTING = 0
MAX_TICKER = len(total_tickers)
COOL_CNT_ORDER = 150
MIN_CV_CNT = 1
MAX_CV_CNT = 25
CV_THRESHOLD = 0.098
ZONBER_UP = 0.002  
BTC_RESET_UP = BTC_UP
BTC_ZONBER_DOWN   = 0.001
###############################################################################


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


def on_hit_check_fill(ticker):
    # TODO: 아래부분 시간계산이 정밀하지 않다.
    for i in range(int(COOL_TIME_HIT / 30)):
        l = coin.get_live_orders(ticker, 'KRW')
        found = False
        for (oid, askbid, price, cnt, odt) in l:
            if askbid == 'ask':
                continue
            found = True
            if i == 0:
                print('waiting..{:,} min.'.format(int(COOL_TIME_HIT / 60)), oid, askbid, '{:,.2f}'.format(float(price)), odt)
            break
        if found == False:
            return True
        time.sleep(30)
        t = ticker
        ask_price = float(ask_prices[t] if t in ask_prices else -1.0)
        bid_price = float(price)
        cur_price = float(tick_round(coin.get_price(t, 'KRW')))
        left_min = float((COOL_TIME_HIT - 30 * i) / 60)
        print(t, '{:.2f}min.left, ask:{:,.2f}, bid:{:,.2f} cur:{:,.2f}'.
                format(left_min, ask_price, bid_price, cur_price))
        # print('{:<5} cv : {:.5f}, prices: {}'.format(t, cv, [ast.literal_eval("{:.2f}".format(i)) for i in list(prices[t])]))
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

def sell(pd, bPartial = False):
    global gain, ask_oids, BTC_UP, BTC_DOWN, BTC_DELTA_UP
    bid_oid_dict = {}

    # 1. bid first
    for t, price in pd.items():
        cv = np.std(prices[t]) / np.mean(prices[t])
        print('selling..' if bPartial == False else 'partial selling..', t, 'cv:{:.5f}({})'.format(cv, len(prices[t])))
        if t not in ask_oids:
            print(t, 'not in', ask_oids)  # 최소주문금액 500원때문에 생긴 550원 bid의 경우 여기 걸릴 수 있음
            continue

        #ask fill 상황체크
        print(t, 'check oid:{}'.format(ask_oids[t]))
        rb = coin.get_fill_order(ask_oids[t])
        if 'price' not in rb:
            gain = 0
            send_telegram('get_fill_order({}, ) fail!'.format(t, ask_oids[t]))
            continue
        else:
            ask_price = rb['price']
            ask_volume = rb['volume']
            ask_amount = rb['final_amount']
        bid_price = base_prices[t] * (1.0 + BTC_DOWN);bid_price=tick_round(bid_price)
        print('bid price:', bid_price)
        ask_price_minus1 = tick_round(ask_price - bid_price * FEE * 2 + coin.get_tick_size(ask_price))
        bid_price=min(bid_price, ask_price_minus1)
        bid_oid_dict[t] = coin.limit_buy(t, bid_price, ask_volume)

    # log
    for t, price in pd.items():
        if t in base_prices:
            price = tick_round(coin.get_price(t, 'KRW'))
            change = round((price-base_prices[t])*100.0/base_prices[t],1)
            print(t, 'price from:{:,.2f} to:{:,.2f}, change:{}%, cv:{:.5f}'.
                    format(base_prices[t], price, change, np.std(prices[t])/np.mean(prices[t])))
            print('{:<5} cv : {:.5f}, prices: {}'.format(t, cv, [ast.literal_eval("{:.2f}".format(i)) for i in list(prices[t])]))

    # 2. check bid fill
    bSuccess = False
    for t, price in pd.items():
        if t not in bid_oid_dict:
            continue
        oid = bid_oid_dict[t]
        r = on_hit_check_fill(t)
        gain = 0
        if r:
            BTC_UP += BTC_UP * BTC_DELTA_UP
            BTC_DOWN += BTC_DOWN * BTC_DELTA_UP
            r2 = coin.get_fill_order(oid)
            bid_price = r2['price']
            gain = int(ask_amount - r2['final_amount'])
            print("!==============>", t, "buy!", "sell:", ask_price, "buy:", bid_price,
                    "<< gain:{} >>".format(gain))
            bSuccess = True
        else:
            BTC_UP -= BTC_UP * BTC_DELTA_UP
            BTC_DOWN -= BTC_DOWN * BTC_DELTA_UP
            # coin.cancel(oid)  # cancel partial buy
            continue

        if t in ask_oids:
            del ask_oids[t]  # 완판 했기 때문에 지워줌


tickers = []
prices = {}
btc = -1
prev_btc_total = -1
gain = 0
total_gain = 0
while True:
    if   BTC_UP > BTC_MAX_UP : BTC_UP = BTC_MAX_UP
    elif BTC_UP < BTC_MIN_UP : BTC_UP = BTC_MIN_UP
    if   BTC_DOWN > BTC_MAX_DOWN : BTC_DOWN = BTC_MAX_DOWN
    elif BTC_DOWN < BTC_MIN_DOWN : BTC_DOWN = BTC_MIN_DOWN

    print('')
    cancel_pending_bids()
    cancel_pending_asks()
    btc_total = coin.get_asset_info('BTC')['total']
    tr_btc = btc_total
    btc_price = int(coin.get_price('BTC', 'KRW'))
    print('\n!', datetime.now().strftime("%m-%d %H:%M:%S"), 'my btc:', '{:.4f}'.format(btc_total), 
        'btc price:', '{:,}'.format(btc_price), 'BTC자산:', '{:,}'.format(int(btc_total*btc_price)))
    real_gain =  tr_btc - btc
    total_gain += real_gain if btc > -1 else 0
    gain = 0
    btc = tr_btc
    

    bet = min(btc_total * BTC_BETTING_RATIO, BTC_MAX_BETTING)

    send_telegram('\n-= UP:-{:.4f}, DOWN:-{:.4f}, 총수익:{:.4f} BTC = {:,}원, 배팅:{:.4f} BTC = {:,}원  =-'.
                  format(BTC_UP, BTC_DOWN, btc_price*total_gain, int(total_gain), bet, int(bet*btc_price)))

    if bet*btc_price <= 1000:
        print("betting too small!")
        time.sleep(COOL_TIME_ORDER)
        continue

    random.shuffle(total_tickers)
    tickers = total_tickers[:1]

    base_prices = {}
    ask_prices = {}
    ask_oids = {}
    btc_money = coin.get_asset_info('BTC')  # to float

    # TODO:
    # 이렇게 주기적으로 샘플링하는 방식으로는 순간적인 피크를 검출 못해서
    # cv값이 작게 나와서 걸러야 하는 순간 매수를 하게 될 수 있다. OHLC를 쓰던가, 전체 틱을 보는 식으로 보완필요
    for ticker in total_tickers:
        price = tick_round(coin.get_price(ticker, 'KRW'))
        if ticker not in prices: prices[ticker] = deque(maxlen=MAX_CV_CNT)
        prices[ticker].append(price)

    for ticker in tickers:
        cp = tick_round(coin.get_price(ticker, 'KRW'))
        ask_price = tick_round(cp + cp * BTC_UP)
        ask_prices[ticker] = ask_price
        ask_cnt = bet

        if btc_money['free'] < bet:
            print(ticker, 'not enough BTC!')
            continue

        cv = np.std(prices[ticker]) / np.mean(prices[ticker])
        if cv <= CV_THRESHOLD and len(prices[ticker]) >= MIN_CV_CNT:
            if ticker not in zonber_tickers:
                oid = coin.limit_sell(ticker, ask_price, ask_cnt, True)
                base_prices[ticker] = cp
                ask_oids[ticker] = oid
                #print(ticker, 'oid:{}'.format(oid))
        else:
            print('{:<5} cv : {:.5f}, prices: {}'.format(ticker, cv, [ast.literal_eval("{:.2f}".format(i)) for i in list(prices[ticker])]))


    n = datetime.now()
    while (datetime.now() - n).seconds < COOL_TIME_ORDER:
        l = coin.get_live_orders('KRW')
        pd = copy.deepcopy(base_prices)  
        for (ticker, oid, askbid, price, cnt, odt) in l:
            if ticker not in pd or askbid != 'ask': continue
            del pd[ticker]

        if len(pd) > 0:
            send_telegram("\n!-=-= {} hits... {}=-=-".format(len(pd), list(pd.keys())))
            sell(pd)
            break

        print(".", end="", flush=True)

    BTC_UP -= BTC_UP * BTC_DELTA_UP
    BTC_DOWN -= BTC_DOWN * BTC_DELTA_UP
