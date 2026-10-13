import streamlit as st
import pandas as pd
import numpy as np
import time
import requests
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh

# ==========================================
# 1. PAGE CONFIGURATION & LIVE AUTOREFRESH
# ==========================================
st.set_page_config(page_title="Topu Algo - Upstox Options Dashboard", layout="wide")

# Automatically refreshes the UI grid every 2 seconds
st_autorefresh(interval=2000, key="datarefresh")

# ==========================================
# 2. SESSION STATES INITIALIZATION
# ==========================================
if 'order_status' not in st.session_state:
    st.session_state.order_status = "No Active Positions"
if 'pending_signal' not in st.session_state:
    st.session_state.pending_signal = None
if 'execution_logs' not in st.session_state:
    st.session_state.execution_logs = []
if 'current_token' not in st.session_state:
    st.session_state.current_token = ""
if 'api_connected' not in st.session_state:
    st.session_state.api_connected = False
if 'last_valid_spot' not in st.session_state:
    st.session_state.last_valid_spot = 22500.00

# Trailing Stop Loss Management States
if 'trade_active' not in st.session_state:
    st.session_state.trade_active = False
if 'entry_price' not in st.session_state:
    st.session_state.entry_price = 0.0
if 'current_sl' not in st.session_state:
    st.session_state.current_sl = 0.0
if 'highest_price_seen' not in st.session_state:
    st.session_state.highest_price_seen = 0.0

# ==========================================
# 3. LIVE MARKET DATA ENGINES (NO DEMO DATA)
# ==========================================

def get_live_market_snapshot(index_name, access_token):
    if not access_token:
        return None, "Error: Access Token Required"
        
    instrument_mapping = {
        "NIFTY": "NSE_INDEX|Nifty 50", 
        "BANK NIFTY": "NSE_INDEX|Nifty Bank", 
        "SENSEX": "BSE_INDEX|SENSEX"
    }
    instrument_key = instrument_mapping.get(index_name, "NSE_INDEX|Nifty 50")
    
    url = f"https://upstox.com{instrument_key}"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token.strip()}'
    }
    
    try:
        response = requests.get(url, headers=headers).json()
        if response.get('status') == 'success' and instrument_key in response.get('data', {}):
            spot = float(response['data'][instrument_key]['last_price'])
            st.session_state.last_valid_spot = spot
            return spot, None
        else:
            err_msg = response.get('errors', [{'message': 'Invalid Response from Upstox'}])['message']
            return None, err_msg
    except Exception as e:
        return None, str(e)


def fetch_live_option_chain_data(index_name, expiry_date, access_token):
    if not access_token:
        return None, "Token Required"
        
    instrument_mapping = {
        "NIFTY": "NSE_INDEX|Nifty 50", 
        "BANK NIFTY": "NSE_INDEX|Nifty Bank"
    }
    instrument_key = instrument_mapping.get(index_name, "NSE_INDEX|Nifty 50")
    
    url = f"https://upstox.com{instrument_key}&expiry_date={expiry_date}"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token.strip()}'
    }
    
    try:
        response = requests.get(url, headers=headers).json()
        if response.get('status') == 'success':
            chain_list = response.get('data', [])
            records = []
            total_call_oi = 0
            total_put_oi = 0
            
            for item in chain_list:
                strike = item.get('strike_price')
                call_data = item.get('call_options', {})
                put_data = item.get('put_options', {})
                
                c_oi = call_data.get('market_data', {}).get('oi', 0) if call_data else 0
                c_chg_oi = call_data.get('market_data', {}).get('p_change_in_oi', 0) if call_data else 0
                p_oi = put_data.get('market_data', {}).get('oi', 0) if put_data else 0
                p_chg_oi = put_data.get('market_data', {}).get('p_change_in_oi', 0) if put_data else 0
                
                total_call_oi += c_oi
                total_put_oi += p_oi
                
                records.append({
                    "Strike": strike,
                    "Call OI": c_oi,
                    "Call Chg OI %": round(c_chg_oi, 2),
                    "Put OI": p_oi,
                    "Put Chg OI %": round(p_chg_oi, 2)
                })
            
            df_chain = pd.DataFrame(records)
            live_pcr = round(total_put_oi / total_call_oi, 2) if total_call_oi > 0 else 0.0
            return {"df": df_chain, "pcr": live_pcr}, None
        else:
            err_msg = response.get('errors', [{'message': 'Chain Fetch Error'}])['message']
            return None, err_msg
    except Exception as e:
        return None, str(e)

# ==========================================
# 4. USER INTERFACE DESIGN
# ==========================================

st.title("🤖 Topu Semi-Automatic Options Algo Dashboard")

# 📊 UI SECTION 1: AUTHENTICATION & API KEY CONTROL
st.sidebar.header("🔑 Authentication & Control")

