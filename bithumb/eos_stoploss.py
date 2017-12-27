#! /usr/bin/env python
import sys
from xcoin_api_client import *
import pprint
import time


api_key = "api_connect_key";
api_secret = "api_secret_key";

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
		time.sleep(0.5)


while True:
	date, updown, price = get_lastest_transaction('BTC')
	print('BTC', date, updown, price)
	date, updown, price = get_lastest_transaction('EOS')
	print('EOS', date, updown, price)

