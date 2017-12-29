#! /usr/bin/env python
import sys
from xcoin_api_client import *
import pprint
import time

api_key = "";
api_secret = "";

# options ########################################
panic_sell_cnt = 10
real_panic_sell_cnt = 30
price_count_threshold = 3
volume_count_threshold = 3
eos_only_price_count_threshold = 4
min_price_drop = 30
buy_back_price_offset = 40
##################################################



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
    if result['status'] != '0000': return -1, result['status']
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


def panic_sell(sell_cnt):
    sell_price, err = market_sell('EOS', sell_cnt)
    while int(err) != 0:
        if int(err) != 5600: print('['+err+']')
        assert(int(err)==5600)
        sell_price, err = market_sell('EOS', sell_cnt)

    print("panic sell done. sell price: ", sell_price)
    return sell_price

def buy_back(sell_price, sell_cnt, buy_price):
    print("sell price", sell_price, "buy_price", buy_price)
    assert(buy_price <= sell_price - buy_back_price_offset)

    sell_amount = sell_price * sell_cnt
    fee = 0.00151  # trailing 1 is for preventing overflow
    buy_cnt = round( (1.0) * sell_amount / (buy_price * (1.0 + fee) ), 4)# - 0.0001
    print("buy_cnt: ", buy_cnt)

    print('order_new...', buy_price, buy_cnt)
    err = order_new('EOS', buy_price, buy_cnt, 'bid')
    while err!='0000':  #please try again
        if err != '5600':
            print(err)
            assert False
        err = order_new('EOS', buy_price, buy_cnt, 'bid')
        time.sleep(0.1)
    print("buy_back done.")


class Monitor:
    def __init__(self, ticker):
        self.ticker = ticker
        self.puc = 0  # continuous uptick count (price)
        self.pdc = 0  # continuous downtick count (price)
        self.vuc = 0  # continuous uptick count (volume)
        self.vdc = 0  # continuous uptick count (volume)
        self.dsp = 0  # down start price
        self.usp = 0  # up start price
        self.dsv = 0  # down start volume
        self.usv = 0  # up start volume
        self.lp = []  # list price
        self.lv = []  # list volume

    def get(self):
        date, updown, price, volume = get_lastest_transaction(self.ticker)
        while len(self.lp) > 0 and self.lp[-1] == price and self.lv[-1] == volume:
            date, updown, price, volume = get_lastest_transaction(self.ticker)
        if self.dsp == 0: self.dsp = price
        if self.usp == 0: self.usp = price
        if self.dsv == 0: self.dsv = volume
        if self.usv == 0: self.usv = volume
        self.lp.append(price)
        self.lv.append(volume)
        if len(self.lp) < 2: return False, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0

        if   self.lp[-1] > self.lp[-2]: self.puc += 1; self.pdc = 0; self.dsp = price
        elif self.lp[-1] < self.lp[-2]: self.puc = 0; self.pdc += 1; self.usp = price

        if   self.lv[-1] > self.lv[-2]: self.vuc += 1; self.vdc = 0; self.dsv = volume
        elif self.lv[-1] < self.lv[-2]: self.vuc = 0; self.vdc += 1; self.usv = volume

        pd = self.lp[-1] - self.lp[-2]  # price delta
        vd = self.lv[-1] - self.lv[-2]  # volume delta

        return True, date, price, volume, pd, vd, self.puc, self.pdc, self.vuc, self.vdc, self.usp, self.dsp, self.usv, self.dsv



def one_turn(cnt):
    eos_monitor = Monitor('EOS')
    btc_monitor = Monitor('BTC')

    while True:
        ech, ed, ep, ev, epd, evd, epuc, epdc, evuc, evdc, eusp, edsp, eusv, edsv = eos_monitor.get()
        bch, bd, bp, bv, bpd, bvd, bpuc, bpdc, bvuc, bvdc, busp, bdsp, busv, bdsv = btc_monitor.get()

        if ech or bch:  # flag_eos_change or flag_btc_change
            print(ed[11:], 'EOS', "￦{:,}({:>+4,})".format(int(ep), epd), "(c{:>+5,}) [￦↓{}".format(ep - edsp, epdc),\
                           "V↑{}] (c{:>+5})".format(evuc, int(ev - eusv)), "V{:<5,.0f}({:>+4,.0f})".format(ev, evd),\
                       '\t\tBTC', "￦{:,}({:>+8,})".format(int(bp), bpd), "[￦↓{}".format(bpdc), "V↑{}]".format(bvuc), "V{:.4f}({:>+4,.4f})".format(bv, bvd))

        if edsp - ep >= min_price_drop:        
            if epdc >= price_count_threshold and bpdc >= price_count_threshold:
                if evuc >= volume_count_threshold and bvuc >= volume_count_threshold:
                    print('real panic!!!')
                    sell_price = panic_sell(real_panic_sell_cnt)
                    buy_price = sell_price - (epdc - price_count_threshold + 1) * buy_back_price_offset * 3
                    buy_back(sell_price, real_panic_sell_cnt, buy_price)
                else:
                    print('small panic!!')
                    sell_price = panic_sell(panic_sell_cnt)
                    buy_price = sell_price - (epdc - price_count_threshold + 1) * buy_back_price_offset
                    buy_back(sell_price, panic_sell_cnt, buy_price)
            if epdc >= eos_only_price_count_threshold:
                    print('eos only panic!!')
                    sell_price = panic_sell(panic_sell_cnt)
                    buy_price = sell_price - (epdc - eos_only_price_count_threshold + 1) * buy_back_price_offset
                    buy_back(sell_price, panic_sell_cnt, buy_price)

while True:
    one_turn(panic_sell_cnt)
    break
