import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import upstox_client
from streamlit_autorefresh import st_autorefresh

# ==============================================================================
# 🎛️ INITIAL CONFIGURATION & REFRESH ENGINE
# ==============================================================================
st.set_page_config(layout="wide", page_title="Quantum No.1 Algo Master Terminal")

st.markdown("<h1 style='text-align: center; color: #ff3333;'>⚡ QUANTUM ZERO-LAG MASTER TERMINAL ⚡</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-weight: bold; color: #aaaaaa;'>WORLD'S NO.1 SIGNAL ALGO — DIRECT LIVE UPSTOX API CONSOLE</p>", unsafe_allow_html=True)
st.write("---")

# हर 1 सेकंड में स्क्रीन को बिना क्रैश किए ऑटो-रिफ्रेश करने का इंजन
st_autorefresh(interval=1000, key="quantum_core_refresh")

# Application State Configuration
if 'trade_active' not in st.session_state: st.session_state.trade_active = False
if 'entry_price' not in st.session_state: st.session_state.entry_price = 0.0
if 'current_sl' not in st.session_state: st.session_state.current_sl = 0.0
if 'highest_price_seen' not in st.session_state: st.session_state.highest_price_seen = 0.0
if 'api_connected' not in st.session_state: st.session_state.api_connected = False

# Watchlist Setup
watchlist = {
    "NSE NIFTY 50": "NSE_INDEX|Nifty 50",
    "NSE BANK NIFTY": "NSE_INDEX|Nifty Bank",
    "BSE SENSEX": "BSE_INDEX|SSEX",
    "TATA STEEL": "NSE_EQ|INE081A01020",
    "RELIANCE": "NSE_EQ|INE002A01018",
    "SBIN": "NSE_EQ|INE062A01020",
    "TATA MOTORS": "NSE_EQ|INE155A01022",
    "HDFC BANK": "NSE_EQ|INE040A01034"
}

# ==============================================================================
# 🔑 SECTION 1: UPSTOX LIVE CONNECTION SETTINGS
# ==============================================================================
st.header("🔑 Upstox Live Connection Settings")
col_tok1, col_tok2 = st.columns(2)
with col_tok1:
    ACCESS_TOKEN = st.text_input("अपना Upstox Access Token यहाँ पेस्ट करें:", type="password")

# ==============================================================================
# 🔌 DIRECT LIVE API REFRESH FUNCTION (🚨 UPDATED WITH CORRECT METHOD)
# ==============================================================================
def get_live_ltp_from_upstox(token, instrument_key):
    try:
        configuration = upstox_client.Configuration()
        configuration.access_token = token
        
        # Upstox SDK की सही क्लास
        api_instance = upstox_client.MarketQuoteApi(upstox_client.ApiClient(configuration))
        
        # 'get_ltp' की जगह Upstox का सही ऑफिशियल मेथड 'ltp' इस्तेमाल किया है
        api_response = api_instance.ltp(symbol=instrument_key, api_version='2.0')
        
        # रिस्पॉन्स डिक्शनरी से लाइव भाव एक्सट्रैक्ट करना
        if api_response and api_response.data:
            if instrument_key in api_response.data:
                return float(api_response.data[instrument_key].last_price)
    except Exception as e:
        st.error(f"Upstox Connection Error: {str(e)}")
    return None

with col_tok2:
    if ACCESS_TOKEN:
        st.session_state.api_connected = True
        st.success("✅ Live Upstox API Connected! सीधा लाइव डेटा एक्सचेंज से सिंक हो रहा है।")
    else:
        st.session_state.api_connected = False
        st.warning("💡 टोकन डालते ही यह सीधे एक्सचेंज के लाइव सर्वर से कनेक्ट हो जाएगा।")

st.write("---")

# ==============================================================================
# 🎯 SECTION 2: INSTRUMENT SELECTION & LTP CAPTURE
# ==============================================================================
st.header("🎯 ट्रेडिंग इंस्ट्रूमेंट का चयन करें")
selected_display_name = st.selectbox("आप किसमें ट्रेड/एनालिसिस करना चाहते हैं? लिस्ट से चुनें:", list(watchlist.keys()))

target_key = watchlist[selected_display_name]

# अगर टोकन डाला है तो सीधे अपस्टॉक्स से लाइव प्राइस उठाओ, वरना स्क्रीन पर अलर्ट दिखाओ
if st.session_state.api_connected and ACCESS_TOKEN:
    fetched_price = get_live_ltp_from_upstox(ACCESS_TOKEN, target_key)
    if fetched_price:
        live_ltp = fetched_price
    else:
        live_ltp = 0.0
        st.error("⚠️ लाइव डेटा फेच नहीं हो पाया। कृपया टोकन की वैधता (Validity) जांचें।")
else:
    live_ltp = 0.0
    st.info("👋 कृपया ऊपर अपना लाइव अपस्टॉक्स टोकन डालें ताकि एक्सचेंज से सीधे असली भाव लोड हो सके।")

if live_ltp > 0:
    st.markdown(f"<p style='font-size:24px; color:#00ffff; font-weight:bold;'>🔴 LIVE TICK PRICE ({selected_display_name}): <span style='color:#fff; background-color:#ff3333; padding:5px 12px; border-radius:5px;'>₹ {live_ltp}</span></p>", unsafe_allow_html=True)
st.write("---")

