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

# --- Dynamic MCX Keys (Exact 2026 Live Formats) ---
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
        # बिल्कुल लाइव चलने वाले नवंबर/दिसंबर कॉन्ट्रैक्ट्स
        return {
            "GOLD": {"key": "MCX_FO|GOLD26DECFUT", "name": "GOLD 26DEC FUT"},
            "SILVER": {"key": "MCX_FO|SILVER26DECFUT", "name": "SILVER 26DEC FUT"},
            "CRUDEOIL": {"key": "MCX_FO|CRUDEOIL26NOVFUT", "name": "CRUDEOIL 26NOV FUT"},
            "NATURALGAS": {"key": "MCX_FO|NATURALGAS26NOVFUT", "name": "NATURALGAS 26NOV FUT"},
        }

with st.spinner("Upstox Live System se instruments update kar raha hu..."):
    MCX_MAP = load_latest_mcx_keys()

# आपके वर्किंग कोड की तरह यहाँ कॉमा से अलग की गई सिंगल स्ट्रिंग तैयार की जा रही है
MCX_KEYS = [v["key"] for v in MCX_MAP.values() if v is not None]
ALL_KEYS_LIST = MCX_KEYS + ["NSE_INDEX|Nifty 50"]
JOINED_KEYS_STRING = ",".join(ALL_KEYS_LIST)

# --- Fetch Data (Exactly matching your working code logic) ---
def get_ltp(joined_string):
    final = {}
    status = 0
    try:
        # आपके लाइव कोड की तरह सीधे सिंगल स्ट्रिंग पैरामीटर भेजा गया है
        r = requests.get("https://upstox.com",
                         headers=headers, params={"instrument_key": joined_string}, timeout=6)
        status = r.status_code
        if r.status_code == 200 and r.text:
            final = r.json().get("data", {})
    except Exception as e:
        pass
    return final, status

# --- UI Render ---
live_box = st.empty()

with live_box.container():
    prices, status = get_ltp(JOINED_KEYS_STRING)
    
    st.subheader("📊 MCX Live Rates")
    
    if status == 200:
        cols = st.columns(len(MCX_MAP))
        
        for idx, (sym, details) in enumerate(MCX_MAP.items()):
            if details:
                key = details["key"]
                clean_target = key.split('|')[-1].upper()
                ltp_value = "Updating..."
                
                # सेफ मैचिंग लूप
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
        
        # Nifty Display (वर्किंग कोड आधारित)
        nifty_val = "Updating..."
        if "NSE_INDEX|Nifty 50" in prices:
            nifty_val = prices["NSE_INDEX|Nifty 50"].get("last_price", "Updating...")
        else:
            for r_key, q_data in prices.items():
                if "NIFTY" in r_key.upper():
                    nifty_val = q_data.get("last_price", "Updating...")
                    break
                    
        st.info(f"📈 Nifty 50 Live: {nifty_val}")
        
        # Raw Debug Window
        st.subheader("🔍 Live API Data Stream (Debug)")
        st.json(prices)
        
        st.caption(f"Last updated at: {datetime.now().strftime('%H:%M:%S')} | Connection: Stable")
    else:
        st.error(f"Upstox Client connect to hai par response khali hai. Status Code: {status}")

# --- Loop Rerun ---
if st.session_state.auto:
    time.sleep(5)
    st.rerun()
