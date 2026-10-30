import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import urllib.parse

st.set_page_config(page_title="Topu Upstox Live - No Trap V11", layout="wide")
st.title("🔥 Topu Upstox Live - No Trap V11 FINAL")
st.caption("Direct Upstox API - Pre-Market + Live - No Trap")

# === SIDEBAR ===
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

headers = {'Authorization': f'Bearer {access_token}', 'Accept': 'application/json'}

def get_upstox_candles(instrument_key, display_interval):
    try:
        encoded_key = urllib.parse.quote(instrument_key, safe='')
        
        # 1. Intraday try
        url_intra = f"https://api.upstox.com/v2/historical-candle/intraday/{encoded_key}/1minute"
        resp = requests.get(url_intra, headers=headers).json()
        candles = resp.get('data', {}).get('candles', [])

        # 2. Agar khali hai (8:50 pre-market ya raat) to kal ka data
        if not candles:
            yesterday = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
            today = datetime.now().strftime("%Y-%m-%d")
            url_hist = f"https://api.upstox.com/v2/historical-candle/{encoded_key}/1minute/{yesterday}/{today}"
            resp_hist = requests.get(url_hist, headers=headers).json()
            candles = resp_hist.get('data', {}).get('candles', [])
            if candles:
                st.info(f"{instrument_key} - Pre-Market: Kal ka data dikha raha hu, Live 9:15 ke baad ayega")
        
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
       