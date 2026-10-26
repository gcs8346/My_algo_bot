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

# --- 2026 Active Contracts Dynamic Finder ---
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
                row = filtered.iloc[0]
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
        # बिल्कुल लाइव चलने वाले नवंबर/दिसंबर 2026 के चाबियों का शुद्ध बैकअप
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

# साफ कॉमा-सेपरेटेड स्ट्रिंग
JOINED_KEYS_STRING = ",".join(list(set(ALL_KEYS_LIST)))

# --- Fetch Data (URL Encoding Mismatch Fixed) ---
def get_ltp_clean(joined_string):
    final = {}
    status = 0
    raw_response_text = ""
    response_headers = {}
    
    try:
        # फिक्स: यूआरएल को मैन्युअल जोड़ने के बजाय requests के इन-बिल्ट 'params' को शुद्ध स्ट्रिंग थमा दी
        # इससे यूआरएल में डॉट टूटने की समस्या हमेशा के लिए खत्म हो गई
        r = requests.get(
            url="https://upstox.com",
            headers=headers,
            params={"instrument_key": joined_string},
            timeout=6
        )
        
        status = r.status_code
        response_headers = dict(r.headers)
        raw_response_text = r.text
        
        if r.status_code == 200 and r.text:
            final = r.json().get("data", {})
    except Exception as e:
        raw_response_text = f"Network Exception: {str(e)}"
        
    return final, status, raw_response_text, response_headers

# --- UI Render ---
live_box = st.empty()

with live_box.container():
    prices, status, raw_text, resp_headers = get_ltp_clean(JOINED_KEYS_STRING)
    
    st.subheader("📊 MCX Live Rates")
    
    cols = st.columns(len(MCX_MAP))
    for idx, (sym, details) in enumerate(MCX_MAP.items()):
        if details:
            key = details["key"]
            clean_target = key.split('|')[-1].upper()
            ltp_value = "Updating..."
            
            # सेफ डेटा मैचिंग
            if key in prices:
                ltp_value = prices[key].get("last_price", "Updating...")
            elif key.lower() in prices:
                ltp_value = prices[key.lower()].get("last_price", "Updating...")
            else:
                for response_key, quote_data in prices.items():
                    if clean_target in response_key.upper() or response_key.upper() in key.upper():
                        ltp_value = quote_data.get("last_price", "Updating...")
                        break
            
            cols[idx].metric(label=details["name"], value=f"₹{ltp_value}" if ltp_value != "Updating..." else ltp_value)
    
    st.markdown("---")
    
    # Nifty Display
    nifty_val = "Updating..."
    if "NSE_INDEX|Nifty 50" in prices:
        nifty_val = prices["NSE_INDEX|Nifty 50"].get("last_price", "Updating...")
    else:
        for r_key, q_data in prices.items():
            if "NIFTY" in r_key.upper():
                nifty_val = q_data.get("last_price", "Updating...")
                break
    st.info(f"📈 Nifty 50 Live: {nifty_val}")
    
    # Raw Diagnostics
    st.markdown("### 🛠️ Raw Diagnostics")
    st.code(raw_text, language="json" if not raw_text.startswith("<") else "html")
    st.json(resp_headers)
    
    st.caption(f"Last updated at: {datetime.now().strftime('%H:%M:%S')} | Status Code: {status}")

# --- Loop Rerun ---
if st.session_state.auto:
    time.sleep(5)
    st.rerun()
