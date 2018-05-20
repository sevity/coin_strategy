import time
from datetime import datetime
from coin import *



# param #######################################################################
THRESHOLD = 200
CUT_OFF = 100
WAIT_TIME_SEC = 60 * 10
COOL_TIME_SEC = 60 * 3
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


def Go(sell_price, sell_cnt, wait_sec):
    cnt = wait_sec
    avg_sell_price = 1.0 * sell_price / sell_cnt
    print('Go! avg_sell_price..', avg_sell_price, 'sell_cnt..', sell_cnt, 'wait_sec..', wait_sec)
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
            buy_try = round(1.0 * (sell_cnt * (1 - FEE) * sell_price) / price, 4)
            bt.market_buy('EOS', buy_try * (1.0 + 0))[0]
            return
        if price >= sell_price + CUT_OFF:
            print('cutoff fail!')

            sell_more_price = bt.market_sell('EOS', sell_cnt)[0]
            Go(1.0 * (sell_price + sell_more_price) / 2, sell_cnt * 2, wait_sec * 2)
            return

        time.sleep(1)
        cnt -= 1
        if cnt == 0:
            print('timeout fail!')

            if price <= sell_price - 50:
                buy_try = round(1.0 * (sell_cnt * (1 - FEE) * sell_price) / price, 4)
                bt.market_buy('EOS', buy_try * (1.0 + 0))[0]
            else:
                sell_more_price = bt.market_sell('EOS', sell_cnt)[0]
                Go(1.0 * (sell_price + sell_more_price) / 2, sell_cnt * 2, wait_sec * 2)
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
    Go(sell_price, TRADE_CNT, WAIT_TIME_SEC)
    print('wating cool time...', COOL_TIME_SEC)
    time.sleep(COOL_TIME_SEC)

