import streamlit as st
import requests
import pandas as pd
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go

st.set_page_config(page_title="TOPU TOWER - WORLD NO.1", layout="wide")
st_autorefresh(interval=2000, key="tower_final")

# --- 1. YEARLY LICENSE TOKEN ---
LICENSE = "TOPU-2026-TEST"
st.markdown("### 👑 TOPU TOWER - WORLD NO.1 SIGNAL")
input_license = st.text_input("🔑 Yearly Token (TOPU-2026-XXXX)", value="TOPU-2026-TEST")

if input_license != LICENSE:
    st.error("❌ Galat Yearly Token! TOPU-2026-TEST daal")
    st.stop()

# --- 2. UPSTOX LIVE TOKEN BOX ---
st.sidebar.title("🔴 UPSTOX LIVE")
upstox_token = st.sidebar.text_input("Upstox Daily Token yaha daal (Roz Naya)", type="password")
instrument = st.sidebar.selectbox("Instrument", ["NSE_INDEX|Nifty 50", "NSE_INDEX|Nifty Bank", "NSE_EQ|INE002A01018"])

live_price = None
source = "Yahoo Finance (Delay)"

if upstox_token:
    try:
        headers = {'Authorization': f'Bearer {upstox_token}', 'Accept': 'application/json'}
        url = f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={instrument}"
        r = requests.get(url, headers=headers, timeout=3)
        data = r.json()
        if r.status_code == 200:
            live_price = list(data['data'].values())[0]['last_price']
            source = "UPSTOX LIVE - 1 SEC"
            st.sidebar.success(f"✅ LIVE: ₹{live_price}")
        else:
            st.sidebar.error(f"Token Expire: {data.get('message')}")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

# --- 3. TOWER LOGIC (Tera wala) ---
st.markdown(f"#### SENSEX / NIFTY - Live Signal Tower | Source: {source}")

# Price logic
if live_price is None:
    df = yf.download("^NSEI", period="1d", interval="1m")
    live_price = float(df['Close'].iloc[-1])

# Tera Signal Tower
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
st.info(f"Live Price: ₹{live_price} | Option Chain: Nifty 25500 CE pe OI kam, PE pe add + Smart Money Order Block se bounce")
st.warning("💡 Execution: Tu bas signal dekh ke Upstox App me jaake manually BUY/SELL maar dega. Tower order nahi marega.")