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
            return (ask1+bid1)/2
        except:
            if 'error' in j:
                if int(j['error']['name']) == 404:
                    return None
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



def order_new(ticker, price, cnt, askbid, ord_type, bLog = True):
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
        print(res, res.text)
        return (-1, None)
    oid = json.loads(res.content)['uuid']
    # print(' ', oid)
    # print(oid, res)
    if bLog and ord_type!='price': print(fg.li_black + '  order_new...', ticker, 'price:{:,.2f}'.format(price),
        'cnt:{:,.4f}, amount:{:,}KRW'.format(cnt, int(price*cnt)), askbid, oid + fg.rs)
    elif bLog and ord_type=='price': print(fg.li_black + '  market_buy order_new...', ticker, 
        'amount:{:,}KRW'.format(int(price)), askbid, oid + fg.rs)
    return (oid,res)

def order_new_btc(ticker, price, cnt, askbid, ord_type, bLog = True):
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
        print(res, res.text)
        en = json.loads(res.text)['error']['name']
        if en == 'under_min_total_market_ask':  # 최소 주문 금액은 500.0 KRW입니다.
            return (-1, None)
        return (-1, None)
    oid = json.loads(res.content)['uuid']
    # print(' ', oid)
    # print(oid, res)
    if bLog and ord_type!='price': print(fg.li_black + '  order_new...', ticker, 'price:{:.8f}'.format(price),
        'cnt:{:,.8f}, amount:{:.8f}BTC'.format(cnt, (price*cnt)), askbid, oid + fg.rs)
    return (oid,res)

def limit_buy(ticker, price, cnt, bLog=True):
    return order_new(ticker, price, cnt, 'bid', 'limit', bLog)[0]

def limit_sell(ticker, price, cnt, bLog=True):
    return order_new(ticker, price, cnt, 'ask', 'limit', bLog)[0]

def limit_buy_btc(ticker, price, cnt, bLog=True):
    return order_new_btc(ticker, price, cnt, 'bid', 'limit', bLog)[0]

def limit_sell_btc(ticker, price, cnt, bLog=True):
    return order_new_btc(ticker, price, cnt, 'ask', 'limit', bLog)[0]

def market_buy(ticker, price, bLog=True):
    return order_new(ticker, price, 0, 'bid', 'price' , bLog)[0]

def market_sell(ticker, cnt, bLog=True):
    (oid, res) = order_new(ticker, 0, cnt, 'ask', 'market', bLog)
    if oid == -1: return {}
    print("market sell done..", ticker, cnt)
    r = {}
    while 'final_amount' not in r:
        r = get_fill_order(oid)
    # print('  debug info..', 'get_fill_order..', r)
    return r

def cancel(oid, bLog=True):
    if bLog: print(fg.li_black + '  order_cancel...', oid + fg.rs)
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
        print('  cancel fail...', oid, res.ok, res, res.text)
    return res

@dispatch(str, str) 
def get_live_orders(ticker, currency):
    r = []
    page_id = 1

    while True:
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
        while ok == False:
            try:
                res = requests.get(server_url + "/v1/orders", params=query, headers=headers)
                ok = True
            except Exception as e:
                print('[get_live_orders] error when get request response, so retrying... with exception:', e)

        # if json conversion error occurs then return empty dictionary
        try:
            rj = res.json()
        except Exception as e:
            r = []
            print('[get_live_orders] error when making response to json, returning empty, with exception:', e)
            return r

        if rj is None:
            r = []
            print('[get_live_orders] error: json is None, returning empty')
            return r

        # loop end condition, return current response, empty live orders in this page, meaning the end of the page
        if not bool(res.json()):
            return r

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
                print('[get_live_orders] error when appending individual order, so skipping... with exception:', e)
        page_id = page_id + 1

    return r

@dispatch(str, str) 
def get_live_orders_ext(ticker, currency):
    query = {
        'market': '{}-{}'.format(currency, ticker),  # 왠일인지 이게 안먹네
        'state': 'wait',
    }
    query_string = urlencode(query)

    uuids = [
        '9ca023a5-851b-4fec-9f0a-48cd83c2eaae',
        #...
    ]
    uuids_query_string = '&'.join(["uuids[]={}".format(uuid) for uuid in uuids])

    #query['uuids[]'] = uuids
    #query_string = "{0}&{1}".format(query_string, uuids_query_string).encode()

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
    for ord in res.json():
        try:
            # print('ord:', ord)
            ct = datetime.strptime(ord['created_at'], '%Y-%m-%dT%H:%M:%S%z')
            price = float(ord['price'])
            ordered_volume = float(ord['volume'])
            remaining_volume = float(ord['remaining_volume'])
        except:
            ct = None
            price = 0.0
            ordered_volume = 0.0
            remaining_volume = 0.0
        r.append((ord['uuid'], ord['side'], price, ordered_volume, remaining_volume, ct))
    return r

@dispatch(str) 
def get_live_orders(currency):
    query = {
        'state': 'wait',
    }
    query_string = urlencode(query)

    uuids = [
        '9ca023a5-851b-4fec-9f0a-48cd83c2eaae',
        #...
    ]
    uuids_query_string = '&'.join(["uuids[]={}".format(uuid) for uuid in uuids])

    #query['uuids[]'] = uuids
    #query_string = "{0}&{1}".format(query_string, uuids_query_string).encode()

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

def get_fill_order(oid):
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

    global g_ask_fee, g_bid_fee
    if g_ask_fee == -1 or g_bid_fee == -1:
        ticker = j[0]['market'].split('-')[1]
        info = get_info(ticker, 'KRW')
        g_ask_fee = info['ask_fee']
        g_bid_fee = info['bid_fee']

    print(j)

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
