import os
import tdameritrade as td
import tdameritrade.orders.order_builder as o
from Actions.login import login

# login
client_id = os.getenv('TDAMERITRADE_CLIENT_ID')
account_id = os.getenv('TDAMERITRADE_ACCOUNT_ID')
refresh_token = os.getenv('TDAMERITRADE_REFRESH_TOKEN')
t = td.TDClient(
    client_id=client_id,
    refresh_token=refresh_token,
    account_ids=[account_id]
)

# get watchlist
algoListId = os.getenv('TDAMERITRADE_ALGOLIST_ID')
algoList = t.watchlists(account_id, algoListId)['watchlistItems']

# check how stocks are performing
volatilities = {}
for asset in algoList:
    symbol = asset['instrument']['symbol']
    volatilities[symbol] = t.options(symbol)['volatility']

# print(t.quote('C'))
print(volatilities)
