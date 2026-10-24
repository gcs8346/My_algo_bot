import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests, yfinance as yf
from urllib.parse import quote
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Topu V29.2 FIXED")
st.title("🔥 Topu V29.2 - PURE UPSTOX + AUTO FALLBACK")

# ===== SIDEBAR =====
st.sidebar.header("🔑 UPSTOX TOKEN BOX")
upstox_token = st.sidebar.text_input("Upstox Access Token Paste Kar", type="password")
is_token = len(upstox_token.strip()) > 30 if upstox_token else False
st.sidebar.write("Status: 🟢 TOKEN ON" if is_token else "🔴 TOKEN OFF - yfinance se chalega")

st.sidebar.header("🔊 SOUND BOX V17")
enable_sound = st.sidebar.checkbox("Sound ON", True)

upstox_map = {
    "NIFTY 50": "NSE_INDEX|Nifty 50",
    "BANK NIFTY": "NSE_INDEX|Nifty Bank",
    "FIN NIFTY": "NSE_INDEX|Nifty Fin Service",
    "SENSEX": "BSE_INDEX|SENSEX"
}
yahoo_map = {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "FIN NIFTY": "^CNXFINANCE", "SENSEX": "^BSESN"}

selected = st.sidebar.selectbox("Index Chuno", list(upstox_map.keys()))
custom = st.sidebar.text_input("Stock (RELIANCE, TCS)", "").strip().upper()
interval = st.sidebar.selectbox("Timeframe", ["1minute","5minute","15minute","30minute","day"], index=2)

# ===== FUNCTIONS =====
def ema(s,n): return s.ewm(span=n, adjust=False).mean()
def rsi(s,n=14):
    d=s.diff(); g=d.where(d>0,0).rolling(n).mean(); l=-d.where(d<0,0).rolling(n).mean()
    return 100-(100/(1+g/l))

def get_upstox_live(token, instrument_key, interval):
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    # 1. Intraday try
    try:
        url = f"https://api.upstox.com/v2/historical-candle/intraday/{quote(instrument_key, safe='')}/{interval}"
        r = requests.get(url, headers=headers, timeout=15)
        j = r.json()
        st.sidebar.write(f"Intraday API: {j.get('status')}")
        if j.get("status") == "success" and len(j["data"]["candles"]) > 0:
            df = pd.DataFrame(j["data"]["candles"], columns=["ts","Open","High","Low","Close","Volume","OI"])
            df["ts"]=pd.to_datetime(df["ts"]); df.set_index("ts", inplace=True)
            return df.sort_index(), "TODAY LIVE - UPSTOX"
    except Exception as e:
        st.sidebar.error(f"Intraday fail: {e}")

    # 2. Historical try (Saturday ke liye)
    try:
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        url2 = f"https://api.upstox.com/v2/historical-candle/{quote(instrument_key, safe='')}/{interval}/{to_date}/{from_date}"
        r2 = requests.get(url2, headers=headers, timeout=15)
        j2 = r2.json()
        st.sidebar.write(f"Historical API: {j2.get('status')}")
        if j2.get("status") == "success" and len(j2["data"]["candles"]) > 0:
            df = pd.DataFrame(j2["data"]["candles"], columns=["ts","Open","High","Low","Close","Volume","OI"])
            df["ts"]=pd.to_datetime(df["ts"]); df.set_index("ts", inplace=True)
            return df.sort_index(), "LAST WEEK - UPSTOX"
        else:
            st.sidebar.json(j2)
    except Exception as e:
        st.sidebar.error(f"Historical fail: {e}")
    return None, "FAIL"

