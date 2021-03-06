import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from coin import *
import time
from datetime import datetime, timezone, timedelta
import json
import telegram
import threading

# param #######################################################################
FEE = 0.0005  # 수수료는 0.05%
UPDOWN = 0.01  # 2% 상하로 걸어놓기..  성공하면 1.9%먹는 게임
BETTING = 900000  # 한번에 거는 돈의 크기
UPBIT_MIN_BETTING = 5100 # upbit의 최소 BTC 베팅 금액
COOL_TIME = 60 * 15  # 초단위
# TIMEOUT_DAYS = 1
TIMEOUT_HOURS = 24
BTC_LOCK = 0.90 # 최소 30%는 항상 BTC로 보유
BTC_LOCK_V = 2.00 # 최소 1.5 BTC 보유
BTC_BOX_CHECK = False
BTC_BOX_MIN = 36000000 #minimum boundary in krw OF BTC box
BTC_BOX_MAX = 38000000 #maximum boundary in krw OF BTC box
BTC_LOCK_PENDING_CHECK = True
THREAD_COOL_TIME = 5 #초단위
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
    try:
        log_file_name = global_conf['log-file-name']
        log_file = open("../log/{}".format(log_file_name), "a+")
        log_file.write("\n{}".format(msg))
    except:
        pass
    if do_send:
        try:
            bot_info['bot'].sendMessage(chat_id=bot_info['chat_id'], text=msg)
        except:
            pass


def get_config():
    try:
        with open("../conf/conf.json", "r") as conf_file:
            return json.load(conf_file)
    except Exception as e:
        print('err', e)


def write_config(json_data):
    try:
        with open("../conf/conf.json", "w") as conf_file:
            return json.dump(json_data, conf_file)
    except Exception as e:
        print('err', e)


def load_config():
    global UPDOWN, BETTING, COOL_TIME, TIMEOUT_HOURS, BTC_LOCK, BTC_LOCK_V, BTC_LOCK_PENDING_CHECK, BTC_BOX_CHECK, BTC_BOX_MIN, BTC_BOX_MAX
    conf = get_config()
    try:
        UPDOWN = float(conf['up-down-percent']) / 100
        BETTING = float(conf['betting-krw'])
        COOL_TIME = int(conf['cool-time-seconds'])
        TIMEOUT_HOURS = int(conf['timeout-hours'])
        BTC_LOCK = float(conf['btc-lock-percent']) / 100
        BTC_LOCK_V = float(conf['btc-lock-abs-amount'])
        BTC_LOCK_PENDING_CHECK = conf['btc-lock-pending-check'] == 'yes'
        BTC_BOX_CHECK = conf['btc-box-check'] == 'yes'
        BTC_BOX_MAX = float(conf['btc-box-max-krw'])
        BTC_BOX_MIN = float(conf['btc-box-min-krw'])
        print('conf: {}'.format(conf))
        return conf
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
        log_and_send_msg(bot_info, "{} orders alive...".format(len(l)), True)
        bid_sum = 0
        ask_sum = 0
        bid_cnt_sum = 0
        ask_cnt_sum = 0
        sid = 1
        for (oid, askbid, price, cnt, odt) in l:
            now = datetime.now(KST)
            date_diff = (now-odt).days
            hour_diff = int(date_diff*24 + (now-odt).seconds/3600)
            print('[{}]'.format(sid), oid, askbid, '{:,} {:.2f}m'.format(int(float(price)), float(cnt)*1000), odt, hour_diff, 'hours')
            if askbid == 'ask':
                ask_sum += price * cnt
                ask_cnt_sum += cnt
            else:
                bid_sum += price * cnt
                bid_cnt_sum += cnt
            if date_diff >= TIMEOUT_HOURS:
                log_and_send_msg(bot_info, "cancel order.. {}".format(oid), True)
                r = coin.cancel(oid)

                # 나중에 bid만으로 KRW부족이 발생해서, 오래된건 위치조정하지 말고 그냥 버리는걸로 해본다. > 근데 KRW부족이 peak eater 때문이어서 원복 ㅋ
                # if askbid=='ask': coin.limit_sell('BTC', ask_price, ask_cnt)
                # else: coin.limit_buy('BTC', bid_price, bid_cnt)
            sid = sid + 1

        print("pending orders' bid cnt: {}, bid sum: {}, ask cnt: {}, ask sum: {}".format(bid_cnt_sum, bid_sum, ask_cnt_sum, ask_sum))
        return {'bid_cnt': bid_cnt_sum, 'bid_krw': bid_sum, 'ask_cnt': ask_cnt_sum, 'ask_krw': ask_sum}
    except Exception as e:
        print('err', e)
        sys.exit()


