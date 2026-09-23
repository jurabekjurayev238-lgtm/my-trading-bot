# my-trading-bot
Bitcoin trading bot for MetaTrader 5

## Fayllar

| Fayl | Vazifasi |
|------|----------|
| `bitcoin_strategy.py` | Jonli bot: EMA(9/21) kesishuvi + RSI(14) filtri, SL 1% / TP 2%, 1% risk |
| `indicators.py` | EMA, RSI va signal mantiqi — bot va backtest uchun umumiy |
| `risk.py` | SL/TP masofasi va lot hisoblash — bot va backtest uchun umumiy |
| `backtest.py` | MT5 tarixida backtest + parametrlarni optimallashtirish |
| `tests/` | Bot va backtest testlari (MT5 kerak emas) |

## O'rnatish

MetaTrader5 Python paketi faqat **Windows**'da ishlaydi, MT5 terminali o'rnatilgan va ochiq bo'lishi kerak.

```bash
pip install -r requirements.txt
```

## Backtest

```bash
# Hozirgi sozlamalar bilan (EMA 9/21, RSI 14, SL 1% / TP 2%)
python backtest.py --from 2024-01-01 --to 2025-01-01

# Boshqa timeframe va parametrlar
python backtest.py --timeframe H4 --from 2023-01-01 --ema-fast 12 --ema-slow 26 --sl-pct 1.5 --tp-pct 3
```

MT5 login: terminalda hisob ochiq bo'lsa hech narsa kerak emas. Aks holda muhit o'zgaruvchilarini bering
(parolni buyruq qatoriga yozmaslik uchun):

```powershell
$env:MT5_LOGIN="12345678"; $env:MT5_PASSWORD="parol"; $env:MT5_SERVER="Broker-Server"
```

Asosiy parametrlar: `--symbol`, `--timeframe` (M5, M15, M30, H1, H4, D1), `--balance`, `--risk`,
`--ema-fast`, `--ema-slow`, `--rsi`, `--rsi-buy`, `--rsi-sell`, `--sl-pct`, `--tp-pct`,
`--spread-points` (default: MT5 tarixidagi spread), `--commission`, `--out`. To'liq ro'yxat: `python backtest.py -h`.

Natijalar `results/` papkasida:
- `trades.csv` — har bir savdo (kirish/chiqish vaqti, narx, lot, sabab: TP/SL/END, foyda)
- `equity.png` — equity va drawdown grafigi
- konsolda: win rate, profit factor, sof foyda, max drawdown, buy & hold bilan taqqoslash

## Optimizatsiya

```bash
python backtest.py --from 2023-01-01 --optimize
python backtest.py --from 2023-01-01 --optimize --opt-ema-fast 5,9,12 --opt-ema-slow 21,34,50 \
    --opt-rsi 50,55 --opt-sl 0.5,1,2 --opt-tp 1,2,4
```

- EMA fast/slow, RSI darajasi (BUY > L, SELL < 100-L) va SL/TP kombinatsiyalari sinab ko'riladi.
- Ma'lumot **70% in-sample / 30% out-of-sample** ga bo'linadi (`--oos`). Parametrlar faqat birinchi qismda
  tanlanadi, eng yaxshi 5 tasi ikkinchi qismda qayta tekshiriladi (`oos_*` ustunlari).
  In-sample'da zo'r, out-of-sample'da yomon natija — parametrlar tarixga moslashib qolgani (overfitting) belgisi.
- `--min-trades` dan kam savdo qilgan kombinatsiyalar tashlanadi. To'liq jadval: `results/optimization.csv`.

## Muhim eslatmalar

- **SL/TP narx foizida.** `SL_PERCENT = 1.0`, `TP_PERCENT = 2.0` (bot sozlamalarida). BTC $100,000 da
  SL ≈ $1,000, TP ≈ $2,000. Broker'ning `point` qiymatiga bog'liq emas (avval 200 point edi — `point = 0.01`
  bo'lgan brokerlarda bu atigi $2 bo'lib, spread'dan ham kichik edi).
- **Lot hisobi.** Lot shunday tanlanadiki, SL tegsa aynan `RISK_PERCENT` (1%) yo'qotiladi:
  `lot = balans × 1% / (SL masofasi / tick_size × tick_value)`, broker'ning lot qadamiga pastga yaxlitlanadi.
  Kichik hisobda minimal lot (0.01) ham 1% dan ko'p risk qilsa, bot ogohlantirish chiqaradi.
- **Signal vaqti.** Jonli bot har 60 soniyada hali yopilmagan shamdan signal oladi; backtest esa signalni
  yopilgan shamda oladi va keyingi sham ochilishida kiradi. Natijalar farq qilishi mumkin.
- **Simulyatsiya qoidalari.** Bir vaqtda 1 pozitsiya; bitta shamda SL ham TP ham tegsa — SL deb hisoblanadi;
  gap bo'lsa — sham ochilish narxida chiqiladi; lot bot bilan bir xil formulada (`risk.py`).
- **Tarix uzunligi.** MT5 "Tools → Options → Charts → Max bars in chart" sozlamasi berilgan shamlar sonini
  cheklaydi. Ma'lumot kam kelsa, uni oshiring.
- O'tgan natijalar kelajakni kafolatlamaydi. Bu moliyaviy maslahat emas.

## Testlar

```bash
pip install pytest
pytest
```
