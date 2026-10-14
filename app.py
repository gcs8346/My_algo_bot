
import streamlit as st
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
API_LTP = "api.upstox.com"
API_CHAIN = "api.upstox.com"

if 'current_token' not in st.session_state:
    st.session_state.current_token = ""

def clean_token(raw):
    if not raw:
        return ""
    t = raw.strip().replace('"','').replace("'","")
    if t.lower().startswith("bearer "):
        t = t[7:].strip()
    return t

def get_live_spot(token):
    headers = {'Authorization': f'Bearer {token}'}
    params = {"instrument_key": "NSE_INDEX|Nifty 50,BSE_INDEX|SENSEX"}
    r = requests.get(API_LTP, headers=headers, params=params, timeout=10)
    j = r.json()
    data = j.get('data', {})
    nifty = 0
    sensex = 0
    for k,v in data.items():
        if "Nifty 50" in k:
            nifty = v.get('last_price',0)
        if "SENSEX" in k:
            sensex = v.get('last_price',0)
    return nifty, sensex, j

with st.sidebar:
    st.header("Auth")
    token_input = st.text_input("Token Paste Karo", type="password")
    cleaned = clean_token(token_input)
    if cleaned and len(cleaned) > 100:
        st.session_state.current_token = cleaned

    if st.session_state.current_token:
        st.success(f"Token Active | Len {len(st.session_state.current_token)}")

    idx = st.selectbox("Index:", ["NIFTY","SENSEX"], index=1)
    expiry = st.text_input("Expiry", value="2026-10-15" if idx=="SENSEX" else "2026-10-20")
    lot = st.number_input("Lot", value=1)

if not st.session_state.current_token:
    st.warning("Pehle Token Connect Karo")
    st.stop()

nifty_spot, sensex_spot, raw_json = get_live_spot(st.session_state.current_token)
st.write(f"NIFTY LIVE: {nifty_spot} | SENSEX LIVE: {sensex_spot}")

if idx=="NIFTY":
    spot = nifty_spot
else:
    spot = sensex_spot

LINE 105 FIX - STAR YAHI HAI
atm = round(spot / 50) _ 50 if idx != "SENSEX" else round(spot / 100) _ 100

st.success(f"Selected {idx} Spot: {spot} | ATM: {atm}")

