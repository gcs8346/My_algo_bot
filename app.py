import streamlit as st, requests, time, pandas as pd
from datetime import datetime
from PIL import Image
import os

st.set_page_config(page_title="TOWER V70 GANESH", layout="wide")

# --- GANESH HEADER ---
st.markdown("""
<style>
.stApp {background:#0a0a0a; color:white;}
.ganesh-box {text-align:center; background: radial-gradient(circle, #2a1a00 0%, #0a0a0a 70%); padding:15px; border-radius:20px; border:1px solid #FFD700; margin-bottom:10px;}
</style>
""", unsafe_allow_html=True)

# Ganesh Photo - Top pe
with st.container():
    st.markdown('<div class="ganesh-box">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        if os.path.exists("ganesh.png"):
            st.image("ganesh.png", use_container_width=True)
        elif os.path.exists("image_20261026_170940.webp"):
            st.image("image_20261026_170940.webp", use_container_width=True)
        else:
            st.markdown("### 🙏 Shri Ganeshay Namah 🙏")
        st.markdown("#### 🏰 TOWER V70 - SHRI GANESH - NUMBER 1")
        st.markdown("##### ॐ गं गणपतये नमः | Labh hi Labh Hoga")
    st.markdown('</div>', unsafe_allow_html=True)

def beep_box():
    st.markdown("""
    <div style="border:2px solid #00ff88; background:#111; padding:10px; border-radius:12px; text-align:center;">
    <b style="color:#00ff88;">🔊 SIGNAL BAJA! Ganesh Ji Ki Jai!</b>
    <audio autoplay controls style="width:100%; margin-top:6px;">
    <source src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" type="audio/ogg">
    </audio></div>""", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown("#### 🔊 SOUND BOX")
    c1,c2,c3 = st.columns(3)
    sound_on = c1.toggle("Sound ON", value=True)
    c2.write("Ganesh Ashirwad ON")
    if c3.button("🔊 TEST BEEP"):
        beep_box()

# --- TOKEN ---
raw = st.text_input("🔑 Upstox Token (Roz Naya)", type="password")
if raw:
    token = raw.strip().replace("Bearer ","").replace("bearer ","").replace('"','').replace("'","").strip()
    if "last_tok" not in st.session_state or st.session_state["last_tok"]!=token:
        if sound_on: beep_box()
        st.session_state["last_tok"]=token
        st.success(f"Ganesh Ji Beep! Token {len(token)} chars")
    st.session_state["tok"]=token
else:
    token = st.session_state.get("tok","")

if not token:
    st.warning("Token daal bhai - Ganesh ji dekh rahe hain"); st.stop()
if len(token) < 50:
    st.error(f"Token chhota {len(token)}"); st.stop()

headers={"Authorization":f"Bearer {token}","Accept":"application/json"}
speed = st.selectbox("Speed", ["0.1 sec", "0.8 sec", "2.0 sec"], index=1)
speed_val = 0.1 if "0.1" in speed else 0.8 if "0.8" in speed else 2.0

indices = ["NSE_INDEX|Nifty 50","NSE_INDEX|Nifty Bank","BSE_INDEX|Sensex"]
stocks = ["NSE_EQ|RELIANCE","NSE_EQ|TCS","NSE_EQ|INFY","NSE_EQ|HDFCBANK"]

def get_ltp(key):
    try:
        r=requests.get("https://api.upstox.com/v3/market-quote/ltp", headers=headers, params={"instrument_key":key}, timeout=6)
        if r.status_code==200:
            d=r.json().get("data",{}).get(key,{}).get("last_price")
            if d: return d, f"OK {r.status_code}"
        return None, f"Fail {r.status_code}"
    except Exception as e: return None, str(e)

ltp, stat = get_ltp("NSE_INDEX|Nifty 50")
if not ltp: st.error(f"LIVE fail {stat}"); st.stop()

st.metric(f"Nifty 50 - {stat}", f"₹{ltp}")
st.success(f"TOTAL 8/10 - 🚀 READY @ ₹{ltp} - Shri Ganesh Prasann")
if sound_on:
    beep_box()

st.caption(f"V70 GANESH FINAL | {datetime.now().strftime('%H:%M:%S')}")
time.sleep(speed_val)
st.rerun()