import pandas as pd

MA_PERIODS = [10, 20, 50, 100, 200]
SLOPE_LOOKBACK = 5  # trading days (one week) to measure MA direction


def moving_averages(df: pd.DataFrame) -> dict:
    """Compute SMAs, price-relative position, and slope direction for a single ticker."""
    close = df["Close"]
    current_price = close.iloc[-1]

    results = {}
    for period in MA_PERIODS:
        ma_series = close.rolling(period).mean()
        ma_value = ma_series.iloc[-1]
        if pd.isna(ma_value):
            raise SystemExit(f"Not enough data to compute {period}-day MA.")

        prior_value = ma_series.iloc[-(SLOPE_LOOKBACK + 1)]
        slope_rising = None if pd.isna(prior_value) else bool(ma_value > prior_value)

        results[period] = {
            "series": ma_series,
            "value": ma_value,
            "price_above": current_price > ma_value,
            "slope_rising": slope_rising,
        }

    above_count = sum(1 for r in results.values() if r["price_above"])
    below_count = len(results) - above_count
    rising_count = sum(1 for r in results.values() if r["slope_rising"] is True)
    falling_count = sum(1 for r in results.values() if r["slope_rising"] is False)

    return {
        "price": current_price,
        "moving_averages": results,
        "above_count": above_count,
        "below_count": below_count,
        "rising_count": rising_count,
        "falling_count": falling_count,
    }
