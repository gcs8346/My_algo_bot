import streamlit as st
import requests
import time
import json
import gzip
from datetime import datetime

st.set_page_config(page_title="TOWER V84 FINAL", layout="wide")
st.title("TOWER V84 - CENTURY FINAL 🔴 LIVE")

# --- Auto Refresh ---
if "auto" not in st.session_state:
    st.session_state.auto = True
c1,c2 = st.columns([4,1])
with c2:
    auto_on = st.toggle("Auto 5s", value=st.session_state.auto)
    st.session_state.auto = auto_on
    if st.button("🔄 Refresh"):
        st.rerun()

# --- Token ---
raw = st.text_input("Upstox Token (Roz Naya)", type="password")
token = raw.strip().replace("Bearer ","").strip() if raw else st.session_state.get("tok","")
if raw:
    st.session_state["tok"] = token
if not token or len(token) < 50:
    st.warning("Token daal de bhai - Roz subah naya banta hai")
    st.stop()

headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

# --- Fixed Most Liquid Map - Tera V82 wala hi sahi tha ---
MCX_MAP = {
    "GOLD": {"key": "MCX_FO|495213", "name": "GOLD 26DEC FUT - 1KG"},
    "SILVER": {"key": "MCX_FO|495214", "name": "SILVER 26DEC FUT - 30KG"},
    "CRUDEOIL": {"key": "MCX_FO|573422", "name": "CRUDEOIL 26NOV FUT"},
    "NATURALGAS": {"key": "MCX_FO|570750", "name": "NATURALGAS 26OCT FUT"},
}
MCX_KEYS = [v["key"] for v in MCX_MAP.values()]
ALL_KEYS = MCX_KEYS + ["NSE_INDEX|Nifty 50"]

def format_expiry(e):
    try:
        if isinstance(e, int):
            ts = e/1000 if e > 1e10 else e
            return datetime.fromtimestamp(ts).strftime("%d %b %y")
        return str(e).split("T")[0]
    except:
        return str(e)

def get_ltp(keys):
    final = {}
    status = 0
    for i in range(0, len(keys), 6):
        joined = ",".join(keys[i:i+6])
        try:
            r = requests.get("https://api.upstox.com/v3/market-quote/ltp",
                             headers=headers, params={"instrument_key": joined}, timeout=10)
            status = r.status_code
            if r.status_code == 200:
                data = r.json().get("data", {})
                for trade_sym, quote in data.items():
                    inst = quote.get("instrument_token")
                    if inst:
                        final[inst] = quote
                    final[trade_sym] = quote
            elif r.status_code == 401:
                st.error("Token expire ho gaya - Upstox se naya token bana ke daal")
                st.stop()
        except Exception as e:
            st.warning(f"API error: {e}")
        time.sleep(0.2)
    return final, status

prices, status = get_ltp(ALL_KEYS)

#