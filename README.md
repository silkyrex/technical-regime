# Technical Regime (Beginner-Friendly)

A simple market "health check" for major indexes, macro signals, and US sectors.

This project does **not** try to predict the future.
It gives you a clean checklist so you can see if market conditions look healthy, weak, or mixed.

---

## Begin Here (Complete Beginner Guide)

Welcome! If this is your first time opening this project, follow these steps in order.

### Step 1: Open your terminal

- On Mac: press `Cmd + Space`, type `Terminal`, hit Enter
- You should see a blinking cursor — this is where you type commands

### Step 2: Go to the project folder

```bash
cd ~/technical-regime
```

This moves you into the project directory. Think of it like opening a folder on your desktop.

### Step 3: Install what the project needs

```bash
pip install -r requirements.txt
```

This downloads two things the project depends on: `yfinance` (gets stock data) and `pandas` (organizes data into tables). You only need to do this once.

If `pip` doesn't work, try `pip3` instead.

### Step 4: Run it

```bash
python cli.py
```

(Or `python3 cli.py` if `python` doesn't work.)

That's it. You'll see a market health report for all index tickers. It takes a few seconds because it's downloading live market data.

To run **sector analysis** instead (comparing sectors against each other):

```bash
python cli.py --sectors
```

### Step 5: Read the output

The output shows you three things per ticker:

1. **Price vs MAs** — Is the price above or below the major trend lines?
2. **MA slope** — Are those trend lines going up or down?
3. **Trend** — Is the market making higher highs (stairs up) or lower lows (stairs down)?

Then at the bottom, you'll see the **Regime** label (BULLISH / BEARISH / NEUTRAL) and a **Market Summary** across all tickers.

### Step 6: Run tests (optional, for learning)

```bash
python -m pytest -q
```

This runs all the automated checks to make sure the code is working correctly. If you see all tests pass, everything is good.

### What the tickers mean

**Indexes & Macro** (`python cli.py`):

| Ticker | What it tracks |
|--------|---------------|
| SPY | S&P 500 (large US companies) |
| DIA | Dow Jones Industrial Average (30 blue-chip stocks) |
| QQQ | Nasdaq 100 (tech-heavy) |
| IWM | Russell 2000 (small US companies) |
| TLT | 20+ Year Treasury Bonds (safe haven / interest rate signal) |
| GLD | Gold (inflation hedge / fear signal) |
| SMH | Semiconductors (tech cycle leader) |
| DX-Y.NYB | US Dollar Index (dollar strength — strong dollar can pressure stocks) |
| ^TNX | 10-Year Treasury Yield (rising = higher rates, falling = flight to safety) |

**US Sectors** (`python cli.py --sectors`):

| Ticker | Sector |
|--------|--------|
| XLK | Technology |
| XLF | Financials |
| XLE | Energy |
| XLY | Consumer Discretionary |
| XLI | Industrials |
| XLC | Communication Services |
| XLP | Consumer Staples |
| XLU | Utilities |
| XLRE | Real Estate |
| XLB | Materials |

### What to do with the output

- **All tickers BULLISH** — Market looks broadly healthy
- **All tickers BEARISH** — Market looks broadly weak
- **Mixed** — Normal. Different parts of the market don't always agree. Read the "How to Interpret Regime Conflict" section below for help.

### If something goes wrong

- **"No module named 'yfinance'"** — Run `pip install -r requirements.txt` again
- **"No data returned for X"** — Your internet might be down, or the market data service is temporarily unavailable. Try again in a minute.
- **A ticker says "skipped"** — That ticker failed to fetch data. The rest still work. Check your internet connection.

### Vocabulary cheat sheet

| Term | Plain English |
|------|--------------|
| MA (Moving Average) | Average price over the last X days. Smooths out noise. |
| SMA | Simple Moving Average — just a plain average, nothing fancy |
| Bullish | Things look like they're going up |
| Bearish | Things look like they're going down |
| OHLCV | Open, High, Low, Close, Volume — the 5 data points for each trading day |
| Swing high/low | A local peak or valley in price — like the top or bottom of a hill |
| HH/HL | Higher High / Higher Low — stairs going up |
| LH/LL | Lower High / Lower Low — stairs going down |
| ATH | All-Time High — the highest price ever recorded |
| Regime | The overall "mood" of the market based on all checks combined |

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

## What We Have Built So Far (Phases 1 to 6)

## Phase 1: Data Foundation

- Pulls daily OHLCV data using `yfinance`
- Index tickers: `SPY`, `DIA`, `QQQ`, `IWM`, `TLT`, `GLD`, `SMH`, `DX-Y.NYB`, `^TNX`
- Sector tickers: `XLE`, `XLU`, `XLRE`, `XLP`, `XLF`, `XLB`, `XLY`, `XLI`, `XLC`, `XLK`
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

## Phase 5: Key Levels

- Computes All-Time High (ATH) and 252-day recent high
- Pulls last swing high, last swing low, and prior significant low from trend structure
- Calculates percent distance from current price to each level
- Reuses trend structure output to avoid redundant computation

## Phase 6: Regime Aggregation

- 4 checks per ticker: MA cluster, Trend, Recent High distance, Prior Significant Low distance
- MA cluster combines position + slope into one signal (both must agree to count)
- Contradiction guard: if MA cluster and Trend disagree, ticker is forced NEUTRAL
- Ticker labels: BULLISH (net >= +2), BEARISH (net <= -2), NEUTRAL (otherwise)
- Market-wide regime: majority vote across all tickers
- Resilient fetching: if a ticker fails to download, the rest still run

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

## How to Interpret Regime Conflict

A "regime conflict" is when the three checks disagree with each other. This is common and does not mean something is broken — it just means the market is sending mixed signals.

### What conflict looks like

```text
SPY  Close: 561.10
   10-day MA:   548.20  ABOVE  RISING  (+2.3%)
   20-day MA:   553.80  ABOVE  RISING  (+1.3%)
   50-day MA:   558.40  ABOVE  FALLING (-0.4%)
  100-day MA:   545.90  ABOVE  FALLING (+2.8%)
  200-day MA:   530.10  ABOVE  FALLING (+5.8%)
  Price vs MA:  +5/-0
  MA slope:     +2/-3
  Trend:        MIXED (HH/LL)
```

Price is above all MAs (bullish), but most slopes are falling and trend structure is mixed. Three checks, three different answers.

### How to read conflict

| What you see | What it likely means |
|---|---|
| Price above MAs, but slopes falling | Rally is losing momentum — trend lines starting to roll over |
| Price below MAs, but slopes rising | Possible early recovery — but not confirmed yet |
| Uptrend structure, but price below MAs | Structure still intact from prior move, price pulling back inside it |
| Downtrend structure, but price above short MAs | Short-term bounce inside a longer downtrend |
| All three agree bullish | Clean bull regime — least conflicted |
| All three agree bearish | Clean bear regime — least conflicted |

### The golden rule for conflict

**Count the agreements, not just the disagreements.**

- 3/3 agree = clean signal, act with more confidence
- 2/3 agree = leaning one way, but treat as cautious
- 1/3 agree = no clear regime, reduce conviction

### Common conflict patterns

**"Rising price, falling slopes"** — Price climbed fast but MAs have not caught up yet, or the move is stalling. Watch if slopes start rising again or price pulls back to MAs.

**"Mixed trend, clean MAs"** — Swing structure is choppy but MAs are still aligned. Often happens after a sharp move that breaks the prior swing pattern. MAs tend to be more stable here.

**"INSUFFICIENT trend"** — Not enough confirmed swings yet. This happens on new data, low-volatility stretches, or right after a sharp reversal. Not a bearish signal on its own — just not enough evidence yet.

### Baby tip for conflict

When in doubt, give more weight to the **longer timeframe signals**:
- 200-day MA position > 10-day MA position
- Trend structure > short-term slope direction

Short-term signals flip often. Longer signals change slowly and carry more weight.

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

## What's Next (Ideas)

- Colorized terminal output (green/red/yellow)
- Historical regime tracking (save daily snapshots)
- Multi-timeframe analysis (weekly + daily)
- Sector rotation signals
- Export to CSV or dashboard

---

## One-Line Summary

This project is your market "dashboard light system":
**green when many checks agree bullish, red when many checks agree bearish, yellow when signals conflict.**
