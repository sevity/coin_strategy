from coin import *
import time
from datetime import datetime

f = open("../upbit_api_key.txt", 'r')
access_key = f.readline().rstrip()
secret_key = f.readline().rstrip()
f.close()

coin = Coin('upbit',access_key,secret_key)
btc_price = coin.get_price('BTC', 'KRW')
eos_price = coin.get_price('EOS', 'KRW')

print('BTC price:', btc_price)
print('EOS price:', eos_price)
