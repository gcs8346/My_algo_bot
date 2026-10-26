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

# --- Token Processing ---
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
    "Accept": "application/json"
}

# --- 2026 Active Contracts Locator ---
@st.cache_data(ttl=1800)
def load_latest_mcx_keys():
    try:
        url = "https://upstox.com"
        df = pd.read_csv(url, compression='gzip')
        mcx_df = df[(df['exchange'] == 'MCX') & (df['instrument_type'] == 'FUT')].copy()
        
        def get_exact_numeric_key(prefix):
            filtered = mcx_df[mcx_df['trading_symbol'].str.startswith(prefix)]
            if not filtered.empty:
                filtered = filtered.sort_values(by='expiry')
                row = filtered.iloc
                return {"key": str(row['instrument_key']), "name": str(row['trading_symbol'])}
            return None

        res = {
            "GOLD": get_exact_numeric_key("GOLD"),
            "SILVER": get_exact_numeric_key("SILVER"),
            "CRUDEOIL": get_exact_numeric_key("CRUDEOIL"),
            "NATURALGAS": get_exact_numeric_key("NATURALGAS")
        }
        if res["CRUDEOIL"] is not None:
            return res
        raise Exception("Fallback")
    except:
        return {
            "GOLD": {"key": "MCX_FO|GOLD26DECFUT", "name": "GOLD 26DEC FUT"},
            "SILVER": {"key": "MCX_FO|SILVER26DECFUT", "name": "SILVER 26DEC FUT"},
            "CRUDEOIL": {"key": "MCX_FO|CRUDEOIL26NOVFUT", "name": "CRUDEOIL 26NOV FUT"},
            "NATURALGAS": {"key": "MCX_FO|NATURALGAS26NOVFUT", "name": "NATURALGAS 26NOV FUT"},
        }

with st.spinner("Upstox System se exact Numbers trace kar raha hu..."):
    MCX_MAP = load_latest_mcx_keys()

# चाबियों की कंबाइंड लिस्ट
ALL_KEYS_LIST = ["NSE_INDEX|Nifty 50"]
for v in MCX_MAP.values():
    if v:
        ALL_KEYS_LIST.append(v["key"])
        clean_symbol = v["key"].split('|')[-1]
        ALL_KEYS_LIST.append(f"MCX_FO|{clean_symbol}")

JOINED_KEYS_STRING = ",".join(list(set(ALL_KEYS_LIST)))

# --- Fetch Data & Detailed Diagnostic Logging ---
def get_ltp_with_diagnostics(joined_string):
    final = {}
    status = 0
    raw_response_text = ""
    response_headers = {}
    
    try:
        encoded_url = requests.utils.requote_uri(f"https://upstox.com{joined_string}")
        r = requests.get(encoded_url, headers=headers, timeout=6)
        
        status = r.status_code
        response_headers = dict(r.headers)
        raw_response_text = r.text
        
        if r.status_code == 200 and r.text:
            final = r.json().get("data", {})
    except Exception as e:
        raw_response_text = f"Network/Code Exception: {str(e)}"
        
    return final, status, raw_response_text, response_headers

# --- UI Render ---
live_box = st.empty()

with live_box.container():
    prices, status, raw_text, resp_headers = get_ltp_with_diagnostics(JOINED_KEYS_STRING)
    
    st.subheader("📊 MCX Live Rates")
    
    cols = st.columns(len(MCX_MAP))
    for idx, (sym, details) in enumerate(MCX_MAP.items()):
        if details:
            key = details["key"]
            clean_target = key.split('|')[-1].upper()
            ltp_value = "Updating..."
            
            for response_key, quote_data in prices.items():
                if clean_target in response_key.upper() or response_key.upper() in key.upper():
                    ltp_value = quote_data.get("last_price", "Updating...")
                    break
            
            cols[idx].metric(label=details["name"], value=f"₹{ltp_value}" if ltp_value != "Updating..." else ltp_value)
    
    st.markdown("---")
    
    # Nifty Display
    nifty_val = "Updating..."
    for r_key, q_data in prices.items():
        if "NIFTY" in r_key.upper():
            nifty_val = q_data.get("last_price", "Updating...")
            break
    st.info(f"📈 Nifty 50 Live: {nifty_val}")
    
    # 🚨 --- सुपर डीबग विंडो (यह बताएगी असली कारण) --- 🚨
    st.markdown("### 🛠️ 100% Raw System Diagnostics (Asli Kaaran Window)")
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.write("**1. Server Se Aaya Asli Raw Text (JSON/HTML):**")
        st.code(raw_text, language="json" if not raw_text.startswith("<") else "html")
    
    with col_d2:
        st.write("**2. Server Metadata (Headers - Error Tracking):**")
        st.json(resp_headers)
        
    st.write(f"**Requested Keys Format sent to Upstox:** `{JOINED_KEYS_STRING}`")
    st.caption(f"Last updated at: {datetime.now().strftime('%H:%M:%S')} | Status Code: {status}")

# --- Loop Rerun ---
if st.session_state.auto:
    time.sleep(5)
    st.rerun()
