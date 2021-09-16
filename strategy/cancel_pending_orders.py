import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from coin import *
import time
from datetime import datetime, timezone, timedelta
import argparse

parser = argparse.ArgumentParser(description='cancel pending orders')
parser.add_argument('--ticker', '-t', required=True)
parser.add_argument('--askbid', required=False, default='all', choices=['ask', 'bid', 'all'])
parser.add_argument('--market', '-m', required=False, default='ALL', 
    choices=['ALL', 'KRW','BTC', 'all', 'krw', 'btc'])
args = parser.parse_args()
ticker = args.ticker.upper()
askbid = args.askbid.lower()
market = args.market.upper()
print('ticker:', ticker, 'askbid:', askbid, 'market:', market)

f = open("../upbit_api_key.txt", 'r')
access_key = f.readline().rstrip()
secret_key = f.readline().rstrip()
f.close()
coin = Coin('upbit',access_key,secret_key)

if market == 'ALL':
    l = coin.get_live_orders(ticker, 'KRW')
    if l != 'bad request':
        for (oid, askbid_, price, cnt, odt) in l:
            if askbid == 'all' or askbid_ == askbid:
                coin.cancel(oid, True)
    l = coin.get_live_orders(ticker, 'BTC')
    for (oid, askbid_, price, cnt, odt) in l:
        if askbid == 'all' or askbid_ == askbid:
            coin.cancel(oid, True)
else:
    l = coin.get_live_orders(ticker, market)
    for (oid, askbid_, price, cnt, odt) in l:
        if askbid == 'all' or askbid_ == askbid:
            coin.cancel(oid, True)

os.system("rm ../obj/*{}*".format(ticker))
