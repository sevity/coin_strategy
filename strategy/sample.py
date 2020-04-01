import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from coin import *
import time
from datetime import datetime

f = open("../bithumb_api_key.txt", 'r')
api_key = f.readline().rstrip()
secret_key = f.readline().rstrip()
f.close()

coin = Coin('bithumb',api_key,secret_key)
xrp = coin.get_asset_info('XRP') # ripple
money = coin.get_asset_info('KRW')

print('krw..', money)
print('xrp..', xrp)

# coin.market_buy('XRP', 10)
