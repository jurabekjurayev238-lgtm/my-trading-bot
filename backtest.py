# ============================================================
# Bitcoin Strategy Backtest + Optimizatsiya (MetaTrader 5)
# Strategiya: EMA Crossover + RSI Filter (bitcoin_strategy.py bilan bir xil)
# Ma'lumot:   MT5 terminalidan tarixiy shamlar (copy_rates_range)
# ============================================================
#
# Ishlatish:
#   python backtest.py --from 2024-01-01 --to 2025-01-01
#   python backtest.py --from 2023-01-01 --optimize
#
# MT5 login (ixtiyoriy, bo'lmasa terminaldagi ochiq hisob ishlatiladi):
#   MT5_LOGIN, MT5_PASSWORD, MT5_SERVER muhit o'zgaruvchilari

import argparse
import itertools
import math
import os
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd

from indicators import add_signals

# ── SOZLAMALAR ──────────────────────────────────────────────
DEFAULT_SYMBOL    = "BTCUSD"
DEFAULT_TIMEFRAME = "H1"
TIMEFRAMES        = ["M5", "M15", "M30", "H1", "H4", "D1"]

# Optimizatsiya uchun standart qiymatlar
OPT_EMA_FAST   = [5, 7, 9, 12, 15]
OPT_EMA_SLOW   = [18, 21, 26, 34, 50]
OPT_RSI_LEVELS = [45, 50, 55, 60]     # BUY > L, SELL < 100 - L
OPT_MIN_TRADES = 10                   # Kam savdoli natijalar tashlanadi
OPT_TOP_N      = 5                    # Out-of-sample'da tekshiriladigan eng yaxshilar
# ────────────────────────────────────────────────────────────


@dataclass
class BacktestConfig:
    """Backtest sozlamalari. Default'lar bitcoin_strategy.py bilan bir xil."""
    # Strategiya
    ema_fast:   int   = 9
    ema_slow:   int   = 21
    rsi_period: int   = 14
    rsi_buy:    float = 50
    rsi_sell:   float = 50
    sl_points:  float = 200
    tp_points:  float = 400
    # Hisob va risk
    initial_balance: float = 10_000.0
    risk_percent:    float = 1.0
    # Simvol xususiyatlari (MT5'dan olinadi)
    point:         float = 0.01
    contract_size: float = 1.0
    min_lot:       float = 0.01
    lot_step:      float = 0.01
    max_lot:       float = 100.0
    # Xarajatlar
    spread_points:      float = 0.0
    commission_per_lot: float = 0.0   # 1 lot uchun (ochish + yopish)


@dataclass
class BacktestResult:
    trades: pd.DataFrame
    equity: pd.Series
    config: BacktestConfig
    buy_hold_pct: float


# ── MA'LUMOT ────────────────────────────────────────────────

def load_mt5_data(symbol: str, timeframe: str, date_from: datetime,
                  date_to: datetime, cfg: BacktestConfig,
                  spread_points: Optional[float] = None):
    """
    MT5'dan tarixiy shamlarni olish.
    Simvol xususiyatlari (point, contract size, lot chegaralari, spread) config'ga yoziladi.
    """
    import MetaTrader5 as mt5

    login    = os.getenv("MT5_LOGIN")
    password = os.getenv("MT5_PASSWORD")
    server   = os.getenv("MT5_SERVER")
    if login and password and server:
        from bitcoin_strategy import connect_mt5
        if not connect_mt5(int(login), password, server):
            raise RuntimeError("MT5 ga ulanib bo'lmadi")
    elif not mt5.initialize():
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")

    try:
        if not mt5.symbol_select(symbol, True):
            raise RuntimeError(f"Simvol topilmadi: {symbol}")
        info = mt5.symbol_info(symbol)
        if info is None:
            raise RuntimeError(f"Simvol ma'lumoti yo'q: {symbol}")

        tf    = getattr(mt5, f"TIMEFRAME_{timeframe}")
        rates = mt5.copy_rates_range(symbol, tf, date_from, date_to)
        if rates is None or len(rates) == 0:
            raise RuntimeError(f"Ma'lumot olishda xato: {mt5.last_error()}")
    finally:
        mt5.shutdown()

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')

    if spread_points is None:
        # Har bir sham uchun MT5 spread'ining medianasi
        spread_points = float(df['spread'].median()) if 'spread' in df else float(info.spread)

    cfg = replace(cfg,
                  point=info.point,
                  contract_size=info.trade_contract_size,
                  min_lot=info.volume_min,
                  lot_step=info.volume_step,
                  max_lot=info.volume_max,
                  spread_points=spread_points)
    return df, cfg


