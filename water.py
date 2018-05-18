import time
from datetime import datetime
from coin import *



# param #######################################################################
THRESHOLD = 200
CUT_OFF = 100
WAIT_TIME_SEC = 60 * 60 * 1
COOL_TIME_SEC = 60 * 10
TRADE_CNT = 1
FEE = 0.00158
###############################################################################




bt = Coin('bithumb')


def check_account():
    a = bt.get_krw_info()
    b = bt.get_balance_all()
    money = float(a['free'])
    coin = float(b['EOS'])
    print('KRW info', a)
    print('my coins', b)
    return money, coin

money, coin = check_account()
rcnt = [0, 0]
origin_cnt = TRADE_CNT
origin_wait = WAIT_TIME_SEC


def Go(sell_price):
    global TRADE_CNT
    global WAIT_TIME_SEC
    cnt = WAIT_TIME_SEC
    while True:
        try:
            price = bt.get_price('EOS', 'KRW')
        except Exception as e:
            print('err', e)
            time.sleep(1)
            continue

        print(datetime.now().strftime("%m-%d %H:%M:%S"), 'sell price..', sell_price, 'cur price..', price, 'delta..', price - sell_price, 'remain sec..', cnt)

        if price <= sell_price - THRESHOLD:
            print('success!')
            rcnt[0] += 1
            buy_try = round(1.0 * (TRADE_CNT * (1 - FEE) * sell_price) / price, 4)
            bt.market_buy('EOS', buy_try * (1.0 + 0))[0]
            TRADE_CNT = origin_cnt
            WAIT_TIME_SEC = origin_wait
            return
        if price >= sell_price + CUT_OFF:
            print('cutoff fail!')
            rcnt[1] += 1
            buy_try = round(1.0 * (TRADE_CNT * (1 - FEE) * sell_price) / price, 4)
            bt.market_buy('EOS', buy_try * (1.0 + 0))[0]
            TRADE_CNT *= 2
            WAIT_TIME_SEC *= 2
            return

        time.sleep(1)
        cnt -= 1
        if cnt == 0:
            print('timeout fail!')
            rcnt[1] += 1
            buy_try = round(1.0 * (TRADE_CNT * (1 - FEE) * sell_price) / price, 4)
            bt.market_buy('EOS', buy_try * (1.0 + 0))[0]

            if price <= sell_price - 50:
                TRADE_CNT = origin_cnt
                WAIT_TIME_SEC = origin_wait
            else:
                TRADE_CNT *= 1.5
                WAIT_TIME_SEC *= 1.5
            return

while True:
    try:
        price = bt.get_price('EOS', 'KRW')
    except Exception as e:
        print('err', e)
        time.sleep(1)
        continue
    
    sell_price = bt.market_sell('EOS', TRADE_CNT)[0]
    buy_cnt = sell_price
    Go(sell_price)
    print('win rate..', 1.0 * rcnt[0] / (rcnt[0] + rcnt[1]), 'win..', rcnt[0], 'lose..', rcnt[1])
    print('wating cool time...', COOL_TIME_SEC)
    time.sleep(COOL_TIME_SEC)

