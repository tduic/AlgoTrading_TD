import os
import tdameritrade as td
import tdameritrade.orders.order_builder as o
from actions.login import *
from utils.optionPnl import coveredCall

# get watchlist
algolist_id = os.getenv('TDAMERITRADE_ALGOLIST_ID')
algoList = t.watchlists(account_id, algolist_id)['watchlistItems']

# check how stocks are performing
volatilities = {}
for asset in algoList:
    symbol = asset['instrument']['symbol']
    volatilities[symbol] = t.options(symbol)['volatility']
