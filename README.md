# AlphaPulse: Institutional Quantitative Stock & Crypto Terminal

AlphaPulse (GO::OS) is an institutional-grade quantitative trading platform and execution terminal designed to analyze real-time equity and crypto markets, isolate idiosyncratic alpha from sector/market beta, compute options dealer gamma exposure (GEX & Max Pain), and enforce mathematical risk parity.

---

## 🚀 Live Cloud Deployment

### Option A: 1-Click Deploy on Render (Free & Recommended)
1. Fork or push this repository to your GitHub account (`https://github.com/shamir-khan-dev/Stock-Analyzer.git`).
2. Go to [Render.com](https://render.com) and create a **New Web Service**.
3. Select your GitHub repository.
4. Render will automatically detect `render.yaml`:
   - **Environment:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path:** `/health`
5. Click **Deploy Web Service** — your app is live on `https://your-app.onrender.com`!

### Option B: Deploy on Railway
1. Go to [Railway.app](https://railway.app) and select **Deploy from GitHub repo**.
2. Railway detects the `Procfile` / `Dockerfile` and builds automatically.
3. Add environment variable: `PORT=8000`.

### Option C: Docker Container
Run anywhere with Docker:
```bash
docker build -t alphapulse-terminal .
docker run -p 8000:8000 alphapulse-terminal
```

---

## ⚡ Local Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/shamir-khan-dev/Stock-Analyzer.git
cd Stock-Analyzer
pip install -r requirements.txt
```

### 2. Launch
```bash
# Windows
START_STOCK_ANALYZER.bat

# Or direct Python
python backend/run.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

---

## 🏛️ Quantitative Mathematical Engine

### 1. Factor-Neutral Residual Engine (Avellaneda & Lee, 2010)
Standard technical indicators fail because they trade unhedged market beta. AlphaPulse regresses each stock against its benchmark sector ETF (`SOXX`, `XLK`, `XLY`, `XLF`, `XLE`) and `SPY`:
$$R_{\text{stock}, t} = \alpha + \beta_{\text{mkt}} R_{\text{SPY}, t} + \beta_{\text{sec}} R_{\text{sec}, t} + \epsilon_t$$
Extracts the cumulative idiosyncratic residual spread and computes the Ornstein-Uhlenbeck **$s$-score**:
- **$s < -1.5\sigma$ (Stat-Arb Bullish Divergence):** Stock is oversold relative to sector peers; primed for mean-reversion catch-up.
- **$s > +1.5\sigma$ (Stat-Arb Bearish Exhaustion):** Relative outperformance is stretched; vulnerable to pullbacks.
- **$-1.5\sigma \le s \le +1.5\sigma$:** Sector in-line fair value.

### 2. Options Market Structure & Gamma Desk (GEX)
Mega-cap price action is heavily dictated by options dealer delta-hedging:
- **Max Pain Strike:** The strike price where aggregate option buyer value expires worthless (the institutional settlement magnet).
- **Call Wall & Put Wall:** Major open-interest resistance ceiling and downside floor.
- **Gamma Regime:** Detects **Positive Gamma** (volatility pinned near Max Pain) vs **Negative Gamma** (volatility expansion cascades).

### 3. Volatility-Targeted Risk Parity Sizing (Grinold-Kahn)
- Replaces arbitrary share guesses with volatility-constant risk budgeting.
- Computes exact share sizing for a fixed **$500 risk budget** ($\text{Risk} / \text{ATR Stop Distance}$).
- 1-click **"⚡ Auto-Size Paper Trade"** button auto-populates exact shares into the execution ticket.
- Tracks institutional **Sortino Ratio** (downside semivariance) and **Calmar Ratio**.

### 4. Multi-Horizon Wall Street Strategy Desk
- **1 – 2 Days (Scalp):** Intraday pivot mean-reversion & micro-momentum.
- **Days – Weeks (Swing):** AQR time-series momentum & trend following.
- **Months – Years (Long-Term):** 200-SMA institutional regime & accumulation zones.

### 5. Multimodal Computer Vision & AI TradeBot
- Paste any chart screenshot (`Ctrl+V`) from TradingView, Robinhood, Binance, or Webull.
- Computer Vision extracts candlestick mass distribution and trajectory slope.
- Conversational TradeBot answers queries with direct P&L calculations and plain-English translation.

---

## ⌨️ Trader Hotkey Shortcuts
- <kbd>/</kbd> — Jump focus to Ticker Search
- <kbd>1</kbd> / <kbd>2</kbd> / <kbd>3</kbd> — Select **Intraday**, **Swing**, or **Long-Term** horizon cards
- <kbd>B</kbd> — Instant Paper Buy current ticker
- <kbd>S</kbd> — Instant Paper Sell current ticker
- <kbd>Esc</kbd> — Dismiss modals / guide

---

## 📂 Project Architecture
```
Stock-Analyzer/
├── backend/
│   ├── app/
│   │   ├── api/                  # REST endpoints (Analysis, Backtest, Paper, Bot, Market)
│   │   ├── core/
│   │   │   ├── factor_engine.py  # Factor neutralization & s-score calculation
│   │   │   ├── options_engine.py # Options chain Max Pain & Gamma Wall calculator
│   │   │   ├── risk_engine.py    # Volatility risk parity sizing & Sortino metrics
│   │   │   ├── quant_engine.py   # Multi-factor confluence scoring & ATR targets
│   │   │   ├── data_fetcher.py   # Ingestion layer with LRU/TTL caching
│   │   │   ├── indicators.py     # Technical indicators
│   │   │   └── backtester.py     # Historical simulation engine
│   │   ├── vision/
│   │   │   ├── chart_vision.py   # Computer vision & chart screenshot analysis
│   │   │   └── trade_bot.py      # Conversational trade partner
│   │   ├── config.py             # Environment configuration
│   │   └── main.py               # FastAPI application
│   └── run.py                    # Server launcher
├── frontend/
│   ├── index.html                # High-density institutional dark terminal UI
│   ├── css/styles.css            # Glassmorphism & responsive CSS styling
│   └── js/
│       ├── app.js                # State coordinator & quant rendering
│       ├── chart.js              # 60 FPS HTML5 Canvas candlestick chart
│       └── bot.js                # Clipboard paste (Ctrl+V) & chat coordinator
├── Procfile                      # Cloud hosting process definition
├── render.yaml                   # 1-Click Render.com deployment spec
├── Dockerfile                    # Containerization spec
└── requirements.txt              # Python dependencies
```

---

## ⚖️ License
MIT License. Built for algorithmic and quantitative research.
