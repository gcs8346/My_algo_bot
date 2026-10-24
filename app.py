import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from urllib.parse import quote
from datetime import datetime, timedelta
import time

st.set_page_config(layout="wide", page_title="Topu V38.1 FIX")
st.title("🔥 Topu V38.1 - BACKTEST BUTTON FIX LOCK")

# ===== SIDEBAR =====
st.sidebar.header("🔑 UPSTOX TOKEN BOX")
upstox_token = st.sidebar.text_input("Upstox Access Token", type="password")
is_token = len(upstox_token.strip()) > 30 if upstox_token else False
if is_token:
    st.sidebar.success("🟢 TOKEN ON")
else:
    st.sidebar.error("🔴 TOKEN DALO")

st.sidebar.header("🔊 SOUND BOX V17")
enable_sound = st.sidebar.checkbox("Sound ON", True)

upstox_index_map = {
    "NIFTY 50": "NSE_INDEX|Nifty 50", "BANK NIFTY": "NSE_INDEX|Nifty Bank",
    "FIN NIFTY": "NSE_INDEX|Nifty Fin Service", "SENSEX": "BSE_INDEX|SENSEX",
    "NIFTY IT": "NSE_INDEX|Nifty IT", "MIDCAP": "NSE_INDEX|Nifty Mid Select"
}
stock_isin_map = {
    "RELIANCE": "NSE_EQ|INE002A01018", "TCS": "NSE_EQ|INE467B01029", "INFY": "NSE_EQ|INE009A01021",
    "HDFCBANK": "NSE_EQ|INE040A01034", "ICICIBANK": "NSE_EQ|INE090A01021", "SBIN": "NSE_EQ|INE062A01020"
}

st.sidebar.header("📋 WATCHLIST BOX")
watch_input = st.sidebar.text_area("Watchlist comma se", "NIFTY 50, BANK NIFTY, RELIANCE, TCS", height=80)

mode = st.sidebar.radio("Main Chart Kiska?", ["INDEX","STOCK"], index=0)

if mode=="INDEX":
    sel_idx = st.sidebar.selectbox("Index Chuno", list(upstox_index_map.keys()), index=0)
    final_label = sel_idx
    final_key_fixed = upstox_index_map[sel_idx]
else:
    sel_stock = st.sidebar.selectbox("Stock Chuno", list(stock_isin_map.keys()), index=0)
    custom = st.sidebar.text_input("Ya Likh Do (RELIANCE)", "").strip().upper()
    final_label = custom if custom else sel_stock
    final_key_fixed = stock_isin_map.get(final_label) if not custom else None

timeframe_ui = st.sidebar.selectbox("Timeframe", ["1minute","5minute","15minute","30minute","day"], index=2)
st.sidebar.header("⚡ TICK SPEED")
tick_mode = st.sidebar.selectbox("Speed", ["1 SEC ULTRA FAST ⚡","2 SEC FAST","5 SEC SAFE"], index=0)
tick_map = {"1 SEC ULTRA FAST ⚡":1,"2 SEC FAST":2,"5 SEC SAFE":5}
tick_sec = tick_map[tick_mode]
auto_tick = st.sidebar.checkbox(f"TICK TICK ON ({tick_sec} sec)", True)

historical_map = {"1minute":"1minute","5minute":"1minute","15minute":"30minute","30minute":"30minute","day":"day"}

if not is_token:
    st.error("Token dalo Topu No.1")
    st.stop()

def ema(s,n): return s.ewm(span=n, adjust=False).mean()
def rsi_fixed(s, n=14):
    delta=s.diff(); gain=delta.where(delta>0,0.0); loss=-delta.where(delta<0,0.0)
    ag=gain.ewm(alpha=1/n, min_periods=n, adjust=False).mean()
    al=loss.ewm(alpha=1/n, min_periods=n, adjust=False).mean()
    rs=ag/al
    rsi=100-(100/(1+rs))
    return rsi.fillna(50)
def supertrend_bull(df,p=10,m=3):
    hl2=(df['High']+df['Low'])/2; atr=(df['High']-df['Low']).rolling(p).mean()
    return df['Close'] > (hl2 - m*atr)

def resolve_stock_key(token, symbol):
    headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}
    if symbol in upstox_index_map: return upstox_index_map[symbol]
    if symbol in stock_isin_map: return stock_isin_map[symbol]
    try:
        url=f"https://api.upstox.com/v2/instruments/search?query={symbol}&exchanges=NSE&segments=EQ&records=5"
        r=requests.get(url, headers=headers, timeout=10)
        j=r.json()
        if j.get("status")=="success" and len(j["data"])>0:
            return j["data"][0].get("instrument_key")
    except: pass
    return f"NSE_EQ|{symbol}"

