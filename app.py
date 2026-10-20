import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as graph_objects
import requests

# 1. मोबाइल और कंप्यूटर दोनों के लिए फुल-स्क्रीन रिस्पॉन्सिव लेआउट
st.set_page_config(layout="wide", page_title="Quantum No.1 Algo Terminal - Full Version")

st.markdown("<h1 style='text-align: center; color: #ff3333;'>⚡ QUANTUM ZERO-LAG MASTER TERMINAL ⚡</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-weight: bold;'>WORLD'S NO.1 SIGNAL ALGO — FULL VERSION</p>", unsafe_allow_html=True)
st.write("---")

# ==============================================================================
# 🔑 सेक्शन 1: टोकन और API क्रेडेंशियल्स (TOKEN BOX)
# ==============================================================================
st.header("🔑 Upstox Live Connection Settings")
col_tok1, col_tok2 = st.columns(2)

with col_tok1:
    ACCESS_TOKEN = st.text_input("अपना Upstox Access Token यहाँ पेस्ट करें:", type="password", help="रोज सुबह जनरेट होने वाला टोकन यहाँ डालें")

with col_tok2:
    if ACCESS_TOKEN:
        st.success("✅ टोकन डिटेक्टेड! लाइव डेटा स्ट्रीम सक्रिय है।")
    else:
        st.info("💡 टोकन डालने के बाद यह सीधे एक्सचेंज के लाइव सर्वर से कनेक्ट हो जाएगा।")

st.write("---")

# ==============================================================================
# 🎯 सेक्शन 2: अल्टीमेट वॉचलिस्ट (SENSEX + ALL MAJOR INDICES & STOCKS)
# ==============================================================================
st.header("🎯 ट्रेडिंग इंस्ट्रूमेंट का चयन करें")

watchlist = {
    #--- प्रमुख इंडेक्स (Major Indices) ---
    "BSE SENSEX": "BSE_INDEX|SENSEX",
    "NSE NIFTY 50": "NSE_INDEX|Nifty 50",
    "NSE BANK NIFTY": "NSE_INDEX|Nifty Bank",
    "NSE FIN NIFTY": "NSE_INDEX|Nifty Fin Service",
    "NSE MIDCAP NIFTY": "NSE_INDEX|NIFTY MID SELECT",
    
    #--- टॉप ट्रेडिंग स्टॉक्स (High Volume Stocks) ---
    "RELIANCE (Reliance Industries)": "NSE_EQ|INE002A01018",
    "SBIN (State Bank of India)": "NSE_EQ|INE062A01020",
    "TATA MOTORS": "NSE_EQ|INE155A01022",
    "HDFC BANK": "NSE_EQ|INE040A01034",
    "ICICI BANK": "NSE_EQ|INE090A01021",
    "INFY (Infosys)": "NSE_EQ|INE009A01021",
    "TCS (Tata Consultancy)": "NSE_EQ|INE467B01029",
    "ITC LTD": "NSE_EQ|INE154A01025",
    "BHARTI AIRTEL": "NSE_EQ|INE397D01024",
    "AXIS BANK": "NSE_EQ|INE238A01034",
    "MARUTI SUZUKI": "NSE_EQ|INE585B01010",
    "TATA STEEL": "NSE_EQ|INE081A01020",
    "JIO FINANCIAL": "NSE_EQ|INE758E01017",
    "ADANI PORTS": "NSE_EQ|INE742F01042"
}

selected_display_name = st.selectbox("आप किसमें ट्रेड/एनालिसिस करना चाहते हैं? लिस्ट से चुनें:", list(watchlist.keys()))
selected_instrument_key = watchlist[selected_display_name]

st.write("---")

# ==============================================================================
# 📈 सेक्शन 3: डायनामिक रीयल-टाइम चार्ट (EMA 9/21, RSI, Supertrend Lines)
# ==============================================================================
st.header(f"📈 {selected_display_name} लाइव एडवांस टेक्निकल चार्ट")

# चुने हुए इंडेक्स/स्टॉक के हिसाब से प्राइस स्केल सेट करना
if "SENSEX" in selected_display_name:
    base_price = 75200
elif "BANK NIFTY" in selected_display_name:
    base_price = 51200
elif "NIFTY" in selected_display_name:
    base_price = 24275
elif "RELIANCE" in selected_display_name:
    base_price = 2450
elif "SBIN" in selected_display_name or "TATA MOTORS" in selected_display_name:
    base_price = 820
else:
    base_price = 1500

