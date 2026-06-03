# AlgoTrading_TD

A local Python script for analyzing options trading opportunities through the TD Ameritrade API. It scans a TD Ameritrade watchlist, computes volatility metrics for each underlying, and evaluates the profit/loss profiles of common options strategies.

Unlike the related serverless [`AlgoTrading_Chalice`](https://github.com/tduic/AlgoTrading_Chalice) webhook bot, this project runs locally as a command-line script driven by `main.py`.

## Features

- **Watchlist scanning** — pulls a configured TD Ameritrade watchlist ("AlgoList") and gathers quotes and fundamentals (beta, average volume) for each symbol.
- **Volatility analysis**:
  - Historical volatility computed from daily price history (annualized standard deviation of log returns).
  - Implied volatility and IV percentile scraped from the thinkorswim web platform via Selenium.
- **Strategy evaluation** (`utils/optionPnl.py`) — calculates breakeven, max gain, max loss, and current P&L for:
  - Covered call
  - Married put
  - Iron condor
  - Long strangle
- **Straddle screening** (`main.py`) — filters watchlist assets by historical volatility and IV percentile, then surfaces viable near-the-money call/put pairs based on a delta/theta and volatility filter.
- **Order helpers** — login flow and order placement scaffolding using `tda-api`'s options order builders (order execution is currently stubbed/commented in `main.py`).

## Tech stack

- Python 3.7
- [`tda-api` / `tdameritrade`](https://pypi.org/project/tdameritrade/) — TD Ameritrade REST client and OAuth
- Selenium + `webdriver-manager` (Chrome) — automated login and scraping IV / IV percentile from thinkorswim

## Project structure

```
main.py                 # entry point: scan watchlist, run straddle logic
actions/login.py        # TD Ameritrade OAuth login (token file or Selenium login flow)
utils/constants.py      # environment-driven config and trade constants
utils/helpers.py        # volatility math, option symbol/date helpers, IV scraping
utils/optionPnl.py      # P&L calculators for options strategies
utils/strategies.py     # scratch/experimental
requirements.txt
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   You will also need `selenium` and `webdriver-manager` for the login flow and IV scraping, plus Google Chrome installed.

2. Set the required environment variables:

   | Variable | Description |
   | --- | --- |
   | `TDAMERITRADE_CLIENT_ID` | TD Ameritrade developer app client ID (the `@AMER.OAUTHAP` suffix is added automatically) |
   | `TDAMERITRADE_TOKEN_PATH` | Path where the OAuth token file is stored |
   | `TDAMERITRADE_REDIRECT_URI` | OAuth redirect URI registered for your app |
   | `TDAMERITRADE_ACCOUNT_ID` | TD Ameritrade account ID |
   | `TDAMERITRADE_ALGOLIST_ID` | ID of the watchlist to scan |

3. For IV scraping, create a `.login` pickle file containing your thinkorswim credentials (`username`, `password`, and security-question answers) as expected by `impliedVolatility()` in `utils/helpers.py`.

## Usage

```bash
python main.py
```

On first run, if no token file exists, a Chrome window opens to complete the TD Ameritrade OAuth login flow and persist a token. Subsequent runs reuse the saved token. The script then scans the watchlist, computes volatility, and prints viable straddle candidates.

## Disclaimer

This is a personal/experimental project for educational purposes. It is not financial advice. Trading options involves substantial risk; use at your own risk.
