import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="V105 FINAL NO.1", layout="wide")
st.title("V105 - NIFTY FINAL 🔥 SCALP + FIRE")
st.caption("2/10 pe SCALP | 6/10 pe STRONG | 10/10 pe FIRE | 1-MIN | 2 Sec Refresh")

if "tok" not in st.session_state:
    st.session_state.tok = ""

token_input = st.text_input("Upstox Token v3 daal (Roz Naya)", type="password")
if token_input and len(token_input.strip()) > 50:
    st.session_state.tok = token_input.strip().replace("Bearer ", "").strip()

token = st.session_state.get("tok", "")
if not token or len(token) < 50:
    st.warning("Pehle Token daal")
    st.stop()

headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

INDICES = {
    "NIFTY 50": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
    "FINNIFTY": "NSE_INDEX|Nifty Fin Service",
    "SENSEX": "BSE_INDEX|SENSEX",
}
TOP_STOCKS = {
    "RELIANCE": "NSE_EQ|INE002A01018", "TCS": "NSE_EQ|INE467B01029",
    "INFY": "NSE_EQ|INE009A01021", "HDFCBANK": "NSE_EQ|INE040A01034",
    "ICICIBANK": "NSE_EQ|INE090A01021", "SBIN": "NSE_EQ|INE062A01020",
    "BHARTIARTL": "NSE_EQ|INE397D01024", "ITC": "NSE_EQ|INE154A01025",
    "LT": "NSE_EQ|INE018A01030", "KOTAKBANK": "NSE_EQ|INE237A01028",
    "AXISBANK": "NSE_EQ|INE238A01034", "BAJFINANCE": "NSE_EQ|INE296A01024",
    "MARUTI": "NSE_EQ|INE585B01010", "HCLTECH": "NSE_EQ|INE860A01027",
    "SUNPHARMA": "NSE_EQ|INE044A01036", "TATAMOTORS": "NSE_EQ|INE155A01022",
    "TITAN": "NSE_EQ|INE280A01028", "ASIANPAINT": "NSE_EQ|INE021A01026",
}
ALL = {**INDICES, **TOP_STOCKS}

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

def get_df(key, interval="1minute"):
    try:
        url = f"https://api.upstox.com/v3/historical-candle/intraday/{key}/{interval}"
        r = requests.get(url, headers=headers, timeout=12)
        if r.status_code == 200:
            c = r.json().get("data", {}).get("candles", [])
            if c and len(c) > 30:
                df = pd.DataFrame(c, columns=["ts","open","high","low","close","volume","oi"])
                return df.iloc[::-1].reset_index(drop=True)
    except: pass
    return None

def get_ltp_batch(all_keys):
    try:
        url = "https://api.upstox.com/v3/market-quote/ltp"
        params = {"instrument_key": ",".join(all_keys)}
        r = requests.get(url, headers=headers, params=params, timeout=12)
        if r.status_code == 200:
            return r.json().get("data", {})
    except: return {}
    return {}

@st.fragment(run_every=2)
def live_board():
    all_keys_list = list(ALL.values())
    ltp_data = get_ltp_batch(all_keys_list)
    if not ltp_data:
        st.info("📴 Market Closed - Last Close se signal check kar raha hu. Monday 9:15 se LIVE 1-MIN")

    for name, pipe_key in ALL.items():
        colon_key = pipe_key.replace("|", ":")
        q = ltp_data.get(colon_key) or ltp_data.get(pipe_key) or {}
        ltp = q.get("last_price", 0) if q else 0
        df = get_df(pipe_key, "1minute")
        if df is None or len(df) < 30:
            if ltp: st.markdown(f"**{name}** {ltp:.1f} - WAIT")
            continue

        close, high, low, vol = df["close"], df["high"], df["low"], df["volume"]
        e9 = ema(close, 9).iloc[-1]
        e21 = ema(close, 21).iloc[-1]
        e50 = ema(close, 50).iloc[-1]
        r_val = rsi(close).iloc[-1]
        atr_val = atr(df, 10).iloc[-1]
        live_price = ltp if ltp > 0 else close.iloc[-1]

        last_3_high = high.iloc[-4:-1].max()
        last_3_low = low.iloc[-4:-1].min()
        top_break = live_price > last_3_high
        bottom_break = live_price < last_3_low
        
        tp = (high + low + close) / 3
        vwap_val = (tp * vol).cumsum() / vol.cumsum() if vol.sum()>0 else close
        vwap_check = live_price > vwap_val.iloc[-1] if vol.sum()>0 else True
        vol_spike = vol.iloc[-1] > vol.iloc[-10:-1].mean() * 0.8
        bos_check = live_price > high.iloc[-10:-1].max() * 0.999
        st_check = live_price > e50

        checks = {
            "EMA9>21": e9 > e21, "Close>EMA9": live_price > e9,
            "RSI 52+": r_val > 52, "Supertrend": st_check,
            "Close>EMA50": live_price > e50, "TOP-BREAK(3C)": top_break,
            "VWAP": vwap_check, "Vol Spike": vol_spike,
            "BOS": bos_check, "Momentum": 50 < r_val < 75,
        }
        score = sum(checks.values())
        fast_scalp_core = (e9 > e21) and top_break and (live_price > e9)

        # --- YAHI HAI NAYA 3-LEVEL LOGIC ---
        if score >= 9:
            color, tag = "#00ff88", f"🔥🔥 {score}/10 FIRE BUY"
            call = f" | 🎯 {(live_price+atr_val*2):.1f} | SL {(live_price-atr_val):.1f} | HOLD"
        elif score >= 6:
            color, tag = "#00ff88", f"🔥 {score}/10 STRONG BUY"
            call = f" | 🎯 {(live_price+atr_val*1.5):.1f} | SL {(live_price-atr_val*0.8):.1f}"
        elif score >= 2 and fast_scalp_core:
            color, tag = "#00ffaa", f"⚡ {score}/10 SCALP BUY"
            call = f" | ⚡ SCALP TGT {(live_price+atr_val*0.8):.1f} | SL {(live_price-atr_val*0.5):.1f} | FAST"
        elif score <= 2 and bottom_break and r_val < 48:
            color, tag = "#ff4444", f"🔻 {score}/10 SCALP SELL"
            call = f" | SELL TGT {(live_price-atr_val*0.8):.1f}"
        else:
            color, tag = "#aaaaaa", f"💤 {score}/10 WAIT"
            call = ""

        sup = low.iloc[-20:].min()
        res = high.iloc[-20:].max()
        failed = [k for k,v in checks.items() if not v]

        st.markdown(f"### {name} - Rs.{live_price:.1f} - <span style='color:{color}'>{tag}</span>{call}", unsafe_allow_html=True)
        if score < 9:
            st.caption(f"Fail: {', '.join(failed) if failed else 'No'} | S:{sup:.0f} R:{res:.0f} | 3C High:{last_3_high:.0f} | RSI:{r_val:.0f}")
        else:
            st.caption(f"✅ 10/10 FIRE - S:{sup:.0f} R:{res:.0f} - TANATAN")
        st.divider()

    st.caption(f"Updated: {datetime.now().strftime('%H:%M:%S')}")

live_board()
