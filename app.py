import streamlit as st
import pandas as pd
import requests
import urllib.parse
from datetime import datetime, timedelta

st.set_page_config(page_title="Topu Live V14.1 Fixed", layout="wide")
st.title("🔥 Topu V14.1 - REAL LIVE RATE (FIXED)")
st.caption("Candle + LTP - Exact Rate - No Hang")

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
        data = r.get('data', {})
        # Debug - kya aa raha hai dekh le
        # st.write(f"LTP Debug {symbol_key}:", r)
        if symbol_key in data:
            return data[symbol_key].get('last_price')
        for v in data.values():
            if isinstance(v, dict) and 'last_price' in v:
                return v['last_price']
        return None
    except Exception as e:
        st.error(f"LTP Error {e}")
        return None

def get_candles(symbol_key):
    try:
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
    except Exception as e:
        st.error(f"Candle Error {e}")
        return None

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
            st.metric(f"{name} LIVE RATE", f"{ltp:.2f}")
            if df is not None:
                diff = ltp - df.iloc[-1]['close']
                st.caption(f"Candle Close: {df.iloc[-1]['close']:.2f} | Diff: {diff:+.2f} (Candle 1 min slow hota hai)")
        else:
            st.warning("LTP nahi mila - Token check kar ya Market band hai")
            st.write("Debug: Upstox LTP API ne data nahi diya")
        
        if df is not None:
            df['EMA9'] = df['close'].ewm(span=9).mean()
            df['EMA21'] = df['close'].ewm(span=21).mean()
            df['RSI'] = 100 - (100 / (1 + (df['close'].diff().where(lambda x: x>0, 0).rolling(14).mean() / -df['close'].diff().where(lambda x: x<0, 0).rolling(14).mean())))
            last = df.iloc[-1]
            if last['EMA9'] > last['EMA21']:
                st.success(f"🟢 BUY Trend | EMA9 {last['EMA9']:.1f} > EMA21 {last['EMA21']:.1f} | RSI {last['RSI']:.1f}")
            else:
                st.error(f"🔴 SELL Trend | EMA9 {last['EMA9']:.1f} < EMA21 {last['EMA21']:.1f} | RSI {last['RSI']:.1f}")
            st.dataframe(df.tail(3))
        else:
            st.error("Candle data nahi")

st.caption(f"Last Update: {datetime.now().strftime('%H:%M:%S')} | Manual Refresh dabana")
if st.button("🔄 Refresh Kar"):
    st.rerun()