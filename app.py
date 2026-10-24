import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from urllib.parse import quote
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Topu V30 PURE TOKEN")
st.title("🔥 Topu V30 - PURE TOKEN ONLY - Live Mid")

# ===== SIDEBAR =====
st.sidebar.header("🔑 UPSTOX TOKEN BOX")
upstox_token = st.sidebar.text_input("Upstox Access Token", type="password")
is_token = len(upstox_token.strip()) > 30 if upstox_token else False

st.sidebar.header("🔊 SOUND BOX V17")
enable_sound = st.sidebar.checkbox("Sound ON", True)

upstox_map = {
    "NIFTY 50": "NSE_INDEX|Nifty 50",
    "BANK NIFTY": "NSE_INDEX|Nifty Bank",
    "FIN NIFTY": "NSE_INDEX|Nifty Fin Service",
    "SENSEX": "BSE_INDEX|SENSEX",
    "NIFTY IT": "NSE_INDEX|Nifty IT"
}
selected = st.sidebar.selectbox("Index Chuno", list(upstox_map.keys()))
custom = st.sidebar.text_input("Stock (RELIANCE, TCS)", "").strip().upper()

# Upstox me 2 tarah ka interval hota hai
timeframe_ui = st.sidebar.selectbox("Timeframe", ["1minute", "5minute", "15minute", "30minute", "day"], index=2)

# Historical API ke liye mapping - yahi tera error tha
historical_map = {
    "1minute": "1minute",
    "5minute": "1minute",  # 5min historical me nahi hai to 1min lelo
    "15minute": "30minute", # 15min historical me nahi hai to 30min lelo
    "30minute": "30minute",
    "day": "day"
}
intraday_interval = timeframe_ui
historical_interval = historical_map[timeframe_ui]

if not is_token:
    st.error("⚠️ Topu, Token dalo. Ye pure token wala hai, yfinance nahi chalega.")
    st.stop()

def ema(s,n): return s.ewm(span=n, adjust=False).mean()
def rsi(s,n=14):
    d=s.diff(); g=d.where(d>0,0).rolling(n).mean(); l=-d.where(d<0,0).rolling(n).mean()
    return 100-(100/(1+g/l))

def get_pure_upstox(token, instrument_key, intra_int, hist_int):
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    
    # 1. INTRADAY TRY - Aaj ka live (Saturday ko khali ayega)
    try:
        url1 = f"https://api.upstox.com/v2/historical-candle/intraday/{quote(instrument_key, safe='')}/{intra_int}"
        r1 = requests.get(url1, headers=headers, timeout=15)
        j1 = r1.json()
        st.sidebar.write(f"Intraday: {intra_int} -> {j1.get('status')}")
        if j1.get("status") == "success" and len(j1["data"]["candles"]) > 0:
            df = pd.DataFrame(j1["data"]["candles"], columns=["ts","Open","High","Low","Close","Volume","OI"])
            df["ts"]=pd.to_datetime(df["ts"]); df.set_index("ts", inplace=True)
            return df.sort_index(), f"TODAY LIVE {intra_int}"
    except Exception as e:
        st.sidebar.error(f"Intraday error: {e}")

    # 2. HISTORICAL TRY - Last trading day (FIXED INTERVAL)
    try:
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        url2 = f"https://api.upstox.com/v2/historical-candle/{quote(instrument_key, safe='')}/{hist_int}/{to_date}/{from_date}"
        r2 = requests.get(url2, headers=headers, timeout=15)
        j2 = r2.json()
        st.sidebar.write(f"Historical: {hist_int} -> {j2.get('status')}")
        if j2.get("status") == "success" and len(j2["data"]["candles"]) > 0:
            df = pd.DataFrame(j2["data"]["candles"], columns=["ts","Open","High","Low","Close","Volume","OI"])
            df["ts"]=pd.to_datetime(df["ts"]); df.set_index("ts", inplace=True)
            return df.sort_index(), f"LAST TRADING {hist_int}"
        else:
            st.error("Upstox ka pura jawab:")
            st.json(j2)
    except Exception as e:
        st.error(f"Historical error: {e}")
    
    return None, "FAIL"

inst_key = f"NSE_EQ|{custom}" if custom else upstox_map[selected]
df, mode = get_pure_upstox(upstox_token, inst_key, intraday_interval, historical_interval)

if df is None:
    st.error("Data nahi aaya. Token expire hai kya? Upstox me 1 din me expire hota hai.")
    st.stop()

df['EMA9']=ema(df['Close'],9); df['EMA21']=ema(df['Close'],21); df['EMA50']=ema(df['Close'],50)
df['RSI']=rsi(df['Close'],14)

last_day = df.index[-1].date()
df_today = df[df.index.date == last_day]
today_mid = (df_today['High'].max() + df_today['Low'].min())/2 if len(df_today)>0 else (df['High'].iloc[-20:].max()+df['Low'].iloc[-20:].min())/2
opening_mid = (df_today.head(3)['High'].max() + df_today.head(3)['Low'].min())/2 if len(df_today)>=3 else today_mid

df['Cross']=(df['EMA9']>df['EMA21']) & (df['EMA9'].shift(1)<=df['EMA21'].shift(1))
df['ENTRY']=df['Cross'] & (df['Close']>df['EMA9']) & (df['RSI']>=55) & (df['RSI']<=80) & (df['Close']>df['EMA50'])
df['EXIT']=(df['Close']<df['Open']) & (df['Close'].shift(1)<df['Open'].shift(1))
last=df.iloc[-1]

if enable_sound and last['ENTRY']:
    st.components.v1.html('<audio autoplay><source src="https://cdn.pixabay.com/audio/2022/03/24/audio_1b9bd41700.mp3" type="audio/mpeg"></audio><h2>🔔 ENTRY BUY!</h2>', height=80)
    st.balloons()

c1,c2,c3=st.columns(3)
c1.metric("Price", f"{last['Close']:.2f}", mode)
c2.metric("MID TODAY Live Beech Me", f"{today_mid:.2f}", "UPAR" if last['Close']>today_mid else "NEECHE")
c3.metric("Opening Mid", f"{opening_mid:.2f}")

fig=go.Figure()
fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']))
fig.add_trace(go.Scatter(x=df.index, y=df['EMA9'], name="EMA9")); fig.add_trace(go.Scatter(x=df.index, y=df['EMA21'], name="EMA21"))
fig.add_hline(y=today_mid, line_dash="dash", line_color="orange", annotation_text=f"MID {today_mid:.1f}")
fig.add_hline(y=opening_mid, line_dash="dot", line_color="purple", annotation_text=f"OPEN MID {opening_mid:.1f}")
fig.add_trace(go.Scatter(x=df[df['ENTRY']].index, y=df[df['ENTRY']]['Low']*0.998, mode='markers', marker=dict(symbol='triangle-up', size=14, color='green'), name="ENTRY"))
fig.add_trace(go.Scatter(x=df[df['EXIT']].index, y=df[df['EXIT']]['High']*1.002, mode='markers', marker=dict(symbol='triangle-down', size=14, color='red'), name="EXIT"))
fig.update_layout(height=650, xaxis_rangeslider_visible=False); st.plotly_chart(fig, use_container_width=True)
st.success(f"V30 PURE TOKEN READY - {mode} | No yfinance")