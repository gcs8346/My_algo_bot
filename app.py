import streamlit as st
import pandas as pd
import requests
import urllib.parse
from datetime import datetime, timedelta

st.set_page_config(page_title="Topu V15 Trap Detector", layout="wide")
st.title("🔥 Topu V15 - TRAP DETECTOR PRO")
st.caption("Live vs Candle Divergence = Trap")

st.sidebar.header("Topu ka Upstox Setup")
token = st.sidebar.text_input("Upstox Access Token Daal", type="password")
tf = st.sidebar.selectbox("Timeframe", ["1minute", "5minute", "15minute"], index=0)

if not token:
    st.warning("Token daal bhai")
    st.stop()

headers = {'Authorization': f'Bearer {token}'}

def get_ltp(k):
    try:
        enc = urllib.parse.quote(k, safe='')
        url = f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={enc}"
        r = requests.get(url, headers=headers).json()
        data = r.get('data', {})
        if k in data:
            return data[k].get('last_price')
        for v in data.values():
            if isinstance(v, dict) and 'last_price' in v:
                return v['last_price']
        return None
    except:
        return None

def get_candles(k):
    enc = urllib.parse.quote(k, safe='')
    url1 = f"https://api.upstox.com/v2/historical-candle/intraday/{enc}/1minute"
    r1 = requests.get(url1, headers=headers).json()
    candles = r1.get('data', {}).get('candles', [])
    if not candles:
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
        url2 = f"https://api.upstox.com/v2/historical-candle/{enc}/1minute/{from_date}/{to_date}"
        r2 = requests.get(url2, headers=headers).json()
        candles = r2.get('data', {}).get('candles', [])
    if not candles:
        return None
    df = pd.DataFrame(candles, columns=['time','open','high','low','close','volume','oi'])
    df['time'] = pd.to_datetime(df['time'])
    df = df.sort_values('time')
    df = df.set_index('time')
    if tf != "1minute":
        mins = 5 if tf=="5minute" else 15
        df = df.resample(f'{mins}min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum','oi':'last'}).dropna()
    return df.reset_index()

def get_signal(df, ltp):
    df['EMA9'] = df['close'].ewm(span=9).mean()
    df['EMA21'] = df['close'].ewm(span=21).mean()
    df['RSI'] = 100 - (100 / (1 + (df['close'].diff().where(lambda x: x>0, 0).rolling(14).mean() / -df['close'].diff().where(lambda x: x<0, 0).rolling(14).mean())))
    df['Res'] = df['high'].rolling(20).max()
    df['Sup'] = df['low'].rolling(20).min()
    last = df.iloc[-1]
    
    diff = ltp - last['close']
    # Trap logic
    if last['EMA9'] > last['EMA21'] and diff < -10:
        return "⚠️ TRAP", f"FAKE BUY! Candle BUY bol raha hai lekin LIVE {diff:.2f} niche gir raha hai. Resistance {last['Res']:.1f} pe atak gaya!", last['Res'], last['Sup']
    if last['EMA9'] > last['EMA21'] and last['RSI'] > 55:
        if ltp > last['Res'] * 0.998:
            return "WAIT", f"RESISTANCE pe {last['Res']:.1f} - Yahan BUY mat le, wapas ayega!", last['Res'], last['Sup']
        return "BUY", f"BUY OK | Target {ltp*1.005:.1f} | SL {ltp*0.997:.1f}", last['Res'], last['Sup']
    if last['EMA9'] < last['EMA21']:
        return "SELL", f"SELL Trend | Support {last['Sup']:.1f}", last['Res'], last['Sup']
    return "WAIT", f"Sideways | RSI {last['RSI']:.1f}", last['Res'], last['Sup']

SYMBOLS = {
    "NIFTY": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
}

cols = st.columns(2)
for i, (name, key) in enumerate(SYMBOLS.items()):
    df = get_candles(key)
    ltp = get_ltp(key)
    with cols[i]:
        st.subheader(name)
        if ltp and df is not None:
            st.metric(f"{name} LIVE", f"{ltp:.2f}", f"{ltp - df.iloc[-1]['close']:+.2f} vs Candle")
            sig, reason, res, sup = get_signal(df, ltp)
            if "TRAP" in sig:
                st.error(f"🔴 {sig} - {reason}")
            elif sig == "BUY":
                st.success(f"🟢 {sig} - {reason}")
            elif sig == "SELL":
                st.error(f"🔴 {sig} - {reason}")
            else:
                st.warning(f"🟡 {sig} - {reason}")
            st.caption(f"Res: {res:.1f} | Sup: {sup:.1f}")
            st.dataframe(df.tail(2))
        else:
            st.warning("Data nahi")

st.caption(f"Update: {datetime.now().strftime('%H:%M:%S')}")
if st.button("🔄 Refresh"):
    st.rerun()