def get_ltp(token,key):
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

def get_candles(token,key,intra,hist):
    headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}
    try:
        url1=f"https://api.upstox.com/v2/historical-candle/intraday/{quote(key, safe='')}/{intra}"
        r1=requests.get(url1, headers=headers, timeout=12)
        j1=r1.json()
        if j1.get("status")=="success" and len(j1["data"]["candles"])>10:
            df=pd.DataFrame(j1["data"]["candles"], columns=["ts","Open","High","Low","Close","Volume","OI"])
            df["ts"]=pd.to_datetime(df["ts"]); df.set_index("ts", inplace=True)
            return df.sort_index(), f"TODAY {intra}"
    except: pass
    try:
        to_date=datetime.now().strftime("%Y-%m-%d"); from_date=(datetime.now()-timedelta(days=60)).strftime("%Y-%m-%d")
        url2=f"https://api.upstox.com/v2/historical-candle/{quote(key, safe='')}/{hist}/{to_date}/{from_date}"
        r2=requests.get(url2, headers=headers, timeout=12)
        j2=r2.json()
        if j2.get("status")=="success" and len(j2["data"]["candles"])>0:
            df=pd.DataFrame(j2["data"]["candles"], columns=["ts","Open","High","Low","Close","Volume","OI"])
            df["ts"]=pd.to_datetime(df["ts"]); df.set_index("ts", inplace=True)
            return df.sort_index(), f"LAST {hist}"
    except: pass
    return None, "FAIL"

def analyze_df(df):
    df['EMA9']=ema(df['Close'],9); df['EMA21']=ema(df['Close'],21); df['EMA50']=ema(df['Close'],50)
    df['RSI']=rsi_fixed(df['Close'],14)
    df['C1']=df['EMA9']>df['EMA21']; df['C2']=df['Close']>df['EMA9']
    df['C3']=(df['RSI']>=55)&(df['RSI']<=80); df['C4']=supertrend_bull(df); df['C5']=df['Close']>df['EMA50']
    df['HEAT']=df['C1'].astype(int)+df['C2'].astype(int)+df['C3'].astype(int)+df['C4'].astype(int)+df['C5'].astype(int)
    df['ALL5']=df['C1']&df['C2']&df['C3']&df['C4']&df['C5']
    df['ENTRY']=df['ALL5']&(df['ALL5'].shift(1)==False)
    df['Body']=abs(df['Close']-df['Open']); df['UpperWick']=df['High']-df[['Open','Close']].max(axis=1)
    df['Green']=df['Close']>df['Open']; df['Red']=df['Close']<df['Open']
    df['Exit1']=df['Green']&df['Green'].shift(1)&df['Green'].shift(2)&(df['Close']>df['EMA21']*1.012)
    df['Exit2']=(df['Green'].shift(1))&(df['Red'])&(df['Open']>df['Close'].shift(1))
    df['Exit3']=(df['UpperWick']>2*df['Body']); df['Exit4']=df['Red']&df['Red'].shift(1)
    df['Exit5']=(df['RSI'].shift(1)>75)&(df['RSI']<df['RSI'].shift(1))
    df['EXIT']=df['Exit1']|df['Exit2']|df['Exit3']|df['Exit4']|df['Exit5']
    return df

if final_key_fixed is None:
    final_key_fixed = resolve_stock_key(upstox_token, final_label)

# WATCHLIST
st.subheader("📋 WATCHLIST")
watch_labels = [x.strip().upper() for x in watch_input.split(",") if x.strip()]
watch_rows=[]
for lbl in watch_labels[:6]:
    k = resolve_stock_key(upstox_token, lbl)
    ltp = get_ltp(upstox_token, k)
    df_w,_ = get_candles(upstox_token, k, "15minute", "30minute")
    heat=0; status="..."
    if df_w is not None:
        df_w=analyze_df(df_w)
        last_w=df_w.iloc[-1]
        heat=int(last_w['HEAT'])
        if last_w['ALL5']:
            status="🔥 5/5 BUY"
        else:
            status=f"{heat}/5 WAIT"
    watch_rows.append({"Symbol":lbl,"LTP":ltp,"HEAT":heat,"Status":status})
