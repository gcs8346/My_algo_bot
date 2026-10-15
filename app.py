import streamlit as st
import pandas as pd
import os
import http://plotly.graph_objects as go
import requests
from datetime import datetime

SYMBOL = "SENSEX"
SL_POINTS = 25

http://st.set_page_config(page_title="TOPU TOWER LIVE", layout="wide")
http://st.title(f"🚀 {SYMBOL} TOPU TOWER - LIVE")

TOKEN = http://os.getenv("UPSTOX_TOKEN")
if not TOKEN:
    http://st.error("Render > Environment > UPSTOX_TOKEN daal de")
    http://st.stop()

@st.cache_data(ttl=30)
def get_live():
    inst = "BSE_INDEX|SENSEX"
    url = f"https://api.upstox.com/v2/historical-candle/intraday/{inst}/5minute"
    headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}
    r = http://requests.get(url, headers=headers, timeout=10)
    j = http://r.json()
    if http://j.get("status")!= "success":
        raise Exception(str(j))
    candles = j["data"]["candles"]
    df = http://pd.DataFrame(candles, columns=['timestamp','open','high','low','close','volume','oi'])
    df['timestamp'] = http://pd.to_datetime(df['timestamp'])
    df = http://df.sort_values('timestamp')
    ltp = float(df.iloc[-1]['close'])
    return df, ltp

df, ltp = get_live()

http://st.metric("LIVE LTP", f"{ltp:.1f}", f"{ltp-df['open'].iloc:+.1f}")
fig = http://go.Figure(data=[go.Candlestick(x=df['timestamp'], open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
http://fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False)
http://st.plotly_chart(fig, use_container_width=True)[0]

if ltp > df['open'].iloc:
    http://st.success(f"🟢 BULLISH - BUY | SL: {ltp-SL_POINTS:.0f}")
else:
    http://st.error(f"🔴 BEARISH - WAIT")[0]