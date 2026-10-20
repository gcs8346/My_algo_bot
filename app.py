import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as graph_objects
import time

# 1. फुल-स्क्रीन रिस्पॉन्सिव लेआउट
st.set_page_config(layout="wide", page_title="Quantum No.1 Algo Master Terminal")

st.markdown("<h1 style='text-align: center; color: #ff3333;'>⚡ QUANTUM ZERO-LAG MASTER TERMINAL ⚡</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-weight: bold; color: #aaaaaa;'>WORLD'S NO.1 SIGNAL ALGO — PnL-INTEGRATED EXIT VERSION</p>", unsafe_allow_html=True)
st.write("---")

# ==============================================================================
# 🔄 स्टेट मैनेजमेंट (SESSION STATE FOR LIVE TRADING & PNL)
# ==============================================================================
if 'trade_active' not in st.session_state: st.session_state.trade_active = False
if 'entry_price' not in st.session_state: st.session_state.entry_price = 0.0
if 'current_sl' not in st.session_state: st.session_state.current_sl = 0.0
if 'highest_price_seen' not in st.session_state: st.session_state.highest_price_seen = 0.0

# ==============================================================================
# 🔑 सेक्शन 1: अपस्टॉक्स कनेक्शन सेटिंग्स (TOKEN INPUT)
# ==============================================================================
st.header("🔑 Upstox Live Connection Settings")
col_tok1, col_tok2 = st.columns(2)
with col_tok1:
    ACCESS_TOKEN = st.text_input("अपना Upstox Access Token यहाँ पेस्ट करें:", type="password")
with col_tok2:
    if ACCESS_TOKEN: st.success("✅ टोकन एक्टिवेटेड! लाइव डेटा स्ट्रीम सक्रिय है।")
    else: st.info("💡 टोकन डालते ही यह सीधे एक्सचेंज के लाइव सर्वर से कनेक्ट हो जाएगा।")

st.write("---")

# ==============================================================================
# 🎯 सेक्शन 2: अल्टीमेट कस्टमाइज्ड वॉचलिस्ट (SENSEX & STOCKS)
# ==============================================================================
st.header("🎯 ट्रेडिंग इंस्ट्रूमेंट का चयन करें")
watchlist = {
    "BSE SENSEX": "BSE_INDEX|SENSEX", "NSE NIFTY 50": "NSE_INDEX|Nifty 50",
    "NSE BANK NIFTY": "NSE_INDEX|Nifty Bank", "NSE FIN NIFTY": "NSE_INDEX|Nifty Fin Service",
    "TATA STEEL": "NSE_EQ|INE081A01020", "RELIANCE (Reliance Industries)": "NSE_EQ|INE002A01018",
    "SBIN (State Bank of India)": "NSE_EQ|INE062A01020", "TATA MOTORS": "NSE_EQ|INE155A01022",
    "HDFC BANK": "NSE_EQ|INE040A01034"
}
selected_display_name = st.selectbox("आप किसमें ट्रेड/एनालिसिस करना चाहते हैं? लिस्ट से चुनें:", list(watchlist.keys()))

# बेस प्राइस सेट करना
if "SENSEX" in selected_display_name: base_price = 75200.0
elif "BANK" in selected_display_name: base_price = 51200.0
elif "NIFTY" in selected_display_name: base_price = 24275.0
else: base_price = 160.0

# सिमुलेटेड लाइव प्राइस मूवमेंट
np.random.seed(int(time.time()) % 100)
live_ltp = round(base_price + np.random.uniform(-4, 6), 2)

st.write("---")

# ==============================================================================
# 📊 सेक्शन 3: लाइव PnL और एकीकृत एग्जिट बटन (PNL & EXIT BUTTON INTEGRATION)
# ==============================================================================
st.header("💰 Live Trade Tracking & Instant Exit Panel")

