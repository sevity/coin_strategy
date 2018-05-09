import exchange.bithumb.sevity_coin_api
import exchange.binance.sevity_coin_api

class Coin:
    def __init__(self, exchange_name):
        self._api = None
        if exchange_name == 'bithumb':
            self._api = exchange.bithumb.sevity_coin_api
        elif exchange_name == 'binance':
            self._api = exchange.binance.sevity_coin_api
        else:
            assert False

    def get_price(self, ticker, currency):
        return self._api.get_price(ticker, currency)

    def get_krw_info(self):
        return self._api.get_krw_info()

    def get_balance_all(self):
        return self._api.get_balance_all(False)

    def market_buy(self, ticker, cnt):
        return self._api.market_buy(ticker, cnt)

    def market_sell(self, ticker, cnt):
        return self._api.market_sell(ticker, cnt)
