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
    print("Bithumb Public API URI('/public/ticker') Request...");
    result = api.xcoinApiCall("/public/ticker", rgParams);
    print("- Status Code: " + result["status"]);
    print("- Closing Price: " + result["data"]["closing_price"]);
    time.sleep(1)

