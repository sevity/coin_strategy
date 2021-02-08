# -*- coding: utf-8 -*-
#! /usr/bin/env python
from __future__ import absolute_import
import time
import socket
import json
import telegram
import threading
import sys
import redis
import re

CONF_FILE = "../conf/conf.json"

def send_metric_telegraf(m):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(
            json.dumps({'metric_name': 'updown_metrics', 'total_money_in_btc_cnt': m['total_btc_cnt'],
                        'total_krw': m['total_krw'], 'btc_price': m['btc_price'], 'btc_ratio': m['btc_ratio'], 'p_orders_cnt': m['p_orders_cnt'], 'total_gain': m['total_gain']}).encode(),
            ('localhost', 8094)
        )
        sock.close()
    except socket.error as e:
        print(f'Got error: {e}')


def get_config():
    global CONF_FILE
    try:
        with open(CONF_FILE, "r") as conf_file:
            return json.load(conf_file)
    except Exception as e:
        print('err', e)


def load_config():
    conf = get_config()
    try:
        return conf
    except Exception as e:
        print('err', e)
        sys.exit()


global_conf = load_config()


def strip_special_characters(s):
    return re.sub(r'\x1b(\[.*?[@-~]|\].*?(\x07|\x1b\\))', '', s)


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
            bot_info['bot'].sendMessage(chat_id=bot_info['chat_id'], text=strip_special_characters(msg))
        except:
            pass




def write_config(json_data):
    try:
        with open("../conf/conf.json", "w") as conf_file:
            return json.dump(json_data, conf_file)
    except Exception as e:
        print('err', e)



def get_telegram_bot_info():
    try:
        with open("../conf/telegram.json", "r") as telegram_file:
            j = json.load(telegram_file)
            return {'bot': telegram.Bot(token=j['token']), 'chat_id': j['chat_id']}
    except Exception as e:
        print('err', e)
        pass


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


THREAD_COOL_TIME = 5 #초단위


def make_error(bot_info, param):
    log_and_send_msg(bot_info,
                     'wrong command error! {} \n (only support for start/stop/exit/set parameter)'.format(param), True)


def get_telegram_command(bot_info):
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


class CommandProcessor (threading.Thread):
    offset_pos = 0
    commands = ['start', 'stop', 'exit', 'none', 'set']

    def __init__(self, bot, run_status):
        threading.Thread.__init__(self)
        self.command = 'start'
        self.prev_command = 'start'
        self.bot_info = bot
        self.run_status = run_status

    def run(self):
        while True:
            try:
                res = get_telegram_command(self.bot_info)
                args = res.split(' ')
                argc = len(args)
            except Exception as e:
                log_and_send_msg(self.bot_info, "telegram get commands make errors: {}".format(e))
            try:
                if argc == 0:
                    self.make_error('empty command')
                else:
                    arg = args[0]
                    if arg != 'none':
                        self.prev_command = self.command
                        self.command = res
                    if arg == 'exit':
                        log_and_send_msg(self.bot_info, 'exit command has been received, exiting ... ', True)
                        self.run_status.set('exit')
                        sys.exit()
                    elif arg == 'stop':
                        if self.command != self.prev_command:
                            self.run_status.set('stop')
                            log_and_send_msg(self.bot_info, 'stop command has been received, pausing ... ', True)
                    elif arg == 'start':
                        if self.command != self.prev_command:
                            self.run_status.set('start')
                            log_and_send_msg(self.bot_info, 'start command has been received, starting ... ', True)
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
                                    log_and_send_msg(self.bot_info, 'setting parameter with name {}, value {} \n json conf file will be {}'.format(name, value, config_json), True)
                                else:
                                    log_and_send_msg(self.bot_info, 'unknown parameter name {} : refer to current conf.json file {}'.format(name, config_json), True)
                            else:
                                make_error(arg)
                    elif arg != 'none':
                        if self.command != self.prev_command:
                            make_error(arg)
            except Exception as e:
                make_error('with an error: {}'.format(e))
            time.sleep(THREAD_COOL_TIME)


def redis_get(key):

    try:
        conn = redis.StrictRedis(
            host=global_conf['redis-host'],
            port=int(global_conf['redis-port']))

        res = conn.get(key)
        return res
    except Exception as ex:
        print('Error:', ex)
        raise ex


def redis_set(key,val):
    try:
        conn = redis.StrictRedis(
            host=global_conf['redis-host'],
            port=int(global_conf['redis-port']))

        res = conn.set(key,val)
        return res
        # print('Delete Record:', conn.delete("test"))
        #
        # print('Get Deleted Record:', conn.get("test"))

    except Exception as ex:
        print('Error:', ex)
        raise ex



def redis_del(key):
    try:
        conn = redis.StrictRedis(
            host=global_conf['redis-host'],
            port=int(global_conf['redis-port']))

        res = conn.delete(key)
        return res
    except Exception as ex:
        print('Error:', ex)
        raise ex


def jsonkey2int(x):
    if isinstance(x, dict):
            return {int(k):v for k,v in x.items()}
    return x