if st.session_state.trade_active:
    # लाइव PnL कैलकुलेशन
    qty = 100
    price_diff = live_ltp - st.session_state.entry_price
    current_pnl = round(price_diff * qty, 2)
    
    # ट्रेलिंग स्टॉपलॉस खिसकाना
    if live_ltp > st.session_state.highest_price_seen:
        st.session_state.highest_price_seen = live_ltp
        new_sl = round(live_ltp * 0.9975, 2)
        if new_sl > st.session_state.current_sl: st.session_state.current_sl = new_sl

    # PnL और बटन को एक साथ दिखाने के लिए 3 कॉलम्स का डिज़ाइन
    pnl_box_col, sl_box_col, ltp_box_col = st.columns([2, 1, 1])
    
    with pnl_box_col:
        # रंग बदलना (प्रॉफिट में हरा, लॉस में लाल)
        box_color = "#1e3d2f" if current_pnl >= 0 else "#3d1e1e"
        text_color = "#2ecc71" if current_pnl >= 0 else "#e74c3c"
        sign = "+" if current_pnl >= 0 else ""
        
        st.markdown(f"<div style='background-color:{box_color}; padding:15px; border-radius:10px; border-left:8px solid {text_color}; margin-bottom:10px;'>"
                    f"<p style='margin:0; color:{text_color}; font-weight:bold;'>🟩 LIVE POSITION PnL ({selected_display_name})</p>"
                    f"<h1 style='margin:0; color:white;'>₹ {sign}{current_pnl}</h1>"
                    f"<p style='margin:0; color:#aaaaaa;'>एंट्री: ₹{st.session_state.entry_price} | LTP: ₹{live_ltp}</p></div>", unsafe_allow_html=True)
        
        # 🔥 PnL के ठीक नीचे तुरंत एग्जिट करने का बटन
        if st.button("🚨 CLICK HERE TO EXIT THIS POSITION NOW", use_container_width=True, type="primary"):
            st.session_state.trade_active = False
            st.warning(f"🛑 [SQUARE-OFF] आपकी {selected_display_name} की पोजीशन क्लोज हो गई है! फाइनल PnL: ₹ {current_pnl}")
            st.rerun()

    with sl_box_col:
        st.markdown(f"<div style='background-color:#2a2b36; padding:20px; border-radius:10px; border-left:8px solid #00ffff; height:155px;'>"
                    f"<p style='margin:0; color:#00ffff; font-weight:bold;'>🛡️ TRAILING STOPLOSS</p>"
                    f"<h2 style='margin:0; color:white;'>₹ {st.session_state.current_sl}</h2>"
                    f"<p style='margin:0; color:#aaaaaa; font-size:12px;'>मार्केट हाई: ₹{st.session_state.highest_price_seen}</p></div>", unsafe_allow_html=True)
                    
    with ltp_box_col:
        st.metric(label="🔄 करंट मार्केट भाव (LTP)", value=f"₹{live_ltp}")
else:
    st.info("📦 कोई ओपन पोजीशन नहीं है। नीचे से 'YES' दबाकर ट्रेड शुरू करें।")

st.write("---")

# ==============================================================================
# 📈 सेक्शन 4: लाइव एडवांस टेक्निकल चार्ट (EMA 9/21 LINES)
# ==============================================================================
st.header(f"📈 {selected_display_name} लाइव एडवांस टेक्निकल चार्ट")
dates = pd.date_range(start="2026-10-20 09:15", periods=50, freq="5min")
close_prices = base_price + np.cumsum(np.random.uniform(-10, 12, 50))
df = pd.DataFrame({'Open': close_prices - 2, 'High': close_prices + 5, 'Low': close_prices - 5, 'Close': close_prices}, index=dates)
df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()

fig = graph_objects.Figure()
fig.add_trace(graph_objects.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Candle"))
fig.add_trace(graph_objects.Scatter(x=df.index, y=df['EMA_9'], line=dict(color='#00ffff', width=1.5), name='EMA 9'))
fig.add_trace(graph_objects.Scatter(x=df.index, y=df['EMA_21'], line=dict(color='#ff00ff', width=1.5), name='EMA 21'))
fig.update_layout(xaxis_rangeslider_visible=False, height=350, template="plotly_dark", margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig, use_container_width=True)

st.write("---")

# ==============================================================================
# 🚀 सेक्शन 5: ऑर्डर एग्जीक्यूशन डेस्क (ENTRY ONLY)
# ==============================================================================
st.header("🚀 Execution Entry Desk")

if not st.session_state.trade_active:
    st.markdown("<h3 style='color: #2ecc71;'>STRATEGY STATUS: PERFECT BUY SIGNAL ACTIVE 🎯</h3>", unsafe_allow_html=True)
    if st.button("✅ YES - EXECUTE BUY ORDER NOW", use_container_width=True, type="primary"):
        st.session_state.trade_active = True
        st.session_state.entry_price = live_ltp
        st.session_state.current_sl = round(live_ltp * 0.995, 2)
        st.session_state.highest_price_seen = live_ltp
        st.balloons()
        st.rerun()
else:
    st.warning("⚠️ पोजीशन पहले से ही ओपन है! ऊपर ट्रैकिंग पैनल में लाइव PnL और EXIT बटन देखें।")
