from __future__ import annotations

import yfinance as yf
import pandas as pd

AMERICAS_TICKERS = ["^VIX", "^GSPTSE", "^BVSP", "DX-Y.NYB", "^RUT", "^GSPC", "^DJI", "^IXIC"]
EUROPE_TICKERS   = ["^FTSE", "^XDE", "^XDB", "^FCHI", "^N100", "^STOXX50E", "^125904-USD-STRD", "^GDAXI"]
ASIA_TICKERS     = ["000001.SS", "^HSI", "^XDA", "^AXJO", "^XDN", "^KS11", "^N225", "^BSESN"]

REGIONS = {
    "Americas": AMERICAS_TICKERS,
    "Europe":   EUROPE_TICKERS,
    "Asia":     ASIA_TICKERS,
}

TICKERS = AMERICAS_TICKERS + EUROPE_TICKERS + ASIA_TICKERS
SECTOR_TICKERS = ["XLE", "XLU", "XLRE", "XLP", "XLF", "XLB", "XLY", "XLI", "XLC", "XLK"]

BOND_TICKERS = ["^TNX", "ZT=F", "ZN=F", "^IRX", "^FVX", "^TYX"]

FUTURES_TICKERS = [
    "SI=F", "CL=F", "ES=F", "YM=F", "NQ=F", "RTY=F", "ZB=F", "ZN=F", "ZF=F", "ZT=F", "GC=F", "MGC=F",
    "SIL=F", "PL=F", "HG=F", "PA=F", "HO=F", "NG=F", "RB=F", "BZ=F", "B0=F", "ZC=F", "ZO=F", "KE=F", "ZR=F",
    "ZM=F", "ZL=F", "ZS=F", "GF=F", "HE=F", "LE=F", "CC=F", "KC=F", "CT=F", "LBS=F", "OJ=F", "SB=F",
]

CURRENCY_TICKERS = [
    "EURUSD=X", "USDJPY=X", "GBPUSD=X", "AUDUSD=X", "NZDUSD=X", "EURJPY=X", "GBPJPY=X", "EURGBP=X",
    "EURCAD=X", "EURSEK=X", "EURCHF=X", "EURHUF=X", "USDCNY=X", "USDHKD=X", "USDSGD=X", "USDINR=X",
    "USDMXN=X", "USDPHP=X", "USDIDR=X", "USDTHB=X", "USDMYR=X", "USDZAR=X", "USDRUB=X",
]

MIN_ROWS = 200
REQUIRED_COLUMNS = ["Open", "High", "Low", "Close"]

def fetch(ticker: str, period: str = "2y", min_rows: int = MIN_ROWS) -> pd.DataFrame:
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
    if len(df) < min_rows:
        raise ValueError(f"Only {len(df)} rows for {ticker}. Need at least {min_rows}.")
    return df

def fetch_all(
    tickers: list[str] | None = None, period: str = "2y", min_rows: int = MIN_ROWS
) -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    """Fetch data for given tickers (defaults to TICKERS). Returns (data, errors) dicts."""
    if tickers is None:
        tickers = TICKERS
    results = {}
    errors = {}
    for t in tickers:
        try:
            results[t] = fetch(t, period, min_rows=min_rows)
        except ValueError as exc:
            errors[t] = str(exc)
    return results, errors
