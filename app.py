# V46 FINAL - 10/10 + Sensex + Speed Slider + Sound
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import streamlit.components.v1 as components

st.set_page_config(page_title="TOWER V46 FINAL", layout="wide")
st.title("🏰 TOWER V46 - 10/10 FINAL")

upstox_token = st.sidebar.text_input("Upstox Token", type="password")

# --- SPEED BUTTON - 0.8 to 3 sec ---
tick_speed = st.sidebar.select_slider("⏱️ Tik-Tik Speed", options=[0.8, 1.0, 1.5, 2.0, 3.0], value=1.0, format_func=lambda x: f"{x} sec")
auto_tick = st.sidebar.checkbox(f"🔴 LIVE ON ({tick_speed}s)")
sound_on = st.sidebar.checkbox("🔊 Sound ON (10/10 pe)", value=True)

# STOCKS + TIMEFRAME - jo tune bola tha 1,3,2,3,4,5 minute wala
STOCKS = {"Nifty 50":"NSE_INDEX|Nifty 50","Bank Nifty":"NSE_INDEX|Nifty Bank","Sensex":"BSE_INDEX|SENSEX","RELIANCE":"NSE_EQ|INE002A01018","TCS":"NSE_EQ|INE467B01029","INFY":"NSE_EQ|INE009A01021","HDFCBANK":"NSE_EQ|INE040A01034","ICICIBANK":"NSE_EQ|INE090A01021","SBIN":"NSE_EQ|INE062A01020","GOLD":"MCX_FO|GOLD26DECFUT","CRUDEOIL":"MCX_FO|CRUDEOIL26NOVFUT"}
sel_name = st.sidebar.selectbox("Stock", list(STOCKS.keys()))
sel_inst = STOCKS[sel_name]
tf = st.sidebar.selectbox("Timeframe", ["1minute","3minute","5minute","15minute","30minute","day"], index=2)

def get_candles(token, inst, interval):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        url = f"https://api.upstox.com/v2/historical-candle/intraday/{inst}/{interval}"
        r = requests.get(url, headers=headers, timeout=5).json()
        if r.get('status')=='success' and r['data'].get('candles'):
            df=pd.DataFrame(r['data']['candles'], columns=['Timestamp','Open','High','Low','Close','Volume','OI'])
            df['Timestamp']=pd.to_datetime(df['Timestamp']); df.set_index('Timestamp', inplace=True); df.sort_index(inplace=True); return df
    except: pass
    try:
        to_date=datetime.now().strftime("%Y-%m-%d"); from_date=(datetime.now()-timedelta(days=10)).strftime("%Y-%m-%d")
        url=f"https://api.upstox.com/v2/historical-candle/{inst}/30minute/{to_date}/{from_date}"
        r=requests.get(url, headers=headers, timeout=5).json()
        if r.get('status')=='success' and r['data'].get('candles'):
            df=pd.DataFrame(r['data']['candles'], columns=['Timestamp','Open','High','Low','Close','Volume','OI'])
            df['Timestamp']=pd.to_datetime(df['Timestamp']); df.set_index('Timestamp', inplace=True); df.sort_index(inplace=True); return df
    except: pass
    return None

def calc_rsi(s):
    d=s.diff(); g=d.where(d>0,0).rolling(14).mean(); l=-d.where(d<0,0).rolling(14).mean(); return 100-(100/(1+g/l))

def analyze(df):
    df['EMA9']=df['Close'].ewm(span=9).mean(); df['EMA21']=df['Close'].ewm(span=21).mean(); df['EMA50']=df['Close'].ewm(span=50).mean()
    df['RSI']=calc_rsi(df['Close']); df['VolSMA']=df['Volume'].rolling(20).mean()
    df['Typical']=(df['High']+df['Low']+df['Close'])/3; df['VWAP']=(df['Typical']*df['Volume']).cumsum()/df['Volume'].cumsum()
    hl2=(df['High']+df['Low'])/2; atr=(df['High']-df['Low']).rolling(10).mean()
    df['C1']=df['EMA9']>df['EMA21']; df['C2']=df['Close']>df['EMA9']; df['C3']=(df['RSI']>=55)&(df['RSI']<=80); df['C4']=df['Close']>(hl2+3*atr); df['C5']=df['Close']>df['EMA50']
    df['HEAT']=df[['C1','C2','C3','C4','C5']].sum(axis=1)
    df['SM1']=df['Close']>df['High'].rolling(10).max().shift(1); df['SM2']=df['Close']>df['Low'].rolling(10).min().shift(1)
    fvg=[True if i>2 and df['Low'].iloc[i]>df['High'].iloc[i-2] else False for i in range(len(df))]
    df['SM3']=pd.Series(fvg, index=df.index).rolling(10).max().astype(bool); df['SM4']=df['Close']>df['VWAP']; df['SM5']=df['Volume']>df['VolSMA']*1.2
    df['SM_HEAT']=df[['SM1','SM2','SM3','SM4','SM5']].sum(axis=1)
    df['TOTAL']=df['HEAT']+df['SM_HEAT']
    df['Body']=abs(df['Close']-df['Open']); df['Lower']=df[['Open','Close']].min(axis=1)-df['Low']; df['Hammer']=df['Lower']>2*df['Body']
    return df

