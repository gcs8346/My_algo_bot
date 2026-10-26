import streamlit as st
import requests
import time
from datetime import datetime

st.set_page_config(page_title="TOWER V90 PROOF", layout="wide")
st.title("TOWER V90 - PROOF WALA TICK TICK 🔴")

# Token
token_input = st.text_input("Upstox Token (Roz Naya)", type="password", key="token_box")
if token_input and len(token_input.strip()) > 50:
    st.session_state.tok = token_input.strip().replace("Bearer ", "").strip()

token = st.session_state.get("tok", "")
if not token or len(token) < 50:
    st.warning("Token daal")
    st.stop()

# Counter - proof ke liye
if "count" not in st.session_state:
    st.session_state.count = 0
st.session_state.count += 1

# Controls
if "tick" not in st.session_state:
    st.session_state.tick = True

c1, c2, c3, c4 = st.columns([1,1,1,3])
with c1:
    if st.button("🟢 START"):
        st.session_state.tick = True
        st.rerun()
with c2:
    if st.button("🔴 STOP"):
        st.session_state.tick = False
        st.rerun()
with c3:
    speed = st.selectbox("Sec", [1,2,3,5], index=1, label_visibility="collapsed")
with c4:
    st.metric("TICK COUNT", st.session_state.count, f"LIVE {datetime.now().strftime('%H:%M:%S')}")

headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
KEYS = ["MCX_FO|495213", "MCX_FO|495214", "MCX_FO|573422", "MCX_FO|570750"]
NAMES = ["GOLD", "SILVER", "CRUDEOIL", "NATURALGAS"]

prices = {}
for k in KEYS:
    r = requests.get("https://api.upstox.com/v3/market-quote/ltp", headers=headers, params={"instrument_key": k}, timeout=10)
    if r.status_code == 200:
        data = r.json().get("data", {})
        for _, q in data.items():
            prices[q.get("instrument_token")] = q

# --- PROOF TICKER ---
html = ""
for i, k in enumerate(KEYS):
    q = prices.get(k, {})
    last = q.get("last_price", 0)
    html += f"<span style='margin-right:40px;color:#00ff88;font-weight:bold'>{NAMES[i]} Rs.{last} | Vol:{q.get('volume')} </span>"

st.markdown(f"<div style='background:#0e1117;border:2px solid #00ff88;padding:12px;border-radius:10px'><marquee scrollamount='8'>{html} | COUNT:{st.session_state.count} | TIME:{datetime.now().strftime('%H:%M:%S')}</marquee></div>", unsafe_allow_html=True)

cols = st.columns(4)
for i, k in enumerate(KEYS):
    q = prices.get(k, {})
    with cols[i]:
        if q.get("last_price"):
            st.metric(NAMES[i], f"Rs.{q.get('last_price')}", f"Vol {q.get('volume')} | LTQ {q.get('ltq')}")
            # Ye har tick pe badlega - proof
            st.caption(f"Tick #{st.session_state.count} | {datetime.now().strftime('%H:%M:%S')} | {k}")

st.info(f"✅ PROOF: Agar COUNT {st.session_state.count} badh raha hai aur TIME badal raha hai har {speed} sec me, toh TICK TICK chal raha hai! Price tabhi badlega jab MCX me trade hoga. Abhi GOLD ka volume 4071 tha, agla trade hote hi 4072 ho jayega.")

with st.expander("LIVE JSON"):
    st.json(prices)

if st.session_state.tick:
    time.sleep(speed)
    st.rerun()