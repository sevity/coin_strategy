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
    'MFT','IQ','CRE','MBL','STMX','SC','MED','EDR','TSHP','SPND','TT', 'IOST', 'AHT', 'QKC', 'ANKR', 'TFUEL', 'OST', 'PXL',
    'SRN', 'CHZ', 'GTO', 'ORBS', 'UPP', 'MOC', 'STPT', 'VET', 'TRX', 'ZIL', 'LOOM', 'IGNIS', 'SNT', 'CVC', 'POLY', 
    'BORA', 'HBAR', 'AERGO', 'DKA', 'WAXP', 'EMC2', 'XEM', 'GNT', 'MANA', 'ARDR', 'POWR', 'XLM', 'ELF', 'SOLVE', 'ADA', 'DMT',
    'ONG', 'STORJ', 'MLK', 'ENJ', 'GRS', 'STEEM', 'ADX', 'HIVE', 'BAT', 'VTC', 'XRP', 'THETA', 'IOTA', 'MTL', 'ICX', 'ZRX', 'ARK',
    'STRAT', 'KMD', 'ONT', 'SBD', 'LSK', 'KNC', 'OMG', 'GAS', 'WAVES', 'QTUM', 'EOS', 'XTZ', 'KAVA', 'ATOM', 'ETC',
    'LINK', 'BTG', 'NEO', 'DCR', 'REP', 'LTC', 'ETH', 'JST', 'CRO', 'TON', 'SXP', 'LAMB', 'HUNT', 'MARO'
    ]

# MANA는 틱갭이 너무 커서 UP해도 가격 같은경우가 생김
# KAVA는 가격변화가 심해서 peak eat가 아니라 다른 경우가 자주 생김
ban_tickers = []

# 얘네들은 클리어대상에서 제외
zonber_tickers = ['BTC', 'DKA']

FEE = 0.0005  # 0.05%, 위아래 해서 0.1%인듯
DOWN = 0.0
UP   = 0.0
RESET_DOWN = 0.0155
LIMIT_DOWN = 0.0135
BETTING = 0
COOL_TIME_ORDER = 60 * 1.5
COOL_CNT_ORDER = 25
COOL_TIME_HIT = 72 * 60 * 60.0
MIN_CV_CNT = 5
MAX_CV_CNT = 13
CV_THRESHOLD = 0.008
MAX_TICKER = 30
###############################################################################

# TODO: 매번 COOL_TIME_ORDER만큼만 기다리고 bid cancel을 하니 랭크가 내려가서 bid체결이 잘안되니, bid cancel없이 갱신하는거 해보자.
# TODO: CV대신 체결볼륨을 사용해볼 수 있을것 같다. 거래가 많으면 피하는 식으로..
# TODO: 코인별로 과거 성공여부 확인해서 파라미터를 코인별로 조정하기(지금 EOS, XRP, ETH같은건 거의 안걸리는데 이거하면 될지도)
# TODO: 코인별 로직을 스레드로 분기하기(맨위 TODO하기에도 이게 좋을듯?)
# TODO: KRW말고 BTC마켓에서도 한번 굴려보자(알트가 영향받는게 BTC마켓인거 같기도 해서 비트폭락시 영향을 적게받을거 같기도 하다), 그리고 BTC많이 있을때 유용

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

def format_numbers(dict, rnd):
    for key, val in dict.items():
        dict[key] = '{:,}'.format(round(val, rnd) if rnd!=0 else int(val))

# return price multiple of ticksize
def tick_round(price):
    t = coin.get_tick_size(price)
    return int(price / t) * t

