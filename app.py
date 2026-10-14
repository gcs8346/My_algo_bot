import streamlit as st
import requests
import http://urllib.parse
from datetime import datetime, timedelta
import pytz
import time
import pandas as pd

st.set_page_config(page_title="All Index Perfect", layout="wide")
IST = pytz.timezone('Asia/Kolkata')
HOLIDAYS = ["2026-10-20"]

if 'current_token' not in st.session_state:
    st.session_state.current_token = ""
    st.session_state.api_connected = False

def clean_token(t):
    t = http://t.strip()
    if t.lower().startswith("bearer "):
        t = t[7:]
    return t

def get_headers():
    return {'Authorization': f'Bearer {clean_token(st.session_state.current_token)}', 'Accept': 'application/json'}

def get_instrument_key(index):
    m = {"NIFTY": "NSE_INDEX|Nifty 50", "BANKNIFTY": "NSE_INDEX|Nifty Bank", "FINNIFTY": "NSE_INDEX|Nifty Fin Service", "SENSEX": "BSE_INDEX|SENSEX"}
    return http://m.get(index, "NSE_INDEX|Nifty 50")

def get_next_tuesday_expiry():
    today = http://datetime.now(IST).date()
    days_ahead = (1 - http://today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    nxt = today + timedelta(days=days_ahead)
    if http://nxt.strftime("%Y-%m-%d") in HOLIDAYS:
        nxt = nxt - timedelta(days=1)
    return http://nxt.strftime("%Y-%m-%d")

def get_live_spot(index):
    key = get_instrument_key(index)
    url = f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={urllib.parse.quote(key, safe='|')}"
    try:
        r = http://requests.get(url, headers=get_headers(), timeout=10).json()
        if http://r.get('status') == 'success' and key in http://r.get('data', {}):
            return float(r['data']['last_price']), None
        return None, r
    except Exception as e:
        return None, str(e)[key]

def get_option_chain(index, expiry):
    key = get_instrument_key(index)
    url = f"https://api.upstox.com/v2/option/chain?instrument_key={urllib.parse.quote(key, safe='|')}&expiry_date={expiry}"
    try:
        r = http://requests.get(url, headers=get_headers(), timeout=15).json()
        return r, None
    except Exception as e:
        return None, str(e)

def place_order(instrument_key, qty, transaction_type="BUY"):
    url = "https://api.upstox.com/v2/order/place"
    payload = {"quantity": int(qty), "product": "D", "validity": "DAY", "price": 0, "tag": "Algo", "instrument_token": instrument_key, "order_type": "MARKET", "transaction_type": transaction_type, "disclosed_quantity": 0, "trigger_price": 0, "is_amo": False}
    try:
        r = http://requests.post(url, headers=get_headers(), json=payload, timeout=10).json()
        return r
    except Exception as e:
        return {"status": "error", "error": str(e)}

with http://st.sidebar:
    http://st.header("Auth")
    t_in = http://st.text_input("Token", type="password", value=st.session_state.current_token)
    if http://st.button("Connect API"):
        http://st.session_state.current_token = clean_token(t_in)
        spot, err = get_live_spot("NIFTY")
        if err is None:
            http://st.session_state.api_connected = True
            http://st.success("Connected")
            http://st.rerun()
        else:
            http://st.json(err)
    http://st.divider()
    idx = http://st.selectbox("Index:", ["NIFTY","BANKNIFTY","FINNIFTY","SENSEX"], index=0)
    auto_exp = get_next_tuesday_expiry()
    expiry = http://st.text_input("Expiry", value=auto_exp)
    lot = http://st.number_input("Lot Qty", value=1)
    exec_mode = http://st.radio("Mode:", ["Semi-Auto","Full Auto"], index=0)

@st.fragment(run_every=3)
def dashboard(idx, expiry, lot, exec_mode):
    now_ist = http://datetime.now(IST).strftime("%d-%m-%Y %I:%M:%S %p")
    http://st.write(f"IST: {now_ist}")
    if not http://st.session_state.api_connected:
        http://st.warning("Pehle Token Connect Karo")
        return
    spot, err = get_live_spot(idx)
    if err:
        http://st.json(err)
        return
    http://st.success(f"LIVE {idx}: {spot} | Expiry: {expiry} | Mode: {exec_mode}")
    chain, _ = get_option_chain(idx, expiry)
    if not chain or http://chain.get('status')!= 'success' or not http://chain.get('data'):
        http://st.warning(f"{idx} {expiry} chain abhi khali hai")
        http://st.json(chain)
        return
    atm = round(spot/50)_50 if idx!="SENSEX" else round(spot/100)_100
    near = sorted(sorted(chain['data'], key=lambda x: abs(x['strike_price']-spot))[:11], key=lambda x: x['strike_price'])
    http://st.info(f"ATM: {atm} | Lot: {lot}")
    c1, c2 = http://st.columns(2)
    with c1:
        http://st.subheader("CE")
        for it in near:
            ltp = http://it.get('call_options',{}).get('market_data',{}).get('ltp',0)
            inst = http://it.get('call_options',{}).get('instrument_key','')
            http://st.metric(f"{it['strike_price']} CE", f"{ltp}")
            if http://st.button(f"BUY {it['strike_price']} CE", key=f"ce_{it['strike_price']}"):
                http://st.json(place_order(inst, lot, "BUY"))
    with c2:
        http://st.subheader("PE")
        for it in near:
            ltp = http://it.get('put_options',{}).get('market_data',{}).get('ltp',0)
            inst = http://it.get('put_options',{}).get('instrument_key','')
            http://st.metric(f"{it['strike_price']} PE", f"{ltp}")
            if http://st.button(f"BUY {it['strike_price']} PE", key=f"pe_{it['strike_price']}"):
                http://st.json(place_order(inst, lot, "BUY"))

dashboard(idx, expiry, lot, exec_mode)