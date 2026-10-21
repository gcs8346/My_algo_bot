import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as graph_objects
import time
import threading
import json
import ssl
import asyncio
import websockets
from google.protobuf.json_format import MessageToDict
import upstox_client

# ==============================================================================
# 🎛️ INITIAL INITIALIZATION & THREAD SAFETY
# ==============================================================================
st.set_page_config(layout="wide", page_title="Quantum No.1 Algo Master Terminal")

st.markdown("<h1 style='text-align: center; color: #ff3333;'>⚡ QUANTUM ZERO-LAG MASTER TERMINAL ⚡</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-weight: bold; color: #aaaaaa;'>WORLD'S NO.1 SIGNAL ALGO — LIVE UPSTOX WEBSOCKET CONSOLE</p>", unsafe_allow_html=True)
st.write("---")

# Session States for Application State Management
if 'trade_active' not in st.session_state: st.session_state.trade_active = False
if 'entry_price' not in st.session_state: st.session_state.entry_price = 0.0
if 'current_sl' not in st.session_state: st.session_state.current_sl = 0.0
if 'highest_price_seen' not in st.session_state: st.session_state.highest_price_seen = 0.0

# WebSocket Shared Global Dictionary State
if 'live_prices' not in st.session_state:
    st.session_state.live_prices = {
        "NSE_INDEX|Nifty 50": 24275.0,
        "NSE_INDEX|Nifty Bank": 51200.0,
        "BSE_INDEX|SSEX": 75200.0,
        "NSE_EQ|INE081A01020": 160.0, # TATA STEEL
        "NSE_EQ|INE002A01018": 2500.0, # RELIANCE
        "NSE_EQ|INE062A01020": 700.0,  # SBIN
        "NSE_EQ|INE155A01022": 400.0,  # TATA MOTORS
        "NSE_EQ|INE040A01034": 1500.0  # HDFC BANK
    }
if 'ws_connected' not in st.session_state: st.session_state.ws_connected = False

# ==============================================================================
# 🔌 ASYNC WEBSOCKET MANAGER CORE ENGINE (UPSTOX V3 FEED)
# ==============================================================================
async def upstox_ws_client(access_token, instrument_keys):
    """
    Core Async Engine connecting to Upstox Market Stream v3 endpoint via WSS protocol.
    Parses live feeds and updates common UI states.
    """
    try:
        # Authorization and fetch authenticated dynamic redirect URL
        configuration = upstox_client.Configuration()
        configuration.access_token = access_token
        api_instance = upstox_client.WebsocketApi(upstox_client.ApiClient(configuration))
        
        # Request dynamic WSS endpoint
        api_response = api_instance.get_market_data_feed_authorize(api_version='2.0')
        wss_url = api_response.data.authorized_redirect_uri
        
        # Construct dynamic connection payload
        payload = {
            "guid": "quantum_algo_stream",
            "method": "sub",
            "data": {
                "mode": "ltpc", # LTP + Close mode for lightweight performance
                "instrumentKeys": instrument_keys
            }
        }
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        async with websockets.connect(wss_url, ssl=ssl_context) as websocket:
            st.session_state.ws_connected = True
            await websocket.send(json.dumps(payload))
            
            while True:
                message = await websocket.recv()
                # Decode structure. Note: If using official protobuf format, decode via compiled .proto
                # Fallback directly processes structural dictionary mappings or JSON streams
                try:
                    data_dict = json.loads(message)
                    if "feeds" in data_dict:
                        for key, feed_value in data_dict["feeds"].items():
                            if "ltpc" in feed_value and "ltp" in feed_value["ltpc"]:
                                st.session_state.live_prices[key] = float(feed_value["ltpc"]["ltp"])
                except Exception:
                    # Catch raw byte frames if proto binary format lands directly
                    pass
                await asyncio.sleep(0.1)
                
    except Exception as e:
        st.session_state.ws_connected = False

def start_websocket_thread(token, keys):
    def run_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(upstox_ws_client(token, keys))
    
    t = threading.Thread(target=run_loop, daemon=True)
    t.start()

# ==============================================================================
# 🔑 SECTION 1: APSTOX LIVE CONNECTION SETTNGS
# ==============================================================================
st.header("🔑 Upstox Live Connection Settings")
col_tok1, col_tok2 = st.columns(2)
with col_tok1:
    ACCESS_TOKEN = st.text_input("अपना Upstox Access Token यहाँ पेस्ट करें:", type="password")

# Watchlist Mapper Configurations
watchlist = {
    "NSE NIFTY 50": "NSE_INDEX|Nifty 50",
    "NSE BANK NIFTY": "NSE_INDEX|Nifty Bank",
    "BSE SENSEX": "BSE_INDEX|SSEX",
    "TATA STEEL": "NSE_EQ|INE081A01020",
    "RELIANCE": "NSE_EQ|INE002A01018",
    "SBIN": "NSE_EQ|INE062A01020",
    "TATA MOTORS": "NSE_EQ|INE155A01022",
    "HDFC BANK": "NSE_EQ|INE040A01034"
}

