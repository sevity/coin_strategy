#! /usr/bin/env python
import sys
from xcoin_api_client import *
import pprint
import time


api_key = "";
api_secret = "";


api = XCoinAPI(api_key, api_secret);

def get_lastest_transaction(ticker):
	rgParams = {
	};
	while True:
		try:
			result = api.xcoinApiCall("/public/recent_transactions/"+ticker, rgParams);
			assert(result['status']=='0000')
			a = result['data'][0]['transaction_date'];
			b = 'uptick' if result['data'][0]['type'] == 'ask' else 'downtick';
			c = int(result['data'][0]['price']);
			return a, b, c
		except:
                        print('e')
			time.sleep(0.05)
			pass
		


def market_sell(ticker,cnt):
	rgParams = {
		"units" : cnt,
		"currency" : ticker

	};
	result = api.xcoinApiCall("/trade/market_sell/", rgParams);
	# print(result)
        if result['status'] != '0000':
            return -1, result['status']
	assert(result['status']=='0000')
        fill_cnt = len(result['data'])
        print('market sell fill_cnt', fill_cnt)
        price = 0.0
        for x in result['data']:
            price += float(x['price'])

	return price / fill_cnt, result['status']

def order_new(ticker, price, cnt, askbid):
	rgParams = {
		"order_currency" : ticker,
		"payment_currency" : "KRW",
		"units" : float(cnt),
		"price" : int(price),
		"type" : askbid,
	};
	result = api.xcoinApiCall("/trade/place/", rgParams);
	# print(result)
	return result['status']
	# return result['data']['price']

list_fill = []
def one_turn(cnt):
	eos_uc = 0  # eos uptick count
	eos_lp = -1  # eos last price
	eos_sp = -1  # eos start price

        global list_fill


        cnt = 0
        pcnt = 0  # printed cnt
	while True:

		date, updown, price = get_lastest_transaction('EOS')

		if eos_lp == -1: eos_lp = price
		if eos_sp == -1: eos_sp = price

		if price > eos_lp: eos_uc += 1
		elif price < eos_lp: eos_uc = 0;eos_sp = price


                if len(list_fill)==0 or list_fill[-1] != price:
                    list_fill.append(price)
                    cnt += 1
                if len(list_fill) < 20:
		    eos_lp = price
                    if pcnt < cnt:
                        print('EOS', date, "{:,}".format(int(price)), eos_uc, list_fill[-20:])
                        pcnt += 1
		    time.sleep(0.1)
                    continue

                ma20 = sum(list_fill[-20:]) / 20
                ma5 = sum(list_fill[-5:]) / 5
                if pcnt < cnt:
                    print('EOS', date, "{:,}".format(int(price)), eos_uc, list_fill[-20:])
                    print('ma20', ma20, 'ma5', ma5, 'down cycle' if ma5 < ma20 else 'up cycle')
                    pcnt += 1
		time.sleep(0.1)

                if ma5 >= ma20:
		    eos_lp = price
                    continue

		if eos_uc >= 2:
			print('hit!!')
                        cnt = ma20 - ma5
                        assert(cnt > 0)
			sell_price, err = market_sell('EOS', cnt)
                        while err != '0000':
                            print('['+err+']')
                            assert(err=='5600')
			    sell_price, err = market_sell('EOS', cnt)

			print("sell price: ", sell_price)
			# order_price = max(sell_price - 10, eos_sp)
			order_price = eos_lp  # base diff
			if order_price > sell_price - 15: order_price = sell_price - 15  # min diff
			print("order price: ", order_price)

			total_sell = sell_price * cnt
			new_cnt = round(1.0 * total_sell / order_price, 4) - 0.0001
			print("new_cnt: ", new_cnt)

			# new_cnt = cnt

			print('order_new...', order_price, new_cnt)
			err = order_new('EOS', order_price, new_cnt, 'bid')
			while err=='5600':  #please try again
				err = order_new('EOS', order_price, new_cnt, 'bid')
				time.sleep(0.1)
			return
		eos_lp = price

while True:
	one_turn(1)
