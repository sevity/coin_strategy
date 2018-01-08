#! /usr/bin/env python
from sevity_coin_api import *

# options ########################################
ticker = 'XRP'  # (BTC, ETH, DASH, LTC, ETC, XRP, BCH, XMR, ZEC, QTUM, BTG, EOS)
askbid = 'bid'
price = 2200
cnt = 50        # min cnt : (BTC: 0.001 | ETH: 0.01 | DASH: 0.01 | LTC: 0.1 | ETC: 0.1 | XRP: 10 | BCH: 0.001 | XMR: 0.01 | ZEC: 0.001 | QTUM: 0.1 | BTG: 0.01 | EOS: 1)
##################################################
#order_new('EOS', 10700, 100, 'bid')
#order_new('XRP', 3520, 43, 'bid')
#while True:
    #market_buy('XRP', 500)
#market_sell('EOS', 1)

#market_buy('EOS', 100)
#order_new('QTUM', 75920, 5.977, 'ask')
#buy_all('EOS', False)

#price, cnt, cost = buy_some('XRP', 40000)
#print('result', 'unit_price', price, 'buy_cnt', cnt, 'cost', cost)

#print(get_account_info('XRP'))
#sell_all('XRP')

#print(rate_change(10364,10364), rate_change(1818100, 1856700))
print(rate_change(70000,88000))
print(rate_change(440,572))
print(rate_change(2396,2657))
print(rate_change(91,154))
sys.exit()