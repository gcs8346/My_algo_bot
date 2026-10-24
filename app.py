import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from urllib.parse import quote
from datetime import datetime, timedelta
import time

st.set_page_config(layout="wide", page_title="Topu V36 STOCK LOCK")
st.title("🔥 Topu V36 - STOCK + INDEX FULL LOCK")

# ===== SIDEBAR =====
st.sidebar.header("🔑 UPSTOX TOKEN BOX")
upstox_token = st.sidebar.text_input("Upstox Access Token", type="password")
is_token = len(upstox_token.strip()) > 30 if upstox_token else False
st.sidebar.write("🟢 TOKEN ON" if is_token else "🔴 TOKEN DALO")

st.sidebar.header("🔊 SOUND BOX V17")
enable_sound = st.sidebar.checkbox("Sound ON", True)
sound_entry = "https://cdn.pixabay.com/audio/2022/03/24/audio_1b9bd41700.mp3"
sound_exit = "https://cdn.pixabay.com/audio/2022/03/10/audio_c3c8a6faa7.mp3"

# ===== STOCK + INDEX SELECTOR =====
st.sidebar.header("📊 MODE CHUNO")
mode = st.sidebar.radio("Kya chalana hai?", ["INDEX", "STOCK"], index=0)

upstox_index_map = {
    "NIFTY 50": "NSE_INDEX|Nifty 50",
    "BANK NIFTY": "NSE_INDEX|Nifty Bank",
    "FIN NIFTY": "NSE_INDEX|Nifty Fin Service",
    "SENSEX": "BSE_INDEX|SENSEX",
    "NIFTY IT": "NSE_INDEX|Nifty IT",
    "MIDCAP": "NSE_INDEX|Nifty Mid Select"
}

# 50 Stock list with ISIN fallback
stock_isin_map = {
    "RELIANCE": "NSE_EQ|INE002A01018", "TCS": "NSE_EQ|INE467B01029", "INFY": "NSE_EQ|INE009A01021",
    "HDFCBANK": "NSE_EQ|INE040A01034", "ICICIBANK": "NSE_EQ|INE090A01021", "SBIN": "NSE_EQ|INE062A01020",
    "BHARTIARTL": "NSE_EQ|INE397D01024", "ITC": "NSE_EQ|INE154A01025", "LT": "NSE_EQ|INE018A01030",
    "KOTAKBANK": "NSE_EQ|INE237A01028", "AXISBANK": "NSE_EQ|INE238A01034", "WIPRO": "NSE_EQ|INE075A01022",
    "BAJFINANCE": "NSE_EQ|INE296A01024", "HCLTECH": "NSE_EQ|INE860A01027", "ASIANPAINT": "NSE_EQ|INE021A01026",
    "MARUTI": "NSE_EQ|INE585B01010", "TITAN": "NSE_EQ|INE280A01028", "SUNPHARMA": "NSE_EQ|INE044A01036",
    "ULTRACEMCO": "NSE_EQ|INE481G01011", "NTPC": "NSE_EQ|INE733E01010"
}

if mode == "INDEX":
    selected_index = st.sidebar.selectbox("Index Chuno", list(upstox_index_map.keys()))
    final_instrument_key = upstox_index_map[selected_index]
    selected_label = selected_index
else:
    stock_list = list(stock_isin_map.keys())
    selected_stock = st.sidebar.selectbox("Stock Chuno (50 stock)", stock_list, index=0)
    custom_stock = st.sidebar.text_input("Ya Stock Likh Do (RELIANCE, TCS)", "").strip().upper()
    if custom_stock:
        selected_label = custom_stock
        final_instrument_key = None  # search se ayega
    else:
        selected_label = selected_stock
        final_instrument_key = stock_isin_map[selected_stock]

timeframe_ui = st.sidebar.selectbox("Timeframe", ["1minute","5minute","15minute","30minute","day"], index=2)
st.sidebar.header("⚡ TICK SPEED")
tick_mode = st.sidebar.selectbox("Speed", ["1 SEC ULTRA FAST ⚡","2 SEC FAST","5 SEC SAFE"], index=0)
tick_map = {"1 SEC ULTRA FAST ⚡":1,"2 SEC FAST":2,"5 SEC SAFE":5}
tick_sec = tick_map[tick_mode]
auto_tick = st.sidebar.checkbox(f"TICK TICK ON ({tick_sec} sec)", True)

