# ============================================================
# Indikatorlar va signal mantiqi
# Jonli bot (bitcoin_strategy.py) va backtest (backtest.py)
# bitta koddan foydalanishi uchun. MetaTrader5 kerak emas.
# ============================================================

import pandas as pd


def calc_ema(series: pd.Series, period: int) -> pd.Series:
    """EMA hisoblash"""
    return series.ewm(span=period, adjust=False).mean()


def calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """RSI hisoblash"""
    delta = series.diff()
    gain  = delta.clip(lower=0)
    loss  = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs  = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def add_signals(df: pd.DataFrame, ema_fast: int, ema_slow: int,
                rsi_period: int, rsi_buy: float, rsi_sell: float) -> pd.DataFrame:
    """
    Har bir sham uchun signal:
    BUY  (1)  → EMA_fast yuqoriga kesib o'tdi + RSI > rsi_buy
    SELL (-1) → EMA_fast pastga kesib o'tdi + RSI < rsi_sell
    HOLD (0)  → aks holda
    """
    df = df.copy()
    df['ema_fast'] = calc_ema(df['close'], ema_fast)
    df['ema_slow'] = calc_ema(df['close'], ema_slow)
    df['rsi']      = calc_rsi(df['close'], rsi_period)

    prev_fast = df['ema_fast'].shift(1)
    prev_slow = df['ema_slow'].shift(1)

    buy = ((prev_fast < prev_slow) &
           (df['ema_fast'] > df['ema_slow']) &
           (df['rsi'] > rsi_buy))
    sell = ((prev_fast > prev_slow) &
            (df['ema_fast'] < df['ema_slow']) &
            (df['rsi'] < rsi_sell))

    df['signal'] = 0
    df.loc[buy, 'signal']  = 1
    df.loc[sell, 'signal'] = -1
    return df
