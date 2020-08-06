import os
from actions.login import Login
import requests
from utils.constants import *
from utils.optionPnl import *
from utils.helpers import *
from tda import client

def main():
    t = Login()

    algolist = t.get_watchlist(ACCOUNT_ID, ALGOLIST_ID).json()['watchlistItems']

    for asset in algolist:
        symbol = asset['instrument']['symbol']
        quote = t.get_quote(symbol).json()
        fundamentalEnum = t.Instrument.Projection.FUNDAMENTAL
        fund = t.search_instruments(symbol, fundamentalEnum).json()[symbol]['fundamental']
        beta = fund['beta']
        vol10DayAvg = fund['vol10DayAvg']
        historyDays = 90
        hv = historicalVolatility(t, symbol, 90)


if __name__ == '__main__':
    main()
