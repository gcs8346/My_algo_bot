import streamlit as st
import pandas as pd
import numpy as np
import time
import requests
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="Topu Algo - Live Order & SL Dashboard", layout="wide")
st_autorefresh(interval=2000, key="datarefresh")

# 2. SESSION STATES INITIALIZATION
if 'order_status' not in st.session_state:
    st.session_state.order_status = "No Active Positions"
if 'execution_logs' not in st.session_state:
    st.session_state.execution_logs = []
if 'current_token' not in st.session_state:
    st.session_state.current_token = ""
if 'api_connected' not in st.session_state:
    st.session_state.api_connected = False
if 'last_valid_spot' not in st.session_state:
    st.session_state.last_valid_spot = 22500.00
if 'trade_active' not in st.session_state:
    st.session_state.trade_active = False
if 'entry_price' not in st.session_state:
    st.session_state.entry_price = 0.0
if 'current_sl' not in st.session_state:
    st.session_state.current_sl = 0.0
if 'highest_price_seen' not in st.session_state:
    st.session_state.highest_price_seen = 0.0
if 'live_order_id' not in st.session_state:
    st.session_state.live_order_id = None
if 'sl_order_id' not in st.session_state:
    st.session_state.sl_order_id = None

# ==========================================
# 3. REAL LIVE UPSTOX PLACING ENGINE (V2/V3 OFFICIAL API)
# ==========================================
def punch_real_upstox_order(access_token, instrument, tx_type, order_type, qty, price=0, trigger_price=0):
    """एक्सचेंज पर लाइव ऑर्डर पंच करने का असली फंक्शन"""
    url = "https://api.upstox.com/v2/order/place" # आधिकारिक ऑर्डर प्लेसमेंट यूआरएल
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    
    payload = {
        "quantity": int(qty),
        "product": "I",        # I = Intraday (MIS)
        "validity": "DAY",
        "price": float(price),
        "tag": "TopuAlgoLive",
        "instrument_token": instrument,
        "order_type": order_type, # MARKET, LIMIT, SL, SL-M
        "transaction_type": tx_type, # BUY या SELL
        "disclosed_quantity": 0,
        "trigger_price": float(trigger_price),
        "is_amo": False
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        res_data = response.json()
        if res_data.get('status') == 'success' or 'data' in res_data:
            return {"status": "success", "order_id": res_data['data']['order_id']}
        else:
            return {"status": "failed", "error": res_data.get('errors', [{'message': 'Unknown API Error'}])[0]['message']}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ==========================================
# 4. SIMULATED LIVE STREAM DATA FOR OPTION CHAIN
# ==========================================
def get_live_market_snapshot(index_name):
    spot = st.session_state.last_valid_spot + np.random.uniform(-1.0, 1.0)
    st.session_state.last_valid_spot = spot
    return round(spot, 2)

# ==========================================
# 5. STREAMLIT UI DASHBOARD GENERATION
# ==========================================
st.title("🤖 Topu Semi-Automatic Options Algo Dashboard")

with st.sidebar:
    st.header("🔑 Authentication & Control")
    # टोकन इनपुट बॉक्स
    token_input = st.text_input("Upstox Access Token", value=st.session_state.current_token, type="password")
    
    if st.button("🔌 CONNECT API", use_container_width=True):
        if token_input:
            st.session_state.current_token = token_input
            st.session_state.api_connected = True
            st.session_state.execution_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🟢 API Token Link Completed.")
        else:
            st.error("कृपया टोकन दर्ज करें!")

    selected_index = st.selectbox("🎯 SELECT INDEX", ["NIFTY", "BANK NIFTY", "SENSEX"])
    
    # लॉट साइज और इंस्ट्रूमेंट मैपिंग
    qty_mapping = {"NIFTY": 65, "BANK NIFTY": 30, "SENSEX": 20}
    inst_mapping = {"NIFTY": "NSE_INDEX|Nifty 50", "BANK NIFTY": "NSE_INDEX|Nifty Bank", "SENSEX": "BSE_INDEX|SENSEX"}
    
    st.markdown("---")
    st.subheader("⚙️ SL & Trailing Settings")
    sl_points = st.number_input("Initial Stop Loss (Points)", min_value=1.0, value=10.0, step=1.0)
    trail_points = st.number_input("Trail Every (Points)", min_value=1.0, value=2.0, step=1.0)

    st.markdown("---")
    st.subheader("💼 Current Status")
    st.info(f"Position: {st.session_state.order_status}")

# लाइव प्राइस कैलकुलेशन
spot_price = get_live_market_snapshot(selected_index)

# 🔄 लाइव ट्रेलिंग स्टॉप लॉस ट्रैकर इंजन
if st.session_state.trade_active:
    if spot_price > st.session_state.highest_price_seen:
        diff = spot_price - st.session_state.highest_price_seen
        if diff >= trail_points:
            trails = int(diff // trail_points)
            st.session_state.current_sl += (trails * trail_points)
            st.session_state.highest_price_seen = spot_price
            st.session_state.execution_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 📈 TSL Moved Up to {st.session_state.current_sl:.2f}")
            
    # अगर प्राइस स्टॉप लॉस के नीचे आ गया तो लाइव एग्जिट मारो
    if spot_price <= st.session_state.current_sl:
        st.session_state.trade_active = False
        st.session_state.order_status = "No Active Positions"
        # एक्सचेंज पर असल मार्केट स्क्वायर-ऑफ पंच करें
        if st.session_state.current_token:
            exit_res = punch_real_upstox_order(st.session_state.current_token, inst_mapping[selected_index], "SELL", "MARKET", qty_mapping[selected_index])
        st.session_state.execution_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🚨 STOP LOSS HIT AT EXCHANGE! Exited Position.")

# डैशबोर्ड लेआउट
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("🕒 LIVE TIMER (IST)", datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%H:%M:%S'))
    st.metric(f"📊 {selected_index} SPOT PRICE", f"{spot_price:.2f}")

with col2:
    st.subheader("🎯 Live SL Tracker Status")
    if st.session_state.trade_active:
        st.warning(f"Live Entry Price: {st.session_state.entry_price:.2f}")
        st.error(f"Active Live SL: {st.session_state.current_sl:.2f}")
        st.text(f"Live Order ID: {st.session_state.live_order_id}")
    else:
        st.write("❌ No active running trade.")

with col3:
    st.subheader("⚡ Signal & Order Punch Control")
    
    if not st.session_state.trade_active:
        # असली ऑर्डर बटन
        if st.button("🚀 EXECUTE ORDER OPTIONS (YES)", type="primary", use_container_width=True):
            if not st.session_state.api_connected:
                st.error("पहले ऊपर API CONNECT करें! बिना टोकन ऑर्डर पंच नहीं होगा।")
            else:
                st.write("⏱️ Sending Live Order to Upstox Exchange...")
                # 1. मुख्य ट्रेड खरीदने का असली आर्डर पंच
                order_result = punch_real_upstox_order(
                    access_token=st.session_state.current_token,
                    instrument=inst_mapping[selected_index],
                    tx_type="BUY",
                    order_type="MARKET",
                    qty=qty_mapping[selected_index]
                )
                
                if order_result["status"] == "success":
                    st.session_state.trade_active = True
                    st.session_state.entry_price = spot_price
                    st.session_state.highest_price_seen = spot_price
                    st.session_state.current_sl = spot_price - sl_points
                    st.session_state.live_order_id = order_result["order_id"]
                    st.session_state.order_status = f"Long in {selected_index}"
                    
                    # 2. तुरंत एक्सचेंज पर प्रोटेक्शन स्टॉप लॉस ऑर्डर (SL-M) भी पंच करें
                    sl_order_result = punch_real_upstox_order(
                        access_token=st.session_state.current_token,
                        instrument=inst_mapping[selected_index],
                        tx_type="SELL",
                        order_type="SL-M", 
                        qty=qty_mapping[selected_index],
                        trigger_price=st.session_state.current_sl
                    )
                    
                    st.session_state.execution_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🛒 Live Order punched! ID: {order_result['order_id']}")
                    if sl_order_result["status"] == "success":
                        st.session_state.execution_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🛡️ Protection Stop Loss order active at exchange!")
                else:
                    st.error(f"Upstox Error: {order_result.get('error')}")
    else:
        if st.button("❌ CLOSE ORDER OPTIONS (NO)", type="secondary", use_container_width=True):
            # मैन्युअल पोजीशन क्लोज करने का असली पंच
            exit_res = punch_real_upstox_order(st.session_state.current_token, inst_mapping[selected_index], "SELL", "MARKET", qty_mapping[selected_index])
            st.session_state.trade_active = False
            st.session_state.order_status = "No Active Positions"
            st.session_state.execution_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🛑 Position manually squared off at exchange.")

st.markdown("---")
st.subheader("📋 Real-time System Logs")
for log in reversed(st.session_state.execution_logs[-8:]):
    st.text(log)
