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
    # NIFTY Expiry = Tuesday (weekday 1)
    # Agar aaj Tuesday hai aur 3:30 se pehle hai to aaj ki expiry
    weekday = today.weekday() # Mon=0, Tue=1
    if weekday == 1 and now_ist.hour < 15:
        return str(today)
    days_ahead = (1 - weekday) % 7
    if days_ahead == 0:
        days_ahead = 7
    next_exp = today + timedelta(days=days_ahead)
    return str(next_exp)

def clean_token(raw):
    if not raw: return ""
    t = raw.strip().replace('"','').replace("'","")
    if t.lower().startswith("bearer "): t = t[7:].strip()
    return t

def get_live_data(token, expiry):
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    try:
        spot_r = requests.get("https://api.upstox.com/v2/market-quote/ltp", headers=headers, params={"instrument_key": "NSE_INDEX|Nifty 50"}, timeout=10)
        if spot_r.status_code != 200:
            return None, f"Token Fail: {spot_r.text[:200]}"
        spot_price = spot_r.json()['data']['NSE_INDEX:Nifty 50']['last_price']
        
        chain_r = requests.get("https://api.upstox.com/v2/option/chain", headers=headers, params={"instrument_key": "NSE_INDEX|Nifty 50", "expiry_date": expiry}, timeout=15)
        chain_json = chain_r.json()
        
        return {"spot": spot_price, "chain": chain_json, "time_ist": datetime.now(IST)}, None
    except Exception as e:
        return None, str(e)

# UI
st.title("🤖 Topu Algo - AUTO IST ✅")
st.caption(f"🕒 IST Time: {datetime.now(IST).strftime('%d-%m-%Y %I:%M:%S %p')}")

with st.sidebar:
    st.header("🔑 Auth")
    token_input = st.text_input("Upstox Token", type="password", placeholder="eyJ... paste karo")
    c1,c2 = st.columns(2)
    with c1:
        if st.button("Connect API", use_container_width=True):
            cleaned = clean_token(token_input)
            if len(cleaned) < 100:
                st.error(f"Token galat! Length {len(cleaned)}")
            else:
                st.session_state.current_token = cleaned
                st.session_state.api_connected = True
                st.rerun()
    with c2:
        if st.button("Disconnect", use_container_width=True):
            st.session_state.current_token = ""
            st.session_state.api_connected = False
            st.rerun()
    
    if st.session_state.current_token:
        st.success(f"Token: {st.session_state.current_token[:20]}... | Len: {len(st.session_state.current_token)}")
    
    st.divider()
    st.header("⚙️ Settings - AUTO")
    auto_expiry = get_next_nifty_expiry()
    expiry = st.text_input("Expiry (Auto Tuesday)", value=auto_expiry)
    st.info(f"Auto Next Expiry: {auto_expiry} (Tuesday)")
    
    sl = st.number_input("Initial SL (Points)", value=20.0)
    trail = st.number_input("Trail Every (Points)", value=5.0)
    lot = st.number_input("Lot Qty", value=1)
    auto_refresh = st.checkbox("Auto Refresh (3 sec) - ON Rakho", value=True)

if not st.session_state.api_connected:
    st.warning("👆 Sidebar me Token dal ke Connect dabao")
    st.stop()

data, err = get_live_data(st.session_state.current_token, expiry)

if err:
    st.error(f"FAILED: {err}")
    st.session_state.api_connected = False
else:
    st.success(f"🟢 LIVE | NIFTY: {data['spot']} | Expiry: {expiry} | IST: {data['time_ist'].strftime('%H:%M:%S %p')}")
    
    # Chain data dikhao
    if data['chain'].get('data'):
        # Simple Table banao CE/PE ka
        rows = []
        for item in data['chain']['data'][:15]: # Top 15 strikes
            ce = item.get('call_options', {}).get('market_data', {})
            pe = item.get('put_options', {}).get('market_data', {})
            rows.append({
                "Strike": item.get('strike_price'),
                "CE LTP": ce.get('ltp', 0),
                "PE LTP": pe.get('ltp', 0),
            })
        st.dataframe(rows, use_container_width=True)
    else:
        st.warning(f"Expiry {expiry} pe data khali hai. Agla Tuesday try karo: 2026-10-20")
        st.json(data['chain'])

if auto