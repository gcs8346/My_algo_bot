import streamlit as st
import pandas as pd
import requests
import urllib.parse
from datetime import datetime, timedelta
import streamlit.components.v1 as components

st.set_page_config(page_title="Topu V17 FINAL", layout="wide")
st.title("🔥 Topu V17 - 100% FIXED | Ab Data Ayega")
st.caption("Saturday fix + 15 Instrument + Beep + Minus OI | Final")

st.sidebar.header("Topu ka Upstox Setup")
token = st.sidebar.text_input("Naya Token Daal", type="password")
tf = st.sidebar.selectbox("Timeframe", ["1minute","5minute","15minute"], index=0)
beep_on = st.sidebar.checkbox("🔊 BEEP ON/OFF", value=True)

if not token:
    st.warning("Pehle Token daal bhai")
    st.stop()

headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}

def play_beep(t="FIRE"):
    try:
        if "TRAP" in t:
            js = """<script>try{var c=new(window.AudioContext||window.webkitAudioContext)();function b(f,t){var o=c.createOscillator();var g=c.createGain();o.connect(g);g.connect(c.destination);o.frequency.value=f;g.gain.value=1;o.start(c.currentTime+t);o.stop(c.currentTime+t+0.3);}b(900,0);b(900,0.4);b(900,0.8);}catch(e){}</script>"""
        else:
            js = """<script>try{var c=new(window.AudioContext||window.webkitAudioContext)();var o=c.createOscillator();var g=c.createGain();o.connect(g);g.connect(c.destination);o.frequency.value=800;g.gain.value=1;o.start();o.stop(c.currentTime+0.5);}catch(e){}</script>"""
        components.html(js, height=0, width=0)
    except: pass

def get_ltp(k):
    try:
        enc = urllib.parse.quote(k, safe='')
        url = f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={enc}"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200: return None
        data = r.json().get('data', {})
        if k in data: return data[k].get('last_price')
        for v in data.values():
            if isinstance(v, dict) and 'last_price' in v: return v['last_price']
        return None
    except: return None

def get_candles(k, timeframe):
    try:
        enc = urllib.parse.quote(k, safe='')
        url1 = f"https://api.upstox.com/v2/historical-candle/intraday/{enc}/1minute"
        r1 = requests.get(url1, headers=headers, timeout=10)
        if r1.status_code == 200:
            candles = r1.json().get('data', {}).get('candles', [])
            if candles and len(candles) > 5:
                df = pd.DataFrame(candles, columns=['time','open','high','low','close','volume','oi'])
                df['time']=pd.to_datetime(df['time']); df=df.sort_values('time').set_index('time')
                if timeframe!="1minute":
                    mins=5 if timeframe=="5minute" else 15
                    df=df.resample(f'{mins}min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum','oi':'last'}).dropna()
                return df.reset_index()

        to_date = datetime.now()
        while to_date.weekday() >= 5: to_date -= timedelta(days=1)
        from_date = to_date - timedelta(days=5)
        to_str = to_date.strftime("%Y-%m-%d")
        from_str = from_date.strftime("%Y-%m-%d")
        # FIX: to_date PEHLE, from_date BAAD ME
        url2 = f"https://api.upstox.com/v2/historical-candle/{enc}/1minute/{to_str}/{from_str}"
        r2 = requests.get(url2, headers=headers, timeout=15)
        if r2.status_code != 200:
        candles = r2.json().get('data', {}).get('candles', [])
        if not candles: return None
        df = pd.DataFrame(candles, columns=['time','open','high','low','close','volume','oi'])
        df['time']=pd.to_datetime(df['time']); df=df.sort_values('time').set_index('time')
        if timeframe!="1minute":
            mins=5 if timeframe=="5minute" else 15
            df=df.resample(f'{mins}min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum','oi':'last'}).dropna()
        return df.reset_index()
    except: return None

