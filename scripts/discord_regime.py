#!/usr/bin/env python3
"""Post a market regime update to Discord via webhook.

Morning run (6:30 AM PT): global context (Europe + Asia) + full US sweep
Intraday runs (7:30-12:30 PM PT): US-focused only

Usage:
    DISCORD_WEBHOOK_URL=<url> python scripts/discord_regime.py

Set DISCORD_WEBHOOK_URL in the environment or in a .env file at the project root.
"""

from __future__ import annotations

import datetime
import os
import sys

import requests
from zoneinfo import ZoneInfo

# Allow running from scripts/ directory or project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from regime.data import (
    AMERICAS_TICKERS,
    ASIA_TICKERS,
    BOND_TICKERS,
    EUROPE_TICKERS,
    SECTOR_TICKERS,
)
from regime.report import SECTOR_NAMES, TICKER_NAMES, build_regime_report

PT = ZoneInfo("America/Los_Angeles")

REGIME_EMOJI = {"BULLISH": "🟢", "NEUTRAL": "🟡", "BEARISH": "🔴", "MIXED": "🟡"}
REGIME_COLOR = {
    "BULLISH": 0x57F287,
    "NEUTRAL": 0xFEE75C,
    "BEARISH": 0xED4245,
    "MIXED": 0xFEE75C,
}

# Key futures: equity index futures + gold + oil (skip soft commodities)
KEY_FUTURES = ["ES=F", "NQ=F", "YM=F", "RTY=F", "GC=F", "CL=F", "BZ=F"]

# Key FX pairs (DXY already in AMERICAS_TICKERS)
KEY_CURRENCIES = ["EURUSD=X", "USDJPY=X", "GBPUSD=X", "AUDUSD=X"]

DISPLAY_NAMES: dict[str, str] = {
    "ES=F": "S&P 500 Futs",
    "NQ=F": "Nasdaq Futs",
    "YM=F": "Dow Futs",
    "RTY=F": "Russell Futs",
    "GC=F": "Gold",
    "CL=F": "Crude Oil",
    "BZ=F": "Brent Crude",
    "EURUSD=X": "EUR/USD",
    "USDJPY=X": "USD/JPY",
    "GBPUSD=X": "GBP/USD",
    "AUDUSD=X": "AUD/USD",
}


def _display_name(ticker: str) -> str:
    return (
        DISPLAY_NAMES.get(ticker)
        or SECTOR_NAMES.get(ticker)
        or TICKER_NAMES.get(ticker, ticker)
    )


def _is_morning() -> bool:
    """True for the 6:30 AM PT run (hour == 6)."""
    return datetime.datetime.now(PT).hour == 6


def _category_summary(tickers_data: dict, ticker_list: list[str]) -> dict:
    """Aggregate regime counts and avg net score for a group of tickers."""
    counts = {"bullish": 0, "neutral": 0, "bearish": 0}
    net_sum = 0
    n = 0
    for t in ticker_list:
        row = tickers_data.get(t)
        if not row or not row.get("ok"):
            continue
        label = row["regime"]["label"].lower()
        counts[label] = counts.get(label, 0) + 1
        net_sum += row["regime"]["net_score"]
        n += 1
    avg = net_sum / n if n else 0.0
    if avg >= 2.0:
        label = "BULLISH"
    elif avg <= -1.0:
        label = "BEARISH"
    else:
        label = "MIXED"
    return {"label": label, "counts": counts, "avg": avg, "n": n}


def _ticker_lines(tickers_data: dict, ticker_list: list[str]) -> str:
    lines = []
    for t in ticker_list:
        row = tickers_data.get(t)
        if not row or not row.get("ok"):
            continue
        label = row["regime"]["label"]
        net = row["regime"]["net_score"]
        sign = "+" if net > 0 else ""
        emoji = REGIME_EMOJI.get(label, "⚪")
        lines.append(f"{emoji} {_display_name(t)} ({sign}{net})")
    return "\n".join(lines) or "_No data_"


