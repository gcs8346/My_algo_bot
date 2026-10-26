import streamlit as st
import requests
import time
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="TOWER V84 FINAL", layout="wide")
st.title("TOWER V84 - CENTURY FINAL 🔴 LIVE")

# --- Auto Refresh Controls ---
if "auto" not in st.session_state:
    st.session_state.auto = True

c1, c2 = st.columns([4, 1])
with c2:
    auto_on = st.toggle("Auto 5s", value=st.session_state.auto)
    st.session_state.auto = auto_on
    if st.button("🔄 Refresh"):
        st.rerun()

# --- Upstox Token Input ---
raw = st.text_input("Upstox Token (Roz Naya)", type="password")

# टोकन क्लीनिंग को पूरी तरह से सुरक्षित बनाया
if raw:
    token = raw.strip().replace("Bearer ", "").replace('"', '').replace("'", "").strip()
    st.session_state["tok"] = token
else:
    token = st.session_state.get("tok", "")

if not token or len(token) < 50:
    st.warning("Token daal de bhai - Roz subah naya banta hai")
    st.stop()

# Headers में आवश्यक Accept फ़ील्ड्स को सुधारा
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# --- Fetch Dynamic MCX Keys ---
@st.cache_data(ttl=3600)
def load_latest_mcx_keys():
    try:
        url = "https://upstox.com"
        df = pd.read_csv(url, compression='gzip')
        mcx_df = df[df['exchange'] == 'MCX']
        
        def get_key(prefix):
            filtered = mcx_df[
                (mcx_df['trading_symbol'].str.startswith(prefix)) & 
                (mcx_df['instrument_type'] == 'FUT')
            ]
            if not filtered.empty:
                filtered = filtered.sort_values(by='expiry')
                row = filtered.iloc[0]
                return {"key": row['instrument_key'], "name": row['trading_symbol']}
            return None

        return {
            "GOLD": get_key("GOLD"),
            "SILVER": get_key("SILVER"),
            "CRUDEOIL": get_key("CRUDEOIL"),
            "NATURALGAS": get_key("NATURALGAS")
        }
    except Exception as e:
        return {
            "GOLD": {"key": "MCX_FO|495213", "name": "GOLD FUT (Backup)"},
            "SILVER": {"key": "MCX_FO|495214", "name": "SILVER FUT (Backup)"},
            "CRUDEOIL": {"key": "MCX_FO|573422", "name": "CRUDEOIL FUT (Backup)"},
            "NATURALGAS": {"key": "MCX_FO|570750", "name": "NATURALGAS FUT (Backup)"},
        }

with st.spinner("Upstox se aaj ke latest MCX codes nikal raha hu..."):
    MCX_MAP = load_latest_mcx_keys()

# Prepare Request Keys
MCX_KEYS = [v["key"] for v in MCX_MAP.values() if v is not None]
ALL_KEYS = MCX_KEYS + ["NSE_INDEX|Nifty 50"]

# --- Fetch LTP Function (Error Handling Added) ---
def get_ltp(keys):
    final = {}
    status = 0
    joined = ",".join(keys)
    try:
        r = requests.get("https://api.upstox.com/v3/market-quote/ltp",
                         headers=headers, params={"instrument_key": joined}, timeout=7)
        status = r.status_code
        
        if r.status_code == 200:
            # चेक करें कि रिस्पॉन्स खाली तो नहीं है
            if r.text and r.text.strip():
                try:
                    data = r.json().get("data", {})
                    for trade_sym, quote in data.items():
                        final[trade_sym] = quote
                except Exception as json_err:
                    st.error(f"JSON Parsing Error: {json_err}. Server sent invalid JSON.")
            else:
                st.warning("Server se khali response aaya.")
        elif r.status_code == 401:
            st.error("Token expire ho gaya ya galat hai - Naya token daal.")
            st.stop()
        else:
            st.error(f"Upstox API Error Status: {r.status_code}. Response: {r.text}")
            
    except Exception as e:
        st.warning(f"Network/API Connection error: {e}")
    return final, status

# --- Live Display Container ---
live_box = st.empty()

with live_box.container():
    prices, status = get_ltp(ALL_KEYS)
    
    if prices:
        st.subheader("📊 MCX Live Rates")
        cols = st.columns(len(MCX_MAP))
        
        for idx, (sym, details) in enumerate(MCX_MAP.items()):
            if details:
                key = details["key"]
                if key in prices:
                    ltp = prices[key].get("last_price", "N/A")
                    cols[idx].metric(label=details["name"], value=f"₹{ltp}")
                else:
                    cols[idx].metric(label=details["name"], value="No Data")
        
        st.markdown("---")
        if "NSE_INDEX|Nifty 50" in prices:
            nifty_ltp = prices["NSE_INDEX|Nifty 50"].get("last_price", "N/A")
            st.info(f"📈 Nifty 50 Live: {nifty_ltp}")
            
        st.caption(f"Last updated at: {datetime.now().strftime('%H:%M:%S')} | API Status: {status}")
    else:
        # क्रैश होने के बजाय स्क्रीन पर सीधे अपस्टॉक्स का स्टेटस कोड दिखेगा ताकि समस्या पकड़ी जा सके
        st.error(f"Upstox API se data nahi mila. Status Code: {status}")
        st.info("Agar Status Code 401/400 hai, toh aapka Token sahi se format nahi hua hai. Naya Token generate karke daalein.")

# --- Stable Auto Refresh Loop ---
if st.session_state.auto:
    time.sleep(5)
    st.rerun()
