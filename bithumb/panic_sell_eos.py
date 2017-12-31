#! /usr/bin/env python
from sevity_coin_api import *


# options ########################################
panic_sell_cnt = 3
real_panic_sell_cnt = 20
price_count_threshold = 3
volume_count_threshold = 3
eos_only_price_count_threshold = 7
btc_only_price_count_threshold = 8

detect_panic_delta = 30
min_price_drop = 50
panic_price_offset = 10
real_panic_price_offset = 30
##################################################


def panic_sell(sell_cnt):
    return market_sell('EOS', sell_cnt)

def buy_back(sell_price, sell_cnt, buy_price):
    if buy_price >= sell_price - min_price_drop: buy_price = sell_price - min_price_drop
    print("* buy_price", buy_price, "gain:{:,} *".format(sell_price - buy_price))
    # assert(buy_price <= sell_price - buy_back_price_offset)

    sell_amount = sell_price * sell_cnt
    fee = 0.00151  # trailing 1 is for preventing overflow
    buy_cnt = round( (1.0) * sell_amount / (buy_price * (1.0 + fee) ), 4)# - 0.0001
    # print("buy_cnt: ", buy_cnt)

    order_new('EOS', buy_price, buy_cnt, 'bid')
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
    panic_cnt = 0

    while True:
        ech, ed, ep, ev, epd, evd, epuc, epdc, evuc, evdc, eusp, edsp, eusv, edsv = eos_monitor.get()
        bch, bd, bp, bv, bpd, bvd, bpuc, bpdc, bvuc, bvdc, busp, bdsp, busv, bdsv = btc_monitor.get()

        if ech or bch:  # flag_eos_change or flag_btc_change
            print(ed, 'EOS', "￦{:,}({:>+4,})".format(int(ep), epd), "(c{:>+5,}) [￦↓{}".format(ep - edsp, epdc),\
                      "V↑{}] (c{:>+5})".format(evuc, int(ev - eusv)), "V{:<5,.0f}({:>+4,.0f})".format(ev, evd),\
                  '\t\tBTC', "￦{:,}({:>+8,})".format(int(bp), bpd), "[￦↓{}".format(bpdc), "V↑{}]".format(bvuc), "V{:.4f}({:>+4,.4f})".format(bv, bvd))
        else:
            continue

        if bpdc >= btc_only_price_count_threshold:
                print('BTC only panic!!'); panic_cnt += 1
                sell_price = panic_sell(panic_sell_cnt)
                buy_price = sell_price - min_price_drop - (panic_cnt - 1) * panic_price_offset
                buy_back(sell_price, panic_sell_cnt, buy_price)
                continue

        if edsp - ep >= detect_panic_delta:        
            if epdc >= price_count_threshold and bpdc >= price_count_threshold:
                if evuc >= volume_count_threshold and bvuc >= volume_count_threshold:
                    print('real panic!!!'); panic_cnt += 1
                    sell_price = panic_sell(real_panic_sell_cnt)
                    buy_price = sell_price - min_price_drop - (panic_cnt - 1) * real_panic_price_offset
                    buy_back(sell_price, real_panic_sell_cnt, buy_price)
                    continue
                else:
                    print('small panic!!'); panic_cnt += 1
                    sell_price = panic_sell(panic_sell_cnt)
                    buy_price = sell_price - min_price_drop - (panic_cnt - 1) * panic_price_offset
                    buy_back(sell_price, panic_sell_cnt, buy_price)
                    continue
            if epdc >= eos_only_price_count_threshold:
                    print('EOS only panic!!'); panic_cnt += 1
                    sell_price = panic_sell(panic_sell_cnt)
                    buy_price = sell_price - min_price_drop - (panic_cnt - 1) * panic_price_offset
                    buy_back(sell_price, panic_sell_cnt, buy_price)
                    continue
        panic_cnt = 0

while True:
    krw = get_krw_info()
    krw = ', '.join('{{{}: ￦{:,.0f}}}'.format(k,v) for k,v in krw.items())
    print('KRW info', krw)
    coins = get_balance_all(False)
    coins = ', '.join("{{{}: {:,.4f}}}".format(k,v) for k,v in coins.items())
    print('my coins', coins)

    one_turn(panic_sell_cnt)
    break
