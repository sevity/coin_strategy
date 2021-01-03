import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from coin import *
import time
from datetime import datetime, timezone, timedelta
from tkinter import *
from tkinter.ttk import *

f = open("../upbit_api_key.txt", 'r')
access_key = f.readline().rstrip()
secret_key = f.readline().rstrip()
f.close()
coin = Coin('upbit',access_key,secret_key)


# return price multiple of ticksize
def tick_round(price):
    t = coin.get_tick_size(price)
    return int(price / t) * t

def cancel_pending_bids(ticker, bLog=True):
    l = coin.get_live_orders(ticker, 'KRW')
    if bLog: print(' cancel pending bids..')
    for (oid, askbid, price, cnt, odt) in l:
        if askbid == 'ask':
            continue
        r = coin.cancel(oid, False)

def cancel_pending_asks(ticker, bLog=True):
    l = coin.get_live_orders(ticker, 'KRW')
    if bLog:print(' cancel pending asks..')
    for (oid, askbid, price, cnt, odt) in l:
        if askbid == 'bid':
            continue
        r = coin.cancel(oid)

window = Tk()
frame1 = Frame(window)
frame2 = Frame(window)
frame1.grid(row=0, column=0)
frame2.grid(row=1, column=0, sticky=W)

window.title("코인 댕댕이")
# window.geometry('350x200')



vTicker = StringVar(value='')
vPrice = StringVar(value='0.0')
vKRW = StringVar(value='0.0')
vOrderCnt = StringVar(value='0.0')
vHoldCnt = StringVar(value='0.0')
vFreeCnt = StringVar(value='0.0')
vAmount = StringVar(value='0')
vKind = StringVar(value='limit1')
flagAllIn = False
def get_price(ticker):
    if vKind.get() == 'limit1':
        if vAskbid.get() == 'bid':
            a = coin.get_bid1(ticker, 'KRW')
        else:
            a = coin.get_ask1(ticker, 'KRW')
    else:
        if vAskbid.get() == 'bid':
            a = coin.get_ask1(ticker, 'KRW')
        else:
            a = coin.get_bid1(ticker, 'KRW')
    return a

def button_update():
    ticker = vTicker.get().upper()
    vTicker.set(ticker)
    if len(ticker)<2:
        print('set ticker!')
        return
    if ticker not in eTicker['values']:
        eTicker['values'] += (ticker,)
    update_cnt()
def update_cnt():
    global flagAllIn
    ticker = vTicker.get()
    krw = coin.get_asset_info('KRW')
    vKRW.set('{:,}'.format(int(krw['free'])))
    a = get_price(ticker)
    vPrice.set('{:,.4f}'.format(a))
    asset = coin.get_asset_info(ticker)
    if 'free' in asset:
        vFreeCnt.set('{:,}'.format(asset['free']))
        vHoldCnt.set('{:,}'.format(asset['total']))
    else:
        vFreeCnt.set('{:,}'.format(0))
        vHoldCnt.set('{:,}'.format(0))
    amount = float(vAmount.get().replace(',',''))
    free_krw = float(vKRW.get().replace(',',''))
    free_cnt = float(vFreeCnt.get().replace(',',''))
    price = get_price(ticker)
    if vAskbid.get() == 'bid':
        amount = min(amount, free_krw)
    else:
        amount = min(amount, price * free_cnt)
    vAmount.set('{:,}'.format(amount))
    order_cnt = amount / price
    free_cnt = float(vFreeCnt.get().replace(',',''))

    flagAllIn = False
    if vAskbid.get() == 'ask':
        order_cnt = min(order_cnt, free_cnt)
        if vHoldCnt.get() == vOrderCnt.get():
            flagAllIn = True
            print('all in')
    else:
        if int(free_krw) == int(amount):
            flagAllIn = True
            print('all in')

    vOrderCnt.set('{:,}'.format(order_cnt))
def reset():
    a = float(0)
    vAmount.set('{:,}'.format(a))
    update_cnt()
def add_100m():
    a = float(vAmount.get().replace(',','')) + 1000000
    vAmount.set('{:,}'.format(a))
    update_cnt()
def add_10m():
    a = float(vAmount.get().replace(',','')) + 100000
    vAmount.set('{:,}'.format(a))
    update_cnt()
def add_1m():
    a = float(vAmount.get().replace(',','')) + 10000
    vAmount.set('{:,}'.format(a))
    update_cnt()
def cancel():
    ticker = vTicker.get().upper()
    vTicker.set(ticker)
    if len(ticker)<2:
        print('set ticker!')
        return
    cancel_pending_bids(ticker)
    cancel_pending_asks(ticker)
    button_update()

def on_kind_limit1():
    button_update()
