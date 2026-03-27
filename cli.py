from regime.data import fetch_all
from regime.indicators import moving_averages


def main():
    data = fetch_all()
    for ticker, df in data.items():
        result = moving_averages(df)
        price = result["price"]
        print(f"\n{ticker}  Close: {price:.2f}")
        for period, ma in result["moving_averages"].items():
            position = "ABOVE" if ma["price_above"] else "BELOW"
            slope = {True: "RISING", False: "FALLING", None: "  N/A "}[ma["slope_rising"]]
            diff_pct = (price - ma["value"]) / ma["value"] * 100
            print(f"  {period:>3d}-day MA: {ma['value']:>8.2f}  {position:>5s}  {slope:>7s}  ({diff_pct:+.1f}%)")
        print(f"  Price vs MA:  +{result['above_count']}/-{result['below_count']}")
        print(f"  MA slope:     +{result['rising_count']}/-{result['falling_count']}")


if __name__ == "__main__":
    main()