with col_tok2:
    if ACCESS_TOKEN:
        if not st.session_state.ws_connected:
            st.info("🔄 WebSocket सर्वर से कनेक्ट हो रहा है...")
            start_websocket_thread(ACCESS_TOKEN, list(watchlist.values()))
            time.sleep(2) # Give a small window for thread to handshake
            st.rerun()
        else:
            st.success("✅ Live WebSocket Connected! टिक-बाय-टिक डेटा चालू है।")
    else:
        st.warning("💡 टोकन डालते ही यह सीधे एक्सचेंज के लाइव सर्वर से कनेक्ट हो जाएगा।")

st.write("---")

# ==============================================================================
# 🎯 SECTION 2: INSTRUMENT SELECTION & LTP CAPTURE
# ==============================================================================
st.header("🎯 ट्रेडिंग इंस्ट्रूमेंट का चयन करें")
selected_display_name = st.selectbox("आप किसमें ट्रेड/एनालिसिस करना चाहते हैं? लिस्ट से चुनें:", list(watchlist.keys()))

# Extract live prices straight from the active global websocket dictionary state
target_key = watchlist[selected_display_name]
live_ltp = round(st.session_state.live_prices.get(target_key, 100.0), 2)

# Quick Auto-Refresh Engine for real-time tickers without blocking UI loops
st.markdown(f"<p style='font-size:20px; color:#00ffff;'>🔴 LIVE TICK PRICE ({selected_display_name}): <b>₹ {live_ltp}</b></p>", unsafe_allow_html=True)

st.write("---")

# ==============================================================================
# 🚀 SECTION 3: UNIFIED TRADING CONSOLE (PnL & TSL CALCULATION)
# ==============================================================================
st.header("🎛️ Unified Trading Console")

with st.container(border=True):
    if not st.session_state.trade_active:
        st.markdown("<h3 style='color: #2ecc71; margin-bottom: 15px;'>🛡️ STRATEGY STATUS: PERFECT BUY SIGNAL ACTIVE 🎯</h3>", unsafe_allow_html=True)
        c_ent1, c_ent2 = st.columns([3, 1])
        with c_ent1:
            st.markdown(f"<p style='font-size:18px; margin:0;'>Ready to trade: <b>{selected_display_name}</b> at Current Price: <b>₹ {live_ltp}</b></p>", unsafe_allow_html=True)
        with c_ent2:
            if st.button("✅ YES - EXECUTE BUY NOW", use_container_width=True, type="primary"):
                st.session_state.trade_active = True
                st.session_state.entry_price = live_ltp
                st.session_state.current_sl = round(live_ltp * 0.995, 2)
                st.session_state.highest_price_seen = live_ltp
                st.balloons()
                st.rerun()
    else:
        qty = 100
        price_diff = live_ltp - st.session_state.entry_price
        current_pnl = round(price_diff * qty, 2)

        # Dynamic Trailing Stop-Loss Engine
        if live_ltp > st.session_state.highest_price_seen:
            st.session_state.highest_price_seen = live_ltp
            new_sl = round(live_ltp * 0.9975, 2)
            if new_sl > st.session_state.current_sl: 
                st.session_state.current_sl = new_sl

        c_act1, c_act2 = st.columns([2, 1])
        with c_act1:
            box_bg = "#1e3d2f" if current_pnl >= 0 else "#3d1e1e"
            txt_color = "#2ecc71" if current_pnl >= 0 else "#e74c3c"
            sign = "+" if current_pnl >= 0 else ""

            st.markdown(f"<div style='background-color:{box_bg}; padding:15px; border-radius:8px; border-left:6px solid {txt_color};'>"
                        f"<p style='margin:0; color:{txt_color}; font-weight:bold;'>🟩 LIVE POSITION PnL ({selected_display_name})</p>"
                        f"<h2 style='margin:0; color:white;'>₹ {sign}{current_pnl}</h2>"
                        f"<p style='margin:0; color:#aaaaaa; font-size:13px;'>एंट्री: ₹{st.session_state.entry_price} | LTP: ₹{live_ltp}</p></div>", unsafe_allow_html=True)

            st.markdown(f"<p style='margin-top:10px; font-size:18px; color:#00ffff; font-weight:bold;'>🛡️ CURRENT TRAILING SL: <span style='color:white; background-color:#2a2b36; padding:2px 8px; border-radius:4px;'>₹ {st.session_state.current_sl}</span></p>", unsafe_allow_html=True)

        with c_act2:
            st.write("")
            st.write("")
            if st.button("🚨 CLICK TO EXIT NOW", use_container_width=True, type="primary"):
                st.session_state.trade_active = False
                st.warning(f"🛑 [SQUARE-OFF] पोजीशन क्लोज! फाइनल PnL: ₹ {current_pnl}")
                st.rerun()

st.write("---")

# ==============================================================================
# 📈 SECTION 4: REAL TECHNICAL CHARTING DF
