#!/usr/bin/env python3
"""
Generate an ICS calendar file with GEM rebalance check reminders.

Creates one all-day event per month on the first trading day (skipping
weekends and GPW holidays). Each event has 5 daily alarms (day 0 through
day 4) so that missed reminders keep firing for up to 5 days.

The output file can be imported into Proton Calendar (or any other
calendar app that supports ICS).

Usage:
  # Default: from next month until 12 months from now
  python reminders.py

  # Custom date range
  python reminders.py --start 2026-06 --end 2028-12

  # Custom output file
  python reminders.py -o my-reminders.ics
"""

import argparse
import sys
from datetime import date, timedelta

# GPW (Warsaw Stock Exchange) non-weekend holidays.
# Fixed-date holidays that recur every year.
GPW_FIXED_HOLIDAYS = [
    (1, 1),    # New Year's Day
    (1, 6),    # Epiphany
    (5, 1),    # May Day
    (5, 3),    # Constitution Day
    (8, 15),   # Assumption of Mary
    (11, 1),   # All Saints' Day
    (11, 11),  # Independence Day
    (12, 24),  # Christmas Eve
    (12, 25),  # Christmas Day
    (12, 26),  # 2nd Day of Christmas
    (12, 31),  # New Year's Eve
]


def easter(year):
    """Compute Easter Sunday for a given year (Anonymous Gregorian algorithm)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def gpw_holidays(year):
    """Return a set of GPW holiday dates for a given year."""
    holidays = set()
    for month, day in GPW_FIXED_HOLIDAYS:
        holidays.add(date(year, month, day))
    easter_sun = easter(year)
    holidays.add(easter_sun + timedelta(days=1))   # Easter Monday
    holidays.add(easter_sun + timedelta(days=60))  # Corpus Christi
    return holidays


def first_trading_day(year, month):
    """Return the first trading day (non-weekend, non-GPW-holiday) of a month."""
    holidays = gpw_holidays(year)
    d = date(year, month, 1)
    while d.weekday() >= 5 or d in holidays:
        d += timedelta(days=1)
    return d


def generate_ics(start_year, start_month, end_year, end_month):
    """Generate ICS content with rebalance reminders for the given range."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//GEM Rebalance//EN",
        "CALSCALE:GREGORIAN",
        "X-WR-CALNAME:GEM Rebalance",
        "X-WR-TIMEZONE:Europe/Warsaw",
    ]

    today = date.today()
    y, m = start_year, start_month
    while (y, m) <= (end_year, end_month):
        ftd = first_trading_day(y, m)
        next_day = ftd + timedelta(days=1)
        uid = f"gem-rebalance-{y}-{m:02d}@ike"

        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uid}")
        lines.append(f"DTSTAMP:{today.strftime('%Y%m%d')}T000000Z")
        lines.append(f"DTSTART;VALUE=DATE:{ftd.strftime('%Y%m%d')}")
        lines.append(f"DTEND;VALUE=DATE:{next_day.strftime('%Y%m%d')}")
        lines.append("SUMMARY:GEM Rebalance Check")
        lines.append(
            "DESCRIPTION:Run: python rebalance.py signal\\n\\n"
            "If the winner changed\\, rebalance into the new ETF.\\n"
            "Log into Bossa.pl\\, check holdings\\, and run rebalance command if needed."
        )
        lines.append("TRANSP:TRANSPARENT")

        for alarm_day in range(5):
            lines.append("BEGIN:VALARM")
            lines.append(f"TRIGGER:P{alarm_day}D")
            lines.append("ACTION:DISPLAY")
            if alarm_day == 0:
                lines.append("DESCRIPTION:GEM Rebalance Check - run python rebalance.py signal")
            else:
                lines.append("DESCRIPTION:GEM Rebalance Check - still pending!")
            lines.append("END:VALARM")

        lines.append("END:VEVENT")

        # advance to next month
        if m == 12:
            y += 1
            m = 1
        else:
            m += 1

    lines.append("END:VCALENDAR")
    return "\n".join(lines) + "\n"


def parse_month(s):
    """Parse YYYY-MM string into (year, month)."""
    parts = s.split("-")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError(f"Invalid format: '{s}'. Expected YYYY-MM.")
    try:
        year, month = int(parts[0]), int(parts[1])
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid format: '{s}'. Expected YYYY-MM.")
    if month < 1 or month > 12:
        raise argparse.ArgumentTypeError(f"Month must be 1-12, got {month}.")
    return year, month


def main():
    today = date.today()
    # Default start: next month
    if today.month == 12:
        default_start = f"{today.year + 1}-01"
    else:
        default_start = f"{today.year}-{today.month + 1:02d}"
    # Default end: 12 months from now
    end = today.replace(day=1) + timedelta(days=365)
    default_end = f"{end.year}-{end.month:02d}"

    parser = argparse.ArgumentParser(
        description="Generate ICS file with GEM rebalance check reminders"
    )
    parser.add_argument(
        "--start",
        type=parse_month,
        default=default_start,
        metavar="YYYY-MM",
        help=f"First month to include (default: {default_start})",
    )
    parser.add_argument(
        "--end",
        type=parse_month,
        default=default_end,
        metavar="YYYY-MM",
        help=f"Last month to include (default: {default_end})",
    )
    parser.add_argument(
        "-o", "--output",
        default="gem-rebalance.ics",
        metavar="FILE",
        help="Output file path (default: gem-rebalance.ics)",
    )

    args = parser.parse_args()

    if isinstance(args.start, str):
        args.start = parse_month(args.start)
    if isinstance(args.end, str):
        args.end = parse_month(args.end)

    start_year, start_month = args.start
    end_year, end_month = args.end

    if (start_year, start_month) > (end_year, end_month):
        print("Error: --start must be before --end.", file=sys.stderr)
        sys.exit(1)

    ics = generate_ics(start_year, start_month, end_year, end_month)
    with open(args.output, "w") as f:
        f.write(ics)

    # Count events
    count = 0
    y, m = start_year, start_month
    while (y, m) <= (end_year, end_month):
        count += 1
        m = m + 1 if m < 12 else 1
        y = y if m > 1 else y + 1

    print(f"Wrote {count} reminders to {args.output}")
    print(f"Range: {start_year}-{start_month:02d} to {end_year}-{end_month:02d}")
    print(f"Import into Proton Calendar: Settings > Import calendar > {args.output}")


if __name__ == "__main__":
    main()
