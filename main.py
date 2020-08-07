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

    ivList, ivpList = impliedVolatility()

    algoAssets = {}
    for i in range(len(algolist)):
        asset = {}
        symbol = algolist[i]['instrument']['symbol']
        quote = t.get_quote(symbol).json()[symbol]
        fundamentalEnum = t.Instrument.Projection.FUNDAMENTAL
        fund = t.search_instruments(symbol, fundamentalEnum).json()[symbol]['fundamental']
        asset['beta'] = fund['beta']
        asset['vol10DayAvg'] = fund['vol10DayAvg']
        asset['vol3MonthAvg'] = fund['vol3MonthAvg']
        historyDays = 90
        asset['hv'] = historicalVolatility(t, symbol, historyDays)
        asset['iv'] = ivList[i]
        asset['ivp'] = ivpList[i]
        algoAssets[symbol] = asset

if __name__ == '__main__':
    main()
