import streamlit as st
import pandas as pd
import numpy as np
import time
import requests
import urllib.parse
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh

# ==========================================
# 1. PAGE CONFIGURATION & LIVE AUTOREFRESH
# ==========================================
st.set_page_config(page_title="Topu Algo - Upstox Options Dashboard", layout="wide")
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
# 3. LIVE MARKET DATA & PORTFOLIO ENGINES - FIXED
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

    # FIX 1: Sahi Upstox Endpoint + Encode
    encoded_key = urllib.parse.quote(instrument_key, safe='')
    url = f"https://api.upstox.com/v2/market-quote/quotes?instrument_key={encoded_key}"

    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token.strip()}'
    }

    try:
        response = requests.get(url, headers=headers).json()
        if response.get('status') == 'success':
            # Upstox quotes response structure
            data_dict = response.get('data', {})
            if encoded_key in data_dict or instrument_key in data_dict:
                key_to_check = encoded_key if encoded_key in data_dict else instrument_key
                # Different endpoint returns last_price inside
                spot_data = data_dict[key_to_check]
                spot = float(spot_data.get('last_price', spot_data.get('ltp', 0)))
                st.session_state.last_valid_spot = spot
                return spot, None
            else:
                # Try ltp endpoint as fallback
                url_ltp = f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={encoded_key}"
                res_ltp = requests.get(url_ltp, headers=headers).json()
                if res_ltp.get('status') == 'success':
                    price = list(res_ltp['data'].values())[0]['last_price']
                    st.session_state.last_valid_spot = float(price)
                    return float(price), None

        err_msg = response.get('errors', [{}])[0].get('message', str(response))
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

    # FIX 2: Sahi Option Chain Endpoint
    encoded_key = urllib.parse.quote(instrument_key, safe='')
    url = f"https://api.upstox.com/v2/option/chain?instrument_key={encoded_key}&expiry_date={expiry_date}"

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
                c_chg_oi = call_data.get('market_data', {}).get('oi_percent_change', 0) if call_data else 0
                p_oi = put_data.get('market_data', {}).get('oi', 0) if put_data else 0
                p_chg_oi = put_data.get('market_data', {}).get('oi_percent_change', 0) if put_data else 0

                total_call_oi += c_oi
                total_put_oi += p_oi

                records.append({
                    "Strike": strike,
                    "Call OI": c_oi,
                    "Call Chg OI %": round(c_chg_oi, 2),
                    "Put OI": p_oi,
                    "Put Chg OI %": round(p_chg_oi, 2)
                })

            df_chain = pd.DataFrame(records).sort_values("Strike")
            live_pcr = round(total_put_oi / total_call_oi, 2) if total_call_oi > 0 else 0.0
            return {"df": df_chain, "pcr": live_pcr}, None
        else:
            err_msg = response.get('errors', [{}])[0].get('message', str(response))
            return None, err_msg
    except Exception as e:
        return None, str(e)

def fetch_real_live_positions(access_token):
    if not access_token:
        return None, "Token Missing"

    url = 'https://api.upstox.com/v2/portfolio/short-term-positions'
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

                live_pnl = round((ltp - buy_avg) * net_qty, 2) if net_qty!= 0 else 0.0

                records.append({
                    "Symbol": trading_symbol,
                    "Net Qty": net_qty,
                    "Avg Buy Price": buy_avg,
                    "Live LTP": ltp,
                    "Live PNL (MTM)": live_pnl
                })
            return pd.DataFrame(records), None
        else:
            err_msg = response.get('errors', [{}])[0].get('message', 'Position API Error')
            return None, err_msg
    except Exception as e:
        return None, str(e)

def fetch_live_fii_dii_data(access_token):
    # Note: Upstox me FII/DII ka direct API nahi hai, isliye yahan 0 return karenge
    # Aap NSE ka free API use kar sakte ho
    return {"FII": 0.0, "DII": 0.0}

# ==========================================
# 4. USER INTERFACE & LOGIC FLOW
# ==========================================

st.title("🤖 Topu Semi-Automatic Options Algo Dashboard")

st.sidebar.header("🔑 Authentication & Control")
token_input = st.sidebar.text_input("Upstox Access Token", type="password", value=st.session_state.current_token)

if st.sidebar.button("Connect API"):
    if token_input:
        st.session_state.current_token = token_input.strip()
        spot, err = get_live_market_snapshot("NIFTY", st.session_state.current_token)
        if err is None:
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

if st.session_state.api_connected:
    st.sidebar.markdown("**API Status:** 🟢 CONNECTED")
else:
    st.sidebar.markdown("**API Status:** 🔴 DISCONNECTED")

st.sidebar.header("⚙️ SL & Trailing Settings")
initial_sl = st.sidebar.number_input("Initial Stop Loss (Points)", min_value=1.0, value=20.0, step=1.0)
trail_every = st.sidebar.number_input("Trail Every (Points)", min_value=1.0, value=5.0, step=1.0)

st.header("📈 Live Derivatives Tracker & Analytics")
index_choice = st.selectbox("🎯 SELECT INDEX", ["NIFTY", "BANK NIFTY"])
expiry_choice = st.text_input("📅 Expiry Date (YYYY-MM-DD format)", value=datetime.now().strftime("%Y-%m-%d"))

if st.session_state.api_connected and st.session_state.current_token:
    live_spot, spot_err = get_live_market_snapshot(index_choice, st.session_state.current_token)
    chain_data, chain_err = fetch_live_option_chain_data(index_choice, expiry_choice, st.session_state.current_token)

    if spot_err:
        st.error(f"Spot Error: {spot_err}")
    if chain_err:
        st.warning(f"Option Chain Error (Expiry check karo): {chain_err}")

    if live_spot:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(label=f"🔥 {index_choice} Live Spot", value=f"₹{live_spot:.2f}")
        if chain_data:
            col2.metric(label="📊 PCR", value=chain_data['pcr'], delta="Bullish" if chain_data['pcr'] >= 1.0 else "Bearish")
            st.subheader("🔥 Real-Time Option Chain")
            st.dataframe(chain_data['df'], use_container_width=True)
        else:
            col2.metric(label="📊 PCR", value="--")

        col3.metric(label="💼 FII Net", value="N/A")
        col4.metric(label="🏢 DII Net", value="N/A")