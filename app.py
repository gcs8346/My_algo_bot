import os
import asyncio
import threading
import ssl
import json
import time
import collections
import streamlit as st
import pandas as pd
import plotly.express as px
import websockets
from dotenv import load_dotenv
from upstox_client import MarketDataFeedApi, Configuration, ApiClient
from upstox_client.feeder.market_data_feeder import MarketDataFeeder 


# --- 1. छुपी हुई फाइल/क्लाउड सीक्रेट्स से टोकन लोड करना ---
load_dotenv()
ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")

# सुरक्षा जांच
if not ACCESS_TOKEN:
    st.error("❌ ERROR: UPSTOX_ACCESS_TOKEN NOT FOUND IN SECRETS! Please check configuration.")
    st.stop()

# --- 2. मास्टर टोकन्स और इंस्ट्रूमेंट्स डिक्शनरी ---
INSTRUMENTS = {
    "NIFTY 50": "NSE_INDEX|Nifty 50",
    "BANK NIFTY": "NSE_INDEX|Nifty Bank",
    "FIN NIFTY": "NSE_INDEX|Nifty Fin Service",
    "SENSEX": "BSE_INDEX|SENSEX",
    "RELIANCE": "NSE_EQ|INE002A01018",
    "HDFC BANK": "NSE_EQ|INE040H01021",
    "ICICI BANK": "NSE_EQ|INE090A01021",
    "SBI": "NSE_EQ|INE062A01020",
    "TCS": "NSE_EQ|INE467B01029",
    "INFY": "NSE_EQ|INE009A01021"
}

st.set_page_config(layout="wide", page_title="PRO Neon Quantum Terminal")

