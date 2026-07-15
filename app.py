"""
Donchian Channel Strategy App
=============================
20-day Donchian breakdown/recovery strategy. Symbols from Nifty 250 list,
OHLCV from yfinance, state persisted to GitHub Gist (Streamlit Cloud ready).

Run:
    pip install -r requirements.txt
    streamlit run app.py
"""

from __future__ import annotations

import json
import warnings
from datetime import datetime
from typing import Any

import pandas as pd
import requests
import streamlit as st
import yfinance as yf

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────
NIFTY250_SYMBOLS = [
    "TRIDENT.NS", "YESBANK.NS", "UCOBANK.NS", "CENTRALBK.NS", "IOB.NS", "SUZLON.NS",
    "JAIBALAJI.NS", "SJVN.NS", "NHPC.NS", "IDFCFIRSTB.NS", "BAJAJHFL.NS", "NMDC.NS",
    "IDBI.NS", "MAHABANK.NS", "NTPCGREEN.NS", "IRFC.NS", "LEMONTREE.NS", "PNB.NS",
    "GMRAIRPORT.NS", "ZEEL.NS", "IEX.NS", "IREDA.NS", "CANBK.NS", "MOTHERSON.NS",
    "IOC.NS", "BANKINDIA.NS", "ASHOKLEY.NS", "IGL.NS", "UNIONBANK.NS", "GAIL.NS",
    "SAIL.NS", "WIPRO.NS", "HFCL.NS", "AWL.NS", "TATASTEEL.NS", "HUDCO.NS",
    "BELRISE.NS", "JIOFIN.NS", "ENGINERSIN.NS", "ONGC.NS", "RVNL.NS", "SWIGGY.NS",
    "CROMPTON.NS", "BANKBARODA.NS", "NYKAA.NS", "POWERGRID.NS", "ITC.NS", "PETRONET.NS",
    "LTF.NS", "M&MFIN.NS", "JSWINFRA.NS", "BANSALWIRE.NS", "NLCINDIA.NS", "BPCL.NS",
    "FEDERALBNK.NS", "GICRE.NS", "NTPC.NS", "RECLTD.NS", "NATIONALUM.NS",
    "KALYANKJIL.NS", "EXIDEIND.NS", "BHEL.NS", "TATAPOWER.NS", "HINDPETRO.NS", "KOTAKBANK.NS",
    "POONAWALLA.NS", "BIOCON.NS", "OIL.NS", "LICHSGFIN.NS", "PATANJALI.NS", "BEL.NS",
    "JUBLFOOD.NS", "DABUR.NS", "APOLLOTYRE.NS", "PFC.NS", "DELHIVERY.NS", "COALINDIA.NS",
    "CIEINDIA.NS", "CONCOR.NS", "CHAMBLFERT.NS", "ICICIPRULI.NS", "BERGEPAINT.NS", "IRCTC.NS",
    "VBL.NS", "METROPOLIS.NS", "BALRAMCHIN.NS", "JSWENERGY.NS", "HINDZINC.NS", "HDFCLIFE.NS",
    "SONACOMS.NS", "DLF.NS", "SBICARD.NS", "JUBLINGREA.NS", "TATAINVEST.NS",
    "ATGL.NS", "EIDPARRY.NS", "GRANULES.NS", "APLLTD.NS", "KPITTECH.NS",
    "HDFCBANK.NS", "MARICO.NS", "INDIANB.NS", "INDUSINDBK.NS", "MOTILALOFS.NS", "FORTIS.NS",
    "BAJFINANCE.NS", "CGPOWER.NS", "SHRIRAMFIN.NS", "HINDALCO.NS", "NAUKRI.NS", "GODREJCP.NS",
    "AUBANK.NS", "SBIN.NS", "MAXHEALTH.NS", "KPRMILL.NS", "GODREJIND.NS", "PREMIERENE.NS",
    "UNOMINDA.NS", "PAYTM.NS", "TATACONSUM.NS", "JINDALSTEL.NS", "360ONE.NS", "NAM-INDIA.NS",
    "INFY.NS", "HCLTECH.NS", "HAVELLS.NS", "MEDANTA.NS", "DRREDDY.NS", "JSWSTEEL.NS",
    "ABREL.NS", "UNITDSPR.NS", "BDL.NS", "RELIANCE.NS", "ICICIBANK.NS", "ACC.NS",
    "CIPLA.NS", "VOLTAS.NS", "AXISBANK.NS", "LAURUSLABS.NS", "NESTLEIND.NS", "TORNTPOWER.NS",
    "AUROPHARMA.NS", "RAINBOW.NS", "TECHM.NS", "ADANIGREEN.NS", "COFORGE.NS", "COCHINSHIP.NS",
    "PRESTIGE.NS", "IPCALAB.NS", "ASTRAL.NS", "PIDILITIND.NS", "DEEPAKNTR.NS", "POLICYBZR.NS",
    "MFSL.NS", "CHOLAFIN.NS", "BLUESTARCO.NS", "OBEROIRLTY.NS", "DALBHARAT.NS", "LLOYDSME.NS",
    "BAJAJFINSV.NS", "GODREJPROP.NS", "ICICIGI.NS", "SUNPHARMA.NS", "ADANIPORTS.NS", "PHOENIXLTD.NS",
    "BHARTIARTL.NS", "TATACOMM.NS", "COLPAL.NS", "COROMANDEL.NS", "BHARATFORG.NS", "GLENMARK.NS",
    "GLAXO.NS", "HINDUNILVR.NS", "TCS.NS", "BALKRISIND.NS", "LUPIN.NS", "MPHASIS.NS",
    "MANKIND.NS", "MAZDOCK.NS", "ENDURANCE.NS", "HDFCAMC.NS", "SRF.NS", "ASIANPAINT.NS",
    "ESCORTS.NS", "PIIND.NS", "MCX.NS", "ADANIENT.NS", "AJANTPHARM.NS", "WAAREEENER.NS",
    "TRENT.NS", "M&M.NS", "GRASIM.NS", "MUTHOOTFIN.NS", "TIINDIA.NS", "TVSMOTOR.NS",
    "LTTS.NS", "CEATLTD.NS", "SUPREMEIND.NS", "RADICO.NS", "FLUOROCHEM.NS", "SIEMENS.NS",
    "LTM.NS", "BSE.NS", "TATAELXSI.NS", "CRISIL.NS", "SCHAEFFLER.NS",
    "DMART.NS", "TITAN.NS", "TORNTPHARM.NS", "SUNDARMFIN.NS", "HAL.NS", "AIAENG.NS",
    "DATAPATTNS.NS", "THERMAX.NS", "NETWEB.NS", "HEROMOTOCO.NS", "PERSISTENT.NS", "BRITANNIA.NS",
    "ALKEM.NS", "JKCEMENT.NS", "KEI.NS", "CUMMINSIND.NS", "DIVISLAB.NS", "LINDEINDIA.NS",
    "ABB.NS", "EICHERMOT.NS", "APOLLOHOSP.NS", "OFSS.NS", "POLYCAB.NS", "ULTRACEMCO.NS",
    "DIXON.NS", "MARUTI.NS", "APARINDS.NS", "SHREECEM.NS", "ABBOTINDIA.NS", "3MINDIA.NS",
    "HONAUT.NS", "BOSCHLTD.NS", "PAGEIND.NS", "MRF.NS",
]

