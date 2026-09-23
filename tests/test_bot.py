import importlib
import sys
from types import ModuleType, SimpleNamespace

import pandas as pd
import pytest


@pytest.fixture
def bot(monkeypatch):
    """bitcoin_strategy ni soxta MetaTrader5 moduli bilan import qilish"""
    fake = ModuleType("MetaTrader5")
    fake.TIMEFRAME_H1 = 16385
    fake.ORDER_TYPE_BUY, fake.ORDER_TYPE_SELL = 0, 1
    fake.TRADE_ACTION_DEAL = 1
    fake.ORDER_TIME_GTC = 0
    fake.ORDER_FILLING_IOC = 1
    fake.TRADE_RETCODE_DONE = 10009
    fake.balance = 10_000.0
    # BTCUSD: 1 lot = 1 BTC, tick 0.01 = $0.01
    fake.account_info = lambda: SimpleNamespace(balance=fake.balance)
    fake.symbol_info = lambda s: SimpleNamespace(
        point=0.01, digits=2, trade_tick_size=0.01, trade_tick_value=0.01,
        volume_min=0.01, volume_step=0.01, volume_max=100.0)
    fake.symbol_info_tick = lambda s: SimpleNamespace(bid=100_000.0, ask=100_015.0)
    fake.sent = []

    def order_send(request):
        fake.sent.append(request)
        return SimpleNamespace(retcode=fake.TRADE_RETCODE_DONE, comment="done")
    fake.order_send = order_send

    monkeypatch.setitem(sys.modules, "MetaTrader5", fake)
    sys.modules.pop("bitcoin_strategy", None)
    module = importlib.import_module("bitcoin_strategy")
    yield module, fake
    sys.modules.pop("bitcoin_strategy", None)


def test_sl_distance_is_percent_of_price(bot):
    b, _ = bot
    sl_dist, tp_dist = b.sl_tp_distance(100_000, b.SL_PERCENT, b.TP_PERCENT)
    assert (sl_dist, tp_dist) == (1_000, 2_000)        # avval: 200 point = $2


def test_calc_lot_risks_exactly_one_percent(bot):
    b, _ = bot
    lot = b.calc_lot("BTCUSD", 1.0, sl_distance=1_000)
    assert lot == pytest.approx(0.1)                    # $100 risk / $1,000 SL
    assert lot * 1_000 == pytest.approx(10_000 * 0.01)


def test_calc_lot_warns_when_min_lot_exceeds_risk(bot, capsys):
    b, fake = bot
    fake.balance = 100.0                                # 1% = $1, lekin min lot 0.01 × $1,000 = $10
    assert b.calc_lot("BTCUSD", 1.0, sl_distance=1_000) == pytest.approx(0.01)
    assert "Minimal lot" in capsys.readouterr().out


def test_place_order_sets_sl_tp_from_distance(bot):
    b, fake = bot
    b.place_order("BTCUSD", "BUY", 0.1, 1_000, 2_000)
    b.place_order("BTCUSD", "SELL", 0.1, 1_000, 2_000)
    buy, sell = fake.sent
    assert (buy['price'], buy['sl'], buy['tp']) == (100_015, 99_015, 102_015)
    assert (sell['price'], sell['sl'], sell['tp']) == (100_000, 101_000, 98_000)
    assert buy['volume'] == 0.1


def test_get_signal_matches_shared_logic(bot):
    b, _ = bot
    up = pd.DataFrame({'close': [100 - i for i in range(30)] + [70 + 3 * i for i in range(8)]})
    down = pd.DataFrame({'close': [100 + i for i in range(30)] + [130 - 3 * i for i in range(8)]})
    flat = pd.DataFrame({'close': [100.0] * 40})
    assert (b.get_signal(up), b.get_signal(down), b.get_signal(flat)) == ("BUY", "SELL", "HOLD")
