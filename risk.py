# ============================================================
# Risk boshqaruvi: SL/TP masofasi va lot hisoblash
# Jonli bot (bitcoin_strategy.py) va backtest (backtest.py)
# bitta formuladan foydalanishi uchun. MetaTrader5 kerak emas.
# ============================================================

import math


def sl_tp_distance(price: float, sl_percent: float, tp_percent: float) -> tuple:
    """
    SL va TP masofasi narx birligida — narxning foizi sifatida.
    Broker'ning point qiymatiga bog'liq emas: BTC $100,000 da 1% = $1,000.
    """
    return price * sl_percent / 100, price * tp_percent / 100


def lot_from_risk(risk_amount: float, loss_per_lot: float,
                  min_lot: float, lot_step: float, max_lot: float) -> float:
    """
    Risk asosida lot: SL tegsa zarar ≈ risk_amount bo'ladi.
    loss_per_lot — 1 lot uchun SL tegsagi zarar (hisob valyutasida).
    Lot lot_step ga pastga yaxlitlanadi va [min_lot, max_lot] oralig'ida bo'ladi.
    """
    if loss_per_lot <= 0:
        return min_lot
    lot = risk_amount / loss_per_lot
    lot = math.floor(lot / lot_step + 1e-9) * lot_step
    lot = min(max(lot, min_lot), max_lot)
    return round(lot, 8)
