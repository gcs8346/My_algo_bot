import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="TOWER No.1 - SMART MONEY", layout="wide")
st.title("🏰 TOWER No.1 - SMART MONEY EDITION")

# --- TOKEN ---
upstox_token = st.sidebar.text_input("Upstox Access Token", type="password")
final_label = st.sidebar.selectbox("Stock/Index", ["Nifty 50","Bank Nifty","RELIANCE","TCS"])
keys = {"Nifty 50":"NSE_INDEX|Nifty 50","Bank Nifty":"NSE_INDEX|Nifty Bank","RELIANCE":"NSE_EQ|INE002A01018","TCS":"NSE_EQ|INE467B01029"}
final_key_fixed = keys[final_label]

def get_candles(token, instrument, interval, hist_interval):
    headers = {"Authorization": f"Bearer {token}", "Accept":"application/json"}
    try:
        url = f"https://api.upstox.com/v2/historical-candle/intraday/{instrument}/{interval}"
        r = requests.get(url, headers=headers, timeout=10).json()
        if r.get('status')=='success' and r['data'].get('candles'):
            df = pd.DataFrame(r['data']['candles'], columns=['Timestamp','Open','High','Low','Close','Volume','OI'])
            df['Timestamp']=pd.to_datetime(df['Timestamp']); df.set_index('Timestamp', inplace=True); df.sort_index(inplace=True)
            return df, "intraday"
    except: pass
    try:
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now()-timedelta(days=60)).strftime("%Y-%m-%d")
        url = f"https://api.upstox.com/v2/historical-candle/{instrument}/{hist_interval}/{to_date}/{from_date}"
        r = requests.get(url, headers=headers, timeout=10).json()
        if r.get('status')=='success' and r['data'].get('candles'):
            df = pd.DataFrame(r['data']['candles'], columns=['Timestamp','Open','High','Low','Close','Volume','OI'])
            df['Timestamp']=pd.to_datetime(df['Timestamp']); df.set_index('Timestamp', inplace=True); df.sort_index(inplace=True)
            return df, "historical"
    except Exception as e:
        st.error(f"Data error: {e}")
    return None, "none"

def calc_rsi(s, n=14):
    d=s.diff(); g=d.where(d>0,0).rolling(n).mean(); l=-d.where(d<0,0).rolling(n).mean()
    rs=g/l; return 100-(100/(1+rs))

def calc_supertrend(df, period=10, mult=3):
    hl2=(df['High']+df['Low'])/2
    atr=(df['High']-df['Low']).rolling(period).mean()
    up=hl2+mult*atr; low=hl2-mult*atr
    st_dir=np.where(df['Close']>up, True, False)
    return st_dir

def analyze_df(df):
    df['EMA9']=df['Close'].ewm(span=9).mean()
    df['EMA21']=df['Close'].ewm(span=21).mean()
    df['EMA50']=df['Close'].ewm(span=50).mean()
    df['RSI']=calc_rsi(df['Close'])
    df['VolSMA']=df['Volume'].rolling(20).mean()
    # VWAP
    df['Typical']=(df['High']+df['Low']+df['Close'])/3
    df['VWAP']=(df['Typical']*df['Volume']).cumsum()/df['Volume'].cumsum()
    
    # --- TECHNICAL 5 ---
    df['C1']=df['EMA9']>df['EMA21']
    df['C2']=df['Close']>df['EMA9']
    df['C3']=(df['RSI']>=55)&(df['RSI']<=80)
    df['C4']=calc_supertrend(df)
    df['C5']=df['Close']>df['EMA50']
    df['HEAT']=df[['C1','C2','C3','C4','C5']].sum(axis=1)

    # --- SMART MONEY LOGIC ---
    # Swing High/Low
    df['SwingHigh']=df['High'].rolling(5, center=True).max()==df['High']
    df['SwingLow']=df['Low'].rolling(5, center=True).min()==df['Low']
    last_high = df[df['SwingHigh']]['High'].iloc[-2] if len(df[df['SwingHigh']])>2 else df['High'].max()
    last_low = df[df['SwingLow']]['Low'].iloc[-2] if len(df[df['SwingLow']])>2 else df['Low'].min()

    # 1. BOS - Break of Structure
    df['SM1_BOS']=df['Close']>last_high
    # 2. CHOCH safe - Last low nahi toda
    df['SM2_CHOCH_SAFE']=df['Close']>last_low
    
    # 3. FVG Bullish - 3 candle gap
    fvg = []
    for i in range(len(df)):
        if i>2 and df['Low'].iloc[i] > df['High'].iloc[i-2]:
            fvg.append(True)
        else:
            fvg.append(False)
    df['SM3_FVG']=fvg
    df['SM3_FVG'] = df['SM3_FVG'].rolling(10).max().astype(bool) # last 10 me koi FVG hai

    # 4. VWAP ke upar = Institutional buying
    df['SM4_VWAP']=df['Close']>df['VWAP']
    
    # 5. Smart Volume + Order Block proxy
    df['SM5_VOL']=df['Volume']>df['VolSMA']*1.2
    
    df['SM_HEAT']=df[['SM1_BOS','SM2_CHOCH_SAFE','SM3_FVG','SM4_VWAP','SM5_VOL']].sum(axis=1)
    
    # Liquidity Grab (Hammer at bottom)
    df['Body']=abs(df['Close']-df['Open'])
    df['LowerWick']=df[['Open','Close']].min(axis=1)-df['Low']
    df['LIQ_GRAB']=(df['LowerWick']>df['Body']*2) & (df['SwingLow'])

    # Premium/Discount
    day_high=df['High'].tail(1).max(); day_low=df['Low'].tail(1).min()
    df['DiscountZone']=df['Close']<(day_low+(day_high-day_low)*0.5)

    # Total Tower 10/10
    df['TOTAL_TOWER']=df['HEAT']+df['SM_HEAT']
    return df