DONCHIAN_PERIOD = 20
EXIT_MULTIPLIER = 1.0628
PRICE_FILTER_MIN = 0
PRICE_FILTER_MAX = 5000
GIST_DATA_FILE = "donchian_data.json"

EMPTY_STORAGE = {
    "watchlist": [],
    "positions": [],
    "buy_signals": [],
    "history": [],
    "blocked": [],
    "sheet_status": {}
}

st.set_page_config(page_title="Donchian Strategy", page_icon="📡", layout="wide")

st.markdown(
    """
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
div[data-testid="stHorizontalBlock"] { gap: 10px; }
</style>
""",
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# GitHub Gist persistence
# ─────────────────────────────────────────────────────────────────────────────
def _get_secret(key: str, default: str = "") -> str:
    """Read config from Streamlit secrets or explicit session overrides."""
    override_key = f"cfg_{key.lower()}"
    if override_key in st.session_state:
        override = st.session_state[override_key]
        if override is not None and str(override).strip():
            return str(override).strip()

    try:
        if key in st.secrets:
            return str(st.secrets[key]).strip()
        if key == "GITHUB_TOKEN" and "GH_TOKEN" in st.secrets:
            return str(st.secrets["GH_TOKEN"]).strip()
    except (FileNotFoundError, KeyError, AttributeError):
        pass
    return default


def _gist_auth_help(status_code: int) -> str:
    if status_code != 401:
        return ""
    return (
        " GitHub returned 401 Unauthorized. Use a **classic** Personal Access Token "
        "(not fine-grained) with the **gist** scope, created on the same account "
        "that owns the gist. Set `GIST_ID` and `GITHUB_TOKEN` in Streamlit Cloud "
        "secrets (no quotes, no extra spaces)."
    )


class GistStorage:
    """Persist watchlist, positions, and history in a GitHub Gist."""

    def __init__(self) -> None:
        self.gist_id = _get_secret("GIST_ID")
        self.github_token = _get_secret("GITHUB_TOKEN")
        self.enabled = bool(self.gist_id and self.github_token)
        self.api_url = f"https://api.github.com/gists/{self.gist_id}" if self.gist_id else ""

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Donchian-Strategy-Streamlit-App",
        }

    def test_connection(self) -> tuple[bool, str]:
        """Verify token and gist access before load/save."""
        if not self.enabled:
            return False, "Set GIST_ID and GITHUB_TOKEN in Streamlit secrets."

        try:
            user_resp = requests.get(
                "https://api.github.com/user",
                headers=self._headers(),
                timeout=20,
            )
            if user_resp.status_code == 401:
                return False, "Token rejected by GitHub." + _gist_auth_help(401)

            user_resp.raise_for_status()
            login = user_resp.json().get("login", "unknown")

            gist_resp = requests.get(self.api_url, headers=self._headers(), timeout=20)
            if gist_resp.status_code == 404:
                return False, f"Gist `{self.gist_id}` not found. Check GIST_ID."
            if gist_resp.status_code == 401:
                return (
                    False,
                    f"Token for `{login}` cannot access gist `{self.gist_id}`."
                    + _gist_auth_help(401),
                )
            gist_resp.raise_for_status()
            return True, f"Connected as `{login}`"
        except requests.RequestException as exc:
            return False, f"GitHub API error: {exc}"

    def load(self) -> dict[str, list]:
        if not self.enabled:
            return dict(EMPTY_STORAGE)

        ok, message = self.test_connection()
        if not ok:
            st.error(message)
            return dict(EMPTY_STORAGE)

        try:
            response = requests.get(self.api_url, headers=self._headers(), timeout=30)
            response.raise_for_status()
            files = response.json().get("files", {})
            for meta in files.values():
                if meta.get("filename") == GIST_DATA_FILE:
                    raw = requests.get(meta["raw_url"], timeout=30)
                    raw.raise_for_status()
                    data = json.loads(raw.text)
                    return _normalize_storage(data)
            return dict(EMPTY_STORAGE)
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else 0
            st.error(f"Could not load Gist data: {exc}.{_gist_auth_help(status)}")
            return dict(EMPTY_STORAGE)
        except Exception as exc:
            st.error(f"Could not load Gist data: {exc}")
            return dict(EMPTY_STORAGE)

    def save(self, data: dict[str, list]) -> bool:
        if not self.enabled:
            return False

        ok, message = self.test_connection()
        if not ok:
            st.error(message)
            return False

        try:
            response = requests.get(self.api_url, headers=self._headers(), timeout=30)
            response.raise_for_status()
            files = response.json().get("files", {})
            files[GIST_DATA_FILE] = {
                "content": json.dumps(data, indent=2, default=str),
            }
            payload = {
                "files": files,
                "description": (
                    "Donchian Strategy Data — "
                    f"updated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                ),
            }
            response = requests.patch(
                self.api_url, json=payload, headers=self._headers(), timeout=30
            )
            response.raise_for_status()
            return True
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else 0
            st.error(f"Could not save to Gist: {exc}.{_gist_auth_help(status)}")
            return False
        except Exception as exc:
            st.error(f"Could not save to Gist: {exc}")
            return False


def _normalize_storage(data: dict[str, Any]) -> dict[str, list]:
    blocked = data.get("blocked", data.get("ineligible", []))
    return {
        "watchlist": list(data.get("watchlist", [])),
        "positions": list(data.get("positions", [])),
        "buy_signals": list(data.get("buy_signals", [])),
        "history": list(data.get("history", [])),
        "blocked": list(blocked),
        "sheet_status": dict(data.get("sheet_status", {})),
    }


def load_storage() -> dict[str, list]:
    if "storage_data" not in st.session_state:
        gist = GistStorage()
        if gist.enabled:
            st.session_state.storage_data = gist.load()
        else:
            st.session_state.storage_data = {
                "watchlist": list(st.session_state.get("watchlist", [])),
                "positions": list(st.session_state.get("positions", [])),
                "buy_signals": [],
                "history": list(st.session_state.get("history", [])),
                "blocked": list(st.session_state.get("blocked", [])),
            }
    return _normalize_storage(st.session_state.storage_data)


def persist_storage(data: dict[str, list]) -> None:
    st.session_state.storage_data = data
    gist = GistStorage()
    if gist.enabled:
        if gist.save(data):
            st.success("Saved to GitHub Gist.")
    else:
        st.info("Gist not configured — data kept in this session only.")


# ─────────────────────────────────────────────────────────────────────────────
# yfinance data and Donchian signals
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=3600)
def fetch_ohlcv(symbols: tuple[str, ...], period: str) -> tuple[pd.DataFrame, tuple[str, ...]]:
    """Download daily OHLCV for all symbols via yfinance."""
    if not symbols:
        return pd.DataFrame(), tuple()

    raw = yf.download(
        list(symbols),
        period=period,
        interval="1d",
        auto_adjust=False,
        group_by="ticker",
        threads=True,
        progress=False,
    )

    if raw.empty:
        return pd.DataFrame(), tuple(symbols)

    rows: list[pd.DataFrame] = []
    failed: list[str] = []

    multi = isinstance(raw.columns, pd.MultiIndex)

    for symbol in symbols:
        try:
            if multi:
                if symbol not in raw.columns.get_level_values(0):
                    failed.append(symbol)
                    continue
                sym_df = raw[symbol].copy()
            else:
                sym_df = raw.copy()

            sym_df = sym_df.dropna(subset=["Close"]).reset_index()
            if sym_df.empty:
                failed.append(symbol)
                continue

            sym_df["Symbol"] = symbol
            rows.append(sym_df[["Date", "Symbol", "Open", "High", "Low", "Close"]])
        except Exception:
            failed.append(symbol)

    if not rows:
        return pd.DataFrame(), tuple(failed)

    master = pd.concat(rows, ignore_index=True)
    master["Date"] = pd.to_datetime(master["Date"])
    return master.sort_values(["Symbol", "Date"]), tuple(failed)


