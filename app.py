import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="TOWER V86 FINAL", layout="wide")
st.title("TOWER V86 - FINAL STABLE 🔴")

# Token - ek baar daalo, tab tak chalega jab tak expire na ho
if "tok" not in st.session_state:
    st.session_state.tok = ""

raw = st.text_input("Upstox Token (Roz Naya)", type="password", placeholder="Bearer eyJ0... paste kar")
if raw:
    tok = raw.strip().replace("Bearer ","").strip()
    st.session_state.tok = tok
    st.success("Token save ho gaya - neeche rate aayega")
    st.rerun()

token = st.session_state.tok
if not token or len(token) < 100:
    st.warning("Pehle https://api.upstox.com/v2/login se token bana ke yahan daal")
    st.stop()

if st.button("🔄 REFRESH LIVE RATE", type="primary"):
    st.rerun()

headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

# Jo V83 me LIVE the wahi 4
KEYS = ["MCX_FO|495213","MCX_FO|495214","MCX_FO|573422","MCX_FO|570750"]
NAMES = ["GOLD 1KG","SILVER 30KG","CRUDEOIL","NATURALGAS"]

prices = {}
status = 0
debug_txt = ""

for k in KEYS:
    try:
        r = requests.get("https://api.upstox.com/v3/market-quote/ltp",
                         headers=headers, params={"instrument_key": k}, timeout=15)
        status = r.status_code
        debug_txt = r.text[:2000]
        if r.status_code == 200:
            data = r.json().get("data", {})
            for _, q in data.items():
                inst = q.get("instrument_token")
                if inst:
                    prices[inst] = q
        elif r.status_code == 401:
            st.error("❌ 401 - Token expire ho gaya! Naya token banao")
            st.code(debug_txt)
            st.stop()
        else:
            st.error(f"Status {status}")
            st.code(debug_txt)
    except Exception as e:
        st.error(f"Error: {e}")

now = datetime.now().strftime("%H:%M:%S - %d %b")

if prices:
    st.success(f"🔴 MCX LIVE - {now} - Status {status}")
    cols = st.columns(4)
    for i, k in enumerate(KEYS):
        q = prices.get(k, {})
        last = q.get("last_price")
        with cols[i]:
            if last:
                diff = (last - q.get("cp",0)) if q.get("cp") else 0
                st.metric(NAMES[i], f"₹{last}", f"{diff:+.1f}")
                st.caption(f"LTQ {q.get('ltq')} | Vol {q.get('volume')} | {k}")
            else:
                st.metric(NAMES[i], "WAIT", k)
else:
    st.error(f"Data nahi aaya - Status {status}")
    with st.expander("Debug kya bola API ne"):
        st.code(debug_txt)

with st.expander("Full JSON (LIVE hai toh yahan price dikhega)"):
    st.json(prices)