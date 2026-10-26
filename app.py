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
token = raw.strip().replace("Bearer ", "").strip() if raw else st.session_state.get("tok", "")
if raw:
    st.session_state["tok"] = token
if not token or len(token) < 50:
    st.warning("Token daal de bhai - Roz subah naya banta hai")
    st.stop()

headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

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

# --- Fetch LTP Function ---
def get_ltp(keys):
    final = {}
    status = 0
    joined = ",".join(keys)
    try:
        r = requests.get("https://upstox.com",
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

# --- Live Display Container ---
live_box = st.empty()

with live_box.container():
    prices, status = get_ltp(ALL_KEYS)
    
    if prices:
        # Display MCX Cards
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
        
        # Display Nifty Index
        st.markdown("---")
        if "NSE_INDEX|Nifty 50" in prices:
            nifty_ltp = prices["NSE_INDEX|Nifty 50"].get("last_price", "N/A")
            st.info(f"📈 Nifty 50 Live: {nifty_ltp}")
            
        st.caption(f"Last updated at: {datetime.now().strftime('%H:%M:%S')} | API Status: {status}")
    else:
        st.error("Upstox API se data nahi aa raha hai. Ek baar Token validation check karein.")

# --- Stable Auto Refresh Loop ---
if st.session_state.auto:
    time.sleep(5)
    st.rerun()
