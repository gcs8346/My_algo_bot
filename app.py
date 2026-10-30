import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
import urllib.parse

st.set_page_config(page_title="Topu Upstox Live - No Trap", layout="wide")
st.title("🔥 Topu Upstox Live - No Trap V9 Fixed")
st.caption("Direct Upstox API - No Yfinance, No Delay")

# === SIDEBAR - TERA TOKEN ===
st.sidebar.header("Topu ka Upstox Setup")
access_token = st.sidebar.text_input("Upstox Access Token Daal (6 8 7 8 wala)", type="password")
display_timeframe = st.sidebar.selectbox("Timeframe (Display)", ["1minute", "5minute", "15minute"], index=1)
refresh_sec = st.sidebar.slider("Auto Refresh (sec)", 5, 60, 10)

# Upstox Instrument Keys - Sahi wale
SYMBOLS = {
    "NIFTY": "NSE_INDEX|Nifty 50",
    "SENSEX": "BSE_INDEX|SENSEX",
    "RELIANCE": "NSE_EQ|INE002A01018",
    # "CRUDE MCX": "MCX_FO|CRUDEOIL25NOVFUT" # Isko har month update karna padta hai
}

if not access_token:
    st.warning("Bhai token daal de sidebar me, tabhi live chalega!")
    st.stop()

headers = {
    'Authorization': f'Bearer {access_token}',
    'Accept': 'application/json'
}

def get_upstox_candles(instrument_key, display_interval):
    try:
        # Upstox intraday sirf 1minute leta hai, baaki hum resample karenge
        api_interval = "1minute"
        
        # | ko encode karna zaroori hai
        encoded_key = urllib.parse.quote(instrument_key, safe='')
        
        url_intra = f"https://api.upstox.com/v2/historical-candle/intraday/{encoded_key}/{api_interval}"
        
        resp = requests.get(url_intra, headers=headers)
        data = resp.json()
        
        if 'data' in data and 'candles' in data['data']:
            candles = data['data']['candles']
            df = pd.DataFrame(candles, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'OI'])
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            df = df.sort_values('Timestamp')
            df.set_index('Timestamp', inplace=True)

            # Ab 1min ko 5min / 15min me convert karo
            if display_interval == "5minute":
                df = df.resample('5min').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum','OI':'last'}).dropna().reset_index()
            elif display_interval == "15minute":
                df = df.resample('15min').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum','OI':'last'}).dropna().reset_index()
            else:
                df = df.reset_index()
            
            return df
        else:
            st.error(f"Upstox Error: {data}")
            return None
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

def check_signal(df):
    if df is None or len(df) < 25:
        return None
    
    df['EMA9'] = df['Close'].ewm(span=9).mean()
    df['EMA21'] = df['Close'].ewm(span=21).mean()
    df['Vol_SMA'] = df['Volume'].rolling(20).mean()
    
    # RSI Fixed
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    last = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]

    volume_ok = last['Volume'] > last['Vol_SMA'] * 0.8
    price_up = last['Close'] > prev['Close']
    oi_up = last['OI'] > prev['OI'] if 'OI' in df.columns else True
    oi_fake_bullish = price_up and not oi_up
    
    lower_wick = min(prev2['Open'], prev2['Close']) - prev2['Low']
    body_range = prev2['High'] - prev2['Low']
    is_sweep = lower_wick > body_range * 0.6 if body_range>0 else False

    buy_cross = (prev['EMA9'] < prev['EMA21']) and (last['EMA9'] > last['EMA21'])
    sell_cross = (prev['EMA9'] > prev['EMA21']) and (last['EMA9'] < last['EMA21'])

    signal = "WAIT"
    reason = "Market dekh raha hu..."

    if buy_cross and last['RSI'] > 55 and volume_ok and not oi_fake_bullish:
        if last['Close'] > prev['High']:
            signal = "BUY"
            reason = f"No Trap BUY - OI {last['OI']} up hai, Volume OK"
    elif sell_cross and last['RSI'] < 45 and volume_ok:
        if last['Close'] < prev['Low']:
            signal = "SELL"
            reason = f"SELL - OI confirm"

    if oi_fake_bullish:
        reason = f"TRAP! Price up par OI down ({last['OI']}) - Mat le entry"
    elif is_sweep:
        reason = "TRAP! Abhi Stop Hunt hua - 1 candle wait"

    return last['Close'], last['EMA9'], last['EMA21'], last['RSI'], last['OI'], signal, reason

# === LIVE DASHBOARD ===
placeholder = st.empty()
with placeholder.container():
    cols = st.columns(3)
    for i, (name, key) in enumerate(SYMBOLS.items()):
        df = get_upstox_candles(key, display_timeframe)
        if df is None: continue
        result = check_signal(df)
        if result is None: continue
        price, ema9, ema21, rsi, oi, signal, reason = result
        with cols[i]:
            st.subheader(f"{name} ({display_timeframe})")
            st.metric("Live Price", f"{price:.2f}", f"RSI {rsi:.1f} | OI {oi}")
            if signal == "BUY": st.success(f"🟢 {signal} - {reason}")
            elif signal == "SELL": st.error(f"🔴 {signal} - {reason}")
            else: st.warning(f"🟡 {signal} - {reason}")
            st.caption(f"Updated: {datetime.now().strftime('%H:%M:%S')}")

time.sleep(refresh_sec)
st.rerun()