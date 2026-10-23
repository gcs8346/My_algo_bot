import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
from datetime import datetime, timedelta

st.set_page_config(page_title="TOPU TOWER FINAL", layout="wide")

# ===== LICENSE =====
LICENSE = "TOPU-2026-TEST"
st.markdown("## 👑 TOPU TOWER - FINAL COMPLETE")
lic = st.text_input("🔑 Yearly Token", value="TOPU-2026-TEST")
if lic != LICENSE:
    st.error("❌ Token Galat"); st.stop()

# ===== SIDEBAR - SETTINGS =====
st.sidebar.title("🔴 UPSTOX DIRECT")
upstox_token = st.sidebar.text_input("Upstox Token (Roz Naya)", type="password")
if not upstox_token:
    st.warning("Bhai Upstox Token daal"); st.stop()
headers = {'Authorization': f'Bearer {upstox_token}', 'Accept': 'application/json'}

sound_on = st.sidebar.checkbox("🔊 Sound ON", value=True)
refresh_speed = st.sidebar.select_slider("Refresh Speed", options=[1,2,3,5], value=1, format_func=lambda x: f"{x} Sec")
st_autorefresh(interval=refresh_speed*1000, key="final_1sec")

instrument_type = st.sidebar.radio("KISME TRADE?", ["INDEX", "STOCK"], index=0)
if instrument_type == "INDEX":
    instrument_key = st.sidebar.selectbox("Index Chuno", ["NSE_INDEX|Nifty 50", "NSE_INDEX|Nifty Bank", "BSE_INDEX|SENSEX"])
else:
    s = st.sidebar.text_input("Stock Symbol", "RELIANCE").upper()
    instrument_key = f"NSE_EQ|{s}"

# ===== EXPIRY AUTO FIX - AB DATA KHALI NAHI AYEGA =====
def get_all_expiries(instrument_key, headers):
    try:
        url = f"https://api.upstox.com/v2/option/contract?instrument_key={instrument_key}"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json().get('data', [])
            exps = sorted(list(set([d['expiry'] for d in data])))
            return exps
    except:
        pass
    return []

def get_sahi_PCR(instrument_key, live_price, expiry_date, headers):
    if "INDEX" not in instrument_key or live_price==0:
        return 1.0, "PCR Index me hi"
    try:
        url = f"https://api.upstox.com/v2/option/chain?instrument_key={instrument_key}&expiry_date={expiry_date}"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return 1.0, f"API {r.status_code}"
        data = r.json().get('data')
        if not data:
            return 1.0, "Data Khali - Market Band"
        atm = min(data, key=lambda x: abs(x['strike_price'] - live_price))['strike_price']
        nearby = sorted(data, key=lambda x: abs(x['strike_price'] - atm))[:10]
        ce_oi = sum([d.get('call_options',{}).get('market_data',{}).get('oi',0) for d in nearby])
        pe_oi = sum([d.get('put_options',{}).get('market_data',{}).get('oi',0) for d in nearby])
        if ce_oi==0 and pe_oi==0:
            return 1.0, "OI 0 - Raat ko band"
        if ce_oi==0:
            return 1.0, "CE 0"
        pcr = pe_oi/ce_oi
        if pcr>=1.25: sig="✅ STRONG BULL"
        elif pcr>=1.0: sig="✅ BULL"
        elif pcr<=0.8: sig="❌ STRONG BEAR"
        else: sig="❌ BEAR"
        return round(pcr,2), f"{sig} | ATM {atm}"
    except Exception as e:
        return 1.0, f"Err {e}"

all_exps = get_all_expiries(instrument_key, headers)
if all_exps:
    expiry_date = st.sidebar.selectbox("Sahi Expiry (Auto List)", all_exps, index=0)
    st.sidebar.caption(f"Selected: {expiry_date}")
else:
    expiry_date = st.sidebar.text_input("Expiry YYYY-MM-DD", value="2026-10-30")

def play_alarm(t):
    html=f"""<audio autoplay><source src="https://www.soundjay.com/buttons/sounds/beep-07a.mp3"></audio>
    <div style="background:red;padding:10px;border-radius:10px;"><h2 style="color:white;text-align:center;margin:0;">🔊 {t} 🔊</h2></div>"""
    components.html(html,height=110)

if 'last_candle' not in st.session_state:
    st.session_state.last_candle=None

