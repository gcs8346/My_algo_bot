import streamlit as st
import pandas as pd
import requests
import urllib.parse
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="Topu Live V14 Real Rate", layout="wide")
st.title("🔥 Topu V14 - REAL LIVE RATE")
st.caption("Candle + LTP - Exact Rate")

# Auto refresh har 5 sec
st_autorefresh = st.sidebar.checkbox("Auto Refresh (5 sec)", value=True)
if st_autorefresh:
    st.sidebar.write("Har 5 sec me auto update hoga")
    time.sleep(5)
    st.rerun()

st.sidebar.header("Topu ka Upstox Setup")
token = st.sidebar.text_input("Upstox Access Token Daal", type="password")
tf = st.sidebar.selectbox("Timeframe", ["1minute", "5minute", "15minute"], index=0)

if not token:
    st.warning("Token daal bhai")
    st.stop()

headers = {'Authorization': f'Bearer {token}'}

def get_ltp(symbol_key):
    try:
        enc = urllib.parse.quote(symbol_key, safe='')
        url = f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={enc}"
        r = requests.get(url, headers=headers).json()
        # LTP nikalna
        data = r.get('data', {})
        # key me : hota hai isliye direct access
        if symbol_key in data:
            return data[symbol_key]['last_price']
        # kabhi kabhi dict ke andar hota hai
        for v in data.values():
            if 'last_price' in v:
                return v['last_price']
        return None
    except:
        return None

def get_candles(symbol_key):
    enc = urllib.parse.quote(symbol_key, safe='')
    url1 = f"https://api.upstox.com/v2/historical-candle/intraday/{enc}/1minute"
    r1 = requests.get(url1, headers=headers).json()
    candles = r1.get('data', {}).get('candles', [])
    if not candles:
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
        url2 = f"https://api.upstox.com/v2/historical-candle/{enc}/1minute/{from_date}/{to_date}"
        r2 = requests.get(url2, headers=headers).json()
        candles = r2.get('data', {}).get('candles', [])
    if not candles:
        return None
    df = pd.DataFrame(candles, columns=['time','open','high','low','close','volume','oi'])
    df['time'] = pd.to_datetime(df['time'])
    df = df.sort_values('time')
    df = df.set_index('time')
    if tf != "1minute":
        mins = 5 if tf=="5minute" else 15
        df = df.resample(f'{mins}min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum','oi':'last'}).dropna()
    return df.reset_index()

SYMBOLS = {
    "NIFTY": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
}

cols = st.columns(2)
for i, (name, key) in enumerate(SYMBOLS.items()):
    df = get_candles(key)
    ltp = get_ltp(key)
    
    with cols[i]:
        st.subheader(name)
        if ltp:
            # Exact live rate yahan
            st.metric(f"{name} LIVE RATE", f"{ltp:.2f}", delta=f"Candle Close {df.iloc[-1]['close']:.2f}" if df is not None else "")
            if df is not None and abs(ltp - df.iloc[-1]['close']) > 5:
                st.info(f"⚡ Live {ltp} vs Candle {df.iloc[-1]['close']:.2f} - Difference kyuki candle 1 min slow hai")
        else:
            st.warning("LTP nahi mila - Token expiry check kar")
        
        if df is not None:
            # Signal logic simple
            df['EMA9'] = df['close'].ewm(span=9).mean()
            df['EMA21'] = df['close'].ewm(span=21).mean()
            last = df.iloc[-1]
            if last['EMA9'] > last['EMA21']:
                st.success(f"🟢 BUY Trend | EMA9 {last['EMA9']:.1f} > EMA21 {last['EMA21']:.1f}")
            else:
                st.error(f"🔴 SELL Trend | EMA9 {last['EMA9']:.1f} < EMA21 {last['EMA21']:.1f}")
            st.dataframe(df.tail(3))

st.caption(f"Last Exact Update: {datetime.now().strftime('%H:%M:%S')} | LTP = Real Time, Candle = 1 min delayed")
if st.button("🔄 Manual Refresh"):
    st.rerun()