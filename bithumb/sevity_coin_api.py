#! /usr/bin/env python
import sys
from xcoin_api_client import *
import pprint
import time

from sevity_key import *


api = XCoinAPI(api_key, api_secret);

def print_err(result):
    r = int(result['status'])
    m = None
    if 'message' in result:
        m = result['message']
        # print('mm',m)

    if r == 0: return
    if r != 5600: print(result); return
    assert(r==5600)
    if m is None: return
    if m == 'Please try again': return
    if m == 'Please try again.': return
    if m == '점검중 입니다.': return
    if m == '잠시 후 이용해 주십시오.9999': return
    print(result)

def get_lastest_transaction(ticker):
    rgParams = {
    };
    while True:
        try:
            result = api.xcoinApiCall("/public/recent_transactions/"+ticker, rgParams);
            print_err(result)
            assert(int(result['status'])==0)
            a = result['data'][0]['transaction_date']
            b = 'uptick' if result['data'][0]['type'] == 'ask' else 'downtick'
            c = int(result['data'][0]['price'])
            d = float(result['data'][0]['units_traded'])
            return a, b, c, d
        except:
            print('e')
            time.sleep(0.05)
            pass 


def order_new_sub(ticker, price, cnt, askbid):
    rgParams = {
        "order_currency" : ticker,
        "payment_currency" : "KRW",
        "units" : float(cnt),
        "price" : int(price),
        "type" : askbid,
    };
    result = api.xcoinApiCall("/trade/place/", rgParams);
    print_err(result)
    r = int(result['status'])
    # if r == 0: print(result)
    return r


def order_new(ticker, price, cnt, askbid):
    print('order_new...', ticker, price, cnt, askbid)
    err = order_new_sub(ticker, price, cnt, askbid)
    while err!=0:  #please try again
        #if err != 5600:
        #    print(err)
        #    assert False
        err = order_new_sub(ticker, price, cnt, askbid)
        time.sleep(0.1)


def market_sell_sub(ticker,cnt):
    rgParams = {
        "units" : cnt,
        "currency" : ticker
    };
    result = api.xcoinApiCall("/trade/market_sell/", rgParams);
    print_err(result)
    r = int(result['status'])
    if r != 0:
        return -1, r
    assert(r==0)
    fill_cnt = len(result['data'])
    # print('market sell fill_cnt', fill_cnt)
    price = 0.0
    for x in result['data']:
        price += float(x['price'])
    return price / fill_cnt, r


def market_sell(ticker, sell_cnt):
    while True:
        print("market_sell..", ticker, sell_cnt)
        try:
            sell_price, err = market_sell_sub(ticker, sell_cnt)
            while err != 0:
                if err != 5600: print('['+err+']')
                assert(err==5600)
                sell_price, err = market_sell_sub(ticker, sell_cnt)

            print("market sell done. sell price: ", sell_price)
            return sell_price
        except:
            pass
        sleep(0.1)

def get_account_info(ticker):
    rgParams = {
        "currency" : ticker,
    };
    result = api.xcoinApiCall("/info/account/", rgParams);
    err = int(result['status'])
    assert(err == 0)
    return float(result['data']['balance'])

def get_balance(ticker):
    return get_account_info(ticker)



def get_balance_info():
    rgParams = {
        "currency" : 'ALL',
    };
    err = 1
    while err != 0:
        result = api.xcoinApiCall("/info/balance/", rgParams);
        print_err(result)
        err = int(result['status'])
    return(result)


def get_balance_all(flag_include_zero_banlance):
    list_coin = ['BTC', 'ETH', 'DASH', 'LTC', 'ETC', 'XRP', 'BCH', 'XMR', 'ZEC', 'QTUM', 'BTG', 'EOS']
    r = {}
    # rk = get_balance_info()
    # r['KRW'] = float(rk['data']['total_krw'])

    for coin in list_coin:
        b = get_balance(coin)
        if flag_include_zero_banlance is True or b >= 1e-4:
            r[coin] = b

    return r

def get_krw_info():
    rk = get_balance_info()
    r = {}
    r['total'] = float(rk['data']['total_krw'])
    r['inuse'] = float(rk['data']['in_use_krw'])
    r['free'] = float(rk['data']['available_krw'])
    return r


def market_buy_sub(ticker,cnt):
    rgParams = {
        "units" : cnt,
        "currency" : ticker
    };
    result = api.xcoinApiCall("/trade/market_buy/", rgParams);
    print_err(result)
    r = int(result['status'])
    if r != 0: return -1, r
    assert(r==0)
    fill_cnt = len(result['data'])
    # print('market buy fill_cnt', fill_cnt)
    price = 0.0
    for x in result['data']:
        price += float(x['price'])
    return price / fill_cnt, r

def market_buy(ticker, buy_cnt):
    while True:
        print("market_buy..", ticker, buy_cnt)
        try:
            buy_price, err = market_buy_sub(ticker, buy_cnt)
            print(buy_price, err)
            while err != 0:
                if err != 5600:
                    print('['+err+']')
                    return 0, err
                buy_price, err = market_buy_sub(ticker, buy_cnt)

            print("market buy done. buy price: ", buy_price)
            return buy_price, err
        except:
            pass

def get_quote(ticker):
    rgParams = {
    };

    while True:
        try:
            result = api.xcoinApiCall("/public/orderbook/"+ticker, rgParams);
            assert(int(result['status'])==0)
            # print(result);
            return result
            # print(result['data']['asks'][0]['price'])
        except:
            print('e')
            time.sleep(0.05)
            pass 



def buy_all_sub(ticker, flag_use_last_fill_price):
    krw = get_krw_info()
    free_krw = krw['free']
    if flag_use_last_fill_price:
        date, updown, price, volume = get_lastest_transaction(ticker)
    else:
        r = get_quote(ticker)
        # print(r)
        ask1_price = int(r['data']['asks'][0]['price'])
        price = ask1_price

    max_buy_cnt = 1.0 * free_krw / price
    max_buy_cnt *= 0.9999  #margin
    max_buy_cnt = round(max_buy_cnt, 4)
    print('free krw', "{:,.0f}".format(free_krw), ticker, 'price', "{:,.0f}".format(price), 'max_buy_cnt', "{:,.4f}".format(max_buy_cnt))
    buy_price, err = market_buy_sub(ticker, max_buy_cnt)
    return buy_price, err


def buy_all(ticker, flag_use_last_fill_price = True):
    err = 1
    while err != 0:
        buy_price, err = buy_all_sub(ticker, flag_use_last_fill_price)
    print('buy_all done.', 'buy_price', buy_price)
    krw = get_krw_info()
    krw = ', '.join('{{{}: ￦{:,.0f}}}'.format(k,v) for k,v in krw.items())
    print('KRW info', krw)

def rate_change(before_price, after_price):
    return "{:+}%".format(round(100 * (after_price - before_price) / before_price, 2))
