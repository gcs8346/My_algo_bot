import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from urllib.parse import quote
from datetime import datetime, timedelta
import time

st.set_page_config(layout="wide", page_title="Topu V33 NIGHT LOCK")
st.title("🔥 Topu V33 NIGHT LOCK - Raat Wala Final")

# ===== SIDEBAR =====
st.sidebar.header("🔑 UPSTOX TOKEN BOX")
upstox_token = st.sidebar.text_input("Upstox Access Token", type="password")
is_token = len(upstox_token.strip()) > 30 if upstox_token else False
st.sidebar.write("🟢 TOKEN ON - Pure Token Mode" if is_token else "🔴 TOKEN DALO")

st.sidebar.header("🔊 SOUND BOX V17")
enable_sound = st.sidebar.checkbox("Sound ON", True)
sound_entry = "https://cdn.pixabay.com/audio/2022/03/24/audio_1b9bd41700.mp3"
sound_exit = "https://cdn.pixabay.com/audio/2022/03/10/audio_c3c8a6faa7.mp3"

upstox_map = {
    "NIFTY 50": "NSE_INDEX|Nifty 50",
    "BANK NIFTY": "NSE_INDEX|Nifty Bank",
    "FIN NIFTY": "NSE_INDEX|Nifty Fin Service",
    "SENSEX": "BSE_INDEX|SENSEX",
    "NIFTY IT": "NSE_INDEX|Nifty IT",
    "MIDCAP": "NSE_INDEX|Nifty Mid Select"
}
selected = st.sidebar.selectbox("Index", list(upstox_map.keys()))
custom = st.sidebar.text_input("Stock Likh (RELIANCE)", "").strip().upper()
timeframe_ui = st.sidebar.selectbox("Timeframe", ["1minute","5minute","15minute","30minute","day"], index=2)
auto_tick = st.sidebar.checkbox("TICK TICK ON (5 sec)", True)

historical_map = {"1minute":"1minute","5minute":"1minute","15minute":"30minute","30minute":"30minute","day":"day"}

if not is_token:
    st.error("Topu No.1, Token dalo. Ye pure token wala hai, yfinance nahi hai.")
    st.stop()

def ema(s,n): return s.ewm(span=n, adjust=False).mean()
def rsi(s,n=14):
    d=s.diff(); g=d.where(d>0,0).rolling(n).mean(); l=-d.where(d<0,0).rolling(n).mean()
    rs = g/l; return 100-(100/(1+rs))
def supertrend_bull(df, p=10, m=3):
    hl2=(df['High']+df['Low'])/2; atr=(df['High']-df['Low']).rolling(p).mean()
    return df['Close'] > (hl2 - m*atr)

def get_ltp(token, key):
    headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}
    url=f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={quote(key, safe='')}"
    try:
        r=requests.get(url, headers=headers, timeout=8)
        j=r.json()
        if j.get("status")=="success":
            v=list(j["data"].values())[0]
            return v.get("last_price"), v.get("last_traded_time")
    except: pass
    return None, None

def get_candles(token, key, intra, hist):
    headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}
    try:
        url1=f"https://api.upstox.com/v2/historical-candle/intraday/{quote(key, safe='')}/{intra}"
        r1=requests.get(url1, headers=headers, timeout=12)
        j1=r1.json()
        if j1.get("status")=="success" and len(j1["data"]["candles"])>5:
            df=pd.DataFrame(j1["data"]["candles"], columns=["ts","Open","High","Low","Close","Volume","OI"])
            df["ts"]=pd.to_datetime(df["ts"]); df.set_index("ts", inplace=True)
            return df.sort_index(), f"TODAY LIVE {intra}"
    except: pass
    try:
        to_date=datetime.now().strftime("%Y-%m-%d"); from_date=(datetime.now()-timedelta(days=7)).strftime("%Y-%m-%d")
        url2=f"https://api.upstox.com/v2/historical-candle/{quote(key, safe='')}/{hist}/{to_date}/{from_date}"
        r2=requests.get(url2, headers=headers, timeout=12)
        j2=r2.json()
        if j2.get("status")=="success" and len(j2["data"]["candles"])>0:
            df=pd.DataFrame(j2["data"]["candles"], columns=["ts","Open","High","Low","Close","Volume","OI"])
            df["ts"]=pd.to_datetime(df["ts"]); df.set_index("ts", inplace=True)
            return df.sort_index(), f"LAST {hist}"
        else:
            st.sidebar.json(j2)
    except Exception as e:
        st.sidebar.error(str(e))
    return None, "FAIL"

inst_key = f"NSE_EQ|{custom}" if custom else upstox_map[selected]
hist_int = historical_map[timeframe_ui]

if auto_tick:
    ltp, ltt = get_ltp(upstox_token, inst_key)
    if ltp: st.success(f"🔴 LIVE TICK TIK {selected} - LTP: {ltp} | {ltt}")
    else: st.info("Weekend hai - LTP Monday ko tik tik karega")

df, mode = get_candles(upstox_token, inst_key, timeframe_ui, hist_int)
if df is None: st.stop()

df['EMA9']=ema(df['Close'],9); df['EMA21']=ema(df['Close'],21); df['EMA50']=ema(df['Close'],50)
df['RSI']=rsi(df['Close'],14); df['VWAP']=(df['Close']*df['Volume']).cumsum()/df['Volume'].cumsum()
df['Body']=abs(df['Close']-df['Open']); df['UpperWick']=df['High']-df[['Open','Close']].max(axis=1)
df['Green']=df['Close']>df['Open']; df['Red']=df['Close']<df['Open']

