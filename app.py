"""Local Streamlit dashboard for technical-regime. Run: streamlit run app.py --server.address localhost"""

from __future__ import annotations

# Cache TTL for Yahoo fetch + regime build; sidebar Refresh bumps session token to bypass.
CACHE_TTL_SECONDS = 120

import pandas as pd
import streamlit as st

from regime.report import build_regime_report, normalize_tickers_csv

# Regime column: saturated fills + dark text for contrast (light Streamlit theme).
_REGIME_STYLES = {
    "BULLISH": "background-color: #34d399; color: #022c22; font-weight: 700",
    "BEARISH": "background-color: #fb7185; color: #450a0a; font-weight: 700",
    "NEUTRAL": "background-color: #fbbf24; color: #422006; font-weight: 700",
    "—": "background-color: #e5e7eb; color: #374151; font-weight: 500",
}

st.set_page_config(page_title="Technical Regime", layout="wide")
st.title("Technical Regime")

if "refresh_token" not in st.session_state:
    st.session_state.refresh_token = 0

with st.sidebar:
    mode = st.radio(
        "Universe",
        [
            "Global indexes",
            "US sectors",
            "Bonds / rates",
            "Futures",
            "Currencies",
            "Custom",
        ],
        index=0,
    )
    st.caption("Data from Yahoo Finance via yfinance.")
    st.caption(f"Cached ~{CACHE_TTL_SECONDS // 60} min. Use **Refresh data** to fetch again.")
    if st.button("Refresh data"):
        st.session_state.refresh_token += 1

use_sectors = mode == "US sectors"
use_bonds = mode == "Bonds / rates"
use_futures = mode == "Futures"
use_currencies = mode == "Currencies"
custom_tickers: list[str] | None = None
tickers_key = ""
if mode == "Custom":
    raw = st.text_input("Tickers (comma-separated)", value="AAPL, MSFT")
    custom_tickers = normalize_tickers_csv(raw)
    tickers_key = ",".join(custom_tickers)
    if not custom_tickers:
        st.error("Enter at least one ticker (comma-separated), e.g. AAPL,MSFT")
        st.stop()


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner="Loading market data…")
def load_report(
    use_sectors_flag: bool,
    use_bonds_flag: bool,
    use_futures_flag: bool,
    use_currencies_flag: bool,
    token: int,
    tickers_csv: str,
) -> dict:
    _ = token
    tickers = normalize_tickers_csv(tickers_csv) if tickers_csv else None
    return build_regime_report(
        use_sectors=use_sectors_flag,
        use_bonds=use_bonds_flag,
        use_futures=use_futures_flag,
        use_currencies=use_currencies_flag,
        tickers=tickers,
    )


report = load_report(
    use_sectors,
    use_bonds,
    use_futures,
    use_currencies,
    st.session_state.refresh_token,
    tickers_key,
)

for sym, msg in report["fetch_errors"].items():
    st.warning(f"{sym}: fetch skipped — {msg}")

if report["overall_fetched_count"] == 0:
    st.error("No ticker data available. Check your connection and try Refresh.")
    st.stop()

overall = report["overall"]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Overall regime", overall["label"])
c2.metric("Bullish", overall["counts"]["bullish"])
c3.metric("Neutral", overall["counts"]["neutral"])
c4.metric("Bearish", overall["counts"]["bearish"])
st.caption(f"Average net score: {overall['average_net_score']:+.2f}  ·  Tickers used: {overall['tickers_used']}")

_tickers = report["tickers"]


def _rows_for_region(region_name: str, ticker_order: list[str]) -> list[dict]:
    out = []
    for t in ticker_order:
        row = _tickers[t]
        if not row.get("ok"):
            out.append(
                {
                    "Region": region_name,
                    "Ticker": t,
                    "Name": row.get("display_name", ""),
                    "Close": None,
                    "Regime": "—",
                    "Net": None,
                    "Structure": "",
                    "MA chk": "",
                    "Trend chk": "",
                    "RHigh": "",
                    "PSLow": "",
                    "Note": row.get("error", "error"),
                }
            )
            continue
        rg = row["regime"]
        ck = rg["checks"]
        out.append(
            {
                "Region": region_name,
                "Ticker": t,
                "Name": row["display_name"],
                "Close": row["close"],
                "Regime": rg["label"],
                "Net": rg["net_score"],
                "Structure": f"{row['trend']['label']} ({row['trend']['reason']})",
                "MA chk": ck["ma"],
                "Trend chk": ck["trend"],
                "RHigh": ck["rhigh"],
                "PSLow": ck["pslow"],
                "Note": "",
            }
        )
    return out


for region_name, info in report["regions"].items():
    st.subheader(region_name)
    summ = info["summary"]
    st.caption(
        f"Region regime: **{summ['label']}**  ·  "
        f"bull {summ['counts']['bullish']} / neutral {summ['counts']['neutral']} / bear {summ['counts']['bearish']}  ·  "
        f"avg net {summ['average_net_score']:+.2f}"
    )
    rows = _rows_for_region(region_name, info["tickers"])
    df = pd.DataFrame(rows)

    def _style_regime_col(s: pd.Series) -> list[str]:
        return [
            _REGIME_STYLES.get(str(v).strip(), "background-color: #f3f4f6; color: #111827")
            for v in s
        ]

    def _style_net_col(s: pd.Series) -> list[str]:
        out: list[str] = []
        for v in s:
            if v is None or (isinstance(v, float) and pd.isna(v)):
                out.append("")
            elif isinstance(v, (int, float)) and v > 0:
                out.append("color: #047857; font-weight: 700")
            elif isinstance(v, (int, float)) and v < 0:
                out.append("color: #b91c1c; font-weight: 700")
            else:
                out.append("color: #92400e; font-weight: 600")
        return out

    styled = df.style.apply(_style_regime_col, subset=["Regime"]).apply(_style_net_col, subset=["Net"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

st.divider()
st.caption("Not financial advice — same checklist rules as the CLI.")
