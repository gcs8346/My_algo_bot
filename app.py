import streamlit as st
import pandas as pd
import requests
import urllib.parse
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("Topu LITE TEST - Sirf Data Check")

token = st.sidebar.text_input("Naya Token Daal", type="password")
if not token:
    st.warning("Token daal")
    st.stop()

headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}

def get_candles_simple(k):
    try:
        enc = urllib.parse.quote(k, safe='')
        to_date = datetime.now()
        while to_date.weekday() >= 5:
            to_date -= timedelta(days=1)
        from_date = to_date - timedelta(days=5)
        url = f"https://api.upstox.com/v2/historical-candle/{enc}/1minute/{from_date.strftime('%Y-%m-%d')}/{to_date.strftime('%Y-%m-%d')}"
        st.write(f"Trying: {k} -> {url[:100]}...")
        r = requests.get(url, headers=headers, timeout=15)
        st.write(f"Status: {r.status_code}")
        if r.status_code != 200:
            st.error(f"Error: {r.text[:500]}")
            return None
        candles = r.json().get('data', {}).get('candles', [])
        st.write(f"Candles mile: {len(candles)}")
        if not candles:
            return None
        df = pd.DataFrame(candles, columns=['time','open','high','low','close','volume','oi'])
        return df
    except Exception as e:
        st.error(f"Exception: {e}")
        return None

SYMBOLS = {
    "NIFTY 50": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
    "SENSEX": "BSE_INDEX|SENSEX",
}

for name, key in SYMBOLS.items():
    st.subheader(name)
    df = get_candles_simple(key)
    if df is not None:
        st.success(f"✅ Data aa gaya! Last close: {df.iloc[0]['close']}")
        st.dataframe(df.head(3))
    else:
        st.error("❌ Data nahi aaya")