# Donchian Channel Strategy App

Streamlit app for a 20-day Donchian breakdown/recovery strategy on the Nifty 250 universe. It loads symbols from the built-in list, fetches OHLCV from **yfinance**, computes previous-day DC20 signals, and persists watchlist/positions/history to a **GitHub Gist**.

No parquet file or manual upload required.

## Strategy Rules

| Step | Rule |
|------|------|
| **Universe** | ~240 Nifty stocks (symbol list in `update_data.py`) |
| **Data** | Daily OHLCV from yfinance |
| **Watchlist** | Previous session Close < DC20 Lower |
| **Buy** | On watchlist **and** Close > DC20 Upper |
| **Watchlist removal** | Removed when moved to buy |
| **Position fields** | Breakdown Date, Buy Date, Buy Price, Current CMP, Days Held |
| **Exit** | CMP ≥ Buy Price × **1.0628** |
| **History fields** | Breakdown Date, Buy Date, Exit Date, Holding Days, Profit % |
| **Re-entry** | Only after a fresh breakdown |
| **Price filter** | ₹0 – ₹5000 |
| **Positions** | Unlimited |

## Quick Start (Local)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Optional persistence — create `.streamlit/secrets.toml`:

```toml
GIST_ID = "your_gist_id"
GITHUB_TOKEN = "your_github_pat_with_gist_scope"
```

## Streamlit Cloud Deployment

1. Push `app.py`, `update_data.py`, `requirements.txt`, and `README.md` to GitHub.
2. Deploy at [share.streamlit.io](https://share.streamlit.io) with main file `app.py`.
3. Add secrets (**Settings → Secrets**):

```toml
GIST_ID = "your_gist_id"
GITHUB_TOKEN = "your_github_pat_with_gist_scope"
```

4. Create a gist at [gist.github.com](https://gist.github.com) and use its ID. The app stores state in `donchian_data.json` inside that gist.

**Note:** The app needs outbound network access for yfinance and the GitHub Gist API. Streamlit Cloud provides this by default.

## How Data Flows

1. **Symbols** — imported from `update_data.symbols` (Nifty 250 list).
2. **Prices** — `yfinance.download()` for daily OHLCV (cached 1 hour).
3. **Donchian** — latest session close vs DC20 from the prior 20 sessions.
4. **Strategy** — watchlist → buy → exit → history with fresh-breakdown gating.
5. **Persistence** — GitHub Gist JSON (session-only fallback without secrets).

Use **Refresh market data** in the sidebar to bypass the yfinance cache.

## Gist Data Schema

```json
{
  "watchlist": [
    {"symbol": "RELIANCE.NS", "breakdown_date": "2024-01-15", "breakdown_price": 2500.0}
  ],
  "positions": [
    {
      "symbol": "TCS.NS",
      "breakdown_date": "2024-01-10",
      "buy_date": "2024-01-20",
      "buy_price": 3500.0,
      "current_cmp": 3550.0,
      "days_held": 5
    }
  ],
  "history": [
    {
      "symbol": "INFY.NS",
      "breakdown_date": "2024-01-05",
      "buy_date": "2024-01-12",
      "exit_date": "2024-01-18",
      "holding_days": 6,
      "profit_pct": 6.28
    }
  ],
  "blocked": ["TCS.NS"]
}
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| yfinance fetch fails | Retry with **Refresh market data**; check Streamlit Cloud network |
| No signals | Ensure 21+ trading days in selected history period |
| Gist errors | Token needs `gist` scope; verify Gist ID |
| Missing symbols | Some tickers may fail on yfinance; see expander in app |

## Disclaimer

For educational and research use only. Not financial advice.