def compute_previous_day_donchian(df: pd.DataFrame, period: int = DONCHIAN_PERIOD) -> pd.DataFrame:
    """
    One row per symbol: latest session close vs DC20 bands computed from the
    prior `period` sessions (excluding the signal day).
    """
    rows: list[dict[str, Any]] = []

    for symbol in df["Symbol"].unique():
        sym_df = df.loc[df["Symbol"] == symbol].sort_values("Date")
        if len(sym_df) < period + 1:
            continue

        signal_row = sym_df.iloc[-1]
        close = float(signal_row["Close"])
        if not (PRICE_FILTER_MIN <= close <= PRICE_FILTER_MAX):
            continue

        prior = sym_df.iloc[:-1].tail(period)
        if len(prior) < period:
            continue

        dc_upper = float(prior["High"].max())
        dc_lower = float(prior["Low"].min())

        if close > dc_upper:
            status = "above_upper"
        elif close < dc_lower:
            status = "below_lower"
        else:
            status = "inside"

        rows.append(
            {
                "Symbol": symbol,
                "Date": signal_row["Date"].strftime("%Y-%m-%d"),
                "Close": round(close, 2),
                "DC_Upper": round(dc_upper, 2),
                "DC_Lower": round(dc_lower, 2),
                "Status": status,
            }
        )

    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# Strategy engine
