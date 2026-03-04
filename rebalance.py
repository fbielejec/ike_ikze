#!/usr/bin/env python3
"""
GEM (Global Equities Momentum) Rebalancing Script for Bossa.pl IKE/IKZE

All values are in PLN. The script calculates exact sell/buy transactions
to move from the current portfolio state to 100% in the target ETF.

ETF lineup:
  SPYL     — SPDR S&P 500 UCITS ETF (Acc), IE000XZSV718, USD on LSE
  IEMA     — iShares MSCI EM UCITS ETF (Acc), IE00B4L5YC18, USD on LSE
  ETFBTBSP — Beta ETF TBSP (Acc), PLBTBSP00012, PLN on GPW (fixed-rate bonds)
  ETFBCASH — Beta ETF Obligacji 6M (Acc), PLBETWT00010, PLN on GPW (cash equivalent)

=== HOW TO USE ===

Step 1: Determine the momentum winner (which ETF to hold)
  - Run: python rebalance.py signal
  - The script fetches 12-month price data from Stooq, converts
    everything to PLN, and shows which ETF had the highest return
  - The lookback window is 12 months ending at the last day of the
    month BEFORE the current month (current month is skipped)
    e.g. on 1 March 2026 → range is 1 Feb 2025 to 28 Feb 2026

Step 2: Gather portfolio state from Bossa.pl
  - Log into https://trader.bossa.pl/
  - From the portfolio view, note for each position:
    - Name/ticker of the ETF
    - Number of units held
    - Current price per unit in PLN (as shown in Bossa)
  - Note the PLN cash balance on the account
  - Pass holdings via --holding NAME:UNITS:PRICE_PLN
  - Pass cash via --cash (PLN)

Step 3: Run the rebalance and execute
  - Run: python rebalance.py rebalance --target <WINNER> ...
  - The script outputs the exact sell/buy orders with PLN amounts
  - Execute the trades manually in the Bossa trader interface

Examples:
  # Check momentum signal
  python rebalance.py signal

  # Switch from IEMA to SPYL
  python rebalance.py rebalance --target SPYL --target-price 67.50 --cash 1200 --holding IEMA:120:185.50

  # Fresh start, cash only
  python rebalance.py rebalance --target SPYL --target-price 67.50 --cash 50000

  # Already in target, extra cash available
  python rebalance.py rebalance --target SPYL --cash 4500 --holding SPYL:350:67.50

  # Already in target, no extra cash
  python rebalance.py rebalance --target SPYL --cash 100 --holding SPYL:350:67.50
"""

import argparse
import csv
import io
import math
import sys
import urllib.request
import urllib.error
from datetime import date, timedelta


# --- ETF and data configuration ---

ETFS = {
    "SPYL":     {"stooq": "spyl.uk",      "currency": "USD"},
    "IEMA":     {"stooq": "iema.uk",      "currency": "USD"},
    "ETFBTBSP": {"stooq": "etfbtbsp.pl",  "currency": "PLN"},
    "ETFBCASH": {"stooq": "etfbcash.pl",  "currency": "PLN"},
}
FX_TICKER = "usdpln"
STOOQ_URL = "https://stooq.pl/q/d/l/?s={ticker}&d1={d1}&d2={d2}&i=d"


# --- Stooq data fetching ---

def fetch_stooq_csv(ticker, d1, d2):
    """Fetch daily close prices from Stooq. Returns list of (date_str, close)."""
    url = STOOQ_URL.format(
        ticker=ticker,
        d1=d1.strftime("%Y%m%d"),
        d2=d2.strftime("%Y%m%d"),
    )
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
    except (urllib.error.URLError, OSError) as e:
        print(f"Error: Could not fetch data from Stooq for '{ticker}': {e}", file=sys.stderr)
        sys.exit(1)

    if not raw.strip() or raw.strip() == "Brak danych":
        print(
            f"Error: No price data returned for '{ticker}'. "
            f"The ticker may be delisted or Stooq may be temporarily unavailable.",
            file=sys.stderr,
        )
        sys.exit(1)

    rows = []
    reader = csv.DictReader(io.StringIO(raw))
    for row in reader:
        rows.append((row["Data"], float(row["Zamkniecie"])))
    rows.sort(key=lambda r: r[0])
    return rows


def lookback_window(today):
    """Return (start_date, end_date) for the 12-month lookback, skipping current month."""
    # End = last day of previous month
    first_of_month = today.replace(day=1)
    end = first_of_month - timedelta(days=1)
    # Start = first day of the month 12 months before end's month
    start_year = end.year - 1
    start_month = end.month
    start = date(start_year, start_month, 1)
    return start, end


# --- Signal command ---

