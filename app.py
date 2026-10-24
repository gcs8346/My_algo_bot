import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import streamlit.components.v1 as components

st.set_page_config(page_title="TOWER V45 TIK-TIK SPEED", layout="wide")
st.title("🏰 TOWER V45 - SPEED CONTROL")

upstox_token = st.sidebar.text_input("Upstox Access Token", type="password")

# --- YAHI WO BUTTON HAI JO TUNE BOLA THA - 0.8 TO 3 SEC ---
st.sidebar.markdown("### ⏱️ TIK-TIK SPEED")
tick_speed = st.sidebar.select_slider(
    "Speed Aage Peeche Kar",
    options=[0.8, 1.0, 1.2, 1.5, 2.0, 3.0],
    value=1.0,
    format_func=lambda x: f"{x} second"
)
st.sidebar.caption(f"Abhi: {tick_speed} sec me update hoga")

auto_tick = st.sidebar.checkbox(f"🔴 LIVE TIK-TIK ON ({tick_speed}s)", value=False)
sound_on = st.sidebar.checkbox("🔊 Sound ON", value=True)

# --- SENSEX SAHIT LIST - STUCK BUG FIX ---
STOCKS = {
"Nifty 50":"NSE_INDEX|Nifty 50",
"Bank Nifty":"NSE_INDEX|Nifty Bank",
"Sensex":"BSE_INDEX|SENSEX",
"RELIANCE":"NSE_EQ|INE002A01018",
"TCS":"NSE_EQ|INE467B01029",
"INFY":"NSE_EQ|INE009A01021",
"HDFCBANK":"NSE_EQ|INE040A01034",
"ICICIBANK":"NSE_EQ|INE090A01021",
"SBIN":"NSE_EQ|INE062A01020",
}
selected_name = st.sidebar.selectbox("Stock Select Kar", list(STOCKS.keys()))
selected_inst = STOCKS[selected_name]
tf = st.sidebar.selectbox("Timeframe", ["1minute","3minute","5minute","15minute","30minute","day"], index=2)

def get_candles(token, instrument, interval):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        url = f"https://api.upstox.com/v2/historical-candle/intraday/{instrument}/{interval}"
        r = requests.get(url, headers=headers, timeout=5).json()
        if r.get('status')=='success' and r['data'].get('candles'):
            df = pd.DataFrame(r['data']['candles'], columns=['Timestamp','Open','High','Low','Close','Volume','OI'])
            df['Timestamp']=pd.to_datetime(df['Timestamp']); df.set_index('Timestamp', inplace=True); df.sort_index(inplace=True)
            return df
    except: pass
    try:
        to_date = datetime.now().strftime("%Y-%m-%d"); from_date = (datetime.now()-timedelta(days=5)).strftime("%Y-%m-%d")
        url = f"https://api.upstox.com/v2/historical-candle/{instrument}/30minute/{to_date}/{from_date}"
        r = requests.get(url, headers=headers, timeout=5).json()
        if r.get('status')=='success' and r['data'].get('candles'):
            df = pd.DataFrame(r['data']['candles'], columns=['Timestamp','Open','High','Low','Close','Volume','OI'])
            df['Timestamp']=pd.to_datetime(df['Timestamp']); df.set_index('Timestamp', inplace=True); df.sort_index(inplace=True)
            return df
    except: pass
    return None

# LIVE CHECK
if st.button(f"🚀 {selected_name} CHECK KAR", type="primary", use_container_width=True) or auto_tick:
    st.write(f"Checking: **{selected_name}** | Speed: {tick_speed}s | Time: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
    df = get_candles(upstox_token, selected_inst, tf)
    if df is not None:
        last = df.iloc[-1]
        c1,c2,c3 = st.columns(3)
        c1.metric(f"{selected_name} LTP", f"{last['Close']:.2f}")
        c2.metric("Timeframe", tf)
        c3.metric("Speed", f"{tick_speed}s")

        # Candle check
        body = abs(last['Close']-last['Open'])
        lower = min(last['Open'],last['Close']) - last['Low']
        is_hammer = lower > 2*body
        if is_hammer:
            st.success("🟢 Hammer - Bottom Reversal")
            if sound_on:
                components.html("""<audio autoplay><source src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg"></audio>""", height=0)
        
        st.dataframe(df[['Close','Volume']].tail(10), use_container_width=True)
    else:
        st.error(f"{selected_name} ka data nahi aaya - Token check kar")

# --- YAHI SE SPEED CONTROL HOGA ---
if auto_tick:
    time.sleep(tick_speed)
    st.rerun()