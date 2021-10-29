# -*- coding: utf-8 -*-
#! /usr/bin/env python
from __future__ import absolute_import
import sys
import pprint
import time
import json
import requests
import os
import jwt
import uuid
import hashlib
import math
from urllib.parse import urlencode
from datetime import datetime, timezone, timedelta
from multipledispatch import dispatch # https://www.geeksforgeeks.org/python-method-overloading/
from sty import fg, bg, ef, rs

server_url = 'https://api.upbit.com'

g_api_key = ""
g_api_secret = ""
g_ask_fee = -1
g_bid_fee = -1

def set_key(api_key, secret_key):
    global g_api_key, g_api_secret
    g_api_key = api_key
    g_api_secret = secret_key

def log(msg):
    print('  ' + fg.li_black + msg + fg.rs)

def get_price(ticker, currency):
    while True:
        j = {}
        try:
            url = server_url + "/v1/orderbook"
            querystring = {"markets":"{}-{}".format(currency, ticker)}
            response = requests.request("GET", url, params=querystring)
            if response.ok == False:
                if response.status_code != 429:  # too many api requeists
                    print(fg.li_black + response.url, response.text, fg.rs)
            j = json.loads(response.text)
            ask1 = float(j[0]["orderbook_units"][0]["ask_price"])
            bid1 = float(j[0]["orderbook_units"][0]["bid_price"])
            return round((ask1+bid1)/2, 8)  # round(..,8) for BTC market
        except:
            try:
                if int(j['error']['name']) == 404:
                    return None
            except:
                pass
            time.sleep(1.0)

def get_ask1(ticker, currency):
    while True:
        try:
            url = server_url + "/v1/orderbook"
            querystring = {"markets":"{}-{}".format(currency, ticker)}
            response = requests.request("GET", url, params=querystring)
            if response.ok == False:
                if response.status_code != 429:  # too many api requeists
                    print(  response.url, response.text)
            j = json.loads(response.text)
            # print(j[0]["orderbook_units"])
            ask1 = float(j[0]["orderbook_units"][0]["ask_price"])
            return ask1
        except:
            time.sleep(1.0)

def get_bid1(ticker, currency):
    while True:
        try:
            url = server_url + "/v1/orderbook"
            querystring = {"markets":"{}-{}".format(currency, ticker)}
            response = requests.request("GET", url, params=querystring)
            if response.ok == False:
                if response.status_code != 429:  # too many api requeists
                    print(  response.url, response.text)
            j = json.loads(response.text)
            bid1 = float(j[0]["orderbook_units"][0]["bid_price"])
            return bid1
        except:
            time.sleep(1.0)

def get_info(ticker, currency):
    query = {
        'market': '{}-{}'.format(currency, ticker),
    }
    query_string = urlencode(query).encode()

    m = hashlib.sha512()
    m.update(query_string)
    query_hash = m.hexdigest()

    payload = {
        'access_key': g_api_key,
        'nonce': str(uuid.uuid4()),
        'query_hash': query_hash,
        'query_hash_alg': 'SHA512',
    }

    jwt_token = jwt.encode(payload, g_api_secret).decode('utf-8')
    authorize_token = 'Bearer {}'.format(jwt_token)
    headers = {"Authorization": authorize_token}

    res = requests.get(server_url + "/v1/orders/chance", params=query, headers=headers)
    a = res.json()
    r = {}
    r['ask_fee'] = float(a['ask_fee'])
    r['bid_fee'] = float(a['bid_fee'])
    r['tick_size'] = a['market']['ask']['price_unit']
    return r

def get_asset_info(currency):
    url = server_url + "/v1/accounts"

    payload = {
        'access_key': g_api_key,
        'nonce': str(uuid.uuid4()),
    }

    while True:
        try:
            jwt_token = jwt.encode(payload, g_api_secret).decode('utf-8')
            authorize_token = 'Bearer {}'.format(jwt_token)
            headers = {"Authorization": authorize_token}
            res = requests.get(url, headers=headers)
            a = res.json()
            r = {}
            for i in range(len(a)):
                if a[i]['currency']==currency:
                    r['free'] = float(a[i]['balance'])
                    r['inuse'] = float(a[i]['locked'])
                    r['total'] = r['free'] + r['inuse']
                    break
            return r
        except:
            time.sleep(1.0)