if watch_rows:
    st.dataframe(pd.DataFrame(watch_rows), use_container_width=True)

st.divider()

# MAIN DATA
df_main,_ = get_candles(upstox_token, final_key_fixed, timeframe_ui, historical_map[timeframe_ui])
if df_main is None:
    st.error("Data nahi aaya")
    st.stop()
df_main=analyze_df(df_main)
last=df_main.iloc[-1]

c1,c2,c3,c4=st.columns(4)
c1.metric(f"{final_label} Price", f"{last['Close']:.2f}")
c2.metric("HEAT", f"{int(last['HEAT'])}/5")

# YAHI FIX KIYA HAI - IF ELSE
if last['ALL5']:
    c3.success("🔥 5/5 BUY")
else:
    c3.warning(f"WAIT {int(last['HEAT'])}/5")

c4.metric("RSI", f"{last['RSI']:.0f}")

# BACKTEST BUTTON
st.divider()
st.subheader("📊 BACKTEST - BUTTON WALA")

backtest_btn = st.button("🔍 BACKTEST BUTTON DABA - PICHLA DATA DEKH", type="primary", use_container_width=True)

if backtest_btn:
    st.session_state['show_backtest'] = True

if st.session_state.get('show_backtest', False):
    with st.spinner(f"{final_label} ka pichla 60 din ka data nikal raha hu..."):
        df_bt,_ = get_candles(upstox_token, final_key_fixed, "day", "day")
        if df_bt is not None and len(df_bt)>20:
            df_bt=analyze_df(df_bt)
            trades=[]
            for i in range(20, len(df_bt)-5):
                if df_bt.iloc[i]['ENTRY']:
                    entry = df_bt.iloc[i]['Close']
                    future_close = df_bt.iloc[i+5]['Close']
                    pnl_pct = (future_close-entry)/entry*100
                    if pnl_pct > 0.5:
                        result_str = "✅ WIN"
                    else:
                        result_str = "❌ LOSS"
                    trades.append({"Date":str(df_bt.index[i].date()),"Entry":round(entry,2),"5 Din Baad":round(future_close,2),"PnL %":round(pnl_pct,2),"Result":result_str})
            if trades:
                df_trades=pd.DataFrame(trades)
                total=len(df_trades)
                wins=len(df_trades[df_trades['Result']=="✅ WIN"])
                win_rate=wins/total*100 if total>0 else 0
                m1,m2,m3,m4=st.columns(4)
                m1.metric("Total 5/5 Trades", total)
                m2.metric("WIN", wins)
                m3.metric("Win Rate", f"{win_rate:.1f}%")
                m4.metric("Avg Profit", f"{df_trades['PnL %'].mean():.2f}%")
                st.success(f"👇 Ye raha pura data - {final_label} me pichle 60 din ka")
                st.dataframe(df_trades, use_container_width=True)
            else:
                st.warning("Pichle 60 din me isme 5/5 ka signal hi nahi bana")
        else:
            st.error("Backtest data nahi aaya")
else:
    st.info("👆 Button daba - tere saamne data aa jayega ki kya kya hua tha")

# CHART
fig=go.Figure()
fig.add_trace(go.Candlestick(x=df_main.index, open=df_main['Open'], high=df_main['High'], low=df_main['Low'], close=df_main['Close'], name="Price"))
fig.add_trace(go.Scatter(x=df_main.index, y=df_main['EMA9'], name="EMA9"))
fig.add_trace(go.Scatter(x=df_main.index, y=df_main['EMA21'], name="EMA21"))
fig.add_trace(go.Scatter(x=df_main.index, y=df_main['EMA50'], name="EMA50"))
fig.add_trace(go.Scatter(x=df_main[df_main['ENTRY']].index, y=df_main[df_main['ENTRY']]['Low']*0.998, mode='markers', marker=dict(symbol='triangle-up', size=15, color='green'), name="5/5 BUY"))
fig.add_trace(go.Scatter(x=df_main[df_main['EXIT']].index, y=df_main[df_main['EXIT']]['High']*1.002, mode='markers', marker=dict(symbol='triangle-down', size=15, color='red'), name="EXIT"))
fig.update_layout(height=650, xaxis_rangeslider_visible=False, title=f"{final_label} - {timeframe_ui} - V38.1 FIX")
st.plotly_chart(fig, use_container_width=True)

st.caption(f"V38.1 FIX LOCK | {final_label} | {tick_sec}SEC | Pure Token")

if auto_tick:
    time.sleep(tick_sec)
    st.rerun()