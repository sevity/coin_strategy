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
			c = result['data'][0]['price'];
			return a, b, c
		except:
			# print("err1")
			pass
		time.sleep(0.05)


def market_sell(ticker,cnt):
	rgParams = {
		"units" : cnt,
		"currency" : ticker

	};
	result = api.xcoinApiCall("/trade/market_sell/", rgParams);
	print(result)
	assert(result['status']=='0000')
	return result['data'][0]['price']

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

def one_turn():
	eos_uc = 0  # eos uptick count
	eos_lp = -1  # eos last price
	eos_sp = -1  # eos start price


	while True:

		date, updown, price = get_lastest_transaction('EOS')
		if eos_lp == -1: eos_lp = price
		if eos_sp == -1: eos_sp = price

		if price > eos_lp: eos_uc += 1
		else: eos_uc = 0;eos_sp = price
		eos_lp = price

		print('EOS', date, "{:,}".format(int(price)), eos_uc)

		if eos_uc >= 3:
			print('hit!!')
			sell_price = market_sell('EOS', 1)
			print("sell price: ", sell_price)
			print("order price: ", eos_sp)

			err = order_new('EOS', eos_sp, 1, 'bid')
			while err=='5600':  #please try again
				print('trying again...')
				err = order_new('EOS', eos_sp, 1, 'bid')

			return

while True:
	one_turn()
	break