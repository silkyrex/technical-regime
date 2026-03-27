import sys

from regime.data import fetch_all, TICKERS, SECTOR_TICKERS
from regime.indicators import (
    key_levels,
    market_regime,
    moving_averages,
    ticker_regime,
    trend_structure,
)


def _print_level(levels: dict, name: str, label: str):
    level = levels["levels"][name]
    dist = levels["distance_pct"][name]
    level_text = "N/A" if level is None else f"{level:.2f}"
    dist_text = "N/A" if dist is None else f"{dist:+.1f}%"
    print(f"    {label:<6} {level_text:>8}  ({dist_text})")


SECTOR_NAMES = {
    "XLE": "Energy",
    "XLU": "Utilities",
    "XLRE": "Real Estate",
    "XLP": "Consumer Staples",
    "XLF": "Financials",
    "XLB": "Materials",
    "XLY": "Consumer Discretionary",
    "XLI": "Industrials",
    "XLC": "Communication Services",
    "XLK": "Technology",
}


def main():
    use_sectors = "--sectors" in sys.argv
    tickers = SECTOR_TICKERS if use_sectors else TICKERS
    label = "Sector" if use_sectors else "Market"

    data, fetch_errors = fetch_all(tickers)
    for t, reason in fetch_errors.items():
        print(f"\n{t} skipped: {reason}")
    if not data:
        print("Error: no ticker data available.")
        raise SystemExit(1)
    ticker_regimes = {}
    for ticker, df in data.items():
        try:
            result = moving_averages(df)
        except ValueError as exc:
            print(f"\n{ticker} skipped: {exc}")
            continue
        structure = trend_structure(df)
        levels = key_levels(df, trend_result=structure)
        price = result["price"]
        sector_name = SECTOR_NAMES.get(ticker, "")
        name_suffix = f"  ({sector_name})" if sector_name else ""
        print(f"\n{ticker}{name_suffix}  Close: {price:.2f}")
        for period, ma in result["moving_averages"].items():
            position = "ABOVE" if ma["price_above"] else "BELOW"
            slope = {True: "RISING", False: "FALLING", None: "  N/A "}[ma["slope_rising"]]
            diff_pct = (price - ma["value"]) / ma["value"] * 100
            print(f"  {period:>3d}-day MA: {ma['value']:>8.2f}  {position:>5s}  {slope:>7s}  ({diff_pct:+.1f}%)")
        print(f"  Price vs MA:  +{result['above_count']}/-{result['below_count']}")
        print(f"  MA slope:     +{result['rising_count']}/-{result['falling_count']}")
        print(f"  Trend:        {structure['label']} ({structure['reason']})")
        print("  Key levels:")
        _print_level(levels, "ath", "ATH")
        _print_level(levels, "recent_high_252d", "RHigh")
        _print_level(levels, "last_swing_high", "SHigh")
        _print_level(levels, "last_swing_low", "SLow")
        _print_level(levels, "prior_significant_low", "PSLow")

        regime = ticker_regime(result, structure, levels)
        ticker_regimes[ticker] = regime
        checks = regime["checks"]
        print(f"  Regime:      {regime['label']}")
        print(f"  Checklist:   +{regime['bullish_checks']}/-{regime['bearish_checks']} (net {regime['net_score']:+d})")
        print(
            "  Checks:      "
            f"MA={checks['ma']}  Trend={checks['trend']}  RHigh={checks['rhigh']}  PSLow={checks['pslow']}"
        )

    market = market_regime(ticker_regimes)
    print(f"\n=== {label} Summary ===")
    print(f"{label} regime: {market['label']}")
    print(f"Tickers used:  {market['tickers_used']}")
    c = market["counts"]
    print(f"Tickers:       bullish={c['bullish']} neutral={c['neutral']} bearish={c['bearish']}")
    suffix = " (partial data)" if market["tickers_used"] < len(data) else ""
    print(f"Average net:   {market['average_net_score']:+.2f}{suffix}")


if __name__ == "__main__":
    main()
