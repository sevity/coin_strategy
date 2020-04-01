from coin import *
import time
from datetime import datetime

api_key = "e3653ee4a58434abf5fba29f2797de9a"
secret_key = ""

coin = Coin('bithumb',api_key,secret_key)
xrp = coin.get_asset_info('XRP') # ripple
money = coin.get_asset_info('KRW')

print('krw..', money)
print('xrp..', xrp)

# coin.market_buy('XRP', 10)
