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

# --- 2026/Current Live MCX Mapping (Dynamic + Solid Fallback) ---
@st.cache_data(ttl=1800)
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
                filtered = filtered.sort_values(by='expiry')
                row = filtered.iloc
                return {"key": str(row['instrument_key']), "name": str(row['trading_symbol'])}
            return None

        res = {
            "GOLD": get_key("GOLD"),
            "SILVER": get_key("SILVER"),
            "CRUDEOIL": get_key("CRUDEOIL"),
            "NATURALGAS": get_key("NATURALGAS")
        }
        if res["CRUDEOIL"] is not None:
            return res
        raise Exception("CSV Empty")
    except:
        # 2026 के लाइव बेस कॉन्ट्रैक्ट्स
        return {
            "GOLD": {"key": "GOLD26DECFUT", "name": "GOLD 26DEC FUT"},
            "SILVER": {"key": "SILVER26DECFUT", "name": "SILVER 26DEC FUT"},
            "CRUDEOIL": {"key": "CRUDEOIL26NOVFUT", "name": "CRUDEOIL 26NOV FUT"},
            "NATURALGAS": {"key": "NATURALGAS26NOVFUT", "name": "NATURALGAS 26NOV FUT"},
        }

with st.spinner("Upstox Live System se instruments update kar raha hu..."):
    MCX_MAP = load_latest_mcx_keys()

# --- महा-सूची निर्माण (Omni-Format Key Generation) ---
# अपस्टॉक्स को किसी भी फ़ॉर्मेट में भ्रम न हो, इसलिए हम सभी संभावित फ़ॉर्मेट्स एक साथ भेजेंगे
REQUEST_KEYS = []
for v in MCX_MAP.values():
    if v:
        base_key = v["key"].split('|')[-1]
        # 1. बड़े अक्षरों में प्रिफिक्स के साथ
        REQUEST_KEYS.append(f"MCX_FO|{base_key.upper()}")
        # 2. छोटे अक्षरों में प्रिफिक्स के साथ
        REQUEST_KEYS.append(f"mcx_fo|{base_key.lower()}")
        # 3. बिना प्रिफिक्स के शुद्ध नाम
        REQUEST_KEYS.append(base_key.upper())
        REQUEST_KEYS.append(base_key.lower())

# निफ्टी के भी दोनों संभावित फ़ॉर्मेट्स जोड़ें
REQUEST_KEYS.extend(["NSE_INDEX|Nifty 50", "NSE_INDEX|NIFTY50", "nse_index|nifty 50"])
ALL_KEYS = list(set(REQUEST_KEYS))

# --- Fetch Data ---
def get_ltp(keys):
    final = {}
    status = 0
    try:
        # अपस्टॉक्स के नियमानुसार लिस्ट को सीधे URL पैरामीटर्स के रूप में भेजना
        r = requests.get("https://upstox.com",
                         headers=headers, params={"instrument_key": keys}, timeout=6)
        status = r.status_code
        if r.status_code == 200 and r.text:
            final = r.json().get("data", {})
    except Exception as e:
        pass
    return final, status

# --- UI Render ---
live_box = st.empty()

with live_box.container():
    prices, status = get_ltp(ALL_KEYS)
    
    st.subheader("📊 MCX Live Rates")
    
    if status == 200:
        cols = st.columns(len(MCX_MAP))
        
        for idx, (sym, details) in enumerate(MCX_MAP.items()):
            if details:
                base_name = details["key"].split('|')[-1].upper()
                ltp_value = "Updating..."
                
                # रिस्पॉन्स में आए डेटा में से सही भाव ढूंढना (चाहे वह किसी भी केस/फ़ॉर्मेट में आया हो)
                for response_key, quote_data in prices.items():
                    clean_resp_key = response_key.split('|')[-1].upper()
                    if base_name in clean_resp_key or clean_resp_key in base_name:
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
        
        # Raw Data Stream Window
        st.subheader("🔍 Live API Data Stream (Debug)")
        st.json(prices)
        
        st.caption(f"Last updated at: {datetime.now().strftime('%H:%M:%S')} | Connection: Stable")
    else:
        st.error(f"Upstox Client connect to hai par response khali hai. Status Code: {status}")

# --- Loop Rerun ---
if st.session_state.auto:
    time.sleep(5)
    st.rerun()
