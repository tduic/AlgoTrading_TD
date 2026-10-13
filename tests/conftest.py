"""Test bootstrap for a 2020 TD Ameritrade bot whose broker API no longer
exists.

* Fake (non-secret) values for the TDAMERITRADE_* env vars, because
  utils/constants.py reads them at import time.
* Stub modules for `tda`, `selenium` and `webdriver_manager` are installed in
  sys.modules BEFORE any project import, so no real broker client, browser or
  driver download can ever be reached from the tests. Tests patch the stub
  attributes they need.
"""
import os
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

for key, value in {
    "TDAMERITRADE_CLIENT_ID": "TESTCLIENT",
    "TDAMERITRADE_TOKEN_PATH": "/nonexistent/td-token.json",
    "TDAMERITRADE_REDIRECT_URI": "https://127.0.0.1/callback",
    "TDAMERITRADE_ACCOUNT_ID": "000000000",
    "TDAMERITRADE_ALGOLIST_ID": "111",
}.items():
    os.environ.setdefault(key, value)


def _stub(name, **attrs):
    mod = types.ModuleType(name)
    mod.__dict__.update(attrs)
    sys.modules[name] = mod
    parent, _, child = name.rpartition(".")
    if parent:
        setattr(sys.modules[parent], child, mod)
    return mod


def _unreachable(*a, **k):
    raise AssertionError("tests must not reach the real broker/browser")


class _Options:
    def __init__(self):
        self.arguments = []

    def add_argument(self, arg):
        self.arguments.append(arg)


class _ChromeDriverManager:
    def install(self):
        return "/fake/chromedriver"


_stub("tda")
_stub("tda.auth", client_from_token_file=_unreachable,
      client_from_login_flow=_unreachable)
_stub("tda.client", Client=object)
_stub("tda.orders")
_stub("tda.orders.options")
_stub("selenium")
_stub("selenium.webdriver", Chrome=_unreachable)
_stub("selenium.webdriver.chrome")
_stub("selenium.webdriver.chrome.options", Options=_Options)
_stub("webdriver_manager")
_stub("webdriver_manager.chrome", ChromeDriverManager=_ChromeDriverManager)
