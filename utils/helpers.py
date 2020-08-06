import time, math
from datetime import date, datetime, timedelta
from utils.constants import *

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

def isLongUnderlying(t, asset, contracts):
    neededShares = SHARES_PER_CONTRACT * contracts
    posEnum = t.Account.Fields.POSITIONS
    positions = t.accounts(ACCOUNT_ID, posEnum).json()['securitiesAccount']['positions']
    for pos in positions:
        if pos['instrument']['symbol'] == asset:
            return pos['longQuantity'] >= neededShares
    return False

def historicalVolatility(t, symbol, n):
    ph = t.PriceHistory
    td = timedelta(n)
    priceHistory = t.get_price_history(
        symbol,
        period_type=ph.PeriodType.MONTH,
        frequency_type=ph.FrequencyType.DAILY,
        frequency=ph.Frequency.DAILY,
        start_datetime=datetime.today() - td,
        need_extended_hours_data="true"
    ).json()['candles']

    # step 1 -- calculate returns
    dailyReturns = []
    for i in range(1, len(priceHistory)):
        dailyReturns.append(math.log(priceHistory[i]['close'] / priceHistory[i-1]['close']))

    # step 2 -- std dev of returns
    avgReturn = sum(dailyReturns) / len(dailyReturns)
    dailyReturnDevs = []
    for r in dailyReturns:
        dailyReturnDevs.append((r - avgReturn) ** 2)
    returnVariance = sum(dailyReturnDevs) / len(dailyReturnDevs)
    stdDev = math.sqrt(returnVariance)
    stdDevAnnualized = stdDev * math.sqrt(252)

    return stdDevAnnualized