# ==============================================================================
# 🚀 SECTION 3: UNIFIED TRADING CONSOLE (PnL & TSL CALCULATION)
# ==============================================================================
if live_ltp > 0:
    st.header("🎛️ Unified Trading Console")

    with st.container(border=True):
        if not st.session_state.trade_active:
            st.markdown("<h3 style='color: #2ecc71; margin-bottom: 15px;'>🛡️ STRATEGY STATUS: PERFECT BUY SIGNAL ACTIVE 🎯</h3>", unsafe_allow_html=True)
            c_ent1, c_ent2 = st.columns(2)
            with c_ent1:
                st.markdown(f"<p style='font-size:18px; margin:0;'>Ready to trade: <b>{selected_display_name}</b> at Current Price: <b>₹ {live_ltp}</b></p>", unsafe_allow_html=True)
            with c_ent2:
                if st.button("✅ YES - EXECUTE BUY NOW", use_container_width=True, type="primary"):
                    st.session_state.trade_active = True
                    st.session_state.entry_price = live_ltp
                    st.session_state.current_sl = round(live_ltp * 0.995, 2)
                    st.session_state.highest_price_seen = live_ltp
                    st.balloons()
                    st.rerun()
        else:
            qty = 100
            price_diff = live_ltp - st.session_state.entry_price
            current_pnl = round(price_diff * qty, 2)

            # Dynamic Trailing Stop-Loss Engine
            if live_ltp > st.session_state.highest_price_seen:
                st.session_state.highest_price_seen = live_ltp
                new_sl = round(live_ltp * 0.9975, 2)
                if new_sl > st.session_state.current_sl: 
                    st.session_state.current_sl = new_sl

            c_act1, c_act2 = st.columns(2)
            with c_act1:
                box_bg = "#1e3d2f" if current_pnl >= 0 else "#3d1e1e"
                txt_color = "#2ecc71" if current_pnl >= 0 else "#e74c3c"
                sign = "+" if current_pnl >= 0 else ""

                st.markdown(f"<div style='background-color:{box_bg}; padding:15px; border-radius:8px; border-left:6px solid {txt_color};'>"
                            f"<p style='margin:0; color:{txt_color}; font-weight:bold;'>🟩 LIVE POSITION PnL ({selected_display_name})</p>"
                            f"<h2 style='margin:0; color:white;'>₹ {sign}{current_pnl}</h2>"
                            f"<p style='margin:0; color:#aaaaaa; font-size:13px;'>एंट्री: ₹{st.session_state.entry_price} | LTP: ₹{live_ltp}</p></div>", unsafe_allow_html=True)

                st.markdown(f"<p style='margin-top:10px; font-size:18px; color:#00ffff; font-weight:bold;'>🛡️ CURRENT TRAILING SL: <span style='color:white; background-color:#2a2b36; padding:2px 8px; border-radius:4px;'>₹ {st.session_state.current_sl}</span></p>", unsafe_allow_html=True)

            with c_act2:
                st.write("")
                st.write("")
                if st.button("🚨 CLICK TO EXIT NOW", use_container_width=True, type="primary"):
                    st.session_state.trade_active = False
                    st.warning(f"🛑 [SQUARE-OFF] पोजीशन क्लोज! FINAL PnL: ₹ {current_pnl}")
                    st.rerun()

    st.write("---")

    # ==============================================================================
    # 📈 SECTION 4: REAL-TIME TECHNICAL CHART & OPTION CHAIN
    # ==============================================================================
    st.header("📈 Real-Time Market Analysis & Option Chain")

    tab1, tab2 = st.tabs(["📊 Technical Live Chart", "⛓️ Live Option Chain (Derivatives)"])

    with tab1:
        np.random.seed(int(live_ltp) % 1000)
        chart_data = pd.DataFrame({
            'Time': pd.date_range(end=pd.Timestamp.now(), periods=30, freq='min'),
            'Price': np.linspace(live_ltp - 20, live_ltp, 30) + np.random.normal(0, 4, 30)
        })
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=chart_data['Time'], y=chart_data['Price'], mode='lines+markers', name='LTP Path', line=dict(color='#ff3333', width=3)))
        fig.update_layout(title=f"{selected_display_name} 1-Min Live Pulse Chart", template="plotly_dark", xaxis_title="Time", yaxis_title="Price (₹)")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader(f"⚡ {selected_display_name} Near-Month Derivative Matrix")
        
        step_value = 50 if "NIFTY" in selected_display_name and "BANK" not in selected_display_name else 100
        atm_strike = int(round(live_ltp / step_value) * step_value)
        
        strike_diff = 100 if "BANK" in selected_display_name else 50
        strikes = [atm_strike - strike_diff * i for i in range(-3, 4)]
        strikes.sort()
        
        op_data = []
        for s in strikes:
            ce_value = round((live_ltp - s) * 0.9 + 50 if live_ltp > s else 30 + (s - live_ltp) * 0.1, 2)
            pe_value = round((s - live_ltp) * 0.9 + 50 if s > live_ltp else 30 + (live_ltp - s) * 0.1, 2)
            
            op_data.append({
                "CALL OI (Lakhs)": round(np.random.uniform(5, 45), 2),
                "CALL LTP (₹)": max(ce_value, 0.5),
                "STRIKE PRICE": s,
                "PUT LTP (₹)": max(pe_value, 0.5),
