import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="TOPU TOWER V3 FINAL", layout="wide")

# ===== 1. YAHAN TOKEN SETTING HAI =====
LICENSE = "TOPU-2026-TEST"
st.markdown("## 👑 TOPU TOWER - V3 FINAL FIX")
lic = st.text_input("🔑 Yearly Token", value="TOPU-2026-TEST")
if lic != LICENSE:
    st.error("❌ Token galat"); st.stop()

# ===== 2. YAHAN UPSTOX TOKEN DALNA HAI - SIDEBAR ME =====
st.sidebar.title("🔴 UPSTOX DIRECT")
upstox_token = st.sidebar.text_input("Upstox Token (Roz Naya)", type="password")
if not upstox_token:
    st.warning("Bhai upstox token daal de"); st.stop()
headers = {'Authorization': f'Bearer {upstox_token}', 'Accept': 'application/json'}

st.sidebar.markdown("---")
sound_on = st.sidebar.checkbox("🔊 Sound Alarm ON", value=True)
refresh_speed = st.sidebar.select_slider("Refresh Speed", options=[1,2,3,5], value=1, format_func=lambda x: f"{x} Sec")
st_autorefresh(interval=refresh_speed*1000, key="tower_v3")

instrument_type = st.sidebar.radio("KISME TRADE?", ["INDEX", "STOCK SEARCH"])
if instrument_type == "INDEX":
    selected = st.sidebar.selectbox("Index Chuno", ["NSE_INDEX|Nifty 50", "NSE_INDEX|Nifty Bank", "BSE_INDEX|SENSEX"])
    instrument_key = selected
else:
    stock_symbol = st.sidebar.text_input("Stock Symbol", value="RELIANCE").upper()
    instrument_key = f"NSE_EQ|{stock_symbol}"

def get_next_expiry():
    today = datetime.today()
    days_ahead = 3 - today.weekday()
    if days_ahead <= 0: days_ahead += 7
    return (today + timedelta(days_ahead)).strftime("%Y-%m-%d")
expiry_date = st.sidebar.text_input("Expiry Date (YYYY-MM-DD)", value=get_next_expiry())

# ===== 3. YE FUNCTION YAHI PE DALNA HAI - TOP PE =====
def get_sahi_PCR(instrument_key, live_price, expiry_date, headers):
    """Ye sahi PCR dega - ATM ke aas paas ke 10 strike se"""
    try:
        url = f"https://api.upstox.com/v2/option/chain?instrument_key={instrument_key}&expiry_date={expiry_date}"
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code != 200:
            return 1.0, f"API Error {r.status_code}"
        data = r.json().get('data', [])
        if not data:
            return 1.0, "Data Khali"
        
        # Spot ke sabse kareeb ATM nikalo
        atm_strike = min(data, key=lambda x: abs(x['strike_price'] - live_price))['strike_price']
        
        # ATM ke aas paas ke 10 strike
        nearby = sorted(data, key=lambda x: abs(x['strike_price'] - atm_strike))[:10]
        
        ce_oi = sum([d.get('call_options',{}).get('market_data',{}).get('oi',0) for d in nearby])
        pe_oi = sum([d.get('put_options',{}).get('market_data',{}).get('oi',0) for d in nearby])
        
        if ce_oi == 0:
            return 1.0, "CE OI 0"
        pcr = pe_oi / ce_oi
        
        if pcr >= 1.25: sig = "✅ STRONG BULLISH"
        elif pcr >= 1.0: sig = "✅ BULLISH"
        elif pcr <= 0.8: sig = "❌ STRONG BEARISH"
        else: sig = "❌ BEARISH"
        return round(pcr, 2), sig
    except Exception as e:
        return 1.0, f"Error {e}"

def play_alarm(text):
    html = f"""<audio autoplay><source src="https://www.soundjay.com/buttons/sounds/beep-07a.mp3"></audio>
    <div style="background:red;padding:10px;border-radius:10px;"><h2 style="color:white;text-align:center;margin:0;">🔊 {text} 🔊</h2></div>"""
    components.html(html, height=110)

if 'last_alert_candle' not in st.session_state:
    st.session_state.last_alert_candle = None

