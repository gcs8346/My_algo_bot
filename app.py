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
# 3. LIVE MARKET DATA ENGINES (CORRECTED)
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
    
    # सुधार: Upstox का सही लाइव कोड्स (Quotes) API URL
    url = "https://upstox.com"
    
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token.strip()}'
    }
    # सुधार: क्वेरी पैरामीटर को सही तरीके से पास किया गया है
    params = {
        'instrument_key': instrument_key
    }
    
    try:
        response = requests.get(url, headers=headers, params=params).json()
        if response.get('status') == 'success' and instrument_key in response.get('data', {}):
            spot = float(response['data'][instrument_key]['last_price'])
            st.session_state.last_valid_spot = spot
            return spot, None
        else:
            errors = response.get('errors', [{'message': 'Invalid Response from Upstox'}])
            err_msg = errors[0]['message'] if isinstance(errors, list) else errors.get('message', 'Error')
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
    
    # सुधार: Upstox का सही लाइव ऑप्शन चेन API URL
    url = "https://upstox.com"
    
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token.strip()}'
    }
    # सुधार: पैरामीटर्स को अलग से डिक्शनरी में सेट किया गया है
    params = {
        'instrument_key': instrument_key,
        'expiry_date': expiry_date
    }
    
    try:
        response = requests.get(url, headers=headers, params=params).json()
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
            errors = response.get('errors', [{'message': 'Chain Fetch Error'}])
            err_msg = errors[0]['message'] if isinstance(errors, list) else errors.get('message', 'Error')
            return None, err_msg
    except Exception as e:
        return None, str(e)