# ── SIMULYATSIYA ────────────────────────────────────────────

def calc_lot(balance: float, cfg: BacktestConfig) -> float:
    """Risk asosida lot: balansning risk_percent qismi SL masofasiga teng"""
    sl_value_per_lot = cfg.sl_points * cfg.point * cfg.contract_size
    if sl_value_per_lot <= 0:
        return cfg.min_lot
    lot = balance * (cfg.risk_percent / 100) / sl_value_per_lot
    lot = math.floor(lot / cfg.lot_step + 1e-9) * cfg.lot_step
    lot = min(max(lot, cfg.min_lot), cfg.max_lot)
    return round(lot, 8)


def simulate(df: pd.DataFrame, cfg: BacktestConfig) -> BacktestResult:
    """
    Savdolarni sham-ma-sham simulyatsiya qilish. df da 'signal' ustuni bo'lishi kerak.
    - Signal yopilgan shamda (i-1) → kirish keyingi sham ochilishida (i)
    - Bir vaqtda faqat 1 pozitsiya (bot kabi)
    - Shamlar Bid narxida: BUY Ask'da ochilib Bid'da yopiladi, SELL — teskari
    - Bitta shamda SL ham TP ham tegsa → SL (konservativ)
    - Gap bo'lsa → sham ochilish narxida chiqish
    """
    times   = df['time'].to_numpy() if 'time' in df else df.index.to_numpy()
    opens   = df['open'].to_numpy(dtype=float)
    highs   = df['high'].to_numpy(dtype=float)
    lows    = df['low'].to_numpy(dtype=float)
    closes  = df['close'].to_numpy(dtype=float)
    signals = df['signal'].to_numpy()
    n = len(df)

    sl_dist = cfg.sl_points * cfg.point
    tp_dist = cfg.tp_points * cfg.point
    spread  = cfg.spread_points * cfg.point

    balance = cfg.initial_balance
    equity  = np.empty(n)
    trades  = []
    pos     = None

    def close_position(exit_price: float, exit_time, reason: str):
        nonlocal balance, pos
        pnl = (pos['dir'] * (exit_price - pos['entry']) * pos['lot'] * cfg.contract_size
               - cfg.commission_per_lot * pos['lot'])
        balance += pnl
        trades.append({
            'entry_time': pos['time'],
            'exit_time':  exit_time,
            'type':       "BUY" if pos['dir'] == 1 else "SELL",
            'lot':        pos['lot'],
            'entry':      pos['entry'],
            'sl':         pos['sl'],
            'tp':         pos['tp'],
            'exit':       exit_price,
            'reason':     reason,
            'pnl':        pnl,
            'balance':    balance,
        })
        pos = None

    for i in range(n):
        # 1) Oldingi yopilgan shamda signal → shu sham ochilishida kirish
        if pos is None and i > 0 and signals[i - 1] != 0 and balance > 0:
            d     = int(signals[i - 1])
            entry = opens[i] + spread if d == 1 else opens[i]
            pos = {
                'dir':   d,
                'entry': entry,
                'sl':    entry - d * sl_dist,
                'tp':    entry + d * tp_dist,
                'lot':   calc_lot(balance, cfg),
                'time':  times[i],
            }

        # 2) SL / TP tekshiruvi (BUY Bid bo'yicha, SELL Ask bo'yicha yopiladi)
        if pos is not None:
            adj = 0.0 if pos['dir'] == 1 else spread
            o, h, l = opens[i] + adj, highs[i] + adj, lows[i] + adj
            sl, tp  = pos['sl'], pos['tp']
            if pos['dir'] == 1:
                if o <= sl:
                    close_position(o, times[i], "SL")
                elif o >= tp:
                    close_position(o, times[i], "TP")
                elif l <= sl:
                    close_position(sl, times[i], "SL")
                elif h >= tp:
                    close_position(tp, times[i], "TP")
            else:
                if o >= sl:
                    close_position(o, times[i], "SL")
                elif o <= tp:
                    close_position(o, times[i], "TP")
                elif h >= sl:
                    close_position(sl, times[i], "SL")
                elif l <= tp:
                    close_position(tp, times[i], "TP")

        # 3) Equity (balans + ochiq pozitsiya natijasi)
        if pos is not None:
            mark = closes[i] if pos['dir'] == 1 else closes[i] + spread
            equity[i] = balance + pos['dir'] * (mark - pos['entry']) * pos['lot'] * cfg.contract_size
        else:
            equity[i] = balance

    # Ma'lumot tugadi — ochiq pozitsiyani oxirgi narxda yopish
    if pos is not None:
        last = closes[-1] if pos['dir'] == 1 else closes[-1] + spread
        close_position(last, times[-1], "END")
        equity[-1] = balance

    columns = ['entry_time', 'exit_time', 'type', 'lot', 'entry', 'sl', 'tp',
               'exit', 'reason', 'pnl', 'balance']
    trades_df = pd.DataFrame(trades, columns=columns)
    equity_s  = pd.Series(equity, index=pd.Index(times, name='time'), name='equity')
    buy_hold  = (closes[-1] / opens[0] - 1) * 100 if n else 0.0
    return BacktestResult(trades_df, equity_s, cfg, buy_hold)


