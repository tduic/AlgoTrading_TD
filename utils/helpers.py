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

def get_row_count(table):
    return len(table.find_elements_by_tag_name("tr"));

def get_column_count(table):
    return len(table.find_elements_by_xpath("//tr[2]/td"));

def impliedVolatility():
    from selenium import webdriver
    from webdriver_manager.chrome import ChromeDriverManager
    import pickle
    with webdriver.Chrome(ChromeDriverManager().install()) as driver:
        data = pickle.load(open(".login", "rb"))

        # login to ToS web
        driver.get('https://trade.thinkorswim.com/')
        driver.find_element_by_id('username0').send_keys(data['username'])
        driver.find_element_by_id('password').send_keys(data['password'])
        driver.find_element_by_id('accept').click()
        driver.implicitly_wait(10000)
        driver.find_element_by_css_selector('details > summary').click()
        driver.find_element_by_id('stepup_secretquestion0').click()
        question = driver.find_elements_by_css_selector('main > div')[1].find_elements_by_css_selector('p')[1].text[10:]
        driver.find_element_by_id('secretquestion0').send_keys(data[question])
        driver.find_element_by_id('accept').click()
        driver.find_element_by_css_selector('[for=trustthisdevice0_0]').click()
        driver.find_element_by_id('accept').click()

        # switch watchlist to AlgoList and add IV Percentile
        watchlist = driver.find_element_by_css_selector('.watchlist-description')
        watchlist.click()
        driver.find_element_by_css_selector('[aria-label=AlgoList').click()
        driver.find_element_by_css_selector('[aria-label="Column Configuration Collapsed"]').click()
        driver.find_element_by_css_selector('[data-rbd-draggable-id="watchlist-table-table-column-drawer-IV Percentile"]').click()
        driver.find_element_by_css_selector('[aria-label="Column Configuration Expanded"]').click()

        # obtain IV and IV Percentile indices
        headers = driver.find_element_by_css_selector('[data-rbd-droppable-id="watchlist-table-table-header"]')
        row = headers.find_elements_by_xpath("//tr["+str(1)+"]/td")
        ivIndex = 0
        ivpIndex = 0
        for i in range(len(row)) :
            if row[i].text == 'IV':
                ivIndex = i+1
            if row[i].text == 'IV Pctl':
                ivpIndex = i+1

        # get IV and IVP for each asset
        body = driver.find_element_by_id('watchlist-table-body')
        rowCount = get_row_count(body)
        colCount = get_column_count(body)
        print(rowCount, colCount)
        ivCol = body.find_elements_by_xpath("//tr/td["+str(ivIndex+1)+"]")
        ivList = []
        for elem in ivCol:
            ivList.append(elem.text)
        print(ivList)
        time.sleep(10)
