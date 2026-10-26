import streamlit as st, requests, time, pandas as pd
from datetime import datetime

st.set_page_config(page_title="TOWER V71 BAR", layout="wide")
st.title("TOWER V71 - DIRECT BAR")

# --- TOKEN ---
raw = st.text_input("Upstox Token", type="password")
token = raw.strip().replace("Bearer ","").replace("bearer ","").strip() if raw else st.session_state.get("tok","")
if raw: st.session_state["tok"]=token
if not token or len(token)<50:
    st.warning("Token daal"); st.stop()

headers={"Authorization":f"Bearer {token}","Accept":"application/json"}

indices=["NSE_INDEX|Nifty 50","NSE_INDEX|Nifty Bank","BSE_INDEX|Sensex"]
stocks=["NSE_EQ|RELIANCE","NSE_EQ|TCS","NSE_EQ|INFY","NSE_EQ|HDFCBANK","NSE_EQ|ICICIBANK","NSE_EQ|SBIN","NSE_EQ|BHARTIARTL","NSE_EQ|ITC","NSE_EQ|LT","NSE_EQ|KOTAKBANK","NSE_EQ|AXISBANK","NSE_EQ|BAJFINANCE","NSE_EQ|MARUTI","NSE_EQ|TATAMOTORS","NSE_EQ|ADANIENT"]

ALL = indices+stocks

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
        time.sleep(0.4) # block se bachne ke liye
    return final

# --- DIRECT BAR LOGIC ---
if "last_prices" not in st.session_state: st.session_state["last_prices"]={}

# Har 10 sec me ek baar pura scan, warna purana data dikhao
now=time.time()
if "last_scan" not in st.session_state or now-st.session_state["last_scan"]>10:
    data=get_bulk_batched(ALL)
    if data:
        st.session_state["last_prices"]=data
        st.session_state["last_scan"]=now

prices=st.session_state["last_prices"]

# --- TOP BAR ---
if prices:
    bar_html=""
    for k in ALL:
        name=k.split("|")[-1]
        p=prices.get(k,{}).get("last_price")
        if p:
            bar_html+=f"<span style='margin-right:30px; color:#00ff88; font-weight:bold;'>{name}: ₹{p}</span>"
        else:
            bar_html+=f"<span style='margin-right:30px; color:gray;'>{name}: ...</span>"

    st.markdown(f"""
    <div style="background:#111; border:1px solid #333; padding:12px; border-radius:10px; overflow:hidden; white-space:nowrap;">
    <marquee scrollamount="6">{bar_html}</marquee>
    </div>
    """, unsafe_allow_html=True)
else:
    st.error("Bar fail - Token expire ya net slow, 10 sec me retry hoga")

# --- Niche table bhi ---
if prices:
    rows=[]
    for k in ALL:
        rows.append({"NAME":k.split("|")[-1], "LTP": prices.get(k,{}).get("last_price","WAIT")})
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

st.caption(f"Last Scan: {datetime.now().strftime('%H:%M:%S')} - Auto 10 sec")
time.sleep(1)
st.rerun()