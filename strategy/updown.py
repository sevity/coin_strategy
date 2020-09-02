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
BTC_LOCK = 0.1  # 최소 10%는 항상 BTC로 보유
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
    btc_ratio = btc['total']*a / (money['total']+btc['total']*a)
    print('BTC to KRW ratio..', '{:.4f}'.format(btc_ratio))
    if btc_ratio < BTC_LOCK: print('!!!!! less than BTC LOCK! {}'.format(BTC_LOCK))
    print(datetime.now().strftime("%m-%d %H:%M:%S"), 'BTC price..', 'upbit', '{:,}'.format(a))
    #a = round(a, -1) # minimum 10 won

    ask_price = round(a + a * UPDOWN, -3); ask_cnt = float(BETTING) / ask_price 
    bid_price = round(a - a * UPDOWN, -3); bid_cnt = float(BETTING) / bid_price
    if money['free'] > bid_price * bid_cnt :
        if btc['free'] > ask_cnt and btc_ratio > BTC_LOCK:
            coin.limit_buy('BTC', bid_price, bid_cnt)
            coin.limit_sell('BTC', ask_price, ask_cnt)
        else:
            print('!!!!!!!!!!!! not enough BTC! or BTC LOCK!')
            new_bid_price = round(a - a * UPDOWN * 0.5, -3); new_bid_cnt = float(BETTING) / new_bid_price / 5
            coin.limit_buy('BTC', new_bid_price, new_bid_cnt)

    else:
        print('!!!!!!!!!!!! not enough KRW!')
        if btc['free'] > ask_cnt and btc_ratio > BTC_LOCK:
            new_ask_price = round(a + a * UPDOWN * 0.5, -3); new_ask_cnt = float(BETTING) / new_ask_price / 5
            coin.limit_sell('BTC', new_ask_price, new_ask_cnt)

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
                # 나중에 bid만으로 KRW부족이 발생해서, 오래된건 위치조정하지 말고 그냥 버리는걸로 해본다. > 근데 KRW부족이 peak eater 때문이어서 원복 ㅋ
                if askbid=='ask': coin.limit_sell('BTC', ask_price, ask_cnt)
                else: coin.limit_buy('BTC', bid_price, bid_cnt)

    except Exception as e:
        print('err', e)

    time.sleep(COOL_TIME)