def order_new(ticker, price, cnt, askbid, ord_type, bLog = True, bConfirm = True):
    if ticker=='BTC':
        price = round(price, -3) # minimum 1000 won

    query = {
        'market': 'KRW-{}'.format(ticker),
        'side': askbid,
        'volume': cnt,
        'price': price,
        'ord_type': ord_type,
    }
    if ord_type=='market':
        query = {
            'market': 'KRW-{}'.format(ticker),
            'side': askbid,
            'volume': cnt,
            'ord_type': ord_type,
        }
    if ord_type=='price':
        query = {
            'market': 'KRW-{}'.format(ticker),
            'side': askbid,
            'price': price,
            'ord_type': ord_type,
        }
    query_string = urlencode(query).encode()

    m = hashlib.sha512()
    m.update(query_string)
    query_hash = m.hexdigest()

    payload = {
        'access_key': g_api_key,
        'nonce': str(uuid.uuid4()),
        'query_hash': query_hash,
        'query_hash_alg': 'SHA512',
    }

    jwt_token = jwt.encode(payload, g_api_secret).decode('utf-8')
    authorize_token = 'Bearer {}'.format(jwt_token)
    headers = {"Authorization": authorize_token}

    ok = False
    while ok == False:
        try:
            res = requests.post(server_url + "/v1/orders", params=query, headers=headers)
            ok = True
        except:
            pass
    
    if res.ok == False:
        log('order_new.. ' + res.text)
        return (-1, res)
    oid = json.loads(res.content)['uuid']
    # print(' ', oid)
    # print(oid, res)
    if bLog and ord_type!='price': print(fg.li_black + '  order_new...', ticker, 'price:{:,.2f}'.format(price),
        'cnt:{:,.4f}, amount:{:,}KRW'.format(cnt, int(price*cnt)), askbid, oid.split('-')[0] + fg.rs)
    elif bLog and ord_type=='price': print(fg.li_black + '  market_buy order_new...', ticker, 
        'amount:{:,}KRW'.format(int(price)), askbid, oid.split('-')[0] + fg.rs)
    if bConfirm:
        c = 0
        while c > -1:
            time.sleep(c)
            s = get_order_state(oid)
            if s == 'ack' or s == 'fill' or s == 'partial_fill':
                c = -2
            c += 1
        # log('order confirmed')
    return (oid,res)

def order_new_btc(ticker, price, cnt, askbid, ord_type, bLog = True, bConfirm = False):
    # price = math.floor(price*100000000)/100000000  # 사토시 이하 버림처리
    price = round(price, 8)  # 사이토 이하 반올림 처리
    # print('price:{:.8f}'.format(price))
    query = {
        'market': 'BTC-{}'.format(ticker),
        'side': askbid,
        'volume': cnt,
        'price': price,
        'ord_type': ord_type,
    }
    if ord_type=='market':
        query = {
            'market': 'BTC-{}'.format(ticker),
            'side': askbid,
            'volume': cnt,
            'ord_type': ord_type,
        }
    if ord_type=='price':
        query = {
            'market': 'BTC-{}'.format(ticker),
            'side': askbid,
            'price': price,
            'ord_type': ord_type,
        }
    query_string = urlencode(query).encode()

    m = hashlib.sha512()
    m.update(query_string)
    query_hash = m.hexdigest()

    payload = {
        'access_key': g_api_key,
        'nonce': str(uuid.uuid4()),
        'query_hash': query_hash,
        'query_hash_alg': 'SHA512',
    }

    jwt_token = jwt.encode(payload, g_api_secret).decode('utf-8')
    authorize_token = 'Bearer {}'.format(jwt_token)
    headers = {"Authorization": authorize_token}

    ok = False
    while ok == False:
        try:
            res = requests.post(server_url + "/v1/orders", params=query, headers=headers)
            ok = True
        except:
            pass

    if res.ok == False:
        # log('order_new.. ' + res.text)
        return (-1, res)
    
    oid = json.loads(res.content)['uuid']
    # print(' ', oid)
    # print(oid, res)
    if bLog and ord_type!='price': print(fg.li_black + '  order_new...', ticker, 'price:{:.8f}'.format(price),
        'cnt:{:,.8f}, amount:{:.8f}BTC'.format(cnt, (price*cnt)), askbid, oid.split('-')[0] + fg.rs)

    if bConfirm:
        c = 0
        while c > -1:
            time.sleep(c)
            s = get_order_state(oid)
            if s == 'ack' or s == 'fill' or s == 'partial_fill':
                c = -2
            c += 1
        # log('order confirmed')
    return (oid,res)

