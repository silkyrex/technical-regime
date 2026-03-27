# Technical Regime (Beginner-Friendly)

A global market regime checklist covering 24 indexes and currency indexes across Americas, Europe, and Asia — plus 10 US sectors.

This project does **not** try to predict the future.
It gives you a clean, objective checklist so you can see whether market conditions look healthy, weak, or mixed — across the world, not just the US.

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
python3 cli.py
```

That's it. You'll see a global market health report grouped by region. It takes a few seconds because it's downloading live market data.

To run **US sector analysis** instead:

```bash
python3 cli.py --sectors
```

### Step 5: Read the output

For each ticker you'll see 5 lines:

1. **Ticker + Close price** — what it is and where it's trading
2. **MA line** — is price above or below each moving average, and is each MA rising (↑) or falling (↓)?
3. **Levels line** — how far price is from key reference points (ATH, recent high, swing highs/lows)
4. **Trend line** — is the market making higher highs (stairs up) or lower lows (stairs down)?
5. **Regime line** — the overall verdict (BULLISH / BEARISH / NEUTRAL) and what drove it

Then at the end of each region you'll see a **Summary** listing every ticker's verdict, plus overall counts and average score.

### Step 6: Run tests (optional, for learning)

```bash
python3 -m pytest -q
```

This runs all the automated checks to make sure the code is working correctly. If you see all tests pass, everything is good.

### What the tickers mean

**Americas** (`python3 cli.py`):

| Ticker | What it tracks |
|--------|---------------|
| ^VIX | CBOE Volatility Index — fear gauge |
| ^GSPTSE | S&P/TSX Composite — Canadian market |
| ^BVSP | Bovespa — Brazilian market |
| DX-Y.NYB | US Dollar Index — dollar strength |
| ^RUT | Russell 2000 — small US companies |
| ^GSPC | S&P 500 — large US companies |
| ^DJI | Dow Jones — 30 blue-chip US stocks |
| ^IXIC | Nasdaq Composite — tech-heavy US market |

**Europe** (`python3 cli.py`):

| Ticker | What it tracks |
|--------|---------------|
| ^FTSE | FTSE 100 — UK market |
| ^XDE | Euro Currency Index |
| ^XDB | British Pound Index |
| ^FCHI | CAC 40 — French market |
| ^N100 | Euronext 100 — broad European market |
| ^STOXX50E | EURO STOXX 50 — eurozone blue chips |
| ^125904-USD-STRD | MSCI Europe — broad European equities |
| ^GDAXI | DAX — German market |

**Asia** (`python3 cli.py`):

| Ticker | What it tracks |
|--------|---------------|
| 000001.SS | SSE Composite — Shanghai / Chinese market |
| ^HSI | Hang Seng — Hong Kong market |
| ^XDA | Australian Dollar Index |
| ^AXJO | S&P/ASX 200 — Australian market |
| ^XDN | Japanese Yen Index |
| ^KS11 | KOSPI — South Korean market |
| ^N225 | Nikkei 225 — Japanese market |
| ^BSESN | S&P BSE Sensex — Indian market |

**US Sectors** (`python3 cli.py --sectors`):

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

- **All tickers BULLISH** — Market looks broadly healthy globally
- **All tickers BEARISH** — Market looks broadly weak globally
- **Mixed** — Normal. Different regions and markets don't always agree.

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
| RHigh | Recent high — highest price in the last 252 trading days (~1 year) |
| SHigh / SLow | Last confirmed swing high / swing low |
| PSLow | Prior significant low — the swing low before the most recent one |
| Regime | The overall "mood" of the market based on all checks combined |
| ↑ | Rising — the MA is sloping upward |
| ↓ | Falling — the MA is sloping downward |

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
- Rising (↑) = trend gaining strength
- Falling (↓) = trend losing strength

### 3) Trend structure (swings) = Staircase direction

- Are highs and lows getting higher? → stairs up (UPTREND)
- Are highs and lows getting lower? → stairs down (DOWNTREND)
- Mixed pattern? → choppy/noisy market

### 4) Key levels = How far from important price points

- Close to ATH or recent high = bullish
- Far below recent high = bearish
- Well above prior swing low = healthy
- At or below prior swing low = warning sign

---

## How the Regime Score Works

Each ticker gets **4 checks**, each scored bullish, neutral, or bearish:

| Check | What it measures | Bullish condition | Bearish condition |
|-------|-----------------|-------------------|-------------------|
| MA | Position + slope combined | Price above 4+ MAs AND 4+ MAs rising | Price below 4+ MAs AND 4+ MAs falling |
| Trend | Swing structure | UPTREND (HH/HL) | DOWNTREND (LH/LL) |
| RHigh | Distance from 252-day high | Within 2% of recent high | More than 8% below recent high |
| PSLow | Distance above prior swing low | More than 3% above | At or below prior low |

**Net score** = bullish checks − bearish checks

- Net ≥ +2 → **BULLISH**
- Net ≤ −2 → **BEARISH**
- Otherwise → **NEUTRAL**

**Contradiction guard:** if MA and Trend directly contradict each other, the ticker is forced NEUTRAL regardless of score.

---

## Example Output

```text
^GSPC  (S&P 500)  Close: 6418.37
  MA:      10d BELOW↓  20d BELOW↓  50d BELOW↓  100d BELOW↓  200d BELOW↑  (+0/-5 pos, +1/-4 slope)
  Levels:  ATH -8.3%  RHigh -8.3%  SHigh -8.2%  SLow -5.3%  PSLow -5.3%
  Trend:   DOWNTREND (LH/LL)
  Regime:  BEARISH  +0/-4 (net -4)  MA=bearish  Trend=bearish  RHigh=bearish  PSLow=bearish
