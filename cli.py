from regime.data import fetch_all
from regime.indicators import MA_PERIODS, SWING_WINDOW, moving_averages, trend_structure


def main():
    try:
        data = fetch_all()
    except Exception as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)
    print(
        f"Run summary: tickers={len(data)}  MA periods={MA_PERIODS}  swing_window={SWING_WINDOW}"
    )
    for ticker, df in data.items():
        result = moving_averages(df)
        try:
            structure = trend_structure(df)
        except ValueError:
            structure = {"label": "INSUFFICIENT", "reason": "ERROR"}
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


if __name__ == "__main__":
    main()
