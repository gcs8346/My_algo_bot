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

# हर 2 सेकंड में पूरे डैशボード को रीयल-टाइम अपडेट और सिंक करेगा
st_autorefresh(interval=2000, key="datarefresh")

# ==========================================
# 2. SESSION STATES INITIALIZATION
# ==========================================
if 'execution_logs' not in st.session_state:
    st.session_state.execution_logs = []
if 'current_token' not in st.session_state:
    st.session_state.current_token = ""
if 'api_connected' not in st.session_state:
    st.session_state.api_connected = False
if 'last_valid_spot' not in st.session_state:
    st.session_state.last_valid_spot = 22500.00

# ==========================================
# 3. LIVE MARKET DATA & PORTFOLIO ENGINES
# ==========================================

# A. लाइव स्पॉट प्राइस (Upstox Market Quote API)
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


# B. लाइव ऑप्शन चेन और पीसीआर (Upstox Option Chain API)
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


# C. बिल्कुल असली लाइव पोजीशन और MTM ट्रैकर (Upstox Live Portfolio Integration)
def fetch_real_live_positions(access_token):
    if not access_token:
        return None, "Token Missing"
    
    url = 'https://upstox.com'
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token.strip()}'
    }
    
    try:
        response = requests.get(url, headers=headers).json()
        if response.get('status') == 'success':
            pos_list = response.get('data', [])
            if not pos_list:
                return pd.DataFrame(), None
                
            records = []
            for pos in pos_list:
                trading_symbol = pos.get('trading_symbol')
                net_qty = int(pos.get('quantity', 0))
                buy_avg = float(pos.get('buy_price', 0.0))
                ltp = float(pos.get('last_price', 0.0))
                
                live_pnl = round((ltp - buy_avg) * net_qty, 2) if net_qty != 0 else 0.0
                
                records.append({
                    "Symbol": trading_symbol,
                    "Net Qty": net_qty,
                    "Avg Buy Price": buy_avg,
                    "Live LTP": ltp,
                    "Live PNL (MTM)": live_pnl
                })
            return pd.DataFrame(records), None
        else:
            err_msg = response.get('errors', [{'message': 'Position API Error'}])['message']
            return None, err_msg
    except Exception as e:
        return None, str(e)


# D. लाइव FII / DII डेटा फ़ीड (Upstox Analytics Integration)
def fetch_live_fii_dii_data(access_token):
    if not access_token:
        return {"FII": 0.0, "DII": 0.0}
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {access_token.strip()}'}
    try:
        fii_res = requests.get("https://upstox.com", headers=headers).json()
        dii_res = requests.get("https://upstox.com", headers=headers).json()
        fii_net = fii_res.get('data', [{}]).get('net_value', 0.0) if fii_res.get('status') == 'success' else 0.0
        dii_net = dii_res.get('data', [{}]).get('net_value', 0.0) if dii_res.get('status') == 'success' else 0.0
        return {"FII": fii_net, "DII": dii_net}
    except:
        return {"FII": 0.0, "DII": 0.0}

# ==========================================
# 4. USER INTERFACE & LOGIC FLOW
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
    fii_dii = fetch_live_fii_dii_data(st.session_state.current_token)
    
    if not spot_err and chain_data is not None:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(label=f"🔥 {index_choice} Live Spot", value=f"₹{live_spot:.2f}")
        col2.metric(label="📊 Put-Call Ratio (PCR)", value=chain_data['pcr'], 
                    delta="Bullish Sentiment" if chain_data['pcr'] >= 1.0 else "Bearish Sentiment")
        col3.metric(label="💼 FII Net Activity", value=f"₹{fii_dii['FII']:,} Cr")
        col4.metric(label="🏢 DII Net Activity", value=f"₹{fii_dii['DII']:,} Cr")
        
        st.subheader("🔥 Real-Time Option Chain Analytics (OI Breakdown)")
        if not chain_data['df'].empty: