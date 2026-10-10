import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time
import upstox_client
from upstox_client.rest import ApiException

# --- PAGE SETUP ---
st.set_page_config(page_title="Semi-Auto Options Dashboard - Upstox v2", layout="wide")

# --- 1. CONFIGURATION & STATE ---
if 'active_pos' not in st.session_state:
    st.session_state.active_pos = None

# --- 2. INDICATOR ENGINE ---
def get_signals(df):
    close = df['close']
    ema9 = close.ewm(span=9, adjust=False).mean().iloc[-1]
    ema21 = close.ewm(span=21, adjust=False).mean().iloc[-1]

    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean().iloc[-1]
    loss = -delta.where(delta < 0, 0).rolling(14).mean().iloc[-1]
    rsi = 100 - (100 / (1 + gain/loss)) if loss != 0 else 50

    atr = (df['high'] - df['low']).rolling(14).mean().iloc[-1]
    supertrend_buy = close.iloc[-1] > ema21

    signal = "WAIT"
    if supertrend_buy and ema9 > ema21 and rsi > 52:
        signal = "CE_BUY"
    elif not supertrend_buy and ema9 < ema21 and rsi < 48:
        signal = "PE_BUY"
    
    return ema9, ema21, rsi, atr, signal

# --- 3. UPSTOX v2 IMPLEMENTATION ---
def place_order_upstox(token, instrument_key, qty, side):
    """
    Executes standard order placement payload utilizing Upstox SDK v2.
    """
    if not token:
        return {"status": "error", "msg": "Access Token missing!"}
        
    configuration = upstox_client.Configuration()
    configuration.access_token = token
    api_instance = upstox_client.OrderApi(upstox_client.ApiClient(configuration))
    
    body = upstox_client.PlaceOrderRequest(
        quantity=int(qty),
        product="INTRADAY",
        validity="DAY",
        price=0.0,
        tag="DashboardEngine",
        instrument_token=instrument_key,
        order_type="MARKET",
        transaction_type=side,
        disclosed_quantity=0,
        trigger_price=0.0,
        is_amo=False
    )
    
    try:
        api_response = api_instance.place_order(body, api_version='2.0')
        return {"status": "success", "order_id": api_response.data.order_id}
    except ApiException as e:
        return {"status": "error", "msg": e.body}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

# --- UI STRUCTURE ---
st.title("🎛️ Institutional Options Execution Engine")

c1, c2, c3, c4 = st.columns(4)
c1.metric("LIVE TIME", datetime.now().strftime("%H:%M:%S"))
index = c2.selectbox("INDEX", ["NIFTY", "BANKNIFTY", "SENSEX"])
pcr = c3.metric("PCR", "1.08", "+0.05 Bullish")
token = c4.text_input("Upstox v2 Access Token", type="password")

# Base calculations for synthetic data pipeline
spot_base = {"NIFTY": 24250, "BANKNIFTY": 52400, "SENSEX": 79800}
spot = spot_base[index] + np.random.randint(-30, 30)
st.divider()

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📈 Technical Confluence")
    candles = pd.DataFrame({
        'close': [spot - i + np.random.rand() for i in range(30, 0, -1)],
        'high': [spot + 10] * 30, 'low': [spot - 10] * 30
    })
    ema9, ema21, rsi, atr, signal = get_signals(candles)
    
    st.write(f"**SuperTrend:** {'BUY 🟢' if 'CE' in signal else 'SELL 🔴' if 'PE' in signal else 'WAIT 🟡'}")
    st.write(f"**EMA 9/21:** {round(ema9,1)} / {round(ema21,1)} - {'Bullish' if ema9 > ema21 else 'Bearish'}")
    st.write(f"**RSI:** {round(rsi,1)} | **ATR:** {round(atr,1)}")
    st.write(f"**Spot:** {spot}")

    st.subheader("💰 Macro")
    st.write("FII Net: +1,240 Cr | DII Net: -450 Cr | Bias: BULLISH")

with col2:
    st.subheader(f"📊 Live OI - 5 ITM + 5 OTM - {index}")
    step = 50 if index == "NIFTY" else 100
    atm = round(spot / step) * step
    
    strikes = []
    for i in range(-5, 6):
        s = atm + i * step
        strikes.append({
            "Strike": s, 
            "Type": "ATM" if i == 0 else "ITM" if i < 0 else "OTM",
            "CE LTP": round(120 - i * 20 + np.random.rand(), 1),
            "CE OI Ch%": round(np.random.uniform(-5, 40), 1),
            "PE LTP": round(120 + i * 20 + np.random.rand(), 1),
            "PE OI Ch%": round(np.random.uniform(-5, 40), 1),
            "Theta/hr": round(-12 - abs(i), 1)
        })
    df_strikes = pd.DataFrame(strikes)
    st.dataframe(df_strikes, use_container_width=True)

# --- PANEL 5: EXECUTION ROUTER ---
st.divider()
st.subheader("🚀 Semi-Auto Execution Terminal")

# ATM element maps directly to index position 5 inside our matrix list
atm_strike_data = strikes[5]

if "BUY" in signal:
    is_ce = "CE" in signal
    opt_type = "CE" if is_ce else "PE"
    ltp = atm_strike_data["CE LTP"] if is_ce else atm_strike_data["PE LTP"]
    
    suggested = f"{index} {atm} {opt_type} @ {ltp}"
    sl = round(ltp - atr, 1)
    tgt = round(ltp + atr * 1.5, 1)
    
    st.warning(f"STRATEGY DETECTED: {signal} | Entry target: {suggested} | SL: {sl} | Target: {tgt}")

    c_yes, c_no = st.columns(2)
    if c_yes.button("YES 🟢 BUY - PROCEED", use_container_width=True):
        res = place_order_upstox(token, f"NSE_FO|{index}{atm}{opt_type}", 50, "BUY")
        if res["status"] == "success":
            st.session_state.active_pos = {
                "instrument": f"{index}{atm}{opt_type}",
                "entry": ltp, 
                "sl": sl, 
                "tgt": tgt, 
                "type": opt_type
            }
            st.success(f"Execution Dispatched: {res['order_id']}")
        else:
            st.error(f"Order Execution Failed: {res['msg']}")
            
    if c_no.button("NO 🔴 CANCEL", use_container_width=True):
        st.info("Execution Routine Postponed.")
else:
    st.info(f"Signal State: {signal} - Standing by for market momentum metrics...")

# --- PANEL 6: REALTIME POSITION TRACKING ---
if st.session_state.active_pos:
    st.subheader("📍 Active Position Tracking")
    pos = st.session_state.active_pos
    
    # Calculate variable changes mimicking runtime tracking
    current_ltp = atm_strike_data["CE LTP"] if pos["type"] == "CE" else atm_strike_data["PE LTP"]
    current_ltp += round(np.random.uniform(-1, 3), 1)
    pnl = (current_ltp - pos['entry']) * 50
    
    pcol1, pcol2, pcol3 = st.columns(3)
    pcol1.metric("PnL (INR)", f"₹{round(pnl,2)}", delta=f"{round(current_ltp - pos['entry'], 1)} LTP Shift")
    pcol2.write(f"**Target:** {pos['tgt']} | **StopLoss:** {pos['sl']}")
    
    if pcol3.button("💥 EMERGENCY SQUARE OFF", use_container_width=True):
        place_order_upstox(token, f"NSE_FO|{pos['instrument']}", 50, "SELL")
        st.session_state.active_pos = None
        st.experimental_rerun()
    
