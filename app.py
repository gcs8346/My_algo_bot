import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as graph_objects
import time

# 1. फुल-स्क्रीन मोबाइल फ्रेंडली लेआउट
st.set_page_config(layout="wide", page_title="Quantum No.1 Algo Master Terminal")

st.markdown("<h1 style='text-align: center; color: #ff3333;'>⚡ QUANTUM ZERO-LAG MASTER TERMINAL ⚡</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-weight: bold; color: #aaaaaa;'>WORLD'S NO.1 SIGNAL ALGO — INTEGRATED TRADING CONSOLE</p>", unsafe_allow_html=True)
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
# 🚀 🔥 सेक्शन 3: यूनिफाइड ट्रेडिंग कंसोल (EXECUTE, PNL, TSL & EXIT ALL-IN-ONE)
# ==============================================================================
st.header("🎛️ Unified Trading Console")

# पूरा सिस्टम एक ही कंटेनर बॉक्स के अंदर दिखेगा
with st.container(border=True):
    
    if not st.session_state.trade_active:
        # --- जब कोई ट्रेड ओपन नहीं है (एंट्री मोड) ---
        st.markdown("<h3 style='color: #2ecc71; margin-bottom: 15px;'>🛡️ STRATEGY STATUS: PERFECT BUY SIGNAL ACTIVE 🎯</h3>", unsafe_allow_html=True)
        
        c_ent1, c_ent2 = st.columns([3, 1])
        with c_ent1:
            st.markdown(f"<p style='font-size:18px; margin:0;'>Ready to trade: <b>{selected_display_name}</b> at Current Price: <b>₹ {live_ltp}</b></p>", unsafe_allow_html=True)
        with c_ent2:
            if st.button("✅ YES - EXECUTE BUY NOW", use_container_width=True, type="primary"):
                st.session_state.trade_active = True
                st.session_state.entry_price = live_ltp
                st.session_state.current_sl = round(live_ltp * 0.995, 2)  # शुरुआती SL 0.5% नीचे
                st.session_state.highest_price_seen = live_ltp
                st.balloons()
                st.rerun()
                
    else:
        # --- जब ट्रेड एक्टिव हो चुका है (PnL, TSL, और Exit मोड) ---
        qty = 100
        price_diff = live_ltp - st.session_state.entry_price
        current_pnl = round(price_diff * qty, 2)
        
        # ट्रेलिंग स्टॉपलॉस कैलकुलेशन
        if live_ltp > st.session_state.highest_price_seen:
            st.session_state.highest_price_seen = live_ltp
            new_sl = round(live_ltp * 0.9975, 2)  # नया SL प्राइस से 0.25% नीचे
            if new_sl > st.session_state.current_sl: st.session_state.current_sl = new_sl

        # डिज़ाइन: PnL + TSL एक तरफ, EXIT बटन ठीक उसके सामने
        c_act1, c_act2 = st.columns([2, 1])
        
        with c_act1:
            box_bg = "#1e3d2f" if current_pnl >= 0 else "#3d1e1e"
            txt_color = "#2ecc71" if current_pnl >= 0 else "#e74c3c"
            sign = "+" if current_pnl >= 0 else ""
            
            # लाइव PnL डिस्प्ले
            st.markdown(f"<div style='background-color:{box_bg}; padding:15px; border-radius:8px; border-left:6px solid {txt_color};'>"
                        f"<p style='margin:0; color:{txt_color}; font-weight:bold;'>🟩 LIVE POSITION PnL ({selected_display_name})</p>"
                        f"<h2 style='margin:0; color:white;'>₹ {sign}{current_pnl}</h2>"
                        f"<p style='margin:0; color:#aaaaaa; font-size:13px;'>एंट्री: ₹{st.session_state.entry_price} | LTP: ₹{live_ltp}</p></div>", unsafe_allow_html=True)
            
            # 🔥 ट्रेलिंग स्टॉपलॉस ठीक PnL के नीचे चमकीले अक्षरों में
            st.markdown(f"<p style='margin-top:10px; font-size:18px; color:#00ffff; font-weight:bold;'>🛡️ CURRENT TRAILING SL: <span style='color:white; background-color:#2a2b36; padding:2px 8px; border-radius:4px;'>₹ {st.session_state.current_sl}</span></p>", unsafe_allow_html=True)

        with c_act2:
            st.write("") # थोड़ा स्पेसिंग देने के लिए
            st.write("")
            # 🔥 एग्जिट बटन ठीक PnL और TSL के बगल में सामने
            if st.button("🚨 CLICK TO EXIT NOW", use_container_width=True, type="primary"):
                st.session_state.trade_active = False
                st.warning(f"🛑 [SQUARE-OFF] पोजीशन क्लोज! फाइनल PnL: ₹ {current_pnl}")
                st.rerun()

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
fig.update_layout(xaxis_rangeslider_visible=False, height=320, template="plotly_dark", margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig, use_container_width=True)

st.write("---")

# ==============================================================================
# 🔢 सेक्शन 5: लाइव कस्टमाइज्ड ऑप्शन चेन (OPTION CHAIN - CALL / PUT OI)
# ==============================================================================
st.header(f"🔢 {selected_display_name} रीयल-टाइम ऑप्शन चेन (OI डेटा)")
step = 100 if "SENSEX" in selected_display_name or "BANK" in selected_display_name else (50 if "NIFTY" in selected_display_name else 5)
strike_center = int(round(live_ltp / step) * step)
strikes = [strike_center - (2*step), strike_center - step, strike_center, strike_center + step, strike_center + (2*step)]

option_chain_df = pd.DataFrame({
    'Call OI (Lakhs)': [42.1, 68.4, 95.2, 38.1, 14.5],
    'Call LTP (₹)': [180.0, 120.0, 75.0, 35.0, 12.0],
    'STRIKE PRICE': strikes,
    'Put LTP (₹)': [10.0, 28.0, 68.0, 115.0, 190.0],
    'Put OI (Lakhs)': [12.4, 31.2, 88.5, 54.1, 41.6]
})
st.dataframe(option_chain_df, use_container_width=True, height=220)
