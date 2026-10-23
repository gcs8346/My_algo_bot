import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="TOPU TOWER FINAL - WORLD NO.1", layout="wide")

# --- LICENSE ---
LICENSE = "TOPU-2026-TEST"
st.markdown("## 👑 TOPU TOWER - FINAL WORLD NO.1 - SENSEX + NIFTY + STOCK")
lic = st.text_input("🔑 Yearly Token", value="TOPU-2026-TEST")
if lic != LICENSE:
    st.error("❌ Token galat"); st.stop()

# --- SIDEBAR ---
st.sidebar.title("🔴 UPSTOX DIRECT")
upstox_token = st.sidebar.text_input("Upstox Token (Roz Naya)", type="password")
if not upstox_token:
    st.warning("Bhai token daal de"); st.stop()

headers = {'Authorization': f'Bearer {upstox_token}', 'Accept': 'application/json'}

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ SETTING")
sound_on = st.sidebar.checkbox("🔊 Sound Alarm ON", value=True)
refresh_speed = st.sidebar.select_slider("Refresh Speed", options=[1,2,3,5], value=1, format_func=lambda x: f"{x} Sec TICK")
st_autorefresh(interval=refresh_speed*1000, key="final_tower")

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 KISME TRADE KARNA HAI?")
instrument_type = st.sidebar.radio("Select", ["INDEX", "STOCK SEARCH"])

if instrument_type == "INDEX":
    selected = st.sidebar.selectbox("Index Chuno", ["NSE_INDEX|Nifty 50", "NSE_INDEX|Nifty Bank", "BSE_INDEX|SENSEX", "NSE_INDEX|Nifty Fin Service"])
    instrument_key = selected
else:
    stock_symbol = st.sidebar.text_input("Stock Symbol (ex: RELIANCE, TCS, INFY)", value="RELIANCE").upper()
    stock_map = {
        "RELIANCE": "NSE_EQ|INE002A01018", "TCS": "NSE_EQ|INE467B01029", "INFY": "NSE_EQ|INE009A01021",
        "HDFCBANK": "NSE_EQ|INE040A01034", "ICICIBANK": "NSE_EQ|INE090A01021", "SBIN": "NSE_EQ|INE062A01020",
        "BHARTIARTL": "NSE_EQ|INE397D01024", "ITC": "NSE_EQ|INE154A01025", "LT": "NSE_EQ|INE018A01030",
        "KOTAKBANK": "NSE_EQ|INE237A01028", "BAJFINANCE": "NSE_EQ|INE296A01024", "WIPRO": "NSE_EQ|INE075A01022",
        "MARUTI": "NSE_EQ|INE585B01010", "TATAMOTORS": "NSE_EQ|INE155A01022", "SUNPHARMA": "NSE_EQ|INE044A01036",
        "NTPC": "NSE_EQ|INE733E01010", "POWERGRID": "NSE_EQ|INE752E01010", "AXISBANK": "NSE_EQ|INE238A01034"
    }
    instrument_key = stock_map.get(stock_symbol, f"NSE_EQ|{stock_symbol}")
    st.sidebar.caption(f"Instrument: {instrument_key}")

# Expiry auto
def get_next_expiry():
    today = datetime.today()
    # Thursday for Nifty, Friday for Sensex logic
    days_ahead = 3 - today.weekday() # Thursday
    if days_ahead <= 0: days_ahead += 7
    return (today + timedelta(days_ahead)).strftime("%Y-%m-%d")

expiry_date = st.sidebar.text_input("Expiry Date (YYYY-MM-DD)", value=get_next_expiry())

