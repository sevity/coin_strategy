import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from coin import *
import time
from datetime import datetime, timezone, timedelta
import json
import telegram

# param #######################################################################
FEE = 0.0005  # 수수료는 0.05%
UPDOWN = 0.01  # 2% 상하로 걸어놓기..  성공하면 1.9%먹는 게임
BETTING = 900000  # 한번에 거는 돈의 크기
COOL_TIME = 60 * 15  # 초단위
# TIMEOUT_DAYS = 1
TIMEOUT_HOURS = 24
BTC_LOCK = 0.90 # 최소 30%는 항상 BTC로 보유
BTC_LOCK_V = 2.00 # 최소 1.5 BTC 보유
BTC_LOCK_PENDING_CHECK = True
###############################################################################
# 상하방 양쪽으로 걸어서 박스권에서 왔다갔다 할경우 소액씩 계속 먹는 전략
# TODO: 지금은 가격이 떨어지면 BTC만 남는구조인데 거꾸로 가격이 떨어지면 KRW_LOCK을 늘리고 가격이 오르면 BTC_LOCK을 올리는식으로 해보자.
# 떨어지는걸 판단하는 기준이 좀 문제인데
# 1. 미체결 매수매도 주문수 비율로 판단한다.
# 2. 가격 이평선 같은걸로 하락추세인지 상승추세인지를 파악한다.

# TODO: 핸들링하고 있는 금액이 얼마인지 로깅을 추가해보자.
# TODO: file 로깅 기능을 추가해보자.
f = open("../conf/upbit_api_key.txt", 'r')
access_key = f.readline().rstrip()
secret_key = f.readline().rstrip()
f.close()
coin = Coin('upbit',access_key,secret_key)


def cancel_pending_bids(bLog=True):
    l = coin.get_live_orders('BTC', 'KRW')
    if bLog: print(' cancel pending bids..')
    for (oid, askbid, price, cnt, odt) in l:
        if askbid == 'ask':
            continue
        r = coin.cancel(oid, False)

def cancel_pending_asks(bLog=True):
    l = coin.get_live_orders('BTC', 'KRW')
    if bLog:print(' cancel pending asks..')
    for (oid, askbid, price, cnt, odt) in l:
        if askbid == 'bid':
            continue
        r = coin.cancel(oid)


def check_pending_ask(bLog=True):
    l = coin.get_live_orders('BTC', 'KRW')
    if bLog:print(' check pending asks..')
    for (oid, askbid, price, cnt, odt) in l:
        if askbid == 'bid':
            continue
        return True
    return False


def log_and_send_msg(bot_info, msg, do_send=False):
    print(msg)
    if do_send:
        try:
            bot_info['bot'].sendMessage(chat_id=bot_info['chat_id'], text=msg)
        except:
            pass


def load_config():
    try:
        with open("../conf/conf.json", "r") as conf_file:
            conf = json.load(conf_file)
            global UPDOWN, BETTING, COOL_TIME, TIMEOUT_HOURS, BTC_LOCK, BTC_LOCK_V, BTC_LOCK_PENDING_CHECK
            UPDOWN = conf['up_down_percent'] / 100
            BETTING = conf['betting_in_krw']
            COOL_TIME = conf['cool_time_in_seconds']
            TIMEOUT_HOURS = conf['timeout_in_hours']
            BTC_LOCK = conf['btc_lock_percent'] / 100
            BTC_LOCK_V = conf['btc_lock_abs_amount']
            BTC_LOCK_PENDING_CHECK = conf['btc_lock_pending_check'] == 'yes'
            print('conf: updown: {}, betting: {}, cool_time: {}, timeout_hours: {}, btc_lock: {}, btc_lock_v: {}, btc_lock_pending_check: {}'.format(UPDOWN, BETTING, COOL_TIME, TIMEOUT_HOURS, BTC_LOCK, BTC_LOCK_V, BTC_LOCK_PENDING_CHECK))
    except Exception as e:
        print('err', e)
        sys.exit()

def get_telegram_bot_info():
    try:
        with open("../conf/telegram.json", "r") as telegram_file:
            j = json.load(telegram_file)
            return {'bot': telegram.Bot(token=j['token']), 'chat_id': j['chat_id']}
    except Exception as e:
        print('err', e)
        pass

