"""utils/helpers.py: date/symbol helpers, historical volatility, position
checks, straddle screening, and the thinkorswim IV scrape (fake Selenium)."""
import datetime as real_dt
import math
import pickle
import statistics
import sys

import pytest
from fakes import El, FakeDriver, FakeTD

from utils import constants, helpers


@pytest.fixture
def today(monkeypatch):
    class FakeDate(real_dt.date):
        @classmethod
        def today(cls):
            return cls(2020, 8, 18)
    monkeypatch.setattr(helpers, "date", FakeDate)
    return FakeDate.today()


def test_constants_from_env():
    assert constants.API_KEY == "TESTCLIENT@AMER.OAUTHAP"
    assert constants.COMMISSION_PER_SHARE == pytest.approx(0.0065)


def test_cmp():
    assert (helpers.cmp(1, 2), helpers.cmp(2, 2), helpers.cmp(3, 2)) == (-1, 0, 1)


def test_read_write_file(tmp_path):
    p = tmp_path / "x.txt"
    helpers.writeFile(p, "wt", "abc")
    helpers.writeFile(p, "at", "def")
    assert helpers.readFile(p, "rt") == "abc\ndef\n"


def test_days_to_expiry_and_chain_key(today):
    assert helpers.getDaysToExpiry("2020-08-21") == 3
    assert helpers.getDaysToExpiry("2020-08-11") == 7          # absolute distance
    assert helpers.makeOptionDateStr("2020-08-21") == "2020-08-21:3"


@pytest.mark.parametrize("strike, kind, want", [
    (105, "call", "AAPL_082120C105"),
    (105.0, "call", "AAPL_082120C105"),
    (102.5, "put", "AAPL_082120P102.5"),
])
def test_option_symbol(strike, kind, want):
    assert helpers.makeOptionSymbolStr("AAPL", "2020-08-21", strike, kind) == want


def test_is_long_underlying():
    t = FakeTD(positions=[{"instrument": {"symbol": "AAPL"}, "longQuantity": 200},
                          {"instrument": {"symbol": "MSFT"}, "longQuantity": 50}])
    assert helpers.isLongUnderlying(t, "AAPL", 2) is True
    assert helpers.isLongUnderlying(t, "AAPL", 3) is False
    assert helpers.isLongUnderlying(t, "MSFT", 1) is False
    assert helpers.isLongUnderlying(t, "TSLA", 1) is False
    assert t.calls[0] == ("accounts", constants.ACCOUNT_ID, "positions")


def test_historical_volatility_is_annualized_stdev_of_log_returns():
    closes = [100.0, 101.0, 99.5, 102.0, 101.0, 103.5]
    t = FakeTD(candles={"AAPL": closes})
    rets = [math.log(b / a) for a, b in zip(closes, closes[1:])]
    want = statistics.pstdev(rets) * math.sqrt(252)
    assert helpers.historicalVolatility(t, "AAPL", 90) == pytest.approx(want)
    (_, symbol, kwargs), = t.calls
    assert kwargs["period_type"] == "month" and kwargs["frequency_type"] == "daily"


def test_historical_volatility_flat_prices_is_zero():
    t = FakeTD(candles={"X": [50.0] * 10})
    assert helpers.historicalVolatility(t, "X", 30) == 0.0


def _greeks(delta, theta, vol):
    return [{"delta": str(delta), "theta": str(theta), "volatility": str(vol)}]


def test_viable_options_screen():
    calls = {"95.0": _greeks(0.6, -0.05, 15),     # outside the strike range
             "99.0": _greeks(0.5, -0.05, 15),     # viable pair
             "100.0": _greeks(0.1, -0.05, 15),    # call fails delta > -5*theta
             "101.0": _greeks(0.5, -0.05, 25)}    # call IV too high
    puts = {"95.0": _greeks(-0.4, -0.05, 15),
            "99.0": _greeks(-0.2, -0.05, 15),
            "100.0": _greeks(-0.2, -0.05, 15),
            "101.0": _greeks(-0.2, -0.05, 15)}
    got = helpers.viableOptions(100.0, calls, puts, strikeRange=3.0)
    assert got == [(calls["99.0"][0], puts["99.0"][0])]
    puts["99.0"] = _greeks(-0.3, -0.05, 15)       # put fails delta > 5*theta
    assert helpers.viableOptions(100.0, calls, puts, 3.0) == []


@pytest.mark.xfail(strict=True, raises=NameError,
                   reason="BUG: stopLoss() references an undefined WORKING constant")
def test_stop_loss_is_unfinished():
    class WithOrders(FakeTD):
        def get_orders(self, account_id, status):
            return []
    helpers.stopLoss(WithOrders())


def test_implied_volatility_scrape(tmp_path, monkeypatch):
    creds = {"username": "u", "password": "p", "pet?": "rex"}
    (tmp_path / ".login").write_bytes(pickle.dumps(creds))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(helpers.time, "sleep", lambda s: None)

    log = []
    header = [El(t) for t in ("Symbol", "Last", "IV", "IV Pctl")]
    rows = [El() for _ in range(2)]
    body = El(children={
        ("tag*", "tr"): rows,
        ("xpath*", "//tr[2]/td"): [El()] * 4,
        ("xpath*", "//tr/td[4]"): [El("35.2%"), El("61")],
        ("xpath*", "//tr/td[5]"): [El("12%"), El("88.5%")],
    })
    question = El(children={("css*", "p"): [El("x"), El("Question: pet?")]})
    driver = FakeDriver({
        ("css*", "main > div"): [El(), question],
        ("css", '[data-rbd-droppable-id="watchlist-table-table-header"]'):
            El(children={("xpath*", "//tr[1]/td"): header}),
        ("id", "watchlist-table-body"): body,
        ("id", "secretquestion0"): El(log=log),
        ("id", "username0"): El(log=log),
        ("id", "password"): El(log=log),
    })
    seen = {}

    def chrome(path, chrome_options=None):
        seen["path"], seen["opts"] = path, chrome_options.arguments
        return driver
    monkeypatch.setattr(sys.modules["selenium.webdriver"], "Chrome", chrome)

    iv, ivp = helpers.impliedVolatility()
    assert (iv, ivp) == (["35.2", "61"], ["12", "88.5"])
    assert driver.visited == ["https://trade.thinkorswim.com/"]
    assert seen == {"path": "/fake/chromedriver",
                    "opts": ["--headless", "--window-size=2560x1600"]}
    assert ("keys", "u") in log and ("keys", "p") in log and ("keys", "rex") in log
