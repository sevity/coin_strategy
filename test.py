from coin import *
import time
bt = Coin('bithumb')
bn = Coin('binance')

print 'KRW info', bt.get_krw_info()
print 'my coins', bt.get_balance_all()

skip_turn = 0
while True:
    a = bt.get_price('EOS', 'KRW')
    b = bn.get_price('EOS', 'BTC')
    c = bt.get_price('BTC', 'KRW')
    gap = b*c-a
    print 'EOS price..', 'bithumb', a, 'binance', b*c, 'gap', gap
    if skip_turn > 0:
        skip_turn -= 1
        if gap > 100:
            bt.market_buy('EOS', 1)
            skip_turn = 10
        elif gap < -100:
            bt.market_sell('EOS', 1)
            skip_turn = 10
    time.sleep(1)
