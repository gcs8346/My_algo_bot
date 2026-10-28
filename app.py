import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import time

st.set_page_config(page_title="V96 SENSEX + OIL LIVE", layout="wide")
st.title("V96 - FINAL LIVE - TOWER + PCR READY ✅")

token_input = st.text_input("Upstox Token (Roz Naya)", type="password")
if token_input and len(token_input.strip()) > 50:
    st.session_state.tok = token_input.strip().replace("Bearer ", "").strip()

token = st.session_state.get("tok", "")
if not token or len(token) < 50:
    st.warning("Token daal ke ENTER maar")
    st.stop()

headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
st.success(f"Token OK ...{token[-10:]} | Time: {datetime.now().strftime('%H:%M:%S')}")

INSTRUMENTS = {
    "SENSEX": "BSE_INDEX|SENSEX",
    "BANKEX": "BSE_INDEX|BANKEX",
    "NIFTY 50": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
    "RELIANCE": "NSE_EQ|INE002A01018",
    "GOLD": "MCX_FO|495213",
    "CRUDEOIL": "MCX_FO|573422",
    "SILVER": "MCX_FO|495214",
}

# --- SIMPLE TEST WITHOUT FRAGMENT ---
st.divider()
st.write("### TESTING API...")

all_keys = list(INSTRUMENTS.values())
url = "https://api.upstox.com/v3/market-quote/ltp"
params = {"instrument_key": ",".join(all_keys)}

try:
    r = requests.get(url, headers=headers, params=params, timeout=15)
    st.write(f"**Status Code:** {r.status_code}")
    st.code(r.text[:2000])

    if r.status_code == 200:
        data = r.json().get("data", {})
        st.write(f"**LTP Keys Mila:** {len(data)}")
        for name, key in INSTRUMENTS.items():
            q = data.get(key, {})
            ltp = q.get("last_price", "NO DATA") if q else "NO KEY"
            st.metric(name, f"{ltp}")
    elif r.status_code == 401:
        st.error("❌ TOKEN EXPIRE - https://account.upstox.com/developer/apps se naya banao")
    else:
        st.error(f"API Fail {r.status_code}")

except Exception as e:
    st.error(f"Network Error: {e}")
    st.info("Streamlit Cloud ka net slow hai - 10 sec ruk ke REFRESH maar")

st.caption("V96.4 NO FRAGMENT TEST MODE | Isko daal ke screenshot bhej")