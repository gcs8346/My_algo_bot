import streamlit as st
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
import time

st.set_page_config(page_title="TOPU SIGNAL ONLY", layout="centered")
st.markdown("## 👑 TOPU TOWER - SIGNAL ONLY (FAST)")

if st.text_input("🔑 Token", value="TOPU-2026-TEST", type="password") != "TOPU-2026-TEST":
    st.stop()

token = st.sidebar.text_input("Upstox Token (Roz Naya)", type="password")
if not token: 
    st.warning("Token daal bhai")
    st.stop()

headers = {'Authorization': f'Bearer {token}'}
st_autorefresh(interval=1000, key="signal_only_v10")

instrument_key = "NSE_INDEX|Nifty 50"

# Expiry ek baar - fast ke liye
@st.cache_data(ttl=3600)
def get_exps():
    try:
        r=requests.get(f"https://api.upstox.com/v2/option/contract?instrument_key={instrument_key}", headers=headers, timeout=4)
        if r.status_code==200:
            return sorted(list(set([d['expiry'] for d in r.json().get('data',[])])))
    except: pass
    return ["2026-10-30"]

exps=get_exps()
expiry=st.sidebar.selectbox("Expiry Auto", exps)
sound_on=st.sidebar.checkbox("🔊 Sound ON", value=True)

def play_sound(txt):
    components.html(f"""<audio autoplay><source src="https://www.soundjay.com/buttons/sounds/beep-07a.mp3"></audio><b>{txt}</b>""", height=50)

# Candle EMA ke liye - 15 sec me ek baar hi - yehi fast ka raaz hai
if 'candle_cache' not in st.session_state:
    st.session_state.candle_cache=pd.DataFrame()
    st.session_state.last_candle_time=0

if time.time() - st.session_state.last_candle_time > 15 or st.session_state.candle_cache.empty:
    try:
        r=requests.get(f"https://api.upstox.com/v2/historical-candle/intraday/{instrument_key}/1minute", headers=headers, timeout=5)
        if r.status_code==200 and r.json().get('data',{}).get('candles'):
            st.session_state.candle_cache=pd.DataFrame(r.json()['data']['candles'], columns=['t','o','h','l','c','v','oi'])
            st.session_state.last_candle_time=time.time()
    except: pass

# LIVE - har 1 sec
try:
    r_ltp=requests.get(f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={instrument_key}", headers=headers, timeout=3)
    live=list(r_ltp.json()['data'].values())[0]['last_price'] if r_ltp.status_code==200 else 0
except: live=0

# PCR - har 1 sec
def get_pcr(live_price):
    try:
        r=requests.get(f"https://api.upstox.com/v2/option/chain?instrument_key={instrument_key}&expiry_date={expiry}", headers=headers, timeout=4)
        data=r.json().get('data') if r.status_code==200 else None
        if not data: return 1.0, "WAIT", live_price
        atm=min(data, key=lambda x: abs(x['strike_price']-live_price))['strike_price']
        near=sorted(data, key=lambda x: abs(x['strike_price']-atm))[:10]
        ce=sum([d.get('call_options',{}).get('market_data',{}).get('oi',0) for d in near])
        pe=sum([d.get('put_options',{}).get('market_data',{}).get('oi',0) for d in near])
        pcr=pe/ce if ce else 1.0
        return round(pcr,2), atm
    except:
        return 1.0, live_price

pcr_val, atm = get_pcr(live)

# EMA - Backend me banta hai, chart ki zarurat nahi
df=st.session_state.candle_cache
signal="WAIT"
fidi_status="WAIT"
ema_status="WAIT"

if not df.empty:
    df=df.sort_values('t').copy()
    df.loc[df.index[-1], 'c']=live
    df['EMA9']=df['c'].ewm(span=9).mean()
    df['EMA21']=df['c'].ewm(span=21).mean()
    df['FIDI']=df['c'].ewm(span=50).mean()
    last=df.iloc[-1]
    fidi_status="BULL" if live>last['FIDI'] else "BEAR"
    ema_status="BULL" if last['EMA9']>last['EMA21'] else "BEAR"
    
    if live < last['FIDI'] and pcr_val >= 1.35:
        signal = f"🟢 BOTTOM ZONE @ ₹{live} - Candle ghum rahi hai upar - BUY READY"
    elif live > last['FIDI'] and pcr_val <= 0.80:
        signal = f"🔴 TOP ZONE @ ₹{live} - SELL READY"
    elif fidi_status=="BULL" and ema_status=="BULL":
        signal = f"🚀 FULL BULLISH @ ₹{live}"
    elif fidi_status=="BEAR" and ema_status=="BEAR":
        signal = f"🔻 FULL BEARISH @ ₹{live}"
    else:
        signal = f"⏳ SIDEWAYS @ ₹{live}"

# ===== FINAL DASHBOARD - SIRF SIGNAL =====
st.markdown(f"### LIVE ₹{live} | PCR {pcr_val} | ATM {atm}")

if "BOTTOM" in signal:
    st.success(f"# {signal}")
    st.caption(f"PCR {pcr_val} STRONG BULL hai par price neeche - Reverse ka time")
    if sound_on: play_sound("BOTTOM ZONE")
elif "TOP" in signal:
    st.error(f"# {signal}")
    if sound_on: play_sound("TOP ZONE")
elif "BULLISH" in signal:
    st.success(f"## {signal}")
elif "BEARISH" in signal:
    st.error(f"## {signal}")
else:
    st.warning(f"## {signal}")

col1,col2,col3=st.columns(3)
col1.metric("LIVE", f"₹{live}")
col2.metric("PCR", pcr_val, f"ATM {atm}")
col3.metric("FIDI 50", fidi_status, ema_status)

st.caption("Chart hata diya hai, ab Upstox pe chart dekho, signal yahan se lo - 1 sec FAST")