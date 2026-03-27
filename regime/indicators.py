import pandas as pd

MA_PERIODS = [10, 20, 50, 100, 200]
SLOPE_LOOKBACK = 5  # trading days (one week) to measure MA direction
SWING_WINDOW = 5


def moving_averages(df: pd.DataFrame) -> dict:
    """Compute SMAs, price-relative position, and slope direction for a single ticker.

    Slope compares today's MA to the value SLOPE_LOOKBACK bars ago. If equal (flat),
    slope_rising is False — same as falling for the printed +rising / -falling counts.
    """
    close = df["Close"]
    current_price = close.iloc[-1]

    results = {}
    for period in MA_PERIODS:
        ma_series = close.rolling(period).mean()
        ma_value = ma_series.iloc[-1]
        if pd.isna(ma_value):
            raise ValueError(f"Not enough data to compute {period}-day MA.")

        prior_value = ma_series.iloc[-(SLOPE_LOOKBACK + 1)]
        slope_rising = None if pd.isna(prior_value) else bool(ma_value > prior_value)

        results[period] = {
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


def trend_structure(df: pd.DataFrame, window: int = SWING_WINDOW) -> dict:
    """Classify trend structure using confirmed swing highs/lows.

    A confirmed swing center i needs window bars on each side:
    window <= i <= len(df) - 1 - window.
    """
    if window < 1:
        raise ValueError("window must be >= 1")
    if "High" not in df.columns or "Low" not in df.columns:
        raise ValueError("DataFrame must include High and Low columns.")

    highs = df["High"]
    lows = df["Low"]
    swing_highs = []
    swing_lows = []

    for i in range(window, len(df) - window):
        high_window = highs.iloc[i - window : i + window + 1]
        low_window = lows.iloc[i - window : i + window + 1]
        center_high = highs.iloc[i]
        center_low = lows.iloc[i]

        # Strict-only extrema: center must be the unique max/min in its window.
        if center_high == high_window.max() and (high_window == center_high).sum() == 1:
            swing_highs.append({"index": i, "date": df.index[i], "price": float(center_high)})
        if center_low == low_window.min() and (low_window == center_low).sum() == 1:
            swing_lows.append({"index": i, "date": df.index[i], "price": float(center_low)})

    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return {
            "label": "INSUFFICIENT",
            "reason": "NOT_ENOUGH_SWINGS",
            "swing_window": window,
            "swing_highs": swing_highs[-2:],
            "swing_lows": swing_lows[-2:],
        }

    # Compare pivots from a shared recent context to avoid stale/misaligned pairs.
    common_cutoff = min(swing_highs[-1]["index"], swing_lows[-1]["index"])
    comparable_highs = [s for s in swing_highs if s["index"] <= common_cutoff]
    comparable_lows = [s for s in swing_lows if s["index"] <= common_cutoff]
    last_highs = comparable_highs[-2:] if len(comparable_highs) >= 2 else swing_highs[-2:]
    last_lows = comparable_lows[-2:] if len(comparable_lows) >= 2 else swing_lows[-2:]

    h1 = last_highs[0]["price"]
    h2 = last_highs[1]["price"]
    l1 = last_lows[0]["price"]
    l2 = last_lows[1]["price"]

    if h2 > h1 and l2 > l1:
        label, reason = "UPTREND", "HH/HL"
    elif h2 < h1 and l2 < l1:
        label, reason = "DOWNTREND", "LH/LL"
    elif h2 > h1 and l2 < l1:
        label, reason = "MIXED", "HH/LL"
    elif h2 < h1 and l2 > l1:
        label, reason = "MIXED", "HL/LH"
    else:
        label, reason = "MIXED", "MIXED"

    return {
        "label": label,
        "reason": reason,
        "swing_window": window,
        "swing_highs": last_highs,
        "swing_lows": last_lows,
    }
