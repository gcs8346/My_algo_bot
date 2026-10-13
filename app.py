import streamlit as st
import requests
from datetime import datetime, timedelta
import time
from zoneinfo import ZoneInfo

st.set_page_config(page_title="Topu Algo - AUTO", layout="wide")
IST = ZoneInfo("Asia/Kolkata")

if 'current_token' not in st.session_state:
    st.session_state.current_token = ""
if 'api_connected' not in st.session_state:
    st.session_state.api_connected = False

def get_next_nifty_expiry():
    now_ist = datetime.now(IST)
    today = now_ist.date()
    weekday = today.weekday()
    if weekday == 1 and now_ist.hour < 15:
        if now_ist.hour < 15 or (now_ist.hour == 15 and now_ist.minute <= 30):
            return str(today)
    days_ahead = (1 - weekday) % 7
    if days_ahead == 0:
        days_ahead = 7
    next_exp = today + timedelta(days=days_ahead)
    return str(next_exp)

def clean_token(raw):
    if not raw:
        return ""
    t = raw.strip().replace('"','').replace("'","").replace('`','')
    if t.lower().startswith("bearer "):
        t = t[7:].strip()
    return t

def get_live_data(token, expiry):
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    try:
        spot_url = "https://api.upstox.com/v2/market-quote/ltp"
        spot_params = {"instrument_key": "NSE_INDEX|Nifty 50"}
        spot_r = requests.get(spot_url, headers=headers, params=spot_params, timeout=10)
        if spot_r.status_code != 200:
            return None, f"Token Fail {spot_r.status_code}: {spot_r.text[:200]}"
        
        spot_json = spot_r.json()
        spot_price = spot_json['data']['NSE_INDEX:Nifty 50']['last_price']
        
        chain_url = "https://api.upstox.com/v2/option/chain"
        chain_params = {"instrument_key": "NSE_INDEX|Nifty 50", "expiry_date": expiry}
        chain_r = requests.get(chain_url, headers=headers, params=chain_params, timeout=15)
        chain_json = chain_r.json()
        
        return {"spot": spot_price, "chain": chain_json, "time_ist": datetime.now(IST)}, None
    except Exception as e:
        return None, str(e)

st.title("🤖 Topu Algo - AUTO IST")
st.caption(f"🕒 IST: {datetime.now(IST).strftime('%d-%m-%Y %I:%M:%S %p')}")

with st.sidebar:
    st.header("🔑 Auth")
    token_input = st.text_input("Upstox Token", type="password", placeholder="eyJ... paste karo")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Connect API", use_container_width=True):
            cleaned = clean_token(token_input)
            if len(cleaned) < 100:
                st.error(f"Token galat! Length {len(cleaned)}")
            else:
                st.session_state.current_token = cleaned
                st.session_state.api_connected = True
                st.success("Connected")
                st.rerun()
    with c2:
        if st.button("Disconnect", use_container_width=True):
            st.session_state.current_token = ""
            st.session_state.api_connected = False
            st.rerun()
    
    if st.session_state.current_token:
        st.code(f"Len: {len(st.session_state.current_token)} | {st.session_state.current_token[:25]}...")
    
    st.divider()
    st.header("⚙️ Settings")
    auto_expiry = get_next_nifty_expiry()
    expiry = st.text_input("Expiry (Auto Tuesday)", value=auto_expiry)
    st.info(f"Next Expiry Auto: {auto_expiry}")
    
    sl = st.number_input("Initial SL (Points)", value=20.0)
    trail = st.number_input("Trail Every (Points)", value=5.0)
    lot = st.number_input("Lot Qty", value=1)
    auto_refresh = st.checkbox("Auto Refresh (3 sec)", value=True)

if not st.session_state.api_connected or not st.session_state.current_token:
    st.warning("👆 Sidebar me Token dal ke Connect dabao")
    st.stop()

data, err = get_live_data(st.session_state.current_token, expiry)

if err:
    st.error(f"FAILED: {err}")
    st.session_state.api_connected = False
    st.stop()

st.success(f"🟢 LIVE | NIFTY: {data['spot']} | Expiry: {expiry} | IST: {data['time_ist'].strftime('%H:%M:%S %p')}")

chain_data = data['chain'].get('data', [])
if chain_data:
    rows = []
    for item in chain_data[:20]:
        ce_data = item.get('call_options', {}).get('market_data', {})
        pe_data = item.get('put_options', {}).get('market_data', {})
        rows.append({
            "Strike": item.get('strike_price'),
            "CE LTP": ce_data.get('ltp', 0),
            "PE LTP": pe_data.get('ltp', 0),
        })
    st.dataframe(rows, use_container_width=True)
else:
    st.warning(f"Expiry {expiry} pe data khali hai. Next try karo: 2026-10-20")
    st.json(data['chain'])

if auto_refresh:
    time.sleep(3)
    st.rerun()