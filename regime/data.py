import yfinance as yf
import pandas as pd

TICKERS = ["SPY", "DIA", "QQQ"]
MIN_ROWS = 200
REQUIRED_COLUMNS = ["Open", "High", "Low", "Close"]

def fetch(ticker: str, period: str = "2y") -> pd.DataFrame:
    """Fetch daily OHLCV for a single ticker. Returns a clean DataFrame."""
    df = yf.Ticker(ticker).history(period=period)
    if df.empty:
        raise ValueError(f"No data returned for {ticker}. Check ticker symbol or connection.")
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing required columns for {ticker}: {', '.join(missing_cols)}."
        )
    df = df.dropna(subset=REQUIRED_COLUMNS)
    if df.empty:
        raise ValueError(
            f"All rows for {ticker} have missing OHLC values after cleaning."
        )
    if len(df) < MIN_ROWS:
        raise ValueError(f"Only {len(df)} rows for {ticker}. Need at least {MIN_ROWS}.")
    return df

def fetch_all(period: str = "2y") -> dict[str, pd.DataFrame]:
    """Fetch data for all tickers. Returns {"SPY": df, "DIA": df, "QQQ": df}."""
    return {t: fetch(t, period) for t in TICKERS}
