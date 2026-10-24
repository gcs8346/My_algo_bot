import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="TOWER No.1 FINAL", layout="wide")
st.title("🏰 TOWER No.1 - FINAL COMBINED 10/10")

# --- TOKEN ---
upstox_token = st.sidebar.text_input("Upstox Access Token", type="password")

# --- PURA STOCKS LIST WAPAS ---
STOCKS = {
"Nifty 50":"NSE_INDEX|Nifty 50",
"Bank Nifty":"NSE_INDEX|Nifty Bank",
"RELIANCE":"NSE_EQ|INE002A01018",
"TCS":"NSE_EQ|INE467B01029",
"INFY":"NSE_EQ|INE009A01021",
"HDFCBANK":"NSE_EQ|INE040A01034",
"ICICIBANK":"NSE_EQ|INE090A01021",
"SBIN":"NSE_EQ|INE062A01020",
"BHARTIARTL":"NSE_EQ|INE397D01024",
"LT":"NSE_EQ|INE018A01030",
"ITC":"NSE_EQ|INE154A01025",
"BAJFINANCE":"NSE_EQ|INE296A01024",
"MARUTI":"NSE_EQ|INE585B01010",
"WIPRO":"NSE_EQ|INE075A01022",
"TATAMOTORS":"NSE_EQ|INE155A01022"
}
final_label = st.sidebar.selectbox("Stock Select Kar", list(STOCKS.keys()), index=2)
final_key_fixed = STOCKS[final_label]

# --- PURA MINUTE WALA WAPAS - 1,3,5,15,30 ---
timeframe_ui = st.sidebar.selectbox("Timeframe", ["1minute","3minute","5minute","15minute","30minute","day"], index=3)
hist_map = {"1minute":"1minute","3minute":"30minute","5minute":"30minute","15minute":"30minute","30minute":"30minute","day":"day"}
hist_interval = hist_map[timeframe_ui]

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

def analyze_df(df):
    df['EMA9']=df['Close'].ewm(span=9).mean()
    df['EMA21']=df['Close'].ewm(span=21).mean()
    df['EMA50']=df['Close'].ewm(span=50).mean()
    df['RSI']=calc_rsi(df['Close'])
    df['VolSMA']=df['Volume'].rolling(20).mean()
    df['Typical']=(df['High']+df['Low']+df['Close'])/3
    df['VWAP']=(df['Typical']*df['Volume']).cumsum()/df['Volume'].cumsum()
    # Technical 5
    df['C1']=df['EMA9']>df['EMA21']
    df['C2']=df['Close']>df['EMA9']
    df['C3']=(df['RSI']>=55)&(df['RSI']<=80)
    # Supertrend simple
    hl2=(df['High']+df['Low'])/2
    atr=(df['High']-df['Low']).rolling(10).mean()
    up=hl2+3*atr
    df['C4']=df['Close']>up
    df['C5']=df['Close']>df['EMA50']
    df['HEAT']=df[['C1','C2','C3','C4','C5']].sum(axis=1)

    # Smart Money 5
    df['SwingHigh']=df['High'].rolling(5, center=True).max()==df['High']
    df['SwingLow']=df['Low'].rolling(5, center=True).min()==df['Low']
    last_high = df[df['SwingHigh']]['High'].iloc[-2] if len(df[df['SwingHigh']])>2 else df['High'].max()
    last_low = df[df['SwingLow']]['Low'].iloc[-2] if len(df[df['SwingLow']])>2 else df['Low'].min()
    df['SM1_BOS']=df['Close']>last_high
    df['SM2_SAFE']=df['Close']>last_low
    fvg=[]
    for i in range(len(df)):
        if i>2 and df['Low'].iloc[i] > df['High'].iloc[i-2]: fvg.append(True)
        else: fvg.append(False)
    df['SM3_FVG']=pd.Series(fvg, index=df.index).rolling(10).max().astype(bool)
    df['SM4_VWAP']=df['Close']>df['VWAP']
    df['SM5_VOL']=df['Volume']>df['VolSMA']*1.2
    df['SM_HEAT']=df[['SM1_BOS','SM2_SAFE','SM3_FVG','SM4_VWAP','SM5_VOL']].sum(axis=1)
    
    # Extra
    df['Body']=abs(df['Close']-df['Open'])
    df['LowerWick']=df[['Open','Close']].min(axis=1)-df['Low']
    df['LIQ_GRAB']=(df['LowerWick']>df['Body']*2)
    df['TOTAL_TOWER']=df['HEAT']+df['SM_HEAT']
    
    # SIGNAL PURANA WALA WAPAS
    cond = []
    for i in range(len(df)):
        if i==0: cond.append(False)
        else:
            if df['TOTAL_TOWER'].iloc[i]>=8 and df['TOTAL_TOWER'].iloc[i-1]<8: cond.append(True)
            else: cond.append(False)
    df['SIGNAL']=cond
    return df

