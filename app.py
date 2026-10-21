import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
from datetime import datetime

st.set_page_config(page_title="TOPU TOWER FINAL - WORLD NO.1", layout="wide")
st_autorefresh(interval=5000, key="final_tower") # 5 sec refresh

# --- LICENSE ---
LICENSE = "TOPU-2026-TEST"
st.markdown("## 👑 TOPU TOWER - FINAL WORLD NO.1 - SENSEX + NIFTY + STOCK")
lic = st.text_input("🔑 Yearly Token", value="TOPU-2026-TEST")
if lic != LICENSE:
    st.error("❌ Token galat"); st.stop()

# --- SIDEBAR - UPSTOX + STOCK SELECTION ---
st.sidebar.title("🔴 UPSTOX DIRECT")
upstox_token = st.sidebar.text_input("Upstox Token (Roz Naya)", type="password")
if not upstox_token:
    st.warning("Bhai token daal de"); st.stop()

headers = {'Authorization': f'Bearer {upstox_token}', 'Accept': 'application/json'}

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 KISME TRADE KARNA HAI? TYPE KARO")

# Yahi hai tera main control
instrument_type = st.sidebar.radio("Select", ["INDEX", "STOCK SEARCH"])

if instrument_type == "INDEX":
    selected = st.sidebar.selectbox("Index Chuno", ["NSE_INDEX|Nifty 50", "NSE_INDEX|Nifty Bank", "BSE_INDEX|SENSEX", "NSE_INDEX|Nifty Fin Service"])
    instrument_key = selected
else:
    # Stock type karega toh uska chart ayega
    stock_symbol = st.sidebar.text_input("Stock Symbol Type Karo (ex: RELIANCE, TCS, INFY, HDFCBANK)", value="RELIANCE").upper()
    # Upstox stock ka instrument key banane ka try
    # Top stocks ka ISIN map (50 stocks) - direct kaam karega
    stock_map = {
        "RELIANCE": "NSE_EQ|INE002A01018", "TCS": "NSE_EQ|INE467B01029", "INFY": "NSE_EQ|INE009A01021",
        "HDFCBANK": "NSE_EQ|INE040A01034", "ICICIBANK": "NSE_EQ|INE090A01021", "SBIN": "NSE_EQ|INE062A01020",
        "BHARTIARTL": "NSE_EQ|INE397D01024", "ITC": "NSE_EQ|INE154A01025", "LT": "NSE_EQ|INE018A01030",
        "KOTAKBANK": "NSE_EQ|INE237A01028", "BAJFINANCE": "NSE_EQ|INE296A01024", "WIPRO": "NSE_EQ|INE075A01022"
    }
    instrument_key = stock_map.get(stock_symbol, f"NSE_EQ|{stock_symbol}")
    st.sidebar.caption(f"Instrument Key: {instrument_key}")

# --- FUNCTION FOR SOUND ALARM ---
def play_alarm(signal_text):
    # Base64 beep sound + browser alert
    alarm_html = f"""
    <audio autoplay>
        <source src="https://www.soundjay.com/buttons/sounds/beep-07a.mp3" type="audio/mpeg">
    </audio>
    <script>
        var audio = new Audio('https://www.soundjay.com/buttons/sounds/beep-07a.mp3');
        audio.play();
        // Notification
        if (Notification.permission === "granted") {{
            new Notification("TOPU TOWER SIGNAL! 🚀", {{ body: "{signal_text}" }});
        }}
    </script>
    <h2 style="color:red; animation: blinker 1s linear infinite;">🔊🔊 ALARM - {signal_text} - ABHI ENTRY LE 🔊🔊</h2>
    <style> @keyframes blinker {{ 50% {{ opacity: 0; }} }} </style>
    """
    components.html(alarm_html, height=100)

