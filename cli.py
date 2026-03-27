import sys

from regime.data import fetch_all, TICKERS, SECTOR_TICKERS, REGIONS
from regime.indicators import (
    key_levels,
    market_regime,
    moving_averages,
    ticker_regime,
    trend_structure,
)

_GREEN  = "\033[32m"
_RED    = "\033[31m"
_YELLOW = "\033[33m"
_RESET  = "\033[0m"


def _regime_color(label: str) -> str:
    if label == "BULLISH": return _GREEN
    if label == "BEARISH": return _RED
    return _YELLOW


def _c(text: str, color: str) -> str:
    return f"{color}{text}{_RESET}"



TICKER_NAMES = {
    # Americas
    "^VIX":             "CBOE Volatility Index",
    "^GSPTSE":          "S&P/TSX Composite",
    "^BVSP":            "Bovespa Index",
    "DX-Y.NYB":         "U.S. Dollar Index",
    "^RUT":             "Russell 2000",
    "^GSPC":            "S&P 500",
    "^DJI":             "Dow Jones",
    "^IXIC":            "Nasdaq Composite",
    # Europe
    "^FTSE":            "FTSE 100",
    "^XDE":             "Euro Currency Index",
    "^XDB":             "British Pound Index",
    "^FCHI":            "CAC 40",
    "^N100":            "Euronext 100",
    "^STOXX50E":        "EURO STOXX 50",
    "^125904-USD-STRD": "MSCI Europe",
    "^GDAXI":           "DAX",
    # Asia
    "000001.SS":        "SSE Composite",
    "^HSI":             "Hang Seng",
    "^XDA":             "Australian Dollar Index",
    "^AXJO":            "S&P/ASX 200",
    "^XDN":             "Japanese Yen Index",
    "^KS11":            "KOSPI",
    "^N225":            "Nikkei 225",
    "^BSESN":           "S&P BSE Sensex",
}

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


def _print_ticker(ticker: str, df, ticker_regimes: dict) -> None:
    try:
        result = moving_averages(df)
    except ValueError as exc:
        print(f"\n{ticker} skipped: {exc}")
        return
    structure = trend_structure(df)
    levels = key_levels(df, trend_result=structure)
    price = result["price"]
    display_name = SECTOR_NAMES.get(ticker, "") or TICKER_NAMES.get(ticker, "")
    name_suffix = f"  ({display_name})" if display_name else ""
    print(f"\n{ticker}{name_suffix}  Close: {price:.2f}")

    slope_sym = {True: _c("↑", _GREEN), False: _c("↓", _RED), None: "~"}
    ma_parts = []
    for period, ma in result["moving_averages"].items():
        pos = _c("ABOVE", _GREEN) if ma["price_above"] else _c("BELOW", _RED)
        sym = slope_sym[ma["slope_rising"]]
        ma_parts.append(f"{period}d {pos}{sym}")
    ma_str = "  ".join(ma_parts)
    ac, bc = result['above_count'], result['below_count']
    rc, fc = result['rising_count'], result['falling_count']
    pos_color = _GREEN if ac > bc else (_RED if bc > ac else "")
    slope_color = _GREEN if rc > fc else (_RED if fc > rc else "")
    pos_str   = _c(f"+{ac}/-{bc}", pos_color)   if pos_color   else f"+{ac}/-{bc}"
    slope_str = _c(f"+{rc}/-{fc}", slope_color) if slope_color else f"+{rc}/-{fc}"
    print(f"  MA:      {ma_str}  ({pos_str} pos, {slope_str} slope)")

    def _fmt_dist(name):
        d = levels["distance_pct"][name]
        return "N/A" if d is None else f"{d:+.1f}%"
    print(f"  Levels:  ATH {_fmt_dist('ath')}  RHigh {_fmt_dist('recent_high_252d')}  SHigh {_fmt_dist('last_swing_high')}  SLow {_fmt_dist('last_swing_low')}  PSLow {_fmt_dist('prior_significant_low')}")

    trend_label = structure['label']
    trend_col = _GREEN if trend_label == "UPTREND" else (_RED if trend_label == "DOWNTREND" else _YELLOW)
    print(f"  Trend:   {_c(trend_label, trend_col)} ({structure['reason']})")

    regime = ticker_regime(result, structure, levels)
    ticker_regimes[ticker] = regime
    checks = regime["checks"]
    check_str = "  ".join(
        f"{k}={_c(v, _regime_color(v.upper()))}" for k, v in checks.items()
    )
    regime_label = regime['label']
    print(f"  Regime:  {_c(regime_label, _regime_color(regime_label))}  +{regime['bullish_checks']}/-{regime['bearish_checks']} (net {regime['net_score']:+d})  {check_str}")


def _print_summary(label: str, ticker_regimes: dict, total_fetched: int) -> None:
    summary = market_regime(ticker_regimes)
    print(f"\n=== {label} Summary ===")
    for ticker, regime in ticker_regimes.items():
        display_name = SECTOR_NAMES.get(ticker, "") or TICKER_NAMES.get(ticker, "") or ticker
        lbl = regime['label']
        print(f"  {ticker:<20} {display_name:<30}  {_c(lbl, _regime_color(lbl))}")
    slbl = summary['label']
    print(f"Regime:        {_c(slbl, _regime_color(slbl))}")
    print(f"Tickers used:  {summary['tickers_used']}")
    c = summary["counts"]
    print(f"Tickers:       bullish={c['bullish']} neutral={c['neutral']} bearish={c['bearish']}")
    suffix = " (partial data)" if summary["tickers_used"] < total_fetched else ""
    print(f"Average net:   {summary['average_net_score']:+.2f}{suffix}")


def main():
    use_sectors = "--sectors" in sys.argv

    if use_sectors:
        data, fetch_errors = fetch_all(SECTOR_TICKERS)
        for t, reason in fetch_errors.items():
            print(f"\n{t} skipped: {reason}")
        if not data:
            print("Error: no ticker data available.")
            raise SystemExit(1)
        ticker_regimes: dict = {}
        for ticker, df in data.items():
            _print_ticker(ticker, df, ticker_regimes)
        _print_summary("Sector", ticker_regimes, len(data))
        return

    data, fetch_errors = fetch_all(TICKERS)
    for t, reason in fetch_errors.items():
        print(f"\n{t} skipped: {reason}")
    if not data:
        print("Error: no ticker data available.")
        raise SystemExit(1)

    all_ticker_regimes: dict = {}
    for region_name, region_tickers in REGIONS.items():
        region_data = {t: data[t] for t in region_tickers if t in data}
        if not region_data:
            continue
        print(f"\n{'='*40}")
        print(f"  {region_name}")
        print(f"{'='*40}")
        region_regimes: dict = {}
        for ticker, df in region_data.items():
            _print_ticker(ticker, df, region_regimes)
        all_ticker_regimes.update(region_regimes)
        _print_summary(region_name, region_regimes, len(region_data))

    print(f"\n{'='*40}")
    _print_summary("Overall Market", all_ticker_regimes, len(data))


if __name__ == "__main__":
    main()