# ===== MAIN =====
try:
    # LIVE PRICE - 1 SEC PE
    live_price=0
    try:
        r_ltp=requests.get(f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={instrument_key}", headers=headers, timeout=4)
        if r_ltp.status_code==200:
            live_price=list(r_ltp.json()['data'].values())[0]['last_price']
    except:
        pass

    # CANDLE - MARKET BAND FIX
    df=pd.DataFrame()
    try:
        r_c=requests.get(f"https://api.upstox.com/v2/historical-candle/intraday/{instrument_key}/1minute", headers=headers, timeout=8)
        if r_c.status_code==200:
            candles=r_c.json().get('data',{}).get('candles',[])
            if candles:
                df=pd.DataFrame(candles, columns=['timestamp','open','high','low','close','volume','oi'])
    except:
        pass

    if df.empty or len(df)<25:
        to_d=datetime.today().strftime('%Y-%m-%d')
        from_d=(datetime.today()-timedelta(days=7)).strftime('%Y-%m-%d')
        try:
            r2=requests.get(f"https://api.upstox.com/v2/historical-candle/{instrument_key}/day/{to_d}/{from_d}", headers=headers, timeout=8)
            if r2.status_code==200 and r2.json().get('data',{}).get('candles'):
                df=pd.DataFrame(r2.json()['data']['candles'], columns=['timestamp','open','high','low','close','volume','oi'])
        except:
            pass

    if df.empty:
        st.metric("LIVE PRICE", f"₹{live_price}")
        st.warning("🔴 Market Band Hai - Kal 9:15 pe 1 Sec wala live chalega")
        st.stop()

    df['timestamp']=pd.to_datetime(df['timestamp'])
    df=df.sort_values('timestamp')
    df['EMA_9']=df['close'].ewm(span=9).mean()
    df['EMA_21']=df['close'].ewm(span=21).mean()
    df['FIDI_50']=df['close'].ewm(span=50).mean()

    pcr_val, pcr_txt = get_sahi_PCR(instrument_key, live_price, expiry_date, headers)
    st.markdown(f"### 📈 {instrument_key} | LIVE ₹{live_price} | PCR {pcr_val} {pcr_txt} | Refresh {refresh_speed} Sec")

    fig=go.Figure(data=[
        go.Candlestick(x=df['timestamp'], open=df['open'], high=df['high'], low=df['low'], close=df['close']),
        go.Scatter(x=df['timestamp'], y=df['EMA_9'], line=dict(color='yellow'), name="EMA9"),
        go.Scatter(x=df['timestamp'], y=df['EMA_21'], line=dict(color='red'), name="EMA21"),
        go.Scatter(x=df['timestamp'], y=df['FIDI_50'], line=dict(color='cyan'), name="FIDI50"),
    ])
    fig.update_layout(height=520, xaxis_rangeslider_visible=False, template="plotly_dark", margin=dict(l=10,r=10,t=10,b=10))
    st.plotly_chart(fig, use_container_width=True)

    last=df.iloc[-1]; prev=df.iloc[-2]
    is_bull=last['EMA_9']>last['EMA_21'] and last['close']>last['FIDI_50']
    is_bear=last['EMA_9']<last['EMA_21'] and last['close']<last['FIDI_50']
    cross_up=(prev['EMA_9']<=prev['EMA_21']) and (last['EMA_9']>last['EMA_21'])
    cross_down=(prev['EMA_9']>=prev['EMA_21']) and (last['EMA_9']<last['EMA_21'])

    curr=str(last['timestamp'])
    new=st.session_state.last_candle!=curr

    if cross_up and is_bull:
        st.success(f"## 🚀 FRESH BUY @ ₹{live_price}")
        if new and sound_on: play_alarm(f"BUY {instrument_key}"); st.session_state.last_candle=curr; st.balloons()
    elif is_bull:
        st.success(f"## 🚀 BULLISH TREND CONTINUES @ ₹{live_price}")
    elif cross_down and is_bear:
        st.error(f"## 🔻 FRESH SELL @ ₹{live_price}")
        if new and sound_on: play_alarm(f"SELL {instrument_key}"); st.session_state.last_candle=curr
    elif is_bear:
        st.error(f"## 🔻 BEARISH TREND CONTINUES @ ₹{live_price}")
    else:
        st.warning(f"## ⏳ WAIT @ ₹{live_price}")

    c1,c2,c3,c4=st.columns(4)
    c1.metric("FIDI 50","BULL" if last['close']>last['FIDI_50'] else "BEAR")
    c2.metric("EMA","BULL" if last['EMA_9']>last['EMA_21'] else "BEAR")
    c3.metric("PCR",pcr_val,pcr_txt)
    c4.metric("LIVE",f"₹{live_price}")

except Exception as e:
    st.error(f"Error: {e}")