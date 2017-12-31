#! /usr/bin/env python
import sys
from xcoin_api_client import *
import pprint
import time


api_key = "api_connect_key";
api_secret = "api_secret_key";

api = XCoinAPI(api_key, api_secret);

rgParams = {
    "order_currency" : "EOS",
    "payment_currency" : "KRW"
};

while True:
    try:
        result = api.xcoinApiCall("/public/orderbook", rgParams);
        assert(int(result['status'])==0)
        # print(result);
        return result
        # print(result['data']['asks'][0]['price'])
    except:
        print('e')
        time.sleep(0.05)
        pass 

