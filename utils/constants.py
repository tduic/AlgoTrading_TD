import os

# environment vars
TOKEN_PATH = os.getenv('TDAMERITRADE_TOKEN_PATH')
_CLIENT_ID = os.getenv('TDAMERITRADE_CLIENT_ID')
# None when unset so importing never fails; Login() raises a clear error instead
API_KEY = _CLIENT_ID + '@AMER.OAUTHAP' if _CLIENT_ID else None
REDIRECT_URI = os.getenv('TDAMERITRADE_REDIRECT_URI')
ACCOUNT_ID = os.getenv('TDAMERITRADE_ACCOUNT_ID')
ALGOLIST_ID = os.getenv('TDAMERITRADE_ALGOLIST_ID')

# options calculations
SHARES_PER_CONTRACT = 100
OPTIONS_CONTRACT_COMMISSION = .65
COMMISSION_PER_SHARE = OPTIONS_CONTRACT_COMMISSION / SHARES_PER_CONTRACT

# trade constants
STOP_LIMIT = 30
