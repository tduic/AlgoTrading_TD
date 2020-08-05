import time
from datetime import date, datetime
import utils.constants

def cmp(a, b):
    return (a > b) - (a < b)

def getDaysToExpiry(expiry):
    # number of days to given expiry from today
    today = date.today()
    expireDate = datetime.strptime(expiry, '%Y-%m-%d').date()
    return abs(expireDate-today).days

def makeOptionDateStr(expiry):
    # creates string passable to option chain to obtain options for specific expiry
    # takes date with format YYYY-MM-DD and returns string with format YYYY-MM-DD:#
    daysToExpiry = getDaysToExpiry(expiry)
    return '{0}:{1}'.format(expiry, daysToExpiry)

def makeOptionSymbolStr(asset, expiry, strike, optionType):
    strike = int(strike) if int(strike) == strike else strike
    year, month, day = expiry.split('-')
    putCall = 'C' if optionType == 'call' else 'P'
    return '{0}_{1}{2}{3}{4}{5}'.format(asset, month, day, year[-2:], putCall, strike)

def isLongUnderlying(asset, contracts):
    neededShares = SHARES_PER_CONTRACT * contracts
    positions = t.accounts('positions')[account_id]['securitiesAccount']['positions']
    for pos in positions:
        if pos['instrument']['symbol'] == asset:
            return pos['longQuantity'] >= neededShares
    return False