def order_new_wrap(ticker, price, cnt, askbid, ord_type, bLog = True, bConfirm = False):
    oid, res = order_new(ticker, price, cnt, askbid, 'limit', bLog, bConfirm)
    # log('res.reason:' + str(res.reason))
    while str(res.reason) == 'Too Many Requests':
        log('too_many_request_order.. retrying')
        time.sleep(15)
        oid, res = order_new(ticker, price, cnt, askbid, 'limit', bLog, bConfirm)
    return oid, res

def order_new_wrap_btc(ticker, price, cnt, askbid, ord_type, bLog = True, bConfirm = False):
    oid, res = order_new_btc(ticker, price, cnt, askbid, 'limit', bLog, bConfirm)
    if str(res.reason) == 'Bad Request':
        log('res.text:' + res.text)
        time.sleep(15)

    while str(res.reason) == 'Too Many Requests':
        log('too_many_request_order.. retrying')
        time.sleep(15)
        oid, res = order_new_btc(ticker, price, cnt, askbid, 'limit', bLog, bConfirm)
    return oid, res

def limit_buy(ticker, price, cnt, bLog=True, bConfirm=False):
    return order_new_wrap(ticker, price, cnt, 'bid', 'limit', bLog, bConfirm)[0]

def limit_sell(ticker, price, cnt, bLog=True, bConfirm=False):
    return order_new_wrap(ticker, price, cnt, 'ask', 'limit', bLog, bConfirm)[0]

def limit_buy_btc(ticker, price, cnt, bLog=True, bConfirm=False):
    return order_new_wrap_btc(ticker, price, cnt, 'bid', 'limit', bLog, bConfirm)[0]

def limit_sell_btc(ticker, price, cnt, bLog=True, bConfirm=False):
    return order_new_wrap_btc(ticker, price, cnt, 'ask', 'limit', bLog, bConfirm)[0]

def market_buy(ticker, price, bLog=True, bConfirm=False):
    return order_new(ticker, price, 0, 'bid', 'price' , bLog, bConfirm)[0]

def market_sell(ticker, cnt, bLog=True, bConfirm=False):
    (oid, res) = order_new(ticker, 0, cnt, 'ask', 'market', bLog, bConfirm)
    if oid == -1: return {}
    print("market sell done..", ticker, cnt)
    r = {}
    while 'final_amount' not in r:
        r = get_fill_order(oid)
    # print('  debug info..', 'get_fill_order..', r)
    return r

def cancel_wrap(oid, bLog):
    res = cancel_sub(oid, bLog)
    # log('res.reason:' + str(res.reason))
    while str(res.reason) == 'Too Many Requests':
        log('too_many_request_order.. retrying')
        time.sleep(15)
        res = cancel_sub(oid, bLog)
    return res
def cancel_sub(oid, bLog=True):
    if bLog: log('order_cancel...' + str(oid))
    query = {
        'uuid': oid,
    }
    query_string = urlencode(query).encode()

    m = hashlib.sha512()
    m.update(query_string)
    query_hash = m.hexdigest()

    payload = {
        'access_key': g_api_key,
        'nonce': str(uuid.uuid4()),
        'query_hash': query_hash,
        'query_hash_alg': 'SHA512',
    }

    jwt_token = jwt.encode(payload, g_api_secret).decode('utf-8')
    authorize_token = 'Bearer {}'.format(jwt_token)
    headers = {"Authorization": authorize_token}

    while True:
        try:
            res = requests.delete(server_url + "/v1/order", params=query, headers=headers)
            break
        except:
            time.sleep(1.0)
    if res.ok == False or res.status_code != 200:
        log('cancel fail...' + str(oid) + str(res.ok) + str(res) + str(res.text))
    return res
