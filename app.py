import streamlit as st
import pandas as pd
import os
import plotly.graph_objects as go
import requests
from datetime import datetime

SYMBOL = "SENSEX"
SL_POINTS = 25

# Streamlit पेज कॉन्फ़िगरेशन
st.set_page_config(page_title="TOPU TOWER LIVE", layout="wide")
st.title(f"🚀 {SYMBOL} TOPU TOWER - LIVE")

TOKEN = os.getenv("UPSTOX_TOKEN")
if not TOKEN:
    st.error("Render > Environment > UPSTOX_TOKEN daal de")
    st.stop()

@st.cache_data(ttl=30)
def get_live():
    inst = "BSE_INDEX|SENSEX"
    # 1. यहाँ URL में 5minute को बदलकर 1minute कर दिया है
    url = f"https://api.upstox.com/v2/historical-candle/intraday/{inst}/1minute"
    headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}
    
    r = requests.get(url, headers=headers, timeout=10)
    j = r.json()
    
    if j.get("status") != "success":
        raise Exception(str(j))
        
    candles = j["data"]["candles"]
    
    # 1 मिनट का DataFrame बनाना
    df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    # 2. 1 मिनट के डेटा को 5 मिनट (5min) में बदलना (Resampling)
    df.set_index('timestamp', inplace=True)
    
    ohlc_dict = {
        'open': 'first',   # 5 मिनट अंतराल का पहला ओपन
        'high': 'max',     # 5 मिनट अंतराल का सबसे उच्चतम हाई
        'low': 'min',      # 5 मिनट अंतराल का सबसे निम्नतम लो
        'close': 'last',   # 5 मिनट अंतराल का आखिरी क्लोज
        'volume': 'sum',   # 5 मिनट अंतराल का कुल वॉल्यूम
        'oi': 'last'       # ओपन इंटरेस्ट का आखिरी वैल्यू
    }
    
    # 5 मिनट में कन्वर्ट करना
    df_5min = df.resample('5min').apply(ohlc_dict)
    df_5min.dropna(inplace=True)  # खाली रो (Rows) को हटाना
    df_5min.reset_index(inplace=True)  # इंडेक्स को वापस नॉर्मल कॉलम बनाना
    
    # लाइव प्राइस (LTP) सबसे आखरी क्लोज से निकालना
    ltp = float(df_5min.iloc[-1]['close'])
    
    return df_5min, ltp

# डेटा लोड करना
df, ltp = get_live()

# डेटा की पहली ओपन वैल्यू (कैलकुलेशन के लिए)
first_open = df['open'].iloc[0]
open_diff = ltp - first_open

# डैशबोर्ड डिस्प्ले
st.metric("LIVE LTP", f"{ltp:.1f}", f"{open_diff:+.1f}")

# चार्ट बनाना
fig = go.Figure(data=[go.Candlestick(
    x=df['timestamp'], 
    open=df['open'], 
    high=df['high'], 
    low=df['low'], 
    close=df['close']
)])
fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)

# बुलिश / बियरिश सिग्नल (करंट 5 मिनट कैंडल के ओपन से तुलना)
current_candle_open = df['open'].iloc[-1]

if ltp > current_candle_open:
    st.success(f"🟢 BULLISH - BUY | SL: {ltp - SL_POINTS:.0f}")
else:
    st.error(f"🔴 BEARISH - WAIT")
