from regime.data import fetch_all
from regime.indicators import (
    MA_PERIODS,
    SWING_WINDOW,
    key_levels,
    market_regime,
    moving_averages,
    ticker_regime,
    trend_structure,
)


def main():
    try:
        data = fetch_all()
    except Exception as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)
    print(
        f"Run summary: tickers={len(data)}  MA periods={MA_PERIODS}  swing_window={SWING_WINDOW}"
    )
    ticker_regimes = {}
    for ticker, df in data.items():
        try:
            result = moving_averages(df)
        except ValueError as exc:
            print(f"\n{ticker} skipped: {exc}")
            continue
        try:
            structure = trend_structure(df)
        except ValueError:
            structure = {"label": "INSUFFICIENT", "reason": "ERROR"}
        try:
            levels = key_levels(df)
        except ValueError:
            levels = {
                "levels": {
                    "ath": None,
                    "recent_high_252d": None,
                    "last_swing_high": None,
                    "last_swing_low": None,
                    "prior_significant_low": None,
                },
                "distance_pct": {
                    "ath": None,
                    "recent_high_252d": None,
                    "last_swing_high": None,
                    "last_swing_low": None,
                    "prior_significant_low": None,
                },
            }
        price = result["price"]
        print(f"\n{ticker}  Close: {price:.2f}")
        print(f"  Rows loaded:  {len(df)}")
        for period, ma in result["moving_averages"].items():
            position = "ABOVE" if ma["price_above"] else "BELOW"
            slope = {True: "RISING", False: "FALLING", None: "  N/A "}[ma["slope_rising"]]
            diff_pct = (price - ma["value"]) / ma["value"] * 100
            print(f"  {period:>3d}-day MA: {ma['value']:>8.2f}  {position:>5s}  {slope:>7s}  ({diff_pct:+.1f}%)")
        print(f"  Price vs MA:  +{result['above_count']}/-{result['below_count']}")
        print(f"  MA slope:     +{result['rising_count']}/-{result['falling_count']}")
        print(f"  Trend:        {structure['label']} ({structure['reason']})")
        print("  Key levels:")

        def _fmt_level(name: str, label: str):
            level = levels["levels"][name]
            dist = levels["distance_pct"][name]
            level_text = "N/A" if level is None else f"{level:.2f}"
            dist_text = "N/A" if dist is None else f"{dist:+.1f}%"
            print(f"    {label:<6} {level_text:>8}  ({dist_text})")

        _fmt_level("ath", "ATH")
        _fmt_level("recent_high_252d", "RHigh")
        _fmt_level("last_swing_high", "SHigh")
        _fmt_level("last_swing_low", "SLow")
        _fmt_level("prior_significant_low", "PSLow")

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
    print("\n=== Market Summary ===")
    print(f"Market regime: {market['label']}")
    print(f"Tickers used:  {market['tickers_used']}")
    c = market["counts"]
    print(f"Tickers:       bullish={c['bullish']} neutral={c['neutral']} bearish={c['bearish']}")
    suffix = " (partial data)" if market["tickers_used"] < 3 else ""
    print(f"Average net:   {market['average_net_score']:+.2f}{suffix}")


if __name__ == "__main__":
    main()
