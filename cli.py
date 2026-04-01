from __future__ import annotations

import argparse

from regime.report import SECTOR_NAMES, TICKER_NAMES, build_regime_report, normalize_tickers_csv
from regime.indicators import market_regime

_GREEN = "\033[32m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_RESET = "\033[0m"


def _regime_color(label: str) -> str:
    if label == "BULLISH":
        return _GREEN
    if label == "BEARISH":
        return _RED
    return _YELLOW


def _c(text: str, color: str) -> str:
    return f"{color}{text}{_RESET}"


def _print_ticker_row(ticker: str, row: dict, ticker_regimes: dict) -> None:
    if not row.get("ok"):
        print(f"\n{ticker} skipped: {row['error']}")
        return
    result = row["ma"]
    structure = row["trend"]
    levels = row["levels"]
    regime = row["regime"]
    ticker_regimes[ticker] = regime
    price = result["price"]
    display_name = row["display_name"]
    name_suffix = f"  ({display_name})" if display_name else ""
    print(f"\n{ticker}{name_suffix}  Close: {price:.2f}")

    slope_sym = {True: _c("↑", _GREEN), False: _c("↓", _RED), None: "~"}
    ma_parts = []
    for period, ma in result["moving_averages"].items():
        pos = _c("ABOVE", _GREEN) if ma["price_above"] else _c("BELOW", _RED)
        sym = slope_sym[ma["slope_rising"]]
        ma_parts.append(f"{period}d {pos}{sym}")
    ma_str = "  ".join(ma_parts)
    ac, bc = result["above_count"], result["below_count"]
    rc, fc = result["rising_count"], result["falling_count"]
    pos_color = _GREEN if ac > bc else (_RED if bc > ac else "")
    slope_color = _GREEN if rc > fc else (_RED if fc > rc else "")
    pos_str = _c(f"+{ac}/-{bc}", pos_color) if pos_color else f"+{ac}/-{bc}"
    slope_str = _c(f"+{rc}/-{fc}", slope_color) if slope_color else f"+{rc}/-{fc}"
    print(f"  MA:      {ma_str}  ({pos_str} pos, {slope_str} slope)")

    def _fmt_dist(name):
        d = levels["distance_pct"][name]
        return "N/A" if d is None else f"{d:+.1f}%"

    print(
        f"  Levels:  ATH {_fmt_dist('ath')}  RHigh {_fmt_dist('recent_high_252d')}  "
        f"SHigh {_fmt_dist('last_swing_high')}  SLow {_fmt_dist('last_swing_low')}  "
        f"PSLow {_fmt_dist('prior_significant_low')}"
    )

    trend_label = structure["label"]
    trend_col = _GREEN if trend_label == "UPTREND" else (_RED if trend_label == "DOWNTREND" else _YELLOW)
    print(f"  Trend:   {_c(trend_label, trend_col)} ({structure['reason']})")

    checks = regime["checks"]
    check_str = "  ".join(f"{k}={_c(v, _regime_color(v.upper()))}" for k, v in checks.items())
    regime_label = regime["label"]
    print(
        f"  Regime:  {_c(regime_label, _regime_color(regime_label))}  "
        f"+{regime['bullish_checks']}/-{regime['bearish_checks']} (net {regime['net_score']:+d})  {check_str}"
    )


def _print_summary(label: str, ticker_regimes: dict, total_fetched: int) -> None:
    summary = market_regime(ticker_regimes)
    print(f"\n=== {label} Summary ===")
    for ticker, regime in ticker_regimes.items():
        display_name = SECTOR_NAMES.get(ticker, "") or TICKER_NAMES.get(ticker, "") or ticker
        lbl = regime["label"]
        print(f"  {ticker:<20} {display_name:<30}  {_c(lbl, _regime_color(lbl))}")
    slbl = summary["label"]
    print(f"Regime:        {_c(slbl, _regime_color(slbl))}")
    print(f"Tickers used:  {summary['tickers_used']}")
    c = summary["counts"]
    print(f"Tickers:       bullish={c['bullish']} neutral={c['neutral']} bearish={c['bearish']}")
    suffix = " (partial data)" if summary["tickers_used"] < total_fetched else ""
    print(f"Average net:   {summary['average_net_score']:+.2f}{suffix}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Technical Regime — market regime checklist")
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--sectors", action="store_true", help="Run US sector ETF universe")
    g.add_argument("--bonds", action="store_true", help="Run bonds / Treasury yields preset")
    g.add_argument("--futures", action="store_true", help="Run futures preset")
    g.add_argument("--currencies", action="store_true", help="Run FX preset")
    g.add_argument(
        "--tickers",
        type=str,
        default=None,
        help="Custom comma-separated tickers, e.g. AAPL,MSFT,NVDA",
    )
    args = parser.parse_args(argv)

    tickers = normalize_tickers_csv(args.tickers) if args.tickers else None
    if args.tickers is not None and not tickers:
        print("Error: no tickers provided. Example: --tickers AAPL,MSFT")
        raise SystemExit(1)

    report = build_regime_report(
        use_sectors=args.sectors,
        use_bonds=args.bonds,
        use_futures=args.futures,
        use_currencies=args.currencies,
        tickers=tickers,
    )

    for t, reason in report["fetch_errors"].items():
        print(f"\n{t} skipped: {reason}")

    if report["overall_fetched_count"] == 0:
        print("Error: no ticker data available.")
        raise SystemExit(1)

    tickers = report["tickers"]

    if report.get("custom_tickers"):
        ticker_regimes: dict = {}
        info = report["regions"]["Custom"]
        for ticker in info["tickers"]:
            row = tickers[ticker]
            _print_ticker_row(ticker, row, ticker_regimes)
        _print_summary("Custom", ticker_regimes, info["fetched_count"])
        return

    if report["use_sectors"]:
        ticker_regimes: dict = {}
        info = report["regions"]["Sectors"]
        for ticker in info["tickers"]:
            row = tickers[ticker]
            _print_ticker_row(ticker, row, ticker_regimes)
        _print_summary("Sector", ticker_regimes, info["fetched_count"])
        return

    if report["use_bonds"]:
        ticker_regimes = {}
        info = report["regions"]["Bonds"]
        for ticker in info["tickers"]:
            row = tickers[ticker]
            _print_ticker_row(ticker, row, ticker_regimes)
        _print_summary("Bonds", ticker_regimes, info["fetched_count"])
        return

    if report["use_futures"]:
        ticker_regimes = {}
        info = report["regions"]["Futures"]
        for ticker in info["tickers"]:
            row = tickers[ticker]
            _print_ticker_row(ticker, row, ticker_regimes)
        _print_summary("Futures", ticker_regimes, info["fetched_count"])
        return

    if report["use_currencies"]:
        ticker_regimes = {}
        info = report["regions"]["Currencies"]
        for ticker in info["tickers"]:
            row = tickers[ticker]
            _print_ticker_row(ticker, row, ticker_regimes)
        _print_summary("Currencies", ticker_regimes, info["fetched_count"])
        return

    for region_name, info in report["regions"].items():
        print(f"\n{'='*40}")
        print(f"  {region_name}")
        print(f"{'='*40}")
        region_regimes: dict = {}
        for ticker in info["tickers"]:
            row = tickers[ticker]
            _print_ticker_row(ticker, row, region_regimes)
        _print_summary(region_name, region_regimes, info["fetched_count"])

    print(f"\n{'='*40}")
    overall_regs = {t: tickers[t]["regime"] for t in tickers if tickers[t].get("ok")}
    _print_summary("Overall Market", overall_regs, report["overall_fetched_count"])


if __name__ == "__main__":
    main()
