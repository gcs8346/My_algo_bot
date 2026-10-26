import streamlit as st
import requests
import time
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="TOWER V84 FINAL", layout="wide")
st.title("TOWER V84 - CENTURY FINAL 🔴 LIVE")

# --- Auto Refresh ---
if "auto" not in st.session_state:
    st.session_state.auto = True

c1, c2 = st.columns(2)
with c2:
    auto_on = st.toggle("Auto 5s", value=st.session_state.auto)
    st.session_state.auto = auto_on
    if st.button("🔄 Refresh"):
        st.rerun()

# --- Token ---
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

# --- 2026/Current Live MCX Mapping Logic ---
@st.cache_data(ttl=3600)
def load_latest_mcx_keys():
    try:
        url = "https://upstox.com"
        df = pd.read_csv(url, compression='gzip')
        mcx_df = df[df['exchange'] == 'MCX'].copy()
        
        def get_key(prefix):
            filtered = mcx_df[
                (mcx_df['trading_symbol'].str.startswith(prefix)) & 
                (mcx_df['instrument_type'] == 'FUT')
            ]
            if not filtered.empty:
                # सबसे पास वाली एक्सपायरी को चुनें
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
        raise Exception("CSV data parse limit")
    except:
        # फ़ेल होने पर डायरेक्ट सिंबल स्ट्रिंग्स जो काम करती हैं
        return {
            "GOLD": {"key": "MCX_FO|MCXGOLD26DECFUT", "name": "GOLD DEC FUT"},
            "SILVER": {"key": "MCX_FO|MCXSILVER26DECFUT", "name": "SILVER DEC FUT"},
            "CRUDEOIL": {"key": "MCX_FO|MCXCRUDEOIL26NOVFUT", "name": "CRUDEOIL NOV FUT"},
            "NATURALGAS": {"key": "MCX_FO|MCXNATURALGAS26OCTFUT", "name": "NATURALGAS OCT FUT"},
        }

with st.spinner("Upstox se active instruments list read kar raha hu..."):
    MCX_MAP = load_latest_mcx_keys()

# सभी संभावित कीज़ को एक सूची में तैयार करें
MCX_KEYS = []
for v in MCX_MAP.values():
    if v:
        MCX_KEYS.append(v["key"])
        clean_k = v["key"].split('|')[-1]
        MCX_KEYS.append(clean_k)

ALL_KEYS = list(set(MCX_KEYS)) + ["NSE_INDEX|Nifty 50", "NSE_INDEX|NIFTY50"]

# --- Fetch Data ---
def get_ltp(keys):
    final = {}
    status = 0
    joined = ",".join([k for k in keys if k])
    try:
        r = requests.get("https://upstox.com",
                         headers=headers, params={"instrument_key": joined}, timeout=7)
        status = r.status_code
        if r.status_code == 200 and r.text:
            final = r.json().get("data", {})
    except Exception as e:
        st.warning(f"Connection timeout: {e}")
    return final, status

# --- UI Render ---
live_box = st.empty()

with live_box.container():
    prices, status = get_ltp(ALL_KEYS)
    
    if status == 200:
        st.subheader("📊 MCX Live Rates")
        cols = st.columns(len(MCX_MAP))
        
        for idx, (sym, details) in enumerate(MCX_MAP.items()):
            if details:
                target_key = details["key"]
                clean_target = target_key.split('|')[-1]
                
                ltp_value = None
                # सर्वर से मिले डेटा में सिंबल ढूंढें
                for response_key, quote_data in prices.items():
                    if clean_target in response_key or response_key in target_key:
                        ltp_value = quote_data.get("last_price")
                        break
                
                if ltp_value:
                    cols[idx].metric(label=details["name"], value=f"₹{ltp_value}")
                else:
                    cols[idx].metric(label=details["name"], value="No Feed")
        
        # Nifty Display
        st.markdown("---")
        nifty_val = "No Feed"
        for r_key, q_data in prices.items():
            if "NIFTY" in r_key.upper():
                nifty_val = q_data.get("last_price", "No Feed")
                break
        st.info(f"📈 Nifty 50 Live: {nifty_val}")
        
        # सेफ-गार्ड: अगर भाव फिर भी न दिखें, तो लाइव आने वाला कच्चा डेटा प्रिंट कर दें
        st.subheader("📡 Raw Server Data (Debug Window)")
        st.json(prices)
        
        st.caption(f"Last updated at: {datetime.now().strftime('%H:%M:%S')} | Status: {status}")
    else:
        st.error(f"Upstox Client connect nahi ho saka. Error Status: {status}")

# --- Loop Rerun ---
if st.session_state.auto:
    time.sleep(5)
    st.rerun()
