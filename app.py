import streamlit as st, requests, time, pandas as pd, gzip, json
from datetime import datetime

st.set_page_config(page_title="TOWER V82 MCX FINAL", layout="wide")
st.title("TOWER V82 - MCX MONDAY FIX")

raw = st.text_input("Upstox Token (Roz Naya)", type="password")
token = raw.strip().replace("Bearer ","").strip() if raw else st.session_state.get("tok","")
if raw: st.session_state["tok"]=token
if not token or len(token)<50:
    st.warning("Token daal bhai"); st.stop()

headers={"Authorization":f"Bearer {token}","Accept":"application/json"}

def parse_expiry(e):
    try:
        if e is None: return None
        if isinstance(e, int):
            # ms me hota hai kabhi
            ts = e/1000 if e > 10000000000 else e
            return datetime.fromtimestamp(ts)
        if isinstance(e, str):
            return datetime.fromisoformat(e.split("T")[0])
    except:
        return None
    return None

@st.cache_data(ttl=1800)
def get_mcx_live_keys():
    try:
        url = "https://assets.upstox.com/market-quote/instruments/exchange/MCX.json.gz"
        r = requests.get(url, timeout=10)
        all_ins = json.loads(gzip.decompress(r.content))
        wanted = ["GOLD","SILVER","CRUDEOIL","NATURALGAS"]
        found = {}
        today = datetime.now()
        for sym in wanted:
            cand = [x for x in all_ins if sym == x.get("trading_symbol","").split()[0] and x.get("instrument_type")=="FUT"]
            # future expiry filter
            future = []
            for x in cand:
                exp_dt = parse_expiry(x.get("expiry"))
                if exp_dt and exp_dt >= today:
                    future.append((exp_dt, x))
            if not future:
                future = [(parse_expiry(x.get("expiry")) or today, x) for x in cand] # fallback
            future = sorted(future, key=lambda y: y[0])
            if future:
                found[sym] = future[0][1]
        return found
    except Exception as e:
        return {"ERROR": str(e)}

mcx_details = get_mcx_live_keys()
if "ERROR" in mcx_details:
    st.error(f"Error: {mcx_details['ERROR']}"); st.stop()

st.success(f"MCX Keys OK: {', '.join([f'{k}->{v['instrument_key']} ({v.get('expiry')})' for k,v in mcx_details.items()])}")

MCX_KEYS = [v["instrument_key"] for v in mcx_details.values()]
ALL = MCX_KEYS + ["NSE_INDEX|Nifty 50"]

def get_ltp(keys):
    final={}; status=0; raw={}
    for i in range(0,len(keys),8):
        joined=",".join(keys[i:i+8])
        try:
            r=requests.get("https://api.upstox.com/v3/market-quote/ltp", headers=headers, params={"instrument_key":joined}, timeout=10)
            status=r.status_code
            raw[joined]=r.text[:800]
            if r.status_code==200:
                final.update(r.json().get("data",{}))
            elif r.status_code==401:
                return {},401,raw
        except Exception as e:
            raw[joined]=str(e)
        time.sleep(0.3)
    return final,status,raw

prices,status,raw_debug = get_ltp(ALL)

# UI
bar=""
for sym, det in mcx_details.items():
    k=det["instrument_key"]
    p=prices.get(k,{}).get("last_price")
    if p: bar+=f"<span style='margin-right:30px;color:#ffaa00;font-weight:bold;'>{sym}: ₹{p}</span>"
if not bar: bar=f"MCX WAIT Status {status} - MCX segment enable karo Upstox me - {datetime.now().strftime('%H:%M:%S')}"

st.markdown(f"<div style='background:#111;border:1px solid #ffaa00;padding:12px;border-radius:10px;'><marquee scrollamount='8'>{bar}</marquee></div>", unsafe_allow_html=True)

cols=st.columns(4)
for idx,(sym,det) in enumerate(mcx_details.items()):
    k=det["instrument_key"]
    p=prices.get(k,{}).get("last_price","WAIT")
    with cols[idx]:
        st.metric(sym, f"₹{p}" if p!="WAIT" else "WAIT", det.get("expiry"))

with st.expander("Debug - API kya de raha hai"):
    st.json(prices)
    st.write(raw_debug)

st.caption("Agar NSE chal raha tha din me aur MCX WAIT tha = 100% MCX segment band hai Upstox me")