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
    lot = st.number_input("Lot Qty", value=1)
    mode = st.radio("Mode:", ["Semi-Auto","Full Auto"])
    st.write(f"IST: {datetime.now(IST).strftime('%d-%m-%Y %I:%M:%S %p')}")

if not st.session_state.current_token:
    st.warning("Pehle Token Connect Karo")
    st.stop()

nifty_spot, sensex_spot, raw_json = get_live_spot(st.session_state.current_token)

col1, col2 = st.columns(2)
col1.metric("NIFTY LIVE", nifty_spot)
col2.metric("SENSEX LIVE", sensex_spot)

if idx == "NIFTY":
    spot = nifty_spot
else:
    spot = sensex_spot

if spot == 0:
    st.error("Spot 0 aa raha hai, token expire hai")
    st.json(raw_json)
    st.stop()

if idx == "SENSEX":
    atm = round(spot / 100) _ 100
else:
    atm = round(spot / 50) _ 50

st.success(f"Selected {idx} Spot: {spot} | ATM: {atm} | Expiry: {expiry}")

headers = {'Authorization': f'Bearer {st.session_state.current_token}'}
inst = "BSE_INDEX|SENSEX" if idx=="SENSEX" else "NSE_INDEX|Nifty 50"
chain_res = requests.get(API_CHAIN, headers=headers, params={"instrument_key": inst, "expiry_date": expiry}, timeout=15)
chain_json = chain_res.json()
chain_data = chain_json.get('data', [])

if not chain_data:
    st.error(f"{idx} ka {expiry} pe chain khali hai")
    st.json(chain_json)
    st.stop()

near = sorted(sorted(chain_data, key=lambda x: abs(x['strike_price']-spot))[:11], key=lambda x: x['strike_price'])
for it in near:
    ce = it.get('call_options',{}).get('market_data',{}).get('ltp')
    pe = it.get('put_options',{}).get('market_data',{}).get('ltp')
    st.write(f"{it['strike_price']} | CE: {ce} | PE: {pe}")
