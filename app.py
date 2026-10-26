import streamlit as st
import requests
import time
from datetime import datetime

st.set_page_config(page_title="TOWER V88 TICK TICK", layout="wide")
st.title("TOWER V88 - TICK TICK 🔴 LIVE")

# --- Token ---
token_input = st.text_input("Upstox Token (Roz Naya)", type="password", key="token_box")
if token_input and len(token_input.strip()) > 50:
    st.session_state.tok = token_input.strip().replace("Bearer ","").strip()

token = st.session_state.get("tok","")
if not token or len(token) < 50:
    st.warning("Token daal")
    st.stop()

# --- TICK TICK Controls ---
col1, col2, col3 = st.columns([2,2,6])
with col1:
    tick_on = st.toggle("🟢 TICK TICK ON (2 sec)", value=True)
with col2:
    speed = st.select_slider("Speed", options=[1,2,3,5], value=2, label_visibility="collapsed")
with col3:
    st.caption(f"Last: {datetime.now().strftime('%H:%M:%S')} | GOLD 1KG | SILVER 30KG | Key: MCX_FO|495213")

headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
KEYS = ["MCX_FO|495213","MCX_FO|495214","MCX_FO|573422","MCX_FO|570750"]
NAMES = ["GOLD","SILVER","CRUDEOIL","NATURALGAS"]

# --- Fetch ---
prices = {}
status = 0
for k in KEYS:
    try:
        r = requests.get("https://api.upstox.com/v3/market-quote/ltp",
                         headers=headers, params={"instrument_key": k}, timeout=10)
        status = r.status_code
        if r.status_code == 200:
            data = r.json().get("data", {})
            for _, q in data.items():
                inst = q.get("instrument_token")
                if inst:
                    prices[inst] = q
        elif r.status_code == 401:
            st.error("❌ Token expire - Naya banao")
            st.stop()
    except Exception as e:
        st.error(f"{e}")
        st.stop()

# --- Ticker - TICK TICK Effect ---
ticker_html = ""
for i, k in enumerate(KEYS):
    q = prices.get(k, {})
    last = q.get("last_price", 0)
    cp = q.get("cp", 0)
    diff = last - cp if cp else 0
    color = "#00ff88" if diff >= 0 else "#ff4444"
    arrow = "▲" if diff >= 0 else "▼"
    ticker_html += f"<span style='margin-right:40px;color:{color};font-weight:bold;font-size:18px'>{NAMES[i]} {arrow} ₹{last} ({diff:+.1f})</span>"

st.markdown(f"<div style='background:#0e1117;border:2px solid #00ff88;padding:15px;border-radius:12px;overflow:hidden;white-space:nowrap'><marquee scrollamount='8' style='font-family:monospace'>{ticker_html} | 🔴 TICK TICK LIVE {datetime.now().strftime('%H:%M:%S')}</marquee></div>", unsafe_allow_html=True)

# --- Metrics - Har tick pe change dikhega ---
cols = st.columns(4)
for i, k in enumerate(KEYS):
    q = prices.get(k, {})
    last = q.get("last_price")
    with cols[i]:
        if last:
            st.metric(NAMES[i], f"₹{last}", f"{(last - q.get('cp',0)):+.2f}", delta_color="normal")
            st.caption(f"LTQ:{q.get('ltq')} Vol:{q.get('volume')} | CP:{q.get('cp')} | {q.get('instrument_token')}")
            # TICK effect - progress bar
            st.progress(min(int((q.get('ltq',0)%100)/100*100) if q.get('ltq') else 50, 100))
        else:
            st.metric(NAMES[i], "WAIT")

with st.expander("🔴 LIVE JSON - TICK TICK Data"):
    st.json(prices)

st.caption(f"V88 TICK TICK | Speed {speed}s | Status {status} | {datetime.now().strftime('%d-%m %H:%M:%S')}")

# --- YEHI HAI TICK TICK KA JAADU - Neeche hona chahiye, upar nahi ---
if tick_on:
   