try:
    # LIVE PRICE
    live_price = 0
    url_ltp = f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={instrument_key}"
    r_ltp = requests.get(url_ltp, headers=headers, timeout=5)
    if r_ltp.status_code == 200:
        live_price = list(r_ltp.json()['data'].values())[0]['last_price']
    
    # CANDLE WITH MARKET BAND FIX
    url_candle = f"https://api.upstox.com/v2/historical-candle/intraday/{instrument_key}/1minute"
    r_candle = requests.get(url_candle, headers=headers, timeout=8)
    candles = r_candle.json().get('data',{}).get('candles',[])
    df = pd.DataFrame(candles, columns=['timestamp','open','high','low','close','volume','oi']) if candles else pd.DataFrame()

    if df.empty or len(df) < 25:
        st.warning("🔴 Market Band Hai - Last 5 Din Ka Chart Dikha Raha Hu")
        to_date = datetime.today().strftime('%Y-%m-%d')
        from_date = (datetime.today()-timedelta(days=7)).strftime('%Y-%m-%d')
        r2 = requests.get(f"https://api.upstox.com/v2/historical-candle/{instrument_key}/day/{to_date}/{from_date}", headers=headers, timeout=8)
        if r2.status_code == 200 and r2.json().get('data',{}).get('candles'):
            df = pd.DataFrame(r2.json()['data']['candles'], columns=['timestamp','open','high','low','close','volume','oi'])

    if df.empty or len(df) < 2:
        st.info(f"📈 LIVE: ₹{live_price} | Candle nahi hai, market band hai. Kal 9:15 pe signal ayega")
        st.stop()

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    df['EMA_9'] = df['close'].ewm(span=9).mean()
    df['EMA_21'] = df['close'].ewm(span=21).mean()
    df['FIDI_50'] = df['close'].ewm(span=50).mean()

    # SAHI PCR CALL
    pcr_value, pcr_signal = get_sahi_PCR(instrument_key, live_price, expiry_date, headers)

    st.markdown(f"### 📈 {instrument_key} | LIVE: ₹{live_price} | PCR: {pcr_value} {pcr_signal}")

    fig = go.Figure(data=[
        go.Candlestick(x=df['timestamp'], open=df['open'], high=df['high'], low=df['low'], close=df['close']),
        go.Scatter(x=df['timestamp'], y=df['EMA_9'], line=dict(color='yellow'), name="EMA9"),
        go.Scatter(x=df['timestamp'], y=df['EMA_21'], line=dict(color='red'), name="EMA21"),
        go.Scatter(x=df['timestamp'], y=df['FIDI_50'], line=dict(color='cyan'), name="FIDI 50"),
    ])
    fig.update_layout(height=550, xaxis_rangeslider_visible=False, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    last = df.iloc[-1]
    prev = df.iloc[-2]

    is_bull_trend = last['EMA_9'] > last['EMA_21'] and last['close'] > last['FIDI_50']
    is_bear_trend = last['EMA_9'] < last['EMA_21'] and last['close'] < last['FIDI_50']
    cross_up = (prev['EMA_9'] <= prev['EMA_21']) and (last['EMA_9'] > last['EMA_21'])
    cross_down = (prev['EMA_9'] >= prev['EMA_21']) and (last['EMA_9'] < last['EMA_21'])

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("FIDI 50", "✅ BULLISH" if last['close']>last['FIDI_50'] else "❌ BEARISH")
    c2.metric("EMA Trend", "✅ BULLISH" if last['EMA_9']>last['EMA_21'] else "❌ BEARISH")
    c3.metric("PCR", pcr_value, pcr_signal)
    c4.metric("LIVE", f"₹{live_price}")

    curr_candle = str(last['timestamp'])
    is_new = st.session_state.last_alert_candle != curr_candle

    if cross_up and is_bull_trend:
        st.success(f"## 🚀 FRESH BUY CROSS @ ₹{live_price}")
        if is_new and sound_on:
            play_alarm(f"BUY {instrument_key}"); st.session_state.last_alert_candle = curr_candle; st.balloons()
    elif is_bull_trend:
        st.success(f"## 🚀 BULLISH TREND CONTINUES @ ₹{live_price}")
    elif cross_down and is_bear_trend:
        st.error(f"## 🔻 FRESH SELL CROSS @ ₹{live_price}")
        if is_new and sound_on:
            play_alarm(f"SELL {instrument_key}"); st.session_state.last_alert_candle = curr_candle
    elif is_bear_trend:
        st.error(f"## 🔻 BEARISH TREND CONTINUES @ ₹{live_price}")
    else:
        st.warning(f"## ⏳ WAIT / SIDEWAYS @ ₹{live_price}")

except Exception as e:
    st.error(f"Error: {e}")