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
# UPDOWN_DELTA = 0.00000025  # 현재 유리호가 보다 몇틱 벌려서 내는지(2이면 상하방 2호가)
UPDOWN = {
    'DOT':  0.00002000, 
    'XRP':  0.00000030,
    'XLM':  0.00000020,
    'EOS':  0.00000100,
    'TRX':  0.00000003,
    'MANA': 0.00000010,
    'ZIL':  0.00000004,
    'XTZ':  0.00000150,
    'ALGO': 0.00000070,
    'LINK': 0.00000900,
    'EMC2': 0.00000005,
    'BFC':  0.00000003,
    'OMG':  0.00000200,
    'LOOM':  0.00000007,
    }
BETTING = 0.0006 # 한번에 거는 돈의 크기(2.2만원 정도 된다 ㄷ)
COOL_TIME = 60 * 60  # 초단위
TIMEOUT_DAYS = 500  # temp
###############################################################################
FEE = 0.0025  # 수수료는 0.25%
parser = argparse.ArgumentParser(description='updown strategy for BTC market')
parser.add_argument('--ticker', '-t', required=True, help='coin name ex)XRP')
parser.add_argument('--betting', '-b', required=False, default=BETTING, help='betting BTC amount a time')
parser.add_argument('--cooltime', '-c', required=False, default=str(COOL_TIME), 
    help='wait time between orders in sec')
parser.add_argument('--upratio', '-u', required=False, default=1.2)
args = parser.parse_args()
TICKER = args.ticker.upper()
BETTING = float(args.betting)
COOL_TIME = int(eval(args.cooltime))
UPDOWN_DELTA = UPDOWN[TICKER]
UP_RATIO = float(args.upratio)  # 이게 1.0이면 대칭 2.0이면 매도는 2배 비싸게 낸다.
###############################################################################
f = open("../upbit_api_key.txt", 'r')
access_key = f.readline().rstrip()
secret_key = f.readline().rstrip()
f.close()
coin = Coin('upbit',access_key,secret_key)
btckrw = coin.get_price('BTC', 'KRW')
print('ticker:{}, updown_delta:{:.8f}BTC, betting:{:.8f}BTC({:,}KRW), cooltime:{}sec'.
    format(TICKER, UPDOWN_DELTA, BETTING, int(BETTING * btckrw), COOL_TIME))
assert(UPDOWN_DELTA > 0)
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
    l = coin.get_live_orders_ext(TICKER, 'BTC')
    for (oid_, askbid, price, ocnt, rcnt, odt) in l:
        if oid_ == oid:
            bids[oid] = (price, ocnt)
            break
    if oid in bids:
        return oid, bids[oid][1]
    return (None, None)
        
def sell(price, volume):
    oid = coin.limit_sell_btc(TICKER, price, volume)
    time.sleep(1)
    l = coin.get_live_orders_ext(TICKER, 'BTC')
    for (oid_, askbid, price, ocnt, rcnt, odt) in l:
        if oid_ == oid:
            asks[oid] = (price, ocnt)
            assert(fsame(ocnt, volume))
            print('sell debug.. cnt:{}, new_volume:{}'.format(cnt, ocnt))
            break

# 실행전 걸려있는 미체결 주문들 등록
l = coin.get_live_orders_ext(TICKER, 'BTC')
for (oid_, askbid, price, ocnt, rcnt, odt) in l:
    if askbid=='bid':
        bids[oid_] = (price, ocnt)
    else:
        asks[oid_] = (price, ocnt)

    
