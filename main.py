import os
from actions.login import Login
import requests
from utils.constants import *
from utils.optionPnl import *
from tda import client

# r = requests.get('https://trade.thinkorswim.com/?symbol=AAPL')
# print(r.text)

t = Login()

# t.get_quote('AAPL').json()
# fund = t.Instrument.Projection.FUNDAMENTAL

# print(t.get_quote('AAPL').json()['AAPL'])
# print(t.search_instruments('AAPL', fund).json()['AAPL']['fundamental'])

# print(client.get_options_chain('AAPL').json())

# print(t.get_option_chain('AAPL').json())

# r = c.get_price_history('AAPL',
#         period_type=client.Client.PriceHistory.PeriodType.YEAR,
#         period=client.Client.PriceHistory.Period.TWENTY_YEARS,
#         frequency_type=client.Client.PriceHistory.FrequencyType.DAILY,
#         frequency=client.Client.PriceHistory.Frequency.DAILY)
# assert r.ok, r.raise_for_status()
# print(json.dumps(r.json(), indent=4))
print(coveredCall('AAPL', 250, '2020-08-07', 450))
