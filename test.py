from coin import *
import time
from datetime import datetime



# param #######################################################################
THRESHOLD = 50
COOL_TIME = 10
TRADE_CNT = 1
###############################################################################




bt = Coin('bithumb')
bn = Coin('binance')

print('KRW info', bt.get_krw_info())
print('my coins', bt.get_balance_all())

avg_gap = 0
skip_turn = 10
gap_sum = 0
cnt = 0
while True:
    try:
        a = bt.get_price('EOS', 'KRW')
        b = bn.get_price('EOS', 'BTC')
        c = bt.get_price('BTC', 'KRW')
    except Exception as e:
        print('err', e)
        time.sleep(1)
        continue
    gap = b*c-a
    gap_sum += gap
    cnt += 1
    avg_gap = gap_sum / cnt
    adj_gap = gap - avg_gap

    print(datetime.now().strftime("%m-%d %H:%M:%S"), 'EOS price..', 'bithumb', a, 'binance', b*c, 'gap', gap, 'avg_gap', avg_gap, 'adj_gap', adj_gap)
    if skip_turn <= 0:
        if adj_gap >= THRESHOLD:
            bt.market_buy('EOS', TRADE_CNT)
            skip_turn = COOL_TIME
        elif adj_gap <= -THRESHOLD:
            bt.market_sell('EOS', TRADE_CNT)
            skip_turn = COOL_TIME
    else:
        skip_turn -= 1
        print('skip...')
    time.sleep(1)
