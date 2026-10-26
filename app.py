import streamlit as st
import requests
import time
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="TOWER V70 FINAL", layout="wide")
st.title("TOWER V70 - FINAL")

# --- TOKEN ---
raw = st.text_input("Upstox Token (Roz Naya)", type="password")
if raw:
    token = raw.strip().replace("Bearer ","").replace("bearer ","").replace('"','').replace("'","").strip()
    st.session_state["tok"] = token
else:
    token = st.session_state.get("tok","")

if not token:
    st.warning("Token daal bhai")
    st.stop()
if len(token) < 50:
    st.error(f"Token chhota hai {len(token)} - pura copy kar")
    st.stop()

headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
speed = st.selectbox("Speed", ["0.1 sec", "0.8 sec", "2.0 sec"], index=1)
speed_val = 0.1 if "0.1" in speed else 0.8 if "0.8" in speed else 2.0

indices = ["NSE_INDEX|Nifty 50","NSE_INDEX|Nifty Bank","BSE_INDEX|Sensex"]
stocks = ["NSE_EQ|RELIANCE","NSE_EQ|TCS","NSE_EQ|INFY","NSE_EQ|HDFCBANK","NSE_EQ|ICICIBANK","NSE_EQ|SBIN","NSE_EQ|BHARTIARTL","NSE_EQ|ITC","NSE_EQ|LT","NSE_EQ|KOTAKBANK","NSE_EQ|AXISBANK","NSE_EQ|BAJFINANCE","NSE_EQ|ASIANPAINT","NSE_EQ|MARUTI","NSE_EQ|WIPRO","NSE_EQ|HCLTECH","NSE_EQ|SUNPHARMA","NSE_EQ|TITAN","NSE_EQ|ULTRACEMCO","NSE_EQ|POWERGRID","NSE_EQ|NTPC","NSE_EQ|ONGC","NSE_EQ|TATAMOTORS","NSE_EQ|TATASTEEL","NSE_EQ|JSWSTEEL","NSE_EQ|HINDALCO","NSE_EQ|COALINDIA","NSE_EQ|ADANIENT","NSE_EQ|ADANIPORTS","NSE_EQ|BAJAJFINSV","NSE_EQ|BAJAJ-AUTO","NSE_EQ|BPCL","NSE_EQ|BRITANNIA","NSE_EQ|CIPLA","NSE_EQ|DIVISLAB","NSE_EQ|DRREDDY","NSE_EQ|EICHERMOT","NSE_EQ|GRASIM","NSE_EQ|HEROMOTOCO","NSE_EQ|HINDUNILVR","NSE_EQ|INDUSINDBK","NSE_EQ|M&M","NSE_EQ|NESTLEIND","NSE_EQ|SBILIFE","NSE_EQ|SHREECEM","NSE_EQ|TATACONSUM","NSE_EQ|TECHM","NSE_EQ|UPL","NSE_EQ|HDFCLIFE"]

def get_ltp(key):
    try:
        r = requests.get("https://api.upstox.com/v3/market-quote/ltp", headers=headers, params={"instrument_key": key}, timeout=6)
        if r.status_code == 200:
            d = r.json().get("data", {}).get(key, {}).get("last_price")
            if d: return d, f"V3 OK {r.status_code}"
        r2 = requests.get("https://api.upstox.com/v2/market-quote/ltp", headers=headers, params={"instrument_key": key}, timeout=6)
        if r2.status_code == 200:
            data = r2.json().get("data", {})
            price = data.get(key, {}).get("last_price") if key in data else list(data.values())[0].get("last_price") if data else None
            if price: return price, f"V2 OK {r2.status_code}"
        return None, f"Fail {r.status_code}"
    except Exception as e:
        return None, str(e)

def get_bulk_ltp(all_keys):
    try:
        joined = ",".join(all_keys)
        r = requests.get("https://api.upstox.com/v3/market-quote/ltp", headers=headers, params={"instrument_key": joined}, timeout=10)
        if r.status_code == 200: return r.json().get("data", {})
        r2 = requests.get("https://api.upstox.com/v2/market-quote/ltp", headers=headers, params={"instrument_key": joined}, timeout=10)
        if r2.status_code == 200: return r2.json().get("data", {})
    except: pass
    return {}

ltp, stat = get_ltp("NSE_INDEX|Nifty 50")
if not ltp:
    st.error(f"LIVE fail {stat} - Token expire, naya daal")
    st.stop()

st.metric(f"Nifty 50 - {stat}", f"₹{ltp}")

if st.button("BULK SCAN - 53 Stocks"):
    all_keys = indices + stocks
    with st.spinner("Bulk LTP..."):
        bulk = get_bulk_ltp(all_keys)
    if not bulk:
        st.error("Bulk fail - 1 min ruk ke dabao")
        st.stop()
    res = []
    for key in all_keys:
        price = bulk.get(key, {}).get("last_price")
        res.append({"Name": key.split("|")[-1], "LTP": price if price else "NO DATA"})
    st.dataframe(pd.DataFrame(res), use_container_width=True, height=600)

st.caption(f"{datetime.now().strftime('%H:%M:%S')} | {speed}")
time.sleep(speed_val)
st.rerun()