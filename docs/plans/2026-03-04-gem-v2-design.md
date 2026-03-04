# GEM v2 — Momentum Signal + New ETF Lineup

## Summary

Upgrade rebalance.py with two changes:
1. ✅ New `signal` subcommand that fetches 12-month price data from Stooq and calculates momentum in PLN terms
2. ✅ Updated ETF lineup: SPYL (S&P 500), IEMA (EM), ETFBCASH (Polish bonds)

## ETF Lineup

| Role | Old | New | ISIN | Stooq | Currency |
|---|---|---|---|---|---|
| US Equities (S&P 500) | CSPX | **SPYL** | IE000XZSV718 | spyl.uk | USD |
| Emerging Markets | IEMA | **IEMA** | IE00B4L5YC18 | iema.uk | USD |
| Bonds / Cash | CBU0 + IB01 | **ETFBCASH** | PLBETWT00010 | etfbcash.pl | PLN |

### Why SPYL over CSPX
- TER: 0.03% vs 0.07%
- Tracking difference: -0.20% vs -0.21% (best in class)
- Physical replication (no swap counterparty risk)
- Unit price ~17 USD vs ~630 USD — minimal idle cash when rebalancing
- €12B AUM, growing fast

### Why ETFBCASH over CBU0/IB01
- No USD/PLN currency risk — priced and settled in PLN natively
- Trades on GPW (same exchange as Bossa IKE/IKZE)
- Floating-rate Polish gov bonds — very low volatility (52-week range: 143–145 PLN)
- Replaces two bond ETFs with one simpler option
- Downside: higher TER (0.40% vs 0.07%), Polish sovereign credit risk

## Architecture ✅

Single file `rebalance.py` with two subcommands via argparse subparsers:

```
python rebalance.py signal                          # fetch data, show momentum winner
python rebalance.py rebalance --target ... --cash ... --holding ...  # calculate trades
```

No external dependencies — pure Python stdlib (urllib, csv, argparse).

## `signal` subcommand ✅

### Behavior
1. Determine 12-month lookback window, skipping current month
   - e.g. on 2026-03-04 → 2025-02-03 to 2026-02-28
2. Download daily close prices from Stooq for all 3 ETFs + USD/PLN rate
3. Convert SPYL and IEMA to PLN (close × USD/PLN rate on same day)
4. ETFBCASH already in PLN — use as-is
5. Calculate % return = (last close − first close) / first close
6. Print ranked results, declare winner

### Output
```
=== GEM MOMENTUM SIGNAL ===
Date: 2026-03-04
Lookback: 2025-02-03 to 2026-02-27 (skip Mar 2026)

  #1  SPYL       +28.3%  (PLN)  ← WINNER
  #2  IEMA       +12.1%  (PLN)
  #3  ETFBCASH    +5.8%  (PLN)

Target ETF: SPYL
```

### No arguments needed — fully automatic date/data logic.

## `rebalance` subcommand ✅

Unchanged API from current script:
```
python rebalance.py rebalance --target SPYL --target-price 67.50 --cash 1200 --holding IEMA:120:185.50
```

Same logic: sell non-target → buy target with all available PLN → report leftover cash.

### Future enhancement (not in scope)
`rebalance` without `--target` could run `signal` internally and use the winner automatically.

## Stooq integration ✅

### Ticker mapping (hardcoded)
```python
ETFS = {
    "SPYL":     {"stooq": "spyl.uk",     "currency": "USD"},
    "IEMA":     {"stooq": "iema.uk",     "currency": "USD"},
    "ETFBCASH": {"stooq": "etfbcash.pl", "currency": "PLN"},
}
FX = {"USDPLN": "usdpln"}
```

### URL pattern
`https://stooq.pl/q/d/l/?s={ticker}&d1={YYYYMMDD}&d2={YYYYMMDD}&i=d`

### CSV columns
`Data,Otwarcie,Najwyzszy,Najnizszy,Zamkniecie,Wolumen` — use `Zamkniecie` (close).

### Edge cases
- **Trading day alignment**: SPYL/IEMA on LSE, ETFBCASH on GPW — different holidays. Use first/last available close for each ETF independently.
- **"Brak danych" response**: error with clear message
- **Missing USD/PLN for a day**: skip that day when converting
- **< 200 trading days available**: warning, still calculate with available data

## Error handling ✅

- Network failure → clear error naming the ticker
- Empty/invalid CSV → clear error suggesting Stooq may be down
- Insufficient data → warning but proceed
- No verbose/debug flags — keep it simple

## Documentation updates ✅

Update GEM_STRATEGY.md to reflect new ETF lineup after implementation.
