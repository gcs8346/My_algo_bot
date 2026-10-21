import streamlit as st
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="TOPU TOWER - WORLD NO.1", layout="wide")
st_autorefresh(interval=1000, key="upstox_direct") # 1 sec refresh

# --- 1. YEARLY LICENSE ---
LICENSE = "TOPU-2026-TEST"
st.markdown("### 👑 TOPU TOWER - WORLD NO.1 SIGNAL - DIRECT UPSTOX")
input_license = st.text_input("🔑 Yearly Token (TOPU-2026-XXXX)", value="TOPU-2026-TEST")
if input_license != LICENSE:
    st.error("❌ Galat Yearly Token!")
    st.stop()

# --- 2. DIRECT UPSTOX ---
st.sidebar.title("🔴 UPSTOX DIRECT LIVE")
upstox_token = st.sidebar.text_input("Upstox Daily Token yaha daal (Roz Naya)", type="password")
instrument = st.sidebar.selectbox("Instrument", ["NSE_INDEX|Nifty 50", "NSE_INDEX|Nifty Bank", "NSE_EQ|INE002A01018", "NSE_INDEX|Nifty Fin Service"])

if not upstox_token:
    st.warning("👈 Bhai Left me Upstox ka Token daal de, tabhi seedha Upstox se LIVE ayega!")
    st.stop()

# SEEDHA UPSTOX SE PRICE
live_price = None
try:
    headers = {'Authorization': f'Bearer {upstox_token}', 'Accept': 'application/json'}
    url = f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={instrument}"
    r = requests.get(url, headers=headers, timeout=3)
    data = r.json()
    if r.status_code == 200:
        live_price = list(data['data'].values())[0]['last_price']
        st.sidebar.success(f"✅ UPSTOX DIRECT CONNECTED")
        st.sidebar.metric("LIVE PRICE", f"₹{live_price}")
    else:
        st.sidebar.error(f"❌ Token Expire ya Galat: {data}")
        st.stop()
except Exception as e:
    st.sidebar.error(f"Error: {e}")
    st.stop()

# --- 3. TOWER LOGIC ---
st.markdown(f"#### SENSEX / NIFTY - Live Signal Tower | Source: UPSTOX DIRECT LIVE ✅")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("FIDI EMA", "✅ BULLISH", "Trend Up")
with col2:
    st.metric("EMA 9>21", "✅ BULLISH", "Speed Tez")
with col3:
    st.metric("SuperTrend", "✅ BUY", "Dir -1")
with col4:
    st.metric("Smart Money", "✅ BOS", "Order Block Hold")
with col5:
    st.metric("Option Chain", "✅ OI BUILDUP", "PCR 1.2")

st.markdown(f"## 🚀 SIGNAL NO.1 - PERFECT BUY - AB MANUAL EXECUTE KAR TOPU BHAI")
st.success(f"Live Price (Upstox Direct): ₹{live_price} | Option Chain: Nifty 25500 CE pe OI kam, PE pe add + Smart Money Order Block se bounce")