def on_kind_market():
    button_update()
def on_bid():
    button_update()
def on_ask():
    button_update()
    
    
def order_new():
    button_update()
    ticker = vTicker.get().upper()
    vTicker.set(ticker)
    if len(ticker)<2:
        print('set ticker!')
        return
    askbid = vAskbid.get()
    kind = vKind.get()
    amount = float(vAmount.get().replace(',',''))
    cnt = float(vOrderCnt.get().replace(',',''))
    price = float(vPrice.get().replace(',',''))
    if askbid=='bid':
        if kind == 'limit1':
            if flagAllIn is True:
                cnt *= (1 - 0.0005)  # fee
            coin.limit_buy(ticker, price, cnt)
        else:
            # print(amount)
            if flagAllIn is True:
                print('all amount')
                print('before',amount)
                amount = coin.get_asset_info('KRW')['free']
                amount *= (1 - 0.0005)  # fee
                print('after',amount)

            coin.market_buy(ticker, amount)
    else:
        if kind == 'limit1':
            coin.limit_sell(ticker, price, cnt)
        else:
            if flagAllIn is True:
                print('all amount')
                print('before',amount)
                amount = coin.get_asset_info(ticker)['free']
                print('after',amount)
            coin.market_sell(ticker, cnt)

    

Label(frame1, text = 'ticker').grid(row=0, column=0, sticky=W)
eTicker = Combobox(frame1, width=6, text='XRP', textvariable=vTicker)
eTicker['values'] = ('XRP', 'ETH', 'THETA', 'SC', 'AERGO')
eTicker.current(0)
eTicker.grid(row=0, column=1, sticky=E)
bPriceUpdate = Button(frame1, text='update', command=button_update).grid(row=0, column=2, sticky=W)
Label(frame1, text = 'free KRW').grid(row=1, column=0, sticky=W)
eKRW = Entry(frame1, textvariable=vKRW, state='disabled', justify='right', width=20).grid(row=1, column=1, columnspan=3, sticky=W)
Label(frame1, text = 'askbid').grid(row=2, column=0, sticky=W)
vAskbid = StringVar(value='bid')
rAskbid1 = Radiobutton(frame1, text='bid', value='bid', variable=vAskbid, command=on_bid).grid(row=2, column=1, sticky=W)
rAskbid2 = Radiobutton(frame1, text='ask', value='ask', variable=vAskbid, command=on_ask).grid(row=2, column=2, sticky=W)
Label(frame1, text = 'kind').grid(row=3, column=0, sticky=W)
rKind1 = Radiobutton(frame1, text='limit1', value='limit1', variable=vKind, command=on_kind_limit1).grid(row=3, column=1, sticky=W) 
rKind2 = Radiobutton(frame1, text='market', value='market', variable=vKind, command=on_kind_market).grid(row=3, column=2, sticky=W) 
Label(frame1, text = 'price').grid(row=4, column=0, sticky=W)
ePrice = Entry(frame1, textvariable=vPrice, state='disabled', justify='right', width=20).grid(row=4, column=1)
Label(frame1, text = 'order amount(KRW)').grid(row=5, column=0, sticky=W)
eAmount = Entry(frame1, textvariable=vAmount, justify='right', width=20).grid(row=5, column=1)
bAmount0 = Button(frame1, text='reset', command=reset).grid(row=5, column=2, sticky=W)
bAmount1 = Button(frame1, text='+100M', command=add_100m).grid(row=5, column=3, sticky=W)
bAmount2 = Button(frame1, text='+10M', command=add_10m).grid(row=5, column=4, sticky=W)
bAmount3 = Button(frame1, text='+1M', command=add_1m).grid(row=5, column=5, sticky=W)

Label(frame1, text = 'hold cnt(free)').grid(row=6, column=0, sticky=W)
eHoldCnt = Entry(frame1, textvariable=vFreeCnt, state='disabled', justify='right', width=20).grid(row=6, column=1, columnspan=3, sticky=W)
Label(frame1, text = 'total').grid(row=6, column=2, sticky=W)
eFreeCnt = Entry(frame1, textvariable=vHoldCnt, state='disabled', justify='right', width=20).grid(row=6, column=3, columnspan=3, sticky=W)

Label(frame1, text = 'order cnt').grid(row=7, column=0, sticky=W)
eCnt = Entry(frame1, textvariable=vOrderCnt, state='disabled', justify='right', width=20).grid(row=7, column=1)


Label(frame2, text='').grid(row=0, column=0)

Button(frame2, text='order new', command=order_new).grid(row=1, column=0)
Button(frame2, text='cancel pending askbids', command=cancel).grid(row=1, column=1)


window.mainloop()

