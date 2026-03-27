# Technical Regime (Beginner-Friendly)

A simple market "health check" for `SPY`, `DIA`, and `QQQ`.

This project does **not** try to predict the future.  
It gives you a clean checklist so you can see if market conditions look healthy, weak, or mixed.

---

## Simple Analogy: Market Weather + Doctor Checkup

Think of this tool like two things at once:

- **Weather check** before leaving the house
- **Doctor checkup** for market health

### 1) Price vs Moving Averages = Temperature check

- Is price above or below key moving averages?
- Above = warmer/healthier
- Below = colder/weaker

### 2) MA slope = Warming up or cooling down

- Is each moving average rising or falling?
- Rising = trend gaining strength
- Falling = trend losing strength

### 3) Trend structure (swings) = Staircase direction

- Are highs and lows getting higher? -> stairs up
- Are highs and lows getting lower? -> stairs down
- Mixed pattern? -> choppy/noisy market

---

## What We Have Built So Far (Phases 1 to 4)

## Phase 1: Data Foundation

- Pulls daily OHLCV data using `yfinance`
- Tickers: `SPY`, `DIA`, `QQQ`
- Validates minimum history for long moving averages

Files:
- `regime/data.py`

## Phase 2: Moving Averages + Price Position

- Computes SMA: `10, 20, 50, 100, 200`
- Checks if current price is above/below each MA
- Counts bullish/bearish MA positions

## Phase 3: MA Slope

- Compares MA today vs MA 5 trading days ago
- Marks each MA as `RISING` or `FALLING`
- Counts rising/falling MA slopes

## Phase 4: Trend Structure (Swing Logic)

- Finds confirmed swing highs/lows using `High` and `Low`
- Uses strict rule for ties (flat tops/bottoms are ignored)
- Labels structure:
  - `UPTREND` (`HH/HL`)
  - `DOWNTREND` (`LH/LL`)
  - `MIXED` (`HH/LL`, `HL/LH`, etc.)
  - `INSUFFICIENT` (not enough swing evidence yet)

Files:
- `regime/indicators.py`
- `cli.py`
- `test_indicators.py`

---

## CLI Output: How to Read It

For each ticker, the CLI prints:

1. Current close
2. Each moving average line with:
   - MA value
   - `ABOVE` or `BELOW`
   - `RISING` or `FALLING`
   - percent distance from MA
3. Summary counts:
   - `Price vs MA: +x/-y`
   - `MA slope: +x/-y`
4. Trend structure:
   - `Trend: UPTREND (HH/HL)` (or other label/reason)

## Example Output (with plain-English meaning)

```text
SPY  Close: 612.34
   10-day MA:   608.10  ABOVE  RISING  (+0.7%)
   20-day MA:   603.55  ABOVE  RISING  (+1.5%)
   50-day MA:   590.20  ABOVE  RISING  (+3.7%)
  100-day MA:   575.90  ABOVE  RISING  (+6.3%)
  200-day MA:   548.40  ABOVE  RISING  (+11.7%)
  Price vs MA:  +5/-0
  MA slope:     +5/-0
  Trend:        UPTREND (HH/HL)
```

How to read this quickly:

- `Close: 612.34` -> current price right now
- Each MA line -> where price is vs that timeframe trend
- `ABOVE` + `RISING` together -> strongest bullish combo
- `Price vs MA: +5/-0` -> above all 5 MAs
- `MA slope: +5/-0` -> all 5 trends are rising
- `Trend: UPTREND (HH/HL)` -> staircase still going up (higher highs + higher lows)

Fast 10-second scan rule:

1. Check `Price vs MA`
2. Check `MA slope`
3. Check `Trend`
4. If all 3 agree bullish or bearish, signal is clean. If not, treat as mixed/choppy.

Bearish comparison example:

```text
QQQ  Close: 438.22
   10-day MA:   442.10  BELOW  FALLING  (-0.9%)
   20-day MA:   448.35  BELOW  FALLING  (-2.3%)
   50-day MA:   459.80  BELOW  FALLING  (-4.7%)
  100-day MA:   471.20  BELOW  FALLING  (-7.0%)
  200-day MA:   489.60  BELOW  FALLING  (-10.5%)
  Price vs MA:  +0/-5
  MA slope:     +0/-5
  Trend:        DOWNTREND (LH/LL)
```

What this means in baby terms:

- Price is below all major trend lines
- Those trend lines are still sloping down
- Market structure is making lower highs + lower lows
- This is a clean bearish alignment (the opposite of the bullish example)

### Baby tip

If you see:
- Price mostly above MAs
- Slopes mostly rising
- Trend is `UPTREND`

...that is a strong "healthy" read.

If signals disagree, that is normal. Mixed markets happen often.

---

## Quick Start

## 1) Install dependencies

```bash
pip install -r requirements.txt
```

## 2) Run the CLI

```bash
python cli.py
```

## 3) Run tests

```bash
python -m pytest -q
```

---

## Project Structure

```text
technical-regime/
  cli.py
  requirements.txt
  regime/
    data.py
    indicators.py
  test_indicators.py
```

---

## Important Notes

- This is a checklist tool, not financial advice.
- It is designed for clarity first, complexity later.
- We are intentionally building in phases so each step is testable and easy to understand.

---

## Next Phases (Planned)

- **Phase 5:** Key levels (ATH, recent highs/lows, proximity)
- **Phase 6:** Aggregate all checks into a market-wide regime summary

---

## One-Line Summary

This project is your market "dashboard light system":  
**green-ish when many checks agree bullish, red-ish when many checks agree bearish, yellow when signals conflict.**
