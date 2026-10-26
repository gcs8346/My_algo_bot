import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="TOWER V87 FIXED", layout="wide")
st.title("TOWER V87 - LOOP FIX 🔴")

# --- Token - Simple, No Rerun Loop ---
token_input = st.text_input("Upstox Token (Roz Naya)", type="password", key="token_box")

# Agar box me kuch likha hai toh save karo, bina rerun ke
if token_input and len(token_input.strip()) > 50:
    st.session_state.tok = token_input.strip().replace("Bearer ","").strip()

token = st.session_state.get("tok","")

if not token or len(token) < 50:
    st.warning("Token daal - https://api.upstox.com/v2/login se roz naya banta hai")
    st.stop()

st.success(f"Token OK - {len(token)} chars - {datetime.now().strftime('%H:%M:%S')}")

if st.button("🔄 REFRESH LIVE", type="primary"):
    st.rerun()

headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

KEYS = ["MCX_FO|495213","MCX_FO|495214","MCX_FO|573422","MCX_FO|570750"]
NAMES = ["GOLD","SILVER","CRUDEOIL","NATURALGAS"]

prices = {}
status = 0
debug = ""

for k in KEYS:
    try:
        r = requests.get("https://api.upstox.com/v3/market-quote/ltp",
                         headers=headers, params={"instrument_key": k}, timeout=15)
        status = r.status_code
        debug = r.text[:2000]
        if r.status_code == 200:
            data = r.json().get("data", {})
            for _, q in data.items():
                inst = q.get("instrument_token")
                if inst:
                    prices[inst] = q
        else:
            st.error(f"API Status {status} - Token expire ho sakta hai")
            st.code(debug)
            st.stop()
    except Exception as e:
        st.error(f"Error {e}")
        st.stop()

# --- LIVE ---
if prices:
    cols = st.columns(4)
    for i, k in enumerate(KEYS):
        q = prices.get(k, {})
        last = q.get("last_price")
        with cols[i]:
            if last:
                st.metric(NAMES[i], f"₹{last}", f"CP {q.get('cp')}")
                st.caption(f"LTQ {q.get('ltq')} Vol {q.get('volume')}")
            else:
                st.metric(NAMES[i], "WAIT", k)
    
    with st.expander("Full LIVE JSON"):
        st.json(prices)
else:
    st.error(f"Kuch nahi aaya - Status {status}")
    st.code(debug)

st.caption(f"V87 FIXED | {datetime.now().strftime('%d-%m %H:%M:%S')} | Loop hataya")