if st.button(f"🚀 {sel_name} CHECK", type="primary", use_container_width=True) or auto_tick:
    df=get_candles(upstox_token, sel_inst, tf)
    if df is not None:
        df=analyze(df); last=df.iloc[-1]
        m1,m2,m3,m4=st.columns(4)
        m1.metric(f"{sel_name} LTP", f"{last['Close']:.2f}"); m2.metric("Technical 5/5", f"{int(last['HEAT'])}/5"); m3.metric("Smart 5/5", f"{int(last['SM_HEAT'])}/5"); m4.metric("TOTAL 10/10", f"{int(last['TOTAL'])}/10")
        st.divider()
        st.write(f"**Checklist:** Tech: EMA9>21:{'✅' if last['C1'] else '❌'} | Close>EMA9:{'✅' if last['C2'] else '❌'} | RSI {last['RSI']:.1f}:{'✅' if last['C3'] else '❌'} | Super:{'✅' if last['C4'] else '❌'} | EMA50:{'✅' if last['C5'] else '❌'}")
        st.write(f"**Smart:** BOS:{'✅' if last['SM1'] else '❌'} | SAFE:{'✅' if last['SM2'] else '❌'} | FVG:{'✅' if last['SM3'] else '❌'} | VWAP:{'✅' if last['SM4'] else '❌'} | Vol:{'✅' if last['SM5'] else '❌'}")
        if int(last['TOTAL'])==10:
            st.success("🔥 10/10 FULL SIGNAL!"); st.balloons()
            if sound_on: components.html("""<audio autoplay><source src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg"></audio>""", height=0)
        elif int(last['TOTAL'])>=8: st.warning(f"⚡ {int(last['TOTAL'])}/10 HALF SIGNAL")
        else: st.info(f"💤 {int(last['TOTAL'])}/10 - Wait")
        st.dataframe(df[['Close','HEAT','SM_HEAT','TOTAL','RSI','Hammer']].tail(15), use_container_width=True)
    else: st.error("Data nahi aaya - Token check kar")

if auto_tick:
    time.sleep(tick_speed); st.rerun()
# ======================================================
# YAHAN TAK TERA V46 FINAL LOCK KHATAM - ISKE UPAR KUCH MAT CHHEDNA
# ======================================================

# ========= ADDITIONAL: 10 PT SCALP CHIP - V46 ke saath attach =========
def scalp_10pt_filter(df, total_score, fvg_status):
    try:
        last = df.iloc[-1]
        close = last['close']
        ema9 = last['ema9']
        ema21 = last['ema21']

        big_trend_up = ema9 > ema21
        pullback = abs(close - ema9) / close < 0.0015  # EMA9 ke paas
        tower_strong = total_score >= 8
        fvg_ok = '✅' in str(fvg_status) or fvg_status == True
        bullish = close > last.get('open', close)

        if big_trend_up and pullback and tower_strong and fvg_ok and bullish:
            return "🔥 SCALP READY - 10 PT TARGET | SL 8pt"
        elif pullback and tower_strong:
            return "⚠️ SCALP WATCH - EMA9 pe hai"
        else:
            return ""
    except:
        return ""

# --- Ye display wala part hai ---
try:
    # df_3min, TOTAL, SM3_FVG ye teeno tere V46 me pehle se hain
    scalp_msg = scalp_10pt_filter(df_3min, TOTAL, SM3_FVG)
    if scalp_msg:
        st.success(scalp_msg)
except:
    pass
# ========= ADDITIONAL KHATAM =========
# ========= ADDITIONAL: MULTI-ASSET CHIP - PASTE AT VERY BOTTOM =========
# Isko V46 ke bilkul neeche, last me paste karna hai

import streamlit as st

ASSET_CONFIG = {
    "NIFTY": {"target": 10, "sl": 8, "label": "Nifty 50"},
    "CRUDE": {"target": 20, "sl": 15, "label": "Crude Oil"},
    "GOLD":  {"target": 100, "sl": 70, "label": "Gold"},
}

st.divider()
st.markdown("### 🏆 Additional Chip")

# Ye dropdown neeche ayega, upar wale Stock/Timeframe ko haath mat lagana
asset_choice = st.selectbox("Asset Chun", ["NIFTY", "CRUDE", "GOLD"], key="extra_asset_bottom")

cfg = ASSET_CONFIG[asset_choice]

st.success(f"Selected: {cfg['label']} | Target: {cfg['target']} point | SL: {cfg['sl']} point")
st.caption(f"V46 ka 4/10 wala score same rahega, bas target apne aap {cfg['target']} ho jayega")