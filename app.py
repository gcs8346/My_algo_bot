import streamlit as st
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
API_LTP = "https://api.upstox.com/v2/market-quote/ltp"
API_CHAIN = "https://api.upstox.com/v2/option/chain"

if 'current_token' not in http://st.session_state:
    http://st.session_state.current_token = ""

def clean_token(raw):
    if not raw:
        return ""
    t = http://raw.strip().replace('"','').replace("'","")
    if http://t.lower().startswith("bearer "):
        t = t[7:].strip()
    return t

def get_live_spot(token):
    headers = {'Authorization': f'Bearer {token}'}
    params = {"instrument_key": "NSE_INDEX|Nifty 50,BSE_INDEX|SENSEX"}
    r = http://requests.get(API_LTP, headers=headers, params=params, timeout=10)
    j = http://r.json()
    data = http://j.get('data', {})
    nifty = 0
    sensex = 0
    for k,v in http://data.items():
        if "Nifty 50" in k:
            nifty = http://v.get('last_price',0)
        if "SENSEX" in k:
            sensex = http://v.get('last_price',0)
    return nifty, sensex, j

with http://st.sidebar:
    http://st.header("Auth")
    token_input = http://st.text_input("Token Paste Karo", type="password")
    cleaned = clean_token(token_input)
    if cleaned and len(cleaned) > 100:
        http://st.session_state.current_token = cleaned
    if http://st.session_state.current_token:
        http://st.success(f"Token Active | Len {len(st.session_state.current_token)}")
    idx = http://st.selectbox("Index:", ["NIFTY","SENSEX"], index=1)
    expiry = http://st.text_input("Expiry", value="2026-10-15" if idx=="SENSEX" else "2026-10-20")
    lot = http://st.number_input("Lot Qty", value=1)
    mode = http://st.radio("Mode:", ["Semi-Auto","Full Auto"])
    http://st.write(f"IST: {datetime.now(IST).strftime('%d-%m-%Y %I:%M:%S %p')}")

if not http://st.session_state.current_token:
    http://st.warning("Pehle Token Connect Karo")
    http://st.stop()

nifty_spot, sensex_spot, raw_json = get_live_spot(st.session_state.current_token)

col1, col2 = http://st.columns(2)
http://col1.metric("NIFTY LIVE", nifty_spot)
http://col2.metric("SENSEX LIVE", sensex_spot)

if idx == "NIFTY":
    spot = nifty_spot
else:
    spot = sensex_spot

if spot == 0:
    http://st.error("Spot 0 aa raha hai, token expire hai")
    http://st.json(raw_json)
    http://st.stop()

if idx == "SENSEX":
    atm = round(spot / 100) _ 100
else:
    atm = round(spot / 50) _ 50

http://st.success(f"Selected {idx} Spot: {spot} | ATM: {atm} | Expiry: {expiry}")

headers = {'Authorization': f'Bearer {st.session_state.current_token}'}
inst = "BSE_INDEX|SENSEX" if idx=="SENSEX" else "NSE_INDEX|Nifty 50"
chain_res = http://requests.get(API_CHAIN, headers=headers, params={"instrument_key": inst, "expiry_date": expiry}, timeout=15)
chain_json = chain_res.json()
chain_data = chain_json.get('data', [])

if not chain_data:
    http://st.error(f"{idx} ka {expiry} pe chain khali hai")
    http://st.json(chain_json)
    http://st.stop()

near = sorted(sorted(chain_data, key=lambda x: abs(x['strike_price']-spot))[:11], key=lambda x: x['strike_price'])
for it in near:
    ce = http://it.get('call_options',{}).get('market_data',{}).get('ltp')
    pe = http://it.get('put_options',{}).get('market_data',{}).get('ltp')
    http://st.write(f"{it['strike_price']} | CE: {ce} | PE: {pe}")