def on_hit_check_fill(ticker):
    # TODO: 아래부분 시간계산이 정밀하지 않다.
    for i in range(int(COOL_TIME_HIT / 30)):
        l = coin.get_live_orders(ticker, 'KRW')
        found = False
        for (oid, askbid, price, cnt, odt) in l:
            if askbid == 'bid':
                continue
            found = True
            if i == 0:
                print('waiting..{:,} min.'.format(int(COOL_TIME_HIT / 60)), oid, askbid, '{:,.2f}'.format(float(price)), odt)
            break
        if found == False:
            return True
        time.sleep(30)
        t = ticker
        bid_price = float(bid_prices[t] if t in bid_prices else -1.0)
        ask_price = float(price)
        cur_price = float(tick_round(coin.get_price(t, 'KRW')))
        left_min = float((COOL_TIME_HIT - 30 * i) / 60)
        print(t, '{:.2f}min.left, bid:{:,.2f}, ask:{:,.2f} cur:{:,.2f}, cv:{:.5f}'.
                format(left_min, bid_price, ask_price, cur_price, np.std(prices[t]) / np.mean(prices[t])))
        # print('{:<5} cv : {:.5f}, prices: {}'.format(t, cv, [ast.literal_eval("{:.2f}".format(i)) for i in list(prices[t])]))
    return False

def cancel_pending_bids(bLog=True):
    l = coin.get_live_orders('KRW')
    if bLog: print(' cancel pending bids..')
    for (ticker, oid, askbid, price, cnt, odt) in l:
        if ticker in zonber_tickers or askbid == 'ask':
            continue
        r = coin.cancel(oid, False)

def cancel_pending_asks(bLog=True):
    l = coin.get_live_orders('KRW')
    if bLog:print(' cancel pending asks..')
    for (ticker, oid, askbid, price, cnt, odt) in l:
        if ticker in zonber_tickers or askbid == 'bid':
            continue
        r = coin.cancel(oid)

def market_sell(tickers, bLog=True):
    if bLog: print(' clear {} tickers with market sell'.format(len(tickers)))
    for ticker in tickers:
        ass = coin.get_asset_info(ticker)
        if 'free' in ass and ass['free'] > 0:
            while True:
                try:
                    coin.market_sell(ticker, ass['free'])
                    break
                except:
                    pass

def fsame(a, b, diff=0.0001):  # default: 0.01%이내로 같으면 true 리턴
    a = float(a)
    b = float(b)
    if abs(a-b)<diff:
        return True
    return False

def sell(pd, bPartial = False):
    global gain, bid_oids, RESET_DOWN
    ask_oid_dict = {}

    # 1. ask first
    for t, price in pd.items():
        cv = np.std(prices[t]) / np.mean(prices[t])
        print('selling..' if bPartial == False else 'partial selling..', t, 'cv:{:.5f}({})'.format(cv, len(prices[t])))
        if t not in bid_oids:
            print(t, 'not in', bid_oids)  # 최소주문금액 500원때문에 생긴 550원 bid의 경우 여기 걸릴 수 있음
            continue

        #bid fill 상황체크
        rb = coin.get_fill_order(bid_oids[t])
        if 'price' not in rb:
            gain = 0
            send_telegram('get_fill_order({}, ) fail!'.format(t, bid_oids[t]))
            time.sleep(5 * 60)
            continue
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

    # log
    for t, price in pd.items():
        if t in base_prices:
            price = tick_round(coin.get_price(t, 'KRW'))
            change = round((price-base_prices[t])*100.0/base_prices[t],1)
            print(t, 'price from:{:,.2f} to:{:,.2f}, change:{}%, cv:{:.5f}'.
                    format(base_prices[t], price, change, np.std(prices[t])/np.mean(prices[t])))
            print('{:<5} cv : {:.5f}, prices: {}'.format(t, cv, [ast.literal_eval("{:.2f}".format(i)) for i in list(prices[t])]))

    # 3. check ask fill
    bSuccess = False
    for t, price in pd.items():
        if t not in ask_oid_dict:
            continue
        oid = ask_oid_dict[t]
        r = on_hit_check_fill(t)
        gain = 0
        if r:
            r2 = coin.get_fill_order(oid)
            ask_price = r2['price']
            gain = int(r2['final_amount'] - bid_amount)
            print("!==============>", t, "sold!", "buy:", bid_price, "sell:", ask_price,
                    "<< gain:{} >>".format(gain))
            bSuccess = True
        else:
            RESET_DOWN += 0.002
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
                    # print('debug info..', 'ask_amount..', ask_amount, 'cnt..', bid_volume)
                    print(t, "limit order fail!", "buy:", bid_price, "market sell:", r['price'],
                            "<< gain:{} >>".format(gain))
                    if fsame(bid_volume, r['volume'], 0.1) == False:
                        send_telegram('gain fail!')
                        gain = 0
        # if bSuccess: RESET_DOWN += 0.0013
        if t in bid_oids:
            del bid_oids[t]  # 완판 했기 때문에 지워줌