```

How to read this:

- `10d BELOW↓` → price is below the 10-day MA, and that MA is falling — double bearish
- `200d BELOW↑` → price is below the 200-day MA, but at least that MA is still rising — mixed
- `+0/-5 pos` → below all 5 moving averages
- `+1/-4 slope` → 4 of 5 MAs are falling
- `ATH -8.3%` → price is 8.3% below its all-time high
- `PSLow -5.3%` → price has already broken below the prior significant swing low — bearish signal
- `Regime: BEARISH` → all 4 checks agree bearish, net score −4

```text
^BVSP  (Bovespa Index)  Close: 182803.27
  MA:      10d ABOVE↑  20d ABOVE↓  50d ABOVE↑  100d ABOVE↑  200d ABOVE↑  (+5/-0 pos, +4/-1 slope)
  Levels:  ATH -5.1%  RHigh -5.1%  SHigh -5.1%  SLow +16.9%  PSLow +17.8%
  Trend:   UPTREND (HH/HL)
  Regime:  BULLISH  +3/-0 (net +3)  MA=bullish  Trend=bullish  RHigh=neutral  PSLow=bullish
```

How to read this:

- `+5/-0 pos` → above all 5 MAs
- `+4/-1 slope` → 4 of 5 MAs still rising
- `PSLow +17.8%` → price is 17.8% above the prior swing low — a lot of cushion
- `Trend: UPTREND (HH/HL)` → staircase still going up
- `Regime: BULLISH` → 3 of 4 checks bullish, net score +3

---

## How to Interpret Regime Conflict

A "regime conflict" is when the checks disagree. This is common and does not mean something is broken — it means the market is sending mixed signals.

### How to read conflict

| What you see | What it likely means |
|---|---|
| Price above MAs, but slopes falling | Rally is losing momentum — trend lines starting to roll over |
| Price below MAs, but slopes rising | Possible early recovery — but not confirmed yet |
| UPTREND structure, but price below MAs | Structure still intact from prior move, price pulling back inside it |
| DOWNTREND structure, but price above short MAs | Short-term bounce inside a longer downtrend |
| All checks agree bullish | Clean bull regime — least conflicted |
| All checks agree bearish | Clean bear regime — least conflicted |

### The golden rule for conflict

**Count the agreements, not just the disagreements.**

- 4/4 agree = cleanest possible signal
- 3/4 agree = leaning one way, but treat as cautious
- 2/4 agree = no clear regime, reduce conviction

### Baby tip for conflict

When in doubt, give more weight to the **longer timeframe signals**:
- 200-day MA position > 10-day MA position
- Trend structure > short-term slope direction

Short-term signals flip often. Longer signals change slowly and carry more weight.

---

## Project Structure

```text
technical-regime/
  cli.py               # runs the report — start here
  requirements.txt     # dependencies (yfinance, pandas)
  regime/
    data.py            # fetches and validates market data
    indicators.py      # all the math: MAs, trend, key levels, regime scoring
  test_indicators.py   # 29 automated tests
```

---

## Quick Start

```bash
pip install -r requirements.txt   # one-time setup
python3 cli.py                    # global market report
python3 cli.py --sectors          # US sector breakdown
python3 -m pytest -q              # run all tests
```

---

## Important Notes

- This is a checklist tool, not financial advice.
- It is designed for clarity first, complexity later.
- If a ticker fails to fetch data, it is skipped automatically — the rest of the report still runs.

---

## What's Next (Ideas)

- Colorized terminal output (green/red/yellow)
- Historical regime tracking (save daily snapshots)
- Multi-timeframe analysis (weekly + daily)
- Sector rotation signals
- Export to CSV or simple dashboard

---

## One-Line Summary

Global market regime dashboard: **24 indexes across Americas, Europe, and Asia** scored on MA position, MA slope, trend structure, and key levels — green when signals agree bullish, red when bearish, yellow when mixed.
