import streamlit as st, requests, time, pandas as pd
from datetime import datetime

st.set_page_config(page_title="TOWER V75 BAR FIX", layout="wide")
st.title("TOWER V75 - BAR FIX")

raw = st.text_input("Upstox Token (Roz Naya)", type="password")
token = raw.strip().replace("Bearer ","").strip() if raw else st.session_state.get("tok","")
if raw: st.session_state["tok"]=token
if not token or len(token)<50:
    st.warning("Token daal"); st.stop()

headers={"Authorization":f"Bearer {token}","Accept":"application/json"}
ALL = ["NSE_INDEX|Nifty 50","NSE_INDEX|Nifty Bank","BSE_INDEX|Sensex","NSE_EQ|RELIANCE","NSE_EQ|TCS","NSE_EQ|INFY","NSE_EQ|HDFCBANK","NSE_EQ|ICICIBANK","NSE_EQ|SBIN","NSE_EQ|BHARTIARTL"]

def get_bulk_batched(keys, batch=10):
    final={}
    last_status=0
    for i in range(0,len(keys),batch):
        chunk=keys[i:i+batch]
        joined=",".join(chunk)
        try:
            r=requests.get("https://api.upstox.com/v3/market-quote/ltp", headers=headers, params={"instrument_key":joined}, timeout=8)
            last_status=r.status_code
            if r.status_code==200:
                data=r.json().get("data",{})
                final.update(data)
            elif r.status_code==401:
                return {}, 401
            elif r.status_code==429:
                time.sleep(2)
            # V2 fallback
            if not data:
                r2=requests.get("https://api.upstox.com/v2/market-quote/ltp", headers=headers, params={"instrument_key":joined}, timeout=8)
                last_status=r2.status_code
                if r2.status_code==200:
                    final.update(r2.json().get("data",{}))
        except Exception as e:
            pass
        time.sleep(0.4)
    return final, last_status

if "prices" not in st.session_state: st.session_state["prices"]={}
if "last_scan" not in st.session_state: st.session_state["last_scan"]=0

if time.time() - st.session_state["last_scan"] > 8:
    data, status = get_bulk_batched(ALL)
    if status==401:
        st.error("❌ 401 - Token expire ho gaya, naya bana ke daal")
        st.stop()
    if data:
        st.session_state["prices"]=data
        st.session_state["last_scan"]=time.time()
        st.session_state["last_status"]=status
    else:
        st.session_state["last_status"]=status

prices = st.session_state["prices"]
last_status = st.session_state.get("last_status",0)

# --- TOP BAR - AB KHALI NAHI RAHEGA ---
bar_html = ""
if prices:
    for k in ALL:
        name=k.split("|")[-1]
        p=prices.get(k,{}).get("last_price")
        if p:
            bar_html+=f"<span style='margin-right:35px; color:#00ff88; font-weight:bold;'>{name}: ₹{p}</span>"
        else:
            bar_html+=f"<span style='margin-right:35px; color:gray;'>{name}: ...</span>"
else:
    bar_html = f"⚠️ DATA NAHI AAYA - Status {last_status} - Token expire ya Market band hai (Mon-Fri 9:15-15:30) - {datetime.now().strftime('%H:%M:%S')}"

st.markdown(f"<div style='background:#111; border:1px solid #333; padding:12px; border-radius:10px; overflow:hidden;'><marquee scrollamount='7'>{bar_html}</marquee></div>", unsafe_allow_html=True)

# --- MAIN FOCUS ---
focus = st.selectbox("MAIN pe kisko dekhna hai?", ALL, index=0)
mp = prices.get(focus,{}).get("last_price") if prices else None
if mp:
    st.markdown(f"<div style='background:#151515; border:2px solid #00ff88; border-radius:18px; padding:25px; text-align:center;'><div style='color:gray;'>{focus.split('|')[-1]}</div><div style='color:#00ff88; font-size:65px; font-weight:900;'>₹{mp}</div></div>", unsafe_allow_html=True)
else:
    st.warning(f"{focus.split('|')[-1]} ka rate aa raha hai... Status {last_status}")

with st.expander("Full Table"):
    if prices:
        rows=[{"NAME":k.split("|")[-1], "LTP": prices.get(k,{}).get("last_price","...")} for k in ALL]
        st.dataframe(pd.DataFrame(rows), width='stretch')
    else:
        st.write(f"No data - last status {last_status}")

time.sleep(1)
st.rerun()