holding_value = 0.0
trade_delta = None
trade_volume_delta = None
p_partial_volume = -1
partial_delta = None
while True:
    try:
        money = coin.get_asset_info('BTC')
        ticker = coin.get_asset_info(TICKER)
        a = coin.get_asset_info(TICKER)
        p = coin.get_price(TICKER, 'BTC')
        krwp = coin.get_price(TICKER, 'KRW')
        btckrw = coin.get_price('BTC', 'KRW')
    except Exception as e:
        print('err', e)
        time.sleep(1)
        continue

    print('\n\nBTC..', money)
    print('{}..'.format(TICKER), ticker)
    krw_txt = ''
    if krwp is not None:
        krw_txt = 'KRW price: {:,}KRW({:.8f}BTC)'.format(int(krwp), krwp / btckrw)
        p = krwp / btckrw

    print(fg.magenta + datetime.now().strftime("%m-%d %H:%M:%S"), '{} BTC price:'.
        format(TICKER), '{:.8f}BTC({:,}KRW)'.format(p, int(float(p) * float(btckrw))), 
        krw_txt, 'BTC price:{:,}KRW'.format(int(btckrw))
        + fg.rs)

    print(fg.magenta + 'current price: {:.8f}BTC'.format(p) + fg.rs)

    ask_price = (p + UPDOWN_DELTA * UP_RATIO); ask_cnt = float(BETTING) / ask_price 
    bid_price = (p - UPDOWN_DELTA); bid_cnt = float(BETTING) / bid_price
    if money['free'] > bid_price * bid_cnt :
        if 'free' in ticker and ticker['free'] > ask_cnt:
            oid, new_cnt = buy(bid_price, bid_cnt)
            sell(ask_price, new_cnt)
        else:
            print('!!!!!!!!!!!! not enough {}!'.format(TICKER))
            # new_bid_price = round(a - UPDOWN_DELTA/2, 0); new_bid_cnt = float(BETTING) / new_bid_price / 3
            new_bid_price = bid_price
            new_bid_cnt = bid_cnt
            buy(new_bid_price, new_bid_cnt)

    else:
        print('!!!!!!!!!!!! not enough BTC!')
        # new_ask_price = (p + UPDOWN_DELTA/2); new_ask_cnt = float(BETTING) / new_ask_price / 3
        new_ask_price = ask_price
        new_ask_cnt = ask_cnt
        if 'free' in ticker and ticker['free'] > new_ask_cnt:
            sell(new_ask_price, new_ask_cnt)

    try:
        # 고착화를 막기위해 일정기간 이상의 미체결 주문 청산
        print("cancel pending orders...")
        l = coin.get_live_orders_ext(TICKER, 'BTC')
        KST = timezone(timedelta(hours=9))
        print("{} orders alive...".format(len(l)))
        for (oid, askbid, price, ocnt, rcnt, odt) in l:
            now = datetime.now(KST)
            date_diff = (now-odt).days
            hour_diff = int(date_diff*24 + (now-odt).seconds/3600)
            print(oid.split('-')[0], askbid, 
                '{:.8f}BTC {:.8f}{}'.format(float(price), float(ocnt), TICKER), odt, hour_diff, 'hours')
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

    partial_volume = 0
    l = coin.get_live_orders_ext(TICKER, 'BTC')
    for (oid, askbid, price, order_cnt, remain_cnt, odt) in l:
        if fsame(order_cnt, remain_cnt) is False:
            print('  partial debug..', oid, askbid, price, order_cnt, remain_cnt, odt)
            executed_cnt = order_cnt - remain_cnt
            if askbid == 'bid':
                partial_volume -= executed_cnt
            else:
                partial_volume += executed_cnt
    if fsame(p_partial_volume, partial_volume) is False:
        partial_delta = partial_volume * p
        
    p_partial_volume = partial_volume

    if trade_delta is None:
        if 'total' in a:
            v = float(a['total'])*p
            trade_delta = -v - partial_volume * p
            trade_volume_delta = -a['total'] - partial_volume
        else:
            trade_delta = 0
            trade_volume_delta = 0
    # 체결된 ask/bid에 대해 수익계산 
    for oid, (price, volume) in bps.items():
        delta = (float(price) * float(volume)) * (1.0 + FEE)
        print(fg.red + 'bid filled({:.8f}BTC, {:,}KRW). '.format(price, int(price*btckrw))+fg.green+
            'trade delta: +{:.8f}{}(-{:.8f}BTC)'.
			format(float(volume), TICKER, float(delta))+ fg.rs + ' ' + oid.split('-')[0])
        trade_delta -= delta 
        trade_volume_delta -= volume
        del bids[oid]
    for oid, (price, volume) in aps.items():
        delta = (float(price) * float(volume)) * (1.0 - FEE)
        print(fg.blue + 'ask filled({:.8f}BTC, {:,}KRW). '.format(price, int(price*btckrw))+fg.green+
            'trade delta: -{:.8f}{}(+{:.8f}BTC)'.
			format(float(volume), TICKER, float(delta))+ fg.rs + ' ' + oid.split('-')[0])
        trade_delta += delta 
        trade_volume_delta += volume
        del asks[oid]
    if 'total' in a:
        v = float(a['total'])*p
        print('debug..', a, p, v)
        # print(a['total'], coin.get_price(TICKER, 'BTC'))
        holding_value = v
        holding_volume = a['total']
    else:
        holding_value = 0
        holding_volume = 0

    txt = 'R:{:.8f}BTC, {:,}KRW = '.format(
        #holding_volume + trade_volume_delta + partial_volume, TICKER, 
        holding_value + trade_delta + partial_delta, 
        int(btckrw * (holding_value + trade_delta + partial_volume*p)))
    txt += '\nholding: {:.3f}{}({:.8f}BTC, {:,}KRW) +'.format(
        holding_volume, TICKER, holding_value, int(btckrw*holding_value))
    txt += '\ntrade:   {:.3f}{}({:.8f}BTC, {:,}KRW) +'.format(
        trade_volume_delta, TICKER, (trade_delta), int(btckrw*trade_delta))
    txt += '\npartial: {:.3f}{}({:.8f}BTC, {:,}KRW)'.format(
        partial_volume, TICKER, partial_delta, int(btckrw*partial_delta))

    print(fg.li_yellow + txt + fg.rs)
    send_telegram('[{}-BTC] '.format(TICKER)+txt)
    time.sleep(COOL_TIME)
