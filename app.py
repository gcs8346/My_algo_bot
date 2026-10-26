import streamlit as st, requests, time, pandas as pd, gzip, json
from datetime import datetime

st.set_page_config(page_title="TOWER V80 MCX FIX", layout="wide")
st.title("TOWER V80 - MCX ABHI LIVE - TYPE FIX")

raw = st.text_input("Upstox Token (Roz Naya)", type="password")
token = raw.strip().replace("Bearer ","").strip() if raw else st.session_state.get("tok","")
if raw: st.session_state["tok"]=token
if not token or len(token)<50:
    st.warning("Token daal bhai"); st.stop()

headers={"Authorization":f"Bearer {token}","Accept":"application/json"}

@st.cache_data(ttl=1800)
def get_mcx_live_keys():
    try:
        url = "https://assets.upstox.com/market-quote/instruments/exchange/MCX.json.gz"
        r = requests.get(url, timeout=10)
        data = gzip.decompress(r.content)
        all_ins = json.loads(data)
        wanted = ["GOLD","SILVER","CRUDEOIL","NATURALGAS"]
        found = {}
        for sym in wanted:
            # Bas FUT type dhundo, expiry ka type check nahi karenge
            cand = [x for x in all_ins if sym in x.get("trading_symbol","") and x.get("instrument_type")=="FUT" and x.get("instrument_key","").startswith("MCX")]
            # expiry ko string bana ke sort karo - ab int vs str ka error nahi ayega
            cand = sorted(cand, key=lambda x: str(x.get("expiry","")) )
            if cand:
                found[sym] = cand[0]
        return found
    except Exception as e:
        return {"ERROR": str(e)}

mcx_details = get_mcx_live_keys()

if "ERROR" in mcx_details:
    st.error(f"MCX file error: {mcx_details['ERROR']}")
    st.stop()

if not mcx_details:
    st.error("MCX keys nahi mile file me")
    st.stop()

st.success(f"MCX Keys OK: {', '.join([f'{k}->{v['instrument_key']}' for k,v in mcx_details.items()])}")

MCX_KEYS = [v["instrument_key"] for v in mcx_details.values()]
NSE_KEYS = ["NSE_INDEX|Nifty 50","NSE_INDEX|Nifty Bank","BSE_INDEX|SENSEX"]
ALL = MCX_KEYS + NSE_KEYS

def get_ltp(keys):
    final={}
    status=0
    for i in range(0,len(keys),8):
        chunk=keys[i:i+8]
        joined=",".join(chunk)
        try:
            r=requests.get("https://api.upstox.com/v3/market-quote/ltp", headers=headers, params={"instrument_key":joined}, timeout=8)
            status=r.status_code
            if r.status_code==200:
                final.update(r.json().get("data",{}))
            elif r.status_code==401:
                return {}, 401
        except: pass
        time.sleep(0.4)
    return final, status

if "prices" not in st.session_state: st.session_state["prices"]={}
if "last_scan" not in st.session_state: st.session_state["last_scan"]=0

if time.time() - st.session_state["last_scan"] > 5:
    data, st_code = get_ltp(ALL)
    if st_code==401:
        st.error("401 - Token expire, naya bana"); st.stop()
    if data:
        st.session_state["prices"]=data
        st.session_state["last_scan"]=time.time()
    st.session_state["last_status"]=st_code

prices = st.session_state["prices"]
st_code = st.session_state.get("last_status",0)

bar=""
if prices:
    for sym, det in mcx_details.items():
        k=det["instrument_key"]
        p=prices.get(k,{}).get("last_price")
        if p:
            bar+=f"<span style='margin-right:40px; color:#ffaa00; font-weight:bold;'>🔥 {sym}: ₹{p}</span>"
if not bar:
    bar=f"MCX WAIT - Status {st_code} - Token daal ke 5 sec wait kar - {datetime.now().strftime('%H:%M:%S')}"

st.markdown(f"<div style='background:#111; border:1px solid #ffaa00; padding:12px; border-radius:10px;'><marquee scrollamount='8'>{bar}</marquee></div>", unsafe_allow_html=True)

st.divider()
st.subheader("🔥 MCX LIVE - ABHI")
cols = st.columns(3)
for idx, (sym, det) in enumerate(mcx_details.items()):
    k=det["instrument_key"]
    p=prices.get(k,{}).get("last_price")
    with cols[idx % 3]:
        if p:
            st.markdown(f"<div style='background:#1a1a1a; border:1.5px solid #ffaa00; padding:18px; border-radius:14px; text-align:center; margin-bottom:10px;'><div style='color:#ffaa00; font-weight:bold;'>{sym}</div><div style='color:#00ff88; font-size:32px; font-weight:900;'>₹{p}</div><div style='color:green; font-size:12px;'>● LIVE NOW</div></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='background:#111; border:1px solid #333; padding:18px; border-radius:14px; text-align:center;'><div style='color:gray;'>{sym}</div><div>WAIT...</div><div style='font-size:9px; color:gray;'>{k}</div></div>", unsafe_allow_html=True)

with st.expander("Debug Table"):
    rows=[{"SYM": sym, "KEY": det["instrument_key"], "LTP": prices.get(det["instrument_key"],{}).get("last_price","NO DATA")} for sym, det in mcx_details.items()]
    st.dataframe(pd.DataFrame(rows), width='stretch')

st.caption(f"Last {datetime.now().strftime('%H:%M:%S')} | Status {st_code}")
time.sleep(1)
st.rerun()