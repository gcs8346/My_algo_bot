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

# --- Fetch Dynamic MCX Keys ---
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
                filtered = filtered.sort_values(by='expiry')
                row = filtered.iloc[0]
                # Upstox API v3 requires lower case instrument keys!
                return {"key": str(row['instrument_key']).lower(), "name": row['trading_symbol']}
            return None

        res = {
            "GOLD": get_key("GOLD"),
            "SILVER": get_key("SILVER"),
            "CRUDEOIL": get_key("CRUDEOIL"),
            "NATURALGAS": get_key("NATURALGAS")
        }
        if res["CRUDEOIL"] is not None:
            return res
        raise Exception("Empty CSV")
    except:
        # Fallback with strict lowercase instrument keys
        return {
            "GOLD": {"key": "mcx_fo|mcxgold26decfut", "name": "GOLD 26DEC FUT"},
            "SILVER": {"key": "mcx_fo|mcxsilver26decfut", "name": "SILVER 26DEC FUT"},
            "CRUDEOIL": {"key": "mcx_fo|mcxcrudeoil26novfut", "name": "CRUDEOIL 26NOV FUT"},
            "NATURALGAS": {"key": "mcx_fo|mcxnaturalgas26octfut", "name": "NATURALGAS 26OCT FUT"},
        }

with st.spinner("Upstox se active instruments list read kar raha hu..."):
    MCX_MAP = load_latest_mcx_keys()

# Prepare clean keys string
MCX_KEYS = [v["key"] for v in MCX_MAP.values() if v is not None]
ALL_KEYS = MCX_KEYS + ["nse_index|nifty 50"]

# --- Fetch Data (Safeguarded against JSON crash) ---
def get_ltp(keys):
    final = {}
    status = 0
    joined = ",".join(keys)
    try:
        r = requests.get("https://upstox.com",
                         headers=headers, params={"instrument_key": joined}, timeout=5)
        status = r.status_code
        if r.status_code == 200:
            if r.text and r.text.strip() and not r.text.strip().startswith("<"):
                final = r.json().get("data", {})
            else:
                st.warning("Server sent non-JSON HTML content.")
    except Exception as e:
        pass
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
                key = details["key"]
                # Match by checking exact string or case-insensitive match
                ltp_value = "Updating..."
                if key in prices:
                    ltp_value = prices[key].get("last_price", "Updating...")
                else:
                    for k, v in prices.items():
                        if k.lower() == key.lower() or key.split('|')[-1] in k.lower():
                            ltp_value = v.get("last_price", "Updating...")
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
        st.caption(f"Last updated at: {datetime.now().strftime('%H:%M:%S')} | Connection: Stable")
    else:
        st.error(f"Upstox Client connect nahi ho saka. Status Code: {status}")
        st.info("Agar Status 200 ke alawa kuch hai, toh aapka Token expire ho chuka hai.")

# --- Loop Rerun ---
if st.session_state.auto:
    time.sleep(5)
    st.rerun()
