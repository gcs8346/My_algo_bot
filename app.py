import streamlit as st, requests, time, pandas as pd, gzip, json
from datetime import datetime

st.set_page_config(page_title="TOWER V78 MCX AUTO", layout="wide")
st.title("TOWER V78 - MCX Auto Fix")

raw = st.text_input("Upstox Token (Roz Naya)", type="password")
token = raw.strip().replace("Bearer ","").strip() if raw else st.session_state.get("tok","")
if raw: st.session_state["tok"]=token
if not token or len(token)<50:
    st.warning("Token daal bhai"); st.stop()

headers={"Authorization":f"Bearer {token}","Accept":"application/json"}

# --- MCX KEYS AUTO NIKALO - YAHI FIX HAI ---
@st.cache_data(ttl=3600)
def get_mcx_keys():
    try:
        url = "https://assets.upstox.com/market-quote/instruments/exchange/MCX.json.gz"
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return {}
        data = gzip.decompress(r.content)
        instruments = json.loads(data)
        found = {}
        # GOLD, SILVER, CRUDEOIL, NATURALGAS ka nearest FUT dhundo
        for base in ["GOLD", "SILVER", "CRUDEOIL", "NATURALGAS"]:
            candidates = [x for x in instruments if base in x.get("trading_symbol","") and x.get("instrument_type")=="FUT"]
            # expiry sabse nazdeek wala
            candidates = sorted(candidates, key=lambda x: x.get("expiry",""))
            if candidates:
                found[base] = candidates[0]["instrument_key"]
        return found
    except Exception as e:
        return {"ERROR": str(e)}

mcx_map = get_mcx_keys()
st.caption(f"MCX Auto Keys Found: {mcx_map}")

NSE = ["NSE_INDEX|Nifty 50","NSE_INDEX|Nifty Bank","BSE_INDEX|SENSEX"]
STOCKS = ["NSE_EQ|RELIANCE","NSE_EQ|TCS","NSE_EQ|INFY"]
MCX = list(mcx_map.values()) if mcx_map and "ERROR" not in mcx_map else []

ALL = NSE + MCX + STOCKS
if not ALL:
    st.error("MCX keys nahi mile, NSE se hi test kar raha hu")
    ALL = NSE + STOCKS

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
                return {}, 401, r.text[:200]
            else:
                r2=requests.get("https://api.upstox.com/v2/market-quote/ltp", headers=headers, params={"instrument_key":joined}, timeout=8)
                if r2.status_code==200:
                    final.update(r2.json().get("data",{}))
                    last_status=r2.status_code
        except Exception as e:
            last_status=0
        time.sleep(0.4)
    return final, last_status, ""

if "prices" not in st.session_state: st.session_state["prices"]={}
if "last_scan" not in st.session_state: st.session_state["last_scan"]=0

if time.time() - st.session_state["last_scan"] > 6:
    data, status, err = get_bulk_batched(ALL)
    if status==401:
        st.error(f"401 - Token khatam {err}"); st.stop()
    if data:
        st.session_state["prices"]=data
        st.session_state["last_scan"]=time.time()
    st.session_state["last_status"]=status

prices = st.session_state["prices"]
status = st.session_state.get("last_status",0)

# TOP BAR
bar_html=""
if prices:
    for k in ALL:
        name=k.split("|")[-1]
        p=prices.get(k,{}).get("last_price")
        if p:
            color="#00ff88" if k in MCX else "#ffcc00" if "INDEX" in k else "white"
            bar_html+=f"<span style='margin-right:35px; color:{color}; font-weight:bold;'>{name}: ₹{p}</span>"
if not bar_html:
    bar_html=f"⚠️ WAIT - Status {status} - {datetime.now().strftime('%H:%M:%S')} - Token check karo"

st.markdown(f"<div style='background:#111; border:1px solid #333; padding:12px; border-radius:10px;'><marquee scrollamount='7'>{bar_html}</marquee></div>", unsafe_allow_html=True)

st.divider()
focus = st.selectbox("MAIN pe kisko dekhna hai?", ALL, index=0)
mp = prices.get(focus,{}).get("last_price") if prices else None
if mp:
    st.markdown(f"<div style='background:#151515; border:2px solid #00ff88; border-radius:18px; padding:25px; text-align:center;'><div style='color:gray;'>{focus}</div><div style='color:#00ff88; font-size:60px; font-weight:900;'>₹{mp}</div><div>Status {status} | {datetime.now().strftime('%H:%M:%S')}</div></div>", unsafe_allow_html=True)
else:
    st.warning(f"{focus} WAIT - Status {status} - MCX ke liye raat 11:30 tak wait karo, agar tab bhi nahi aaya to Upstox me MCX segment enable nahi hai")

with st.expander("Debug - MCX Keys + Full Table"):
    st.write("Found MCX Map:", mcx_map)
    if prices:
        rows=[{"KEY":k, "LTP": prices.get(k,{}).get("last_price","NO DATA")} for k in ALL]
        st.dataframe(pd.DataFrame(rows), width='stretch')

time.sleep(1)
st.rerun()