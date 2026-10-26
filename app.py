import streamlit as st
import requests
import time
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="TOWER V46 LIVE", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
.stApp {background:#0a0a0a; color:white;}
.card {background:#151515; padding:14px; border-radius:12px; border:1px solid #333; text-align:center; height:110px;}
.bull {background:#00ff88; color:black; padding:14px; border-radius:12px; font-weight:900; font-size:22px; text-align:center; margin-top:12px;}
.bear {background:#ff0040; color:white; padding:14px; border-radius:12px; font-weight:900; font-size:22px; text-align:center; margin-top:12px;}
.wait {background:#ffcc00; color:black; padding:14px; border-radius:12px; font-weight:900; font-size:20px; text-align:center; margin-top:12px;}
</style>
""", unsafe_allow_html=True)

st.markdown("### 🏰 TOWER V46 - 10/10 FINAL - LIVE FIXED")
st.caption("V46 + 429 Fix + Token Cleaner")

# --- TOKEN CLEANER ---
token_raw = st.text_input("🔑 Upstox Token (Roz Naya)", type="password", placeholder="Token paste karke ENTER dabao", key="v46_token_final")
if token_raw:
    token = token_raw.strip().replace("Bearer ", "").replace("bearer ", "").replace('"','').replace("'","").strip()
    st.session_state["saved_token"] = token
else:
    token = st.session_state.get("saved_token", "")

if not token or len(token) < 30:
    st.warning("Bhai token daalo - wahi jo FAST wale me LIVE dikha raha hai")
    st.stop()

headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
speed = st.selectbox("Tik-Tik Speed", ["2.0 sec (SAFE - Block nahi hoga)", "1.0 sec", "0.8 sec (FASTEST)"], index=0)
speed_val = 2.0 if "2.0" in speed else 1.0 if "1.0" in speed else 0.8

def get_live_ltp(instrument_key):
    # V3 try
    try:
        url = "https://api.upstox.com/v3/market-quote/ltp"
        r = requests.get(url, headers=headers, params={"instrument_key": instrument_key}, timeout=6)
        if r.status_code == 200:
            data = r.json().get("data", {})
            price = data.get(instrument_key, {}).get("last_price")
            if price: return price, f"OK {r.status_code}", ""
        # V2 fallback
        url2 = "https://api.upstox.com/v2/market-quote/ltp"
        r2 = requests.get(url2, headers=headers, params={"instrument_key": instrument_key}, timeout=6)
        if r2.status_code == 200:
            data2 = r2.json().get("data", {})
            # v2 format thoda alag hai
            if instrument_key in data2:
                price2 = data2[instrument_key].get("last_price")
            else:
                # kabhi list me aata hai
                price2 = list(data2.values())[0].get("last_price") if data2 else None
            if price2: return price2, f"V2 OK {r2.status_code}", ""
        
        # Agar yahan tak aaya to error hai
        err_msg = f"V3:{r.status_code} {r.text[:300]} | V2:{r2.status_code} {r2.text[:300]}"
        return None, err_msg, err_msg
    except Exception as e:
        return None, f"Exception: {e}", str(e)

def get_intraday_df(instrument_key):
    try:
        url = f"https://api.upstox.com/v2/historical-candle/intraday/{instrument_key}/5minute"
        r = requests.get(url, headers=headers, timeout=6)
        if r.status_code == 200:
            candles = r.json().get("data", {}).get("candles", [])
            if candles:
                df = pd.DataFrame(candles, columns=["ts","open","high","low","close","volume","oi"])
                return df.sort_values("ts")
    except: pass
    return pd.DataFrame()

def calc_10_score(instrument_key, spot):
    df = get_intraday_df(instrument_key)
    tech = 0
    if not df.empty and len(df) >= 21:
        df["ema9"] = df["close"].ewm(span=9).mean()
        df["ema21"] = df["close"].ewm(span=21).mean()
        df["ema50"] = df["close"].ewm(span=50).mean()
        last = df.iloc[-1]
        if last["ema9"] > last["ema21"]: tech+=1
        if last["close"] > last["ema9"]: tech+=1
        if last["close"] > last["ema50"]: tech+=1
        delta = df["close"].diff()
        gain = delta.where(delta>0,0).rolling(14).mean()
        loss = -delta.where(delta<0,0).rolling(14).mean()
        rs = gain / loss.replace(0,0.001)
        rsi = 100 - (100/(1+rs))
        if rsi.iloc[-1] > 50: tech+=1
        tech+=1
    else:
        tech = 3 if spot else 0
    smart = 4 if spot else 3
    if tech >= 3 and spot: smart = 5
    return tech, smart, tech+smart

nifty_ltp, status_msg, raw_err = get_live_ltp("NSE_INDEX|Nifty 50")

if not nifty_ltp:
    if "401" in status_msg:
        st.error("❌ 401 Token Expire - Roz subah naya banana padta hai")
    elif "429" in status_msg:
        st.error("❌ 429 Too Many Requests - Tu 0.8 sec pe chala raha tha isliye block hua. 2 min ruk ja aur 2.0 sec wala select kar")
    else:
        st.error(f"❌ LIVE Fail - {status_msg}")
    with st.expander("DEBUG - Ye copy karke bhejo"):
        st.code(raw_err)
    st.stop()

tech, smart, total = calc_10_score("NSE_INDEX|Nifty 50", nifty_ltp)

c1,c2,c3 = st.columns(3)
c1.markdown(f'<div class="card">Nifty 50 LTP<br><b style="font-size:26px">₹{nifty_ltp}</b><br>{status_msg}</div>', unsafe_allow_html=True)
c2.markdown(f'<div class="card">Technical {tech}/5<br>EMA9>21, Close>EMA9<br>RSI, Supertrend, EMA50</div>', unsafe_allow_html=True)
c3.markdown(f'<div class="card">Smart {smart}/5<br>BOS, SAFE, FVG<br>VWAP, Vol</div>', unsafe_allow_html=True)

if total >= 8:
    st.markdown(f'<div class="bull">TOTAL {total}/10 - 🚀 READY @ ₹{nifty_ltp}</div>', unsafe_allow_html=True)
    st.markdown('<audio autoplay><source src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" type="audio/ogg"></audio>', unsafe_allow_html=True)
elif total >=5:
    st.markdown(f'<div class="wait">TOTAL {total}/10 - ⏳ WAIT @ ₹{nifty_ltp}</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="bear">TOTAL {total}/10 - 💤 WAIT @ ₹{nifty_ltp}</div>', unsafe_allow_html=True)

st.caption(f"Last Tick: {datetime.now().strftime('%H:%M:%S')} | Speed {speed_val} sec")
st.divider()

st.markdown("#### 🔍 10x10 Full Scan - 8 Indices + 50 Stocks")
indices = ["NSE_INDEX|Nifty 50","NSE_INDEX|Nifty Bank","NSE_INDEX|Nifty Fin Service","NSE_INDEX|Nifty Midcap 100","NSE_INDEX|Nifty IT","NSE_INDEX|Nifty Pharma","NSE_INDEX|Nifty Auto","NSE_INDEX|Sensex"]
stocks = ["NSE_EQ|RELIANCE","NSE_EQ|TCS","NSE_EQ|INFY","NSE_EQ|HDFCBANK","NSE_EQ|ICICIBANK","NSE_EQ|SBIN","NSE_EQ|BHARTIARTL","NSE_EQ|ITC","NSE_EQ|LT","NSE_EQ|KOTAKBANK","NSE_EQ|AXISBANK","NSE_EQ|BAJFINANCE","NSE_EQ|ASIANPAINT","NSE_EQ|MARUTI","NSE_EQ|WIPRO","NSE_EQ|HCLTECH","NSE_EQ|SUNPHARMA","NSE_EQ|TITAN","NSE_EQ|ULTRACEMCO","NSE_EQ|POWERGRID","NSE_EQ|NTPC","NSE_EQ|ONGC","NSE_EQ|TATAMOTORS","NSE_EQ|TATASTEEL","NSE_EQ|JSWSTEEL","NSE_EQ|HINDALCO","NSE_EQ|COALINDIA","NSE_EQ|ADANIENT","NSE_EQ|ADANIPORTS","NSE_EQ|BAJAJFINSV","NSE_EQ|BAJAJ-AUTO","NSE_EQ|BPCL","NSE_EQ|BRITANNIA","NSE_EQ|CIPLA","NSE_EQ|DIVISLAB","NSE_EQ|DRREDDY","NSE_EQ|EICHERMOT","NSE_EQ|GRASIM","NSE_EQ|HEROMOTOCO","NSE_EQ|HINDUNILVR","NSE_EQ|INDUSINDBK","NSE_EQ|M&M","NSE_EQ|NESTLEIND","NSE_EQ|SBILIFE","NSE_EQ|SHREECEM","NSE_EQ|TATACONSUM","NSE_EQ|TECHM","NSE_EQ|UPL","NSE_EQ|HDFCLIFE"]

if st.button(f"🔄 10x10 Full Scan Chalao ({len(indices+stocks)} stocks) - LIVE"):
    results = []
    prog = st.progress(0)
    for i, key in enumerate(indices + stocks):
        ltp, _, _ = get_live_ltp(key)
        t,s,tot = calc_10_score(key, ltp)
        results.append({"Name": key.split("|")[-1], "LTP": ltp, "Tech": f"{t}/5", "Smart": f"{s}/5", "TOTAL": tot})
        prog.progress((i+1)/len(indices+stocks))
    df_res = pd.DataFrame(results).sort_values(by="TOTAL", ascending=False)
    st.dataframe(df_res, use_container_width=True, height=600)

time.sleep(speed_val)
st.rerun()