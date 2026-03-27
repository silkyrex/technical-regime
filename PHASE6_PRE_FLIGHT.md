# Phase 6 Pre-Flight (Regime Aggregation)

## Constraint
Turn existing per-ticker outputs into a simple checklist regime, then combine SPY/DIA/QQQ into one market regime with clear breakdown.

## Rule Set (Beginner-Safe)
- Use 4 checks per ticker: `MA cluster`, `Trend`, `RHigh`, `PSLow`.
- MA cluster combines MA position and MA slope so we do not count the same idea twice.
- Missing distances (`None`) count as neutral.
- Contradiction guard: if MA cluster and Trend disagree, force ticker `NEUTRAL`.

## Ticker Labels
- `BULLISH` if net score (`bullish - bearish`) >= 2
- `BEARISH` if net score <= -2
- `NEUTRAL` otherwise

## Market Label
- Majority vote from ticker labels.
- Include `tickers_used` and counts for transparency.

## CLI Output
- Per ticker:
  - `Regime: ...`
  - `Checklist: +X / -Y (net Z)`
  - check line in fixed order: `MA`, `Trend`, `RHigh`, `PSLow`
- End summary:
  - `Market regime: ...`
  - `Tickers used: N`
  - `Tickers: bullish=A neutral=B bearish=C`

## Minimal Tests
1. Bullish ticker case
2. Bearish ticker case
3. Contradiction -> forced neutral
4. Missing-level neutrality
5. Market majority vote + `tickers_used`
6. CLI summary line presence

## Out of Scope
- Weights/optimization
- Backtest-calibrated thresholds
- Probabilities/confidence %
- Multi-timeframe aggregation
- Colorized output
