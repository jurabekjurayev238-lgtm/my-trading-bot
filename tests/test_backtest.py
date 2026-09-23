from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from backtest import BacktestConfig, calc_lot, compute_stats, optimize, run_backtest, simulate
from indicators import add_signals

# Narx 1000 da SL 10% = 100, TP 20% = 200; 1% risk ($100) → 1.0 lot
CFG = BacktestConfig(point=1.0, sl_percent=10, tp_percent=20,
                     initial_balance=10_000, risk_percent=1.0, contract_size=1.0)


def make_df(bars, signals=None):
    """bars: [(open, high, low, close), ...]"""
    df = pd.DataFrame(bars, columns=['open', 'high', 'low', 'close'])
    df['time'] = pd.date_range("2024-01-01", periods=len(df), freq="h")
    df['signal'] = signals if signals is not None else 0
    return df


def random_walk(n=800, seed=1):
    rng = np.random.default_rng(seed)
    close = 30_000 + np.cumsum(rng.normal(0, 150, n))
    open_ = np.concatenate([[close[0]], close[:-1]])
    high = np.maximum(open_, close) + rng.uniform(0, 100, n)
    low = np.minimum(open_, close) - rng.uniform(0, 100, n)
    return pd.DataFrame({
        'time': pd.date_range("2024-01-01", periods=n, freq="h"),
        'open': open_, 'high': high, 'low': low, 'close': close,
    })


# ── Signal mantiqi ──────────────────────────────────────────

def test_add_signals_buy_on_upward_cross():
    closes = [100 - i for i in range(30)] + [70 + 3 * i for i in range(15)]
    s = add_signals(pd.DataFrame({'close': closes}), 9, 21, 14, 50, 50)
    assert (s['signal'] == 1).sum() == 1
    assert (s['signal'] == -1).sum() == 0
    buy_idx = s.index[s['signal'] == 1][0]
    assert buy_idx >= 30
    assert s.loc[buy_idx, 'ema_fast'] > s.loc[buy_idx, 'ema_slow']
    assert s.loc[buy_idx - 1, 'ema_fast'] < s.loc[buy_idx - 1, 'ema_slow']


def test_add_signals_sell_on_downward_cross():
    closes = [100 + i for i in range(30)] + [130 - 3 * i for i in range(15)]
    s = add_signals(pd.DataFrame({'close': closes}), 9, 21, 14, 50, 50)
    assert (s['signal'] == -1).sum() == 1
    assert (s['signal'] == 1).sum() == 0


def test_add_signals_rsi_filter_blocks_signal():
    closes = [100 - i for i in range(30)] + [70 + 3 * i for i in range(15)]
    s = add_signals(pd.DataFrame({'close': closes}), 9, 21, 14, rsi_buy=99, rsi_sell=50)
    assert (s['signal'] != 0).sum() == 0


# ── Savdo mexanikasi ────────────────────────────────────────

def test_buy_take_profit():
    df = make_df([(1000, 1005, 995, 1000),
                  (1000, 1050, 990, 1040),
                  (1040, 1210, 1030, 1200)], signals=[1, 0, 0])
    res = simulate(df, CFG)
    t = res.trades.iloc[0]
    assert len(res.trades) == 1
    assert (t['type'], t['reason'], t['entry'], t['exit'], t['lot']) == ("BUY", "TP", 1000, 1200, 1.0)
    assert t['pnl'] == pytest.approx(200)          # 2% balans (1:2 RR)
    assert res.equity.iloc[-1] == pytest.approx(10_200)


def test_buy_stop_loss():
    df = make_df([(1000, 1005, 995, 1000),
                  (1000, 1010, 890, 900)], signals=[1, 0])
    t = simulate(df, CFG).trades.iloc[0]
    assert (t['reason'], t['exit']) == ("SL", 900)
    assert t['pnl'] == pytest.approx(-100)         # 1% balans


def test_sl_wins_when_both_hit_in_same_bar():
    df = make_df([(1000, 1005, 995, 1000),
                  (1000, 1250, 850, 1100)], signals=[1, 0])
    t = simulate(df, CFG).trades.iloc[0]
    assert t['reason'] == "SL"
    assert t['pnl'] == pytest.approx(-100)


def test_gap_through_stop_fills_at_open():
    df = make_df([(1000, 1005, 995, 1000),
                  (1000, 1010, 990, 1000),
                  (850, 860, 840, 850)], signals=[1, 0, 0])
    t = simulate(df, CFG).trades.iloc[0]
    assert (t['reason'], t['exit']) == ("SL", 850)
    assert t['pnl'] == pytest.approx(-150)