# 공유된 변수를 위한 클래스
class ThreadVariable():
    def __init__(self):
        self.lock = threading.Lock()
        self.status = 'start'
        self.ret = self.status

    def get(self):
        self.lock.acquire()
        try:
            self.ret = self.status
        finally:
            self.lock.release()
        return self.ret

    # 한 Thread만 접근할 수 있도록 설정한다
    def set(self, value):
        self.lock.acquire()
        try:
            self.status = value
        finally:
            self.lock.release()


global run_status
run_status = ThreadVariable()


class CommandProcessor (threading.Thread):
    offset_pos = 0
    commands = ['start', 'stop', 'exit', 'none', 'set']

    def __init__(self):
        threading.Thread.__init__(self)
        self.command = 'start'
        self.prev_command = 'start'

    @staticmethod
    def make_error(param):
        log_and_send_msg(bot_info, 'wrong command error! {} \n (only support for start/stop/exit/set parameter)'.format(param), True)

    @staticmethod
    def get_telegram_command():
        updates = bot_info['bot'].getUpdates(offset=CommandProcessor.offset_pos)
        commander = bot_info['chat_id']
        is_empty = len(updates) == 0
        if not is_empty:
            try:
                CommandProcessor.offset_pos = updates[-1].update_id
                CommandProcessor.offset_pos = CommandProcessor.offset_pos + 1
                # get last command
                u = updates[-1]
                if u.message['chat']['id'] == commander:
                    text = u.message['text']
                    return text

            except Exception as e:
                return 'none'
        else:
            return 'none'

    def run(self):
        global run_status
        while True:
            try:
                res = CommandProcessor.get_telegram_command()
                args = res.split(' ')
                argc = len(args)
            except Exception as e:
                log_and_send_msg(bot_info, "telegram get commands make errors: {}".format(e))
            try:
                if argc == 0:
                    self.make_error('empty command')
                else:
                    arg = args[0]
                    if arg != 'none':
                        self.prev_command = self.command
                        self.command = res
                    if arg == 'exit':
                        log_and_send_msg(bot_info, 'exit command has been received, exiting ... ', True)
                        run_status.set('exit')
                        sys.exit()
                    elif arg == 'stop':
                        if self.command != self.prev_command:
                            run_status.set('stop')
                            log_and_send_msg(bot_info, 'stop command has been received, pausing ... ', True)
                    elif arg == 'start':
                        if self.command != self.prev_command:
                            run_status.set('start')
                            log_and_send_msg(bot_info, 'start command has been received, starting ... ', True)
                    elif arg == 'set':
                        if self.command != self.prev_command:
                            arg = args[1]
                            if arg == 'parameter':
                                name = args[2]
                                value = args[3]
                                config_json = get_config()
                                if name in config_json:
                                    config_json[name] = value
                                    write_config(config_json)
                                    log_and_send_msg(bot_info, 'setting parameter with name {}, value {} \n json conf file will be {}'.format(name, value, config_json), True)
                                else:
                                    log_and_send_msg(bot_info, 'unknown parameter name {} : refer to current conf.json file {}'.format(name, config_json), True)
                            else:
                                self.make_error(arg)
                    elif arg != 'none':
                        if self.command != self.prev_command:
                            self.make_error(arg)
            except Exception as e:
                self.make_error('with an error: {}'.format(e))
            time.sleep(THREAD_COOL_TIME)


bot_info = get_telegram_bot_info()
command_handling_thread = CommandProcessor()
command_handling_thread.daemon = True
command_handling_thread.start()
global_conf = load_config()

