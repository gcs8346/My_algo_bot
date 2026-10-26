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

# --- Fetch Dynamic Live MCX Keys (Updated for exact 2026 contract match) ---
@st.cache_data(ttl=1800)
def load_latest_mcx_keys():
    try:
        url = "https://upstox.com"
        df = pd.read_csv(url, compression='gzip')
        
        # फ़िल्टर केवल MCX सेगमेंट के लिए
        mcx_df = df[df['exchange'] == 'MCX'].copy()
        
        # केवल फ्यूचर कॉन्ट्रैक्ट्स
        mcx_df = mcx_df[mcx_df['instrument_type'] == 'FUT']
        
        def get_exact_key(symbol_name):
            # उदाहरण के लिए जो सिंबल CRUDEOIL से शुरू होते हैं
            filtered = mcx_df[mcx_df['trading_symbol'].str.startswith(symbol_name)]
            if not filtered.empty:
                # एक्सपायरी के हिसाब से सॉर्ट करें ताकि करंट मंथ (सबसे पास वाला) सबसे ऊपर आए
                filtered = filtered.sort_values(by='expiry')
                row = filtered.iloc[0]
                return {"key": str(row['instrument_key']), "name": str(row['trading_symbol'])}
            return None

        res = {
            "GOLD": get_exact_key("GOLD"),
            "SILVER": get_exact_key("SILVER"),
            "CRUDEOIL": get_exact_key("CRUDEOIL"),
            "NATURALGAS": get_exact_key("NATURALGAS")
        }
        
        if res["CRUDEOIL"] is not None:
            return res
        raise Exception("Dynamic fetch failed, trying fallback")
    except Exception as e:
        # अगर नेटवर्क या फाइल फेल हो तो आज रात के लाइव वर्किंग सिम्बल्स का बैकअप ढांचा
        return {
            "GOLD": {"key": "MCX_FO|MCXGOLD26DECFUT", "name": "GOLD DEC FUT"},
            "SILVER": {"key": "MCX_FO|MCXSILVER26DECFUT", "name": "SILVER DEC FUT"},
            "CRUDEOIL": {"key": "MCX_FO|MCXCRUDEOIL26NOVFUT", "name": "CRUDEOIL NOV FUT"},
            "NATURALGAS": {"key": "MCX_FO|MCXNATURALGAS26OCTFUT", "name": "NATURALGAS OCT FUT"},
        }

with st.spinner("Upstox Live Database se active instruments download ho rahe hain..."):
    MCX_MAP = load_latest_mcx_keys()

# चाबियों की लिस्ट तैयार करें
MCX_KEYS = [v["key"] for v in MCX_MAP.values() if v is not None]
ALL_KEYS = MCX_KEYS + ["NSE_INDEX|Nifty 50"]

# --- Fetch Data Function ---
def get_ltp(keys):
    final = {}
    status = 0
    joined = ",".join(keys)
    try:
        r = requests.get("https://upstox.com",
                         headers=headers, params={"instrument_key": joined}, timeout=6)
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
                key = details["key"]
                ltp_value = "Updating..."
                
                # फ्लेक्सिबल मिलान: कीज को डायरेक्ट या पार्शियल चेक करना
                if key in prices:
                    ltp_value = prices[key].get("last_price", "Updating...")
                else:
                    for response_key, quote_data in prices.items():
                        if response_key.lower() == key.lower() or key.split('|')[-1].lower() in response_key.lower():
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
        
        # सेफगार्ड: अगर स्क्रीन पर भाव न दिखें, तो लाइव आने वाला कच्चा रिस्पॉन्स यहाँ छप जाएगा
        st.subheader("🔍 Live API Data Stream (Debug)")
        st.json(prices)
        
        st.caption(f"Last updated at: {datetime.now().strftime('%H:%M:%S')} | Connection: Stable")
    else:
        st.error(f"Upstox Client connect to hai par response khali hai. Status Code: {status}")

# --- Loop Rerun ---
if st.session_state.auto:
    time.sleep(5)
    st.rerun()