cancel_pending_asks()
market_sell(total_tickers)

tickers = []
prices = {}
krw = -1
gain = 0
total_gain = 0
while True:
    if RESET_DOWN < LIMIT_DOWN : RESET_DOWN = LIMIT_DOWN


    DOWN = RESET_DOWN
    UP = DOWN * 7.0 / 10
    print(datetime.now().strftime("%m-%d %H:%M:%S"), 'cancel pending orders (ask/bid), clear tickers')
    cancel_pending_bids(False)
    cancel_pending_asks(False)
    market_sell(tickers, False)
    tr_krw = coin.get_asset_info('KRW')['free']
    real_gain =  tr_krw - krw
    total_gain += real_gain if krw!=-1 and abs(real_gain) < 7000 else gain
    gain = 0
    krw = tr_krw
    if BETTING == 0:
        bet = round((krw - 110000) / MAX_TICKER, 0)
        cnt = (min(MAX_TICKER, len(total_tickers)))
    else:
        bet = BETTING
        cnt = (min(MAX_TICKER, int((krw - 110000)/ bet), len(total_tickers)))


    send_telegram('\n-= DOWN:{:.4f}, 총수익:{:,}원, cnt:{}, 잔액:{:,}원, 배팅:{:,}원  =-'.
                  format(DOWN, int(total_gain), cnt, int(krw), int(bet)))
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
            oid = coin.limit_buy(ticker, bid_price, bid_cnt, False)
            base_prices[ticker] = cp
            bid_oids[ticker] = oid
        else:
            print('{:<5} cv : {:.5f}, prices: {}'.format(ticker, cv, [ast.literal_eval("{:.2f}".format(i)) for i in list(prices[ticker])]))

    # for i in range(int(COOL_TIME_ORDER/10)):
    for i in range(COOL_CNT_ORDER):
        l = coin.get_live_orders('KRW')

        pd = copy.deepcopy(base_prices)  
        for (ticker, oid, askbid, price, cnt, odt) in l:
            if ticker not in pd or askbid != 'bid': continue
            del pd[ticker]

        if len(pd) > 0:
            send_telegram("\n!-=-= {} hits... {}=-=-".format(len(pd), list(pd.keys())))
            sell(pd)
            break

        # print("orders alive...")
        print(".", end="")
        for (ticker, oid, askbid, price, cnt, odt) in l:
            if ticker not in base_prices or askbid != 'bid': continue
            price = tick_round(coin.get_price(ticker, 'KRW'))
            change = round((price-base_prices[ticker])*100.0/base_prices[ticker],1)
            if change <= -1.0:
                print(ticker, 'price from:{:,.2f} to:{:,.2f}, change:{}%(bid:{:,.2f}), cv:{:.5f}'.
                      format(base_prices[ticker], price, change, bid_prices[ticker], np.std(prices[ticker])/np.mean(prices[ticker])))
        # time.sleep(10)

    cancel_pending_bids(False)
    pd = {}
    for t in tickers:
        ass = coin.get_asset_info(t)
        if 'free' in ass and ass['free'] > 0: pd[t] = 0
    if len(pd) > 0:
        print("-=-= {} partial hits... =-=-".format(len(pd)))
        sell(pd, True)

    RESET_DOWN -= 0.0001