def get_yahoo(ticker, interval):
    # yfinance interval mapping
    y_interval = "15m" if "15" in interval else "5m" if "5" in interval else "1d"
    df = yf.download(ticker, period="10d", interval=y_interval, auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    df.dropna(inplace=True)
    return df

# ===== DATA FETCH =====
df = None
mode = ""
inst_key = f"NSE_EQ|{custom}" if custom else upstox_map[selected]

if is_token:
    df, mode = get_upstox_live(upstox_token, inst_key, interval)

if df is None or len(df) < 10:
    # AUTO FALLBACK - yfinance
    y_ticker = yahoo_map[selected]
    if custom:
        y_ticker = custom + ".NS" if ".NS" not in custom else custom
    st.warning(f"Upstox se data nahi aaya (Token expire ya Saturday). Ab yfinance se {y_ticker} dikha raha hu.")
    df = get_yahoo(y_ticker, interval)
    mode = "FALLBACK YFINANCE (15min delay)"

df['EMA9']=ema(df['Close'],9); df['EMA21']=ema(df['Close'],21); df['EMA50']=ema(df['Close'],50)
df['RSI']=rsi(df['Close'],14)

# ===== LIVE MID BEECH MEIN =====
last_day = df.index[-1].date()
df_today = df[df.index.date == last_day]
today_mid = (df_today['High'].max() + df_today['Low'].min())/2 if len(df_today)>0 else (df['High'].iloc[-20:].max() + df['Low'].iloc[-20:].min())/2
opening_mid = (df_today.head(3)['High'].max() + df_today.head(3)['Low'].min())/2 if len(df_today)>=3 else today_mid

# ENTRY
df['Cross']=(df['EMA9']>df['EMA21']) & (df['EMA9'].shift(1)<=df['EMA21'].shift(1))
df['ENTRY']=df['Cross'] & (df['Close']>df['EMA9']) & (df['RSI']>=55) & (df['RSI']<=80) & (df['Close']>df['EMA50'])
df['EXIT']=(df['Close']<df['Open']) & (df['Close'].shift(1)<df['Open'].shift(1))
last=df.iloc[-1]

# SOUND
if enable_sound and last['ENTRY']:
    st.components.v1.html('<audio autoplay><source src="https://cdn.pixabay.com/audio/2022/03/24/audio_1b9bd41700.mp3" type="audio/mpeg"></audio><h2>🔔 ENTRY!</h2>', height=80)
    st.balloons()
if enable_sound and last['EXIT']:
    st.components.v1.html('<audio autoplay><source src="https://cdn.pixabay.com/audio/2022/03/10/audio_c3c8a6faa7.mp3" type="audio/mpeg"></audio><h2>🚨 EXIT!</h2>', height=80)

# DASHBOARD
c1,c2,c3=st.columns(3)
c1.metric("Price", f"{last['Close']:.2f}", mode)
c2.metric("MID TODAY", f"{today_mid:.2f}", "UPAR" if last['Close']>today_mid else "NEECHE")
c3.metric("Opening Mid", f"{opening_mid:.2f}")

fig=go.Figure()
fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"))
fig.add_trace(go.Scatter(x=df.index, y=df['EMA9'], name="EMA9")); fig.add_trace(go.Scatter(x=df.index, y=df['EMA21'], name="EMA21"))
fig.add_hline(y=today_mid, line_dash="dash", line_color="orange", annotation_text=f"MID {today_mid:.1f}")
fig.add_hline(y=opening_mid, line_dash="dot", line_color="purple", annotation_text=f"OPEN MID {opening_mid:.1f}")
fig.add_trace(go.Scatter(x=df[df['ENTRY']].index, y=df[df['ENTRY']]['Low'], mode='markers', marker=dict(symbol='triangle-up', size=14, color='green'), name="ENTRY"))
fig.add_trace(go.Scatter(x=df[df['EXIT']].index, y=df[df['EXIT']]['High'], mode='markers', marker=dict(symbol='triangle-down', size=14, color='red'), name="EXIT"))
fig.update_layout(height=650, xaxis_rangeslider_visible=False); st.plotly_chart(fig, use_container_width=True)
st.success(f"V29.2 READY - {mode} | Tera 5 Checklist + Live Mid Beech Me Lock Hai")