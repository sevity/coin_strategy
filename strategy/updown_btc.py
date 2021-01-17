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

# 설명 ########################################################################
# updown.py의 BTC시장 알트 버전
# param #######################################################################
# TICKER = 'EMC2'
# UPDOWN_TICK = 0.00000025  # 현재 유리호가 보다 몇틱 벌려서 내는지(2이면 상하방 2호가)
UPDOWN = {
    'DOT': 0.00002000, 
    'XRP': 0.00000020}
BETTING = 0.0006 # 한번에 거는 돈의 크기(2.2만원 정도 된다 ㄷ)
COOL_TIME = 60 * 60  # 초단위
TIMEOUT_DAYS = 5
###############################################################################
FEE = 0.0025  # 수수료는 0.25%
parser = argparse.ArgumentParser(description='updown strategy for BTC market')
parser.add_argument('--ticker', '-t', required=True, help='coin name ex)XRP')
args = parser.parse_args()
TICKER = args.ticker.upper()
UPDOWN_TICK = UPDOWN[TICKER]
###############################################################################
print('ticker:{}, updown_tick:{:.8f}'.format(TICKER, UPDOWN_TICK))
assert(UPDOWN_TICK > 0)

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
    l = coin.get_live_orders(TICKER, 'BTC')
    if bLog: print(' cancel pending bids..')
    for (oid, askbid, price, cnt, odt) in l:
        if askbid == 'ask':
            continue
        r = coin.cancel(oid, False)

def cancel_pending_asks(bLog=True):
    l = coin.get_live_orders(TICKER, 'BTC')
    if bLog:print(' cancel pending asks..')
    for (oid, askbid, price, cnt, odt) in l:
        if askbid == 'bid':
            continue
        r = coin.cancel(oid)


def check_pending_ask(bLog=True):
    l = coin.get_live_orders(TICKER, 'BTC')
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
bids = {}
asks = {}
def buy(price, volume):
    trade_amount = price * volume / (1.0 + FEE)  # 거래금액
    new_volume = trade_amount / price
    oid = coin.limit_buy_btc(TICKER, price, new_volume)
    time.sleep(1)
    l = coin.get_live_orders(TICKER, 'BTC')
    for (oid_, askbid, price, cnt, odt) in l:
        if oid_ == oid:
            bids[oid] = (price, cnt)
            break
    if oid in bids:
        return oid, bids[oid][1]
    return (None, None)
        
def sell(price, volume):
    oid = coin.limit_sell_btc(TICKER, price, volume)
    time.sleep(1)
    l = coin.get_live_orders(TICKER, 'BTC')
    for (oid_, askbid, price, cnt, odt) in l:
        if oid_ == oid:
            asks[oid] = (price, volume)
            print('sell debug.. cnt:{}, new_volume:{}'.format(cnt, volume))
            break

# 실행전 걸려있는 미체결 주문들 등록
l = coin.get_live_orders(TICKER, 'BTC')
for (oid_, askbid, price, cnt, odt) in l:
    if askbid=='bid':
        bids[oid_] = (price, cnt)
    else:
        asks[oid_] = (price, cnt)

    
