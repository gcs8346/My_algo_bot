import streamlit as st, requests, time, pandas as pd
from datetime import datetime

st.set_page_config(page_title="TOWER V74 FIX", layout="wide")
st.title("TOWER V74 - LOG FIX - SINGLE FOCUS")

raw = st.text_input("Upstox Token (Roz Naya)", type="password")
token = raw.strip().replace("Bearer ","").strip() if raw else st.session_state.get("tok","")
if raw: st.session_state["tok"]=token
if not token or len(token)<50:
    st.warning("Token daal bhai"); st.stop()

headers={"Authorization":f"Bearer {token}","Accept":"application/json"}
ALL = ["NSE_INDEX|Nifty 50","NSE_INDEX|Nifty Bank","BSE_INDEX|Sensex","NSE_EQ|RELIANCE","NSE_EQ|TCS","NSE_EQ|INFY","NSE_EQ|HDFCBANK","NSE_EQ|ICICIBANK","NSE_EQ|SBIN","NSE_EQ|BHARTIARTL","NSE_EQ|ITC","NSE_EQ|LT"]

def get_bulk_batched(keys, batch=15):
    final={}
    for i in range(0,len(keys),batch):
        chunk=keys[i:i+batch]
        try:
            joined=",".join(chunk)
            r=requests.get("https://api.upstox.com/v3/market-quote/ltp", headers=headers, params={"instrument_key":joined}, timeout=8)
            if r.status_code==200:
                final.update(r.json().get("data",{}))
            elif r.status_code==401:
                st.error("401 - Token expire, naya bana"); st.stop()
            elif r.status_code==429:
                time.sleep(1)
        except: pass
        time.sleep(0.3)
    return final

if "prices" not in st.session_state: st.session_state["prices"]={}
if "last_scan" not in st.session_state: st.session_state["last_scan"]=0

now=time.time()
if now - st.session_state["last_scan"] > 8:
    data = get_bulk_batched(ALL)
    if data:
        st.session_state["prices"]=data
        st.session_state["last_scan"]=now

prices = st.session_state["prices"]

# TOP BAR
if prices:
    bar=""
    for k in ALL:
        p=prices.get(k,{}).get("last_price")
        if p:
            bar+=f"<span style='margin-right:35px; color:#00ff88; font-weight:bold;'>{k.split('|')[-1]}: ₹{p}</span>"
    st.markdown(f"<div style='background:#111; border:1px solid #333; padding:10px; border-radius:10px;'><marquee scrollamount='7'>{bar}</marquee></div>", width='stretch')
else:
    st.info("Pehli baar scan ho raha hai, 5 sec...")

st.divider()
focus = st.selectbox("MAIN pe kisko dekhna hai?", ALL, index=0)
main_price = prices.get(focus,{}).get("last_price") if prices else None

if main_price:
    st.markdown(f"""
    <div style="background:#151515; border:2px solid #00ff88; border-radius:18px; padding:25px; text-align:center;">
        <div style="color:gray; font-size:18px;">{focus.split('|')[-1]}</div>
        <div style="color:#00ff88; font-size:65px; font-weight:900;">₹{main_price}</div>
        <div style="color:#aaa;">{datetime.now().strftime('%H:%M:%S')} IST</div>
    </div>
    """, width='stretch')
else:
    st.warning("Rate aa raha hai...")

with st.expander("Full List"):
    if prices:
        rows=[{"NAME":k.split("|")[-1], "LTP": prices.get(k,{}).get("last_price","...")} for k in ALL]
        st.dataframe(pd.DataFrame(rows), width='stretch')

st.caption(f"Last Scan: {datetime.fromtimestamp(st.session_state['last_scan']).strftime('%H:%M:%S') if st.session_state['last_scan'] else '...'} | No use_container_width warning now")
time.sleep(1)
st.rerun()