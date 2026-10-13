"""In-memory stand-ins for the tda-api client and a Selenium driver."""
import types


class Resp:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def chain(date_str, calls=None, puts=None):
    """An option-chain payload: {"callExpDateMap": {date: {strike: [opt]}}, ...}"""
    return {"callExpDateMap": {date_str: calls or {}},
            "putExpDateMap": {date_str: puts or {}}}


def opt(bid=0.0, ask=0.0, **extra):
    return [dict(bid=bid, ask=ask, **extra)]


class FakeTD:
    """Mimics the parts of tda.client.Client the bot uses."""

    Account = types.SimpleNamespace(Fields=types.SimpleNamespace(POSITIONS="positions"))
    Instrument = types.SimpleNamespace(
        Projection=types.SimpleNamespace(FUNDAMENTAL="fundamental"))
    PriceHistory = types.SimpleNamespace(
        PeriodType=types.SimpleNamespace(MONTH="month"),
        FrequencyType=types.SimpleNamespace(DAILY="daily"),
        Frequency=types.SimpleNamespace(DAILY=1))

    def __init__(self, chains=None, quotes=None, fundamentals=None, positions=None,
                 candles=None, watchlist=None):
        self.chains = chains or {}
        self.quotes = quotes or {}
        self.fundamentals = fundamentals or {}
        self.positions = positions or []
        self.candles = candles or {}
        self.watchlist = watchlist or []
        self.calls = []

    def get_option_chain(self, symbol):
        self.calls.append(("chain", symbol))
        return Resp(self.chains[symbol])

    def get_quote(self, symbol):
        self.calls.append(("quote", symbol))
        return Resp({symbol: {"lastPrice": self.quotes[symbol]}})

    def search_instruments(self, symbol, projection):
        self.calls.append(("search", symbol, projection))
        return Resp({symbol: {"fundamental": self.fundamentals[symbol]}})

    def accounts(self, account_id, fields):
        self.calls.append(("accounts", account_id, fields))
        return Resp({"securitiesAccount": {"positions": self.positions}})

    def get_price_history(self, symbol, **kwargs):
        self.calls.append(("history", symbol, kwargs))
        return Resp({"candles": [{"close": c} for c in self.candles[symbol]]})

    def get_watchlist(self, account_id, watchlist_id):
        self.calls.append(("watchlist", account_id, watchlist_id))
        return Resp({"watchlistItems": [{"instrument": {"symbol": s}}
                                        for s in self.watchlist]})


# --- Selenium ---------------------------------------------------------------

class El:
    """A permissive fake WebElement: records clicks/keys; lookups are served
    from the `children` dict keyed by (method, selector)."""

    def __init__(self, text="", children=None, log=None):
        self.text = text
        self.children = children or {}
        self.log = log if log is not None else []

    def click(self):
        self.log.append(("click", self.text))

    def send_keys(self, keys):
        self.log.append(("keys", keys))

    def _lookup(self, method, selector, many):
        hit = self.children.get((method, selector))
        if hit is None:
            hit = [] if many else El(log=self.log)
        return hit

    def find_element_by_id(self, s):
        return self._lookup("id", s, False)

    def find_element_by_css_selector(self, s):
        return self._lookup("css", s, False)

    def find_elements_by_css_selector(self, s):
        return self._lookup("css*", s, True)

    def find_elements_by_xpath(self, s):
        return self._lookup("xpath*", s, True)

    def find_elements_by_tag_name(self, s):
        return self._lookup("tag*", s, True)


class FakeDriver(El):
    def __init__(self, children):
        super().__init__(children=children)
        self.visited = []

    def get(self, url):
        self.visited.append(url)

    def implicitly_wait(self, ms):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False
