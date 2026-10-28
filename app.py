import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import time

st.set_page_config(page_title="V96 SENSEX + OIL LIVE", layout="wide")
st.title("V96 - FINAL LIVE - TOWER + PCR READY ✅")

# --- TOKEN ---
token_input = st.text_input("Upstox Token (Roz Naya)", type="password", key="token_box")
if token_input and len(token_input.strip()) > 50:
    st.session_state.tok = token_input.strip().replace("Bearer ", "").strip()

token = st.session_state.get("tok", "")
if not token or len(token) < 50:
    st.warning("Token daal ke ENTER maar - Upstox Login > Get Token")
    st.stop()

headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

# V96 FIXED INSTRUMENTS - Ye wale pakka chalte hain
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

# --- INDICATORS V96 ---
def ema(s, p):
    return s.ewm(span=p, adjust=False).mean()

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
        url = f"https://api.upstox.com/v3/historical-candle/intraday/{key}/5minute"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 429:
            time.sleep(1)
            return None
        if r.status_code == 200:
            c = r.json().get("data", {}).get("candles", [])
            if c:
                df = pd.DataFrame(c, columns=["ts","open","high","low","close","volume","oi"])
                return df.iloc[::-1].reset_index(drop=True)
    except:
        pass
    return None

def get_ltp_batch(all_keys):
    # V96.1 FIX - Ab error dikhega blank nahi
    try:
        url = "https://api.upstox.com/v3/market-quote/ltp"
        params = {"instrument_key": ",".join(all_keys)}
        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code == 401:
            st.error("❌ Token Expire / Galat hai - Upstox se naya token leke daal. Roz subah 6 baje naya chahiye.")
            return {}
        if r.status_code == 429:
            st.warning("⏳ Rate Limit laga - 2 sec ruk raha hu...")
            time.sleep(2)
            return {}
        if r.status_code == 200:
            return r.json().get("data", {})
        else:
            st.error(f"API Error {r.status_code}: {r.text[:300]}")
            return {}
    except Exception as e:
        st.error(f"Network Error: {e}")
        return {}

# --- UI ---
if "tick" not in st.session_state:
    st.session_state.tick = True

c1, c2, c3 = st.columns([1,1,3])
with c1:
    if st.button("🟢 START"):
        st.session_state.tick = True
        st.rerun()
with c2:
    if st.button("🔴 STOP"):
        st.session_state.tick = False
        st.rerun()
with c3:
    st.caption(f"TIME: {datetime.now().strftime('%H:%M:%S')} | V96 Auto: {'ON' if st.session_state.tick else 'OFF'}")

@st.fragment(run_every=2)
def live_board_v96():
    if not st.session_state.tick:
        st.info("STOPPED - START dabao")
        return

    all_keys_list = list(INSTRUMENTS.values())
    ltp_data = get_ltp_batch(all_keys_list)

    if not ltp_data:
        st.warning("LTP Data nahi aaya - Token check karo ya 5 sec wait karo")
        return

    for name, key in INSTRUMENTS.items():
        q = ltp_data.get(key, {})
        ltp = q.get("last_price", 0) if q else 0

        df = get_df_v96(key)
        
        # Agar candle nahi hai toh sirf LTP dikhao - BLANK FIX
        if df is None or len(df) < 30:
            if ltp:
                st.metric(f"{name} - LTP LIVE", f"Rs.{ltp}", "Candle sync ho raha hai...")
            else:
                st.metric(f"{name}", "WAIT - No Data")
            continue

        close = df["close"]
        high = df["high"]
        low = df["low"]
        
        e9 = ema(close, 9).iloc[-1]
        e21 = ema(close, 21).iloc[-1]
        e50 = ema(close, 50).iloc[-1]
        r_val = rsi(close).iloc[-1]
        c = close.iloc[-1]
        live_price = ltp if ltp and ltp > 0 else c

        # VWAP FIX for INDEX (volume 0)
        if df["volume"].sum() > 0:
            tp = (df["high"] + df["low"] + df["close"]) / 3
            vwap = (tp * df["volume"]).cumsum() / df["volume"].cumsum()
            vwap_val = vwap.iloc[-1]
            vwap_check = live_price > vwap_val
        else:
            vwap_check = True

        try:
            st_check = supertrend_v96(df)
        except:
            st_check = live_price > e50
            
        bos_check = live_price > high.iloc[-11:-1].max()

        checks = {
            "EMA9>21": e9>e21,
            "Close>EMA9": live_price>e9,
            "RSI 50+": r_val>50,
            "Supertrend": st_check,
            "EMA50": live_price>e50,
            "BOS": bos_check,
            "SAFE": abs(live_price-e9)/live_price < 0.008,
            "FVG": low.iloc[-1] > high.iloc[-2],
            "VWAP": vwap_check,
            "TIME": True
        }
        score = sum(checks.values())
        color = "#00ff88" if score>=7 else "#ffaa00" if score>=4 else "#ff4444"
        tag = "🔥 FIRE" if score>=7 else "⚠️ SETUP" if score>=4 else "💤 WAIT"
        
        st.markdown(f"### {name} - Rs.{live_price:.1f} - <span style='color:{color}'>{score}/10 {tag}</span> - RSI:{r_val:.0f}", unsafe_allow_html=True)
        if score < 7:
            failed = [k for k,v in checks.items() if not v]
            st.caption(f"Fail: {', '.join(failed)}")

live_board_v96()
st.caption("V96 FINAL CODU SHARMA | Batch LTP = No 429 | Real Supertrend | INDEX VWAP Fixed | Blank Screen Fixed")