import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from coin import *
import time
from datetime import datetime, timezone, timedelta
from tkinter import *

f = open("../upbit_api_key.txt", 'r')
access_key = f.readline().rstrip()
secret_key = f.readline().rstrip()
f.close()
coin = Coin('upbit',access_key,secret_key)



def cancel_pending_bids(bLog=True):
    l = coin.get_live_orders('BTC', 'KRW')
    if bLog: print(' cancel pending bids..')
    for (oid, askbid, price, cnt, odt) in l:
        if askbid == 'ask':
            continue
        r = coin.cancel(oid, False)

def cancel_pending_asks(bLog=True):
    l = coin.get_live_orders('BTC', 'KRW')
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



vAmount = StringVar(value='0')
def reset():
    a = float(0)
    vAmount.set('{:,}'.format(a))
def add_100m():
    a = float(vAmount.get().replace(',','')) + 1000000
    vAmount.set('{:,}'.format(a))
def add_10m():
    a = float(vAmount.get().replace(',','')) + 100000
    vAmount.set('{:,}'.format(a))
def add_1m():
    a = float(vAmount.get().replace(',','')) + 10000
    vAmount.set('{:,}'.format(a))

vTicker = StringVar(value='')
vPrice = StringVar(value='0.0')
vCnt = StringVar(value='0.0')
def button_update():
    ticker = vTicker.get()
    if len(ticker)<3:
        print('set ticker!')
        return
    a = coin.get_price(ticker, 'KRW')
    vPrice.set('{:,}'.format(a))
    

    

Label(frame1, text = 'ticker').grid(row=0, column=0, sticky=W)
eTicker = Entry(frame1, width=5, textvariable=vTicker).grid(row=0, column=1, sticky=W)
Label(frame1, text = 'askbid').grid(row=1, column=0, sticky=W)
vAskbid = StringVar(value='bid')
rAskbid1 = Radiobutton(frame1, text='bid', value='bid', variable=vAskbid).grid(row=1, column=1, sticky=W)
rAskbid2 = Radiobutton(frame1, text='ask', value='ask', variable=vAskbid).grid(row=1, column=2, sticky=W)
Label(frame1, text = 'kind').grid(row=2, column=0, sticky=W)
vKind = StringVar(value='limit1')
rKind1 = Radiobutton(frame1, text='limit1', value='limit1', variable=vKind).grid(row=2, column=1, sticky=W) 
rKind2 = Radiobutton(frame1, text='market', value='market', variable=vKind).grid(row=2, column=2, sticky=W) 
rKind3 = Radiobutton(frame1, text='limit', value='limit', variable=vKind).grid(row=2, column=3, sticky=W) 
Label(frame1, text = 'price').grid(row=3, column=0, sticky=W)
ePrice = Entry(frame1, textvariable=vPrice, state='disabled', justify='right', width=20).grid(row=3, column=1)
bPriceUpdate = Button(frame1, text='update', command=button_update).grid(row=3, column=2, sticky=W)
Label(frame1, text = 'order amount(KRW)').grid(row=4, column=0, sticky=W)
eAmount = Entry(frame1, textvariable=vAmount, justify='right', width=20).grid(row=4, column=1)
bAmount0 = Button(frame1, text='reset', command=reset).grid(row=4, column=2, sticky=W)
bAmount1 = Button(frame1, text='+100M', command=add_100m).grid(row=4, column=3, sticky=W)
bAmount2 = Button(frame1, text='+10M', command=add_10m).grid(row=4, column=4, sticky=W)
bAmount3 = Button(frame1, text='+1M', command=add_1m).grid(row=4, column=5, sticky=W)
Label(frame1, text = 'order cnt').grid(row=5, column=0, sticky=W)
eCnt = Entry(frame1, textvariable=vCnt, state='disabled', justify='right', width=20).grid(row=5, column=1)


Label(frame2, text='').grid(row=0, column=0)

Button(frame2, text='order new').grid(row=1, column=0)
Button(frame2, text='cancel pending askbids').grid(row=1, column=1)


window.mainloop()

