import streamlit as st
import requests
import time
from datetime import datetime

st.set_page_config(page_title="TOWER V84 FINAL", layout="wide")
st.title("TOWER V84 - CENTURY FINAL 🔴 LIVE")

# --- Auto Refresh Logic (Fixes Sleep/Freeze Mode) ---
if "auto" not in st.session_state:
    st.session_state.auto = True

c1, c2 = st.columns([4, 1])
with c2:
    auto_on = st.toggle("Auto 5s", value=st.session_state.auto)
    st.session_state.auto = auto_on
    if st.button("🔄 Refresh"):
        st.rerun()

# --- Token Processing ---
raw = st.text_input("Upstox Token (Roz Naya)", type="password")
token = raw.strip().replace("Bearer ", "").strip() if raw else st.session_state.get("tok", "")
if raw:
    st.session_state["tok"] = token
if not token or len(token) < 50:
    st.warning("Token daal de bhai - Roz subah naya banta hai")
    st.stop()

headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

# --- Instrument Maps ---
MCX_MAP = {
    "GOLD": {"key": "MCX_FO|495213", "name": "GOLD 26DEC FUT - 1KG"},
    "SILVER": {"key": "MCX_FO|495214", "name": "SILVER 26DEC FUT - 30KG"},
    "CRUDEOIL": {"key": "MCX_FO|573422", "name": "CRUDEOIL 26NOV FUT"},
    "NATURALGAS": {"key": "MCX_FO|570750", "name": "NATURALGAS 26OCT FUT"},
}
MCX_KEYS = [v["key"] for v in MCX_MAP.values()]
ALL_KEYS = MCX_KEYS + ["NSE_INDEX|Nifty 50"]

def get_ltp(keys):
    final = {}
    status = 0
    # एक बार में भेजने के लिए कॉमा से अलग की गई स्ट्रिंग
    joined = ",".join(keys)
    try:
        # Upstox API v3 लूप के बिना एक बार में सभी 5 कीज़ का डेटा दे सकती है
        r = requests.get("https://api.upstox.com/v3/market-quote/ltp",
                         headers=headers, params={"instrument_key": joined}, timeout=5)
        status = r.status_code
        if r.status_code == 200:
            data = r.json().get("data", {})
            for trade_sym, quote in data.items():
                final[trade_sym] = quote
        elif r.status_code == 401:
            st.error("Token expire ho gaya - Upstox se naya token bana ke daal")
            st.stop()
    except Exception as e:
        st.warning(f"API error: {e}")
    return final, status

# --- Data Fetching Container ---
live_box = st.empty()

with live_box.container():
    prices, status = get_ltp(ALL_KEYS)
    
    # लाइव डेटा ग्रिड बनाने के लिए (उदाहरण)
    if prices:
        cols = st.columns(len(MCX_MAP))
        for idx, (sym, details) in enumerate(MCX_MAP.items()):
            key = details["key"]
            if key in prices:
                ltp = prices[key].get("last_price", "N/A")
                cols[idx].metric(label=details["name"], value=f"₹{ltp}")
        
        # निफ्टी का डेटा दिखाने के लिए
        if "NSE_INDEX|Nifty 50" in prices:
            nifty_ltp = prices["NSE_INDEX|Nifty 50"].get("last_price", "N/A")
            st.info(f"Nifty 50 Live: {nifty_ltp}")
            
        st.caption(f"Last updated at: {datetime.now().strftime('%H:%M:%S')}")
    else:
        st.error("Data nahi mila. Token ya instrument keys check karein.")

# --- Active Loop for Auto Refresh ---
if st.session_state.auto:
    time.sleep(5)
    st.rerun()
