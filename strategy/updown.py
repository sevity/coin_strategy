import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from coin import *
import time
from datetime import datetime



# param #######################################################################
THRESHOLD = 200
COOL_TIME = 60 * 10
TRADE_CNT = 1
FEE = 0.002
###############################################################################

f = open("../upbit_api_key.txt", 'r')
access_key = f.readline().rstrip()
secret_key = f.readline().rstrip()
f.close()
coin = Coin('upbit',access_key,secret_key)

avg_gap = 0
skip_turn = 10
gap_sum = 0
cnt = 0

while True:
    try:
        a = coin.get_price('EOS', 'KRW')
        b = coin.get_asset_info('KRW')
        c = coin.get_asset_info('EOS')
    except Exception as e:
        print('err', e)
        time.sleep(1)
        continue

    print('KRW..', b)
    print('EOS..', c)
    print(datetime.now().strftime("%m-%d %H:%M:%S"), 'EOS price..', 'bithumb', a)
    a = round(a, -1) # minimum 10 won
    
    if b['free'] > (a - THRESHOLD) * TRADE_CNT:
        pass
    else:
        print('not enough KRW!')
        time.sleep(COOL_TIME)
        continue

    if c['free'] > TRADE_CNT:
        bt.limit_buy('EOS', a - THRESHOLD, TRADE_CNT)
        bt.limit_sell('EOS', a + THRESHOLD, TRADE_CNT)
    else:
        print('not enough EOS!')
        time.sleep(COOL_TIME)

    time.sleep(COOL_TIME)
