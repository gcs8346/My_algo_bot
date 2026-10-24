import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import streamlit.components.v1 as components

st.set_page_config(page_title="TOWER V43 FINAL", layout="wide")
st.title("🏰 TOWER V43 - FINAL + REVERSAL")

# --- TIK-TIK + SUNSET ---
st.sidebar.markdown("### ⏰ LIVE TIK-TIK")
components.html("""
<div style="font-size:28px; font-weight:bold; color:#00FF00; background:black; text-align:center; padding:10px; border-radius:10px;" id="clock"></div>
<script>setInterval(()=>{let n=new Date().toLocaleTimeString('en-IN',{timeZone:'Asia/Kolkata',hour12:false});document.getElementById('clock').innerHTML=n;},1000);</script>
""", height=60)

now_ist = datetime.now()
close_t = now_ist.replace(hour=15, minute=30, second=0, microsecond=0)
if now_ist > close_t:
    st.sidebar.error("🌅 Market Sunset - Band")
else:
    diff = close_t - now_ist
    st.sidebar.warning(f"🌇 Sunset me: {str(diff).split('.')[0]}")

upstox_token = st.sidebar.text_input("Upstox Token", type="password")
auto_tick = st.sidebar.checkbox("🔴 Live Tick 3sec")

# STOCKS - SENSEX SAHIT
STOCKS = {
"Nifty 50":"NSE_INDEX|Nifty 50","Bank Nifty":"NSE_INDEX|Nifty Bank","Sensex":"BSE_INDEX|SENSEX",
"RELIANCE":"NSE_EQ|INE002A01018","TCS":"NSE_EQ|INE467B01029","INFY":"NSE_EQ|INE009A01021",
"HDFCBANK":"NSE_EQ|INE040A01034","ICICIBANK":"NSE_EQ|INE090A01021","SBIN":"NSE_EQ|INE062A01020",
"BHARTIARTL":"NSE_EQ|INE397D01024","LT":"NSE_EQ|INE018A01030","ITC":"NSE_EQ|INE154A01025",
"BAJFINANCE":"NSE_EQ|INE296A01024","MARUTI":"NSE_EQ|INE585B01010"
}
label = st.sidebar.selectbox("Stock", list(STOCKS.keys()), index=3)
inst = STOCKS[label]
tf = st.sidebar.selectbox("Timeframe", ["1minute","3minute","5minute","15minute","30minute","day"], index=3)
hist_map = {"1minute":"1minute","3minute":"30minute","5minute":"30minute","15minute":"30minute","30minute":"30minute","day":"day"}

def get_candles(token, instrument, interval, hist_interval):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        url = f"https://api.upstox.com/v2/historical-candle/intraday/{instrument}/{interval}"
        r = requests.get(url, headers=headers, timeout=10).json()
        if r.get('status')=='success' and r['data'].get('candles'):
            df = pd.DataFrame(r['data']['candles'], columns=['Timestamp','Open','High','Low','Close','Volume','OI'])
            df['Timestamp']=pd.to_datetime(df['Timestamp']); df.set_index('Timestamp', inplace=True); df.sort_index(inplace=True); return df
    except: pass
    try:
        to_date = datetime.now().strftime("%Y-%m-%d"); from_date = (datetime.now()-timedelta(days=60)).strftime("%Y-%m-%d")
        url = f"https://api.upstox.com/v2/historical-candle/{instrument}/{hist_interval}/{to_date}/{from_date}"
        r = requests.get(url, headers=headers, timeout=10).json()
        if r.get('status')=='success' and r['data'].get('candles'):
            df = pd.DataFrame(r['data']['candles'], columns=['Timestamp','Open','High','Low','Close','Volume','OI'])
            df['Timestamp']=pd.to_datetime(df['Timestamp']); df.set_index('Timestamp', inplace=True); df.sort_index(inplace=True); return df
    except: pass
    return None

def calc_rsi(s, n=14):
    d=s.diff(); g=d.where(d>0,0).rolling(n).mean(); l=-d.where(d<0,0).rolling(n).mean(); return 100-(100/(1+g/l))