token_input = st.sidebar.text_input("Upstox Access Token", type="password", value=st.session_state.current_token)

if st.sidebar.button("Connect API"):
    if token_input:
        st.session_state.current_token = token_input.strip()
        spot, err = get_live_market_snapshot("NIFTY", st.session_state.current_token)
        if not err:
            st.session_state.api_connected = True
            st.sidebar.success("CONNECTED TO LIVE MARKET 🟢")
            st.rerun()
        else:
            st.session_state.api_connected = False
            st.sidebar.error(f"Authentication Failed: {err}")
    else:
        st.sidebar.warning("Please paste a valid token first!")

if st.sidebar.button("Disconnect API"):
    st.session_state.current_token = ""
    st.session_state.api_connected = False
    st.rerun()

# Connection Status Label
if st.session_state.api_connected:
    st.sidebar.markdown("**API Status:** 🟢 CONNECTED")
else:
    st.sidebar.markdown("**API Status:** 🔴 DISCONNECTED (Using/Waiting Token)")

# 📊 UI SECTION 2: RISK & TRAILING SETTINGS
st.sidebar.header("⚙️ SL & Trailing Settings")
initial_sl = st.sidebar.number_input("Initial Stop Loss (Points)", min_value=1.0, value=20.0, step=1.0)
trail_every = st.sidebar.number_input("Trail Every (Points)", min_value=1.0, value=5.0, step=1.0)

# 📊 UI SECTION 3: MARKET SELECTOR & LIVE TRACKING
st.header("📈 Live Derivatives Tracker & Analytics")
index_choice = st.selectbox("🎯 SELECT INDEX", ["NIFTY", "BANK NIFTY"])
expiry_choice = st.text_input("📅 Expiry Date (YYYY-MM-DD format)", value=datetime.now().strftime("%Y-%m-%d"))

# Fetch active calculations if verified connection exists
if st.session_state.api_connected and st.session_state.current_token:
    live_spot, spot_err = get_live_market_snapshot(index_choice, st.session_state.current_token)
    chain_data, chain_err = fetch_live_option_chain_data(index_choice, expiry_choice, st.session_state.current_token)
    
    if not spot_err and chain_data is not None:
        col1, col2 = st.columns(2)
        col1.metric(label=f"🔥 {index_choice} Live Spot", value=f"₹{live_spot:.2f}")
        col2.metric(label="📊 Put-Call Ratio (PCR)", value=chain_data['pcr'], 
                    delta="Bullish Sentiment" if chain_data['pcr'] >= 1.0 else "Bearish Sentiment")
        
        st.subheader("🔥 Real-Time Option Chain Analytics (OI Breakdown)")
        if not chain_data['df'].empty:
            st.dataframe(chain_data['df'].sort_values(by="Strike").reset_index(drop=True), use_container_width=True)
        else:
            st.info("Option Chain matrix is currently empty for this specific choice.")
    else:
        st.error(f"Live Fetch Error: {spot_err or chain_err}. Check token lifecycle constraints.")
else:
    st.warning("⚠️ Dashboard Waiting for Connection: कृपया वैध Upstox Token डालें और 'Connect API' पर क्लिक करें।")

# 📊 UI SECTION 4: REAL-TIME POSITION & ORDER MANAGEMENT
st.header("💼 Trading Execution & Position Control")

col_pos, col_btn = st.columns(2)

with col_pos:
    st.subheader("Current Position Status")
    if st.session_state.trade_active:
        st.info(f"🟢 Active Position | Entry Price: ₹{st.session_state.entry_price} | Current SL: ₹{st.session_state.current_sl}")
    else:
        st.code("No Active Positions", language="text")

with col_btn:
    st.subheader("Quick Triggers")
    btn_buy_ce = st.button("⚡ BUY CALL (CE)")
    btn_buy_pe = st.button("⚡ BUY PUT (PE)")
    btn_exit = st.button("🚨 EMERGENCY SQUARE OFF", type="primary")

    if btn_buy_ce:
        st.session_state.trade_active = True
        st.session_state.entry_price = st.session_state.last_valid_spot
        st.session_state.current_sl = st.session_state.last_valid_spot - initial_sl
        st.session_state.execution_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] CE Position Opened manually.")
        st.rerun()

    if btn_buy_pe:
        st.session_state.trade_active = True
        st.session_state.entry_price = st.session_state.last_valid_spot
        st.session_state.current_sl = st.session_state.last_valid_spot + initial_sl
        st.session_state.execution_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] PE Position Opened manually.")
        st.rerun()

    if btn_exit:
        st.session_state.trade_active = False
        st.session_state.execution_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🚨 Emergency Square off executed.")
        st.rerun()

# ==========================================
# 5. SYSTEM LOGS (FIXED INDENTATION)
# ==========================================
st.subheader("📜 System Logs")