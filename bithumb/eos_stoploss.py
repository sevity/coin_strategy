#! /usr/bin/env python
import sys
from xcoin_api_client import *
import pprint
import time


api_key = "e3653ee4a58434abf5fba29f2797de9a";
api_secret = "29119c1739d8e9451b461f5238353700";

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
			# print("err1")
			time.sleep(0.05)
			pass
		


def market_sell(ticker,cnt):
	rgParams = {
		"units" : cnt,
		"currency" : ticker

	};
	result = api.xcoinApiCall("/trade/market_sell/", rgParams);
	print(result)
	assert(result['status']=='0000')
	return int(result['data'][0]['price'])

def order_new(ticker, price, cnt, askbid):
	rgParams = {
		"order_currency" : ticker,
		"payment_currency" : "KRW",
		"units" : cnt,
		"price" : price,
		"type" : askbid,
	};
	result = api.xcoinApiCall("/trade/place/", rgParams);
	print(result)
	return result['status']
	# return result['data']['price']

def one_turn(cnt):
	eos_uc = 0  # eos uptick count
	eos_lp = -1  # eos last price
	eos_sp = -1  # eos start price


	while True:

		date, updown, price = get_lastest_transaction('EOS')

		if eos_lp == -1: eos_lp = price
		if eos_sp == -1: eos_sp = price

		if price > eos_lp: eos_uc += 1
		elif price < eos_lp: eos_uc = 0;eos_sp = price

		print('EOS', date, "{:,}".format(int(price)), eos_uc)
		time.sleep(0.5)

		if eos_uc >= 3:
			print('hit!!')
			sell_price = market_sell('EOS', cnt)
			print("sell price: ", sell_price)
			# order_price = max(sell_price - 10, eos_sp)
			order_price = eos_lp  # base diff
			if order_price > sell_price - 5: order_price = sell_price - 5  # min diff
			print("order price: ", order_price)

			# 아래 코드는 부분체결 고려해서 다시 짜야함
			# total_sell = sell_price * cnt
			# new_cnt = round(1.0 * total_sell / order_price, 4) - 0.0001
			# print("new_cnt: ", new_cnt)

			new_cnt = cnt

			err = order_new('EOS', order_price, new_cnt, 'bid')
			while err=='5600':  #please try again
				print('trying again...')
				err = order_new('EOS', order_price, new_cnt, 'bid')
				time.sleep(0.1)
			return
		eos_lp = price

while True:
	one_turn(5)