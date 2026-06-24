# Donchian Channel Strategy App

A Streamlit-based trading strategy application that uses 20-day Donchian Channel signals from parquet data. The app tracks breakdowns, watchlist entries, buy signals, and exits with GitHub Gist persistence for cloud compatibility.

## Features

- **Previous Day Signals**: Uses only previous day's Donchian signals from parquet data (no live API calls)
- **Watchlist**: Automatically adds stocks where Yesterday Close < Yesterday DC20 Lower
- **Buy Signals**: Automatically moves watchlist stocks to positions when Yesterday Close > Yesterday DC20 Upper
- **Exit Logic**: Automatically exits positions when CMP >= Buy Price × 1.0628
- **Price Filter**: Only considers stocks priced between ₹0 - ₹5000
- **Unlimited Positions**: No limit on number of concurrent positions
- **GitHub Gist Persistence**: All data stored in GitHub Gist for cloud compatibility
- **Streamlit Cloud Ready**: No local file dependencies, fully cloud-deployable
- **History Tracking**: Complete trade history with breakdown date, buy date, exit date, holding days, and profit %

## Strategy Rules

1. **Watchlist Entry**: Stock's previous day close < previous day DC20 Lower band
2. **Buy Entry**: Stock already in watchlist AND previous day close > previous day DC20 Upper band
3. **Auto-Remove**: Stocks automatically removed from watchlist when moved to buy
4. **Exit**: Current market price >= Buy price × 1.0628 (6.28% target)
5. **Re-entry**: Stock becomes eligible again only after a fresh breakdown
6. **Price Filter**: Only stocks priced ₹0 - ₹5000 are considered

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. GitHub Gist Setup (Required for Persistence)

The app uses GitHub Gist to store watchlist, positions, and history data. This enables cloud deployment without local file dependencies.

#### Create a GitHub Personal Access Token:

1. Go to GitHub Settings → Developer Settings → Personal Access Tokens → Tokens (classic)
2. Generate a new token with **gist** scope
3. Copy the token (you won't see it again)

#### Create a Gist:

1. Go to [gist.github.com](https://gist.github.com)
2. Create a new gist (can be empty or with a placeholder file)
3. Copy the Gist ID from the URL (e.g., `abc123def456` from `https://gist.github.com/username/abc123def456`)

### 3. Prepare Parquet Data

Your parquet file must contain the following columns:

| Column | Description |
|--------|-------------|
| Symbol | Stock ticker (e.g., RELIANCE.NS, TCS.NS) |
| Date | Trading date |
| Open | Opening price |
| High | Highest price |
| Low | Lowest price |
| Close | Closing price |

**Requirements**:
- At least 21 trading days per symbol to compute 20-day Donchian channels
- Data should be sorted by Symbol and Date
- Include all symbols you want to screen

### 4. Run Locally

```bash
streamlit run app.py
```

Then in the sidebar:
1. Enter your Gist ID
2. Enter your GitHub Token
3. Upload your parquet file or provide a URL
4. Click to load data and process signals

## Streamlit Cloud Deployment

### Option 1: Deploy with Secrets

1. **Push to GitHub**:
   ```bash
   git init
   git add app.py requirements.txt README.md
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/your-repo.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Connect your GitHub repository
   - Select the repository and branch
   - Enter `app.py` as the main file path

3. **Add Secrets**:
   In your Streamlit Cloud app settings, add these secrets:
   ```
   GIST_ID = your_gist_id_here
   GITHUB_TOKEN = your_github_token_here
   ```

4. **Provide Parquet Data**:
   Since Streamlit Cloud doesn't have persistent local storage, you have two options:
   
   **Option A**: Upload parquet via the app's file uploader each session
   **Option B**: Host your parquet file publicly (e.g., GitHub Releases, S3, GCS) and use the URL option

### Option 2: Environment Variables

You can also use environment variables instead of Streamlit secrets:

```bash
export GIST_ID="your_gist_id"
export GITHUB_TOKEN="your_token"
streamlit run app.py
```

On Streamlit Cloud, add these in the app's environment variables section.

## File Structure

```
.
├── app.py              # Main application
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

## Data Persistence

The app stores all data in a GitHub Gist as a JSON file named `donchian_data.json`:

```json
{
  "watchlist": [
    {
      "symbol": "RELIANCE.NS",
      "breakdown_date": "2024-01-15",
      "breakdown_price": 2500.00,
      "added_date": "2024-01-16 10:30:00"
    }
  ],
  "positions": [
    {
      "symbol": "TCS.NS",
      "breakdown_date": "2024-01-10",
      "buy_date": "2024-01-20",
      "buy_price": 3500.00,
      "current_cmp": 3550.00,
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
      "profit_pct": 6.5
    }
  ],
  "ineligible": ["RELIANCE.NS"]
}
```

## Tabs Overview

- **🟠 Watchlist**: Stocks awaiting recovery (Close < DC20 Lower)
- **🟢 Positions**: Active positions with buy details and current P&L
- **📜 History**: Completed trades with exit details
- **📊 Signals**: Current Donchian signals for all symbols

## Customization

You can adjust strategy parameters in the sidebar:

- **Exit Multiplier**: Default 1.0628 (6.28% target)
- **Min Price**: Default ₹0
- **Max Price**: Default ₹5000

## Troubleshooting

### Gist Authentication Failed

- Verify your GitHub token has the `gist` scope
- Check that your Gist ID is correct (from the Gist URL)
- Ensure the Gist is not deleted

### Parquet Loading Failed

- Verify your parquet file has the required columns
- Check that the file contains at least 21 days of data per symbol
- Ensure the file is not corrupted

### No Signals Showing

- Check that your parquet data is recent
- Verify the price filter isn't excluding all stocks
- Ensure symbols have sufficient historical data

## License

This project is provided as-is for educational and research purposes.

## Disclaimer

This is a trading strategy tool for educational purposes only. Past performance does not guarantee future results. Always do your own research and consult with a financial advisor before making trading decisions.