historical_map = {"1minute":"1minute","5minute":"1minute","15minute":"30minute","30minute":"30minute","day":"day"}

if not is_token:
    st.error("Topu No.1, Token dalo.")
    st.stop()

def ema(s,n): return s.ewm(span=n, adjust=False).mean()
def rsi_fixed(s, n=14):
    delta = s.diff(); gain = delta.where(delta>0, 0.0); loss = -delta.where(delta<0, 0.0)
    avg_gain = gain.ewm(alpha=1/n, min_periods=n, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/n, min_periods=n, adjust=False).mean()
    rsi = 100 - (100 / (1 + avg_gain/avg_loss))
    return rsi.fillna(50)
def supertrend_bull(df, p=10, m=3):
    hl2=(df['High']+df['Low'])/2; atr=(df['High']-df['Low']).rolling(p).mean()
    return df['Close'] > (hl2 - m*atr)

# ===== YE NAYA HAI - STOCK KA SAHI KEY DHOONDNA =====
def resolve_stock_key(token, symbol):
    headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}
    try:
        # Upstox search API - sahi instrument_key dhoondta hai
        url = f"https://api.upstox.com/v2/instruments/search?query={symbol}&exchanges=NSE&segments=EQ&records=5"
        r = requests.get(url, headers=headers, timeout=10)
        j = r.json()
        if j.get("status")=="success" and len(j["data"])>0:
            for item in j["data"]:
                if item.get("trading_symbol")==symbol or symbol in item.get("name",""):
                    return item.get("instrument_key")
            return j["data"][0].get("instrument_key")
    except Exception as e:
        st.sidebar.write(f"Search fail: {e}")
    # Fallback map
    return stock_isin_map.get(symbol)

def get_ltp(token, key):
    headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}
    url=f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={quote(key, safe='')}"
    try:
        r=requests.get(url, headers=headers, timeout=8)
        j=r.json()
        if j.get("status")=="success":
            v=list(j["data"].values())[0]
            return v.get("last_price")
    except: pass
    return None

def get_candles(token, key, intra, hist):
    headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}
    try:
        url1=f"https://api.upstox.com/v2/historical-candle/intraday/{quote(key, safe='')}/{intra}"
        r1=requests.get(url1, headers=headers, timeout=12)
        j1=r1.json()
        if j1.get("status")=="success" and len(j1["data"]["candles"])>10:
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

# Final key resolve
if final_instrument_key is None:
    with st.spinner(f"{selected_label} ka sahi key dhoond raha hu..."):
        final_instrument_key = resolve_stock_key(upstox_token, selected_label)
    if not final_instrument_key:
        st.error(f"{selected_label} ka key nahi mila. Token sahi hai? Ya symbol galat?")
        st.stop()
    st.sidebar.success(f"Key mila: {final_instrument_key}")

hist_int = historical_map[timeframe_ui]

if auto_tick:
    ltp = get_ltp(upstox_token, final_instrument_key)
    if ltp:
        st.markdown(f"## 🔴 LIVE TICK TIK {selected_label} - LTP: {ltp} | {tick_sec} SEC | Key: {final_instrument_key}")
    else:
        st.info("Weekend - LTP Monday ko")

df, mode_txt = get_candles(upstox_token, final_instrument_key, timeframe_ui, hist_int)
if df is None:
    st.error("Data nahi aaya.")
    st.stop()

df['EMA9']=ema(df['Close'],9); df['EMA21']=ema(df['Close'],21); df['EMA50']=ema(df['Close'],50)
df['RSI']=rsi_fixed(df['Close'],14)
df['VWAP']=(df['Close']*df['Volume']).cumsum()/df['Volume'].cumsum()
df['Body']=abs(df['Close']-df['Open']); df['UpperWick']=df['High']-df[['Open','Close']].max(axis=1)
df['Green']=df['Close']>df['Open']; df['Red']=df['Close']<df['Open']

last_day=df.index[-1].date(); df_today=df[df.index.date==last_day]
today_mid=(df_today['High'].max()+df_today['Low'].min())/2 if len(df_today)>0 else df['Close'].iloc[-20:].mean()
opening_mid=(df_today.head(3)['High'].max()+df_today.head(3)['Low'].min())/2 if len(df_today)>=3 else today_mid