holding_value = 0.0
trade_delta = None
while True:
    try:
        a = coin.get_price(TICKER, 'BTC')
        money = coin.get_asset_info('BTC')
        ticker = coin.get_asset_info(TICKER)
    except Exception as e:
        print('err', e)
        time.sleep(1)
        continue

    print('BTC..', money)
    # money['free'] = int(money['free'] - 3000000)
    print('{}..'.format(TICKER), ticker)
    print(datetime.now().strftime("%m-%d %H:%M:%S"), '{} price..'.format(TICKER), 'upbit', '{:.8f}'.format(a))

    ask_price = (a + UPDOWN_TICK); ask_cnt = float(BETTING) / ask_price 
    bid_price = (a - UPDOWN_TICK); bid_cnt = float(BETTING) / bid_price
    if money['free'] > bid_price * bid_cnt :
        if 'free' in ticker and ticker['free'] > ask_cnt:
            oid, new_cnt = buy(bid_price, bid_cnt)
            sell(ask_price, new_cnt)
        else:
            print('!!!!!!!!!!!! not enough {}!'.format(TICKER))
            # new_bid_price = round(a - UPDOWN_TICK/2, 0); new_bid_cnt = float(BETTING) / new_bid_price / 3
            new_bid_price = bid_price
            new_bid_cnt = bid_cnt
            buy(new_bid_price, new_bid_cnt)

    else:
        print('!!!!!!!!!!!! not enough BTC!')
        new_ask_price = (a + UPDOWN_TICK/2); new_ask_cnt = float(BETTING) / new_ask_price / 3
        new_ask_price = ask_price
        new_ask_cnt = ask_cnt
        if 'free' in ticker and ticker['free'] > new_ask_cnt:
            sell(new_ask_price, new_ask_cnt)

    try:
        # 고착화를 막기위해 일정기간 이상의 미체결 주문 청산
        print("cancel pending orders...")
        l = coin.get_live_orders(TICKER, 'BTC')
        KST = timezone(timedelta(hours=9))
        print("{} orders alive...".format(len(l)))
        for (oid, askbid, price, cnt, odt) in l:
            now = datetime.now(KST)
            date_diff = (now-odt).days
            hour_diff = int(date_diff*24 + (now-odt).seconds/3600)
            print(oid.split('-')[0], askbid, 
                '{:.8f}BTC {:.8f}cnt'.format(float(price), float(cnt)), odt, hour_diff, 'hours')
            if date_diff >= TIMEOUT_DAYS:
            #if hour_diff >= 33:
                print("cancel order.. {}".format(oid))
                r = coin.cancel(oid)
    except Exception as e:
        print('err', e)

    # check bid fill
    bps = copy.deepcopy(bids)
    aps = copy.deepcopy(asks)
    l = coin.get_live_orders(TICKER, 'BTC')
    for (oid, askbid, price, cnt, odt) in l:
        if askbid=='bid' and oid in bps:
            del bps[oid]
        elif askbid=='ask' and oid in aps:
            del aps[oid]

    a = coin.get_asset_info(TICKER)
    p = coin.get_price(TICKER, 'BTC')
    btckrw = coin.get_price('BTC', 'KRW')
    if trade_delta is None:
        if 'total' in a:
            v = float(a['total'])*p
            trade_delta = -v
        else:
            trade_delta = 0
    # 체결된 ask/bid에 대해 수익계산 
    for oid, (price, volume) in bps.items():
        delta = (float(price) * float(volume)) * (1.0 + FEE)
        print(fg.red + 'bid filled({:.8f}BTC, {:,}KRW). '.format(price, int(price*btckrw))+fg.green+
            'trade delta: -{:.8f}cnt({:.8f}BTC)'.
			format(float(volume), float(delta))+ fg.rs + ' ' + oid.split('-')[0])
        trade_delta -= delta 
        del bids[oid]
    for oid, (price, volume) in aps.items():
        delta = (float(price) * float(volume)) * (1.0 - FEE)
        print(fg.blue + 'ask filled({:.8f}BTC, {:,}KRW). '.format(price, int(price*btckrw))+fg.green+
            'trade delta: -{:.8f}cnt({:.8f}BTC)'.
			format(float(volume), float(delta))+ fg.rs + ' ' + oid.split('-')[0])
        trade_delta += delta 
        del asks[oid]
    if 'total' in a:
        v = float(a['total'])*p
        print('debug..', a, p, v)
        # print(a['total'], coin.get_price(TICKER, 'BTC'))
        holding_value = v
    txt = 'RETURN: holding value:{:.8f}({:,}KRW) + trade value:{:.8f}({:,}KRW) = {:.8f}BTC({:,}KRW)'.format(
        (holding_value), int(btckrw*holding_value), (trade_delta), int(btckrw*trade_delta), 
        (holding_value + trade_delta), int(btckrw * (holding_value + trade_delta)))

    print(fg.li_yellow + txt + fg.rs)
    send_telegram('[{}-BTC] '.format(TICKER)+txt)
    time.sleep(COOL_TIME)
