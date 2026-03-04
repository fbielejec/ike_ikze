# Global Equity Momentum (GEM) Strategy — IKE/IKZE

## Overview

A momentum-based strategy that rotates monthly between 4 ETFs, always holding 100% in a single one. Based on Gary Antonacci's Global Equities Momentum research, adapted for Polish IKE/IKZE retirement accounts on Bossa.pl.

## ETFs

| Role | Ticker | Fund | ISIN | TER | Currency | Exchange |
|---|---|---|---|---|---|---|
| US Equities (S&P 500) | **SPYL** | SPDR S&P 500 UCITS ETF (Acc) | IE000XZSV718 | 0.03% | USD | LSE |
| Emerging Markets | **IEMA** | iShares MSCI EM UCITS ETF (Acc) | IE00B4L5YC18 | 0.18% | USD | LSE |
| Polish Bonds (fixed-rate) | **ETFBTBSP** | Beta ETF TBSP (Acc) | PLBTBSP00012 | 0.50% | PLN | GPW |
| Cash (floating-rate) | **ETFBCASH** | Beta ETF Obligacji 6M (Acc) | PLBETWT00010 | 0.40% | PLN | GPW |

All four are accumulating (no dividend payouts — reinvested automatically). SPYL and IEMA trade in USD on LSE; ETFBTBSP and ETFBCASH trade in PLN on the Warsaw Stock Exchange (GPW).

> NOTE: You can visually compare the momentum on https://atlasetf.pl/etf-comparison

### Why these ETFs

**SPYL over CSPX (iShares S&P 500)**: Lower TER (0.03% vs 0.07%), best-in-class tracking difference (-0.20%), physical replication, and ~17 USD unit price (vs ~630 USD for CSPX) which minimizes idle cash when rebalancing. Launched Oct 2023, €12B AUM.

**ETFBTBSP and ETFBCASH over CBU0/IB01 (US Treasury bonds)**: Both eliminate USD/PLN currency risk — priced and settled in PLN natively. ETFBTBSP tracks the TBSP index (fixed-rate Polish government bonds) with higher returns (+8.5%/yr) but meaningful volatility (3.2% annualized, -14.5% max drawdown) — it can win the momentum signal in rate-cutting cycles. ETFBCASH tracks GPWB-BWZ (floating-rate bonds, 6m+ maturity) with near-zero volatility (1.1% annualized, -0.4% max drawdown) — acts as pure cash parking. Both trade on GPW alongside the Bossa IKE/IKZE account.

## Monthly Decision Rules

On the **1st of each month**:

1. Run `python rebalance.py signal` — fetches 12-month price data from Stooq, converts everything to PLN, and shows the momentum winner
2. The script automatically uses a **12-month window, skipping the current month**
   - Example: On **1 March 2026**, compares performance from **1 Feb 2025 → 28 Feb 2026** (skips March 2026)
   - Example: On **1 June 2026**, compares **1 May 2025 → 31 May 2026**
3. **Buy 100% of whichever ETF had the highest return** in that 12-month lookback window
4. If you already hold the winning ETF, do nothing

That's it. One check per month, one possible trade.

## Why This Works (Momentum Logic)

- **Relative momentum**: Picks the strongest-performing asset class over the trailing 12 months
- **Absolute momentum**: The bond ETFs (ETFBTBSP, ETFBCASH) act as safe havens — if stocks underperform bonds, the strategy exits equities
- **Skipping the most recent month**: Research shows the last month introduces noise/mean-reversion; excluding it improves signal quality
- Backed by Antonacci's research showing 17.4% CAGR vs 12.3% for S&P 500 over a 43-year backtest

## Broker Setup (Bossa.pl)

- **Account type**: IKE or IKZE (tax-sheltered retirement accounts)
- **Commission**: 0% on all ETFs within IKE/IKZE (promo through Feb 28, 2027)
- **Standard commission** (if promo expires): 0.29% min 14 PLN for foreign ETFs
- **FX**: Convert PLN → USD via walutomat or similar for SPYL/IEMA trades; ETFBTBSP and ETFBCASH trade directly in PLN

## Differences from Original GEM

| Aspect | Original (Antonacci) | This adaptation |
|---|---|---|
| US equities | S&P 500 | S&P 500 (SPYL) — same index, lowest-cost UCITS ETF |
| International equities | MSCI ACWI ex-US | MSCI Emerging Markets (IEMA) — narrower, higher beta |
| Bonds | US Aggregate Bond (single ETF) | Polish gov bonds: ETFBTBSP (fixed-rate) + ETFBCASH (floating-rate) — no FX risk |
| Momentum check | Manual chart comparison | Automated script fetching data from Stooq, comparing in PLN |
| Rebalancing | Monthly | Monthly — same |

## Differences from Video Author's Setup

The YouTube channel author uses a more aggressive variant:

| Aspect | Video author | This setup |
|---|---|---|
| US equities | CNDX (NASDAQ 100) | SPYL (S&P 500) — broader, less tech-concentrated |
| Emerging Markets | EIMI (EM IMI, inc. small caps) | IEMA (EM standard, large+mid cap only) |
| Bonds | CBU0 + IB01 (US Treasuries) | ETFBTBSP + ETFBCASH (Polish gov bonds) — no USD/PLN risk |
| Broker | XTB | Bossa.pl |

## Key Behavioral Rules

- **No discretion**: Follow the numbers mechanically. Do not skip months or override the signal.
- **No partial positions**: Always 100% in one ETF. Sell the old one completely, buy the new one completely.
- **No emotion**: The strategy will sometimes switch to bonds during a rally, or stay in equities during a dip. Trust the process.
- **Calendar discipline**: Check on the 1st (or first trading day) of every month. Set a recurring reminder.

## Sources

- [Gary Antonacci — Global Equities Momentum](https://www.optimalmomentum.com/global-equities-momentum/)
- [GEM Executive Summary — ReSolve](https://investresolve.com/global-equity-momentum-executive-summary/)
- [Bossa.pl IKE/IKZE ETF offer](https://bossa.pl/oferta/rynek-zagraniczny/kid)
- [Bossa 0% commission promo](https://bossa.pl/o-nas/aktualnosci/2025/0-prowizji-na-etf-etp-etn-etc-na-ike-i-ikze-do-konca-lutego-2026-r)
- [ZAwod Inwestor GEM strategy series](https://www.youtube.com/watch?v=FcLnhY2CqPU&list=PLYmBCT7NufbqaYEjh6ElRK7WDQGEnNl14) (Polish) - transcripts in this directory
