import pandas as pd
from unittest.mock import patch
from io import StringIO
from regime.indicators import key_levels, moving_averages, trend_structure, MA_PERIODS, SLOPE_LOOKBACK
from regime.data import fetch, MIN_ROWS
from cli import main


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
    assert {"Open", "High", "Low", "Close"}.issubset(set(result.columns))


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


def test_fetch_all_rows_dropped_after_cleaning_raises():
    sample_df = _make_ohlcv_df(MIN_ROWS)
    sample_df["Open"] = float("nan")
    with patch("regime.data.yf.Ticker") as mock_ticker:
        mock_ticker.return_value.history.return_value = sample_df
        try:
            fetch("SPY", period="2y")
        except ValueError as exc:
            assert "missing OHLC values after cleaning" in str(exc)
        else:
            raise AssertionError("expected ValueError")


def test_cli_handles_bad_trend_inputs_and_continues():
    bad_df = _make_ohlcv_df(MIN_ROWS).drop(columns=["Low"])
    good_df = _make_ohlcv_df(MIN_ROWS)
    fake_data = {"BAD": bad_df, "GOOD": good_df}

    with patch("cli.fetch_all", return_value=fake_data):
        with patch("sys.stdout", new_callable=StringIO) as fake_out:
            main()
            output = fake_out.getvalue()

    assert "BAD skipped:" not in output
    assert "BAD  Close:" in output
    assert "Trend:        INSUFFICIENT (ERROR)" in output
    assert "GOOD  Close:" in output


def test_key_levels_ath_and_recent_high_short_history():
    df = _make_hl_df([10, 11, 12, 13, 14], [8, 8, 9, 10, 11])
    result = key_levels(df)
    assert result["levels"]["ath"] == 14.0
    assert result["levels"]["recent_high_252d"] == 14.0
    assert result["recent_high_window_used"] == 5


def test_key_levels_distance_sign_and_safety():
    df = pd.DataFrame(
        {
            "High": [100.0, 120.0, 110.0],
            "Low": [90.0, 95.0, 92.0],
            "Close": [100.0, 101.0, 100.0],
        }
    )
    result = key_levels(df)
    assert result["distance_pct"]["ath"] < 0

    # Non-positive levels should produce None distance.
    df2 = pd.DataFrame({"High": [0.0, 0.0], "Low": [0.0, 0.0], "Close": [1.0, 1.0]})
    result2 = key_levels(df2)
    assert result2["distance_pct"]["ath"] is None


def test_key_levels_reuses_trend_structure_swings():
    highs = [100.0] * 30
    lows = [90.0] * 30
    highs[6] = 110.0
    highs[15] = 120.0
    highs[24] = 125.0
    lows[8] = 80.0
    lows[20] = 78.0
    df = _make_hl_df(highs, lows)
    ts = trend_structure(df)
    kl = key_levels(df)
    assert kl["levels"]["last_swing_high"] == ts["swing_highs"][-1]["price"]
    assert kl["levels"]["last_swing_low"] == ts["swing_lows"][-1]["price"]
    assert kl["levels"]["prior_significant_low"] == ts["swing_lows"][-2]["price"]
    assert kl["levels"]["prior_significant_low"] != kl["levels"]["last_swing_low"]
    assert kl["swing_source"] == "ok"
    assert kl["swing_error"] is None


def test_key_levels_missing_columns_raises():
    bad_df = pd.DataFrame({"Low": [1.0, 2.0], "Close": [1.0, 2.0]})
    try:
        key_levels(bad_df)
    except ValueError as exc:
        assert "High and Close" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_key_levels_marks_swing_unavailable_when_low_missing():
    df = pd.DataFrame({"High": [10.0, 12.0, 11.0], "Close": [9.0, 10.0, 9.5]})
    result = key_levels(df)
    assert result["swing_source"] == "unavailable"
    assert result["swing_error"] is not None
    assert result["levels"]["last_swing_high"] is None


def test_cli_prints_key_levels_block():
    good_df = _make_ohlcv_df(MIN_ROWS)
    fake_data = {"GOOD": good_df}
    with patch("cli.fetch_all", return_value=fake_data):
        with patch("sys.stdout", new_callable=StringIO) as fake_out:
            main()
            output = fake_out.getvalue()
    assert "Key levels:" in output
    assert "ATH" in output and "RHigh" in output and "PSLow" in output
