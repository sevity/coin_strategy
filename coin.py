from multimethods import multimethod #https://pypi.org/project/multimethods/

import exchange.bithumb.sevity_coin_api
import exchange.upbit.sevity_coin_api
import exchange.binance.sevity_coin_api
from sty import fg, bg, ef, rs
import time
import math
def log(msg):
    print('  ' + fg.li_black + msg + fg.rs)

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
    def get_bid1(self, ticker, currency):
        return self._api.get_bid1(ticker, currency)
    def get_ask1(self, ticker, currency):
        return self._api.get_ask1(ticker, currency)

    def get_asset_info(self, currency):
        return self._api.get_asset_info(currency)

    def get_balance_all(self):
        return self._api.get_balance_all(False)

    def market_buy(self, ticker, cnt, bLog=True, bConfirm=False):
        r =  self._api.market_buy(ticker, cnt, bLog, bConfirm)
        return r

    def market_sell(self, ticker, cnt, bLog=True, bConfirm=False):
        return self._api.market_sell(ticker, cnt, bLog, bConfirm)

    def limit_buy(self, ticker, price, cnt, bLog=True, bConfirm=False):
        return self._api.limit_buy(ticker, price, cnt, bLog, bConfirm)

    def limit_sell(self, ticker, price, cnt, bLog=True, bConfirm=False):
        return self._api.limit_sell(ticker, price, cnt, bLog, bConfirm)
        
    def limit_buy_btc(self, ticker, price, cnt, bLog=True, bConfirm=False):
        return self._api.limit_buy_btc(ticker, price, cnt, bLog, bConfirm)

    def limit_sell_btc(self, ticker, price, cnt, bLog=True, bConfirm=False):
        return self._api.limit_sell_btc(ticker, price, cnt, bLog, bConfirm)

    def cancel(self, oid, bLog=True):
        return self._api.cancel(oid, bLog)

    @multimethod(str, str)
    def get_live_orders(self, ticker, currency):
        r = 'error'
        while str(r) == 'error':
            r = self._api.get_live_orders(ticker, currency)
            if str(r) == 'error':
                time.sleep(5)
                #log('get_live_orders retry..')
        return r

    @multimethod(str, str)
    def get_live_orders_ext(self, ticker, currency):
        r = 'error'
        while str(r) == 'error':
            r = self._api.get_live_orders_ext(ticker, currency)
            if str(r) == 'error':
                time.sleep(5)
                log('get_live_orders_ext error retry..')
        return r
        # return self._api.get_live_orders_ext(ticker, currency)

    @multimethod(str)
    def get_live_orders(self, currency):
        return self._api.get_live_orders(currency)

    def get_order_state(self, oid):
        return self._api.get_order_state(oid)

    def get_fill_order(self, oid):
        return self._api.get_fill_order(oid)

    def get_info(self, ticker, currency):
        return self._api.get_info(ticker, currency)

    # https://upbit.com/service_center/guide
    # https://docs.upbit.com/docs/market-info-trade-price-detail
    def get_tick_size(self, price):
        if price < 10: return 0.01
        if price < 100: return 0.1
        if price < 1000: return 1
        if price < 10000: return 5
        if price < 100000: return 10
        if price < 500000: return 50
        if price < 1000000: return 100
        if price < 2000000: return 500
        return 1000 # BTC

    def satoshi_floor(self, price):
        return math.floor(price*100000000)/100000000

    def satoshi_round(self, price):
        return round(price, 8)



