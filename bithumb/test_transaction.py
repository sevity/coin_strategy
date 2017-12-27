#! /usr/bin/env python
import sys
from xcoin_api_client import *
import pprint
import time


api_key = "api_connect_key";
api_secret = "api_secret_key";

api = XCoinAPI(api_key, api_secret);

rgParams = {
	"order_currency" : "BTC",
	"payment_currency" : "KRW"
};

while True:
	try:
		result = api.xcoinApiCall("/public/recent_transactions", rgParams);
		assert(result['status']=='0000')
		print(result);
	except:
		print("err")
		pass

	time.sleep(2)