def _category_embed(name: str, tickers_data: dict, ticker_list: list[str]) -> dict:
    s = _category_summary(tickers_data, ticker_list)
    b, n, be = s["counts"]["bullish"], s["counts"]["neutral"], s["counts"]["bearish"]
    title = f"{REGIME_EMOJI.get(s['label'], '⚪')} {name} — {s['label']}  B:{b} N:{n} Be:{be} | avg {s['avg']:+.1f}"
    return {
        "title": title,
        "description": _ticker_lines(tickers_data, ticker_list),
        "color": REGIME_COLOR.get(s["label"], 0xAAAAAA),
    }


def _header_embed(
    overall_label: str,
    summaries: dict[str, dict],
    time_str: str,
    date_str: str,
    errors: int,
) -> dict:
    lines = [f"**{REGIME_EMOJI.get(overall_label, '⚪')} Overall: {overall_label}**", ""]
    for cat, s in summaries.items():
        emoji = REGIME_EMOJI.get(s["label"], "⚪")
        lines.append(f"{emoji} **{cat}**: {s['label']} ({s['avg']:+.1f})")
    if errors:
        lines.append(f"\n_⚠ {errors} tickers failed to fetch_")
    footer_text = "technical-regime • data via yfinance"
    return {
        "title": f"Market Regime — {time_str}  |  {date_str}",
        "description": "\n".join(lines),
        "color": REGIME_COLOR.get(overall_label, 0xAAAAAA),
        "footer": {"text": footer_text},
    }


def _overall_label(tickers_data: dict, all_lists: list[list[str]]) -> str:
    flat = [t for lst in all_lists for t in lst]
    return _category_summary(tickers_data, flat)["label"]


def _post(webhook_url: str, embeds: list[dict]) -> None:
    for i in range(0, len(embeds), 10):
        r = requests.post(webhook_url, json={"embeds": embeds[i : i + 10]}, timeout=15)
        r.raise_for_status()


def main() -> None:
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        # Try loading from .env at project root
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("DISCORD_WEBHOOK_URL="):
                        webhook_url = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not webhook_url:
        print("Error: DISCORD_WEBHOOK_URL not set. Add it to environment or .env file.", file=sys.stderr)
        sys.exit(1)

    now = datetime.datetime.now(PT)
    time_str = now.strftime("%-I:%M %p PT")
    date_str = now.strftime("%a %b %-d")
    morning = _is_morning()

    # Build fetch list (deduplicated)
    us_tickers = AMERICAS_TICKERS + SECTOR_TICKERS + BOND_TICKERS + KEY_FUTURES + KEY_CURRENCIES
    fetch_list = list(dict.fromkeys(us_tickers))  # dedupe, preserve order
    if morning:
        extra = [t for t in EUROPE_TICKERS + ASIA_TICKERS if t not in fetch_list]
        fetch_list = fetch_list + extra

    print(f"[{time_str}] Fetching {len(fetch_list)} tickers (morning={morning})...", flush=True)
    report = build_regime_report(tickers=fetch_list)
    td = report["tickers"]
    errors = len(report["fetch_errors"])

    # Category layout
    categories: dict[str, list[str]] = {
        "Americas": AMERICAS_TICKERS,
        "Sectors": SECTOR_TICKERS,
        "Bonds": BOND_TICKERS,
        "Futures": KEY_FUTURES,
        "FX": KEY_CURRENCIES,
    }
    if morning:
        categories["Europe"] = EUROPE_TICKERS
        categories["Asia"] = ASIA_TICKERS

    summaries = {cat: _category_summary(td, tickers) for cat, tickers in categories.items()}
    overall = _overall_label(td, list(categories.values()))

    header = _header_embed(overall, summaries, time_str, date_str, errors)
    category_embeds = [_category_embed(cat, td, tickers) for cat, tickers in categories.items()]
    embeds = [header] + category_embeds

    _post(webhook_url, embeds)
    print(f"Posted {len(embeds)} embeds to Discord. Errors: {errors}", flush=True)


if __name__ == "__main__":
    main()
