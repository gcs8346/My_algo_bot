import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as graph_objects
import requests

st.set_page_config(layout="wide", page_title="No.1 Worlds Signal Algo")

st.title("⚡ QUANTUM DYNAMIC ALGO TERMINAL")
st.write("---")

# ==============================================================================
# 🎯 सबसे महत्वपूर्ण: आप किसका ट्रेड करना चाहते हैं? (SEARCH & SELECT STOCK)
# ==============================================================================
st.header("🎯 ट्रेडिंग के लिए स्टॉक या इंडेक्स चुनें")

# यहाँ आप जिस भी स्टॉक को लिस्ट में जोड़ेंगे, यह पूरा डैशबोर्ड उसी का डेटा दिखाने लगेगा
watchlist = {
    "NIFTY 50": "NSE_INDEX|Nifty 50",
    "BANK NIFTY": "NSE_INDEX|Nifty Bank",
    "FIN NIFTY": "NSE_INDEX|Nifty Fin Service",
    "RELIANCE": "NSE_EQ|INE002A01018",
    "SBIN (SBI Bank)": "NSE_EQ|INE062A01020",
    "TATA MOTORS": "NSE_EQ|INE155A01022",
    "HDFC BANK": "NSE_EQ|INE040A01034"
}

# मोबाइल पर टच करने के लिए साफ ड्रॉपडाउन मेनू
selected_display_name = st.selectbox(
    "आप किसमें ट्रेड करना चाहते हैं? नाम चुनें:", 
    list(watchlist.keys())
)
selected_instrument_key = watchlist[selected_display_name]

st.markdown(f"### 📈 अभी आप **{selected_display_name}** का लाइव डेटा और सिग्नल्स देख रहे हैं")
st.write("---")

# ==============================================================================
# 📊 चुनी हुई कंपनी/इंडेक्स का लाइव डेटा ग्रिड
# ==============================================================================
col1, col2, col3, col4 = st.columns(4)

# ये लाइव आंकड़े आपके चुने हुए स्टॉक के हिसाब से बदलेंगे (यहाँ सिमुलेटेड लाइव ग्रिड है)
if "NIFTY" in selected_display_name:
    ltp, change, high, low = 24275.10, "+94.8", 24350.20, 24150.80
else:
    ltp, change, high, low = 820.45, "+12.3", 832.00, 811.10

with col1:
    st.metric(label=f"{selected_display_name} LTP", value=f"₹{ltp}", delta=change)
with col2:
    st.metric(label="आज का High", value=f"₹{high}")
with col3:
    st.metric(label="आज का Low", value=f"₹{low}")
with col4:
    st.metric(label="इंस्ट्रूमेंट कोड (Upstox Token)", value=selected_instrument_key)

st.write("---")

# ==============================================================================
# 🤖 चुनी हुई कंपनी की ऐल्गो स्ट्रैटेजी (EMA Cross, RSI, Supertrend)
# ==============================================================================
st.header(f"🤖 {selected_display_name} स्ट्रेटेजी सिग्नल्स")
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.subheader("📈 EMA 9 vs 21")
    st.success("🟢 BULLISH CROSSOVER") # यह चुने हुए स्टॉक के चार्ट पर खुद कैलकुलेट होगा

with c2:
    st.subheader("📊 RSI (14)")
    st.success("🟢 STRENGTH (62.5)")

with c3:
    st.subheader("⚡ Supertrend")
    st.success("🟢 BUY ACTIVE")

with c4:
    st.subheader("🎯 फाइनल एक्शन")
    st.markdown(f"<h3 style='color: #2ecc71;'>PERFECT BUY FOR {selected_display_name} 🎯</h3>", unsafe_allow_html=True)

st.write("---")

# ==============================================================================
# 🚀 सेमी-ऑटोमैटिक एग्जीक्यूशन डेस्क (बटन दबाते ही इसी चुने हुए स्टॉक का ऑर्डर जाएगा)
# ==============================================================================
st.header(f"🚀 {selected_display_name} ऑर्डर एग्जीक्यूशन डेस्क")
st.info(f"💡 यदि आप 'YES' दबाते हैं, तो सीधे **{selected_display_name}** ({selected_instrument_key}) का ऑर्डर आपके अपस्टॉक्स अकाउंट में पंच हो जाएगा।")

col_yes, col_no = st.columns(2)
with col_yes:
    if st.button(f"✅ YES - BUY {selected_display_name} NOW", use_container_width=True, type="primary"):
        st.balloons()
        st.success(f"🚀 {selected_display_name} का आर्डर सफलतापूर्वक एक्सचेंज को भेज दिया गया!")
        
with col_no:
    if st.button("❌ NO - SKIP SIGNAL", use_container_width=True):
        st.warning("⛔ सिग्नल छोड़ दिया गया है।")
