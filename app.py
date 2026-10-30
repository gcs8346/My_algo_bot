import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import urllib.parse

st.set_page_config(page_title="Topu Upstox Live V11.1", layout="wide")
st.title("🔥 Topu Upstox Live - No Trap V11.1 FINAL")
st.caption("Direct Upstox API - Pre-Market + Live")

st.sidebar.header("Topu ka Upstox Setup")
access_token = st.sidebar.text_input("Upstox Access Token Daal (6 8 7 8 wala)", type="password")
display_timeframe = st.sidebar.selectbox("Timeframe (Display)", ["1minute", "5minute", "15minute"], index=1)

SYMBOLS = {
    "NIFTY": "NSE_INDEX|Nifty 50",
    "SENSEX": "BSE_INDEX|SENSEX",
    "RELIANCE": "NSE_EQ|INE002A01018",
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
        encoded_key = urllib.parse.quote(instrument_key, safe='')
        url_intra = f"https://api.upstox.com/v2/historical-candle/intraday/{encoded_key}/1minute"
        resp = requests.get(url_intra, headers=headers).json()
        candles = resp.get('data', {}).get('candles', [])

        if not candles:
            yesterday = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
            today = datetime.now().strftime("%Y-%m-%d")
            url_hist = f"https://api.upstox.com/v2/historical-candle/{encoded_key}/1minute/{yesterday}/{today}"
            resp_hist = requests.get(url_hist, headers=headers).json()
            candles = resp_hist.get('data', {}).get('candles', [])
            if candles:
                st.info(f"{instrument_key} - Pre-Market data (Live 9:15 ke baad)")

        if not candles:
            return None

        df = pd.DataFrame(candles, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'OI'])
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df = df.sort_values('Timestamp')
        df.set_index('Timestamp', inplace=True)

        if display_interval == "5minute":
            df = df.resample('5min').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum','OI':'last'}).dropna()
        elif display_interval == "15minute":
            df = df.resample('15min').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum','OI':'last'}).dropna()

        return df.reset_index()

    except Exception as e:
        st.error(f"API Error: {e}")
        return None

def check_signal(df):
    if df is None or len(df) < 25:
        return None

    df['EMA9'] = df['Close'].ewm(span=9).mean()
    df['EMA21'] = df['Close'].ewm(span=21).mean()
    df['Vol_SMA'] = df['Volume'].rolling(20).mean()

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + gain / loss))

    last = df.iloc[-1]
    prev = df.iloc[-2]

    volume_ok = last['Volume'] > last['Vol_SMA'] * 0.8
    oi_up = last['OI'] > prev['OI']
    oi_fake = (last['Close'] > prev['Close']) and (not oi_up)

    buy_cross = (prev['EMA9'] < prev['EMA21']) and (last['EMA9'] > last['EMA21'])
    sell_cross = (prev['EMA9'] > prev['EMA21']) and (last['EMA9'] < last['EMA21'])

    if oi_fake:
        return last['Close'], last['EMA9'], last['EMA21'], last['RSI'], last['OI'], "WAIT", f"TRAP! OI down {last['OI']}"
    if buy_cross and last['RSI'] > 55 and volume_ok:
        return last['Close'], last['EMA9'], last['EMA21'], last['RSI'], last['OI'], "BUY", "No Trap BUY"
    if sell_cross and last['RSI'] < 45 and volume_ok:
        return last['Close'], last['EMA9'], last['EMA21'], last['RSI'], last['OI'], "SELL", "SELL confirm"

    return last['Close'], last['EMA9'], last['EMA21'], last['RSI'], last['OI'], "WAIT", "Market dekh raha hu"

cols = st.columns(3)

for i, (name, key) in enumerate(SYMBOLS.items()):
    df = get_upstox_candles(key, display_timeframe)
    if df is None or df.empty:
        with cols[i]:
            st.subheader(name)
            st.warning("Data nahi - Market 9:15 pe")
        continue

    res = check_signal(df)
    if res is None:
        continue

    price, ema9, ema21, rsi, oi, signal, reason = res
    with cols[i]:
        st.subheader(f"{name} ({display_timeframe})")
        st.metric("Price", f"{price:.2f}", f"RSI {rsi:.1f}")
        st.write(f"EMA9 {ema9:.2f} | EMA21 {ema21:.2f} | OI {oi}")
        if signal == "BUY":
            st.success(f"🟢 {signal} - {reason}")
        elif signal == "SELL":
            st.error(f"🔴 {signal} - {reason}")
        else:
            st.warning(f"🟡 {signal} - {reason}")

st.caption(f"Last Updated: {datetime.now().strftime('%H:%M:%S')}")
if st.button("🔄 Refresh Kar"):
    st.rerun()