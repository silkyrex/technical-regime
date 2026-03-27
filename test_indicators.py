import pandas as pd
from unittest.mock import patch
from regime.indicators import moving_averages, trend_structure, MA_PERIODS, SLOPE_LOOKBACK
from regime.data import fetch, MIN_ROWS


def _make_df(closes: list[float]) -> pd.DataFrame:
    """Build a minimal DataFrame that moving_averages() can consume."""
    return pd.DataFrame({"Close": closes})


def _make_hl_df(highs: list[float], lows: list[float]) -> pd.DataFrame:
    """Build a minimal DataFrame for swing-based trend tests."""
    close = [(h + l) / 2.0 for h, l in zip(highs, lows)]
    return pd.DataFrame(
        {
            "High": highs,
            "Low": lows,
            "Close": close,
        },
        index=pd.date_range("2024-01-01", periods=len(highs), freq="D"),
    )


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


def test_not_enough_data_raises():
    """Too few rows: at least one MA is NaN at the last bar."""
    try:
        moving_averages(_make_df([100.0]))
    except ValueError as exc:
        assert "Not enough data" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_flat_series_slope_not_rising():
    """Flat price: MA equals prior-week MA, so slope is not rising (counts as falling)."""
    n = max(MA_PERIODS) + SLOPE_LOOKBACK + 1
    closes = [100.0] * n
    result = moving_averages(_make_df(closes))
    for period, ma in result["moving_averages"].items():
        assert ma["slope_rising"] is False, f"{period}-day MA flat should not be rising"
    assert result["rising_count"] == 0
    assert result["falling_count"] == len(MA_PERIODS)


def test_trend_structure_uptrend():
    highs = [8, 9, 10, 11, 10, 9, 8, 9, 10, 12, 10, 9, 8, 9, 10, 13, 10, 9, 8]
    lows = [7, 6, 4, 6, 7, 8, 9, 7, 5, 7, 8, 9, 8, 7, 6, 7, 8, 9, 10]
    result = trend_structure(_make_hl_df(highs, lows), window=2)
    assert result["label"] == "UPTREND"
    assert result["reason"] == "HH/HL"


def test_trend_structure_downtrend():
    highs = [9, 10, 12, 13, 12, 11, 10, 9, 11, 12, 11, 10, 9, 8, 10, 11, 10, 9, 8]
    lows = [10, 9, 8, 9, 10, 11, 12, 10, 7, 10, 11, 12, 11, 10, 6, 10, 11, 12, 13]
    result = trend_structure(_make_hl_df(highs, lows), window=2)
    assert result["label"] == "DOWNTREND"
    assert result["reason"] == "LH/LL"


def test_trend_structure_mixed_hh_ll():
    highs = [8, 9, 10, 11, 10, 9, 8, 9, 10, 12, 10, 9, 8, 9, 10, 13, 10, 9, 8]
    lows = [9, 8, 6, 8, 9, 10, 11, 9, 5, 9, 10, 11, 10, 9, 4, 9, 10, 11, 12]
    result = trend_structure(_make_hl_df(highs, lows), window=2)
    assert result["label"] == "MIXED"
    assert result["reason"] == "HH/LL"


def test_trend_structure_strict_tie_not_a_swing():
    highs = [7, 8, 10, 10, 8, 7, 8, 9, 11, 9, 8, 7, 8, 9, 12, 9, 8]
    lows = [9, 8, 7, 8, 9, 10, 9, 8, 6, 8, 9, 10, 9, 8, 5, 8, 9]
    result = trend_structure(_make_hl_df(highs, lows), window=2)
    high_indices = [s["index"] for s in result["swing_highs"]]
    assert 2 not in high_indices and 3 not in high_indices


def test_trend_structure_default_window_path():
    n = 30
    highs = [100.0] * n
    lows = [90.0] * n
    highs[10] = 110.0
    highs[20] = 120.0
    lows[10] = 85.0
    lows[20] = 88.0
    result = trend_structure(_make_hl_df(highs, lows))
    assert result["label"] == "UPTREND"
    assert result["reason"] == "HH/HL"


def test_trend_structure_insufficient():
    highs = [100.0, 101.0, 102.0, 101.0, 100.0, 99.0, 98.0]
    lows = [95.0, 94.0, 93.0, 94.0, 95.0, 96.0, 97.0]
    result = trend_structure(_make_hl_df(highs, lows), window=2)
    assert result["label"] == "INSUFFICIENT"
    assert result["reason"] == "NOT_ENOUGH_SWINGS"


def test_trend_structure_missing_columns_raises():
    bad_df = pd.DataFrame({"Close": [1.0, 2.0, 3.0]})
    try:
        trend_structure(bad_df)
    except ValueError as exc:
        assert "High and Low" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def _make_ohlcv_df(rows: int) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=rows, freq="D")
    values = [100.0 + i for i in range(rows)]
    return pd.DataFrame(
        {
            "Open": values,
            "High": [v + 1.0 for v in values],
            "Low": [v - 1.0 for v in values],
            "Close": values,
        },
        index=idx,
    )


def test_fetch_happy_path_returns_clean_dataframe():
    sample_df = _make_ohlcv_df(MIN_ROWS)
    with patch("regime.data.yf.Ticker") as mock_ticker:
        mock_ticker.return_value.history.return_value = sample_df
        result = fetch("SPY", period="2y")
    assert len(result) == MIN_ROWS
    assert list(result.columns)[:4] == ["Open", "High", "Low", "Close"]


def test_fetch_missing_required_column_raises():
    sample_df = _make_ohlcv_df(MIN_ROWS).drop(columns=["Low"])
    with patch("regime.data.yf.Ticker") as mock_ticker:
        mock_ticker.return_value.history.return_value = sample_df
        try:
            fetch("SPY", period="2y")
        except ValueError as exc:
            assert "Missing required columns" in str(exc)
            assert "Low" in str(exc)
        else:
            raise AssertionError("expected ValueError")
