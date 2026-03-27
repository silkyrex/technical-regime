import pandas as pd
from regime.indicators import moving_averages, MA_PERIODS, SLOPE_LOOKBACK


def _make_df(closes: list[float]) -> pd.DataFrame:
    """Build a minimal DataFrame that moving_averages() can consume."""
    return pd.DataFrame({"Close": closes})


def test_slope_rising():
    """A steadily rising series should make every MA rising."""
    n = max(MA_PERIODS) + SLOPE_LOOKBACK + 1
    closes = [100.0 + i for i in range(n)]
    result = moving_averages(_make_df(closes))
    for period, ma in result["moving_averages"].items():
        assert ma["slope_rising"] is True, f"{period}-day MA should be rising"
    assert result["rising_count"] == len(MA_PERIODS)
    assert result["falling_count"] == 0


def test_slope_falling():
    """A steadily falling series should make every MA falling."""
    n = max(MA_PERIODS) + SLOPE_LOOKBACK + 1
    closes = [500.0 - i for i in range(n)]
    result = moving_averages(_make_df(closes))
    for period, ma in result["moving_averages"].items():
        assert ma["slope_rising"] is False, f"{period}-day MA should be falling"
    assert result["rising_count"] == 0
    assert result["falling_count"] == len(MA_PERIODS)


def test_slope_mixed():
    """A flat-then-rising series: long MAs may still be rising while slope captures the upturn."""
    n = max(MA_PERIODS) + SLOPE_LOOKBACK + 1
    flat = [100.0] * (n - 20)
    ramp = [100.0 + i * 2 for i in range(1, 21)]
    result = moving_averages(_make_df(flat + ramp))
    short_ma = result["moving_averages"][10]
    assert short_ma["slope_rising"] is True, "10-day MA should pick up the ramp"


def test_price_above_still_works():
    """Slope addition must not break the existing price-position logic."""
    n = max(MA_PERIODS) + SLOPE_LOOKBACK + 1
    closes = [100.0 + i for i in range(n)]
    result = moving_averages(_make_df(closes))
    assert result["above_count"] == len(MA_PERIODS)
    assert result["below_count"] == 0
