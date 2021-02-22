import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from coin import *
import time
import math
import random
import copy
from datetime import datetime, timezone, timedelta
import telegram
import numpy as np
from collections import deque
import ast
from sty import fg, bg, ef, rs
import argparse

# 설명 ########################################################################
# BTC개수를 늘리는걸 최우선으로 하여, KRW로 bid후 ask하는 전략
# param #######################################################################
KRW_DELTA = 200000  # 이걸 기준으로 촘촘하게 주문을 낸다.
# BETTING = 10000    # 초기버전은 고정배팅으로 가보자
BETTING = 0  # AUTO
MAX_BETTING = 2000000
###############################################################################
# legacy or fixed
FEE = 0.0005
MIN_BET_FOR_AUTO = 200000
MINOR_DELTA = 0  # sholud be multiple of 1000
###############################################################################

token = '1604518349:AAFoH7TE40SaoegpSGBd5Oe4NsceqH78JTI'
bot = telegram.Bot(token=token)
def send_telegram(msg):
    # print(msg)
    try:
        bot.sendMessage(chat_id=170583240, text=msg)
    except:
        pass
send_telegram('haha')