def run_backtest(df: pd.DataFrame, cfg: BacktestConfig) -> BacktestResult:
    """Signallarni hisoblab, backtest o'tkazish"""
    df = add_signals(df, cfg.ema_fast, cfg.ema_slow, cfg.rsi_period, cfg.rsi_buy, cfg.rsi_sell)
    return simulate(df, cfg)


# ── STATISTIKA ──────────────────────────────────────────────

def compute_stats(result: BacktestResult) -> dict:
    """Asosiy ko'rsatkichlar"""
    pnl     = result.trades['pnl']
    initial = result.config.initial_balance
    final   = result.equity.iloc[-1] if len(result.equity) else initial

    wins   = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    gross_profit = wins.sum()
    gross_loss   = -losses.sum()
    if gross_loss > 0:
        profit_factor = gross_profit / gross_loss
    else:
        profit_factor = math.inf if gross_profit > 0 else 0.0

    peak = result.equity.cummax()
    dd   = result.equity - peak
    max_dd     = float(-dd.min()) if len(dd) else 0.0
    max_dd_pct = float(-(dd / peak).min() * 100) if len(dd) else 0.0

    n = len(pnl)
    return {
        'trades':        n,
        'wins':          len(wins),
        'losses':        len(losses),
        'win_rate':      len(wins) / n * 100 if n else 0.0,
        'net_profit':    final - initial,
        'return_pct':    (final / initial - 1) * 100,
        'profit_factor': profit_factor,
        'avg_win':       wins.mean() if len(wins) else 0.0,
        'avg_loss':      losses.mean() if len(losses) else 0.0,
        'expectancy':    pnl.mean() if n else 0.0,
        'max_dd':        max_dd,
        'max_dd_pct':    max_dd_pct,
        'initial':       initial,
        'final_balance': final,
        'buy_hold_pct':  result.buy_hold_pct,
    }