# --- ALARM FUNCTION FINAL ---
def play_alarm(signal_text):
    alarm_html = f"""
    <audio autoplay loop>
        <source src="https://www.soundjay.com/buttons/sounds/beep-07a.mp3" type="audio/mpeg">
    </audio>
    <script>
        var audio = new Audio('https://www.soundjay.com/buttons/sounds/beep-07a.mp3');
        audio.play().catch(e=>console.log("Autoplay blocked"));
        if (window.Notification) {{
            if (Notification.permission !== "granted") Notification.requestPermission();
            else new Notification("TOPU TOWER SIGNAL! 🚀", {{ body: "{signal_text}" }});
        }}
    </script>
    <div style="background:red; padding:10px; border-radius:10px; animation: blinker 0.8s linear infinite;">
        <h2 style="color:white; text-align:center; margin:0;">🔊🔊 {signal_text} - ABHI ENTRY LE 🔊🔊</h2>
    </div>
    <style> @keyframes blinker {{ 50% {{ opacity: 0.2; }} }} </style>
    """
    components.html(alarm_html, height=110)

if 'last_alert_candle' not in st.session_state:
    st.session_state.last_alert_candle = None

# --- LIVE DATA FETCH ---
try:
    # 1. LTP - check tick file first for 1 sec tick
    live_price = 0
    if os.path.exists("live_tick.txt"):
        try:
            with open("live_tick.txt","r") as f:
                live_price = float(f.read().strip())
        except: pass
    
    if live_price == 0:
        url_ltp = f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={instrument_key}"
        r_ltp = requests.get(url_ltp, headers=headers, timeout=5)
        if r_ltp.status_code != 200:
            st.error(f"Instrument nahi mila: {instrument_key}. Error: {r_ltp.text}"); st.stop()
        live_price = list(r_ltp.json()['data'].values())[0]['last_price']

    # 2. CANDLES
    url_candle = f"https://api.upstox.com/v2/historical-candle/intraday/{instrument_key}/1minute"
    r_candle = requests.get(url_candle, headers=headers, timeout=8)
    candles = r_candle.json()['data']['candles']
    df = pd.DataFrame(candles, columns=['timestamp','open','high','low','close','volume','oi'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')

    # 3. INDICATORS
    df['EMA_9'] = df['close'].ewm(span=9).mean()
    df['EMA_21'] = df['close'].ewm(span=21).mean()
    df['FIDI_50'] = df['close'].ewm(span=50).mean()
    df['SuperTrend_Dir'] = 1
    df.loc[df['close'] < df['EMA_21'], 'SuperTrend_Dir'] = -1

    # 4. OPTION CHAIN PCR
    pcr = 1.0
    oc_signal, oc_text = "STOCK - NO OC", "Stock me OC nahi"
    if "INDEX" in instrument_key:
        try:
            oc_url = f"https://api.upstox.com/v2/option/chain?instrument_key={instrument_key}&expiry_date={expiry_date}"
            r_oc = requests.get(oc_url, headers=headers, timeout=8)
            if r_oc.status_code == 200:
                oc_data = r_oc.json()['data']
                ce_oi = sum([x['call_options']['market_data']['oi'] for x in oc_data[:10] if 'call_options' in x])
                pe_oi = sum([x['put_options']['market_data']['oi'] for x in oc_data[:10] if 'put_options' in x])
                pcr = pe_oi / ce_oi if ce_oi > 0 else 1.0
                if pcr > 1.1: oc_signal, oc_text = "✅ BULLISH OI", f"PE OI jyada PCR {pcr:.2f}"
                elif pcr < 0.9: oc_signal, oc_text = "❌ BEARISH OI", f"CE OI jyada PCR {pcr:.2f}"
                else: oc_signal, oc_text = "NEUTRAL", f"PCR {pcr:.2f}"
            else:
                oc_text = f"Expiry {expiry_date} pe data nahi"
        except Exception as e:
            oc_text = f"OC Error"

    # --- CHART ---
    st.markdown(f"### 📈 {instrument_key} | LIVE: ₹{live_price} | {oc_text} | Refresh: {refresh_speed} Sec")
    fig = go.Figure(data=[
        go.Candlestick(x=df['timestamp'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Candle"),
        go.Scatter(x=df['timestamp'], y=df['EMA_9'], line=dict(color='yellow', width=1.5), name="EMA 9"),
        go.Scatter(x=df['timestamp'], y=df['EMA_21'], line=dict(color='red', width=1.5), name="EMA 21"),
        go.Scatter(x=df['timestamp'], y=df['FIDI_50'], line=dict(color='cyan', width=2), name="FIDI EMA 50"),
    ])
    fig.update_layout(height=550, xaxis_rangeslider_visible=False, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    # --- SIGNAL LOGIC ---
    last = df.iloc[-1]
    prev = df.iloc[-2]
    ema_cross_up = (prev['EMA_9'] <= prev['EMA_21']) and (last['EMA_9'] > last['EMA_21'])
    ema_cross_down = (prev['EMA_9'] >= prev['EMA_21']) and (last['EMA_9'] < last['EMA_21'])
    fidi_cross_up = (prev['close'] <= prev['FIDI_50']) and (last['close'] > last['FIDI_50'])
    bos_up = last['close'] > df['high'].rolling(20).max().iloc[-2]
    is_bullish_now = last['EMA_9'] > last['EMA_21'] and last['close'] > last['FIDI_50'] and pcr >= 1.0

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("FIDI (FI+DI)", "✅ BULLISH" if last['close']>last['FIDI_50'] else "❌ BEARISH")
    c2.metric("EMA 9>21", "✅ BULLISH" if last['EMA_9']>last['EMA_21'] else "❌ BEARISH", "CROSS" if ema_cross_up or ema_cross_down else "NO CROSS")
    c3.metric("SuperTrend", "✅ BUY" if last['SuperTrend_Dir']==1 else "❌ SELL")
    c4.metric("Option Chain", oc_signal, oc_text)
    c5.metric("LIVE PRICE", f"₹{live_price}", f"{last['close']-last['open']:.2f}")

    st.markdown("---")
    current_candle = str(last['timestamp'])
    is_new = st.session_state.last_alert_candle != current_candle

    if (ema_cross_up and fidi_cross_up and is_bullish_now) or (ema_cross_up and bos_up):
        st.success(f"## 🚀🚀 PERFECT BUY NOW - {instrument_key} @ ₹{live_price}")
        st.write(f"Reason: EMA CROSS UP + FIDI CROSS + OI BULLISH = SMART MONEY BUYING")
        if "INDEX" in instrument_key:
            st.success(f"### ENTRY: {instrument_key.split('|')[-1]} {int(live_price/100)*100} CE BUY")
        else:
            st.success(f"### ENTRY: {instrument_key} STOCK BUY")
        if is_new and sound_on:
            play_alarm(f"PERFECT BUY {instrument_key} @ {live_price}")
            st.session_state.last_alert_candle = current_candle
            st.balloons()

    elif ema_cross_down:
        st.error(f"## 🔻 PERFECT SELL / PUT BUY - {instrument_key} @ ₹{live_price}")
        if "INDEX" in instrument_key:
            st.error(f"### ENTRY: {instrument_key.split('|')[-1]} {int(live_price/100)*100} PE BUY")
        else:
            st.error(f"### ENTRY: {instrument_key} STOCK SELL")
        if is_new and sound_on:
            play_alarm(f"PERFECT SELL {instrument_key} @ {live_price}")
            st.session_state.last_alert_candle = current_candle

    else:
        st.warning(f"## ⏳ WAIT - NO EXACT CROSSOVER YET @ ₹{live_price}")
        st.info(f"Check: EMA 9={last['EMA_9']:.2f} EMA21={last['EMA_21']:.2f} | FIDI={last['FIDI_50']:.2f} | PCR={pcr:.2f}. Cross bante hi SOUND ayega.")

except Exception as e:
    st.error(f"Error: {e}")
    st.info("Market band hoga toh candle nahi ayega. Token roz naya dalna hai.")