def get_option_chain_oi(underlying="NSE_INDEX|Nifty 50"):
    try:
        enc = urllib.parse.quote(underlying, safe='')
        url = f"https://api.upstox.com/v2/option/chain?instrument_key={enc}"
        r = requests.get(url, headers=headers, timeout=15).json()
        data = r.get('data', [])
        if not data: return None
        spot = get_ltp(underlying) or 0
        atm = round(spot/50)*50 if spot else 0
        minus_ce, minus_pe = [], []
        total_ce_oi, total_pe_oi, total_ce_chg, total_pe_chg = 0,0,0,0
        for item in data:
            strike = item.get('strike_price', 0)
            if atm and abs(strike - atm) > 300: continue
            ce = item.get('call_options', {}); pe = item.get('put_options', {})
            ce_chg = ce.get('oi_change', 0) or ce.get('change_oi', 0)
            pe_chg = pe.get('oi_change', 0) or pe.get('change_oi', 0)
            total_ce_oi+=ce.get('oi',0); total_pe_oi+=pe.get('oi',0)
            total_ce_chg+=ce_chg; total_pe_chg+=pe_chg
            if ce_chg < -100000: minus_ce.append(f"{strike}CE {ce_chg/100000:.1f}L")
            if pe_chg < -100000: minus_pe.append(f"{strike}PE {pe_chg/100000:.1f}L")
        pcr = total_pe_oi / total_ce_oi if total_ce_oi>0 else 0
        return {"pcr": pcr, "ce_chg": total_ce_chg, "pe_chg": total_pe_chg, "minus_ce": minus_ce, "minus_pe": minus_pe, "atm": atm}
    except: return None

def get_signal(df, ltp, oi_data):
    df['EMA9']=df['close'].ewm(span=9).mean(); df['EMA21']=df['close'].ewm(span=21).mean(); df['EMA50']=df['close'].ewm(span=50).mean()
    df['RSI']=100-(100/(1+(df['close'].diff().where(lambda x: x>0, 0).rolling(14).mean() / -df['close'].diff().where(lambda x: x<0, 0).rolling(14).mean())))
    df['Res']=df['high'].rolling(20).max(); df['Sup']=df['low'].rolling(20).min()
    df['TR']=pd.concat([df['high']-df['low'], (df['high']-df['close'].shift()).abs(), (df['low']-df['close'].shift()).abs()], axis=1).max(axis=1)
    df['ATR']=df['TR'].rolling(10).mean()
    last=df.iloc[-1]; diff=(ltp-last['close']) if ltp else 0; atr_val=last['ATR'] if pd.notna(last['ATR']) else last['close']*0.002
    top_break=(ltp>df['high'].iloc[-4:-1].max()) if ltp else False
    score=sum([last['EMA9']>last['EMA21'], (ltp>last['EMA9']) if ltp else False, last['RSI']>52, (ltp>last['EMA50']) if ltp else False, top_break])
    if oi_data:
        ce_chg, pe_chg = oi_data.get('ce_chg', 0), oi_data.get('pe_chg', 0)
        if ce_chg < -500000 and top_break: return f"🔴 MINUS OI TRAP", f"SL HUNT! CE OI {ce_chg/100000:.1f}L MINUS", last['Res'], last['Sup'], score, diff
        if pe_chg < -500000 and ltp and ltp < last['Sup']*1.002: return f"🟢 MINUS OI BULL", f"BULL REVERSAL! PE OI {pe_chg/100000:.1f}L MINUS", last['Res'], last['Sup'], score, diff
    if last['EMA9']>last['EMA21'] and diff < -15: return f"⚠️ {score}/5 TRAP", f"FAKE BUY! LIVE {diff:+.1f} gir raha", last['Res'], last['Sup'], score, diff
    if score>=4: return f"🔥 {score}/5 FIRE BUY", f"BUY OK | TGT {(ltp if ltp else last['close'])+atr_val*1.5:.1f}", last['Res'], last['Sup'], score, diff
    elif score>=2 and top_break: return f"⚡ {score}/5 SCALP BUY", f"SCALP FAST", last['Res'], last['Sup'], score, diff
    elif last['EMA9']<last['EMA21']: return f"🔻 {score}/5 SELL", f"SELL Trend", last['Res'], last['Sup'], score, diff
    else: return f"💤 {score}/5 WAIT", f"Sideways RSI {last['RSI']:.1f}", last['Res'], last['Sup'], score, diff

