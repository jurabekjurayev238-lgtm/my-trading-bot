# ============================================================
# Bitcoin Trading Strategy for MetaTrader 5
# Strategy: EMA Crossover + RSI Filter + Risk Management
# Author: Jony | my-trading-bot
# ============================================================

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime

from indicators import add_signals
from risk import lot_from_risk, sl_tp_distance

# ── SOZLAMALAR ──────────────────────────────────────────────
SYMBOL       = "BTCUSD"
TIMEFRAME    = mt5.TIMEFRAME_H1   # 1 soatlik chart
EMA_FAST     = 9                  # Tez EMA
EMA_SLOW     = 21                 # Sekin EMA
RSI_PERIOD   = 14                 # RSI davri
RSI_BUY      = 50                 # RSI buy chegarasi
RSI_SELL     = 50                 # RSI sell chegarasi
RISK_PERCENT = 1.0                # Har bir tradeda hisobning 1% risk
SL_PERCENT   = 1.0                # Stop-Loss: narxdan 1% (BTC $100k da ≈ $1,000)
TP_PERCENT   = 2.0                # Take-Profit: narxdan 2% (RR 1:2)
LOT_SIZE     = 0.01               # Minimal lot (simvol ma'lumoti bo'lmasa)
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


def get_signal(df: pd.DataFrame) -> str:
    """
    Signal aniqlash (mantiq indicators.add_signals da — backtest bilan umumiy):
    BUY  → EMA_fast yuqoriga kesib o'tdi + RSI > 50
    SELL → EMA_fast pastga kesib o'tdi + RSI < 50
    """
    df = add_signals(df, EMA_FAST, EMA_SLOW, RSI_PERIOD, RSI_BUY, RSI_SELL)
    signal = df['signal'].iloc[-1]
    if signal == 1:
        return "BUY"
    if signal == -1:
        return "SELL"
    return "HOLD"


def calc_lot(symbol: str, risk_percent: float, sl_distance: float) -> float:
    """
    Risk asosida lot: SL tegsa hisobning risk_percent % i yo'qotiladi.
    sl_distance — SL masofasi narx birligida (masalan $1,000).
    """
    account_info = mt5.account_info()
    info         = mt5.symbol_info(symbol)
    if account_info is None or info is None:
        return LOT_SIZE
    balance      = account_info.balance
    risk_amount  = balance * (risk_percent / 100)
    loss_per_lot = sl_distance / info.trade_tick_size * info.trade_tick_value
    lot = lot_from_risk(risk_amount, loss_per_lot,
                        info.volume_min, info.volume_step, info.volume_max)

    real_risk = lot * loss_per_lot
    if balance > 0 and real_risk > risk_amount * 1.01:
        print(f"⚠️  Minimal lot {lot} bilan risk ${real_risk:,.2f} "
              f"({real_risk / balance * 100:.1f}%) — {risk_percent}% dan katta!")
    return lot


def place_order(symbol: str, order_type: str, lot: float,
                sl_distance: float, tp_distance: float):
    """Buyurtma yuborish (Stop-Loss va Take-Profit bilan). Masofalar narx birligida."""
    tick      = mt5.symbol_info_tick(symbol)
    digits    = mt5.symbol_info(symbol).digits

    if order_type == "BUY":
        price = tick.ask
        sl    = round(price - sl_distance, digits)
        tp    = round(price + tp_distance, digits)
        otype = mt5.ORDER_TYPE_BUY
    else:
        price = tick.bid
        sl    = round(price + sl_distance, digits)
        tp    = round(price - tp_distance, digits)
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
        print(f"✅ {order_type} order ochildi | Lot: {lot} | Price: {price:.2f} | SL: {sl:.2f} | TP: {tp:.2f}")
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
    print(f"🛡️  Risk: {RISK_PERCENT}% | SL: {SL_PERCENT}% | TP: {TP_PERCENT}%")
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
                sl_dist, tp_dist = sl_tp_distance(price, SL_PERCENT, TP_PERCENT)
                lot = calc_lot(SYMBOL, RISK_PERCENT, sl_dist)
                place_order(SYMBOL, signal, lot, sl_dist, tp_dist)

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
