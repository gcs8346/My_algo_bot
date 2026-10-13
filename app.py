import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

st.set_page_config(page_title="Topu Algo", layout="wide")

if 'current_token' not in st.session_state:
    st.session_state.current_token = ""
if 'api_connected' not in st.session_state:
    st.session_state.api_connected = False

def clean_token(raw):
    if not raw: return ""
    t = raw.strip()
    t = t.replace('"','').replace("'","").replace('`','')
    if t.lower().startswith("bearer "):
        t = t[7:].strip()
    return t

def get_headers(token):
    return {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}

def get_live_data(token, expiry):
    headers = get_headers(token)
    try:
        # 1. Spot Price
        spot_url = "https://api.upstox.com/v2/market-quote/ltp"
        spot_params = {"instrument_key": "NSE_INDEX|Nifty 50"}
        spot_r = requests.get(spot_url, headers=headers, params=spot_params, timeout=10)
        
        if spot_r.status_code != 200:
            return None, f"Token Error: {spot_r.status_code} - {spot_r.text[:200]}"
        
        spot_json = spot_r.json()
        if spot_json.get('status') != 'success':
            return None, f"API Failed: {spot_json}"
            
        spot_price = spot_json['data']['NSE_INDEX:Nifty 50']['last_price']
        
        # 2. Option Chain
        chain_url = "https://api.upstox.com/v2/option/chain"
        chain_params = {"instrument_key": "NSE_INDEX|Nifty 50", "expiry_date": expiry}
        chain_r = requests.get(chain_url, headers=headers, params=chain_params, timeout=15)
        
        chain_data = chain_r.json() if chain_r.status_code == 200 else {}
        
        return {"spot": spot_price, "chain": chain_data, "time": datetime.now()}, None
    except Exception as e:
        return None, str(e)

# --- UI ---
st.title("🤖 Topu Algo - FINAL FIXED ✅")

with st.sidebar:
    st.header("🔑 Authentication & Control")
    # yahan value nahi denge taki auto-fill wala dots na aaye
    token_input = st.text_input("Upstox Access Token", type="password", placeholder="eyJ... paste karo")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Connect API", use_container_width=True):
            cleaned = clean_token(token_input)
            if len(cleaned) < 50:
                st.error(f"Token bahut chhota hai! Length: {len(cleaned)}. Naya eyJ... wala token dalo")
            else:
                st.session_state.current_token = cleaned
                st.session_state.api_connected = True
                st.success("Token Save Ho Gaya")
                st.rerun()
    with col2:
        if st.button("Disconnect", use_container_width=True):
            st.session_state.current_token = ""
            st.session_state.api_connected = False
            st.rerun()

    st.divider()
    if st.session_state.current_token:
        st.caption(f"Token Check: {st.session_state.current_token[:20]}... Length: {len(st.session_state.current_token)}")
        st.write(f"API Status: {'🟢 CONNECTED' if st.session_state.api_connected else '🔴 DISCONNECTED'}")
    else:
        st.write("API Status: 🔴 DISCONNECTED - Pehle Token daal ke Connect API dabao")

    st.divider()
    st.header("⚙️ SL & Trailing Settings")
    sl = st.number_input("Initial SL (Points)", value=20.00)
    trail = st.number_input("Trail Every (Points)", value=5.00)
    lot = st.number_input("Lot Qty", value=1)
    auto_refresh = st.checkbox("Auto Refresh (3 sec)")

    st.header("📈 Live Tracker")
    index = st.selectbox("INDEX", ["NIFTY", "BANKNIFTY"])
    expiry = st.text_input("Expiry (YYYY-MM-DD)", value="2026-10-16")

if not st.session_state.api_connected or not st.session_state.current_token:
    st.warning("👆 Sidebar me naya Upstox Token dal ke Connect API dabao")
    st.info("Token roz expire hota hai. Upstox Developer Console -> My Apps -> Generate Token se naya eyJ... wala token lo")
    st.stop()

# Live Data
data, err = get_live_data(st.session_state.current_token, expiry)

if err:
    st.error(f"FAILED: {err}")
    st.error("Token Expired hai! Naya token banao")
    st.session_state.api_connected = False
else:
    st.success(f"🟢 LIVE | NIFTY: {data['spot']} | Time: {data['time'].strftime('%H:%M:%S')}")
    st.json(data['chain'])

if auto_refresh:
    time.sleep(3)
    st.rerun()