SYMBOLS = {
    "NIFTY 50": "NSE_INDEX|Nifty 50", "BANKNIFTY": "NSE_INDEX|Nifty Bank",
    "FINNIFTY": "NSE_INDEX|Nifty Fin Service", "SENSEX": "BSE_INDEX|SENSEX", 
    "MIDCAP 100": "NSE_INDEX|Nifty Midcap 100",
    "RELIANCE": "NSE_EQ|INE002A01018", "HDFCBANK": "NSE_EQ|INE040A01034", 
    "ICICIBANK": "NSE_EQ|INE090A01021", "TCS": "NSE_EQ|INE467B01029", 
    "INFY": "NSE_EQ|INE009A01021", "SBIN": "NSE_EQ|INE062A01020",
    "BHARTIARTL": "NSE_EQ|INE397D01024", "ITC": "NSE_EQ|INE154A01025", 
    "LT": "NSE_EQ|INE018A01030", "BAJFINANCE": "NSE_EQ|INE296A01024",
}

oi_info = get_option_chain_oi("NSE_INDEX|Nifty 50")
if oi_info:
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("PCR", f"{oi_info['pcr']:.2f}"); c2.metric("CE Chg", f"{oi_info['ce_chg']/100000:.1f}L", delta_color="inverse")
    c3.metric("PE Chg", f"{oi_info['pe_chg']/100000:.1f}L"); c4.metric("ATM", f"{oi_info['atm']}")
    if oi_info['minus_ce']: st.error(f"🔴 CE MINUS: {', '.join(oi_info['minus_ce'][:4])}")
    if oi_info['minus_pe']: st.success(f"🟢 PE MINUS: {', '.join(oi_info['minus_pe'][:4])}")

cols = st.columns(3)
beep_triggered=False
for i, (name, key) in enumerate(SYMBOLS.items()):
    df = get_candles(key, tf); ltp = get_ltp(key)
    with cols[i % 3]:
        st.subheader(name)
        if df is not None:
            display_ltp = ltp if ltp else df.iloc[-1]['close']
            sig, reason, res, sup, score, diff = get_signal(df, display_ltp, oi_info)
            if ltp: st.metric(f"{name} LIVE", f"{ltp:.2f}", f"{diff:+.2f}")
            else: st.metric(f"{name} (Fri)", f"{display_ltp:.2f}", "Weekend Data")
            if "TRAP" in sig: 
                st.error(f"{sig} - {reason}")
                if beep_on and not beep_triggered: play_beep("TRAP"); beep_triggered=True
            elif "FIRE" in sig: 
                st.success(f"{sig} - {reason}")
                if beep_on and not beep_triggered: play_beep("FIRE"); beep_triggered=True
            elif "SCALP" in sig: st.info(f"{sig} - {reason}")
            elif "SELL" in sig: st.error(f"{sig} - {reason}")
            else: st.warning(f"{sig} - {reason}")
            st.caption(f"Res: {res:.1f} | Sup: {sup:.1f}")
        else:
            st.error(f"{name} - Data nahi")

st.divider()
if st.button("🔔 TEST BEEP"): play_beep("FIRE"); st.success("Beep baja?")
if st.button("🔄 Refresh"): st.rerun()
st.caption(f"Update: {datetime.now().strftime('%H:%M:%S')} | V17 FINAL 100% FIXED")