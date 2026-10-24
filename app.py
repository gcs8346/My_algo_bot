import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from urllib.parse import quote
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Topu V29 FIXED")
st.title("🔥 Topu V29 FIXED - Pure Upstox + Live Mid + Sound")

# ========= SIDEBAR =========
st.sidebar.header("🔑 UPSTOX TOKEN BOX")
upstox_token = st.sidebar.text_input("Upstox Access Token", type="password", help="Upstox App > API > Access Token")
token_on = len(upstox_token.strip()) > 20 if upstox_token else False

st.sidebar.header("🔊 SOUND BOX V17")
enable_sound = st.sidebar.checkbox("Sound ON", value=True)

upstox_map = {
    "NIFTY 50": "NSE_INDEX|Nifty 50",
    "BANK NIFTY": "NSE_INDEX|Nifty Bank",
    "FIN NIFTY": "NSE_INDEX|Nifty Fin Service",
    "SENSEX": "BSE_INDEX|SENSEX",
    "NIFTY IT": "NSE_INDEX|Nifty IT",
    "MIDCAP": "NSE_INDEX|Nifty Mid Select"
}
selected = st.sidebar.selectbox("Index Chuno", list(upstox_map.keys()))
custom = st.sidebar.text_input("Stock (RELIANCE, TCS)", "").strip().upper()
interval = st.sidebar.selectbox("Timeframe", ["5minute", "15minute", "30minute", "day"], index=0)

if not token_on:
    st.warning("⚠️ Topu, Upstox Token dalo tabhi lakh wala live data ayega. Abhi chart band hai.")
    st.stop()

def ema(s, n): return s.ewm(span=n, adjust=False).mean()
def rsi(s, n=14):
    d = s.diff()
    g = d.where(d>0,0).rolling(n).mean()
    l = -d.where(d<0,0).rolling(n).mean()
    return 100 - (100 / (1 + g/l))

def get_upstox(token, instrument_key, interval):
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    # 1. Try Intraday - aaj ka live
    try:
        url1 = f"https://api.upstox.com/v2/historical-candle/intraday/{quote(instrument_key, safe='')}/{interval}"
        r1 = requests.get(url1, headers=headers, timeout=10)
        j1 = r1.json()
        if j1.get("status") == "success" and len(j1["data"]["candles"]) > 5:
            df = pd.DataFrame(j1["data"]["candles"], columns=["ts","Open","High","Low","Close","Volume","OI"])
            df["ts"] = pd.to_datetime(df["ts"])
            df.set_index("ts", inplace=True)
            return df.sort_index(), "TODAY LIVE"
    except: pass

    # 2. Fallback Historical - last 2 days (Saturday ke liye)
    try:
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d")
        url2 = f"https://api.upstox.com/v2/historical-candle/{quote(instrument_key, safe='')}/{interval}/{to_date}/{from_date}"
        r2 = requests.get(url2, headers=headers, timeout=10)
        j2 = r2.json()
        if j2.get("status") == "success":
            df = pd.DataFrame(j2["data"]["candles"], columns=["ts","Open","High","Low","Close","Volume","OI"])
            df["ts"] = pd.to_datetime(df["ts"])
            df.set_index("ts", inplace=True)
            return df.sort_index(), "LAST TRADING DAY"
    except Exception as e:
        st.error(f"Upstox Error: {e}")
    return None, "FAIL"

inst_key = f"NSE_EQ|{custom}" if custom else upstox_map[selected]
df, mode = get_upstox(upstox_token, inst_key, interval)

if df is None or len(df) < 20:
    st.error("Data nahi aaya. Token expire to nahi? Ya Stock ka naam galat hai.")
    st.stop()

df['EMA9'] = ema(df['Close'],9)
df['EMA21'] = ema(df['Close'],21)
df['EMA50'] = ema(df['Close'],50)
df['RSI'] = rsi(df['Close'],14)

# ===== LIVE MID BEECH MEIN =====
last_day = df.index[-1].date()
df_today = df[df.index.date == last_day]
today_high = df_today['High'].max()
today_low = df_today['Low'].min()
today_mid = (today_high + today_low) / 2
opening_mid = (df_today.head(3)['High'].max() + df_today.head(3)['Low'].min()) / 2 if len(df_today)>=3 else today_mid

# ===== TERA 5 CHECKLIST LOCK =====
df['C1'] = df['EMA9'] > df['EMA21']
df['C2'] = df['Close'] > df['EMA9']
df['C3'] = (df['RSI'] >= 55) & (df['RSI'] <= 80)
df['C4'] = df['Close'] > (df['High']+df['Low'])/2  # Supertrend Bull simplified
df['C5'] = df['Close'] > df['EMA50']
df['Cross'] = (df['EMA9'] > df['EMA21']) & (df['EMA9'].shift(1) <= df['EMA21'].shift(1))
df['ENTRY'] = df['Cross'] & df['C2'] & df['C3'] & df['C4'] & df['C5']
df['EXIT'] = (df['Close'] < df['Open']) & (df['Close'].shift(1) < df['Open'].shift(1))

last = df.iloc[-1]

# ===== SOUND BOX =====
if enable_sound:
    if last['ENTRY']:
        st.components.v1.html('<audio autoplay><source src="https://cdn.pixabay.com/audio/2022/03/24/audio_1b9bd41700.mp3" type="audio/mpeg"></audio><h2>🔔 ENTRY BUY!</h2>', height=100)
        st.balloons()
    if last['EXIT']:
        st.components.v1.html('<audio autoplay><source src="https://cdn.pixabay.com/audio/2022/03/10/audio_c3c8a6faa7.mp3" type="audio/mpeg"></audio><h2>🚨 EXIT!</h2>', height=100)

# ===== DASHBOARD =====
c1,c2,c3 = st.columns(3)
c1.metric("Price", f"{last['Close']:.2f}", f"{mode}")
c2.metric(f"MID ({mode})", f"{today_mid:.2f}", "UPAR" if last['Close']>today_mid else "NEECHE")
c3.metric("Opening 15m Mid", f"{opening_mid:.2f}")

fig = go.Figure()
fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"))
fig.add_trace(go.Scatter(x=df.index, y=df['EMA9'], name="EMA9"))
fig.add_trace(go.Scatter(x=df.index, y=df['EMA21'], name="EMA21"))
fig.add_hline(y=today_mid, line_dash="dash", line_color="orange", annotation_text=f"MID {today_mid:.1f}")
fig.add_hline(y=opening_mid, line_dash="dot", line_color="purple", annotation_text=f"OPEN MID {opening_mid:.1f}")
fig.add_trace(go.Scatter(x=df[df['ENTRY']].index, y=df[df['ENTRY']]['Low']*0.998, mode='markers', marker=dict(symbol='triangle-up', size=14, color='green'), name="ENTRY"))
fig.add_trace(go.Scatter(x=df[df['EXIT']].index, y=df[df['EXIT']]['High']*1.002, mode='markers', marker=dict(symbol='triangle-down', size=14, color='red'), name="EXIT"))
fig.update_layout(height=650, xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)

st.success(f"V29 FIXED READY - Mode: {mode} | Token ON 🟢")