# --- LIVE BUTTON ---
if st.button("🚀 TOWER CHECK KAR - LIVE SIGNAL", type="primary", use_container_width=True):
    df,_ = get_candles(upstox_token, final_key_fixed, timeframe_ui, hist_interval)
    if df is not None:
        df=analyze_df(df)
        last=df.iloc[-1]
        c1,c2,c3,c4=st.columns(4)
        c1.metric("Technical 5/5", f"{int(last['HEAT'])}/5")
        c2.metric("Smart Money 5/5", f"{int(last['SM_HEAT'])}/5")
        c3.metric("TOTAL 10/10", f"{int(last['TOTAL_TOWER'])}/10")
        c4.metric("Price", f"{last['Close']:.2f}")

        st.divider()
        # SIGNAL WAPAS
        if last['TOTAL_TOWER']==10:
            st.success(f"🔥 FULL SIGNAL BUY - {final_label} {timeframe_ui} pe 10/10 TOWER BAN GAYA!")
        elif last['TOTAL_TOWER']>=8:
            st.warning(f"⚡ HALF SIGNAL - {final_label} me {int(last['TOTAL_TOWER'])}/10 bana hai - Nazar rakho")
        elif last['LIQ_GRAB']:
            st.info(f"🔨 LIQUIDITY GRAB - {final_label} me Hammer bana, bada buyer aaya")
        else:
            st.error(f"💤 NO SIGNAL - {int(last['TOTAL_TOWER'])}/10 - Thanda hai")

        st.subheader("📋 Checklist Wapas")
        st.write(f"Tech: EMA9>21:{'✅' if last['C1'] else '❌'} | Close>EMA9:{'✅' if last['C2'] else '❌'} | RSI:{last['RSI']:.1f} | Supertrend:{'✅' if last['C4'] else '❌'} | EMA50:{'✅' if last['C5'] else '❌'}")
        st.write(f"Smart: BOS:{'✅' if last['SM1_BOS'] else '❌'} | Safe:{'✅' if last['SM2_SAFE'] else '❌'} | FVG:{'✅' if last['SM3_FVG'] else '❌'} | VWAP:{'✅' if last['SM4_VWAP'] else '❌'} | Vol:{'✅' if last['SM5_VOL'] else '❌'}")

        st.dataframe(df[['Close','HEAT','SM_HEAT','TOTAL_TOWER','RSI','VWAP','Volume','SIGNAL']].tail(20), use_container_width=True)

# --- BACKTEST BUTTON WAPAS - RELAXED WALA ---
st.divider()
st.subheader("📊 BACKTEST - 60 Din")
if st.button("🔍 BACKTEST BUTTON DABA - PICHLA DATA", use_container_width=True):
    with st.spinner(f"{final_label} ka 60 din ka data nikal raha hu..."):
        df_bt,_ = get_candles(upstox_token, final_key_fixed, "30minute", "30minute")
        if df_bt is not None:
            df_bt=analyze_df(df_bt)
            trades=[]
            for i in range(20, len(df_bt)-5):
                curr=int(df_bt['TOTAL_TOWER'].iloc[i]); prev=int(df_bt['TOTAL_TOWER'].iloc[i-1])
                if curr>=8 and prev<8:
                    entry=df_bt['Close'].iloc[i]; future=df_bt['Close'].iloc[i+5]
                    pnl=(future-entry)/entry*100
                    tag=f"{curr}/10"
                    trades.append({"Date":str(df_bt.index[i]),"Tower":tag,"Entry":round(entry,2),"PnL %":round(pnl,2),"Result":"✅ WIN" if pnl>0.2 else "❌ LOSS"})
            if trades:
                dft=pd.DataFrame(trades)
                total=len(dft); wins=len(dft[dft['Result']=="✅ WIN"])
                m1,m2,m3=st.columns(3)
                m1.metric("Total Signals", total)
                m2.metric("WIN", wins)
                m3.metric("Win Rate", f"{wins/total*100:.1f}%")
                st.dataframe(dft.tail(20), use_container_width=True)
            else:
                st.warning(f"{final_label} me 60 din me 8/10 bhi nahi bana - pura thanda tha")
                st.dataframe(df_bt[['Close','TOTAL_TOWER']].tail(10), use_container_width=True)