def print_stats(stats: dict, title: str = "Backtest natijasi"):
    """Statistikani chiroyli chiqarish"""
    rows = [
        ("Savdolar soni",          f"{stats['trades']}"),
        ("Yutuq / Yutqaziq",       f"{stats['wins']} / {stats['losses']}"),
        ("Win rate",               f"{stats['win_rate']:.1f}%"),
        ("Sof foyda",              f"${stats['net_profit']:,.2f}"),
        ("Daromad",                f"{stats['return_pct']:.2f}%"),
        ("Profit factor",          f"{stats['profit_factor']:.2f}"),
        ("O'rtacha yutuq",         f"${stats['avg_win']:,.2f}"),
        ("O'rtacha yutqaziq",      f"${stats['avg_loss']:,.2f}"),
        ("Expectancy (1 savdo)",   f"${stats['expectancy']:,.2f}"),
        ("Max drawdown",           f"${stats['max_dd']:,.2f} ({stats['max_dd_pct']:.2f}%)"),
        ("Boshlang'ich balans",    f"${stats['initial']:,.2f}"),
        ("Yakuniy balans",         f"${stats['final_balance']:,.2f}"),
        ("Buy & Hold",             f"{stats['buy_hold_pct']:.2f}%"),
    ]
    print(f"\n📊 {title}")
    print("─" * 50)
    for label, value in rows:
        print(f"  {label:<24}{value:>24}")
    print("─" * 50)


def plot_equity(result: BacktestResult, path: str) -> bool:
    """Equity va drawdown grafigini PNG ga saqlash"""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("⚠️  matplotlib o'rnatilmagan — grafik saqlanmadi")
        return False

    eq     = result.equity
    dd_pct = (eq - eq.cummax()) / eq.cummax() * 100
    cfg    = result.config

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True,
                                   gridspec_kw={'height_ratios': [3, 1]})
    ax1.plot(eq.index, eq.values, color="#2a7ae2", lw=1.2)
    ax1.axhline(cfg.initial_balance, color="gray", lw=0.8, ls="--")
    ax1.set_title(f"Equity | EMA({cfg.ema_fast}/{cfg.ema_slow}) + RSI({cfg.rsi_period}) "
                  f"| SL {cfg.sl_points:g} / TP {cfg.tp_points:g} point")
    ax1.set_ylabel("Equity ($)")
    ax1.grid(alpha=0.3)
    ax2.fill_between(dd_pct.index, dd_pct.values, 0, color="#d9534f", alpha=0.4)
    ax2.set_ylabel("Drawdown (%)")
    ax2.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return True


# ── OPTIMIZATSIYA ───────────────────────────────────────────

def optimize(df: pd.DataFrame, base_cfg: BacktestConfig,
             ema_fast_list=OPT_EMA_FAST, ema_slow_list=OPT_EMA_SLOW,
             rsi_levels=OPT_RSI_LEVELS, sl_list=None, tp_list=None,
             oos: float = 0.3, min_trades: int = OPT_MIN_TRADES,
             top_n: int = OPT_TOP_N) -> pd.DataFrame:
    """
    Grid search. Ma'lumot in-sample (1 - oos) va out-of-sample (oos) qismlarga bo'linadi:
    parametrlar faqat in-sample'da tanlanadi, eng yaxshi top_n tasi out-of-sample'da
    qayta tekshiriladi (oos_* ustunlari) — overfitting'ni aniqlash uchun.
    """
    sl_list = sl_list or [base_cfg.sl_points]
    tp_list = tp_list or [base_cfg.tp_points]
    split   = int(len(df) * (1 - oos))

    signal_cache = {}
    rows = []
    for fast, slow, level in itertools.product(ema_fast_list, ema_slow_list, rsi_levels):
        if fast >= slow:
            continue
        sig_df = add_signals(df, fast, slow, base_cfg.rsi_period, level, 100 - level)
        signal_cache[(fast, slow, level)] = sig_df
        for sl, tp in itertools.product(sl_list, tp_list):
            cfg = replace(base_cfg, ema_fast=fast, ema_slow=slow,
                          rsi_buy=level, rsi_sell=100 - level,
                          sl_points=sl, tp_points=tp)
            stats = compute_stats(simulate(sig_df.iloc[:split], cfg))
            rows.append({
                'ema_fast': fast, 'ema_slow': slow,
                'rsi_buy': level, 'rsi_sell': 100 - level,
                'sl_points': sl, 'tp_points': tp,
                **{k: stats[k] for k in ('trades', 'win_rate', 'profit_factor',
                                         'net_profit', 'return_pct', 'max_dd_pct')},
            })

    table = pd.DataFrame(rows)
    if table.empty:
        return table
    table = table[table['trades'] >= min_trades]
    table = table.sort_values(['profit_factor', 'net_profit'], ascending=False)
    table = table.reset_index(drop=True)

    # Out-of-sample tekshiruv
    if 0 < split < len(df):
        for col in ('oos_trades', 'oos_win_rate', 'oos_profit_factor',
                    'oos_net_profit', 'oos_max_dd_pct'):
            table[col] = np.nan
        for idx in table.index[:top_n]:
            r   = table.loc[idx]
            key = (int(r['ema_fast']), int(r['ema_slow']), r['rsi_buy'])
            cfg = replace(base_cfg, ema_fast=key[0], ema_slow=key[1],
                          rsi_buy=r['rsi_buy'], rsi_sell=r['rsi_sell'],
                          sl_points=r['sl_points'], tp_points=r['tp_points'])
            stats = compute_stats(simulate(signal_cache[key].iloc[split:], cfg))
            table.loc[idx, 'oos_trades']        = stats['trades']
            table.loc[idx, 'oos_win_rate']      = stats['win_rate']
            table.loc[idx, 'oos_profit_factor'] = stats['profit_factor']
            table.loc[idx, 'oos_net_profit']    = stats['net_profit']
            table.loc[idx, 'oos_max_dd_pct']    = stats['max_dd_pct']
    return table


