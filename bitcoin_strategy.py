# ============================================================
# Bitcoin Trading Strategy for MetaTrader 5
# Strategy: EMA Crossover + RSI Filter + Risk Management
# Author: Jony | my-trading-bot
# ============================================================

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime

# ── SOZLAMALAR ──────────────────────────────────────────────
SYMBOL       = "BTCUSD"
TIMEFRAME    = mt5.TIMEFRAME_H1   # 1 soatlik chart
EMA_FAST     = 9                  # Tez EMA
EMA_SLOW     = 21                 # Sekin EMA
RSI_PERIOD   = 14                 # RSI davri
RSI_BUY      = 50                 # RSI buy chegarasi
RSI_SELL     = 50                 # RSI sell chegarasi
RISK_PERCENT = 1.0                # Har bir tradeda hisobning 1% risk
LOT_SIZE     = 0.01               # Minimal lot
MAGIC        = 123456             # Bot identifikatori
# ────────────────────────────────────────────────────────────


def connect_mt5(login: int, password: str, server: str) -> bool:
    """MT5 ga ulanish"""
    if not mt5.initialize():
        print(f"❌ MT5 initialize failed: {mt5.last_error()}")
        return False
    authorized = mt5.login(login, password=password, server=server)
    if not authorized:
        print(f"❌ Login failed: {mt5.last_error()}")
        mt5.shutdown()
        return False
    print(f"✅ MT5 ga ulandi | Hisob: {login}")
    return True


def get_candles(symbol: str, timeframe: int, count: int = 100) -> pd.DataFrame:
    """Shamlar ma'lumotini olish"""
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None:
        print(f"❌ Ma'lumot olishda xato: {mt5.last_error()}")
        return pd.DataFrame()
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df


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


def get_signal(df: pd.DataFrame) -> str:
    """
    Signal aniqlash:
    BUY  → EMA_fast yuqoriga kesib o'tdi + RSI > 50
    SELL → EMA_fast pastga kesib o'tdi + RSI < 50
    """
    df['ema_fast'] = calc_ema(df['close'], EMA_FAST)
    df['ema_slow'] = calc_ema(df['close'], EMA_SLOW)
    df['rsi']      = calc_rsi(df['close'], RSI_PERIOD)

    prev = df.iloc[-2]
    curr = df.iloc[-1]

    # BUY signali
    if (prev['ema_fast'] < prev['ema_slow'] and
            curr['ema_fast'] > curr['ema_slow'] and
            curr['rsi'] > RSI_BUY):
        return "BUY"

    # SELL signali
    if (prev['ema_fast'] > prev['ema_slow'] and
            curr['ema_fast'] < curr['ema_slow'] and
            curr['rsi'] < RSI_SELL):
        return "SELL"

    return "HOLD"


def calc_lot(symbol: str, risk_percent: float, sl_points: float) -> float:
    """Risk asosida lot hisoblash"""
    account_info = mt5.account_info()
    if account_info is None:
        return LOT_SIZE
    balance      = account_info.balance
    risk_amount  = balance * (risk_percent / 100)
    tick_value   = mt5.symbol_info(symbol).trade_tick_value
    tick_size    = mt5.symbol_info(symbol).trade_tick_size
    lot = risk_amount / (sl_points / tick_size * tick_value)
    lot = round(max(lot, LOT_SIZE), 2)
    return lot


def place_order(symbol: str, order_type: str, lot: float,
                sl_pips: float = 200, tp_pips: float = 400):
    """Buyurtma yuborish (Stop-Loss va Take-Profit bilan)"""
    tick      = mt5.symbol_info_tick(symbol)
    point     = mt5.symbol_info(symbol).point

    if order_type == "BUY":
        price = tick.ask
        sl    = price - sl_pips * point
        tp    = price + tp_pips * point
        otype = mt5.ORDER_TYPE_BUY
    else:
        price = tick.bid
        sl    = price + sl_pips * point
        tp    = price - tp_pips * point
        otype = mt5.ORDER_TYPE_SELL

    request = {
        "action":       mt5.TRADE_ACTION_DEAL,
        "symbol":       symbol,
        "volume":       lot,
        "type":         otype,
        "price":        price,
        "sl":           sl,
        "tp":           tp,
        "deviation":    10,
        "magic":        MAGIC,
        "comment":      "bitcoin_bot",
        "type_time":    mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"❌ Order xatosi: {result.retcode} | {result.comment}")
    else:
        print(f"✅ {order_type} order ochildi | Price: {price:.2f} | SL: {sl:.2f} | TP: {tp:.2f}")
    return result


def has_open_position(symbol: str) -> bool:
    """Ochiq pozitsiya bormi?"""
    positions = mt5.positions_get(symbol=symbol)
    return positions is not None and len(positions) > 0


def run_bot(login: int, password: str, server: str):
    """Asosiy bot sikli"""
    if not connect_mt5(login, password, server):
        return

    print(f"\n🤖 Bitcoin Trading Bot ishga tushdi")
    print(f"📊 Juft: {SYMBOL} | TF: H1 | Strategiya: EMA({EMA_FAST}/{EMA_SLOW}) + RSI({RSI_PERIOD})")
    print("⚠️  ESLATMA: Bu moliyaviy maslahat emas. Risklarni hisobga oling!\n")

    try:
        while True:
            df = get_candles(SYMBOL, TIMEFRAME, 100)
            if df.empty:
                continue

            signal = get_signal(df)
            now    = datetime.now().strftime("%H:%M:%S")
            price  = df.iloc[-1]['close']

            print(f"[{now}] BTC: ${price:,.2f} | Signal: {signal}")

            if signal != "HOLD" and not has_open_position(SYMBOL):
                lot = calc_lot(SYMBOL, RISK_PERCENT, sl_points=200)
                place_order(SYMBOL, signal, lot, sl_pips=200, tp_pips=400)

            # Har 60 soniyada tekshirish
            import time
            time.sleep(60)

    except KeyboardInterrupt:
        print("\n🛑 Bot to'xtatildi.")
    finally:
        mt5.shutdown()


# ── ISHGA TUSHIRISH ──────────────────────────────────────────
if __name__ == "__main__":
    # MT5 login ma'lumotlaringizni kiriting
    MT5_LOGIN    = 12345678       # MT5 hisob raqami
    MT5_PASSWORD = "your_pass"   # MT5 paroli
    MT5_SERVER   = "Broker-Server"  # Broker server nomi

    run_bot(MT5_LOGIN, MT5_PASSWORD, MT5_SERVER)
