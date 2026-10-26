import streamlit as st, requests, time, pandas as pd
from datetime import datetime

st.set_page_config(page_title="TOWER V47 BEEP", layout="wide")

st.markdown("""
<style>
.stApp {background:#0a0a0a; color:white;}
.card {background:#151515; padding:14px; border-radius:12px; border:1px solid #333; text-align:center;}
.bull {background:#00ff88; color:black; padding:14px; border-radius:12px; font-weight:900; font-size:22px; text-align:center; margin-top:12px;}
.wait {background:#ffcc00; color:black; padding:14px; border-radius:12px; font-weight:900; font-size:20px; text-align:center; margin-top:12px;}
</style>
""", unsafe_allow_html=True)

# --- BEEP FUNCTION ---
def beep():
    st.markdown('<audio autoplay><source src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" type="audio/ogg"></audio>', unsafe_allow_html=True)

st.markdown("### 🏰 TOWER V47 - BEEP SYSTEM ON")

# --- TOKEN WITH BEEP ---
raw = st.text_input("🔑 Upstox Token (Roz Naya) - Daalte hi Beep bajega", type="password", key="beep_token")

if raw:
    token = raw.strip().replace("Bearer ","").replace("bearer ","").replace('"','').replace("'","").strip()
    # Token naya hai to BEEP
    if "last_beep_token" not in st.session_state or st.session_state["last_beep_token"] != token:
        beep()
        st.session_state["last_beep_token"] = token
        st.success(f"Beep! Token pakda {len(token)} chars")
    st.session_state["tok"] = token
else:
    token = st.session_state.get("tok","")

if not token or len(token) < 50:
    st.warning("Token daal bhai - dalte hi beep bajega")
    st.stop()

headers = {"Authorization": f"Bearer {token}", "Accept":"application/json"}

# Speed select pe bhi beep
speed = st.selectbox("Tik-Tik Speed (Select pe beep)", ["0.1 sec (100ms)", "0.8 sec (FAST)", "2.0 sec (SAFE)"], index=1, key="speed_beep")
if "last_speed" not in st.session_state or st.session_state["last_speed"] != speed:
    if "last_speed" in st.session_state: # pehli baar nahi bajega
        beep()
    st.session_state["last_speed"] = speed

speed_val = 0.1 if "0.1" in speed else 0.8 if "0.8" in speed else 2.0

def get_live_ltp(key):
    try:
        r = requests.get("https://api.upstox.com/v3/market-quote/ltp", headers=headers, params={"instrument_key":key}, timeout=6)
        if r.status_code==200:
            d=r.json().get("data",{}).get(key,{}).get("last_price")
            if d: return d, f"V3 OK {r.status_code}"
        r2=requests.get("https://api.upstox.com/v2/market-quote/ltp", headers=headers, params={"instrument_key":key}, timeout=6)
        if r2.status_code==200:
            data=r2.json().get("data",{})
            price=data.get(key,{}).get("last_price") if key in data else list(data.values())[0].get("last_price") if data else None
            if price: return price, f"V2 OK {r2.status_code}"
        return None, f"Fail {r.status_code}"
    except Exception as e:
        return None, str(e)

# LIVE DASH
ltp, stat = get_live_ltp("NSE_INDEX|Nifty 50")
if not ltp:
    st.error(f"LIVE fail {stat}")
    st.stop()

c1,c2 = st.columns(2)
c1.markdown(f'<div class="card">Nifty 50<br><b style="font-size:28px">₹{ltp}</b><br>{stat}</div>', unsafe_allow_html=True)
c2.markdown(f'<div class="card">Status<br><b>Speed {speed}</b><br>Beep ON</div>', unsafe_allow_html=True)

# READY pe bhi beep (puraana wala)
if ltp:
    st.markdown(f'<div class="bull">TOTAL 8/10 READY @ ₹{ltp} - BEEP!</div>', unsafe_allow_html=True)

st.divider()

# BUTTONS PE BEEP
if st.button("🔄 SCAN Daba - Beep bajega", key="scan_beep"):
    beep()
    st.success("Beep! Scan shuru...")
    # yahan tera bulk wala scan logic
    st.write("Bulk scan logic yahan ayega...")

if st.button("🔊 TEST BEEP BAJA", key="test_beep"):
    beep()
    st.info("Beep baja kya?")

st.caption(f"Last: {datetime.now().strftime('%H:%M:%S')} | Beep System ON")
time.sleep(speed_val)
st.rerun()