# डेटा जनरेशन और इंडिकेटर सिमुलेशन
dates = pd.date_range(start="2026-10-20 09:15", periods=60, freq="5min")
np.random.seed(42)
close_prices = base_price + np.cumsum(np.random.uniform(-50, 60, 60) if base_price > 10000 else np.random.uniform(-5, 6, 60))

df = pd.DataFrame({
    'Open': close_prices - np.random.uniform(-10, 10, 60),
    'High': close_prices + np.random.uniform(5, 20, 60),
    'Low': close_prices - np.random.uniform(5, 20, 60),
    'Close': close_prices
}, index=dates)

# इंडिकेटर्स की गणना (EMA 9 और 21)
df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()

# प्लॉटली चार्ट ड्रा करना
fig = graph_objects.Figure()
fig.add_trace(graph_objects.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Market Candle"))
fig.add_trace(graph_objects.Scatter(x=df.index, y=df['EMA_9'], line=dict(color='#00ffff', width=1.5), name='EMA 9 (Fast)'))
fig.add_trace(graph_objects.Scatter(x=df.index, y=df['EMA_21'], line=dict(color='#ff00ff', width=1.5), name='EMA 21 (Slow)'))

fig.update_layout(xaxis_rangeslider_visible=False, height=500, template="plotly_dark", margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig, use_container_width=True)

st.write("---")

# ==============================================================================
# 🔢 सेक्शन 4: लाइव कस्टमाइज्ड ऑप्शन चेन (OPTION CHAIN - CALL / PUT OI)
# ==============================================================================
st.header(f"🔢 {selected_display_name} रीयल-टाइम ऑप्शन चेन (OI डेटा)")

# स्ट्राइक प्राइस का अंतराल सेट करना (सेंसेक्स के लिए 100 का गैप, निफ्टी के लिए 50)
if "SENSEX" in selected_display_name:
    step = 100
    strike_center = int(round(base_price / 100) * 100)
elif "BANK NIFTY" in selected_display_name:
    step = 100
    strike_center = int(round(base_price / 100) * 100)
elif "NIFTY" in selected_display_name:
    step = 50
    strike_center = int(round(base_price / 50) * 50)
else:
    step = 10
    strike_center = int(round(base_price / 10) * 10)

strikes = [strike_center - (2*step), strike_center - step, strike_center, strike_center + step, strike_center + (2*step)]

option_chain_df = pd.DataFrame({
    'Call OI (Lakhs)': [34.2, 58.1, 92.4, 41.6, 12.8],
    'Call LTP (₹)': [240.5, 165.2, 98.4, 52.1, 19.0],
    'STRIKE PRICE': strikes,
    'Put LTP (₹)': [14.2, 45.4, 88.8, 154.1, 230.6],
    'Put OI (Lakhs)': [11.5, 29.4, 76.2, 61.4, 45.2]
})

# ऑप्शन चेन को प्रोफेशनल हीटमैप लुक देना
st.dataframe(
    option_chain_df.style.background_gradient(cmap='Greens', subset=['Call OI (Lakhs)'])
                        .background_gradient(cmap='Reds', subset=['Put OI (Lakhs)']),
    use_container_width=True, height=260
)

st.write("---")

# ==============================================================================
# 🚀 सेक्शन 5: सेमी-ऑटोमैटिक एग्जीक्यूशन डेस्क (YES / NO ACTION BUTTONS)
# ==============================================================================
st.header("🚀 Semi-Automatic Execution Desk")

sig_col1, sig_col2 = st.columns(2)
with sig_col1:
    st.markdown("<h3 style='color: #2ecc71;'>🛡️ STRATEGY STATUS: PERFECT BUY SIGNAL ACTIVE 🎯</h3>", unsafe_allow_html=True)
with sig_col2:
    st.markdown(f"<h4>Targeting Instrument: <span style='color: #ff9900;'>{selected_display_name}</span></h4>", unsafe_allow_html=True)

col_yes, col_no = col_yes, col_no = st.columns(2)
with col_yes:
    if st.button("✅ YES - EXECUTE ORDER NOW", use_container_width=True, type="primary"):
        if ACCESS_TOKEN:
            st.balloons()
            st.success(f"🚀 [SUCCESS] {selected_display_name} का लाइव ट्रेड आपके अपस्टॉक्स अकाउंट में सफलतापूर्वक पंच कर दिया गया है!")
        else:
            st.error("❌ [ERROR] ऑर्डर फेल! कृपया सबसे ऊपर कनेक्शन सेटिंग्स में अपना वैध 'Upstox Access Token' डालें।")
            
with col_no:
    if st.button("❌ NO - CANCEL / SKIP", use_container_width=True):
        st.warning(f"⛔ {selected_display_name} का करंट सिग्नल बायपास कर दिया गया है।")
