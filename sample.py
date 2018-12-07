from coin import *
import time
from datetime import datetime

api_key = ""
secret_key = ""

coin = Coin('bithumb',api_key,secret_key)
money = coin.get_asset_info('KRW')
xrp = coin.get_asset_info('XRP') # ripple
print('krw..', money)
print('xrp..', xrp)

# coin.market_buy('XRP', 10)
