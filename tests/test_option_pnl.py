"""utils/optionPnl.py: breakeven / max gain / max loss / current P&L for the
four strategies, against a fake option chain (no broker)."""
import datetime as real_dt

import pytest
from fakes import FakeTD, chain, opt

from utils import helpers, optionPnl

EXPIRY = "2020-08-21"
KEY = "2020-08-21:3"
C = 0.65 / 100        # commission per share


@pytest.fixture(autouse=True)
def frozen_today(monkeypatch):
    class FakeDate(real_dt.date):
        @classmethod
        def today(cls):
            return cls(2020, 8, 18)
    monkeypatch.setattr(helpers, "date", FakeDate)


def test_covered_call():
    t = FakeTD(chains={"AAPL": chain(KEY, calls={"105": opt(bid=2.0)})},
               quotes={"AAPL": 101.0})
    max_gain, max_loss, be = optionPnl.coveredCall(t, "AAPL", 100.0, EXPIRY, 105)
    assert be == pytest.approx(100 - 2.0 + C)
    assert max_gain == pytest.approx((105 - be) * 100)
    assert max_loss == pytest.approx(be * 100)


def test_covered_call_scales_with_contracts():
    t = FakeTD(chains={"AAPL": chain(KEY, calls={"105": opt(bid=2.0)})},
               quotes={"AAPL": 101.0})
    one = optionPnl.coveredCall(t, "AAPL", 100.0, EXPIRY, 105)
    three = optionPnl.coveredCall(t, "AAPL", 100.0, EXPIRY, 105, contracts=3)
    assert three[0] == pytest.approx(3 * one[0]) and three[2] == one[2]


def test_married_put():
    t = FakeTD(chains={"AAPL": chain(KEY, puts={"95": opt(ask=1.5)})},
               quotes={"AAPL": 103.0})
    pnl, max_loss, be = optionPnl.marriedPut(t, "AAPL", 100.0, EXPIRY, 95)
    assert be == pytest.approx(101.5 + C)
    assert pnl == pytest.approx((103.0 - be) * 100)
    assert max_loss == pytest.approx((be - 95) * 100)


def test_iron_condor():
    t = FakeTD(chains={"SPY": chain(
        KEY,
        puts={"90": opt(ask=0.5), "95": opt(bid=1.2)},
        calls={"105": opt(bid=1.3), "110": opt(ask=0.6)})})
    max_gain, max_loss, be = optionPnl.ironCondor(t, "SPY", EXPIRY, 90, 95, 105, 110)
    net = -0.5 + 1.2 + 1.3 - 0.6
    assert be == pytest.approx({"low": 95 - net + C, "high": 105 + net - C})
    assert max_gain == pytest.approx((net - C) * 100)
    assert max_loss["low"] == pytest.approx((be["low"] - 90) * 100)
    assert max_loss["high"] == pytest.approx((110 - be["high"]) * 100)
    # symmetric wings + symmetric premiums -> symmetric risk
    assert max_loss["low"] == pytest.approx(max_loss["high"])


def _strangle(last):
    t = FakeTD(chains={"TSLA": chain(KEY, puts={"95": opt(ask=1.0)},
                                     calls={"105": opt(ask=1.5)})},
               quotes={"TSLA": last})
    return optionPnl.strangleBuy(t, "TSLA", EXPIRY, 95, 105)


def test_long_strangle_breakevens_and_max_loss():
    pnl, max_loss, be = _strangle(100.0)
    assert be == pytest.approx({"low": 95 - 2.5 - C, "high": 105 + 2.5 + C})
    assert max_loss == pytest.approx((2.5 + C) * 100)
    # between the strikes the loss is capped at the premium paid
    assert pnl == pytest.approx(-max_loss)


@pytest.mark.parametrize("last", [80.0, 120.0])
def test_long_strangle_profits_on_big_moves_either_way(last):
    pnl, max_loss, be = _strangle(last)
    beyond = be["low"] - last if last < 100 else last - be["high"]
    assert pnl == pytest.approx(beyond * 100) and pnl > 0


def test_chain_lookup_uses_expiry_key():
    t = FakeTD(chains={"AAPL": chain("2020-09-18:31", calls={"105": opt(bid=2.0)})},
               quotes={"AAPL": 101.0})
    with pytest.raises(KeyError):
        optionPnl.coveredCall(t, "AAPL", 100.0, EXPIRY, 105)