def analyze(df):
    df['EMA9']=df['Close'].ewm(span=9).mean(); df['EMA21']=df['Close'].ewm(span=21).mean(); df['EMA50']=df['Close'].ewm(span=50).mean()
    df['RSI']=calc_rsi(df['Close']); df['VolSMA']=df['Volume'].rolling(20).mean()
    df['Typical']=(df['High']+df['Low']+df['Close'])/3; df['VWAP']=(df['Typical']*df['Volume']).cumsum()/df['Volume'].cumsum()
    # --- TOWER 10/10 ---
    hl2=(df['High']+df['Low'])/2; atr=(df['High']-df['Low']).rolling(10).mean()
    df['C1']=df['EMA9']>df['EMA21']; df['C2']=df['Close']>df['EMA9']; df['C3']=(df['RSI']>=55)&(df['RSI']<=80); df['C4']=df['Close']>(hl2+3*atr); df['C5']=df['Close']>df['EMA50']
    df['HEAT']=df[['C1','C2','C3','C4','C5']].sum(axis=1)
    df['SwingHigh']=df['High'].rolling(5, center=True).max()==df['High']; df['SwingLow']=df['Low'].rolling(5, center=True).min()==df['Low']
    df['SM1']=df['Close']>df['High'].rolling(10).max().shift(1); df['SM2']=df['Close']>df['Low'].rolling(10).min().shift(1)
    fvg=[True if i>2 and df['Low'].iloc[i]>df['High'].iloc[i-2] else False for i in range(len(df))]
    df['SM3']=pd.Series(fvg, index=df.index).rolling(10).max().astype(bool); df['SM4']=df['Close']>df['VWAP']; df['SM5']=df['Volume']>df['VolSMA']*1.2
    df['SM_HEAT']=df[['SM1','SM2','SM3','SM4','SM5']].sum(axis=1)
    df['TOTAL']=df['HEAT']+df['SM_HEAT']
    
    # --- CANDLE TOP/BOTTOM REVERSAL - NAYA ---
    df['Body']=abs(df['Close']-df['Open']); df['Range']=df['High']-df['Low']
    df['UpperWick']=df['High']-df[['Open','Close']].max(axis=1)
    df['LowerWick']=df[['Open','Close']].min(axis=1)-df['Low']
    df['UpTrend']=df['Close']>df['EMA50']; df['DownTrend']=df['Close']<df['EMA50']
    df['Hammer']=(df['LowerWick']>2*df['Body']) & (df['UpperWick']<df['Body']*0.8) & (df['Range']>0)
    df['ShootingStar']=(df['UpperWick']>2*df['Body']) & (df['LowerWick']<df['Body']*0.8) & (df['Range']>0)
    df['BullEngulf']=(df['Close']>df['Open']) & (df['Close'].shift(1)<df['Open'].shift(1)) & (df['Close']>=df['Open'].shift(1)) & (df['Open']<=df['Close'].shift(1))
    df['BearEngulf']=(df['Close']<df['Open']) & (df['Close'].shift(1)>df['Open'].shift(1)) & (df['Close']<=df['Open'].shift(1)) & (df['Open']>=df['Close'].shift(1))
    df['Doji']=(df['Body']<=df['Range']*0.15)
    df['BOTTOM_REV']=df['Hammer'] | df['BullEngulf'] | (df['Doji'] & df['DownTrend'])
    df['TOP_REV']=df['ShootingStar'] | df['BearEngulf'] | (df['Doji'] & df['UpTrend'])
    return df

if st.button("🚀 TOWER CHECK + REVERSAL", type="primary", use_container_width=True):
    df = get_candles(upstox_token, inst, tf, hist_map[tf])
    if df is not None:
        df=analyze(df); last=df.iloc[-1]
        c1,c2,c3,c4=st.columns(4)
        c1.metric("LTP", f"{last['Close']:.2f}"); c2.metric("Technical", f"{int(last['HEAT'])}/5"); c3.metric("Smart", f"{int(last['SM_HEAT'])}/5"); c4.metric("TOTAL", f"{int(last['TOTAL'])}/10")
        st.divider()
        # REVERSAL SIGNAL
        if last['BOTTOM_REV']:
            st.success(f"🟢 BOTTOM REVERSAL - {label} neeche se palat raha hai! Hammer/Bullish Engulfing bana hai")
            if int(last['TOTAL'])>=7:
                st.success(f"🔥 CONFIRMED BOTTOM - Tower {int(last['TOTAL'])}/10 + Bottom Reversal = STRONG BUY")
                components.html("""<audio autoplay><source src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg"></audio>""", height=0); st.balloons()
        elif last['TOP_REV']:
            st.error(f"🔴 TOP REVERSAL - {label} upar se girega! Shooting Star/Bearish Engulfing bana hai")
            if int(last['TOTAL'])<=3:
                st.error(f"💥 CONFIRMED TOP - Tower {int(last['TOTAL'])}/10 + Top Reversal = STRONG SELL")
        else:
            st.info("➡️ No Candle Reversal - Sidha trend chal raha hai")

        if int(last['TOTAL'])==10:
            st.success(f"🏰 10/10 TOWER - FULL SIGNAL"); st.balloons()
        st.dataframe(df[['Close','TOTAL','RSI','BOTTOM_REV','TOP_REV','Hammer','ShootingStar','BullEngulf','BearEngulf']].tail(20), use_container_width=True)
    else:
        st.error("Data nahi aaya, token check kar")

if auto_tick:
    time.sleep(3); st.rerun()

if st.button("🔍 BACKTEST 60 DIN"):
    df=get_candles(upstox_token, inst, "30minute", "30minute")
    if df is not None:
        df=analyze(df); trades=[]
        for i in range(20,len(df)-5):
            if int(df['TOTAL'].iloc[i])>=8 and int(df['TOTAL'].iloc[i-1])<8 and df['BOTTOM_REV'].iloc[i]:
                entry=df['Close'].iloc[i]; future=df['Close'].iloc[i+5]; pnl=(future-entry)/entry*100
                trades.append({"Date":str(df.index[i]),"Type":"BOTTOM+TOWER","PnL":round(pnl,2)})
        if trades:
            st.dataframe(pd.DataFrame(trades).tail(20))
        else:
            st.warning("60 din me Bottom+Tower combo nahi bana")