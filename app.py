import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="TOWER V85 FINAL STABLE", layout="wide")
st.title("TOWER V85 - NO SLEEP LIVE 🔴")

# --- Token Input ---
raw = st.text_input("Upstox Token (Roz Naya - subah 3:30 baje naya banta hai)", type="password")
token = raw.strip().replace("Bearer ","").strip() if raw else st.session_state.get("tok","")
if raw:
    st.session_state["tok"] = token
    st.rerun()

if not token or len(token) < 100:
    st.warning("Token daal bhai - https://api.upstox.com/v2/login se roz naya milta hai")
    st.stop()

headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

# --- 4 FIXED KEYS - Yahi V83 me LIVE the ---
MCX_MAP = {
    "GOLD": "MCX_FO|495213",       # ispe 142575 aaya tha - GOLD 1KG
    "SILVER": "MCX_FO|495214",     # ispe 194284 aaya tha - SILVER 30KG
    "CRUDEOIL": "MCX_FO|573422",
    "NATURALGAS": "MCX_FO|570750",
}
ALL = list(MCX_MAP.values())

def get_live():
    out = {}
    status = 0
    raw_text = ""
    for key in ALL:
        try:
            r = requests.get("https://api.upstox.com/v3/market-quote/ltp",
                             headers=headers, params={"instrument_key": key}, timeout=10)
            status = r.status_code
            raw_text = r.text[:1000]
            if r.status_code == 200:
                data = r.json().get("data", {})
                for _, q in data.items():
                    inst = q.get("instrument_token")
                    if inst:
                        out[inst] = q
            else:
                # Agar HTML aaya toh yahan dikhega ki token galat hai
                return {}, status, raw_text
        except Exception as e:
            return {}, 0, str(e)
    return out, status, raw_text

if st.button("🔄 REFRESH - LIVE RATE LA"):
    st.rerun()

prices, status, raw_debug = get_live()
now = datetime.now().strftime("%H:%M:%S")

# --- Ticker ---
if prices:
    bar = f"🔴 LIVE {now} | Status {status} | "
    for name, k in MCX_MAP.items():
        p = prices.get(k, {}).get("last_price")
        if p:
            bar += f"{name}: ₹{p} | "
    st.success(bar)
else:
    st.error(f"❌ Data nahi aaya - Status {status} - Token expire ya MCX band")
    st.caption("Neeche dekho API ne kya bola - agar HTML dikhe toh token naya banao")
    with st.expander("🛠️ Live Data Diagnostics - API kya bola"):
        st.code(raw_debug)

cols = st.columns(4)
for i, (name, k) in enumerate(MCX_MAP.items()):
    q = prices.get(k, {})
    last = q.get("last_price")
    with cols[i]:
        if last:
            st.metric(name, f"₹{last}", f"LTQ:{q.get('ltq')} Vol:{q.get('volume')}")
            st.caption(f"{k} | CP:{q.get('cp')} | {now}")
        else:
            st.metric(name, "WAIT", k)

st.caption(f"V85 FINAL STABLE | {now} | No auto-sleep - Button daba ke refresh kar")
