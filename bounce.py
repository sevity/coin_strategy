from coin import *
import time
from datetime import datetime


# param #######################################################################
TICK_MIN = 5
COINS = ['XRP', 'EOS', 'BTC', 'ETH']
DOWN_ENOUGH_TIMES = 3
BOUNCE_CNT = 4
TRADE_COIN = 'XRP'
GOAL_PERCENT = 5
LOSS_CUT_PERCENT = 2
###############################################################################
# This strategy checks every TICK_MIN
# and buys TRADE_COIN when all prices of COINS goes DOWN_ENOUGH_TIMES and atleast BOUNCE_CNT of coins' price are starting to goes up
# and sell it when it reaches the GOAL_PERCENT and must set LOSS_CUT_PERCENT!

bt = Coin('bithumb')

CONTINUOUS_DOWN_CNT = 0
LAST_PRICES = []
for coin in COINS:
    a = bt.get_price(coin, 'KRW')
    LAST_PRICES.append(a)

STAGES = ['CHECK_DOWN', 'CHECK_BOUNCE', 'TRY_TO_SELL']
STAGE = STAGES[0]


def buy_all(ticker):
    FEE = 0.0015
    money = bt.get_asset_info('KRW')['free']
    price = bt.get_price(ticker, 'KRW') * (1.0 + FEE)
    buy_cnt = round(money / price, 4)
    buy_price = bt.market_buy(ticker, buy_cnt)[0]
    print('buy_all..', ticker, ' cnt:', buy_cnt, 'buy_price', buy_price)
    return buy_price


def sell_all(ticker):
    cnt = round(bt.get_asset_info(ticker)['free'], 4)
    sell_price = bt.market_sell(ticker, cnt)[0]
    print('sell_all..', ticker, ' cnt:', cnt, 'sell_price', sell_price)
    return sell_price


BUY_PRICE = 0
while True:
    try:
        print(datetime.now().strftime("%m-%d %H:%M:%S"))
        print('KRW..', bt.get_asset_info('KRW'))
        print('Stage: ', STAGE)
        if STAGE == STAGES[0]:
            DOWN_CNT = 0
            for coin in COINS:
                ix = COINS.index(coin)
                a = bt.get_price(coin, 'KRW')
                b = bt.get_asset_info(coin)
                if LAST_PRICES[ix] > a:
                    DOWN_CNT += 1
                    UPDOWN = 'DN!!!!!!!!!!!!!!!'
                else:
                    UPDOWN = 'UP_HOLD'
                LAST_PRICES[ix] = a
                print('{}..'.format(coin), b, 'price..', a, UPDOWN)
            if DOWN_CNT  == len(COINS):
                CONTINUOUS_DOWN_CNT += 1
            else:
                CONTINUOUS_DOWN_CNT = 0
            print('continuous down cnt..', CONTINUOUS_DOWN_CNT)
            if CONTINUOUS_DOWN_CNT >= DOWN_ENOUGH_TIMES:
                print('DOWN HIT!')
                STAGE = STAGES[1]
        elif STAGE == STAGES[1]:
            UP_CNT = 0
            for coin in COINS:
                ix = COINS.index(coin)
                a = bt.get_price(coin, 'KRW')
                b = bt.get_asset_info(coin)
                if LAST_PRICES[ix] < a:
                    UP_CNT += 1
                    UPDOWN = 'UP!!!!!!!!!!!!!!!!!!'
                else:
                    UPDOWN = 'DN_HOLD'
                print('{}..'.format(coin), b, 'price..', a, UPDOWN)
            print('bounce cnt..', UP_CNT)
            if UP_CNT >= BOUNCE_CNT:
                print('BOUNCE HIT!')
                BUY_PRICE = buy_all(TRADE_COIN)
                STAGE = STAGES[2]
        elif STAGE == STAGES[2]:
            assert BUY_PRICE > 0
            sell_price = BUY_PRICE * (100.0 + GOAL_PERCENT) / 100.0
            cut_loss_price = BUY_PRICE * (100.0 - LOSS_CUT_PERCENT) / 100.0
            print('buy price: ', BUY_PRICE, 'sell_price: ', sell_price, 'cut_loss_price: ', cut_loss_price)
            for coin in COINS:
                ix = COINS.index(coin)
                a = bt.get_price(coin, 'KRW')
                b = bt.get_asset_info(coin)
                print('{}..'.format(coin), b, 'price..', a, UPDOWN)
            p = bt.get_price(TRADE_COIN, 'KRW')
            if p >= sell_price:
                print('GOOD~ reached the goal price')
                sell_all(TRADE_COIN)
                STAGE = STAGES[0]
            elif p <= cut_loss_price:
                print('CUT LOSS!!')
                sell_all(TRADE_COIN)
                STAGE = STAGES[0]

    except Exception as e:
        print('err', e)
        time.sleep(1)
        continue
    
    time.sleep(TICK_MIN * 60)
    continue

