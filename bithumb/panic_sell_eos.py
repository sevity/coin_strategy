#! /usr/bin/env python
import sys
from xcoin_api_client import *
import pprint
import time


api_key = "e3653ee4a58434abf5fba29f2797de9a";
api_secret = "29119c1739d8e9451b461f5238353700";

# api_key = "00665d4fb675b8bd94cbf747e8c75d5070";
# api_secret = "7a429a1a656f2a153b21b83947484798";

api = XCoinAPI(api_key, api_secret);

def get_lastest_transaction(ticker):
	rgParams = {
	};
	while True:
		try:
			result = api.xcoinApiCall("/public/recent_transactions/"+ticker, rgParams);
			assert(result['status']=='0000')
			a = result['data'][0]['transaction_date']
			b = 'uptick' if result['data'][0]['type'] == 'ask' else 'downtick'
			c = int(result['data'][0]['price'])
                        d = float(result['data'][0]['units_traded'])
			return a, b, c, d
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

def one_turn(cnt):
	eos_dc = 0  # eos downtick count
	eos_lp = -1  # eos last price
        btc_dc = 0
        btc_lp = -1
        print_eos = False
        print_btc = False
        eos_lv = -1 # eos last volume
        btc_lv = -1
        eos_luc = 0
        btc_luc = 0

	while True:

		date, updown, price, volume = get_lastest_transaction('EOS')
                if price != eos_lp: print_eos = True
		if eos_lp == -1: eos_lp = price
                if eos_lv == -1: eos_lv = volume
		if price < eos_lp: eos_dc += 1
		elif price > eos_lp: eos_dc = 0
                if volume > eos_lv: eos_luc += 1
                elif volume < eos_lv: eos_luc = 0

		date, updown, bprice, bvolume = get_lastest_transaction('BTC')
                if bprice != btc_lp: print_btc = True
		if btc_lp == -1: btc_lp = bprice
                if btc_lv == -1: btc_lv = bvolume
		if bprice < btc_lp: btc_dc += 1
		elif bprice > btc_lp: btc_dc = 0;
                if bvolume > btc_lv: btc_luc += 1
                elif bvolume < btc_lv: btc_luc = 0

                if print_eos or print_btc:
                    print(date, 'EOS', "{:,}".format(int(price)), eos_dc, eos_luc, volume, 'BTC', "{:,}".format(int(bprice)), btc_dc, btc_luc, bvolume)

		if eos_dc >= 3 and btc_dc >=3:
			print('panic warning!!')
                        if eos_luc >=3 and btc_luc >=3:
                            print('real panic!!!')
                            assert(cnt > 0)
                            sell_price, err = market_sell('EOS', cnt)
                            while err != '0000':
                                # print('['+err+']')
                                assert(err=='5600')
                                sell_price, err = market_sell('EOS', cnt)

                            print("sell price: ", sell_price)
		eos_lp = price
                btc_lp = bprice
                eos_lv = volume
                btc_lv = bvolume
                print_eos = False
                print_btc = False

while True:
	one_turn(10)
        break
