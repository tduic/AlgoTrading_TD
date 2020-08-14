import os, math, time
from actions.login import Login
from datetime import date, datetime, timedelta
from utils.constants import *
from utils.helpers import *
from utils.optionPnl import *
from tda import client
from tda.orders.options import *

def setAssets(t):
    algolist = t.get_watchlist(ACCOUNT_ID, ALGOLIST_ID).json()['watchlistItems']
    ivList, ivpList = impliedVolatility()

    algoAssets = {}
    for i in range(len(algolist)):
        asset = {}
        symbol = algolist[i]['instrument']['symbol']
        quote = t.get_quote(symbol).json()[symbol]
        fundamentalEnum = t.Instrument.Projection.FUNDAMENTAL
        fund = t.search_instruments(symbol, fundamentalEnum).json()[symbol]['fundamental']
        asset['price'] = quote['lastPrice']
        asset['beta'] = fund['beta']
        asset['vol10DayAvg'] = fund['vol10DayAvg']
        asset['vol3MonthAvg'] = fund['vol3MonthAvg']
        historyDays = 90
        asset['hv'] = historicalVolatility(t, symbol, historyDays)
        asset['iv'] = float(ivList[i])
        asset['ivp'] = float(ivpList[i])
        algoAssets[symbol] = asset
    return algoAssets

def getRange(asset):
    return asset['price'] * asset['iv']/100 * math.sqrt(8 / 365)

def straddleLogic(t, assets):
    for symbol, asset in assets.items():
        if asset['hv'] > .5 and asset['ivp'] < 45:
            strikeRange = getRange(asset)
            calls = t.get_option_chain(symbol).json()['callExpDateMap']['2020-08-21:7']
            puts = t.get_option_chain(symbol).json()['putExpDateMap']['2020-08-21:7']
            viables = viableOptions(asset['price'], calls, puts, strikeRange)
    return viables

def main():
    t = Login()
    algoAssets = setAssets(t)
    straddles = straddleLogic(t, algoAssets)

    # symbol = OptionSymbol(symbol, expiry, putCall, strike)
    # option = option_buy_to_open_limit(symbol, quantity, price)
    # order = place_order(t, ACCOUNT_ID, option)

if __name__ == '__main__':
    main()