def cancel(oid, bLog=True):
    return cancel_wrap(oid, bLog)


@dispatch(str, str)
def get_live_orders(ticker, currency):
    r = []
    page_id = 0

    while True:
        page_id = page_id + 1
        query = {
            'market': '{}-{}'.format(currency, ticker),  # 왠일인지 이게 안먹네
            'state': 'wait',
            'page': page_id,
        }
        query_string = urlencode(query)

        uuids = [
            '9ca023a5-851b-4fec-9f0a-48cd83c2eaae',
            #...
        ]
        uuids_query_string = '&'.join(["uuids[]={}".format(uuid) for uuid in uuids])

        m = hashlib.sha512()
        m.update(query_string.encode())
        query_hash = m.hexdigest()

        payload = {
            'access_key': g_api_key,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
        }

        jwt_token = jwt.encode(payload, g_api_secret).decode('utf-8')
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}

        ok = False
        while not ok:
            try:
                res = requests.get(server_url + "/v1/orders", params=query, headers=headers)
                ok = True
            except Exception as e:
                log('[get_live_orders] error when request response with exception:' + str(e))

        if res.ok == False:
            if str(res.reason) != 'Too Many Requests':
                log('[get_live_orders] ' + str(res.reason))
            if str(res.reason) == 'Bad Request':  # BTC마켓에만 있는데 원화로 요청한 경우 여기로 온다.
                return 'bad request'
            time.sleep(5)
            return 'error'

        # if json conversion error occurs then return empty dictionary
        try:
            rj = res.json()
        except Exception as e:
            log('[get_live_orders] error when making response to json, with exception:' +  str(e))
            time.sleep(5)
            return 'error'

        if rj is None:
            print('[get_live_orders] error: json is None, returning an empty result')
            return 'error'
        elif not bool(rj):
            # loop end condition, return current response, empty live orders in this page, meaning the end of the page
            return r

        if res.reason == 'Bad Request':  # ex> BTC마켓에만 있는데 KRW로 조회하는 경우
            return []

        for ord in res.json():
            try:
                # print('ord:', ord)
                ct = datetime.strptime(ord['created_at'], '%Y-%m-%dT%H:%M:%S%z')
                price = float(ord['price'])
                remaining_volume = float(ord['remaining_volume'])
                a = ord['uuid']
                b = ord['side']
                r.append((a, b, price, remaining_volume, ct))
            # maybe data index reference exception? don't we need to return empty dictionary?
            except Exception as e:
                log(res.reason + ', ' +  res.text)
                log('[get_live_orders] error when appending... with exception:' + str(e))
                time.sleep(5)
                return 'error' 

    return r

@dispatch(str, str) 
def get_live_orders_ext(ticker, currency):
    query = {
        'market': '{}-{}'.format(currency, ticker),  # 왠일인지 이게 안먹네
        'state': 'wait',
    }
    query_string = urlencode(query)

    m = hashlib.sha512()
    m.update(query_string.encode())
    query_hash = m.hexdigest()

    payload = {
        'access_key': g_api_key,
        'nonce': str(uuid.uuid4()),
        'query_hash': query_hash,
        'query_hash_alg': 'SHA512',
    }

    jwt_token = jwt.encode(payload, g_api_secret).decode('utf-8')
    authorize_token = 'Bearer {}'.format(jwt_token)
    headers = {"Authorization": authorize_token}

    ok = False
    while ok == False:
        try:
            res = requests.get(server_url + "/v1/orders", params=query, headers=headers)
            ok = True
        except:
            pass
    r = []
    try:
        rj = res.json()
    except:
        return 'error'
        return r

    for ord in res.json():
        try:
            # print('ord:', ord)
            ct = datetime.strptime(ord['created_at'], '%Y-%m-%dT%H:%M:%S%z')
            price = float(ord['price'])
            ordered_volume = float(ord['volume'])
            remaining_volume = float(ord['remaining_volume'])
            r.append((ord['uuid'], ord['side'], price, ordered_volume, remaining_volume, ct))
        except:
            return 'error'
            pass
    return r

