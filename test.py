from coin import *
import time
from datetime import datetime



# param #######################################################################
THRESHOLD = 80
COOL_TIME = 10
TRADE_CNT = 1
FEE = 0.0015
###############################################################################




bt = Coin('bithumb')
bn = Coin('binance')

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

money, coin = check_account()
while True:
    try:
        a = bt.get_price('EOS', 'KRW')
        b = bn.get_price('EOS', 'BTC')
        c = bt.get_price('BTC', 'KRW')
    except Exception as e:
        print('err', e)
        time.sleep(1)
        continue
    gap = b*c-a
    gap_sum += gap
    cnt += 1
    avg_gap = gap_sum / cnt
    adj_gap = gap - avg_gap

    print(datetime.now().strftime("%m-%d %H:%M:%S"), 'EOS price..', 'bithumb', a, 'binance', b*c, 'gap', gap, 'avg_gap', avg_gap, 'adj_gap', adj_gap)
    if skip_turn <= 0:
        if adj_gap >= THRESHOLD:
            if money - FEE * TRADE_CNT >= a * 1.1: #need to fix
                bt.market_buy('EOS', TRADE_CNT)
                skip_turn = COOL_TIME
                money, coin = check_account()
            else:
                print("not enough money!")
        elif adj_gap <= -THRESHOLD:
            if coin - FEE * TRADE_CNT >= TRADE_CNT:
                bt.market_sell('EOS', TRADE_CNT)
                skip_turn = COOL_TIME
                money, coin = check_account()
            else:
                print("not enough coin!")
    else:
        skip_turn -= 1
        print('skip...')
    time.sleep(1)