# ── ISHGA TUSHIRISH ──────────────────────────────────────────

def _int_list(text: str) -> list:
    return [int(x) for x in text.split(",") if x.strip()]


def _float_list(text: str) -> list:
    return [float(x) for x in text.split(",") if x.strip()]


def _date(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def parse_args():
    d = BacktestConfig()
    p = argparse.ArgumentParser(description="Bitcoin EMA+RSI strategiyasi uchun MT5 backtest")
    p.add_argument("--symbol",    default=DEFAULT_SYMBOL)
    p.add_argument("--timeframe", default=DEFAULT_TIMEFRAME, choices=TIMEFRAMES)
    p.add_argument("--from", dest="date_from", type=_date, required=True, help="YYYY-MM-DD")
    p.add_argument("--to",   dest="date_to",   type=_date, default=None, help="YYYY-MM-DD (default: bugun)")
    p.add_argument("--balance",   type=float, default=d.initial_balance)
    p.add_argument("--risk",      type=float, default=d.risk_percent, help="Har savdoda risk, %%")
    p.add_argument("--ema-fast",  type=int,   default=d.ema_fast)
    p.add_argument("--ema-slow",  type=int,   default=d.ema_slow)
    p.add_argument("--rsi",       type=int,   default=d.rsi_period)
    p.add_argument("--rsi-buy",   type=float, default=d.rsi_buy)
    p.add_argument("--rsi-sell",  type=float, default=d.rsi_sell)
    p.add_argument("--sl-points", type=float, default=d.sl_points)
    p.add_argument("--tp-points", type=float, default=d.tp_points)
    p.add_argument("--spread-points", type=float, default=None,
                   help="Default: MT5 tarixidagi spread medianasi")
    p.add_argument("--commission", type=float, default=d.commission_per_lot,
                   help="1 lot uchun komissiya, $ (ochish + yopish)")
    p.add_argument("--out", default="results", help="Natijalar papkasi")
    # Optimizatsiya
    p.add_argument("--optimize", action="store_true", help="Parametrlarni optimallashtirish")
    p.add_argument("--opt-ema-fast", type=_int_list,   default=OPT_EMA_FAST)
    p.add_argument("--opt-ema-slow", type=_int_list,   default=OPT_EMA_SLOW)
    p.add_argument("--opt-rsi",      type=_float_list, default=OPT_RSI_LEVELS,
                   help="RSI darajalari: BUY > L, SELL < 100-L")
    p.add_argument("--opt-sl",       type=_float_list, default=None, help="Masalan: 200,1000,5000")
    p.add_argument("--opt-tp",       type=_float_list, default=None, help="Masalan: 400,2000,10000")
    p.add_argument("--oos",          type=float, default=0.3, help="Out-of-sample ulushi (0..1)")
    p.add_argument("--min-trades",   type=int,   default=OPT_MIN_TRADES)
    return p.parse_args()


def main():
    args = parse_args()
    date_to = args.date_to or datetime.now(timezone.utc)

    cfg = BacktestConfig(
        ema_fast=args.ema_fast, ema_slow=args.ema_slow, rsi_period=args.rsi,
        rsi_buy=args.rsi_buy, rsi_sell=args.rsi_sell,
        sl_points=args.sl_points, tp_points=args.tp_points,
        initial_balance=args.balance, risk_percent=args.risk,
        commission_per_lot=args.commission,
    )

    print(f"📥 MT5'dan ma'lumot olinmoqda: {args.symbol} {args.timeframe} | "
          f"{args.date_from:%Y-%m-%d} → {date_to:%Y-%m-%d}")
    df, cfg = load_mt5_data(args.symbol, args.timeframe, args.date_from, date_to,
                            cfg, args.spread_points)
    print(f"✅ {len(df)} ta sham | {df['time'].iloc[0]} → {df['time'].iloc[-1]}")
    print(f"ℹ️  point={cfg.point:g} | contract={cfg.contract_size:g} | spread={cfg.spread_points:g} point | "
          f"lot {cfg.min_lot:g}..{cfg.max_lot:g} (qadam {cfg.lot_step:g})")
    print(f"ℹ️  SL = {cfg.sl_points:g} point = {cfg.sl_points * cfg.point:,.2f} narx birligi | "
          f"TP = {cfg.tp_points:g} point = {cfg.tp_points * cfg.point:,.2f} narx birligi")

    if len(df) < cfg.ema_slow + cfg.rsi_period + 2:
        print("❌ Ma'lumot juda kam — sanalar oralig'ini kattalashtiring")
        return

    os.makedirs(args.out, exist_ok=True)

    result = run_backtest(df, cfg)
    print_stats(compute_stats(result),
                f"Backtest: EMA({cfg.ema_fast}/{cfg.ema_slow}) + RSI({cfg.rsi_period}) "
                f"{cfg.rsi_buy:g}/{cfg.rsi_sell:g}")

    trades_path = os.path.join(args.out, "trades.csv")
    result.trades.to_csv(trades_path, index=False)
    print(f"💾 Savdolar: {trades_path}")
    equity_path = os.path.join(args.out, "equity.png")
    if plot_equity(result, equity_path):
        print(f"💾 Grafik:   {equity_path}")

    if args.optimize:
        print(f"\n🔍 Optimizatsiya... (in-sample {1 - args.oos:.0%} / out-of-sample {args.oos:.0%})")
        table = optimize(df, cfg, args.opt_ema_fast, args.opt_ema_slow, args.opt_rsi,
                         args.opt_sl, args.opt_tp, oos=args.oos, min_trades=args.min_trades)
        if table.empty:
            print(f"⚠️  {args.min_trades} tadan ko'p savdo qilgan kombinatsiya topilmadi")
            return

        opt_path = os.path.join(args.out, "optimization.csv")
        table.to_csv(opt_path, index=False)

        cols = ['ema_fast', 'ema_slow', 'rsi_buy', 'sl_points', 'tp_points', 'trades',
                'win_rate', 'profit_factor', 'net_profit', 'max_dd_pct']
        cols += [c for c in ('oos_trades', 'oos_profit_factor', 'oos_net_profit') if c in table]
        print("\n🏆 Eng yaxshi 10 ta (in-sample, profit factor bo'yicha):")
        print(table[cols].head(10).to_string(index=False, float_format=lambda x: f"{x:,.2f}"))
        print(f"\n💾 To'liq jadval: {opt_path}")
        print("⚠️  oos_* ustunlari yomon bo'lsa — parametrlar tarixga moslashib qolgan (overfitting).")

    print("\n⚠️  ESLATMA: O'tgan natijalar kelajakni kafolatlamaydi. Bu moliyaviy maslahat emas.")


if __name__ == "__main__":
    main()
