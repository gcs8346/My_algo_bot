import streamlit as st
import requests
import time
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="TOWER V47 ULTIMATE", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
.stApp {background:#0a0a0a; color:white;}
.card {background:#151515; padding:14px; border-radius:12px; border:1px solid #333; text-align:center; height:125px;}
.bull {background:#00ff88; color:black; padding:14px; border-radius:12px; font-weight:900; font-size:22px; text-align:center; margin-top:12px;}
.bear {background:#ff0040; color:white; padding:14px; border-radius:12px; font-weight:900; font-size:22px; text-align:center; margin-top:12px;}
.wait {background:#ffcc00; color:black; padding:14px; border-radius:12px; font-weight:900; font-size:20px; text-align:center; margin-top:12px;}
.ok {color:#00ff88; font-weight:700} .no {color:#ff0040; font-weight:700}
</style>
""", unsafe_allow_html=True)

st.markdown("### 🏰 TOWER V47 - SMART MONEY ULTIMATE - NUMBER 1")
st.caption("V46 + Sensex Fix + Bulk Scan | LIVE 0.1 sec")

# --- TOKEN CLEANER ---
raw = st.text_input("🔑 Upstox Token (Roz Naya)", type="password", key="v47_final_full")
if raw:
    token = raw.strip().replace("Bearer ", "").replace("bearer ", "").replace('"','').replace("'","").strip()
    st.session_state["tok"] = token
else:
    token = st.session_state.get("tok", "")

if not token or len(token) < 30:
    st.warning("Token daal bhai - wahi FAST wala")
    st.stop()

headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

speed = st.selectbox("Tik-Tik Speed", ["0.1 sec (100ms - SUPER FAST)", "0.8 sec (FASTEST)", "2.0 sec (SAFE)"], index=1)
speed_val = 0.1 if "0.1" in speed else 0.8 if "0.8" in speed else 2.0

# --- CORRECT INDEX LIST + STOCKS ---
indices = [
    "NSE_INDEX|Nifty 50",
    "NSE_INDEX|Nifty Bank",
    "NSE_INDEX|Nifty Financial Services",
    "NSE_INDEX|Nifty Midcap 100",
    "NSE_INDEX|Nifty IT",
    "NSE_INDEX|Nifty Pharma",
    "NSE_INDEX|Nifty Auto",
    "BSE_INDEX|Sensex"
]

stocks = ["NSE_EQ|RELIANCE","NSE_EQ|TCS","NSE_EQ|INFY","NSE_EQ|HDFCBANK","NSE_EQ|ICICIBANK","NSE_EQ|SBIN","NSE_EQ|BHARTIARTL","NSE_EQ|ITC","NSE_EQ|LT","NSE_EQ|KOTAKBANK","NSE_EQ|AXISBANK","NSE_EQ|BAJFINANCE","NSE_EQ|ASIANPAINT","NSE_EQ|MARUTI","NSE_EQ|WIPRO","NSE_EQ|HCLTECH","NSE_EQ|SUNPHARMA","NSE_EQ|TITAN","NSE_EQ|ULTRACEMCO","NSE_EQ|POWERGRID","NSE_EQ|NTPC","NSE_EQ|ONGC","NSE_EQ|TATAMOTORS","NSE_EQ|TATASTEEL","NSE_EQ|JSWSTEEL","NSE_EQ|HINDALCO","NSE_EQ|COALINDIA","NSE_EQ|ADANIENT","NSE_EQ|ADANIPORTS","NSE_EQ|BAJAJFINSV","NSE_EQ|BAJAJ-AUTO","NSE_EQ|BPCL","NSE_EQ|BRITANNIA","NSE_EQ|CIPLA","NSE_EQ|DIVISLAB","NSE_EQ|DRREDDY","NSE_EQ|EICHERMOT","NSE_EQ|GRASIM","NSE_EQ|HEROMOTOCO","NSE_EQ|HINDUNILVR","NSE_EQ|INDUSINDBK","NSE_EQ|M&M","NSE_EQ|NESTLEIND","NSE_EQ|SBILIFE","NSE_EQ|SHREECEM","NSE_EQ|TATACONSUM","NSE_EQ|TECHM","NSE_EQ|UPL","NSE_EQ|HDFCLIFE"]

# --- FUNCTIONS ---
def get_live_ltp(key):
    try:
        r = requests.get("https://api.upstox.com/v3/market-quote/ltp", headers=headers, params={"instrument_key": key}, timeout=6)
        if r.status_code == 200:
            d = r.json().get("data", {}).get(key, {}).get("last_price")
            if d: return d, f"V3 OK {r.status_code}"
        r2 = requests.get("https://api.upstox.com/v2/market-quote/ltp", headers=headers, params={"instrument_key": key}, timeout=6)
        if r2.status_code == 200:
            data = r2.json().get("data", {})
            price = data.get(key, {}).get("last_price") if key in data else list(data.values())[0].get("last_price") if data else None
            if price: return price, f"V2 OK {r2.status_code}"
        return None, f"Fail {r.status_code}/{r2.status_code}"
    except Exception as e:
        return None, str(e)

def get_bulk_ltp(all_keys):
    try:
        joined = ",".join(all_keys)
        r = requests.get("https://api.upstox.com/v3/market-quote/ltp", headers=headers, params={"instrument_key": joined}, timeout=10)
        if r.status_code == 200:
            return r.json().get("data", {})
        r2 = requests.get("https://api.upstox.com/v2/market-quote/ltp", headers=headers, params={"instrument_key": joined}, timeout=10)
        if r2.status_code == 200:
            return r2.json().get("data", {})
    except: pass
    return {}

def get_df(key):
    ck = f"c_{key}"; tk = f"t_{key}"; now = time.time()
    if ck in st.session_state and now - st.session_state.get(tk, 0) < 60:
        return st.session_state[ck]
    try:
        r = requests.get(f"https://api.upstox.com/v2/historical-candle/intraday/{key}/5minute", headers=headers, timeout=6)
        if r.status_code == 200:
            c = r.json().get("data", {}).get("candles", [])
            if c:
                df = pd.DataFrame(c, columns=["ts","open","high","low","close","volume","oi"]).sort_values("ts")
                st.session_state[ck] = df
                st.session_state[tk] = now
                return df
    except: pass
    return st.session_state.get(ck, pd.DataFrame())

def ultimate_score(df, spot):
    details = {}; tech = 0; smart = 0
    if df.empty or len(df) < 25:
        return 3, 3, 6, {"Candle kam hai - 60s me ayega": False}
    df["ema9"] = df["close"].ewm(span=9).mean()
    df["ema21"] = df["close"].ewm(span=21).mean()
    df["ema50"] = df["close"].ewm(span=50).mean()
    df["ema200"] = df["close"].ewm(span=200).mean()
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss.replace(0, 0.001)
    df["rsi"] = 100 - (100 / (1 + rs))
    df["tp"] = (df["high"] + df["low"] + df["close"]) / 3
    df["vwap"] = (df["tp"] * df["volume"]).cumsum() / df["volume"].cumsum()
    hl2 = (df["high"] + df["low"]) / 2
    atr = (df["high"] - df["low"]).rolling(10).mean()
    upper = hl2 + 3 * atr; lower = hl2 - 3 * atr
    st_trend = True
    for i in range(1, len(df)):
        if df["close"].iloc[i] > upper.iloc[i-1]: st_trend = True
        elif df["close"].iloc[i] < lower.iloc[i-1]: st_trend = False
    last = df.iloc[-1]
    recent_high = df["high"].iloc[-20:-1].max()
    recent_low = df["low"].iloc[-20:-1].min()
    swing_high = df["high"].iloc[-30:].max()
    swing_low = df["low"].iloc[-30:].min()
    
    c1 = last["ema9"] > last["ema21"] and last["ema21"] > last["ema50"]
    details["EMA9>21>50"] = c1
    if c1: tech += 1
    c2 = last["close"] > last["ema9"] and last["close"] > last["vwap"]
    details["Close>EMA9+VWAP"] = c2
    if c2: tech += 1
    c3 = 50 < last["rsi"] < 75
    details[f"RSI {last['rsi']:.1f} 50-75"] = c3
    if c3: tech += 1
    details["Supertrend BULL"] = st_trend
    if st_trend: tech += 1
    c5 = last["close"] > last["ema200"] or last["close"] > last["ema50"]
    details["Close>EMA50/200"] = c5
    if c5: tech += 1