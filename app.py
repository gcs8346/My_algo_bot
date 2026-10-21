import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=60 * 1000, key="tower_live")
st.set_page_config(page_title="TOPU TOWER FINAL", layout="wide")

SYMBOL_MAP = {
    "SENSEX": "^BSESN",
    "NIFTY": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "FINNIFTY": "^CNXFIN"
}

st.markdown("<h1 style='color:#2ea8ff'>TOPU TOWER - FINAL SUPER COMBO - LIVE ORIGINAL</h1>", unsafe_allow_html=True)

# Top controls
c1,c2,c3,c4,c5 = st.columns(5)
with c1:
    index_opt = st.selectbox("INDEX", ["SENSEX","NIFTY","BANKNIFTY","FINNIFTY","STOCK"])
with c2:
    lot_qty = st.number_input("LOT QTY", value=1, min_value=1)
with c3:
    sl_points = st.number_input("SL POINTS", value=100)
with c4:
    trail_gap = st.number_input("TRAILING GAP", value=50)
with c5:
    stock_symbol = ""
    if index_opt == "STOCK":
        stock_symbol = st.text_input("STOCK SYMBOL NSE", "RELIANCE").upper().strip()
        yahoo_sym = stock_symbol + ".NS" if ".NS" not in stock_symbol and "^" not in stock_symbol else stock_symbol
    else:
        yahoo_sym = SYMBOL_MAP[index_opt]

ema_f, ema_m, ema_s = st.columns(3)
with ema_f:
    ema_fast = st.number_input("EMA FAST", value=9)
with ema_m:
    ema_mid = st.number_input("EMA MEDIUM", value=21)
with ema_s:
    ema_slow = st.number_input("EMA SLOW", value=50)

preset = st.radio("PRESET", ["STOCK 9-21-50","OPTION 10-50-100"], horizontal=True)
if preset == "OPTION 10-50-100":
    ema_fast, ema_mid, ema_slow = 10, 50, 100

# Fetch live
@st.cache_data(ttl=60)
def get_data(sym):
    df = yf.download(sym, period="1d", interval="1m", progress=False, auto_adjust=False)
    return df

if st.button("REFRESH LIVE"):
    st.cache_data.clear()

try:
    with st.spinner(f"Fetching LIVE {yahoo_sym}..."):
        df = get_data(yahoo_sym)
    
    if df.empty:
        st.error(f"Yahoo se data nahi aaya {yahoo_sym} ke liye - Market band ho sakta hai")
        st.stop()
    
    # Flatten if multi-index
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    df['EMA_FAST'] = df['Close'].ewm(span=ema_fast).mean()
    df['EMA_MID'] = df['Close'].ewm(span=ema_mid).mean()
    df['EMA_SLOW'] = df['Close'].ewm(span=ema_slow).mean()
    
    last = df.iloc[-1]
    first = df.iloc[0]
    ltp = float(last['Close'])
    day_open = float(first['Open'])
    
    # Trends
    if ltp > last['EMA_FAST'] > last['EMA_MID'] > last['EMA_SLOW']:
        ema_trend = "BULLISH"
    elif ltp < last['EMA_FAST'] < last['EMA_MID'] < last['EMA_SLOW']:
        ema_trend = "BEARISH"
    else:
        ema_trend = "SIDEWAYS"
    
    open_trend = "BULLISH" if ltp > day_open else "BEARISH" if ltp < day_open else "FLAT"
    
    recent_high = df['High'].tail(20).max()
    recent_low = df['Low'].tail(20).min()
    
    sl = ltp - sl_points if ema_trend=="BULLISH" else ltp + sl_points
    tgt = ltp + sl_points*2.5 if ema_trend=="BULLISH" else ltp - sl_points*2.5
    
    # Top metrics
    m1,m2,m3,m4,m5 = st.columns(5)
    m1.metric(f"{index_opt} LTP", f"{ltp:.2f}", f"{ltp-day_open:.2f}")
    m2.metric("DAY OPEN", f"{day_open:.2f}")
    m3.metric("EMA TREND", ema_trend)
    m4.metric("OPEN TREND", open_trend)
    m5.metric("CHANNEL", f"{recent_low:.0f} - {recent_high:.0f}")
    
    # Alert
    if ema_trend=="BULLISH" and ltp>day_open:
        st.success(f"ALERT: {yahoo_sym} FINAL BULLISH - CALL READY | LTP {ltp:.0f}")
    elif ema_trend=="BEARISH" and ltp<day_open:
        st.error(f"ALERT: {yahoo_sym} FINAL BEARISH - PUT READY | LTP {ltp:.0f}")
    
    # Chart
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Candle"))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_FAST'], line=dict(color='gold', width=2), name=f"EMA {ema_fast}"))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_MID'], line=dict(color='deepskyblue', width=2), name=f"EMA {ema_mid}"))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_SLOW'], line=dict(color='magenta', width=2), name=f"EMA {ema_slow}"))
    fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, title=f"{yahoo_sym} • 1MIN • LIVE ORIGINAL")
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown(f"<div style='display:grid;grid-template-columns:repeat(3,1fr);gap:10px;padding:12px;background:#0f1a2b;border:1px solid #22c55e;border-radius:10px;text-align:center;font-weight:800'><div style='color:#ef4444'>SL: {sl:.0f}</div><div style='color:#22c55e'>TGT: {tgt:.0f}</div><div style='color:#2ea8ff'>LIVE: {yahoo_sym} • {datetime.now().strftime('%H:%M:%S')}</div></div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"LIVE FETCH FAILED: {e}")
    st.info("Market band hai to 1d data nahi ayega, 9:15 ke baad try kar. Ya symbol galat hai.")