def cmd_signal(args):
    today = date.today()
    start, end = lookback_window(today)

    # Fetch USD/PLN rates
    fx_data = fetch_stooq_csv(FX_TICKER, start, end)
    fx_by_date = {d: rate for d, rate in fx_data}

    results = []
    for name, info in ETFS.items():
        prices = fetch_stooq_csv(info["stooq"], start, end)

        if info["currency"] == "USD":
            # Convert to PLN
            pln_prices = []
            for d, close in prices:
                if d in fx_by_date:
                    pln_prices.append((d, close * fx_by_date[d]))
            prices = pln_prices

        if len(prices) < 2:
            print(f"Warning: Insufficient data for {name}, skipping.", file=sys.stderr)
            continue

        first_close = prices[0][1]
        last_close = prices[-1][1]
        ret = (last_close - first_close) / first_close * 100
        results.append((name, ret, prices[0][0], prices[-1][0]))

    if not results:
        print("Error: No valid data for any ETF.", file=sys.stderr)
        sys.exit(1)

    results.sort(key=lambda r: r[1], reverse=True)
    winner = results[0][0]

    # Use actual date range from data
    actual_start = min(r[2] for r in results)
    actual_end = max(r[3] for r in results)
    current_month = today.strftime("%b %Y")

    print(f"\n=== GEM MOMENTUM SIGNAL ===")
    print(f"Date: {today}")
    print(f"Lookback: {actual_start} to {actual_end} (skip {current_month})")
    print()
    for i, (name, ret, _, _) in enumerate(results, 1):
        marker = "  <- WINNER" if i == 1 else ""
        print(f"  #{i}  {name:<10} {ret:+.1f}%  (PLN){marker}")
    print(f"\nTarget ETF: {winner}")
    print()


# --- Rebalance command ---

def parse_holding(s):
    """Parse 'NAME:UNITS:PRICE_PLN' into (name, units, price)."""
    parts = s.split(":")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError(
            f"Invalid holding format: '{s}'. Expected NAME:UNITS:PRICE_PLN"
        )
    name = parts[0].upper()
    try:
        units = int(parts[1])
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid unit count: '{parts[1]}'. Must be an integer."
        )
    try:
        price = float(parts[2])
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid price: '{parts[2]}'. Must be a number."
        )
    return (name, units, price)


def fmt(amount):
    """Format PLN amount with thousands separator and 2 decimals."""
    return f"{amount:,.2f}"


def cmd_rebalance(args):
    target = args.target.upper()
    cash = args.cash
    holdings = args.holding or []
    target_price = args.target_price

    # Find target price from holdings if not provided
    if target_price is None:
        for name, units, price in holdings:
            if name == target:
                target_price = price
                break

    if target_price is None:
        print(
            f"Error: --target-price is required when target ETF '{target}' "
            f"is not in current holdings.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Calculate portfolio value
    holdings_value = sum(units * price for _, units, price in holdings)
    total_value = cash + holdings_value

    # Determine sells (everything not target) and existing target units
    sells = []
    existing_target_units = 0
    sell_proceeds = 0.0

    for name, units, price in holdings:
        if name != target:
            sells.append((name, units, price))
            sell_proceeds += units * price
        else:
            existing_target_units = units

    # Calculate buys
    available_cash = cash + sell_proceeds
    new_units = math.floor(available_cash / target_price)
    buy_cost = new_units * target_price
    leftover_cash = available_cash - buy_cost

    # Final state
    final_units = existing_target_units + new_units
    final_holding_value = final_units * target_price
    final_cash = leftover_cash
    final_total = final_holding_value + final_cash
    idle_pct = (final_cash / final_total * 100) if final_total > 0 else 0

    # Output
    print(f"\n=== GEM REBALANCE ===")
    print(f"Date: {date.today()}")
    print(f"Target ETF: {target}")

    print(f"\nCURRENT PORTFOLIO:")
    print(f"  Cash:          {fmt(cash)} PLN")
    for name, units, price in holdings:
        value = units * price
        print(f"  {name}:{' ' * (13 - len(name))}{units} units × {fmt(price)} PLN = {fmt(value)} PLN")
    print(f"  Total:         {fmt(total_value)} PLN")

    print(f"\nTRANSACTIONS:")
    if not sells and new_units == 0:
        print(f"  No transactions needed.")
    else:
        for name, units, price in sells:
            value = units * price
            print(f"  SELL  {units:>5} × {name:<6} @ {fmt(price)} PLN = {fmt(value)} PLN")
        if new_units > 0:
            print(f"  BUY   {new_units:>5} × {target:<6} @ {fmt(target_price)} PLN = {fmt(buy_cost)} PLN")

    print(f"\nRESULT:")
    if final_units > 0:
        print(f"  {target}:{' ' * (13 - len(target))}{final_units} units × {fmt(target_price)} PLN = {fmt(final_holding_value)} PLN")
    print(f"  Cash:          {fmt(final_cash)} PLN")
    print(f"  Total:         {fmt(final_total)} PLN")
    print(f"  Idle cash:     {idle_pct:.1f}% of portfolio")
    print()


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(
        description="GEM momentum signal & rebalancing calculator for Bossa.pl IKE/IKZE (PLN)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # signal
    subparsers.add_parser(
        "signal",
        help="Fetch 12-month price data and show momentum winner",
    )

    # rebalance
    rebal = subparsers.add_parser(
        "rebalance",
        help="Calculate sell/buy transactions to rebalance into target ETF",
    )
    rebal.add_argument(
        "--target",
        required=True,
        help="Target ETF ticker (e.g. SPYL, IEMA, ETFBCASH)",
    )
    rebal.add_argument(
        "--cash",
        type=float,
        default=0.0,
        help="PLN cash balance on the account",
    )
    rebal.add_argument(
        "--holding",
        type=parse_holding,
        action="append",
        default=None,
        metavar="NAME:UNITS:PRICE_PLN",
        help="Current position (repeatable). Example: --holding SPYL:350:67.50",
    )
    rebal.add_argument(
        "--target-price",
        type=float,
        default=None,
        metavar="PRICE_PLN",
        help="Current PLN price per unit of the target ETF (required if target not in holdings)",
    )

    args = parser.parse_args()

    if args.command == "signal":
        cmd_signal(args)
    elif args.command == "rebalance":
        cmd_rebalance(args)


if __name__ == "__main__":
    main()
