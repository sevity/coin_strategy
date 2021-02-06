# -*- coding: utf-8 -*-
#! /usr/bin/env python
from __future__ import absolute_import
import time
import socket
import json


def send_metric_telegraf(m):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(
            json.dumps({'metric_name': 'updown_metrics', 'total_money_in_btc_cnt': m['total_btc_cnt'],
                        'total_krw': m['total_krw'], 'btc_price': m['btc_price'], 'btc_ratio': m['btc_ratio'], 'p_orders_cnt': m['p_orders_cnt']}).encode(),
            ('localhost', 8094)
        )
        sock.close()
    except socket.error as e:
        print(f'Got error: {e}')

