from coin import *
import time
bt = Coin('bithumb')
bn = Coin('binance')

print 'KRW info', bt.get_krw_info()
print 'my coins', bt.get_balance_all()

avg_gap = 0
skip_turn = 0
gap_sum = 0
cnt = 0
while True:
    a = bt.get_price('EOS', 'KRW')
    b = bn.get_price('EOS', 'BTC')
    c = bt.get_price('BTC', 'KRW')
    gap = b*c-a
    gap_sum += gap
    cnt += 1
    avg_gap = gap_sum / cnt

    print 'EOS price..', 'bithumb', a, 'binance', b*c, 'gap', gap, 'avg_gap', avg_gap, 'adj_gap', gap - avg_gap
    gap -= avg_gap
    if skip_turn > 0:
        skip_turn -= 1
        if gap > 50:
            bt.market_buy('EOS', 1)
            skip_turn = 10
        elif gap < -50:
            bt.market_sell('EOS', 1)
            skip_turn = 10
    time.sleep(1)
