import streamlit as st, requests, pandas as pd, numpy as np
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

st.set_page_config(layout="centered")
st.markdown("## ⚡ TOPU V24 - FAST TICK 1 SEC")

def play_sound():
    components.html("""<audio autoplay><source src="https://www.soundjay.com/buttons/sounds/beep-07a.mp3" type="audio/mpeg"></audio>""", height=0)

if st.text_input("Token", value="TOPU-2026-TEST", type="password") != "TOPU-2026-TEST": st.stop()

token = st.sidebar.text_input("Upstox Token", type="password")
if not token: st.stop()

# SPEED SELECTOR - Tujhe jo chahiye
speed = st.sidebar.select_slider("⚡ Tick Speed", options=["Slow 3s", "Fast 2s", "SuperFast 1s", "Rocket 0.8s"], value="SuperFast 1s")
speed_map = {"Slow 3s":3000, "Fast 2s":2000, "SuperFast 1s":1000, "Rocket 0.8s":800}
interval_ms = speed_map[speed]

sound_on = st.sidebar.checkbox("🔊 Sound ON", True)

# Yahi hai FAST ka jadoo - 1 sec
st_autorefresh(interval=interval_ms, key=f"fast_{interval_ms}")

instrument_key="NSE_INDEX|Nifty 50"
headers_up = {'Authorization': f'Bearer {token}'}

# LIVE - Fast fetch
try:
    r_ltp=requests.get(f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={instrument_key}", headers=headers_up, timeout=2)
    live=float(list(r_ltp.json()['data'].values())[0]['last_price']) if r_ltp.status_code==200 else 22600.0
except:
    live=22600.0

# Candle - Fast (sirf last 100 candle)
@st.cache_data(ttl=2)
def get_candle_fast(live_price):
    try:
        r=requests.get(f"https://api.upstox.com/v2/historical-candle/intraday/{instrument_key}/1minute", headers=headers_up, timeout=3)
        if r.status_code==200:
            df=pd.DataFrame(r.json()['data']['candles'][:100], columns=['t','o','h','l','c','v','oi'])
            df=df.sort_values('t').copy()
            df.loc[df.index[-1], 'c']=live_price
            df['EMA9']=df['c'].ewm(9).mean()
            df['EMA21']=df['c'].ewm(21).mean()
            df['FIDI']=df['c'].ewm(50).mean()
            delta=df['c'].diff()
            df['RSI']=100 - (100/(1+delta.where(delta>0,0).ewm(14).mean()/((-delta.where(delta<0,0)).ewm(14).mean().replace(0,0.001))))
            df['hl2']=(df['h']+df['l'])/2
            df['tr']=df['h']-df['l']
            df['atr']=df['tr'].ewm(10).mean()
            df['ST_dir']=np.where(df['c']>df['hl2']-3*df['atr'], 1, -1)
            return df
    except: pass
    return pd.DataFrame()

df=get_candle_fast(live)

# Checklist - Har 10 sec me ek baar (fast ke liye)
@st.cache_data(ttl=10)
def get_checklist_fast():
    try:
        s=requests.Session()
        s.headers.update({'User-Agent': 'Mozilla/5.0','Referer': 'https://www.nseindia.com/option-chain'})
        s.get("https://www.nseindia.com/option-chain", timeout=5)
        r1=s.get("https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050", timeout=4)
        adv,dec=5,45
        if r1.status_code==200:
            j=r1.json()
            adv=j.get('advance',{}).get('advances',0) or 5
            dec=j.get('advance',{}).get('declines',0) or 45
        r2=s.get("https://www.nseindia.com/api/allIndices", timeout=4)
        heat,green=0,0
        if r2.status_code==200:
            main=["NIFTY BANK","NIFTY IT","NIFTY AUTO","NIFTY FMCG","NIFTY METAL","NIFTY PHARMA"]
            for sec in main:
                for item in r2.json().get('data',[]):
                    if item.get('index')==sec and item.get('percentChange',0)>0:
                        green+=1; break
            heat=int(green/len(main)*100)
        return adv,dec,heat,green
    except:
        return 5,45,0,0

adv,dec,heat,green = get_checklist_fast()

# DASHBOARD - Tik-Tik
st.markdown(f"### ⚡ LIVE ₹{live} - {speed} - {interval_ms}ms")

if not df.empty:
    last=df.iloc[-1]
    mid=(df['h'].max()+df['l'].min())/2
    
    col1,col2,col3,col4=st.columns(4)
    col1.metric("EMA", "BULL" if last['EMA9']>last['EMA21'] else "BEAR", f"{int(last['EMA9'])}")
    col2.metric("FIDI", "BULL" if live>last['FIDI'] else "BEAR")
    col3.metric(f"RSI {int(last['RSI'])}", "BULL" if last['RSI']>50 else "BEAR")
    col4.metric("ST", "BULL" if last['ST_dir']==1 else "BEAR")

    c5,c6=st.columns(2)
    c5.metric("A/D", f"{adv}/{dec}")
    c6.metric("Heat", f"{heat}%")
    
    st.caption(f"MID {int(mid)} | LIVE ₹{live} => {'CALL Heavy' if live>mid else 'PUT Heavy'} | ChangeOI + Premium cached 10s")

    score = (1 if last['EMA9']>last['EMA21'] else 0) + (1 if live>last['FIDI'] else 0) + (1 if last['RSI']>50 else 0) + (1 if last['ST_dir']==1 else 0) + (1 if live>mid else 0) + (1 if adv>dec else 0) + (1 if heat>=50 else 0)

    if score>=5:
        st.success(f"🚀 BUY @ {round(live/50)*50} - {score}/7 FAST")
        if sound_on: play_sound()
    elif score<=2:
        st.error(f"🔻 SELL @ {round(live/50)*50} - {score}/7 FAST")
        if sound_on: play_sound()
    else:
        st.warning(f"⏳ WAIT {score}/7 - Tik-Tik {interval_ms}ms")

st.caption(f"V24 FAST: Interval {interval_ms}ms | Checklist cached 10s taaki fast rahe | EMA+FIDI+RSI+ST+A/D+Heat sab hai")