@dispatch(str) 
def get_live_orders(currency):
    query = {
        'state': 'wait',
    }
    query_string = urlencode(query)

    m = hashlib.sha512()
    m.update(query_string.encode())
    query_hash = m.hexdigest()

    payload = {
        'access_key': g_api_key,
        'nonce': str(uuid.uuid4()),
        'query_hash': query_hash,
        'query_hash_alg': 'SHA512',
    }

    jwt_token = jwt.encode(payload, g_api_secret).decode('utf-8')
    authorize_token = 'Bearer {}'.format(jwt_token)
    headers = {"Authorization": authorize_token}
    ok = False
    while ok == False:
        try:
            res = requests.get(server_url + "/v1/orders", params=query, headers=headers)
            r = []
            for ord in res.json():
                ct = dt = datetime.strptime(ord['created_at'], '%Y-%m-%dT%H:%M:%S%z')
                ticker = ord['market'].split('-')[1]
                r.append((ticker, ord['uuid'], ord['side'], float(ord['price']), float(ord['remaining_volume']), ct))
            ok = True
        except:
            pass
    return r

def get_order_state(oid):
    state = ''
    try:
        query = {
            'uuid': oid,
        }
        query_string = urlencode(query).encode()

        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()

        payload = {
            'access_key': g_api_key,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
        }

        jwt_token = jwt.encode(payload, g_api_secret).decode('utf-8')
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}

        res = requests.get(server_url + "/v1/order", params=query, headers=headers)
        j = res.json()
        if len(j) == 0:
            return ''
        state = j['state']
        req_vol = float(j['volume'])
        remaining_vol = float(j['remaining_volume'])
        if state == 'done' and remaining_vol != 0:
            raise Exception(f'state is done but remaining volume is not zero ({remaining_vol})')
        elif remaining_vol != 0 and remaining_vol != req_vol:
            state = 'partial_fill'
        elif state == 'wait' and remaining_vol == 0:
            raise Exception(f'state is wait but remaining volume is zero ({remaining_vol})')
    except Exception as e:
        log('[get_order_state] error: ' + str(e) + ', j:' + str(j))
        return ''
    if state == 'wait': return 'ack'
    if state == 'done': return 'fill'
    if state == 'partial_fill': return 'partial_fill'
    return ''

def get_fill_order(oid):
    try:
        query = {
            'state': 'done',
        }
        query_string = urlencode(query)

        uuids = [
            oid,
            #...
        ]
        uuids_query_string = '&'.join(["uuids[]={}".format(uuid) for uuid in uuids])

        query['uuids[]'] = uuids
        query_string = "{0}&{1}".format(query_string, uuids_query_string).encode()

        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()

        payload = {
            'access_key': g_api_key,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
        }

        jwt_token = jwt.encode(payload, g_api_secret).decode('utf-8')
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}

        res = requests.get(server_url + "/v1/orders", params=query, headers=headers)
        j = res.json()
        if len(j) == 0:
            return {}

    except Exception as e:
        log('[get_fill_order] error: ' + str(e))
        return {}

    log('j: ' + str(j))
    global g_ask_fee, g_bid_fee
    if g_ask_fee == -1 or g_bid_fee == -1:
        ticker = j[0]['market'].split('-')[1]
        info = get_info(ticker, 'KRW')
        g_ask_fee = info['ask_fee']
        g_bid_fee = info['bid_fee']

    r = {}
    r['askbid'] = j[0]['side']
    r['fee'] = float(j[0]['paid_fee'])
    fee = g_ask_fee if r['askbid']=='ask' else g_bid_fee
    price=0
    volume=0
    r['price']=0
    r['volume']=0
    r['final_amount']=0
    for k in j:
        # print('  debug info..', k)
        volume += float(k['executed_volume'])
        price = r['fee']/fee/volume if k['price'] is None else float(k['price'])
        if r['askbid']=='ask':
            r['final_amount'] += price * volume - r['fee']
        else:
            r['final_amount'] += price * volume + r['fee']
        r['volume'] += volume
        r['price'] += price*volume
    r['final_amount']/=len(j)
    r['price']/=r['volume']
    return r
