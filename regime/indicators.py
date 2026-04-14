from __future__ import annotations

import pandas as pd

MA_PERIODS = [10, 20, 50, 100, 200]
SLOPE_LOOKBACK = 5  # trading days (one week) to measure MA direction
SWING_WINDOW = 5
RECENT_HIGH_WINDOW = 252
R_HIGH_BULLISH_MIN = -2.0
R_HIGH_BEARISH_MAX = -8.0
P_SLOW_BULLISH_MIN = 3.0
P_SLOW_BEARISH_MAX = 0.0
REGIME_BULLISH_MIN = 2
REGIME_BEARISH_MAX = -2


def moving_averages(df: pd.DataFrame, periods: list[int] | None = None) -> dict:
    """Compute SMAs, price-relative position, and slope direction for a single ticker.

    Slope compares today's MA to the value SLOPE_LOOKBACK bars ago. If equal (flat),
    slope_rising is False — same as falling for the printed +rising / -falling counts.
    """
    close = df["Close"]
    current_price = close.iloc[-1]

    if periods is None:
        periods = MA_PERIODS

    results = {}
    for period in periods:
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
        max_val = high_window.max()
        if center_high == max_val and (high_window == max_val).sum() == 1:
            swing_highs.append({"index": i, "date": df.index[i], "price": float(center_high)})
        min_val = low_window.min()
        if center_low == min_val and (low_window == min_val).sum() == 1:
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


def _distance_pct(price: float, level: float | None) -> float | None:
    """Return percent distance from level, or None when not computable."""
    if level is None or level <= 0:
        return None
    return (price - level) / level * 100


def key_levels(df: pd.DataFrame, trend_result: dict | None = None) -> dict:
    """Compute key levels and price distance to each level.

    Pass trend_result to reuse an already-computed trend_structure output.
    """
    if "High" not in df.columns or "Close" not in df.columns:
        raise ValueError("DataFrame must include High and Close columns.")

    price = float(df["Close"].iloc[-1])
    highs = df["High"]
    ath = float(highs.max())
    recent_window_used = min(RECENT_HIGH_WINDOW, len(highs))
    recent_high = float(highs.tail(recent_window_used).max())

    last_swing_high = None
    last_swing_low = None
    prior_significant_low = None
    swing_source = "ok"
    swing_error = None
    try:
        structure = trend_result if trend_result is not None else trend_structure(df)
        if structure["swing_highs"]:
            last_swing_high = float(structure["swing_highs"][-1]["price"])
        if structure["swing_lows"]:
            last_swing_low = float(structure["swing_lows"][-1]["price"])
        if len(structure["swing_lows"]) >= 2:
            prior_significant_low = float(structure["swing_lows"][-2]["price"])
    except ValueError as exc:
        swing_source = "unavailable"
        swing_error = str(exc)

    levels = {
        "ath": ath,
        "recent_high_252d": recent_high,
        "last_swing_high": last_swing_high,
        "last_swing_low": last_swing_low,
        "prior_significant_low": prior_significant_low,
    }
    distance_pct = {name: _distance_pct(price, level) for name, level in levels.items()}

    return {
        "price": price,
        "levels": levels,
        "distance_pct": distance_pct,
        "recent_high_window_used": recent_window_used,
        "swing_source": swing_source,
        "swing_error": swing_error,
    }


def _ma_cluster_signal(ma_result: dict) -> str:
    pos = "neutral"
    if ma_result["above_count"] >= 4:
        pos = "bullish"
    elif ma_result["below_count"] >= 4:
        pos = "bearish"

    slope = "neutral"
    if ma_result["rising_count"] >= 4:
        slope = "bullish"
    elif ma_result["falling_count"] >= 4:
        slope = "bearish"

    if pos == slope and pos != "neutral":
        return pos
    return "neutral"


def _trend_signal(trend_result: dict) -> str:
    if trend_result["label"] == "UPTREND":
        return "bullish"
    if trend_result["label"] == "DOWNTREND":
        return "bearish"
    return "neutral"


def _rhigh_signal(levels_result: dict) -> str:
    dist = levels_result["distance_pct"].get("recent_high_252d")
    if dist is None:
        return "neutral"
    if dist >= R_HIGH_BULLISH_MIN:
        return "bullish"
    if dist <= R_HIGH_BEARISH_MAX:
        return "bearish"
    return "neutral"


def _pslow_signal(levels_result: dict) -> str:
    dist = levels_result["distance_pct"].get("prior_significant_low")
    if dist is None:
        return "neutral"
    if dist >= P_SLOW_BULLISH_MIN:
        return "bullish"
    if dist <= P_SLOW_BEARISH_MAX:
        return "bearish"
    return "neutral"


def ticker_regime(ma_result: dict, trend_result: dict, levels_result: dict) -> dict:
    checks = {
        "ma": _ma_cluster_signal(ma_result),
        "trend": _trend_signal(trend_result),
        "rhigh": _rhigh_signal(levels_result),
        "pslow": _pslow_signal(levels_result),
    }

    bullish_checks = sum(1 for v in checks.values() if v == "bullish")
    bearish_checks = sum(1 for v in checks.values() if v == "bearish")
    net_score = bullish_checks - bearish_checks

    contradiction = {
        ("bullish", "bearish"),
        ("bearish", "bullish"),
    }
    if (checks["ma"], checks["trend"]) in contradiction:
        label = "NEUTRAL"
    elif net_score >= REGIME_BULLISH_MIN:
        label = "BULLISH"
    elif net_score <= REGIME_BEARISH_MAX:
        label = "BEARISH"
    else:
        label = "NEUTRAL"

    return {
        "label": label,
        "bullish_checks": bullish_checks,
        "bearish_checks": bearish_checks,
        "net_score": net_score,
        "checks": checks,
    }


def market_regime(ticker_regimes: dict[str, dict]) -> dict:
    counts = {"bullish": 0, "neutral": 0, "bearish": 0}
    net_sum = 0
    tickers_used = 0
    for result in ticker_regimes.values():
        tickers_used += 1
        net_sum += result["net_score"]
        if result["label"] == "BULLISH":
            counts["bullish"] += 1
        elif result["label"] == "BEARISH":
            counts["bearish"] += 1
        else:
            counts["neutral"] += 1

    avg_net = 0.0 if tickers_used == 0 else net_sum / tickers_used

    if avg_net >= 2.0:
        label = "BULLISH"
    elif avg_net <= -1.0:
        label = "BEARISH"
    else:
        label = "MIXED"
    return {
        "label": label,
        "counts": counts,
        "tickers_used": tickers_used,
        "average_net_score": avg_net,
    }
