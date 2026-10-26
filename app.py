import streamlit as st
import requests
import time
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="TOWER V70 FINAL", layout="wide")

# --- STYLE ---
st.markdown("""
<style>
.stApp {background:#0a0a0a; color:white;}
.ganesh-box {text-align:center; background:#1a1a1a; padding:15px; border-radius:15px; border:1px solid #FFD700; margin-bottom:15px;}
.card {background:#151515; padding:14px; border-radius:12px; border:1px solid #333; text-align:center;}
.bull {background:#00ff88; color:black; padding:14px; border-radius:12px; font-weight:900; font-size:22px; text-align:center; margin-top:12px;}
.bear {background:#ff0040; color:white; padding:14px; border-radius:12px; font-weight:900; font-size:22px; text-align:center; margin-top:12px;}
</style>
""", unsafe_allow_html=True)

# --- GANESH HEADER - BINA PIL KE ---
st.markdown('<div class="ganesh-box">', unsafe_allow_html=True)
try:
    st.image("ganesh.png", use_container_width=True)
except:
    try:
        st.image("image_20261026_171405.webp", use_container_width=True)
    except:
        st.markdown("### 🙏 जय श्री गणेशाय नमः 🙏")
        st.markdown("### Jai Shri Ganeshay Namah")

st.markdown("#### 🏰 TOWER V70 - FINAL - NUMBER 1")
st.markdown("##### ॐ गं गणपतये नमः")
st.markdown('</div>', unsafe_allow_html=True)

def beep_box():
    st.markdown("""
    <div style="border:2px solid #00ff88; background:#111; padding:10px; border-radius:12px; text-align:center;">
    <b style="color:#00ff88;">🔊 SIGNAL BAJA!</b>
    <audio autoplay controls style="width:100%; margin-top:6px;">
    <source src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" type="audio/ogg">
    </audio></div>""", unsafe_allow_html=True)

with st.container(border=True):
    c1,c2,c3 = st.columns(3)
    sound_on = c1.toggle("Sound ON", value=True, key="sound_v70")
    c2.caption("Phone volume full rakho")
    if c3.button("🔊 TEST BEEP", key="test_v70"):
        beep_box()

# --- TOKEN FIX - AB ATKEGA NAHI ---
raw = st.text_input("🔑 Upstox Token (Roz Naya)", type="password", key="token_v70")
if raw:
    token = raw.strip().replace("Bearer ", "").replace("bearer ", "").replace('"','').replace("'","").strip()
    if "last_tok" not in st.session_state or st.session_state["last_tok"] != token:
        if sound_on: beep_box()
        st.session_state["last_tok"] = token
    st.session_state["tok"] = token
    st.caption(f"Token pakda: {len(token)} chars")
else:
    token = st.session_state.get("tok", "")

if not token:
    st.warning("Token daal bhai - niche wala box me")
    st.stop()
if len(token) < 50:
    st.error(f"Token chhota hai {len(token)} chars - pura copy kar, Bearer mat laga")
    st.stop()

headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

speed = st.selectbox("Speed", ["0.1 sec (100ms)", "0.8 sec (FAST)", "2.0 sec (SAFE)"], index=1)
speed_val = 0.1 if "0.1" in speed else 0.8 if "0.8" in speed else 2.0

indices = ["NSE_INDEX|Nifty 50","NSE_INDEX|Nifty Bank","BSE_INDEX|Sensex"]
stocks = ["NSE_EQ|RELIANCE","NSE_EQ|TCS","NSE_EQ|INFY","NSE_EQ|HDFCBANK","NSE_EQ|ICICIBANK","NSE_EQ|SBIN","NSE_EQ|BHARTIARTL","NSE_EQ|ITC","NSE_EQ|LT","NSE_EQ|KOTAKBANK","NSE_EQ|AXISBANK","NSE_EQ|BAJFINANCE","NSE_EQ|ASIANPAINT","NSE_EQ|MARUTI","NSE_EQ|WIPRO","NSE_EQ|HCLTECH","NSE_EQ|SUNPHARMA","NSE_EQ|TITAN","NSE_EQ|ULTRACEMCO","NSE_EQ|POWERGRID","NSE_EQ|NTPC","NSE_EQ|ONGC","NSE_EQ|TATAMOTORS","NSE_EQ|TATASTEEL","NSE_EQ|JSWSTEEL","NSE_EQ|HINDALCO","NSE_EQ|COALINDIA","NSE_EQ|ADANIENT","NSE_EQ|ADANIPORTS","NSE_EQ|BAJAJFINSV","NSE_EQ|BAJAJ-AUTO","NSE_EQ|BPCL","NSE_EQ|BRITANNIA","NSE_EQ|CIPLA","NSE_EQ|DIVISLAB","NSE_EQ|DRREDDY","NSE_EQ|EICHERMOT","NSE_EQ|GRASIM","NSE_EQ|HEROMOTOCO","NSE_EQ|HINDUNILVR","NSE_EQ|INDUSINDBK","NSE_EQ|M&M","NSE_EQ|NESTLEIND","NSE_EQ|SBILIFE","NSE_EQ|SHREECEM","NSE_EQ|TATACONSUM","NSE_EQ|TECHM","NSE_EQ|UPL","NSE_EQ|HDFCLIFE"]

def get_ltp(key):
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
        return None, f"Fail {r.status_code}"
    except Exception as e:
        return None, str(e)

def get_bulk_ltp(all_keys):
    try:
        joined = ",".join(all_keys)
        r = requests.get("https://api.upstox.com/v3/market-quote/ltp", headers=headers, params={"instrument_key": joined}, timeout=10)
        if r.status_code == 200: return r.json().get("data", {})
        r2 = requests.get("https://api.upstox.com/v2/market-quote/ltp", headers=headers, params={"instrument_key": joined}, timeout=10)
        if r2.status_code == 200: return r2.json().get("data", {})
    except: pass
    return {}

def get_df(key):
    ck = f"c_{key}"; tk = f"t_{key}"; now = time.time()
    if ck in st.session_state and now - st.session_state.get(tk, 0) < 60:
        return st.session_state[ck]
    try:
        r = requests.get(f"https://api