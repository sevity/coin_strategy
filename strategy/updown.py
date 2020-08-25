import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from coin import *
import time
from datetime import datetime, timezone, timedelta

# param #######################################################################
FEE = 0.0005  # 수수료는 0.05%
UPDOWN = 0.01  # 2% 상하로 걸어놓기..  성공하면 1.9%먹는 게임
BETTING = 100000  # 한번에 거는 돈의 크기
COOL_TIME = 60 * 30  # 초단위
TIMEOUT_DAYS = 3
###############################################################################
# 상하방 양쪽으로 걸어서 박스권에서 왔다갔다 할경우 소액씩 계속 먹는 전략

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
        a = coin.get_price('BTC', 'KRW')
        money = coin.get_asset_info('KRW')
        btc = coin.get_asset_info('BTC')
    except Exception as e:
        print('err', e)
        time.sleep(1)
        continue

    print('KRW..', money)
    print('BTC..', btc)
    print('free BTC in KRW..', '{:,}'.format(int(btc['free']*a)))
    print('total money..', '{:,}'.format(int(money['total'])+int(btc['total']*a)))
    print(datetime.now().strftime("%m-%d %H:%M:%S"), 'BTC price..', 'upbit', '{:,}'.format(a))
    #a = round(a, -1) # minimum 10 won

    ask_price = a + a * UPDOWN;ask_price = round(ask_price, -3) # minimum 1000 won
    bid_price = a - a * UPDOWN;bid_price = round(bid_price, -3) # minimum 1000 won
    ask_cnt = float(BETTING) / ask_price 
    bid_cnt = float(BETTING) / bid_price
    if money['free'] > bid_price * bid_cnt :
        if btc['free'] > ask_cnt:
            print('order_new...', 'BTC', 'price:{:,.2f}'.format(bid_price), 'cnt:{:,.4f}'.format(bid_cnt), 'bid')
            oid1 = coin.limit_buy('BTC', bid_price, bid_cnt)
            print('order_new...', 'BTC', 'price:{:,.2f}'.format(ask_price), 'cnt:{:,.4f}'.format(ask_cnt), 'ask')
            oid2 = coin.limit_sell('BTC', ask_price, ask_cnt)
            print("oid:", {oid1, oid2})
        else:
            print('not enough BTC!')
    else:
        print('not enough KRW!')

    try:
        # 고착화를 막기위해 일정기간 이상의 미체결 주문 청산
        print("cancel pending orders...")
        l = coin.get_live_orders('BTC', 'KRW')
        KST = timezone(timedelta(hours=9))
        print("{} orders alive...".format(len(l)))
        for (oid, askbid, price, cnt, odt) in l:
            now = datetime.now(KST)
            date_diff = (now-odt).days
            hour_diff = int(date_diff*24 + (now-odt).seconds/3600)
            print(oid, askbid, '{:,} {:.4f}'.format(int(float(price)), float(cnt)), odt, hour_diff, 'hours')
            if date_diff >= TIMEOUT_DAYS:
            #if hour_diff >= 33:
                print("cancel order.. {}".format(oid))
                r = coin.cancel(oid)
                if askbid=='ask':
                    oid2 = coin.limit_sell('BTC', ask_price, ask_cnt)
                    print("oid:", oid2)
                else:
                    oid1 = coin.limit_buy('BTC', bid_price, bid_cnt)
                    print("oid:", oid1)

    except Exception as e:
        print('err', e)

    time.sleep(COOL_TIME)
