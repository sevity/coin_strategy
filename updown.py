from coin import *
import time
from datetime import datetime



# param #######################################################################
THRESHOLD = 100
COOL_TIME = 60 * 10
TRADE_CNT = 0.5
FEE = 0.0015
###############################################################################




bt = Coin('bithumb')

avg_gap = 0
skip_turn = 10
gap_sum = 0
cnt = 0

def check_account():
    a = bt.get_krw_info()
    b = bt.get_balance_all()
    money = float(a['free'])
    coin = float(b['EOS'])
    print('KRW info', a)
    print('my coins', b)
    return money, coin


while True:
    money, coin = check_account()
    try:
        a = bt.get_price('EOS', 'KRW')
    except Exception as e:
        print('err', e)
        time.sleep(1)
        continue

    print(datetime.now().strftime("%m-%d %H:%M:%S"), 'EOS price..', 'bithumb', a)
    
    # money, coin = check_account()
    # if money - FEE * TRADE_CNT >= a * 1.1: #need to fix

    bt.limit_buy('EOS', a - THRESHOLD, TRADE_CNT)
    bt.limit_sell('EOS', a + THRESHOLD, TRADE_CNT)

    time.sleep(COOL_TIME)
