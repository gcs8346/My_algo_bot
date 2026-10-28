import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import time

st.set_page_config(page_title="V96 SENSEX + OIL LIVE", layout="wide")
st.title("V96 - FINAL LIVE - TOWER + PCR READY ✅")

# --- TOKEN ---
token_input = st.text_input("Upstox Token (Roz Naya)", type="password")
if token_input and len(token_input.strip()) > 50:
    st.session_state.tok = token_input.strip().replace("Bearer ", "").strip()

token = st.session_state.get("tok", "")
if not token or len(token) < 50:
    st.warning("Token daal ke ENTER maar")
    st.stop()

headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
st.success(f"Token OK ...{token[-10:]} | Time: {datetime.now().strftime('%H:%M:%S')}")

# --- INSTRUMENTS - Ye wale 100% chalte hain ---
INSTRUMENTS = {
    "SENSEX": "BSE_INDEX|SENSEX",
    "BANKEX": "BSE_INDEX|BANKEX",
    "NIFTY 50": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
    "RELIANCE": "NSE_EQ|INE002A01018",
    "GOLD": "MCX_FO|495213",
    "CRUDEOIL": "MCX_FO|573422",
    "SILVER": "MCX_FO|495214",
}

# --- INDICATORS ---
def ema(s, p): return s.ewm(span=p, adjust=False).mean()
def rsi(s, p=14):
    d = s.diff()
    g = d.where(d > 0, 0).rolling(p).mean()
    l = -d.where(d < 0, 0).rolling(p).mean()
    rs = g / l.replace(0, 0.001)
    return 100 - (100 / (1 + rs))
def atr(df, p=10):
    hl = df["high"] - df["low"]
    hc = (df["high"] - df["close"].shift()).abs()
    lc = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.rolling(p).mean()
def supertrend_v96(df):
    df = df.copy()
    df["atr"] = atr(df, 10)
    hl2 = (df["high"] + df["low"]) / 2
    df["upper"] = hl2 + (3 * df["atr"])
    df["lower"] = hl2 - (3 * df["atr"])
    df["st"] = np.where(df["close"] > df["upper"].shift(), df["lower"], df["upper"])
    return df["close"].iloc[-1] > df["st"].iloc[-1]

def get_df_v96(key):
    try:
        # 1. Intraday 5min
        url = f"https://api.upstox.com/v3/historical-candle/intraday/{key}/5minute"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            c = r.json().get("data", {}).get("candles", [])
            if c and len(c) > 5:
                df = pd.DataFrame(c, columns=["ts","open","high","low","close","volume","oi"])
                return df.iloc[::-1].reset_index(drop=True)
        # 2. Daily fallback - Market band ke baad ke liye
        url2 = f"https://api.upstox.com/v3/historical-candle/{key}/day/2026-10-27/2026-10-28"
        r2 = requests.get(url2, headers=headers, timeout=10)
        if r2.status_code == 200:
            c2 = r2.json().get("data", {}).get("candles", [])
            if c2:
                df = pd.DataFrame(c2, columns=["ts","open","high","low","close","volume","oi"])
                return df.iloc[::-1].reset_index(drop=True)
    except: pass
    return None

def get_ltp_batch(all_keys):
    try:
        url = "https://api.upstox.com/v3/market-quote/ltp"
        params = {"instrument_key": ",".join(all_keys)}
        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code == 401:
            st.error("❌ TOKEN EXPIRE - Naya token banao. Roz subah 6 baje expire hota hai.")
            with st.expander("API Response", expanded=True): st.code(r.text[:1000])
            return {}
        if r.status_code == 200:
            data = r.json().get("data", {})
            if not data:
                with st.expander("DEBUG - LTP Khali Aaya - Response", expanded=True):
                    st.code(r.text[:1500])
                    st.warning("Market band hai ya token me Market Quote permission nahi hai")
            return data
        else:
            st.error(f"API {r.status_code}")
            with st.expander("API Response", expanded=True): st.code(r.text[:1500])
            return {}
    except Exception as e:
        st.error(f"Network Error: {e}")
        return {}

# --- UI ---
if "tick" not in st.session_state: st.session_state.tick = True
c1,c2 = st.columns(2)
with c1:
    if st.button("🟢 START"): st.session_state.tick = True
with c2:
    if st.button("🔴 STOP"): st.session_state.tick = False

@st.fragment(run_every=3)
def live_board_v96():
    if not st.session_state.tick:
        st.info("STOPPED")
        return
    all_keys_list = list(INSTRUMENTS.values())
    ltp_data = get_ltp_batch(all_keys_list)
    if not ltp_data:
        st.warning("LTP Data nahi aaya - Upar DEBUG box dekho")
        return
    for name, key in INSTRUMENTS.items():
        q = ltp_data.get(key, {})
        ltp = q.get("last_price", 0) if q else 0
        df = get_df_v96(key)
        if df is None or len(df) < 10:
            if ltp: st.metric(f"{name}", f"Rs.{ltp}", "Candle WAIT - Market Closed?")
            else: st.metric(f"{name}", "WAIT", "No LTP + No Candle")
            continue
        close = df["close"]
        high = df["high"]
        low = df["low"]
        e9 = ema(close, 9).iloc[-1]
        e21 = ema(close, 21).iloc[-1]
        e50 = ema(close, 50).iloc[-1]
        r_val = rsi(close).iloc[-1]
        c = close.iloc[-1]