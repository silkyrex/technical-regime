"""Build a structured regime report (fetch + indicators). Used by CLI and Streamlit.

Return dict keys (stable contract):
  use_sectors: bool
  use_bonds: bool
  use_futures: bool
  use_currencies: bool
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
    "^TNX": "US 10Y Treasury yield",
    "^IRX": "US 13-Week T-Bill yield",
    "^FVX": "US 5Y Treasury yield",
    "^TYX": "US 30Y Treasury yield",
    "ZT=F": "2Y T-Note futures",
    "ZN=F": "10Y T-Note futures",
    "SI=F": "Silver futures",
    "CL=F": "Crude oil futures",
    "ES=F": "E-mini S&P 500 futures",
    "YM=F": "Mini Dow futures",
    "NQ=F": "Nasdaq 100 futures",
    "RTY=F": "E-mini Russell 2000 futures",
    "ZB=F": "US Treasury bond futures",
    "ZF=F": "5Y T-Note futures",
    "GC=F": "Gold futures",
    "MGC=F": "Micro gold futures",
    "SIL=F": "Micro silver futures",
    "PL=F": "Platinum futures",
    "HG=F": "Copper futures",
    "PA=F": "Palladium futures",
    "HO=F": "Heating oil futures",
    "NG=F": "Natural gas futures",
    "RB=F": "RBOB gasoline futures",
    "BZ=F": "Brent crude futures",
    "B0=F": "Mont Belvieu propane futures",
    "ZC=F": "Corn futures",
    "ZO=F": "Oat futures",
    "KE=F": "KC HRW wheat futures",
    "ZR=F": "Rough rice futures",
    "ZM=F": "Soybean meal futures",
    "ZL=F": "Soybean oil futures",
    "ZS=F": "Soybean futures",
    "GF=F": "Feeder cattle futures",
    "HE=F": "Lean hog futures",
    "LE=F": "Live cattle futures",
    "CC=F": "Cocoa futures",
    "KC=F": "Coffee futures",
    "CT=F": "Cotton futures",
    "LBS=F": "Lumber futures",
    "OJ=F": "Orange juice futures",
    "SB=F": "Sugar #11 futures",
    "EURUSD=X": "EUR/USD",
    "USDJPY=X": "USD/JPY",
    "GBPUSD=X": "GBP/USD",
    "AUDUSD=X": "AUD/USD",
    "NZDUSD=X": "NZD/USD",
    "EURJPY=X": "EUR/JPY",
    "GBPJPY=X": "GBP/JPY",
    "EURGBP=X": "EUR/GBP",
    "EURCAD=X": "EUR/CAD",
    "EURSEK=X": "EUR/SEK",
    "EURCHF=X": "EUR/CHF",
    "EURHUF=X": "EUR/HUF",
    "USDCNY=X": "USD/CNY",
    "USDHKD=X": "USD/HKD",
    "USDSGD=X": "USD/SGD",
    "USDINR=X": "USD/INR",
    "USDMXN=X": "USD/MXN",
    "USDPHP=X": "USD/PHP",
    "USDIDR=X": "USD/IDR",
    "USDTHB=X": "USD/THB",
    "USDMYR=X": "USD/MYR",
    "USDZAR=X": "USD/ZAR",
    "USDRUB=X": "USD/RUB",
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


def _display_name(ticker: str, is_sectors: bool) -> str:
    if is_sectors:
        return SECTOR_NAMES.get(ticker, ticker)
    return TICKER_NAMES.get(ticker, ticker)


def normalize_tickers_csv(csv: str) -> list[str]:
    """Parse a comma-separated ticker string into a normalized list.

    Rules: split on commas, trim, drop empty, de-dupe preserving order.
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


def _single_region_block(
    tickers: dict, raw: dict, order_source: list[str], region_label: str
) -> tuple[dict, dict, int]:
    order = [t for t in order_source if t in raw]
    regs = {t: tickers[t]["regime"] for t in order if t in tickers and tickers[t].get("ok")}
    summary = market_regime(regs)
    regions = {
        region_label: {
            "summary": summary,
            "tickers": order,
            "fetched_count": len(order),
        }
    }
    return regions, summary, len(raw)


def build_regime_report(
    use_sectors: bool = False,
    use_bonds: bool = False,
    use_futures: bool = False,
    use_currencies: bool = False,
    tickers: list[str] | None = None,
) -> dict:
    custom_tickers = None if not tickers else list(tickers)
    if custom_tickers:
        tickers_list = custom_tickers
        use_sectors = use_bonds = use_futures = use_currencies = False
    elif use_sectors:
        tickers_list = data.SECTOR_TICKERS
    elif use_bonds:
        tickers_list = data.BOND_TICKERS
    elif use_futures:
        tickers_list = data.FUTURES_TICKERS
    elif use_currencies:
        tickers_list = data.CURRENCY_TICKERS
    else:
        tickers_list = data.TICKERS
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
            "display_name": _display_name(ticker, is_sectors=use_sectors),
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
        regions, overall, overall_fetched = _single_region_block(
            tickers, raw, data.SECTOR_TICKERS, "Sectors"
        )
    elif use_bonds:
        regions, overall, overall_fetched = _single_region_block(
            tickers, raw, data.BOND_TICKERS, "Bonds"
        )
    elif use_futures:
        regions, overall, overall_fetched = _single_region_block(
            tickers, raw, data.FUTURES_TICKERS, "Futures"
        )
    elif use_currencies:
        regions, overall, overall_fetched = _single_region_block(
            tickers, raw, data.CURRENCY_TICKERS, "Currencies"
        )
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
        "use_bonds": use_bonds,
        "use_futures": use_futures,
        "use_currencies": use_currencies,
        "custom_tickers": custom_tickers,
        "fetch_errors": fetch_errors,
        "tickers": tickers,
        "regions": regions,
        "overall": overall,
        "overall_fetched_count": overall_fetched,
    }