while True:
    if run_status.get() == 'exit':
        sys.exit()
    elif run_status.get() == 'start':
        global_conf = load_config()
        try:
            a = coin.get_price('BTC', 'KRW')
            money = coin.get_asset_info('KRW')
            btc = coin.get_asset_info('BTC')
        except Exception as e:
            print('err', e)
            time.sleep(1)
            continue
        pending_sum = check_and_cancel_pending_orders()
        log_and_send_msg(bot_info, 'KRW.. {}'.format(money))
        # money['free'] = int(money['free'] - 3000000)
        log_and_send_msg(bot_info, 'BTC.. {}'.format(btc))
        log_and_send_msg(bot_info, 'free BTC in KRW.. {:,}'.format(int(btc['free']*a)))
        total_asset_krw = money['total']+btc['total']*a
        log_and_send_msg(bot_info, 'total asset in krw.. {:,}'.format(total_asset_krw), True)

        btc_ratio = 0
        btc_total = 0
        if BTC_LOCK_PENDING_CHECK:
            btc_total = btc['free']
            btc_ratio = btc_total*a / total_asset_krw
            log_and_send_msg(bot_info, 'BTC to KRW ratio.. including pending btc sell {:.4f}'.format(btc_ratio))
            log_and_send_msg(bot_info, 'BTC total {:.4f}, BTC free {:.4f}, BTC pending ask in krw {:.4f}'.format(btc['total'], btc['free'], pending_sum['ask_cnt']))
        else:
            btc_ratio = btc['total']*a / (money['total']+btc['total']*a)
            btc_total = btc['total']
            log_and_send_msg(bot_info, 'BTC to KRW ratio..', '{:.4f}'.format(btc_ratio))

        if btc_ratio < BTC_LOCK: print('!!!!! less than BTC LOCK! {}'.format(BTC_LOCK))
        if btc_total < BTC_LOCK_V: print('!!!!! less than BTC VOLUME LOCK! {}'.format(BTC_LOCK_V))
        log_and_send_msg(bot_info, '[ {} ] BTC price.. upbit {:,}'.format(datetime.now().strftime("%m-%d %H:%M:%S"),a), True)

        ask_price = round(a + a * UPDOWN * 1.5, -3); ask_cnt = float(BETTING) / ask_price
        bid_price = round(a - a * UPDOWN, -3); bid_cnt = float(BETTING) / bid_price
        if money['free'] > bid_price * bid_cnt:
            if btc['free'] > ask_cnt and btc_ratio > BTC_LOCK and btc_total > BTC_LOCK_V:
                if not BTC_BOX_CHECK or (BTC_BOX_CHECK and bid_price >= BTC_BOX_MIN and ask_price <= BTC_BOX_MAX):
                    log_and_send_msg(bot_info, 'reserved limit buy: bid_price: {}, bid_cnt: {}, sell: ask_price: {}, ask_cnt: {}'.format(bid_price, bid_cnt, ask_price, ask_cnt), True)
                    coin.limit_buy('BTC', bid_price, bid_cnt)
                    coin.limit_sell('BTC', ask_price, ask_cnt)
                else:
                    log_and_send_msg(bot_info, 'skipping updown strategy because bid ask prices {} ~ {} are not in the box range {} ~ {}'.format(bid_price, ask_price, BTC_BOX_MIN, BTC_BOX_MAX), True)
            else:
                # canceling pending order logic is not required when BTC_LOCK_PENDING_CHECK is True
                if btc_ratio <= BTC_LOCK:
                    log_and_send_msg(bot_info, '!!!!!!!!!!!! BTC LOCK!', True)
                    if not BTC_LOCK_PENDING_CHECK:
                        cancel_pending_asks()
                        time.sleep(1)
                elif btc_total <= BTC_LOCK_V:
                    log_and_send_msg(bot_info, '!!!!!!!!!!!! BTC VOLUME LOCK!', True)
                    if not BTC_LOCK_PENDING_CHECK:
                        cancel_pending_asks()
                        time.sleep(1)
                else:
                    log_and_send_msg(bot_info, '!!!!!!!!!!!! not enough BTC!', True)

                if not BTC_LOCK_PENDING_CHECK:
                    if not check_pending_ask():
                        coin.limit_sell('BTC', ask_price, ask_cnt)  # 한 개는 걸어둔다(단 한개만)
                        log_and_send_msg(bot_info, 'reserved limit sell: ask_price: {}, ask_cnt: {}'.format(ask_price, ask_cnt))
                    new_bid_price = round(a - a * UPDOWN * 0.25, -3); new_bid_cnt = max(float(BETTING) / new_bid_price / 3, float(UPBIT_MIN_BETTING) / new_bid_price)
                    coin.limit_buy('BTC', new_bid_price, new_bid_cnt)
                    log_and_send_msg(bot_info, 'reserved limit buy: new_bid_price: {}, new_bid_cnt: {}'.format(new_bid_price, new_bid_cnt), True)

        else:
            log_and_send_msg(bot_info, '!!!!!!!!!!!! not enough KRW!', True)
            if btc['free'] > ask_cnt and btc_ratio > BTC_LOCK and btc_total > BTC_LOCK_V:
                new_ask_price = round(a + a * UPDOWN * 0.75, -3); new_ask_cnt = max(float(BETTING) / new_ask_price / 3, float(UPBIT_MIN_BETTING) / new_ask_price)
                coin.limit_sell('BTC', new_ask_price, new_ask_cnt)
                log_and_send_msg(bot_info, 'reserved limit sell: new_ask_price: {}, new_ask_cnt: {}'.format(new_ask_price, new_ask_cnt), True)

    time.sleep(COOL_TIME)
