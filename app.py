import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
from urllib.parse import quote

st.set_page_config(page_title="TOWER V46 FINAL", layout="wide")

# --- CODE PAKADNE KE LIYE - IMPORT KE JUST BAAD ---
params = st.query_params
if "code" in params:
    st.success(f"✅ Upstox Code mil gaya: {params['code']}")
    st.code(params['code'], language="text")
    st.info("Is code ko neeche wale Python script se Token me badlo, phir sidebar me daalo")

st.title("🏰 TOWER V46 - 10/10 FINAL LIVE")

# --- SIDEBAR ---
st.sidebar.header("Upstox Setup")
api_key = st.sidebar.text_input("API Key / Client ID", type="password", help="Developer App se copy karo")
if api_key:
    login_url = f"https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={api_key}&redirect_uri=https://myalgobot-6kbrowounnbyajr6pkvt6y.streamlit.app/"
    st.sidebar.link_button("🔑 Upstox Login Karo", login_url)
    st.sidebar.caption("Login ke baad wapas isi app pe aaoge, upar Code dikhega")

upstox_token = st.sidebar.text_input("Upstox Token (Roz 6 AM naya)", type="password")
tick_speed = st.sidebar.select_slider("⏱️ Tik-Tik Speed", options=[0.8, 1.0, 1.5, 2.0, 3.0], value=1.0)
auto_tick = st.sidebar.checkbox(f"🔴 LIVE ON ({tick_speed}s)", value=False)
st.sidebar.divider()

STOCKS = {
    "Nifty 50":"NSE_INDEX|Nifty 50",
    "Bank Nifty":"NSE_INDEX|Nifty Bank",
    "Sensex":"BSE_INDEX|SENSEX",
    "RELIANCE":"NSE_EQ|INE002A01018",
    "GOLD":"MCX_FO|GOLDM26NOVFUT",
    "CRUDEOIL":"MCX_FO|CRUDEOIL26NOVFUT"
}
sel_name = st.sidebar.selectbox("Stock", list(STOCKS.keys()))
sel_inst = STOCKS[sel_name]
tf = st.sidebar.selectbox("Timeframe", ["1minute","5minute","15minute"], index=1)

# --- API FUNCTIONS - FIXED URL ENCODING ---
def get_ltp(token, inst):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        url = "https://api.upstox.com/v2/market-quote/ltp"
        # params se | aur space auto %7C %20 ban jayega
        r = requests.get(url, headers=headers, params={"instrument_key": inst}, timeout=4).json()
        if r.get('status')=='success':
            return float(r['data'][inst]['last_price'])
    except Exception as e:
        st.sidebar.write(f"LTP Error: {e}")
    return None

@st.cache_data(ttl=20)
def get_candles(token, inst, interval):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        enc_inst = quote(inst, safe='')
        url = f"https://api.upstox.com/v2/historical-candle/intraday/{enc_inst}/{interval}"
        r = requests.get(url, headers=headers, timeout=5).json()
        if r.get('status')=='success' and r['data'].get('candles'):
            df = pd.DataFrame(r['data']['candles'], columns=['Timestamp','Open','High','Low','Close','Volume','OI'])
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            df = df.set_index('Timestamp')
            df = df.sort_index()
            return df
    except Exception as e:
        st.sidebar.write(f"Candle Error: {e}")
    return None

def calc_rsi(s):
    d=s.diff(); g=d.where(d>0,0).rolling(14).mean(); l=-d.where(d<0,0).rolling(14).mean(); return 100-(100/(1+g/l))

def analyze(df):
    df['EMA9']=df['Close'].ewm(span=9).mean(); df['EMA21']=df['Close'].ewm(span=21).mean(); df['EMA50']=df['Close'].ewm(span=50).mean()
    df['RSI']=calc_rsi(df['Close']); df['VolSMA']=df['Volume'].rolling(20).mean()
    df['Typical']=(df['High']+df['Low']+df['Close'])/3; df['VWAP']=(df['Typical']*df['Volume']).cumsum()/df['Volume'].cumsum()
    hl2=(df['High']+df['Low'])/2; atr=(df['High']-df['Low']).rolling(10).mean()
    df['C1']=df['EMA9']>df['EMA21']; df['C2']=df['Close']>df['EMA9']; df['C3']=(df['RSI']>=55)&(df['RSI']<=80); df['C4']=df['Close']>(hl2+3*atr); df['C5']=df['Close']>df['EMA50']
    df['HEAT']=df[['C1','C2','C3','C4','C5']].sum(axis=1)
    df['SM1']=df['Close']>df['High'].rolling(10).max().shift(1); df['SM2']=df['Close']>df['Low'].rolling(10).min().shift(1)
    fvg=[True if i>2 and df['Low'].iloc[i]>df['High'].iloc[i-2] else False for i in range(len(df))]
    df['SM3']=pd.Series(fvg, index=df.index).rolling(10).max().astype(bool); df['SM4']=df['Close']>df['VWAP']; df['SM5']=df['Volume']>df['VolSMA']*1.2
    df['SM_HEAT']=df[['SM1','SM2','SM3','SM4','SM5']].sum(axis=1); df['TOTAL']=df['HEAT']+df['SM_HEAT']
    return df

# --- MAIN ---
if not upstox_token:
    st.warning("Token daal - bina token ke LIVE nahi chalega")
    st.stop()

if st.button(f"🚀 {sel_name} CHECK", type="primary", width='stretch') or auto_tick:
    ltp = get_ltp(upstox_token, sel_inst)
    df = get_candles(upstox_token, sel_inst, tf)
    
    if ltp is None and df is None:
        st.error("Token expire hai - naya token daal. Market band ho to 9:15 ke baad try kar.")
        st.stop()

    if df is not None:
        df = analyze(df); last = df.iloc[-1]
        price = ltp if ltp else last['Close']
        label = "LIVE" if ltp else "CLOSE"
        
        m1,m2,m3,m4=st.columns(4)
        m1.metric(f"{sel_name} LTP ({label})", f"{price:.2f}", delta=datetime.now().strftime("%H:%M:%S"))
        m2.metric("Technical 5/5", f"{int(last['HEAT'])}/5")
        m3.metric("Smart 5/5", f"{int(last['SM_HEAT'])}/5")
        m4.metric("TOTAL 10/10", f"{int(last['TOTAL'])}/10")

        st.divider()
        st.write(f"**Tech:** EMA9>21:{'✅' if last['C1'] else '❌'} | Close>EMA9:{'✅' if last['C2'] else '❌'} | RSI {last['RSI']:.1f}:{'✅' if last['C3'] else '❌'} | Super:{'✅' if last['C4'] else '❌'} | EMA50:{'✅' if last['C5'] else '❌'}")
        st.write(f"**Smart:** BOS:{'✅' if last['SM1'] else '❌'} | SAFE:{'✅' if last['SM2'] else '❌'} | FVG:{'✅' if last['SM3'] else '❌'} | VWAP:{'✅' if last['SM4'] else '❌'} | Vol:{'✅' if last['SM5'] else '❌'}")
        
        if int(last['TOTAL'])==10:
            st.success("🔥 10/10 FULL SIGNAL!"); st.balloons()
        elif int(last['TOTAL'])>=8: st.warning(f"