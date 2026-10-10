import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime
import requests

# Page configuration for wide dashboard layout
st.set_page_config(page_title="Upstox Semi-Auto Options Dashboard", layout="wide")

# Initialize Session States for handling orders and signals
if 'order_status' not in st.session_state:
    st.session_state.order_status = "No Active Positions"
if 'pending_signal' not in st.session_state:
    st.session_state.pending_signal = None
if 'execution_logs' not in st.session_state:
    st.session_state.execution_logs = []

# ==========================================
# 1. MATHEMATICAL INDICATORS & STRATEGY ENGINE
# ==========================================
def calculate_indicators(prices_dict):
    """Natively calculates indicators without heavy external C-libraries"""
    closes = np.array(prices_dict['close'])
    highs = np.array(prices_dict['high'])
    lows = np.array(prices_dict['low'])
    
    # 1. Simple EMA Calculation
    ema_9 = pd.Series(closes).ewm(span=9, adjust=False).mean().iloc[-1]
    ema_21 = pd.Series(closes).ewm(span=21, adjust=False).mean().iloc[-1]
    
    # 2. Native RSI Calculation
    delta = pd.Series(closes).diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
    rs = gain / loss if loss != 0 else 0
    rsi = 100 - (100 / (1 + rs)) if loss != 0 else 50
    
    # 3. ATR & SuperTrend Logic Frame
    atr = np.mean(highs - lows)  # Proxy for simplified execution
    supertrend_direction = "BUY" if closes[-1] > (ema_21) else "SELL"
    
    # Strategy Crossover Rule
    signal = "NO_SIGNAL"
    if supertrend_direction == "BUY" and ema_9 > ema_21 and rsi > 50:
        signal = "CE_BUY_SIGNAL"
    elif supertrend_direction == "SELL" and ema_9 < ema_21 and rsi < 50:
        signal = "PE_BUY_SIGNAL"
        
    return {"rsi": round(rsi, 2), "ema_9": round(ema_9, 2), "ema_21": round(ema_21, 2), "atr": round(atr, 2), "signal": signal}

# ==========================================
# 2. UPSTOX API ROUTER (SIMULATED FOR LIVE UI)
# ==========================================
def execute_upstox_order(access_token, symbol, order_type, entry_price, target, sl):
    """Dispatches order to Upstox API Endpoint"""
    # Replace with real endpoint: https://upstox.com
    url = "https://upstox.com" 
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    
    # Placeholder response mapping live payload execution
    time.sleep(0.4) # Network latency simulation
    return {"status": "success", "order_id": f"UPD-{int(time.time())}", "message": "Order Placed Successfully"}

# ==========================================
# 3. DUMMY DATA GENERATOR (MARKET STREAM PROXY)
# ==========================================
def get_live_market_snapshot(index_name):
    spots = {"NIFTY": 24250, "BANK NIFTY": 52400, "SENSEX": 79600}
    step_sizes = {"NIFTY": 50, "BANK NIFTY": 100, "SENSEX": 100}
    
    spot = spots[index_name] + np.random.randint(-20, 20)
    step = step_sizes[index_name]
    atm_strike = round(spot / step) * step
    
    # Generate 5 ITM and 5 OTM Options Table Matrix
    options_data = []
    for i in range(-5, 6):
        strike = atm_strike + (i * step)
        type_strike = "ITM" if (i < 0) else ("ATM" if i == 0 else "OTM")
        options_data.append({
            "Strike": strike,
            "Type": type_strike,
            "CE LTP": round(150 - (i * 25) + np.random.rand(), 2),
            "CE OI Change (%)": round(np.random.uniform(-10, 50), 2),
            "PE LTP": round(150 + (i * 25) + np.random.rand(), 2),
            "PE OI Change (%)": round(np.random.uniform(-10, 50), 2),
            "Theta": round(-12.5 - (abs(i) * 1.2), 2)
        })
    return spot, pd.DataFrame(options_data)

# ==========================================
# 4. DASHBOARD FRONTEND RENDER
# ==========================================

# Top Status Header Row
col_timer, col_index, col_pcr, col_token = st.columns([2, 2, 2, 4])
with col_timer:
    st.metric("🕒 LIVE TIMER", datetime.now().strftime("%H:%M:%S"))
with col_index:
    selected_index = st.selectbox("🎯 SELECT INDEX", ["NIFTY", "BANK NIFTY", "SENSEX"])
with col_pcr:
    st.metric("📊 LIVE PCR (5 ITM/OTM)", "1.08", delta="Bullish Bias")
with col_token:
    upstox_token = st.text_input("🔑 Upstox Access Token", type="password", value="DUMMY_TOKEN")

# Fetch current market state values
spot_price, options_df = get_live_market_snapshot(selected_index)

# Technical calculations injection
mock_history = {'close': [spot_price - x for x in range(30, 0, -1)], 'high': [spot_price + 5]*30, 'low': [spot_price - 5]*30}
tech_metrics = calculate_indicators(mock_history)

# Grid Layout Generation
st.divider()
panel_col1, panel_col2 = st.columns([4, 6])

with panel_col1:
    st.subheader("📊 Macro & Tech Confluence Panel")
    
    # Macro FII DII Grid Card
    st.markdown("##### **Institutional Flow (Daily Net)**")
    fii_dii_df = pd.DataFrame({
        "Part
