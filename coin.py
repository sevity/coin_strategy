from multimethods import multimethod #https://pypi.org/project/multimethods/

import exchange.bithumb.sevity_coin_api
import exchange.upbit.sevity_coin_api
import exchange.binance.sevity_coin_api

class Coin:
    def __init__(self, exchange_name, api_key, secret_key):
        self._api = None
        if exchange_name == 'bithumb':
            self._api = exchange.bithumb.sevity_coin_api
        elif exchange_name == 'upbit':
            self._api = exchange.upbit.sevity_coin_api
        elif exchange_name == 'binance':
            self._api = exchange.binance.sevity_coin_api
        else:
            assert False
        self._api.set_key(api_key, secret_key)

    def get_price(self, ticker, currency):
        return self._api.get_price(ticker, currency)

    def get_asset_info(self, currency):
        return self._api.get_asset_info(currency)

    def get_balance_all(self):
        return self._api.get_balance_all(False)

    def market_buy(self, ticker, cnt):
        return self._api.market_buy(ticker, cnt)

    def market_sell(self, ticker, cnt):
        return self._api.market_sell(ticker, cnt)

    def limit_buy(self, ticker, price, cnt):
        return self._api.limit_buy(ticker, price, cnt)

    def limit_sell(self, ticker, price, cnt):
        return self._api.limit_sell(ticker, price, cnt)

    def cancel(self, oid):
        return self._api.cancel(oid)

    @multimethod(str, str)
    def get_live_orders(self, ticker, currency):
        return self._api.get_live_orders(ticker, currency)

    @multimethod(str)
    def get_live_orders(self, currency):
        return self._api.get_live_orders(currency)

    def get_info(self, ticker, currency):
        return self._api.get_info(ticker, currency)