"""Build a structured regime report (fetch + indicators). Used by CLI and Streamlit.

Return dict keys (stable contract):
  use_sectors: bool
  custom_tickers: list[str] | None
  fetch_errors: ticker -> message (fetch failed)
  tickers: ticker -> row dict with ok=True/False; if ok: display_name, close, ma, trend, levels, regime
  regions: region_name -> {summary, tickers (order), fetched_count}
  overall: market_regime() dict for full universe
  overall_fetched_count: int (rows fetched successfully, for partial-data hint)
"""

from __future__ import annotations

from regime import data
from regime.indicators import key_levels, market_regime, moving_averages, ticker_regime, trend_structure

TICKER_NAMES = {
    "^VIX": "CBOE Volatility Index",
    "^GSPTSE": "S&P/TSX Composite",
    "^BVSP": "Bovespa Index",
    "DX-Y.NYB": "U.S. Dollar Index",
    "^RUT": "Russell 2000",
    "^GSPC": "S&P 500",
    "^DJI": "Dow Jones",
    "^IXIC": "Nasdaq Composite",
    "^FTSE": "FTSE 100",
    "^XDE": "Euro Currency Index",
    "^XDB": "British Pound Index",
    "^FCHI": "CAC 40",
    "^N100": "Euronext 100",
    "^STOXX50E": "EURO STOXX 50",
    "^125904-USD-STRD": "MSCI Europe",
    "^GDAXI": "DAX",
    "000001.SS": "SSE Composite",
    "^HSI": "Hang Seng",
    "^XDA": "Australian Dollar Index",
    "^AXJO": "S&P/ASX 200",
    "^XDN": "Japanese Yen Index",
    "^KS11": "KOSPI",
    "^N225": "Nikkei 225",
    "^BSESN": "S&P BSE Sensex",
}

SECTOR_NAMES = {
    "XLE": "Energy",
    "XLU": "Utilities",
    "XLRE": "Real Estate",
    "XLP": "Consumer Staples",
    "XLF": "Financials",
    "XLB": "Materials",
    "XLY": "Consumer Discretionary",
    "XLI": "Industrials",
    "XLC": "Communication Services",
    "XLK": "Technology",
}


def _display_name(ticker: str, use_sectors: bool) -> str:
    if use_sectors:
        return SECTOR_NAMES.get(ticker, ticker)
    return TICKER_NAMES.get(ticker, ticker)

def normalize_tickers_csv(csv: str) -> list[str]:
    """Parse a comma-separated ticker string into a normalized list.

    Rules:
    - Split on commas
    - Trim whitespace
    - Drop empty entries
    - De-duplicate while preserving first-seen order

    We intentionally do NOT over-validate formats; Yahoo tickers can include
    symbols like '^', '.', '-' (e.g. '^GSPC', '000001.SS', 'BRK-B').
    """
    if csv is None:
        return []
    parts = [p.strip() for p in str(csv).split(",")]
    seen: set[str] = set()
    out: list[str] = []
    for p in parts:
        if not p:
            continue
        if p in seen:
            continue
        seen.add(p)
        out.append(p)
    return out


def build_regime_report(use_sectors: bool = False, tickers: list[str] | None = None) -> dict:
    custom_tickers = None if not tickers else list(tickers)
    if custom_tickers:
        tickers_list = custom_tickers
        use_sectors = False
    else:
        tickers_list = data.SECTOR_TICKERS if use_sectors else data.TICKERS
    raw, fetch_errors = data.fetch_all(tickers_list)

    tickers: dict = {}
    for ticker, df in raw.items():
        try:
            ma_result = moving_averages(df)
        except ValueError as exc:
            tickers[ticker] = {"ok": False, "error": str(exc)}
            continue
        trend_result = trend_structure(df)
        levels_result = key_levels(df, trend_result=trend_result)
        regime = ticker_regime(ma_result, trend_result, levels_result)
        tickers[ticker] = {
            "ok": True,
            "display_name": _display_name(ticker, use_sectors),
            "close": float(ma_result["price"]),
            "ma": ma_result,
            "trend": trend_result,
            "levels": levels_result,
            "regime": regime,
        }

    regions: dict = {}
    if custom_tickers:
        order = [t for t in custom_tickers if t in raw]
        regs = {
            t: tickers[t]["regime"]
            for t in order
            if t in tickers and tickers[t].get("ok")
        }
        regions["Custom"] = {
            "summary": market_regime(regs),
            "tickers": order,
            "fetched_count": len(order),
        }
        overall = market_regime(regs)
        overall_fetched = len(raw)
    elif use_sectors:
        order = [t for t in data.SECTOR_TICKERS if t in raw]
        regs = {
            t: tickers[t]["regime"]
            for t in order
            if t in tickers and tickers[t].get("ok")
        }
        regions["Sectors"] = {
            "summary": market_regime(regs),
            "tickers": order,
            "fetched_count": len(order),
        }
        overall = market_regime(regs)
        overall_fetched = len(raw)
    else:
        for region_name, rtickers in data.REGIONS.items():
            order = [t for t in rtickers if t in raw]
            if not order:
                continue
            region_regs = {
                t: tickers[t]["regime"]
                for t in order
                if t in tickers and tickers[t].get("ok")
            }
            regions[region_name] = {
                "summary": market_regime(region_regs),
                "tickers": order,
                "fetched_count": len(order),
            }
        overall = market_regime(
            {t: tickers[t]["regime"] for t in tickers if tickers[t].get("ok")}
        )
        overall_fetched = len(raw)

    return {
        "use_sectors": use_sectors,
        "custom_tickers": custom_tickers,
        "fetch_errors": fetch_errors,
        "tickers": tickers,
        "regions": regions,
        "overall": overall,
        "overall_fetched_count": overall_fetched,
    }