# डार्क साइबरपंक नियॉन यूआई इंजेक्शन
st.markdown("""
    <style>
    body { background-color: #0d0e12; color: #ffffff; }
    .stApp { background-color: #0d0e12; }
    div.stButton > button {
        font-weight: bold; height: 3.2em; border-radius: 8px; border: none; transition: 0.2s;
    }
    div.stButton > button:hover { transform: scale(1.02); box-shadow: 0 0 15px rgba(0,255,204,0.4); }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #00ffcc; text-shadow: 0 0 10px rgba(0,255,204,0.6); font-family: monospace; font-size: 26px;'>⚡ QUANTUM ZERO-LAG PRO TERMINAL ⚡</h1>", unsafe_allow_html=True)

# --- 3. ग्लोबल रैम डेटा स्टोरेज (नो-लैग आर्किटेक्चर) ---
if 'master_data' not in st.session_state:
    st.session_state.master_data = {
        k: {"price": 0.0, "change": 0.0, "rsi": 50.0, "oi_change": 0, "history": collections.deque(maxlen=40), "signal": "SCANNING QUANT DATA..."}
        for k in INSTRUMENTS.values()
    }
if 'html_matrix' not in st.session_state:
    st.session_state.html_matrix = ""

# टॉप बार ड्रॉपडाउन एसेट सिलेक्शन
selected_name = st.selectbox("", list(INSTRUMENTS.keys()), label_visibility="collapsed")
ACTIVE_TOKEN = INSTRUMENTS[selected_name]

# स्क्रीन लेआउट विभाजन
col_left, col_right = st.columns([0.8, 1.4])

with col_left:
    signal_box = st.empty()
    chart_box = st.empty()
    exec_panel = st.empty()

with col_right:
    matrix_box = st.empty()

# --- 4. Upstox API और बैकग्राउंड वेबसॉकेट ---
def get_ws_url():
    config = Configuration()
    config.access_token = ACCESS_TOKEN
    api_client = ApiClient(config)
    return MarketDataFeedApi(api_client).get_market_data_feed_authorize("2.0").data.authorized_redirect_url

def calculate_signals(token):
    data = st.session_state.master_data[token]
    prices = list(data["history"])
    if len(prices) < 20: return "⏳ GATHERING TICK CONFLUENCE"
    
    df = pd.DataFrame(prices, columns=['close'])
    ema9 = df['close'].ewm(span=9, adjust=False).mean().iloc[-1]
    ema21 = df['close'].ewm(span=21, adjust=False).mean().iloc[-1]
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
    rsi = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    data["rsi"] = rsi
    oi_chg = data["oi_change"]

    # अल्टीमेट स्मार्ट मनी परफेक्ट कॉन्फ्लुएंस लॉजिक
    if ema9 > ema21 and rsi > 55 and oi_chg > 0: 
        return "🎯 PERFECT BUY (SMART MONEY LONG)"
    elif ema9 < ema21 and rsi < 45 and oi_chg > 0: 
        return "🚨 PERFECT SELL (SMART MONEY SHORT)"
    else: 
        return "⏳ SIDEWAYS MARKET / NO SIGNAL"

# --- 5. कस्टमाइज्ड 1 ATM + 5 ITM + 5 OTM (CE & PE) ग्लोइंग HTML मैट्रिक्स ---
def generate_html_matrix(ltp):
    interval = 100 if "Bank" in ACTIVE_TOKEN else (50 if "Nifty" in ACTIVE_TOKEN or "SENSEX" in ACTIVE_TOKEN else 10)
    atm_strike = round(ltp / interval) * interval
    
    itm_strikes = [atm_strike - (i * interval) for i in range(5, 0, -1)]
    otm_strikes = [atm_strike + (i * interval) for i in range(1, 6)]
    total_strikes = itm_strikes + [atm_strike] + otm_strikes
    
    html = """
    <table style="width:100%; border-collapse: collapse; background-color: #12131a; font-family: monospace; text-align: center; border: 1px solid #232632; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.4);">
        <tr style="background-color: #1a1c24; color: #8a8a93; font-size: 12px; height: 42px; border-bottom: 2px solid #232632;">
            <th style="padding: 10px;">CE OI CHG</th>
            <th>CE TYPE</th>
            <th style="color: #00ffcc;">CE LTP</th>
            <th style="background-color: #1f222e; color: #ffffff; font-size: 14px; letter-spacing:1px;">STRIKE</th>
            <th style="color: #ff3366;">PE LTP</th>
            <th>PE TYPE</th>
            <th>PE OI CHG</th>
        </tr>
    """
    
    for strike in total_strikes:
        # फिक्स: यहाँ पर pe_bg स्ट्रिंग फ़ॉर्मेटिंग एरर ठीक की गई है
        if strike == atm_strike:
            ce_bg, pe_bg = "rgba(255, 215, 0, 0.12)", "rgba(255, 215, 0, 0.12)"
            ce_type, pe_type = "⭐ ATM", "⭐ ATM"
            ce_t_color, pe_t_color = "#ffd700", "#ffd700"
        elif strike < atm_strike:
            ce_bg, pe_bg = "rgba(0, 204, 102, 0.15)", "rgba(255, 51, 102, 0.04)"
            ce_type, pe_type = "🟢 ITM", "🔴 OTM"
            ce_t_color, pe_t_color = "#00ff66", "#8a8a93"
        else:
            ce_bg, pe_bg = "rgba(255, 51, 102, 0.04)", "rgba(0, 204, 102, 0.15)"
            ce_type, pe_type = "🔴 OTM", "🟢 ITM"
            ce_t_color, pe_t_color = "#8a8a93", "#00ff66"
            
        ce_ltp = max(1.5, (ltp - strike) + 22 if strike <= atm_strike else 75 / ((strike - atm_strike)/interval + 1))
        pe_ltp = max(1.5, (strike - ltp) + 22 if strike >= atm_strike else 75 / ((atm_strike - strike)/interval + 1))
        oi_chg = int(38000 + (strike * 0.03))

        html += f"""
        <tr style="height: 38px; border-bottom: 1px solid #1f222e; font-size: 13px;">
            <td style="color: #aaa; background-color: {ce_bg};">{oi_chg:,}</td>
            <td style="color: {ce_t_color}; background-color: {ce_bg}; font-weight: bold;">{ce_type}</td>
            <td style="color: #00ffcc; background-color: {ce_bg}; font-weight: bold; font-size: 14px;">₹{ce_ltp:.2f}</td>
            <td style="background-color: #1a1c24; color: #ffffff; font-weight: bold; border-left: 2px solid #232632; border-right: 2px solid #232632;">{strike}</td>
            <td style="color: #ff3366; background-color: {pe_bg}; font-weight: bold; font-size: 14px;">₹{pe_ltp:.2f}</td>
            <td style="color: {pe_t_color}; background-color: {pe_bg}; font-weight: bold;">{pe_type}</td>
            <td style="color: #aaa; background-color: {pe_bg};">{oi_chg+1500:,}</td>
        </tr>
        """
    html += "</table>"
    st.session_state.html_matrix = html

# --- 6. बैकग्राउंड मल्टी-थ्रेडेड वेबसॉकेट लूप ---
async def ws_multi_streamer():
    try:
        ws_url = get_ws_url()
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        async with websockets.connect(ws_url, ssl=ssl_context) as ws:
            payload = {
                "guid": "final_neon_session", "method": "sub",
                "data": {"mode": "full", "instrumentKeys": list(INSTRUMENTS.values())}
            }
            await ws.send(json.dumps(payload))
            
            while True:
                try:
                    msg = await ws.recv()
                    feeder = MarketDataFeeder(initial_feed=msg)
                    decoded = feeder.feed if hasattr(feeder, 'feed') else json.loads(msg)
                    
                    if "feeds" in decoded:
                        for token in decoded["feeds"]:
                            if token in st.session_state.master_data:
                                tick = decoded["feeds"][token]
                                ltp = 0.0
                                if "ltp" in tick: ltp = float(tick["ltp"])
                                elif "ff" in tick and "marketFF" in tick["ff"]: ltp = float(tick["ff"]["marketFF"]["ltp"])
                                
                                if ltp > 0:
                                    t_data = st.session_state.master_data[token]
                                    t_data["price"] = ltp
                                    t_data["change"] = tick.get("cp", 0.0)
                                    t_data["oi_change"] = tick.get("choi", 0)
                                    t_data["history"].append(ltp)
                                    t_data["signal"] = calculate_signals(token)
                                    
                                    if token == ACTIVE_TOKEN:
                                        generate_html_matrix(ltp)
                except Exception:
                    await asyncio.sleep(1)
                    break
    except Exception:
        pass

if 'ws_thread' not in st.session_state:
    st.session_state.ws_thread = True
    threading.Thread(target=lambda: asyncio.run(ws_multi_streamer()), daemon=True).start()

# --- 7. 🔥 सुपर फ़ास्ट नो-लैग UI रेंडर लूप (100ms) ---
# फिक्स: लाइव डेटा कार्ड, रीयल-टाइम प्लॉटली चार्ट और HTML मैट्रिक्स को बार-बार रेंडर करने का कम्प्लीट सिस्टम।
while True:
    active_data = st.session_state.master_data[ACTIVE_TOKEN]
    price = active_data["price"]
    change = active_data["change"]
    signal = active_data["signal"]
    rsi = active_data["rsi"]
    
    # 1. सिग्नल बॉक्स और टॉप बार रेंडर करें
    chg_color = "#00ffcc" if change >= 0 else "#ff3366"
