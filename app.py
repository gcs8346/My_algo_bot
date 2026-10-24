import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from urllib.parse import quote
from datetime import datetime, timedelta
import time

st.set_page_config(layout="wide", page_title="Topu V35 1SEC")
st.title("🔥 Topu V35 - 1 SEC ULTRA TICK - FINAL LOCK")

# ===== SIDEBAR =====
st.sidebar.header("🔑 UPSTOX TOKEN BOX")
upstox_token = st.sidebar.text_input("Upstox Access Token", type="password")
is_token = len(upstox_token.strip()) > 30 if upstox_token else False
st.sidebar.write("🟢 TOKEN ON" if is_token else "🔴 TOKEN DALO")

st.sidebar.header("🔊 SOUND BOX V17")
enable_sound = st.sidebar.checkbox("Sound ON", True)
sound_entry = "https://cdn.pixabay.com/audio/2022/03/24/audio_1b9bd41700.mp3"
sound_exit = "https://cdn.pixabay.com/audio/2022/03/10/audio_c3c8a6faa7.mp3"

upstox_map = {
    "NIFTY 50": "NSE_INDEX|Nifty 50",
    "BANK NIFTY": "NSE_INDEX|Nifty Bank",
    "FIN NIFTY": "NSE_INDEX|Nifty Fin Service",
    "SENSEX": "BSE_INDEX|SENSEX",
    "NIFTY IT": "NSE_INDEX|Nifty IT",
    "MIDCAP": "NSE_INDEX|Nifty Mid Select"
}
selected = st.sidebar.selectbox("Index", list(upstox_map.keys()))
custom = st.sidebar.text_input("Stock Likh (RELIANCE)", "").strip().upper()
timeframe_ui = st.sidebar.selectbox("Timeframe", ["1minute","5minute","15minute","30minute","day"], index=2)

# TICK SPEED - TERA WALA 0-1 SEC
st.sidebar.header("⚡ TICK SPEED BOX")
tick_mode = st.sidebar.selectbox("Speed Chuno", ["1 SEC ULTRA FAST ⚡","2 SEC FAST","5 SEC SAFE"], index=0)
tick_map = {"1 SEC ULTRA FAST ⚡":1,"2 SEC FAST":2,"5 SEC SAFE":5}
tick_sec = tick_map[tick_mode]
auto_tick = st.sidebar.checkbox(f"TICK TICK ON ({tick_sec} sec)", True)

historical_map = {"1minute":"1minute","5minute":"1minute","15minute":"30minute","30minute":"30minute","day":"day"}

if not is_token:
    st.error("Topu No.1, Token dalo. Ye pure token wala hai.")
    st.stop()

def ema(s,n): return s.ewm(span=n, adjust=False).mean()

def rsi_fixed(s, n=14):
    delta = s.diff()
    gain = delta.where(delta>0, 0.0)
    loss = -delta.where(delta<0, 0.0)
    avg_gain = gain.ewm(alpha=1/n, min_periods=n, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/n, min_periods=n, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)

def supertrend_bull(df, p=10, m=3):
    hl2=(df['High']+df['Low'])/2
    atr=(df['High']-df['Low']).rolling(p).mean()
    return df['Close'] > (hl2 - m*atr)

def get_l