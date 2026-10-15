import streamlit as st
import pandas as pd, os, plotly.graph_objects as go
from datetime import datetime
import upstox_client

SYMBOL = "SENSEX"
SL_POINTS = 25

st.set_page_config(page_title="TOPU TOWER LIVE", layout="wide")
st.title(f"🚀 {SYMBOL} TOPU TOWER - LIVE")

TOKEN = os.getenv("UPSTOX_TOKEN")
if not TOKEN:
    st.error("Render > Environment > UPSTOX_TOKEN daal de")
    st.stop()

configuration = upstox_client.Configuration()
configuration.access_token = TOKEN
api_client = upstox_client.ApiClient(configuration)
history_api = upstox_client.HistoryApi(api_client)

@st.cache_data(ttl=30)
def get_live():
    inst = "BSE_INDEX|SENSEX" if SYMBOL=="SENSEX" else "NSE_INDEX|Nifty 50"
    resp = history_api.get_intra_day_candle_data1(
        instrument_key=inst,
        interval="5minute",
        api_version="2.0"
    )
    df = pd.DataFrame(resp.data.candles, columns=['timestamp','open','high','low','close','volume','oi'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    ltp = float(df.iloc[-1]['close'])
    return df, ltp

df, ltp = get_live()

st.metric("LIVE LTP", f"{ltp:.1f}", f"{ltp-df['open'].iloc:+.1f}")
fig = go.Figure(data=[go.Candlestick(x=df['timestamp'], open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)[0]

if ltp > df['open'].iloc:
    st.success(f"🟢 FINAL BULLISH - BUY | SL: {ltp-SL_POINTS:.0f}")
else:
    st.error(f"🔴 FINAL BEARISH - WAIT")[0]

Ab isko direct select karke copy kar le, Render pe paste kar de.