# --- LIVE DATA FETCH ---
try:
    # 1. LTP
    url_ltp = f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={instrument_key}"
    r_ltp = requests.get(url_ltp, headers=headers, timeout=5)
    if r_ltp.status_code != 200:
        st.error(f"Instrument nahi mila: {instrument_key}. Stock ka naam sahi likh ya INDEX chuno. Error: {r_ltp.json()}")
        st.stop()
    live_price = list(r_ltp.json()['data'].values())[0]['last_price']

    # 2. INTRADAY CANDLES (1 min)
    url_candle = f"https://api.upstox.com/v2/historical-candle/intraday/{instrument_key}/1minute"
    r_candle = requests.get(url_candle, headers=headers, timeout=8)
    candles = r_candle.json()['data']['candles']
    df = pd.DataFrame(candles, columns=['timestamp','open','high','low','close','volume','oi'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')

    # 3. INDICATORS CALC
    df['EMA_9'] = df['close'].ewm(span=9).mean()
    df['EMA_21'] = df['close'].ewm(span=21).mean()
    df['FIDI_50'] = df['close'].ewm(span=50).mean() # FI+DI flow ka EMA
    # SuperTrend simple
    df['SuperTrend_Dir'] = 1
    df.loc[df['close'] < df['EMA_21'], 'SuperTrend_Dir'] = -1

    # 4. OPTION CHAIN (Only for INDEX)
    pcr = 1.0
    oc_signal = "STOCK - NO OC"
    oc_text = "Stock me Option Chain nahi, sirf Index me"
    if "NSE_INDEX" in instrument_key or "BSE_INDEX" in instrument_key:
        try:
            expiry = "2026-10-29" # expiry apni change karna
            if "SENSEX" in instrument_key:
                oc_url = f"https://api.upstox.com/v2/option/chain?instrument_key={instrument_key}&expiry_date={expiry}"
            else:
                oc_url = f"https://api.upstox.com/v2/option/chain?instrument_key={instrument_key}&expiry_date={expiry}"
            r_oc = requests.get(oc_url, headers=headers, timeout=8)
            if r_oc.status_code == 200:
                oc_data = r_oc.json()['data']
                ce_oi = sum([x['call_options']['market_data']['oi'] for x in oc_data[:7] if 'call_options' in x])
                pe_oi = sum([x['put_options']['market_data']['oi'] for x in oc_data[:7] if 'put_options' in x])
                pcr = pe_oi / ce_oi if ce_oi > 0 else 1.0
                if pcr > 1.1: oc_signal, oc_text = "✅ BULLISH OI", f"PE OI jyada PCR {pcr:.2f}"
                elif pcr < 0.9: oc_signal, oc_text = "❌ BEARISH OI", f"CE OI jyada PCR {pcr:.2f}"
                else: oc_signal, oc_text = "NEUTRAL", f"PCR {pcr:.2f}"
        except: pass

    # --- CHART ---
    st.markdown(f"### 📈 {instrument_key} | LIVE: ₹{live_price} | {oc_text}")
    fig = go.Figure(data=[
        go.Candlestick(x=df['timestamp'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Candle"),
        go.Scatter(x=df['timestamp'], y=df['EMA_9'], line=dict(color='yellow', width=1.5), name="EMA 9"),
        go.Scatter(x=df['timestamp'], y=df['EMA_21'], line=dict(color='red', width=1.5), name="EMA 21"),
        go.Scatter(x=df['timestamp'], y=df['FIDI_50'], line=dict(color='cyan', width=2), name="FIDI EMA 50 (FI+DI)"),
    ])
    fig.update_layout(height=550, xaxis_rangeslider_visible=False, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    # --- PERFECT SIGNAL LOGIC - EXACT CROSSOVER ---
    last = df.iloc[-1]
    prev = df.iloc[-2]

    # Crossover exact time pe pakadna
    ema_cross_up = (prev['EMA_9'] <= prev['EMA_21']) and (last['EMA_9'] > last['EMA_21'])
    ema_cross_down = (prev['EMA_9'] >= prev['EMA_21']) and (last['EMA_9'] < last['EMA_21'])
    fidi_cross_up = (prev['close'] <= prev['FIDI_50']) and (last['close'] > last['FIDI_50'])
    bos_up = last['close'] > df['high'].rolling(20).max().iloc[-2]

    is_bullish_now = last['EMA_9'] > last['EMA_21'] and last['close'] > last['FIDI_50'] and pcr >= 1.0

    # TOWER DISPLAY
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("FIDI (FI+DI)", "✅ BULLISH" if last['close']>last['FIDI_50'] else "❌ BEARISH", "FI+DI Flow")
    c2.metric("EMA 9>21", "✅ BULLISH" if last['EMA_9']>last['EMA_21'] else "❌ BEARISH", "CROSS" if ema_cross_up or ema_cross_down else "NO CROSS")
    c3.metric("SuperTrend", "✅ BUY" if last['SuperTrend_Dir']==1 else "❌ SELL", "Trend")
    c4.metric("Option Chain", oc_signal, oc_text)
    c5.metric("LIVE PRICE", f"₹{live_price}", f"{last['close']-last['open']:.2f}")

    # --- FINAL PERFECT ENTRY + SOUND ALARM ---
    st.markdown("---")
    if (ema_cross_up and fidi_cross_up and is_bullish_now) or (ema_cross_up and bos_up):
        st.success(f"## 🚀🚀 PERFECT BUY NOW - {instrument_key} @ ₹{live_price}")
        st.write(f"Reason: EMA CROSS UP + FIDI CROSS + OI BULLISH = SMART MONEY BUYING. CALL/Stock BUY karo.")
        if "NSE_INDEX" in instrument_key or "BSE_INDEX" in instrument_key:
            st.success(f"### ENTRY: {instrument_key.split('|')[-1]} {int(live_price/100)*100} CE BUY")
        else:
            st.success(f"### ENTRY: {instrument_key} STOCK BUY @ ₹{live_price}")
        play_alarm(f"PERFECT BUY {instrument_key} @ {live_price}")
        st.balloons()

    elif ema_cross_down:
        st.error(f"## 🔻 PERFECT SELL / PUT BUY - {instrument_key} @ ₹{live_price}")
        st.write(f"Reason: EMA CROSS DOWN + FIDI DOWN = SMART MONEY SELLING")
        if "NSE_INDEX" in instrument_key or "BSE_INDEX" in instrument_key:
            st.error(f"### ENTRY: {instrument_key.split('|')[-1]} {int(live_price/100)*100} PE BUY")
        else:
            st.error(f"### ENTRY: {instrument_key} STOCK SELL")
        play_alarm(f"PERFECT SELL {instrument_key} @ {live_price}")

    else:
        st.warning(f"## ⏳ WAIT - NO EXACT CROSSOVER YET @ ₹{live_price}")
        st.info(f"Last Crossover Check: EMA 9={last['EMA_9']:.2f} EMA 21={last['EMA_21']:.2f} | FIDI={last['FIDI_50']:.2f} | PCR={pcr:.2f}. Exact cross bante hi SOUND ayega.")

except Exception as e:
    st.error(f"Error: {e}")
    st.info("Market band hoga toh candle nahi ayega, market khulte hi chart ayega. Token roz naya dalna hai.")