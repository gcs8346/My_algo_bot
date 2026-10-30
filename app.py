import streamlit as st
import pandas as pd
import requests
import urllib.parse
from datetime import datetime, timedelta

st.set_page_config(page_title="Topu Live V12.1", layout="wide")
st.title("🔥 Topu Upstox Live V12.1 - WARNING FIXED")
st.caption("Direct Upstox API - No inplace")

st.sidebar.header("Topu ka Upstox Setup")
token = st.sidebar.text_input("Upstox Access Token Daal (6 8 7 8 wala)", type="password")
tf = st.sidebar.selectbox("Timeframe (Display)", ["1minute", "5minute", "15minute"], index=1)

if not token:
    st.warning("Token daal bhai sidebar me")
    st.stop()

headers = {'Authorization': f'Bearer {token}'}

def get_data(symbol_key):
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
        # FIXED: inplace hataya
        df = df.set_index('time')

        if tf == "5minute":
            df = df.resample('5min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum','oi':'last'}).dropna()
        elif tf == "15minute":
            df = df.resample('15min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum','oi':'last'}).dropna()

        df = df.reset_index()
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return None

SYMBOLS = {
    "NIFTY": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank"
}

for name, key in SYMBOLS.items():
    st.subheader(name)
    df = get_data(key)
    if df is None or df.empty:
        st.warning(f"{name} ka data nahi - Market 9:15 ke baad khulega")
    else:
        st.success(f"{name} OK - {len(df)} candles")
        st.dataframe(df.tail(3))
        st.metric(name, f"{df.iloc[-1]['close']:.2f}")

st.caption(f"Last Updated: {datetime.now().strftime('%H:%M:%S')} | No Warning Now")
if st.button("🔄 Refresh Kar"):
    st.rerun()