df['C1']=df['EMA9']>df['EMA21']; df['C2']=df['Close']>df['EMA9']
df['C3']=(df['RSI']>=55)&(df['RSI']<=80); df['C4']=supertrend_bull(df); df['C5']=df['Close']>df['EMA50']
df['HEAT']=df['C1'].astype(int)+df['C2'].astype(int)+df['C3'].astype(int)+df['C4'].astype(int)+df['C5'].astype(int)
df['ALL5']=df['C1']&df['C2']&df['C3']&df['C4']&df['C5']
df['ENTRY']=df['ALL5']&(df['ALL5'].shift(1)==False)
df['Exit1']=df['Green']&df['Green'].shift(1)&df['Green'].shift(2)&(df['Close']>df['EMA21']*1.012)
df['Exit2']=(df['Green'].shift(1))&(df['Red'])&(df['Open']>df['Close'].shift(1))
df['Exit3']=(df['UpperWick']>2*df['Body']); df['Exit4']=df['Red']&df['Red'].shift(1)
df['Exit5']=(df['RSI'].shift(1)>75)&(df['RSI']<df['RSI'].shift(1))
df['EXIT']=df['Exit1']|df['Exit2']|df['Exit3']|df['Exit4']|df['Exit5']

last=df.iloc[-1]

c1,c2,c3,c4=st.columns(4)
c1.metric("Price", f"{last['Close']:.2f}", mode_txt)
c2.metric("TODAY MID", f"{today_mid:.2f}", "UPAR" if last['Close']>today_mid else "NEECHE")
c3.metric("OPEN MID", f"{opening_mid:.2f}")
c4.metric("HEAT", f"{int(last['HEAT'])}/5", "5/5 BUY" if last['HEAT']==5 else "WAIT")

st.subheader(f"✅ {selected_label} - 5 BARISH CHECKLIST")
a,b,c,d,e = st.columns(5)
if last['C1']: a.success("1 EMA9>21 ✅")
else: a.error("1 EMA9>21 ❌")
if last['C2']: b.success("2 Close>9 ✅")
else: b.error("2 Close>9 ❌")
if last['C3']: c.success(f"3 RSI {last['RSI']:.0f} ✅")
else: c.error(f"3 RSI {last['RSI']:.0f} ❌")
if last['C4']: d.success("4 Supertrend ✅")
else: d.error("4 Supertrend ❌")
if last['C5']: e.success("5 EMA50 ✅")
else: e.error("5 EMA50 ❌")

if last['ALL5']:
    st.success(f"🔥 {selected_label} - 5/5 BULLISH BUY 🔥")
    if enable_sound:
        st.components.v1.html(f'<audio autoplay><source src="{sound_entry}" type="audio/mpeg"></audio><h3>🔔 5/5 BUY!</h3>', height=80)
        st.balloons()
else:
    st.warning(f"WAIT - {int(last['HEAT'])}/5")

if last['EXIT']:
    st.error("🚨 EXIT SIGNAL")
    if enable_sound:
        st.components.v1.html(f'<audio autoplay><source src="{sound_exit}" type="audio/mpeg"></audio><h3>🚨 EXIT!</h3>', height=80)

fig=go.Figure()
fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"))
fig.add_trace(go.Scatter(x=df.index, y=df['EMA9'], name="EMA9"))
fig.add_trace(go.Scatter(x=df.index, y=df['EMA21'], name="EMA21"))
fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], name="EMA50"))
fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], name="VWAP", line=dict(dash='dash')))
fig.add_hline(y=today_mid, line_dash="dash", line_color="orange", annotation_text=f"TODAY MID {today_mid:.1f}")
fig.add_hline(y=opening_mid, line_dash="dot", line_color="purple", annotation_text=f"OPEN MID {opening_mid:.1f}")
fig.add_trace(go.Scatter(x=df[df['ENTRY']].index, y=df[df['ENTRY']]['Low']*0.998, mode='markers', marker=dict(symbol='triangle-up', size=15, color='green'), name="BUY"))
fig.add_trace(go.Scatter(x=df[df['EXIT']].index, y=df[df['EXIT']]['High']*1.002, mode='markers', marker=dict(symbol='triangle-down', size=15, color='red'), name="EXIT"))
fig.update_layout(height=700, xaxis_rangeslider_visible=False, title=f"{selected_label} - {mode_txt} - V36 STOCK LOCK")
st.plotly_chart(fig, use_container_width=True)

st.caption(f"V36 STOCK LOCK | {selected_label} | {final_instrument_key} | {tick_sec} SEC")

if auto_tick:
    time.sleep(tick_sec)
    st.rerun()