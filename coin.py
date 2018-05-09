import bithumb.sevity_coin_api
import binance.sevity_coin_api

class Coin:
    def __init__(self, exchange_name):
        self._api = None
        if exchange_name == 'bithumb':
            self._api = bithumb.sevity_coin_api.api
        elif exchange_name == 'binance':
            pass
            # self._api = binance.sevity_coin_api.api
        else:
            assert False
