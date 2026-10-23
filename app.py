import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
from datetime import datetime, timedelta

st.set_page_config(page_title="TOPU TOWER V4 FINAL", layout="wide")
LICENSE = "TOPU-2026-TEST"

st.markdown("## 👑 TOPU TOWER - V4 FINAL")
lic = st.text_input("🔑 Yearly Token", value="TOPU-2026-TEST")
if lic != LICENSE:
    st.error("❌ Token galat"); st.stop()

# ===== SIDEBAR =====
st.sidebar.title("🔴 UPSTOX DIRECT")
upstox_token = st.sidebar.text_input("Upstox Token (Roz Naya)", type="password")
if not upstox_token:
    st.warning("Bhai token daal de"); st.stop()
headers = {'Authorization': f'Bearer {upstox_token}', 'Accept': 'application/json'}

sound_on = st.sidebar.checkbox("🔊 Sound ON", value=True)
st_autorefresh(interval=2000, key="v4")

instrument_type = st.sidebar.radio("KISME TRADE?", ["INDEX", "STOCK"])
if instrument_type == "INDEX":
    instrument_key = st.sidebar.selectbox("Index", ["NSE_INDEX|Nifty 50", "NSE_INDEX|Nifty Bank", "BSE_INDEX|SENSEX"])
else:
    s = st.sidebar.text_input("Stock Symbol", "RELIANCE").upper()
    instrument_key = f"NSE_EQ|{s}"

def get_next_expiry():
    today = datetime.today()
    d = 3 - today.weekday()
    if d <= 0: d+=7
    return (today+timedelta(days=d)).strftime("%Y-%m-%d")
expiry_date = st.sidebar.text_input("Expiry YYYY-MM-DD", value=get_next_expiry())

# ===== FINAL FIX FUNCTION - YAHI MAIN HAI =====
def get_sahi_PCR(instrument_key, live_price, expiry_date, headers):
    if "INDEX" not in instrument_key:
        return 1.0, "Stock me PCR nahi"
    if live_price == 0:
        return 1.0, "Live Price 0"
    try:
        url = f"https://api.upstox.com/v2/option/chain?instrument_key={instrument_key}&expiry_date={expiry_date}"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return 1.0, f"API {r.status_code}"
        
        data = r.json().get('data')
        if not data: # YAHI TERA DATA KHALI WALA FIX HAI
            return 1.0, "Data Khali - Expiry galat?"
        
        # ATM ke sabse kareeb 10 strike
        atm_strike = min(data, key=lambda x: abs(x['strike_price'] - live_price))['strike_price']
        nearby = sorted(data, key=lambda x: abs(x['strike_price'] - atm_strike))[:10]
        
        ce_oi = sum([d.get('call_options',{}).get('market_data',{}).get('oi',0) for d in nearby])
        pe_oi = sum([d.get('put_options',{}).get('market_data',{}).get('oi',0) for d in nearby])
        
        if ce_oi == 0 and pe_oi == 0:
            return 1.0, "OI 0 - Market Band"
        if ce_oi == 0:
            return 1.0, "CE OI 0"
            
        pcr = pe_oi / ce_oi
        if pcr >= 1.25: sig = "✅ STRONG BULL"
        elif pcr >= 1.0: sig = "✅ BULL"
        elif pcr <= 0.8: sig = "❌ STRONG BEAR"
        else: sig = "❌ BEAR"
        return round(pcr,2), f"{sig} | ATM {atm_strike}"
    except Exception as e:
        return 1.0, f"Error {str(e)[:30]}"

def play_alarm(t):
    html = f"""<audio autoplay><source src="https://www.soundjay.com/buttons/sounds/beep-07a.mp3"></audio>
    <div style="background:red;padding:10px;border-radius:10px;"><h2 style="color:white;text-align:center;margin:0;">🔊 {t} 🔊</h2></div>"""
    components.html(html, height=110)

