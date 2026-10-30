import streamlit as st
import pandas as pd
import requests
import urllib.parse
from datetime import datetime, timedelta

st.set_page_config(page_title="Topu Live V12", layout="wide")
st.title("🔥 Topu Upstox Live V12 - FINAL WORKING")
st.caption("No Trap, No Fail")

# Sidebar
st.sidebar.header("Topu ka Upstox Setup")
token = st.sidebar.text_input("Upstox Access Token Daal (6 8 7 8 wala)", type="password")
tf = st.sidebar.selectbox("Timeframe (Display)", ["1minute", "5minute", "15minute"], index=1)

if not token:
    st.warning("Token daal bhai sidebar me")
    st.stop()

headers = {'Authorization': f'Bearer {token}'}

def get_data(symbol_key):
    enc = urllib.parse.quote(symbol_key, safe='')
    # Intraday
    url1 = f"https://api.upstox.com/v2/historical-candle/intraday/{enc}/1minute"
    r1 = requests.get(url1, headers=headers).json()
    candles = r1.get('data', {}).get('candles', [])
    
    # Agar khali hai to 2 din ka history
    if not candles:
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
        url2 = f"https://api.upstox.com/v2/historical-candle/{enc}/1minute/{from_date}/{to_date}"
        r2 = requests.get(url2, headers=headers).json()
        candles = r2.get('data', {}).get('candles', [])
        st.write(f"Debug {symbol_key}:", r2) # Isse pata chalega kya aa raha hai
    
    if not candles:
        return None
    df = pd.DataFrame(candles, columns=['time','open','high','low','close','volume','oi'])
    return df

SYMBOLS = {
    "NIFTY": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank"
}

for name, key in SYMBOLS.items():
    st.subheader(name)
    df = get_data(key)
    if df is None:
        st.error(f"{name} ka data nahi aaya - Market 9:15 ke baad try kar, token check kar")
    else:
        st.success(f"{name} OK - {len(df)} candles mile")
        st.dataframe(df.tail(3))
        last_price = df.iloc[-1]['close']
        st.metric(name, last_price)

st.caption(f"Last Updated: {datetime.now().strftime('%H:%M:%S')}")

if st.button("Refresh"):
    st.rerun()