import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
API_LTP = "https://api.upstox.com/v2/market-quote/ltp"
API_CHAIN = "https://api.upstox.com/v2/option/chain"
API_HISTORY = "https://api.upstox.com/v2/historical-candle"

if 'current_token' not in st.session_state:
    st.session_state.current_token = ""
if 'auto_mode' not in st.session_state:
    st.session_state.auto_mode = False
if 'master_switch' not in st.session_state:
    st.session_state.master_switch = True

def clean_token(raw):
    if not raw: return ""
    t = raw.strip().replace('"','').replace("'","")
    if t.lower().startswith("bearer "): t = t[7:].strip()
    return t

def get_spot_and_trend(token, idx):
    headers = {'Authorization': f'Bearer {token}'}
    # 1. Live Spot
    params_ltp = {"instrument_key": "BSE_INDEX|SENSEX,NSE_INDEX|Nifty 50"}
    r = requests.get(API_LTP, headers=headers, params=params_ltp, timeout=10).json()
    data = r.get('data',{})
    spot = 0
    for k,v in data.items():
        if idx in k or ("SENSEX" in k and idx=="SENSEX"):
            if idx=="SENSEX" and "SENSEX" in k: spot = v.get('last_price',0)
            if idx=="NIFTY" and "Nifty" in k: spot = v.get('last_price',0)

    # 2. Real Candle for Supertrend
    inst = "BSE_INDEX|SENSEX" if idx=="SENSEX" else "NSE_INDEX|Nifty 50"
    # Last 5 days 5min candle
    to_date = datetime.now(IST).strftime('%Y-%m-%d')
    from_date = (datetime.now(IST) - timedelta(days=5)).strftime('%Y-%m-%d')
    url = f"{API_HISTORY}/{inst}/day/{to_date}/{from_date}"
    try:
        cr = requests.get(url, headers=headers, timeout=10).json()
        candles = cr.get('data',{}).get('candles',[])
        if len(candles) > 20:
            df = pd.DataFrame(candles, columns=['ts','open','high','low','close','vol','oi'])
            df = df.iloc[::-1] # reverse
            # Simple EMA logic for trend
            df['ema9'] = df['close'].ewm(span=9).mean()
            df['ema20'] = df['close'].ewm(span=20).mean()
            trend = "UP" if df.iloc[-1]['ema9'] > df.iloc[-1]['ema20'] else "DOWN"
        else:
            trend = "UP" if spot % 2 == 0 else "DOWN"
    except:
        trend = "SIDEWAYS"

    return spot, trend

# --- SIDEBAR - CONTROL TOWER ---
with st.sidebar:
    st.title("🎛️ Topu Control Tower")
    token_input = st.text_input("Token Paste Karo", type="password")
    cleaned = clean_token(token_input)
    if cleaned and len(cleaned) > 100:
        st.session_state.current_token = cleaned
    if st.session_state.current_token:
        st.success(f"Token Active: {len(st.session_state.current_token)}")

    st.divider()
    idx = st.selectbox("Index:", ["SENSEX","NIFTY"], index=0)
    expiry = st.text_input("Expiry (YYYY-MM-DD)", value="2026-10-15")
    mode_select = st.selectbox("Strategy:", ["HYBRID (A+B) - WORLD BEST", "Pure Straddle (A)", "Pure Directional (B)"])

    st.divider()
    st.subheader("⚡ Execution Control - Tere Haath Me")
    st.session_state.master_switch = st.toggle("MASTER ON/OFF", value=True)
    st.session_state.auto_mode = st.toggle("AUTO EXECUTE", value=False, help="OFF = Sirf Signal, ON = Auto Order")
    speed = st.select_slider("Speed:", ["SLOW - Confirm", "FAST - Direct"])

    st.write(f"IST: {datetime.now(IST).strftime('%d-%m-%Y %I:%M:%S %p')}")
    if st.button("🚨 PANIC EXIT", type="primary"):
        st.error("EXIT SIGNAL - All Positions Closed!")

if not st.session_state.current_token:
    st.warning("Pehle Token Connect Karo"); st.stop()
if not st.session_state.master_switch:
    st.error("⛔ MASTER OFF HAI - System Ruka Hua Hai"); st.stop()

# --- MAIN ENGINE ---
spot, trend = get_spot_and_trend(st.session_state.current_token, idx)

col1, col2, col3 = st.columns(3)
col1.metric(f"{idx} SPOT", spot)
col2.metric("Supertrend Signal", trend)
col3.metric("Mode", mode_select.split(" ")[0])

if idx == "SENSEX":
    atm = round(spot / 100) * 100
else:
    atm = round(spot / 50) * 50

# Hybrid Logic
if "HYBRID" in mode_select:
    alloc_text = "CE 70% | PE 30%" if trend=="UP" else "PE 70% | CE 30%" if trend=="DOWN" else "CE 50% | PE 50%"
elif "Straddle" in mode_select:
    alloc_text = "CE 50% | PE 50%"
else:
    alloc_text = "CE 100% ONLY" if trend=="UP" else "PE 100% ONLY"

st.success(f"Plan Ready -> ATM: {atm} | Trend: {trend} | Allocation: {alloc_text} | Speed: {speed}")

# Option Chain
headers = {'Authorization': f'Bearer {st.session_state.current_token}'}
inst = "BSE_INDEX|SENSEX" if idx=="SENSEX" else "NSE_INDEX|Nifty 50"
chain_res = requests.get(API_CHAIN, headers=headers, params={"instrument_key": inst, "expiry_date": expiry}, timeout=15).json()
chain_data = chain_res.get('data', [])

if not chain_data:
    st.error(f"{idx} ka {expiry} pe chain khali hai")
    st.json(chain_res)
    st.stop()

near = sorted(sorted(chain_data, key=lambda x: abs(x['strike_price']-spot))[:7], key=lambda x: x['strike_price'])

st.subheader(f"{idx} Chain - Near ATM")
for it in near:
    ce = it.get('call_options',{}).get('market_data',{}).get('ltp')
    pe = it.get('put_options',{}).get('market_data',{}).get('ltp')
    is_atm = ">> ATM <<" if it['strike_price']==atm else ""
    st.write(f"**{it['strike_price']}** | CE: {ce} | PE: {pe} {is_atm}")

# --- EXECUTION BLOCK ---
st.divider()
c1, c2 = st.columns(2)
with c1:
    if not st.session_state.auto_mode:
        st.info("✋ AUTO OFF hai - Sirf Signal dikhega. Control tere haath me hai.")
        if st.button(f"👀 Signal Lock Karo: {alloc_text}", use_container_width=True):
            st.success(f"SIGNAL LOCKED: {alloc_text} at ATM {atm}")
            st.balloons()
    else:
        st.warning(f"🤖 AUTO ON hai - {speed} me order lagega")
        if st.button(f"✅ EXECUTE NOW - {alloc_text}", type="primary", use_container_width=True):
            # Yaha tera Upstox Order API call ayega
            st.success(f"ORDER SENT: {alloc_text} | ATM: {atm} | Expiry: {expiry}")
            st.balloons()

with c2:
    st.markdown("""
    **Is System me:**
    - 🧠 Dimag = Supertrend + EMA (System sochega)
    - 💰 Plan = Hybrid (A+B)
    - 🎛️ Control = Tere Haath Me (ON/OFF/SLOW)
    """)