def test_sell_take_profit():
    df = make_df([(1000, 1005, 995, 1000),
                  (1000, 1010, 950, 960),
                  (960, 970, 790, 800)], signals=[-1, 0, 0])
    t = simulate(df, CFG).trades.iloc[0]
    assert (t['type'], t['reason'], t['exit']) == ("SELL", "TP", 800)
    assert t['pnl'] == pytest.approx(200)


def test_spread_applied_to_entry_and_sell_exit():
    cfg = replace(CFG, spread_points=10)
    buy = simulate(make_df([(1000, 1005, 995, 1000),
                            (1000, 1300, 1000, 1250)], signals=[1, 0]), cfg).trades.iloc[0]
    # SL/TP masofasi Ask kirish narxidan: 1010 * 20% = 202
    assert (buy['entry'], buy['tp'], buy['exit']) == (1010, 1212, 1212)

    # SELL Ask (Bid + spread) bo'yicha yopiladi: TP 800 ga Bid 790 da yetadi
    sell = simulate(make_df([(1000, 1005, 995, 1000),
                             (1000, 1000, 795, 800),
                             (800, 800, 789, 790)], signals=[-1, 0, 0]), cfg).trades.iloc[0]
    assert sell['entry'] == 1000
    assert sell['exit_time'] == pd.Timestamp("2024-01-01 02:00")
    assert sell['pnl'] == pytest.approx(200)


def test_open_position_closed_at_end():
    df = make_df([(1000, 1005, 995, 1000),
                  (1000, 1050, 990, 1040),
                  (1040, 1060, 1020, 1050)], signals=[1, 0, 0])
    t = simulate(df, CFG).trades.iloc[0]
    assert (t['reason'], t['exit']) == ("END", 1050)
    assert t['pnl'] == pytest.approx(50)


def test_only_one_position_at_a_time():
    df = make_df([(1000, 1005, 995, 1000),
                  (1000, 1010, 990, 1000),
                  (1000, 1010, 990, 1000),
                  (1000, 1210, 990, 1200)], signals=[1, 1, -1, 0])
    res = simulate(df, CFG)
    assert len(res.trades) == 1
    assert res.trades.iloc[0]['type'] == "BUY"


def test_commission_deducted():
    cfg = replace(CFG, commission_per_lot=7)
    df = make_df([(1000, 1005, 995, 1000),
                  (1000, 1210, 990, 1200)], signals=[1, 0])
    assert simulate(df, cfg).trades.iloc[0]['pnl'] == pytest.approx(193)


def test_calc_lot_rounds_down_and_respects_limits():
    cfg = BacktestConfig(risk_percent=1.0, lot_step=0.01)
    assert calc_lot(10_000, 300, cfg) == pytest.approx(0.33)
    assert calc_lot(10, 300, cfg) == pytest.approx(cfg.min_lot)
    assert calc_lot(1e9, 300, cfg) == pytest.approx(cfg.max_lot)


def test_sl_tp_scale_with_btc_price():
    # Default 1% / 2%: BTC $50,000 da SL $500, TP $1,000 (avval point bilan atigi $2 / $4 edi)
    df = make_df([(50_000, 50_010, 49_990, 50_000),
                  (50_000, 51_100, 49_900, 51_000)], signals=[1, 0])
    t = simulate(df, BacktestConfig()).trades.iloc[0]
    assert (t['sl'], t['tp'], t['reason']) == (49_500, 51_000, "TP")
    assert t['lot'] == pytest.approx(0.2)              # $100 risk / $500 SL
    assert t['pnl'] == pytest.approx(200)              # 2% balans


# ── To'liq backtest va optimizatsiya ────────────────────────

def test_run_backtest_consistency():
    df = random_walk()
    cfg = BacktestConfig(point=1.0, sl_percent=1.0, tp_percent=2.0)
    res = run_backtest(df, cfg)
    stats = compute_stats(res)
    assert len(res.equity) == len(df)
    assert stats['trades'] == len(res.trades) > 0
    assert stats['final_balance'] == pytest.approx(cfg.initial_balance + res.trades['pnl'].sum())
    assert stats['final_balance'] == pytest.approx(res.trades['balance'].iloc[-1])
    assert 0 <= stats['max_dd_pct'] <= 100


def test_optimize_grid_and_oos():
    df = random_walk()
    base = BacktestConfig(point=1.0, sl_percent=1.0, tp_percent=2.0)
    table = optimize(df, base, ema_fast_list=[5, 9, 25], ema_slow_list=[21, 30],
                     rsi_levels=[50], oos=0.3, min_trades=0, top_n=2)
    # (25, 21) tashlab ketiladi → 5 ta kombinatsiya
    assert len(table) == 5
    assert (table['ema_fast'] < table['ema_slow']).all()
    assert table['profit_factor'].is_monotonic_decreasing
    assert table['oos_trades'].notna().sum() == 2
    assert table['oos_trades'].iloc[2:].isna().all()
