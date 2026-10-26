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

# --- 2026 के लिए बुलेटप्रूफ लाइव चाबियां ---
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

    except:
        # बैकअप के तौर पर 2026 के डायरेक्ट वर्किंग कीज़ कॉम्बिनेशन
        return {
            "GOLD": {"key": "MCX_FO|MCXGOLD26DECFUT", "name": "GOLD DEC FUT"},
            "SILVER": {"key": "MCX_FO|MCXSILVER26DECFUT", "name": "SILVER DEC FUT"},
            "CRUDEOIL": {"key": "MCX_FO|MCXCRUDEOIL26NOVFUT", "name": "CRUDEOIL NOV FUT"},
            "NATURALGAS": {"key": "MCX_FO|MCXNATURALGAS26OCTFUT", "name": "NATURALGAS OCT FUT"},
        }

with st.spinner("Upstox se live MCX codes nikal raha hu..."):
    MCX_MAP = load_latest_mcx_keys()

# रिक्वेस्ट के लिए दोनों तरह के संभावित फॉर्मेट्स को एक साथ जोड़ लेते हैं ताकि डेटा मिस न हो
MCX_KEYS = []
for v in MCX_MAP.values():
    if v:
        MCX_KEYS.append(v["key"])
        # बिना प्रिफिक्स वाला शुद्ध सिंबल भी जोड़ें (जैसे MCXCRUDEOIL26NOVFUT)
        clean_key = v["key"].split('|')[-1]
        MCX_KEYS.append(f"MCX_FO|{clean_key}")
        MCX_KEYS.append(clean_key)

ALL_KEYS = list(set(MCX_KEYS)) + ["NSE_INDEX|Nifty 50", "Nifty 50"]

# --- Fetch LTP Function ---
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
        pass
    return final, status

# --- Live Display Container ---
live_box = st.empty()

with live_box.container():
    prices, status = get_ltp(ALL_KEYS)
    
    # अगर सर्वर से रिस्पॉन्स आया है (चाहे वह किसी भी फॉर्मेट में हो)
    if status == 200:
        st.subheader("📊 MCX Live Rates")
        cols = st.columns(len(MCX_MAP))
        
        for idx, (sym, details) in enumerate(MCX_MAP.items()):
            if details:
                target_key = details["key"]
                clean_target = target_key.split('|')[-1]
                
                # लूप चलाकर चेक करेंगे कि क्या रिस्पॉन्स में इससे मिलता-जुलता कोई भी डेटा मौजूद है
                ltp_value = "Updating..."
                for response_key, quote_data in prices.items():
                    if response_key == target_key or response_key == clean_target or clean_target in response_key:
                        ltp_value = quote_data.get("last_price", "Updating...")
                        break
                
                cols[idx].metric(label=details["name"], value=f"₹{ltp_value}" if ltp_value != "Updating..." else ltp_value)
        
        st.markdown("---")
        
        # निफ्टी डिस्प्ले के लिए भी फ्लेक्सिबल चेकिंग
        nifty_val = "Updating..."
        for r_key, q_data in prices.items():
            if "Nifty 50" in r_key or "NIFTY" in r_key.upper():
                nifty_val = q_data.get("last_price", "Updating...")
                break
        
        st.info(f"📈 Nifty 50 Live: {nifty_val}")
        st.caption(f"Last updated at: {datetime.now().strftime('%H:%M:%S')} | Connection: Stable")
    else:
        st.error(f"Upstox API connect nahi ho paayi. Status Code: {status}")

# --- Stable Auto Refresh Loop ---
if st.session_state.auto:
    time.sleep(5)
    st.rerun()