# MID BEECH ME
last_day=df.index[-1].date(); df_today=df[df.index.date==last_day]
today_mid=(df_today['High'].max()+df_today['Low'].min())/2 if len(df_today)>0 else df['Close'].iloc[-20:].mean()
opening_mid=(df_today.head(3)['High'].max()+df_today.head(3)['Low'].min())/2 if len(df_today)>=3 else today_mid

# PANCH BARISH ENTRY
df['C1']=df['EMA9']>df['EMA21']; df['C2']=df['Close']>df['EMA9']
df['C3']=(df['RSI']>=55)&(df['RSI']<=80); df['C4']=supertrend_bull(df); df['C5']=df['Close']>df['EMA50']
df['HEAT']=df['C1'].astype(int)+df['C2'].astype(int)+df['C3'].astype(int)+df['C4'].astype(int)+df['C5'].astype(int)
df['ALL5']=df['C1']&df['C2']&df['C3']&df['C4']&df['C5']
df['ENTRY']=df['ALL5']&(df['ALL5'].shift(1)==False)

# 5 EXIT RADAR
df['Exit1']=df['Green']&df['Green'].shift(1)&df['Green'].shift(2)&(df['Close']>df['EMA21']*1.012)
df['Exit2']=(df['Green'].shift(1))&(df['Red'])&(df['Open']>df['Close'].shift(1))
df['Exit3']=(df['UpperWick']>2*df['Body']); df['Exit4']=df['Red']&df['Red'].shift(1)
df['Exit5']=(df['RSI'].shift(1)>75)&(df['RSI']<df['RSI'].shift(1))
df['EXIT']=df['Exit1']|df['Exit2']|df['Exit3']|df['Exit4']|df['Exit5']
df['Div']=(df['Close'].rolling(5).max()>df['Close'].rolling(5).max().shift(5))&(df['RSI'].rolling(5).max()<df['RSI'].rolling(5).max().shift(5))

last=df.iloc[-1]

# DASHBOARD
c1,c2,c3,c4=st.columns(4)
c1.metric("Price", f"{last['Close']:.2f}", mode)
c2.metric("TODAY MID", f"{today_mid:.2f}", "UPAR" if last['Close']>today_mid else "NEECHE")
c3.metric("OPEN MID", f"{opening_mid:.2f}")
c4.metric("HEAT", f"{int(last['HEAT'])}/5", "5/5 BUY" if last['HEAT']==5 else "WAIT")
if last['Div']: st.warning("⚠️ PREMIUM DIVERGENCE")

a,b,c,d,e=st.columns(5)
a.success("1 EMA9>21 ✅") if last['C1'] else a.error("1 EMA9>21 ❌")
b.success("2 Close>9 ✅") if last['C2'] else b.error("2 Close>9 ❌")
c.success(f"3 RSI {last['RSI']:.0f} ✅") if last['C3'] else c.error(f"3 RSI {last['RSI']:.0f} ❌")
d.success("4 Supertrend ✅") if last['C4'] else d.error("4 Supertrend ❌")
e.success("5 EMA50 ✅") if last['C5'] else e.error("5 EMA50 ❌")

if last['ALL5']:
    st.success("🔥 PANCH BARISH LOCK 5/5 BULLISH BUY 🔥")
    if enable_sound:
        st.components.v1.html(f'<audio autoplay><source src="{sound_entry}" type="audio/mpeg"></audio><h3>🔔 5/5 BUY TING!</h3>', height=80)
        st.balloons()
else:
    st.warning(f"WAIT - {int(last['HEAT'])}/5 hai, 5/5 pe BUY")

if last['EXIT']:
    rs=[]
    if last['Exit1']: rs.append("3 Green Thakawat")
    if last['Exit2']: rs.append("Bearish Engulfing")
    if last['Exit3']: rs.append("Shooting Star")
    if last['Exit4']: rs.append("2 Red")
    if last['Exit5']: rs.append("RSI Palat")
    st.error(f"🚨 EXIT - {', '.join(rs)}")
    if enable_sound:
        st.components.v1.html(f'<audio autoplay><source src="{sound_exit}" type="audio/mpeg"></audio><h3>🚨 EXIT!</h3>', height=80)

fig=go.Figure()
fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"))
fig.add_trace(go.Scatter(x=df.index, y=df['EMA9'], name="EMA9")); fig.add_trace(go.Scatter(x=df.index, y=df['EMA21'], name="EMA21")); fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], name="EMA50"))
fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name="VWAP", line=dict(dash='dash')))
fig.add_hline(y=today_mid, line_dash="dash", line_color="orange", annotation_text=f"TODAY MID {today_mid:.1f} BEECH ME")
fig.add_hline(y=opening_mid, line_dash="dot", line_color="purple", annotation_text=f"OPEN MID {opening_mid:.1f}")
fig.add_trace(go.Scatter(x=df[df['ENTRY']].index, y=df[df['ENTRY']]['Low']*0.998, mode='markers', marker=dict(symbol='triangle-up', size=15, color='green'), name="5/5 BUY"))
fig.add_trace(go.Scatter(x=df[df['EXIT']].index, y=df[df['EXIT']]['High']*1.002, mode='markers', marker=dict(symbol='triangle-down', size=15, color='red'), name="EXIT"))
fig.update_layout(height=700, xaxis_rangeslider_visible=False, title=f"{selected} - {mode} - V33 NIGHT LOCK")
st.plotly_chart(fig, use_container_width=True)

st.caption("V33 NIGHT LOCK | Raat wala final | Pure Token | No Yahoo")

if auto_tick:
    time.sleep(5)
    st.rerun()