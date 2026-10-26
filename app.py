import streamlit as st
import requests
import time
import json
import gzip
from datetime import datetime

st.set_page_config(page_title="TOWER V83 CENTURY", layout="wide")
st.title("TOWER V83 - CENTURY PURI 🔥")

# --- TOKEN ---
raw = st.text_input("Upstox Token (Roz Naya)", type="password")
token = raw.strip().replace("Bearer ","").strip() if raw else st.session_state.get("tok","")
if raw:
    st.session_state["tok"] = token

if not token or len(token) < 50:
    st.warning("Token daal bhai - Roz naya banta hai")
    st.stop()

headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

# --- EXPIRY FIX ---
def format_expiry(e):
    try:
        if e is None:
            return "N/A"
        if isinstance(e, int):
            # ms -> sec
            ts = e/1000 if e > 10000000000 else e
            return datetime.fromtimestamp(ts).strftime("%d %b %y")
        if isinstance(e, str):
            return e.split("T")[0]
    except:
        return str(e)
    return str(e)

def parse_expiry_dt(e):
    try:
        if isinstance(e, int):
            ts = e/1000 if e > 10000000000 else e
            return datetime.fromtimestamp(ts)
        if isinstance(e, str):
            return datetime.fromisoformat(e.split("T")[0])
    except:
        return datetime.now()
    return datetime.now()

# --- MCX KEYS - ABHI JO LIVE HAI WOHI ---
@st.cache_data(ttl=3600)
def get_mcx_keys():
    try:
        url = "https://assets.upstox.com/market-quote/instruments/exchange/MCX.json.gz"
        r = requests.get(url, timeout=15)
        all_ins = json.loads(gzip.decompress(r.content))
        
        wanted = {
            "GOLD": "GOLD",
            "SILVER": "SILVER", 
            "CRUDEOIL": "CRUDEOIL",
            "NATURALGAS": "NATURALGAS"
        }
        
        found = {}
        for name, sym_start in wanted.items():
            cand = [x for x in all_ins if x.get("trading_symbol","").startswith(sym_start) and x.get("instrument_type")=="FUT"]
            # nearest expiry wala le
            cand_sorted = sorted(cand, key=lambda x: parse_expiry_dt(x.get("expiry")))
            if cand_sorted:
                # jo sabse near hai par future me hai
                future = [x for x in cand_sorted if parse_expiry_dt(x.get("expiry")) >= datetime.now()]
                pick = future[0] if future else cand_sorted[0]
                found[name] = pick
        return found
    except Exception as e:
        st.error(f"MCX file error: {e}")
        return {}

mcx_details = get_mcx_keys()

if not mcx_details:
    st.error("MCX keys nahi mile")
    st.stop()

# Show Keys OK
keys_str = ", ".join([f"{k}->{v['instrument_key']} ({format_expiry(v.get('expiry'))})" for k,v in mcx_details.items()])
st.success(f"MCX Keys OK: {keys_str}")

MCX_KEYS = [v["instrument_key"] for v in mcx_details.values()]
ALL_KEYS = MCX_KEYS + ["NSE_INDEX|Nifty 50"]

# --- LTP FIX - CENTURY WALA FIX ---
def get_ltp(keys):
    final = {}
    status = 0
    raw_debug = {}
    for i in range(0, len(keys), 6):
        chunk = keys[i:i+6]
        joined = ",".join(chunk)
        try:
            r = requests.get(
                "https://api.upstox.com/v3/market-quote/ltp",
                headers=headers,
                params={"instrument_key": joined},
                timeout=10
            )
            status = r.status_code
            raw_debug[joined] = r.text[:1500]
            
            if r.status_code == 200:
                data = r.json().get("data", {})
                # YAHI FIX HAI - instrument_token se map karo
                for trade_sym, quote in data.items():
                    inst_tok = quote.get("instrument_token")
                    if inst_tok:
                        final[inst_tok] = quote  # MCX_FO|495213 -> data
                    final[trade_sym] = quote     # MCX_FO:GOLD26DECFUT -> data (backup)
            elif r.status_code == 401:
                return {}, 401, raw_debug
        except Exception as e:
            raw_debug[joined] = str(e)
        time.sleep(0.3)
    return final, status, raw_debug

prices, status, raw_debug = get_ltp(ALL_KEYS)

# --- LIVE TICKER ---
bar_text = ""
for sym, det in mcx_details.items():
    k = det["instrument_key"]
    q = prices.get(k, {})
    p = q.get("last_price")
    if p:
        bar_text += f"<span style='margin-right:40px;color:#00ff88;font-weight:bold;font-size:16px;'>{sym}: ₹{p}</span>"

if not bar_text:
    bar_text = f"<span style='color:orange'>MCX WAIT Status {status} - {datetime.now().strftime('%H:%M:%S')} - Debug neeche dekho</span>"
else:
    bar_text = f"<span style='color:#00ff88'>🔥 MCX LIVE - {datetime.now().strftime('%H:%M:%S')} </span>" + bar_text

st.markdown(f"<div style='background:#0e1117;border:1px solid #00ff88;padding:14px;border-radius:12px;'><marquee scrollamount='8'>{bar_text}</marquee></div>", unsafe_allow_html=True)

st.write("")

# --- METRICS ---
cols = st.columns(4)
for idx, (sym, det) in enumerate(mcx_details.items()):
    k = det["instrument_key"]
    q = prices.get(k, {})
    last = q.get("last_price", "WAIT")
    cp = q.get("cp", 0)
    expiry_fmt = format_expiry(det.get("expiry"))
    
    with cols[idx % 4]:
        if last != "WAIT":
            diff = last - cp if cp else 0
            st.metric(sym, f"₹{last}", f"{diff:+.1f} ({expiry_fmt})")
            st.caption(f"{det['instrument_key']}")
        else:
            st.metric(sym, "WAIT", expiry_fmt)

# --- DEBUG ---
with st.expander("Debug - API kya de raha hai (LIVE hai toh yahan price dikhega)"):
    st.json(prices)
    st.write(raw_debug)

st.caption(f"Last Updated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')} | Status: {status} | Century = V83")