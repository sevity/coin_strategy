from coin import *
import time
from datetime import datetime


api_key = ""
secret_key = ""

coin = Coin('bithumb',api_key,secret_key)
money = coin.get_asset_info('KRW')
btc = coin.get_asset_info('BTC') # bitcoin
xrp = coin.get_asset_info('XRP') # ripple
print(money, btc, xrp)

bt.market_sell('XRP', 1)