# ===== MAIN LOGIC =====
try:
    # 1. Live Price
    live_price = 0
    r_ltp = requests.get(f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={instrument_key}", headers=headers, timeout=5)
    if r_ltp.status_code == 200:
        live_price = list(r_ltp.json()['data'].values())[0]['last_price']

    # 2. Candle with Market Band Fix
    r_c = requests.get(f"https://api.upstox.com/v2/historical-candle/intraday/{instrument_key}/1minute", headers=headers, timeout=8)
    candles = r_c.json().get('data',{}).get('candles',[]) if r_c.status_code==200 else []
    df = pd.DataFrame(candles, columns=['timestamp','open','high','low','close','volume','oi']) if candles else pd.DataFrame()

    if df.empty or len(df) < 25:
        st.warning("🔴 Market Band - Daily Chart dikha raha hu")
        to_d = datetime.today().strftime('%Y-%m-%d')
        from_d = (datetime.today()-timedelta(days=7)).strftime('%Y-%m-%d')
        r2 = requests.get(f"https://api.upstox.com/v2/historical-candle/{instrument_key}/day/{to_d}/{from_d}", headers=headers, timeout=8)
        if r2.status_code == 200 and r2.json().get('data',{}).get('candles'):
            df = pd.DataFrame(r2.json()['data']['candles'], columns=['timestamp','open','high','low','close','volume','oi'])

    if df.empty or len(df) < 2:
        pcr_v, pcr_s = get_sahi_PCR(instrument_key, live_price, expiry_date, headers)
        st.metric("LIVE", f"₹{live_price}", f"PCR {pcr_v} | {pcr_s}")
        st.info(f"LIVE ₹{live_price} | Market band hai, kal 9:15 pe full signal ayega")
        st.stop()

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    df['EMA_9'] = df['close'].ewm(span=9).mean()
    df['EMA_21'] = df['close'].ewm(span=21).mean()
    df['FIDI_50'] = df['close'].ewm(span=50).mean()

    pcr_value, pcr_text = get_sahi_PCR(instrument_key, live_price, expiry_date, headers)
    
    st.markdown(f"### 📈 {instrument_key} | LIVE ₹{live_price} | PCR {pcr_value} | {pcr_text}")

    fig = go.Figure(data=[
        go.Candlestick(x=df['timestamp'], open=df['open'], high=df['high'], low=df['low'], close=df['close']),
        go.Scatter(x=df['timestamp'], y=df['EMA_9'], line=dict(color='yellow'), name="EMA9"),
        go.Scatter(x=df['timestamp'], y=df['EMA_21'], line=dict(color='red'), name="EMA21"),
        go.Scatter(x=df['timestamp'], y=df['FIDI_50'], line=dict(color='cyan'), name="FIDI50"),
    ])
    fig.update_layout(height=500, xaxis_rangeslider_visible=False, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    last, prev = df.iloc[-1], df.iloc[-2]
    is_bull = last['EMA_9'] > last['EMA_21'] and last['close'] > last['FIDI_50']
    is_bear = last['EMA_9'] < last['EMA_21'] and last['close'] < last['FIDI_50']
    cross_up = (prev['EMA_9'] <= prev['EMA_21']) and (last['EMA_9'] > last['EMA_21'])

    if cross_up and is_bull:
        st.success(f"## 🚀 FRESH BUY @ ₹{live_price} | {pcr_text}")
        if sound_on: play_alarm(f"BUY {instrument_key}")
    elif is_bull:
        st.success(f"## 🚀 BULLISH TREND @ ₹{live_price}")
    elif is_bear:
        st.error(f"## 🔻 BEARISH TREND @ ₹{live_price}")
    else:
        st.warning(f"## ⏳ WAIT @ ₹{live_price}")

    c1,c2,c3 = st.columns(3)
    c1.metric("FIDI 50", "BULL" if last['close']>last['FIDI_50'] else "BEAR")
    c2.metric("EMA", "BULL" if last['EMA_9']>last['EMA_21'] else "BEAR")
    c3.metric("PCR", pcr_value, pcr_text)

except Exception as e:
    st.error(f"Error: {e}")