# --- LIVE ---
timeframe_ui = st.selectbox("Timeframe", ["1minute","5minute","15minute","30minute"], index=2)
if st.button("🚀 TOWER CHECK KAR", type="primary", use_container_width=True):
    df,_ = get_candles(upstox_token, final_key_fixed, timeframe_ui, "30minute")
    if df is not None:
        df=analyze_df(df)
        last=df.iloc[-1]
        c1,c2,c3=st.columns(3)
        c1.metric("Technical Tower", f"{int(last['HEAT'])}/5")
        c2.metric("Smart Money Tower", f"{int(last['SM_HEAT'])}/5")
        c3.metric("TOTAL TOWER", f"{int(last['TOTAL_TOWER'])}/10", delta="FULL TOWER READY" if last['TOTAL_TOWER']==10 else "")
        
        st.divider()
        st.subheader(f"📍 {final_label} Smart Report")
        st.write(f"**BOS Break:** {'✅ High Toda' if last['SM1_BOS'] else '❌'} | **CHOCH Safe:** {'✅ Low Safe' if last['SM2_CHOCH_SAFE'] else '❌ Breakdown'} | **FVG:** {'✅ Gap Hai' if last['SM3_FVG'] else '❌'} | **VWAP:** {'✅ Upar' if last['SM4_VWAP'] else '❌ Neeche'} | **Volume:** {'✅ Smart Vol' if last['SM5_VOL'] else '❌'}")
        st.write(f"**Liquidity Grab:** {'🔨 Hammer bana - Bada buyer aaya' if last['LIQ_GRAB'] else 'Normal'} | **Zone:** {'💰 DISCOUNT - Saste me' if last['DiscountZone'] else '💎 PREMIUM - Mehenga'}")

        if last['TOTAL_TOWER']>=9:
            st.success(f"🔥 TOPU No.1 -  {final_label} me 10/10 TOWER BAN GAYA! Smart Money bhi yahi kharid raha hai!")
        elif last['TOTAL_TOWER']>=7:
            st.warning(f"⚡ {final_label} me {int(last['TOTAL_TOWER'])}/10 - Half Tower, Nazar rakho")
        else:
            st.info(f"💤 {final_label} me Tower thanda hai {int(last['TOTAL_TOWER'])}/10")

        st.dataframe(df[['Close','HEAT','SM_HEAT','TOTAL_TOWER','RSI','VWAP']].tail(15), use_container_width=True)

# --- BACKTEST V39 ---
st.divider()
if st.button("🔍 60 DIN KA SMART BACKTEST", use_container_width=True):
    df_bt,_ = get_candles(upstox_token, final_key_fixed, "30minute", "30minute")
    if df_bt is not None:
        df_bt=analyze_df(df_bt)
        trades=[]
        for i in range(30, len(df_bt)-5):
            if df_bt['TOTAL_TOWER'].iloc[i]>=8 and df_bt['TOTAL_TOWER'].iloc[i-1]<8:
                entry=df_bt['Close'].iloc[i]; future=df_bt['Close'].iloc[i+5]
                pnl=(future-entry)/entry*100
                trades.append({"Date":str(df_bt.index[i]),"Tower":f"{int(df_bt['TOTAL_TOWER'].iloc[i])}/10","Entry":round(entry,2),"PnL %":round(pnl,2),"Result":"✅ WIN" if pnl>0.2 else "❌"})
        if trades:
            dft=pd.DataFrame(trades)
            st.metric("Total Smart Tower Signals", len(dft))
            st.metric("Win Rate", f"{len(dft[dft['Result']=='✅ WIN'])/len(dft)*100:.1f}%")
            st.dataframe(dft.tail(20), use_container_width=True)
        else:
            st.warning("60 din me 8/10 bhi nahi bana - Stock poora range me tha")