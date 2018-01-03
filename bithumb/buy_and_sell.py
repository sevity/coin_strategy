#! /usr/bin/env python
from sevity_coin_api import *


# options ########################################
unit_money = 40000  # krw
buy_delta = 0.0075    # 1.5%
losscut = 0.01      # 1.0%
gaincut = 0.02
##################################################

class Monitor:
    def __init__(self, ticker):
        self.clear()
        self.ticker = ticker
        self.lb = []  # list buy

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
        if len(self.lp) < 2: return False, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0

        if   self.lp[-1] > self.lp[-2]: self.puc += 1; self.pdc = 0; self.dsp = price
        elif self.lp[-1] < self.lp[-2]: self.puc = 0; self.pdc += 1; self.usp = price

        if   self.lv[-1] > self.lv[-2]: self.vuc += 1; self.vdc = 0; self.dsv = volume
        elif self.lv[-1] < self.lv[-2]: self.vuc = 0; self.vdc += 1; self.usv = volume

        pd = self.lp[-1] - self.lp[-2]  # price delta
        vd = self.lv[-1] - self.lv[-2]  # volume delta

        # ppd = (self.lp[-1] - self.lp[0])/self.lp[0]  # price percent delta
        ppd = 0
        if len(self.lp) >= 10:
            ppd = 1.0
            for x in range(9):
                ppd *= 1.0 + (self.lp[-10+x+1] - self.lp[-10+x])/self.lp[-10+x]
            ppd -= 1.0

        ap = 0  # average buy price
        if len(self.lb) > 0:
            cost_sum = 0
            cnt_sum = 0
            for x in self.lb:
                cost_sum += x['cost']
                cnt_sum += x['cnt']
            ap = cost_sum/cnt_sum

        return True, date, price, volume, pd, vd, self.puc, self.pdc, self.vuc, self.vdc, self.usp, self.dsp, self.usv, self.dsv, ppd, ap

    def clear(self):
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

    def record_buy(self, cost, cnt):
        record = {}
        record['cost'] = cost
        record['cnt'] = cnt
        self.lb.append(record)

    def clear_buy_record(self):
        self.lb = []

def one_turn():
    list_monitor = [Monitor('XRP'),Monitor('BTC'),Monitor('LTC'),Monitor('QTUM'),Monitor('ZEC')]
    # BTC: 0.001 | ETH: 0.01 | DASH: 0.01 | LTC: 0.1 | ETC: 0.1 | XRP: 10 | BCH: 0.001 | XMR: 0.01 | ZEC: 0.001 | QTUM: 0.1 | BTG: 0.01 | EOS: 1
    while True:
        for monitor in list_monitor:
            ch, d, p, v, pd, vd, puc, pdc, vuc, vdc, usp, dsp, usv, dsv, ppd, ap = monitor.get()

            if ch:  # flag_change
                lc = ap * (1.0 - losscut)
                gc = ap * (1.0 + gaincut)

                print(d, monitor.ticker, "￦{:,}({:>+2.2f}%)".format(int(p), ppd*100), "\t\t\tV{:<5,.0f}({:>+4,.0f})".format(v, vd), "ap: {:.4f}".format(ap), "gc: {:.4f}".format(gc), "lc: {:.4f}".format(lc))
                if ap > 0:
                    if p <= lc:
                        print('stoploss!')
                        sell_price, cnt, gain = sell_all(self.ticker)
                        print('loss_unit_price', ap-lc, 'cnt', cnt, 'total loss', cnt * (ap-lc))
                        monitor.clear_buy_record()
                        continue
                    if p >= gc:
                        print('gain cut!!')
                        sell_price, cnt, gain = sell_all(self.ticker)
                        print('gain_unit_price', gc-ap, 'cnt', cnt, 'total gain', cnt * (gc-ap))
                        monitor.clear_buy_record()
                        continue


                if ppd >= buy_delta:
                    price, cnt, cost = buy_some(monitor.ticker, unit_money)
                    print('result', 'unit_price', price, 'buy_cnt', cnt, 'cost', cost, 'real_unit_price', cost / cnt)
                    monitor.record_buy(cost, cnt)
                    monitor.clear()
                    continue

            else:
                continue

while True:
    krw = get_krw_info()
    krw = ', '.join('{{{}: ￦{:,.0f}}}'.format(k,v) for k,v in krw.items())
    print('KRW info', krw)
    coins = get_balance_all(False)
    coins = ', '.join("{{{}: {:,.4f}}}".format(k,v) for k,v in coins.items())
    print('my coins', coins)

    one_turn()