def check_and_cancel_pending_orders():
    try:
        # 고착화를 막기위해 일정기간 이상의 미체결 주문 청산
        print("check if it is needed to cancel pending orders...")
        l = coin.get_live_orders('BTC', 'KRW')
        KST = timezone(timedelta(hours=9))
        print("{} orders alive...".format(len(l)))
        bid_sum = 0
        ask_sum = 0
        bid_cnt_sum = 0
        ask_cnt_sum = 0
        for (oid, askbid, price, cnt, odt) in l:
            now = datetime.now(KST)
            date_diff = (now-odt).days
            hour_diff = int(date_diff*24 + (now-odt).seconds/3600)
            print(oid, askbid, '{:,} {:.2f}m'.format(int(float(price)), float(cnt)*1000), odt, hour_diff, 'hours')
            if askbid == 'ask':
                ask_sum += price * cnt
                ask_cnt_sum += cnt
            else:
                bid_sum += price * cnt
                bid_cnt_sum += cnt
            if date_diff >= TIMEOUT_HOURS:
                print("cancel order.. {}".format(oid))
                # r = coin.cancel(oid)

                # 나중에 bid만으로 KRW부족이 발생해서, 오래된건 위치조정하지 말고 그냥 버리는걸로 해본다. > 근데 KRW부족이 peak eater 때문이어서 원복 ㅋ
                # if askbid=='ask': coin.limit_sell('BTC', ask_price, ask_cnt)
                # else: coin.limit_buy('BTC', bid_price, bid_cnt)
        print("pending orders' bid cnt: {}, bid sum: {}, ask cnt: {}, ask sum: {}".format(bid_cnt_sum, bid_sum, ask_cnt_sum, ask_sum))
        return {'bid_cnt': bid_cnt_sum, 'bid_krw': bid_sum, 'ask_cnt': ask_cnt_sum, 'ask_krw': ask_sum}
    except Exception as e:
        print('err', e)
        sys.exit()


offset_pos = 0
commands = ['start', 'stop', 'exit', 'none']


def get_telegram_command(bot_info):
    global offset_pos, commands
    updates = bot_info['bot'].getUpdates(offset=offset_pos)
    commander = bot_info['chat_id']
    is_empty = len(updates) == 0
    if not is_empty:
        try:
            offset_pos = updates[-1].update_id
            offset_pos = offset_pos + 1
            # get last command
            u = updates[-1]
            if u.message['chat']['id'] == commander:
                text = u.message['text']
                if text in commands:
                    return text
                else:
                    return 'none'

        except Exception as e:
            pass
    else:
        return 'none'


command = 'start'


#later implement this as a separate thread
def handle_commands():
    global command
    prev_command = command
    result = get_telegram_command(bot_info)
    if result != 'none':
        command = result
    if command == 'exit':
        log_and_send_msg(bot_info, 'exit command has been received, exiting ... ', True)
        sys.exist()
    elif command == 'stop':
        if command != prev_command:
            log_and_send_msg(bot_info, 'stop command has been received, pausing ... ', True)
    elif command == 'start':
        if command != prev_command:
            log_and_send_msg(bot_info, 'start command has been received, starting ... ', True)
    return command == 'start'


