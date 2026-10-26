import streamlit as st
import requests
import time
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="TOWER V84 FINAL", layout="wide")
st.title("TOWER V84 - CENTURY FINAL 🔴 LIVE")

# --- Auto Refresh Controls (Columns Issue Fixed Here) ---
if "auto" not in st.session_state:
    st.session_state.auto = True

# st.columns(2) लिखकर संख्या को फिक्स किया ताकि एरर न आए
c1, c2 = st.columns(2)
with c2:
    auto_on = st.toggle("Auto 5s", value=st.session_state.auto)
    st.session_state.auto = auto_on
    if st.button("🔄 Refresh"):
        st.rerun()

# --- Upstox Token Input ---
raw = st.text_input("Upstox Token (Roz Naya)", type="password")

if raw:
    token = raw.strip().replace("Bearer ", "").replace('"', '').replace("'", "").strip()
    st.session_state["tok"] = token
else:
    token = st.session_state.get("tok", "")

if not token or len(token) < 50:
    st.warning("Token daal de bhai - Roz subah naya banta hai")
    st.stop()

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
        
        mcx_df = df[df['exchange'] == 'MCX'].copy()
        mcx_df['expiry'] = pd.to_datetime(mcx_df['expiry'])
        
        today = pd.to_datetime(datetime.now().date())
        mcx_df = mcx_df[mcx_df['expiry'] >= today]

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

        res = {
            "GOLD": get_key("GOLD"),
            "SILVER": get_key("SILVER"),
            "CRUDEOIL": get_key("CRUDEOIL"),
            "NATURALGAS": get_key("NATURALGAS")
        }
        
        if res["CRUDEOIL"] is not None:
            return res
        raise Exception("Data empty")

    except Exception as e:
        # Fallback keys logic
        return {
            "GOLD": {"key": "MCX_FO|MCXGOLD26DECFUT", "name": "GOLD DEC FUT (Live)"},
            "SILVER": {"key": "MCX_FO|MCXSILVER26DECFUT", "name": "SILVER DEC FUT (Live)"},
            "CRUDEOIL": {"key": "MCX_FO|MCXCRUDEOIL26NOVFUT", "name": "CRUDEOIL NOV FUT (Live)"},
            "NATURALGAS": {"key": "MCX_FO|MCXNATURALGAS26OCTFUT", "name": "NATURALGAS OCT FUT (Live)"},
        }

with st.spinner("Upstox se live MCX codes nikal raha hu..."):
    MCX_MAP = load_latest_mcx_keys()

MCX_KEYS = [v["key"] for v in MCX_MAP.values() if v is not None]
ALL_KEYS = MCX_KEYS + ["NSE_INDEX|Nifty 50"]

# --- Fetch LTP Function ---
def get_ltp(keys):
    final = {}
    status = 0
    joined = ",".join(keys)
    try:
        r = requests.get("https://upstox.com",
                         headers=headers, params={"instrument_key": joined}, timeout=7)
        status = r.status_code
        
        if r.status_code == 200 and r.text:
            data = r.json().get("data", {})
            for trade_sym, quote in data.items():
                final[trade_sym] = quote
        elif r.status_code == 401:
            st.error("Token expire ho gaya ya galat hai.")
            st.stop()
    except Exception as e:
        pass
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
                    matched = False
                    for k, v in prices.items():
                        if sym in k or (isinstance(key, str) and key.split('|')[-1] in k):
                            ltp = v.get("last_price", "N/A")
                            cols[idx].metric(label=details["name"], value=f"₹{ltp}")
                            matched = True
                            break
                    if not matched:
                        cols[idx].metric(label=details["name"], value="Updating...")
        
        st.markdown("---")
        if "NSE_INDEX|Nifty 50" in prices:
            nifty_ltp = prices["NSE_INDEX|Nifty 50"].get("last_price", "N/A")
            st.info(f"📈 Nifty 50 Live: {nifty_ltp}")
            
        st.caption(f"Last updated at: {datetime.now().strftime('%H:%M:%S')} | Status: {status}")
    else:
        st.error(f"Upstox API se data nahi mila. Status: {status}")

# --- Stable Auto Refresh Loop ---
if st.session_state.auto:
    time.sleep(5)
    st.rerun()
