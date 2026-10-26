import streamlit as st, requests, time, pandas as pd
from datetime import datetime

st.set_page_config(page_title="TOWER V76 MCX TEST", layout="wide")
st.title("TOWER V76 - MCX NIGHT TEST")

raw = st.text_input("Upstox Token (Roz Naya)", type="password")
token = raw.strip().replace("Bearer ","").strip() if raw else st.session_state.get("tok","")
if raw: st.session_state["tok"]=token
if not token or len(token)<50:
    st.warning("Token daal"); st.stop()

headers={"Authorization":f"Bearer {token}","Accept":"application/json"}

NSE = ["NSE_INDEX|Nifty 50","NSE_INDEX|Nifty Bank","BSE_INDEX|Sensex"]
STOCKS = ["NSE_EQ|RELIANCE","NSE_EQ|TCS","NSE_EQ|INFY","NSE_EQ|HDFCBANK"]

# MCX - YE RAAT KO CHALEGA 11:30 TAK
MCX = [
    "MCX_FO|GOLD",
    "MCX_FO|GOLDM",
    "MCX_FO|SILVER",
    "MCX_FO|SILVERM", 
    "MCX_FO|CRUDEOIL",
    "MCX_FO|CRUDEOILM",
    "MCX_FO|NATURALGAS",
    "MCX_FO|COPPER"
]

ALL = NSE + MCX + STOCKS

def get_bulk_batched(keys, batch=8):
    final={}
    last_status=0
    for i in range(0,len(keys),batch):
        chunk=keys[i:i+batch]
        joined=",".join(chunk)
        try:
            r=requests.get("https://api.upstox.com/v3/market-quote/ltp", headers=headers, params={"instrument_key":joined}, timeout=8)
            last_status=r.status_code
            if r.status_code==200:
                final.update(r.json().get("data",{}))
            elif r.status_code==401:
                return {}, 401
            else:
                # V2 try
                r2=requests.get("https://api.upstox.com/v2/market-quote/ltp", headers=headers, params={"instrument_key":joined}, timeout=8)
                last_status=r2.status_code
                if r2.status_code==200:
                    final.update(r2.json().get("data",{}))
        except: pass
        time.sleep(0.5)
    return final, last_status

if "prices" not in st.session_state: st.session_state["prices"]={}
if "last_scan" not in st.session_state: st.session_state["last_scan"]=0

if time.time() - st.session_state["last_scan"] > 6:
    data, status = get_bulk_batched(ALL)
    if status==401:
        st.error("401 - Token khatam, naya bana"); st.stop()
    if data:
        st.session_state["prices"]=data
        st.session_state["last_scan"]=time.time()
    st.session_state["last_status"]=status

prices = st.session_state["prices"]
status = st.session_state.get("last_status",0)

# --- TOP BAR ---
bar_html=""
if prices:
    for k in ALL:
        name=k.split("|")[-1]
        p=prices.get(k,{}).get("last_price")
        color="#00ff88" if "MCX" in k else "#ffcc00" if "NSE_INDEX" in k or "BSE" in k else "white"
        if p:
            bar_html+=f"<span style='margin-right:35px; color:{color}; font-weight:bold;'>{name}: ₹{p}</span>"
else:
    bar_html=f"⚠️ NO DATA Status {status} - {datetime.now().strftime('%H:%M:%S')}"

st.markdown(f"<div style='background:#111; border:1px solid #333; padding:12px; border-radius:10px;'><marquee scrollamount='7'>{bar_html}</marquee></div>", unsafe_allow_html=True)

st.divider()

# --- MCX LIVE TEST - RAAT KO YE CHALEGA ---
st.subheader("🌙 MCX LIVE - Raat ko 11:30 tak chalega (Test)")
cols = st.columns(4)
mcx_keys = ["MCX_FO|GOLD","MCX_FO|SILVER","MCX_FO|CRUDEOIL","MCX_FO|NATURALGAS"]
for i, key in enumerate(mcx_keys):
    p = prices.get(key,{}).get("last_price") or prices.get(key+"M",{}).get("last_price")
    with cols[i]:
        if p:
            st.markdown(f"<div style='background:#1a1a1a; border:1px solid #ffaa00; padding:15px; border-radius:12px; text-align:center;'><div style='color:#ffaa00;'>{key.split('|')[-1]}</div><div style='color:#00ff88; font-size:28px; font-weight:900;'>₹{p}</div><div style='color:green; font-size:12px;'>● LIVE MCX</div></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='background:#111; border:1px solid #333; padding:15px; border-radius:12px; text-align:center;'><div style='color:gray;'>{key.split('|')[-1]}</div><div style='color:gray;'>WAIT...</div></div>", unsafe_allow_html=True)

st.divider()
st.subheader("☀️ NSE - Din me 9:15-3:30")
cols2 = st.columns(3)
for i, key in enumerate(NSE):
    p = prices.get(key,{}).get("last_price")
    with cols2[i]:
        if p:
            st.metric(key.split("|")[-1], f"₹{p}")
        else:
            st.metric(key.split("|")[-1], "Market Closed / No Data")

with st.expander("Full Table - Sabka LTP"):
    if prices:
        rows=[]
        for k in ALL:
            rows.append({"NAME": k, "LTP": prices.get(k,{}).get("last_price","NO DATA"), "TYPE": "MCX" if "MCX" in k else "NSE"})
        st.dataframe(pd.DataFrame(rows), width='stretch')
    else:
        st.write(f"No data yet - Status {status}")

st.caption(f"Last Scan {datetime.now().strftime('%H:%M:%S')} | Status {status} | MCX raat ko aayega to token OK hai")
time.sleep(1)
st.rerun()