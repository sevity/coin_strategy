import requests
url = "https://api.upbit.com/v1/orderbook"
querystring = {"markets":"KRW-BTC"}
response = requests.request("GET", url, params=querystring)
print(response.text)


import os
import jwt
import uuid
import hashlib
from urllib.parse import urlencode

import requests

server_url = 'https://api.upbit.com'
f = open("../upbit_api_key.txt", 'r')
access_key = f.readline().rstrip()
secret_key = f.readline().rstrip()
f.close()
#up = Coin('upbit',access_key,secret_key)

payload = {
    'access_key': access_key,
    'nonce': str(uuid.uuid4()),
}

jwt_token = jwt.encode(payload, secret_key).decode('utf-8')
authorize_token = 'Bearer {}'.format(jwt_token)
headers = {"Authorization": authorize_token}

res = requests.get(server_url + "/v1/accounts", headers=headers)

print(res.json())