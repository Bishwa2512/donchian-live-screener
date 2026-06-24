"""
Donchian Channel Strategy App
===============================
20-day Donchian Channel breakdown/recovery strategy for Nifty 250.
Uses previous day signals from parquet data. Persists to GitHub Gist.

Run:
    pip install streamlit pandas pyarrow requests
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime, timedelta
from io import BytesIO
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────
DONCHIAN_PERIOD = 20
EXIT_MULTIPLIER = 1.0628
PRICE_FILTER_MIN = 0
PRICE_FILTER_MAX = 5000
GIST_ID = "71e6096d03b9bbb9c586d45d067be413"
GITHUB_TOKEN = "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"
DEFAULT_PARQUET_URL = "nifty250_1year_ohlcv.parquet"

st.set_page_config(page_title="Donchian Strategy", page_icon="📡", layout="wide")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #0b0d12; }
[data-testid="stSidebar"] { background: #131720; }
[data-testid="stSidebar"] * { color: #dce3f5 !important; }
.main .block-container { padding-top: 1.5rem; padding-bottom: 3rem; }
h1,h2,h3 { color: #dce3f5 !important; }
.stMetric { background: #131720; border: 1px solid #252b3d; border-radius: 10px; padding: 14px !important; }
.stMetric label { color: #6b758f !important; font-size: 11px !important; text-transform: uppercase; }
.stMetric [data-testid="stMetricValue"] { color: #dce3f5 !important; font-size: 22px !important; font-weight: 700 !important; }
.stDataFrame { border: 1px solid #252b3d; border-radius: 8px; }
[data-testid="stExpander"] { background: #131720; border: 1px solid #252b3d; border-radius: 8px; }
div[data-testid="stHorizontalBlock"] { gap: 10px; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# GitHub Gist Persistence
# ─────────────────────────────────────────────────────────────────────────────
class GistStorage:
    """Store app data in GitHub Gist for cloud persistence."""
    
    def __init__(self):
        self.gist_id = GIST_ID
        self.github_token = GITHUB_TOKEN
        self.api_url = f"https://api.github.com/gists/{self.gist_id}"
    
    def _get_headers(self):
        return {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def load_data(self):
        """Load data from Gist."""
        if not self.gist_id or not self.github_token:
            return {"watchlist": [], "positions": [], "history": [], "ineligible": []}
        
        try:
            response = requests.get(self.api_url, headers=self._get_headers())
            response.raise_for_status()
            gist_data = response.json()
            
            # Find the data file in the gist
            for filename, file_info in gist_data["files"].items():
                if filename == "donchian_data.json":
                    raw_url = file_info["raw_url"]
                    data_response = requests.get(raw_url)
                    return json.loads(data_response.text)
            
            return {"watchlist": [], "positions": [], "history": [], "ineligible": []}
        except Exception as e:
            st.error(f"Failed to load from Gist: {e}")
            return {"watchlist": [], "positions": [], "history": [], "ineligible": []}
    
    def save_data(self, data):
        """Save data to Gist."""
        if not self.gist_id or not self.github_token:
            st.error("Gist credentials not configured. Data will not persist.")
            return False
        
        try:
            # Get current gist to preserve other files
            response = requests.get(self.api_url, headers=self._get_headers())
            response.raise_for_status()
            gist_data = response.json()
            
            # Update the data file
            files = gist_data.get("files", {})
            files["donchian_data.json"] = {
                "content": json.dumps(data, indent=2, default=str)
            }
            
            # Update gist
            update_data = {
                "files": files,
                "description": f"Donchian Strategy Data - Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
            
            patch_response = requests.patch(self.api_url, json=update_data, headers=self._get_headers())
            patch_response.raise_for_status()
            return True
        except Exception as e:
            st.error(f"Failed to save to Gist: {e}")
            return False


# ─────────────────────────────────────────────────────────────────────────────
# Data Loading from Parquet
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_parquet_data(uploaded_file=None, url=None):
    """Load OHLCV data from parquet file."""
    try:
        if uploaded_file is not None:
            df = pd.read_parquet(uploaded_file)
        elif url:
            # Check if URL is a local file path
            if url.startswith("http://") or url.startswith("https://"):
                response = requests.get(url)
                df = pd.read_parquet(BytesIO(response.content))
            else:
                # Treat as local file path
                df = pd.read_parquet(url)
        else:
            return None
        
        # Ensure required columns exist
        required_cols = ["Symbol", "Date", "Open", "High", "Low", "Close"]
        for col in required_cols:
            if col not in df.columns:
                st.error(f"Missing required column: {col}")
                return None
        
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values(["Symbol", "Date"])
        return df
    except Exception as e:
        st.error(f"Failed to load parquet data: {e}")
        return None


def compute_previous_day_donchian(df, period=20):
    """
    Compute Donchian channels for previous day only.
    Returns DataFrame with one row per symbol for the most recent trading day.
    """
    results = []
    total_symbols = len(df["Symbol"].unique())
    insufficient_data = 0
    price_filtered = 0
    
    for symbol in df["Symbol"].unique():
        sym_df = df[df["Symbol"] == symbol].copy()
        sym_df = sym_df.sort_values("Date")
        
        if len(sym_df) < period + 1:
            insufficient_data += 1
            continue
        
        # Get the most recent day (yesterday's data)
        latest_row = sym_df.iloc[-1]
        latest_date = latest_row["Date"]
        latest_close = latest_row["Close"]
        
        # Get previous 20 days (excluding the latest day)
        prev_data = sym_df.iloc[:-1]
        
        if len(prev_data) < period:
            insufficient_data += 1
            continue
        
        # Compute DC20 from previous 20 days
        dc_upper = prev_data["High"].tail(period).max()
        dc_lower = prev_data["Low"].tail(period).min()
        
        # Price filter
        if not (PRICE_FILTER_MIN <= latest_close <= PRICE_FILTER_MAX):
            price_filtered += 1
            continue
        
        # Determine status based on previous day's close vs DC20
        if latest_close > dc_upper:
            status = "above_upper"
        elif latest_close < dc_lower:
            status = "below_lower"
        else:
            status = "inside"
        
        results.append({
            "Symbol": symbol,
            "Date": latest_date.strftime("%Y-%m-%d"),
            "Close": round(float(latest_close), 2),
            "DC_Upper": round(float(dc_upper), 2),
            "DC_Lower": round(float(dc_lower), 2),
            "Status": status,
            "GapToUpper": round(float((dc_upper - latest_close) / latest_close * 100), 2),
            "GapToLower": round(float((latest_close - dc_lower) / latest_close * 100), 2),
        })
    
    # Log filtering stats
    st.info(f"📊 Filter stats: {total_symbols} total | {insufficient_data} insufficient data | {price_filtered} price filtered | {len(results)} passed")
    
    return pd.DataFrame(results)


# ─────────────────────────────────────────────────────────────────────────────
# Strategy Logic
# ─────────────────────────────────────────────────────────────────────────────
def process_strategy(donchian_df, storage_data):
    """
    Process strategy logic:
    1. Add to watchlist: Yesterday Close < Yesterday DC20 Lower
    2. Move to buy: Watchlist stock AND Yesterday Close > Yesterday DC20 Upper
    3. Check exits: CMP >= Buy Price * 1.0628
    """
    watchlist = storage_data.get("watchlist", [])
    positions = storage_data.get("positions", [])
    history = storage_data.get("history", [])
    ineligible = storage_data.get("ineligible", [])
    
    # Convert to DataFrames for easier manipulation
    watchlist_df = pd.DataFrame(watchlist)
    positions_df = pd.DataFrame(positions)
    
    # Get current prices from donchian_df
    current_prices = dict(zip(donchian_df["Symbol"], donchian_df["Close"]))
    current_dates = dict(zip(donchian_df["Symbol"], donchian_df["Date"]))
    
    # 1. Add new breakdowns to watchlist (if not ineligible)
    new_watchlist = donchian_df[
        (donchian_df["Status"] == "below_lower") &
        (~donchian_df["Symbol"].isin(ineligible)) &
        (~donchian_df["Symbol"].isin([w["symbol"] for w in watchlist]))
    ]
    
    for _, row in new_watchlist.iterrows():
        watchlist.append({
            "symbol": row["Symbol"],
            "breakdown_date": row["Date"],
            "breakdown_price": row["Close"],
            "added_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    # 2. Move watchlist stocks to positions if they recover
    if not watchlist_df.empty:
        watchlist_symbols = watchlist_df["symbol"].tolist()
        recoveries = donchian_df[
            (donchian_df["Status"] == "above_upper") &
            (donchian_df["Symbol"].isin(watchlist_symbols))
        ]
        
        for _, row in recoveries.iterrows():
            symbol = row["Symbol"]
            wl_entry = watchlist_df[watchlist_df["symbol"] == symbol].iloc[0]
            
            # Add to positions
            positions.append({
                "symbol": symbol,
                "breakdown_date": wl_entry["breakdown_date"],
                "buy_date": row["Date"],
                "buy_price": row["Close"],
                "current_cmp": row["Close"],
                "days_held": 0
            })
            
            # Remove from watchlist
            watchlist = [w for w in watchlist if w["symbol"] != symbol]
            
            # Add to ineligible (needs fresh breakdown)
            ineligible.append(symbol)
    
    # 3. Update positions and check exits
    updated_positions = []
    for pos in positions:
        symbol = pos["symbol"]
        
        if symbol in current_prices:
            pos["current_cmp"] = current_prices[symbol]
            
            # Calculate days held
            buy_date = datetime.strptime(pos["buy_date"], "%Y-%m-%d")
            current_date = datetime.strptime(current_dates[symbol], "%Y-%m-%d")
            pos["days_held"] = (current_date - buy_date).days
            
            # Check exit condition
            exit_price = pos["buy_price"] * EXIT_MULTIPLIER
            if pos["current_cmp"] >= exit_price:
                # Move to history
                profit_pct = ((pos["current_cmp"] - pos["buy_price"]) / pos["buy_price"]) * 100
                history.append({
                    "symbol": symbol,
                    "breakdown_date": pos["breakdown_date"],
                    "buy_date": pos["buy_date"],
                    "exit_date": current_dates[symbol],
                    "holding_days": pos["days_held"],
                    "profit_pct": round(profit_pct, 2)
                })
                
                # Remove from ineligible (can re-enter after fresh breakdown)
                if symbol in ineligible:
                    ineligible.remove(symbol)
            else:
                updated_positions.append(pos)
        else:
            updated_positions.append(pos)
    
    positions = updated_positions
    
    return {
        "watchlist": watchlist,
        "positions": positions,
        "history": history,
        "ineligible": ineligible
    }


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📡 Donchian Strategy")
    st.markdown("*Previous day signals from parquet*")
    st.markdown("---")
    
    st.markdown("---")
    
    # Parquet data source
    st.markdown("#### 📁 Data Source")
    data_source = st.radio("Load data from:", ["URL", "Upload Parquet"], index=0)
    
    if data_source == "Upload Parquet":
        uploaded_file = st.file_uploader("Upload parquet file", type=["parquet"])
        parquet_url = None
    else:
        parquet_url = st.text_input("Parquet URL", value=DEFAULT_PARQUET_URL,
                                    help="GitHub raw URL or any public URL to parquet file")
        uploaded_file = None
    
    st.markdown("---")
    
    # Strategy parameters
    st.markdown("#### ⚙️ Strategy Parameters")
    exit_multiplier = st.number_input("Exit Multiplier", value=1.0628, step=0.0001, format="%.4f")
    price_min = st.number_input("Min Price", value=0, step=100)
    price_max = st.number_input("Max Price", value=5000, step=100)
    
    st.markdown("---")
    st.markdown("#### 📊 Strategy Rules")
    st.markdown("""
    - **Watchlist**: Close < DC20 Lower
    - **Buy**: Watchlist + Close > DC20 Upper
    - **Exit**: CMP >= Buy × 1.0628
    - **Price Filter**: ₹0 - ₹5000
    - **Unlimited positions**
    """)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("# 📡 Donchian Channel Strategy")
st.markdown("**Previous day breakdown/recovery strategy — powered by parquet data**")

# Initialize storage
storage = GistStorage()

# Load data
if uploaded_file or parquet_url:
    with st.spinner("Loading parquet data..."):
        parquet_df = load_parquet_data(uploaded_file, parquet_url)
    
    if parquet_df is not None:
        st.success(f"✅ Loaded {len(parquet_df)} rows for {parquet_df['Symbol'].nunique()} symbols")
        
        # Compute Donchian signals
        with st.spinner("Computing Donchian channels..."):
            donchian_df = compute_previous_day_donchian(parquet_df, DONCHIAN_PERIOD)
        
        if donchian_df.empty:
            st.warning("No data after filtering. Check your parquet file.")
        else:
            st.success(f"✅ Computed signals for {len(donchian_df)} symbols")
            
            # Load storage data
            storage_data = storage.load_data()
            
            # Process strategy
            with st.spinner("Processing strategy..."):
                updated_data = process_strategy(donchian_df, storage_data)
                
                # Save to Gist
                if storage.save_data(updated_data):
                    st.success("✅ Data saved to Gist")
            
            # Display results
            tab_watchlist, tab_positions, tab_history, tab_signals = st.tabs(
                ["🟠 Watchlist", "🟢 Positions", "📜 History", "📊 Signals"]
            )
            
            # Watchlist Tab
            with tab_watchlist:
                st.markdown("### 🟠 Watchlist — Stocks Awaiting Recovery")
                st.caption("Stocks where Yesterday Close < Yesterday DC20 Lower")
                
                watchlist_data = updated_data.get("watchlist", [])
                if watchlist_data:
                    wl_df = pd.DataFrame(watchlist_data)
                    wl_df["breakdown_price"] = wl_df["breakdown_price"].map("₹{:,.2f}".format)
                    st.dataframe(wl_df, use_container_width=True, hide_index=True)
                else:
                    st.info("Watchlist is empty.")
            
            # Positions Tab
            with tab_positions:
                st.markdown("### 🟢 Active Positions")
                st.caption("Stocks bought from watchlist, awaiting exit")
                
                positions_data = updated_data.get("positions", [])
                if positions_data:
                    pos_df = pd.DataFrame(positions_data)
                    pos_df["buy_price"] = pos_df["buy_price"].map("₹{:,.2f}".format)
                    pos_df["current_cmp"] = pos_df["current_cmp"].map("₹{:,.2f}".format)
                    pos_df["exit_target"] = (pos_df["buy_price"].astype(float) * exit_multiplier).map("₹{:,.2f}".format)
                    pos_df["pnl_pct"] = ((pos_df["current_cmp"].astype(float) - pos_df["buy_price"].astype(float)) / pos_df["buy_price"].astype(float) * 100).round(2)
                    st.dataframe(pos_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No active positions.")
            
            # History Tab
            with tab_history:
                st.markdown("### 📜 Exit History")
                st.caption("Completed trades with exit details")
                
                history_data = updated_data.get("history", [])
                if history_data:
                    hist_df = pd.DataFrame(history_data)
                    hist_df["profit_pct"] = hist_df["profit_pct"].map("{:.2f}%".format)
                    st.dataframe(hist_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No exit history yet.")
            
            # Signals Tab
            with tab_signals:
                st.markdown("### 📊 Current Donchian Signals")
                st.caption("Previous day signals from parquet data")
                
                # Summary metrics
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Above Upper", len(donchian_df[donchian_df["Status"] == "above_upper"]))
                m2.metric("Below Lower", len(donchian_df[donchian_df["Status"] == "below_lower"]))
                m3.metric("Inside Channel", len(donchian_df[donchian_df["Status"] == "inside"]))
                m4.metric("Total Signals", len(donchian_df))
                
                st.markdown("---")
                
                # Below Lower (Watchlist candidates)
                st.markdown("#### 🟠 Below Lower (Watchlist Candidates)")
                below_lower = donchian_df[donchian_df["Status"] == "below_lower"]
                if not below_lower.empty:
                    disp = below_lower[["Symbol", "Close", "DC_Lower", "GapToUpper", "Date"]].copy()
                    disp.columns = ["Symbol", "Close", "DC Lower", "Gap to Upper", "Date"]
                    disp["Close"] = disp["Close"].map("₹{:,.2f}".format)
                    disp["DC Lower"] = disp["DC Lower"].map("₹{:,.2f}".format)
                    disp["Gap to Upper"] = disp["Gap to Upper"].map("{:.2f}%".format)
                    st.dataframe(disp, use_container_width=True, hide_index=True)
                else:
                    st.info("No stocks below DC20 Lower.")
                
                # Above Upper (Buy signals)
                st.markdown("#### 🟢 Above Upper (Buy Signals)")
                above_upper = donchian_df[donchian_df["Status"] == "above_upper"]
                if not above_upper.empty:
                    disp = above_upper[["Symbol", "Close", "DC_Upper", "GapToLower", "Date"]].copy()
                    disp.columns = ["Symbol", "Close", "DC Upper", "Above Band", "Date"]
                    disp["Close"] = disp["Close"].map("₹{:,.2f}".format)
                    disp["DC Upper"] = disp["DC Upper"].map("₹{:,.2f}".format)
                    disp["Above Band"] = disp["Above Band"].map("{:.2f}%".format)
                    st.dataframe(disp, use_container_width=True, hide_index=True)
                else:
                    st.info("No stocks above DC20 Upper.")
                
                # Inside Channel
                st.markdown("#### ⚪ Inside Channel")
                inside = donchian_df[donchian_df["Status"] == "inside"]
                if not inside.empty:
                    disp = inside[["Symbol", "Close", "DC_Upper", "DC_Lower", "Date"]].copy()
                    disp.columns = ["Symbol", "Close", "DC Upper", "DC Lower", "Date"]
                    disp["Close"] = disp["Close"].map("₹{:,.2f}".format)
                    disp["DC Upper"] = disp["DC Upper"].map("₹{:,.2f}".format)
                    disp["DC Lower"] = disp["DC Lower"].map("₹{:,.2f}".format)
                    st.dataframe(disp, use_container_width=True, hide_index=True, height=300)
                else:
                    st.info("No stocks inside channel.")
    else:
        st.error("Failed to load parquet data.")
else:
    st.info("👆 Upload a parquet file or provide a URL to load stock data.")
    st.markdown("""
    ### Expected Parquet Format:
    Your parquet file should contain the following columns:
    - **Symbol**: Stock ticker (e.g., RELIANCE.NS)
    - **Date**: Trading date
    - **Open**: Opening price
    - **High**: Highest price
    - **Low**: Lowest price
    - **Close**: Closing price
    
    The data should include at least 21 trading days per symbol to compute 20-day Donchian channels.
    """)

# ─────────────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Donchian Channel: 20-day rolling High/Low. "
    "Watchlist: Close < Lower Band. Buy: Watchlist + Close > Upper Band. "
    "Exit: Price >= Entry × 1.0628. "
    "Data persisted to GitHub Gist for cloud compatibility. "
    "No local file dependencies - Streamlit Cloud ready."
)
