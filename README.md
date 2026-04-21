# Technical Regime

Know the regime before you trade.

Scores 24 global indexes, 10 sector ETFs, bonds, futures, and FX on 4 signals: MA position, MA slope, trend structure, and distance from key levels. Output: BULLISH / BEARISH / NEUTRAL per ticker, every morning in under 5 seconds.

## Quick start

```bash
./scripts/init.sh
source .venv/bin/activate
python3 cli.py
```

For a web view: `streamlit run app.py`

## CLI flags

| Command | Universe |
|---------|----------|
| `python3 cli.py` | 24 global indexes (default) |
| `python3 cli.py --sectors` | 10 US sector ETFs |
| `python3 cli.py --bonds` | Treasury yields + futures |
| `python3 cli.py --futures` | Commodity + equity-index futures |
| `python3 cli.py --currencies` | 23 FX pairs |
| `python3 cli.py --tickers AAPL,MSFT` | Custom tickers |

## Output format

Each ticker shows 4 lines: MA position/slope, key levels, trend structure, and an overall regime verdict (BULLISH / BEARISH / NEUTRAL).

## Regime scoring

4 checks per ticker: MA position+slope, trend structure (HH/HL vs LH/LL), distance from 252-day high, distance above prior swing low.

- Net ≥ +2 → **BULLISH**
- Net ≤ −2 → **BEARISH**
- Otherwise → **NEUTRAL**

## Project structure

```
cli.py               # terminal report
app.py               # Streamlit web UI
regime/
  data.py            # Yahoo Finance fetch
  indicators.py      # MA, trend, levels, regime scoring
  report.py          # shared report builder
test_indicators.py   # tests
```

## Status

Personal trading tool. Active project.
