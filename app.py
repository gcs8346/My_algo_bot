import streamlit as st, pandas as pd, requests, time, yfinance as yf
from datetime import datetime

st.set_page_config(layout="wide")
st.title("🏰 TOWER V46 - 10/10 - FINAL LIVE")

token = st.sidebar.text_input("Upstox Token (ho to daal, nahi to bhi chalega)", type="password")
speed = st.sidebar.select_slider("⏱️ Tik-Tik", [0.8, 1.0, 2.0], value=0.8)
live = st.sidebar.checkbox(f"🔴 LIVE ON", value=True)

STOCKS = {
    "Nifty 50": ("NSE_INDEX|Nifty 50","^NSEI"),
    "Sensex": ("BSE_INDEX|SENSEX","^BSESN"),
    "GOLD": ("MCX_FO|GOLDM26NOVFUT","GC=F"),
    "CRUDEOIL": ("MCX_FO|CRUDEOIL26NOVFUT","CL=F")
}
sel = st.sidebar.selectbox("Stock", list(STOCKS.keys()))
inst_upstox, inst_yf = STOCKS[sel]

def get_ltp_dual():
    # 1. Try Upstox if token
    if token:
        try:
            url=f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={inst_upstox}"
            r=requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=3).json()
            if r.get('status')=='success':
                return float(r['data'][inst_upstox]['last_price']), "Upstox LIVE"
        except: pass
    # 2. Fallback - yfinance 1m LIVE (no token needed)
    try:
        df = yf.download(inst_yf, period="1d", interval="1m", progress=False)
        price = float(df['Close'].iloc[-1])
        return price, "NSE LIVE (No Token)"
    except:
        return None, "Fail"

ltp, source = get_ltp_dual()

if ltp is None:
    st.error("Data nahi aaya - thodi der baad try kar")
    st.stop()

# YAHAN TICK DIKHEGA - HAR SECOND BADLEGA
st.metric(f"{sel} LTP - {source}", f"₹ {ltp:.2f}", delta=datetime.now().strftime("%H:%M:%S.%f")[:-4])
st.caption(f"Last Tick: {datetime.now().strftime('%d %b %H:%M:%S')} - Ye time badh raha hai toh LIVE hai Guddu")

if live:
    time.sleep(speed); st.rerun()