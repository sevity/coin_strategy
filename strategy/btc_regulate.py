import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from coin import *
import time
import copy
import telegram
from sty import fg, bg, ef, rs
from datetime import datetime, timezone, timedelta
import argparse
import math

# 설명 ########################################################################
# KRW - BTC의 비율을 항상 1:10으로 맞춰준다.
# param #######################################################################
TARGET_KRW_BTC_RATIO = 0.1
UPDOWN_PERCENT = 0.008  # 기본 상하방 0.8%, 성공하면 수수료 제외 1.5% 먹음
BETTING_KRW = 30000   # 한번에 거는 돈의 크기
COOL_TIME = 60 * 5  # 초단위
###############################################################################
TICKER = 'BTC'
FEE = 0.0025  # 수수료는 0.25%
TIMEOUT_DAYS = 1  # temp
###############################################################################
f = open("../upbit_api_key.txt", 'r')
access_key = f.readline().rstrip()
secret_key = f.readline().rstrip()
f.close()
coin = Coin('upbit',access_key,secret_key)

print('UPDOWN_PERCENT:{}, BETTING_KRW:{:,}KRW, COOL_TIME:{}sec'.
    format(UPDOWN_PERCENT, BETTING_KRW, COOL_TIME))
token = '1267448247:AAE7QjHpSijbtNS9_dnaLm6zfUGX3FhmF78'
bot = telegram.Bot(token=token)
def send_telegram(msg):
    # print(msg)
    try:
        bot.sendMessage(chat_id=170583240, text=msg)
    except:
        pass
def fsame(a, b, diff=0.0001):  # default: 0.01%이내로 같으면 true 리턴
    a = float(a)
    b = float(b)
    if abs(a-b)<diff:
        return True
    return False


while True:
    try:
        btc = coin.get_asset_info(TICKER)
        krw = coin.get_asset_info('KRW')
        eth = coin.get_asset_info('ETH')
        btc_price = coin.get_price(TICKER, 'KRW')
        eth_price = coin.get_price('ETH', 'KRW')
    except Exception as e:
        print('err', e)
        time.sleep(1)
        continue

    print('\n\nBTC..', btc)
    print('KRW..', krw)
    print(fg.magenta + datetime.now().strftime("%m-%d %H:%M:%S") + fg.rs + ' btc price:{:,}KRW'.
        format(int(btc_price)))

    krw_ratio = krw['total'] / (krw['total'] + btc['total'] * btc_price + eth['total'] * eth_price)
    # krw_ratio = 0.2
    UP_DELTA = UPDOWN_PERCENT
    DOWN_DELTA = UPDOWN_PERCENT
    UP_RATIO = 1.0
    DOWN_RATIO = 1.0
    print(fg.yellow + 'TARGET_KRW_BTC_RATIO:{:.4f}, current krw_ratio:{:.4f}'.
        format(TARGET_KRW_BTC_RATIO, krw_ratio) + fg.rs)
    if krw_ratio < TARGET_KRW_BTC_RATIO:
        # 돈부족 상황
        print(fg.blue + 'KRW shortage! strong BTC ask' + fg.rs)
        DOWN_RATIO = (TARGET_KRW_BTC_RATIO / krw_ratio)
        DOWN_RATIO = min(DOWN_RATIO, 10)
        DOWN_DELTA = UP_DELTA * DOWN_RATIO
        DOWN_DELTA = min(DOWN_DELTA, 10)
        UP_DELTA /= 4
        DOWN_DELTA = 0
    else:
        print(fg.red + 'KRW surplus! strong BTC bid' + fg.rs)
        UP_RATIO = krw_ratio / TARGET_KRW_BTC_RATIO 
        UP_RATIO = min(UP_RATIO, 10)
        UP_DELTA = UP_DELTA * UP_RATIO 
        UP_DELTA = min(UP_DELTA, 10)
        DOWN_DELTA /= 4
        UP_DELTA = 0

    print('UP_DELTA:{:.4f}, DOWN_DELTA:{:.4f}, UP_RATIO:{:.4f}, DOWN_RATIO:{:.4f}'.
        format(UP_DELTA, DOWN_DELTA, UP_RATIO, DOWN_RATIO))

    if UP_DELTA > 0:
        ask_price = (btc_price + btc_price * UP_DELTA); ask_cnt = float(BETTING_KRW * DOWN_RATIO) / ask_price 
        coin.limit_sell(TICKER, ask_price, ask_cnt)
    if DOWN_DELTA > 0:
        bid_price = (btc_price - btc_price * DOWN_DELTA);bid_cnt = float(BETTING_KRW * UP_RATIO) / bid_price
        coin.limit_buy(TICKER, bid_price, bid_cnt)
    try:
        # 고착화를 막기위해 일정기간 이상의 미체결 주문 청산
        print("cancel pending orders...")
        l = coin.get_live_orders(TICKER, 'KRW')
        KST = timezone(timedelta(hours=9))
        print("{} orders alive...".format(len(l)))
        for (oid, askbid, price, cnt, odt) in l:
            if price % 100000 == 0: continue  # btc_coin에서 등록된건 넘어간다.
            now = datetime.now(KST)
            date_diff = (now-odt).days
            hour_diff = int(date_diff*24 + (now-odt).seconds/3600)
            print(oid, askbid, '{:,} {:.2f}m'.
                format(int(float(price)), float(cnt)*1000), odt, hour_diff, 'hours')
            if date_diff >= TIMEOUT_DAYS:
            # if hour_diff >= 33:
                print("cancel order.. {}".format(oid))
                r = coin.cancel(oid)

    except Exception as e:
        print('err', e)

    time.sleep(COOL_TIME)
