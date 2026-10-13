"""main.py (watchlist scan + straddle screen) and actions/login.py (token
file vs. browser login flow) against fake broker and browser objects."""
import math
import sys

import pytest
from fakes import FakeDriver, FakeTD

import main
from actions import login


# --- login -------------------------------------------------------------------

def test_login_uses_token_file(monkeypatch):
    seen = []
    auth = sys.modules["tda.auth"]
    monkeypatch.setattr(auth, "client_from_token_file",
                        lambda path, key: seen.append((path, key)) or "client")
    assert login.Login() == "client"
    assert seen == [("/nonexistent/td-token.json", "TESTCLIENT@AMER.OAUTHAP")]


def test_login_falls_back_to_browser_flow(monkeypatch):
    auth = sys.modules["tda.auth"]

    def no_token(path, key):
        raise FileNotFoundError(path)
    flows = []
    driver = FakeDriver({})
    monkeypatch.setattr(auth, "client_from_token_file", no_token)
    monkeypatch.setattr(auth, "client_from_login_flow",
                        lambda d, key, uri, path: flows.append((d, key, uri, path)) or "fresh")
    monkeypatch.setattr(sys.modules["selenium.webdriver"], "Chrome",
                        lambda path: driver)
    assert login.Login() == "fresh"
    assert flows == [(driver, "TESTCLIENT@AMER.OAUTHAP", "https://127.0.0.1/callback",
                      "/nonexistent/td-token.json")]


# --- main --------------------------------------------------------------------

def test_get_range_is_one_sigma_over_eight_days():
    asset = {"price": 100.0, "iv": 40.0}
    assert main.getRange(asset) == pytest.approx(100 * 0.40 * math.sqrt(8 / 365))


def test_set_assets_collects_quotes_fundamentals_and_vol(monkeypatch):
    t = FakeTD(watchlist=["AAPL", "MSFT"],
               quotes={"AAPL": 450.0, "MSFT": 210.0},
               fundamentals={"AAPL": {"beta": 1.2, "vol10DayAvg": 1e7, "vol3MonthAvg": 2e7},
                             "MSFT": {"beta": 0.9, "vol10DayAvg": 3e6, "vol3MonthAvg": 4e6}})
    monkeypatch.setattr(main, "impliedVolatility", lambda: (["35.5", "28"], ["40", "75.5"]))
    monkeypatch.setattr(main, "historicalVolatility", lambda t, s, n: {"AAPL": 0.6, "MSFT": 0.3}[s])
    assets = main.setAssets(t)
    assert assets == {
        "AAPL": {"price": 450.0, "beta": 1.2, "vol10DayAvg": 1e7, "vol3MonthAvg": 2e7,
                 "hv": 0.6, "iv": 35.5, "ivp": 40.0},
        "MSFT": {"price": 210.0, "beta": 0.9, "vol10DayAvg": 3e6, "vol3MonthAvg": 4e6,
                 "hv": 0.3, "iv": 28.0, "ivp": 75.5},
    }
    assert ("watchlist", "000000000", "111") in t.calls


def _greeks(delta, theta, vol):
    return [{"delta": delta, "theta": theta, "volatility": vol}]


def test_straddle_logic_screens_qualifying_asset(monkeypatch):
    key = "2020-08-21:3"
    calls = {"100.0": _greeks(0.5, -0.05, 15), "130.0": _greeks(0.5, -0.05, 15)}
    puts = {"100.0": _greeks(-0.2, -0.05, 15), "130.0": _greeks(-0.2, -0.05, 15)}
    t = FakeTD(chains={"AAPL": {"callExpDateMap": {key: calls},
                                "putExpDateMap": {key: puts}}})
    assets = {"AAPL": {"price": 100.0, "iv": 40.0, "hv": 0.6, "ivp": 30.0}}
    got = main.straddleLogic(t, assets)
    assert got == [(calls["100.0"][0], puts["100.0"][0])]    # 130 is out of range


@pytest.mark.xfail(strict=True, raises=UnboundLocalError,
                   reason="BUG: straddleLogic returns `viables` before assignment "
                          "when no asset passes the hv/ivp screen")
def test_straddle_logic_with_no_qualifying_assets():
    assert main.straddleLogic(FakeTD(), {"X": {"hv": 0.1, "ivp": 90.0}}) == []


def test_main_wires_login_scan_and_screen(monkeypatch, capsys):
    t = FakeTD()
    monkeypatch.setattr(main, "Login", lambda: t)
    monkeypatch.setattr(main, "setAssets", lambda client: {"seen": client is t})
    monkeypatch.setattr(main, "straddleLogic", lambda client, assets: [("call", "put")])
    main.main()
    assert capsys.readouterr().out.strip() == "[('call', 'put')]"