# ─────────────────────────────────────────────────────────────────────────────
def process_strategy(
    signals: pd.DataFrame, storage: dict[str, list]
) -> dict[str, list]:
    """
    Rules:
    1. Watchlist: yesterday close < yesterday DC20 lower (fresh breakdown required
       if symbol was blocked after a prior buy cycle).
    2. Buy: in watchlist and yesterday close > yesterday DC20 upper.
    3. Remove from watchlist when bought.
    4. Exit: CMP >= buy price * EXIT_MULTIPLIER → history.
    5. Block re-entry until the next fresh breakdown.
    """
    watchlist = list(storage.get("watchlist", []))
    positions = list(storage.get("positions", []))
    history = list(storage.get("history", []))
    buy_signals = []
    blocked = set(storage.get("blocked", []))

    watchlist_symbols = {entry["symbol"] for entry in watchlist}
    position_symbols = {pos["symbol"] for pos in positions}

    price_by_symbol = signals.set_index("Symbol")["Close"].to_dict()
    date_by_symbol = signals.set_index("Symbol")["Date"].to_dict()

    breakdowns = signals.loc[signals["Status"] == "below_lower"]
    for _, row in breakdowns.iterrows():
        symbol = row["Symbol"]
        if symbol in position_symbols:
            continue

        if symbol in blocked:
            blocked.remove(symbol)

        if symbol in watchlist_symbols:
            for entry in watchlist:
                if entry["symbol"] == symbol:
                    entry["breakdown_date"] = row["Date"]
                    entry["breakdown_price"] = row["Close"]
            continue

        watchlist.append(
            {
                "symbol": symbol,
                "breakdown_date": row["Date"],
                "breakdown_price": row["Close"],
            }
        )
        watchlist_symbols.add(symbol)

    recoveries = signals.loc[
        (signals["Status"] == "above_upper") & (signals["Symbol"].isin(watchlist_symbols))
    ]
    watchlist_by_symbol = {entry["symbol"]: entry for entry in watchlist}

    for _, row in recoveries.iterrows():
        symbol = row["Symbol"]
        wl_entry = watchlist_by_symbol.get(symbol)
        if not wl_entry:
            continue

        buy_signals.append({"symbol": symbol, "buy_date": row["Date"], "buy_price": row["Close"]})

        positions.append(
            {
                "symbol": symbol,
                "breakdown_date": wl_entry["breakdown_date"],
                "buy_date": row["Date"],
                "buy_price": row["Close"],
                "current_cmp": row["Close"],
                "days_held": 0,
            }
        )
        position_symbols.add(symbol)
        blocked.add(symbol)
        watchlist = [entry for entry in watchlist if entry["symbol"] != symbol]
        watchlist_symbols.discard(symbol)

    active_positions: list[dict[str, Any]] = []
    for pos in positions:
        symbol = pos["symbol"]
        if symbol not in price_by_symbol:
            active_positions.append(pos)
            continue

        cmp_price = price_by_symbol[symbol]
        signal_date = date_by_symbol[symbol]
        buy_date = datetime.strptime(pos["buy_date"], "%Y-%m-%d")
        signal_dt = datetime.strptime(signal_date, "%Y-%m-%d")

        pos["current_cmp"] = cmp_price
        pos["days_held"] = max((signal_dt - buy_date).days, 0)

        exit_target = pos["buy_price"] * EXIT_MULTIPLIER
        if cmp_price >= exit_target:
            profit_pct = ((cmp_price - pos["buy_price"]) / pos["buy_price"]) * 100
            history.append(
                {
                    "symbol": symbol,
                    "breakdown_date": pos["breakdown_date"],
                    "buy_date": pos["buy_date"],
                    "exit_date": signal_date,
                    "holding_days": pos["days_held"],
                    "profit_pct": round(profit_pct, 2),
                }
            )
            blocked.add(symbol)
        else:
            active_positions.append(pos)

    return {
        "watchlist": watchlist,
        "positions": active_positions,
        "buy_signals": buy_signals,
        "history": history,
        "blocked": sorted(blocked),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Display helpers
# ─────────────────────────────────────────────────────────────────────────────
def _format_currency(value: float) -> str:
    return f"₹{value:,.2f}"


def watchlist_table(entries: list[dict[str, Any]]) -> pd.DataFrame:
    if not entries:
        return pd.DataFrame()
    df = pd.DataFrame(entries)
    df = df.rename(
        columns={
            "symbol": "Symbol",
            "breakdown_date": "Breakdown Date",
            "breakdown_price": "Breakdown Price",
        }
    )
    if "Breakdown Price" in df.columns:
        df["Breakdown Price"] = df["Breakdown Price"].map(_format_currency)
    return df


def positions_table(entries: list[dict[str, Any]]) -> pd.DataFrame:
    if not entries:
        return pd.DataFrame()
    df = pd.DataFrame(entries).copy()
    df["exit_target"] = df["buy_price"] * EXIT_MULTIPLIER
    df["pnl_pct"] = ((df["current_cmp"] - df["buy_price"]) / df["buy_price"] * 100).round(2)
    df = df.rename(
        columns={
            "symbol": "Symbol",
            "breakdown_date": "Breakdown Date",
            "buy_date": "Buy Date",
            "buy_price": "Buy Price",
            "current_cmp": "Current CMP",
            "days_held": "Days Held",
            "exit_target": "Exit Target",
            "pnl_pct": "P&L %",
        }
    )
    for col in ("Buy Price", "Current CMP", "Exit Target"):
        if col in df.columns:
            df[col] = df[col].map(_format_currency)
    if "P&L %" in df.columns:
        df["P&L %"] = df["P&L %"].map("{:.2f}%".format)
    return df


def history_table(entries: list[dict[str, Any]]) -> pd.DataFrame:
    if not entries:
        return pd.DataFrame()
    df = pd.DataFrame(entries)
    df = df.rename(
        columns={
            "symbol": "Symbol",
            "breakdown_date": "Breakdown Date",
            "buy_date": "Buy Date",
            "exit_date": "Exit Date",
            "holding_days": "Holding Days",
            "profit_pct": "Profit %",
        }
    )
    if "Profit %" in df.columns:
        df["Profit %"] = df["Profit %"].map("{:.2f}%".format)
    return df.sort_values("Exit Date", ascending=False)


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Donchian Strategy")
    st.caption(f"{len(NIFTY250_SYMBOLS)} symbols · yfinance · GitHub Gist")

    st.markdown("#### GitHub Gist")
    st.caption("Configure in Streamlit Cloud → Settings → Secrets.")

    gist_storage = GistStorage()
    if gist_storage.enabled:
        connected, status_msg = gist_storage.test_connection()
        if connected:
            st.success(status_msg)
        else:
            st.error(status_msg)
    else:
        st.warning("Add `GIST_ID` and `GITHUB_TOKEN` to secrets.")

    with st.expander("Credential override (local dev)"):
        with st.form("gist_credentials"):
            gist_id_input = st.text_input("Gist ID")
            token_input = st.text_input("GitHub Token", type="password")
            apply_creds = st.form_submit_button("Apply overrides")
            clear_creds = st.form_submit_button("Clear overrides")

        if apply_creds:
            if gist_id_input.strip():
                st.session_state["cfg_gist_id"] = gist_id_input.strip()
            if token_input.strip():
                st.session_state["cfg_github_token"] = token_input.strip()
            st.session_state.pop("storage_data", None)
            st.rerun()

        if clear_creds:
            st.session_state.pop("cfg_gist_id", None)
            st.session_state.pop("cfg_github_token", None)
            st.session_state.pop("storage_data", None)
            st.rerun()

    st.markdown(
        """
**Token setup**
1. GitHub → Settings → Developer settings → **Tokens (classic)**
2. Generate token with **`gist`** scope only
3. Create a gist at [gist.github.com](https://gist.github.com)
4. Paste Gist ID + token into secrets:

```
GIST_ID = 71e6096d03b9bbb9c586d45d067be413
GITHUB_TOKEN = ghp_xxxxxxxxxxxx
```

Fine-grained tokens do **not** work with the Gist API.
"""
    )

    st.markdown("---")
    st.markdown("#### Market Data")
    history_period = st.selectbox(
        "Price history",
        options=["6mo", "1y", "2y"],
        index=1,
        help="Needs at least 21 trading days for DC20.",
    )

    if st.button("Refresh market data", use_container_width=True):
        fetch_ohlcv.clear()
        st.rerun()

    st.markdown("---")
    st.markdown("#### Strategy Rules")
    st.markdown(
        f"""
- **Watchlist**: Close < DC{DONCHIAN_PERIOD} Lower
- **Buy**: Watchlist + Close > DC{DONCHIAN_PERIOD} Upper
- **Exit**: CMP ≥ Buy × {EXIT_MULTIPLIER}
- **Price filter**: ₹{PRICE_FILTER_MIN:,} – ₹{PRICE_FILTER_MAX:,}
- **Positions**: Unlimited
- **Re-entry**: Fresh breakdown only
"""
    )

    if st.button("Reload from Gist", use_container_width=True):
        st.session_state.pop("storage_data", None)
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
st.title("Donchian Channel Strategy")
st.markdown(
    f"Breakdown → recovery → exit on **{len(NIFTY250_SYMBOLS)} Nifty stocks** "
    "(yfinance OHLCV, previous-day DC20 signals)."
)

symbol_tuple = tuple(NIFTY250_SYMBOLS)

with st.spinner(f"Fetching OHLCV for {len(symbol_tuple)} symbols from yfinance..."):
    ohlcv_df, failed_symbols = fetch_ohlcv(symbol_tuple, history_period)

if ohlcv_df.empty:
    st.error("Could not fetch market data from yfinance. Check your network and try again.")
    st.stop()

loaded_symbols = ohlcv_df["Symbol"].nunique()
st.success(
    f"Loaded {len(ohlcv_df):,} bars · {loaded_symbols}/{len(symbol_tuple)} symbols"
)

if failed_symbols:
    with st.expander(f"{len(failed_symbols)} symbols failed to download"):
        st.write(", ".join(failed_symbols))

with st.spinner("Computing previous-day Donchian signals..."):
    signals = compute_previous_day_donchian(ohlcv_df)

if signals.empty:
    st.warning("No symbols passed Donchian / price filters.")
    st.stop()

signal_date = signals["Date"].mode().iloc[0] if not signals.empty else "—"
st.success(f"Signals for {len(signals)} symbols · latest session {signal_date}")

storage = load_storage()
with st.spinner("Running strategy..."):
    updated = process_strategy(signals, storage)

if json.dumps(updated, sort_keys=True, default=str) != json.dumps(
    storage, sort_keys=True, default=str
):
    persist_storage(updated)
else:
    st.session_state.storage_data = updated

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Watchlist", len(updated["watchlist"]))
c2.metric("Buy Today", len(updated.get("buy_signals", [])))
c3.metric("Positions", len(updated["positions"]))
c4.metric("History", len(updated["history"]))
c5.metric("Below Lower", int((signals["Status"] == "below_lower").sum()))

tab_wl, tab_buy, tab_pos, tab_hist, tab_sig = st.tabs(
    ["Watchlist", "Buy Today", "Positions", "History", "Signals"]
)

with tab_wl:
    st.subheader("Watchlist")
    st.caption("Previous session Close < DC20 Lower")
    wl_df = watchlist_table(updated["watchlist"])
    if wl_df.empty:
        st.info("Watchlist is empty.")
    else:
        st.dataframe(wl_df, use_container_width=True, hide_index=True)


with tab_buy:
    st.subheader("Today's Buy Signals")
    buys = updated.get("buy_signals", [])
    if not buys:
        st.info("No buy signals today.")
    else:
        df = pd.DataFrame(buys).rename(columns={
            "symbol":"Symbol",
            "buy_date":"Buy Date",
            "buy_price":"Buy Price"
        })
        df["Buy Price"] = df["Buy Price"].map(_format_currency)
        st.dataframe(df, use_container_width=True, hide_index=True)

with tab_pos:
    st.subheader("Active Positions")
    st.caption("Unlimited positions · exit at 6.28% above buy price")
    pos_df = positions_table(updated["positions"])
    if pos_df.empty:
        st.info("No open positions.")
    else:
        st.dataframe(pos_df, use_container_width=True, hide_index=True)

with tab_hist:
    st.subheader("Exit History")
    hist_df = history_table(updated["history"])
    if hist_df.empty:
        st.info("No completed trades yet.")
    else:
        st.dataframe(hist_df, use_container_width=True, hide_index=True)

with tab_sig:
    st.subheader("Previous-Day Donchian Signals")
    m1, m2, m3 = st.columns(3)
    m1.metric("Above Upper", int((signals["Status"] == "above_upper").sum()))
    m2.metric("Below Lower", int((signals["Status"] == "below_lower").sum()))
    m3.metric("Inside Channel", int((signals["Status"] == "inside").sum()))

    display = signals.copy()
    display = display.rename(
        columns={
            "Symbol": "Symbol",
            "Date": "Signal Date",
            "Close": "Close",
            "DC_Upper": "DC Upper",
            "DC_Lower": "DC Lower",
            "Status": "Status",
        }
    )
    display["Close"] = display["Close"].map(_format_currency)
    display["DC Upper"] = display["DC Upper"].map(_format_currency)
    display["DC Lower"] = display["DC Lower"].map(_format_currency)
    st.dataframe(display, use_container_width=True, hide_index=True, height=420)

st.markdown("---")
st.caption(
    "Universe: Nifty 250 symbol list. Prices from yfinance. "
    "State persists in GitHub Gist when GIST_ID and GITHUB_TOKEN are set."
)

# ============================================================
# GOOGLE SHEET - BUY/AVERAGE OUT
# ============================================================

st.markdown("---")
st.header("📈 CAR Buy/Average Out")

CSV_URL = "https://docs.google.com/spreadsheets/d/1wopIdWgQMfBIJ9DnKcGDVmdDM2JiV06HgZLEkNUZaKk/export?format=csv&gid=1924424194"

try:

    # Header starts on second row
    sheet = pd.read_csv(CSV_URL, header=1)

    storage = load_storage()

    if "sheet_status" not in storage:
        storage["sheet_status"] = {}

    status_store = storage["sheet_status"]

    now = datetime.now().strftime("%d-%b-%Y %H:%M")

    rows = []

    for _, row in sheet.iterrows():

        symbol = str(row["NSE Code"]).replace("NSE:", "").strip()

        rating = str(row["Cumulative Average Rule (CAR) Rating"]).strip()

        # create if first time
        if symbol not in status_store:

            status_store[symbol] = {
                "rating": rating,
                "changed_on": now
            }

        # update only when rating changes
        elif status_store[symbol]["rating"] != rating:

            status_store[symbol]["rating"] = rating
            status_store[symbol]["changed_on"] = now

        # Show only actionable stocks
        if rating == "Buy/Average Out":

            rows.append({
                "Symbol": symbol,
                "CAR Rating": rating,
                "Status Changed On":
                    status_store[symbol]["changed_on"]
            })

    storage["sheet_status"] = status_store
    persist_storage(storage)

    if rows:

        display = pd.DataFrame(rows)

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
            height=500
        )

    else:
        st.info("No Buy/Average Out stocks today.")

except Exception as e:
    st.error(e)