while True:
    load_config()
    bot_info = get_telegram_bot_info()
    pending_sum = check_and_cancel_pending_orders()

    if handle_commands():
        try:
            a = coin.get_price('BTC', 'KRW')
            money = coin.get_asset_info('KRW')
            btc = coin.get_asset_info('BTC')
        except Exception as e:
            print('err', e)
            time.sleep(1)
            continue

        log_and_send_msg(bot_info, 'KRW.. {}'.format(money))
        # money['free'] = int(money['free'] - 3000000)
        log_and_send_msg(bot_info, 'BTC.. {}'.format(btc))
        log_and_send_msg(bot_info, 'free BTC in KRW.. {:,}'.format(int(btc['free']*a)))
        log_and_send_msg(bot_info, 'total money.. {:,}'.format(int(money['total'])+int(btc['total']*a)))

        btc_ratio = 0
        btc_total = 0
        if BTC_LOCK_PENDING_CHECK:
            btc_ratio = (btc['total']*a - pending_sum['ask_krw']) / (money['total']+btc['total']*a)
            btc_total = btc['free']
            log_and_send_msg(bot_info, 'BTC to KRW ratio.. including pending btc sell {:.4f}'.format(btc_ratio))
            log_and_send_msg(bot_info, 'BTC total {:.4f}, BTC free {:.4f}, BTC pending ask in krw {:.4f}'.format(btc['total'], btc['free'], pending_sum['ask_cnt']))
        else:
            btc_ratio = btc['total']*a / (money['total']+btc['total']*a)
            btc_total = btc['total']
            log_and_send_msg(bot_info, 'BTC to KRW ratio..', '{:.4f}'.format(btc_ratio))

        if btc_ratio < BTC_LOCK: print('!!!!! less than BTC LOCK! {}'.format(BTC_LOCK))
        if btc_total < BTC_LOCK_V: print('!!!!! less than BTC VOLUME LOCK! {}'.format(BTC_LOCK_V))
        print(datetime.now().strftime("%m-%d %H:%M:%S"), 'BTC price..', 'upbit', '{:,}'.format(a))
        #a = round(a, -1) # minimum 10 won

        ask_price = round(a + a * UPDOWN * 1.5, -3); ask_cnt = float(BETTING) / ask_price
        bid_price = round(a - a * UPDOWN, -3); bid_cnt = float(BETTING) / bid_price
        if money['free'] > bid_price * bid_cnt :
            if btc['free'] > ask_cnt and btc_ratio > BTC_LOCK and btc_total > BTC_LOCK_V:
                coin.limit_buy('BTC', bid_price, bid_cnt)
                coin.limit_sell('BTC', ask_price, ask_cnt)
                log_and_send_msg(bot_info, 'reserved limit buy: bid_price: {}, bid_cnt: {}, sell: ask_price: {}, ask_cnt: {}'.format(bid_price, bid_cnt, ask_price, ask_cnt), True)
            else:
                # canceling pending order logic is not required when BTC_LOCK_PENDING_CHECK is True
                if not BTC_LOCK_PENDING_CHECK:
                    if btc_ratio <= BTC_LOCK:
                        log_and_send_msg(bot_info, '!!!!!!!!!!!! BTC LOCK!')
                        cancel_pending_asks()
                        time.sleep(1)
                    elif btc_total <= BTC_LOCK_V:
                        log_and_send_msg(bot_info, '!!!!!!!!!!!! BTC VOLUME LOCK!')
                        cancel_pending_asks()
                        time.sleep(1)
                    else:
                        log_and_send_msg(bot_info, '!!!!!!!!!!!! not enough BTC!')

                if not check_pending_ask():
                    coin.limit_sell('BTC', ask_price, ask_cnt)  # 한 개는 걸어둔다(단 한개만)
                    log_and_send_msg(bot_info, 'reserved limit sell: ask_price: {}, ask_cnt: {}'.format(ask_price, ask_cnt))
                new_bid_price = round(a - a * UPDOWN * 0.25, -3); new_bid_cnt = float(BETTING) / new_bid_price / 3
                coin.limit_buy('BTC', new_bid_price, new_bid_cnt)
                log_and_send_msg(bot_info, 'reserved limit buy: new_bid_price: {}, new_bid_cnt: {}'.format(new_bid_price, new_bid_cnt), True)

        else:
            print('!!!!!!!!!!!! not enough KRW!')
            if btc['free'] > ask_cnt and btc_ratio > BTC_LOCK and btc_total > BTC_LOCK_V:
                new_ask_price = round(a + a * UPDOWN * 0.75, -3); new_ask_cnt = float(BETTING) / new_ask_price / 3
                coin.limit_sell('BTC', new_ask_price, new_ask_cnt)
                log_and_send_msg(bot_info, 'reserved limit sell: new_ask_price: {}, new_ask_cnt: {}'.format(new_ask_price, new_ask_cnt), True)

    time.sleep(COOL_TIME)
