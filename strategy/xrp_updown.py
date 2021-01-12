import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from coin import *
import time
import copy
import telegram
from sty import fg, bg, ef, rs
from datetime import datetime, timezone, timedelta

# 설명 ########################################################################
# updown.py의 XRP버전
# param #######################################################################
UPDOWN_TICK = 5  # 현재 유리호가 보다 몇틱 벌려서 내는지(2이면 상하방 2호가)
BETTING = 6000 # 한번에 거는 돈의 크기
COOL_TIME = 60 * 15  # 초단위
TIMEOUT_DAYS = 3
###############################################################################
FEE = 0.0005  # 수수료는 0.05%
###############################################################################
f = open("../upbit_api_key.txt", 'r')
access_key = f.readline().rstrip()
secret_key = f.readline().rstrip()
f.close()
coin = Coin('upbit',access_key,secret_key)
token = '1267448247:AAE7QjHpSijbtNS9_dnaLm6zfUGX3FhmF78'
bot = telegram.Bot(token=token)
def send_telegram(msg):
    # print(msg)
    try:
        bot.sendMessage(chat_id=170583240, text=msg)
    except:
        pass

def cancel_pending_bids(bLog=True):
    l = coin.get_live_orders('XRP', 'KRW')
    if bLog: print(' cancel pending bids..')
    for (oid, askbid, price, cnt, odt) in l:
        if askbid == 'ask':
            continue
        r = coin.cancel(oid, False)

def cancel_pending_asks(bLog=True):
    l = coin.get_live_orders('XRP', 'KRW')
    if bLog:print(' cancel pending asks..')
    for (oid, askbid, price, cnt, odt) in l:
        if askbid == 'bid':
            continue
        r = coin.cancel(oid)


def check_pending_ask(bLog=True):
    l = coin.get_live_orders('XRP', 'KRW')
    if bLog:print(' check pending asks..')
    for (oid, askbid, price, cnt, odt) in l:
        if askbid == 'bid':
            continue
        return True
    return False

avg_gap = 0
skip_turn = 10
gap_sum = 0
cnt = 0
total_gain = 0
bids = {}
asks = {}
def buy(price, volume):
    trade_amount = price * volume / (1.0 + FEE)
    new_volume = trade_amount / price
    oid = coin.limit_buy('XRP', price, new_volume)
    bids[oid] = (price, volume)
def sell(price, volume):
    trade_amount = price * volume / (1.0 - FEE)
    new_volume = trade_amount / price
    oid = coin.limit_sell('XRP', price, new_volume)
    asks[oid] = (price, volume)
while True:
    try:
        a = coin.get_price('XRP', 'KRW')
        money = coin.get_asset_info('KRW')
        xrp = coin.get_asset_info('XRP')
    except Exception as e:
        print('err', e)
        time.sleep(1)
        continue

    print('KRW..', money)
    # money['free'] = int(money['free'] - 3000000)
    print('XRP..', xrp)
    print(datetime.now().strftime("%m-%d %H:%M:%S"), 'XRP price..', 'upbit', '{:,}'.format(a))

    ask_price = round(a + UPDOWN_TICK, 0); ask_cnt = float(BETTING) / ask_price 
    bid_price = round(a - UPDOWN_TICK, 0); bid_cnt = float(BETTING) / bid_price
    if money['free'] > bid_price * bid_cnt :
        if 'free' in xrp and xrp['free'] > ask_cnt:
            buy(bid_price, bid_cnt)
            sell(ask_price, ask_cnt)
        else:
            print('!!!!!!!!!!!! not enough XRP!')
            new_bid_price = round(a - UPDOWN_TICK/2, 0); new_bid_cnt = float(BETTING) / new_bid_price / 3
            buy(new_bid_price, new_bid_cnt)

    else:
        print('!!!!!!!!!!!! not enough KRW!')
        if xrp['free'] > ask_cnt:
            new_ask_price = round(a + UPDOWN_TICK/2, 0); new_ask_cnt = float(BETTING) / new_ask_price / 3
            sell(new_ask_price, new_ask_cnt)

    try:
        # 고착화를 막기위해 일정기간 이상의 미체결 주문 청산
        print("cancel pending orders...")
        l = coin.get_live_orders('XRP', 'KRW')
        KST = timezone(timedelta(hours=9))
        print("{} orders alive...".format(len(l)))
        for (oid, askbid, price, cnt, odt) in l:
            now = datetime.now(KST)
            date_diff = (now-odt).days
            hour_diff = int(date_diff*24 + (now-odt).seconds/3600)
            print(oid, askbid, '{:,} {:.2f}'.format(int(float(price)), float(cnt)), odt, hour_diff, 'hours')
            if date_diff >= TIMEOUT_DAYS:
            #if hour_diff >= 33:
                print("cancel order.. {}".format(oid))
                r = coin.cancel(oid)
    except Exception as e:
        print('err', e)

    # check bid fill
    bps = copy.deepcopy(bids)
    aps = copy.deepcopy(asks)
    l = coin.get_live_orders('XRP', 'KRW')
    for (oid, askbid, price, cnt, odt) in l:
        if askbid=='bid' and oid in bps:
            del bps[oid]
        elif askbid=='ask' and oid in aps:
            del aps[oid]

    # 체결된 ask/bid에 대해 수익계산 
    for oid, (price, volume) in bps.items():
        gain = int(float(price) * float(volume))
        print(fg.red + '! bid filled({:,}). '.format(price)+fg.green+'gain will be: -{:.8f}({:,}KRW)'.
			format(volume, gain)+ fg.rs)
        total_gain -= gain
        del bids[oid]
    for oid, (price, volume) in aps.items():
        gain = int(float(price) * float(volume))
        print(fg.blue + '! ask filled({:,}). '.format(price)+fg.green+'gain will be: {:.8f}({:,}KRW)'.
			format(volume, gain)+ fg.rs)
        total_gain += gain
        del asks[oid]
    a = coin.get_asset_info('XRP')
    holding_value = 0
    if 'free' in a:
        v = float(a['total'])*coin.get_price('XRP', 'KRW')
        # print(a['total'], coin.get_price('XRP', 'KRW'))
        holding_value = v
        # print('holding XRP value:', v)

    print(fg.li_yellow + 'current RETURN: holding value:{:,} + trade value:{:,} = {:,}KRW'.
        format(int(holding_value), int(total_gain), int(holding_value + total_gain)) + fg.rs)
    send_telegram('[XRP] current RETURN: holding value:{:,} + trade value:{:,} = {:,}KRW'.
        format(int(holding_value), int(total_gain), int(holding_value + total_gain)))
    time.sleep(COOL_TIME)
