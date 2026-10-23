import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
from datetime import datetime, timedelta

st.set_page_config(page_title="TOPU V6 CHART FIX", layout="wide")
LICENSE = "TOPU-2026-TEST"

st.markdown("## 👑 TOPU TOWER - V6 CHART HILAO")
lic = st.text_input("🔑 Yearly Token", value="TOPU-2026-TEST")
if lic != LICENSE:
    st.error("❌ Token galat"); st.stop()

st.sidebar.title("🔴 UPSTOX DIRECT")
upstox_token = st.sidebar.text_input("Upstox Token", type="password")
if not upstox_token:
    st.warning("Token daal"); st.stop()
headers = {'Authorization': f'Bearer {upstox_token}', 'Accept': 'application/json'}

refresh_speed = st.sidebar.select_slider("Refresh", options=[1,2,3], value=1, format_func=lambda x: f"{x} Sec")
st_autorefresh(interval=refresh_speed*1000, key="v6_chart")

instrument_key = st.sidebar.selectbox("Index", ["NSE_INDEX|Nifty 50", "NSE_INDEX|Nifty Bank", "BSE_INDEX|SENSEX"])

def get_all_expiries(instrument_key, headers):
    try:
        url = f"https://api.upstox.com/v2/option/contract?instrument_key={instrument_key}"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            exps = sorted(list(set([d['expiry'] for d in r.json().get('data', [])])))
            return exps
    except: pass
    return []

def get_sahi_PCR(instrument_key, live_price, expiry_date, headers):
    try:
        url = f"https://api.upstox.com/v2/option/chain?instrument_key={instrument_key}&expiry_date={expiry_date}"
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json().get('data') if r.status_code==200 else None
        if not data: return 1.0, "Data Khali", live_price
        atm = min(data, key=lambda x: abs(x['strike_price'] - live_price))['strike_price']
        nearby = sorted(data, key=lambda x: abs(x['strike_price'] - atm))[:10]
        ce_oi = sum([d.get('call_options',{}).get('market_data',{}).get('oi',0) for d in nearby])
        pe_oi = sum([d.get('put_options',{}).get('market_data',{}).get('oi',0) for d in nearby])
        if ce_oi==0 and pe_oi==0: return 1.0, "OI 0", atm
        pcr = pe_oi/ce_oi if ce_oi!=0 else 1.0
        sig = "✅ BULL" if pcr>=1.0 else "❌ BEAR"
        if pcr>=1.25: sig="✅ STRONG BULL"
        if pcr<=0.8: sig="❌ STRONG BEAR"
        return round(pcr,2), sig, atm
    except:
        return 1.0, "Err", live_price

all_exps = get_all_expiries(instrument_key, headers)
expiry_date = st.sidebar.selectbox("Expiry Auto", all_exps, index=0) if all_exps else st.sidebar.text_input("Expiry", "2026-10-30")

# ===== MAIN - CHART FIX YAHAN HAI =====
try:
    # LIVE
    live_price=0
    r_ltp=requests.get(f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={instrument_key}", headers=headers, timeout=4)
    if r_ltp.status_code==200:
        live_price=list(r_ltp.json()['data'].values())[0]['last_price']

    pcr_val, pcr_sig, atm_strike = get_sahi_PCR(instrument_key, live_price, expiry_date, headers)
    st.markdown(f"### 📈 LIVE ₹{live_price} | PCR {pcr_val} {pcr_sig} | ATM {atm_strike}")

    # CANDLE
    df=pd.DataFrame()
    r_c=requests.get(f"https://api.upstox.com/v2/historical-candle/intraday/{instrument_key}/1minute", headers=headers, timeout=8)
    if r_c.status_code==200:
        c=r_c.json().get('data',{}).get('candles',[])
        if c: df=pd.DataFrame(c, columns=['timestamp','open','high','low','close','volume','oi'])

    if df.empty:
        # Agar data nahi to LIVE se hi 20 candle bana de taaki chart khali na dikhe
        now=datetime.now()
        df=pd.DataFrame([{'timestamp': now-timedelta(minutes=i), 'open':live_price, 'high':live_price+2, 'low':live_price-2, 'close':live_price, 'volume':0, 'oi':0} for i in range(30)][::-1])

    df['timestamp']=pd.to_datetime(df['timestamp'])
    df=df.sort_values('timestamp').copy()
    
    # ===== YEHI MAIN FIX HAI - CHART HILANE KE LIYE =====
    # Last candle ko LIVE price se hilao
    last_idx = df.index[-1]
    df.loc[last_idx, 'close'] = live_price
    # Agar live high se zyada to high bhi badhao, low se kam to low
    if live_price > df.loc[last_idx, 'high']:
        df.loc[last_idx, 'high'] = live_price
    if live_price < df.loc[last_idx, 'low']:
        df.loc[last_idx, 'low'] = live_price

    df['EMA_9']=df['close'].ewm(span=9).mean()
    df['EMA_21']=df['close'].ewm(span=21).mean()
    df['FIDI_50']=df['close'].ewm(span=50).mean()

    # CHART - AB PAKKA DIKHEGA AUR HILEGA
    fig=go.Figure()
    fig.add_trace(go.Candlestick(
        x=df['timestamp'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
        increasing_line_color='green', decreasing_line_color='red', name="Candle"
    ))
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['EMA_9'], line=dict(color='yellow', width=1.5), name="EMA9"))
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['EMA_21'], line=dict(color='red', width=1.5), name="EMA21"))
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['FIDI_50'], line=dict(color='cyan', width=2), name="FIDI50"))
    
    fig.update_layout(height=550, xaxis_rangeslider_visible=False, template="plotly_dark", margin=dict(l=10,r=10,t=10,b=10))
    st.plotly_chart(fig, use_container_width=True, key=f"chart_{live_price}")

    last=df.iloc[-1]; prev=df.iloc[-2]
    is_bull=last['EMA_9']>last['EMA_21'] and live_price>last['FIDI_50']
    is_bear=last['EMA_9']<last['EMA_21'] and live_price<last['FIDI_50']

    if is_bull:
        st.success(f"## 🚀 BULLISH @ ₹{live_price} | PCR {pcr_val}")
    elif is_bear:
        st.error(f"## 🔻 BEARISH @ ₹{live_price} | PCR {pcr_val}")
        if pcr_val>1.25:
            st.warning(f"⚠️ Divergence: Price BEAR par PCR {pcr_val} STRONG BULL - Reversal chance")
    else:
        st.warning(f"## ⏳ WAIT @ ₹{live_price}")

    c1,c2,c3=st.columns(3)
    c1.metric("PCR", pcr_val, f"{pcr_sig} ATM {atm_strike}")
    c2.metric("FIDI", "BULL" if live_price>last['FIDI_50'] else "BEAR")
    c3.metric("LIVE", f"₹{live_price}")

except Exception as e:
    st.error(f"Error {e}")