import streamlit as st, requests, time, pandas as pd
from datetime import datetime

st.set_page_config(page_title="TOWER V72", layout="wide")
st.title("TOWER V72 - SINGLE FOCUS")

raw = st.text_input("Upstox Token", type="password")
token = raw.strip().replace("Bearer ","").strip() if raw else st.session_state.get("tok","")
if raw: st.session_state["tok"]=token
if not token or len(token)<50:
    st.warning("Token daal bhai"); st.stop()

headers={"Authorization":f"Bearer {token}","Accept":"application/json"}

ALL = ["NSE_INDEX|Nifty 50","NSE_INDEX|Nifty Bank","BSE_INDEX|Sensex","NSE_EQ|RELIANCE","NSE_EQ|TCS","NSE_EQ|INFY","NSE_EQ|HDFCBANK","NSE_EQ|ICICIBANK","NSE_EQ|SBIN","NSE_EQ|BHARTIARTL","NSE_EQ|ITC","NSE_EQ|LT","NSE_EQ|KOTAKBANK","NSE_EQ|AXISBANK","NSE_EQ|BAJFINANCE","NSE_EQ|MARUTI","NSE_EQ|TATAMOTORS","NSE_EQ|ADANIENT"]

def get_bulk_batched(keys, batch=15):
    final={}
    for i in range(0,len(keys),batch):
        chunk=keys[i:i+batch]
        try:
            joined=",".join(chunk)
            r=requests.get("https://api.upstox.com/v3/market-quote/ltp", headers=headers, params={"instrument_key":joined}, timeout=8)
            if r.status_code==200:
                final.update(r.json().get("data",{}))
            else:
                r2=requests.get("https://api.upstox.com/v2/market-quote/ltp", headers=headers, params={"instrument_key":joined}, timeout=8)
                if r2.status_code==200:
                    final.update(r2.json().get("data",{}))
        except: pass
        time.sleep(0.3)
    return final

# --- AUTO SCAN ---
if "prices" not in st.session_state: st.session_state["prices"]={}
if "last_scan" not in st.session_state: st.session_state["last_scan"]=0

now=time.time()
if now - st.session_state["last_scan"] > 8:
    data = get_bulk_batched(ALL)
    if data:
        st.session_state["prices"]=data
        st.session_state["last_scan"]=now

prices = st.session_state["prices"]

# --- TOP BAR - SABKA RATE ---
if prices:
    bar=""
    for k in ALL:
        name=k.split("|")[-1]
        p=prices.get(k,{}).get("last_price")
        if p:
            bar+=f"<span style='margin-right:35px; color:#00ff88; font-weight:bold;'> {name}: ₹{p} </span>"
    st.markdown(f"<div style='background:#111; border:1px solid #333; padding:10px; border-radius:10px;'><marquee scrollamount='7'>{bar}</marquee></div>", unsafe_allow_html=True)
else:
    st.info("Pehli baar scan ho raha hai 5 sec me...")

st.divider()

# --- MAIN FOCUS - YEHI TU MANG RAHA THA ---
focus = st.selectbox("👇 Kisko MAIN pe dekhna hai? Select kar", ALL, index=0)

main_price = prices.get(focus,{}).get("last_price") if prices else None

if main_price:
    st.markdown(f"""
    <div style="background:#151515; border:2px solid #00ff88; border-radius:18px; padding:25px; text-align:center; margin-top:10px;">
        <div style="color:gray; font-size:18px;">{focus.split('|')[-1]}</div>
        <div style="color:#00ff88; font-size:65px; font-weight:900;">₹{main_price}</div>
        <div style="color:#aaa; font-size:14px;">Auto Update - {datetime.now().strftime('%H:%M:%S')}</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.warning(f"{focus.split('|')[-1]} ka rate aa raha hai, 2 sec me...")

# Niche full list
with st.expander("📋 Saare 18 ka Weight / LTP Table"):
    if prices:
        rows=[{"NAME":k.split("|")[-1], "LTP": prices.get(k,{}).get("last_price","...")} for k in ALL]
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.write("Scanning...")

st.caption(f"Last Bulk Scan: {datetime.fromtimestamp(st.session_state['last_scan']).strftime('%H:%M:%S') if st.session_state['last_scan'] else '...'}")
time.sleep(1)
st.rerun()