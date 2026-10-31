import streamlit as st
import pandas as pd
import requests
import urllib.parse
from datetime import datetime, timedelta
import streamlit.components.v1 as components

st.set_page_config(page_title="Topu V17 FINAL FIXED", layout="wide")
st.title("🔥 Topu V17 FINAL - BEEP + 15 INSTRUMENT + FIXED")
st.caption("Saturday ko bhi Friday ka data dikhayega | Monday ko auto LIVE | 100% Final")

st.sidebar.header("Topu ka Upstox Setup")
token = st.sidebar.text_input("Upstox Access Token Daal (Roz ka naya)", type="password")
tf = st.sidebar.selectbox("Timeframe", ["1minute", "5minute", "15minute"], index=0)
beep_on = st.sidebar.checkbox("🔊 BEEP ON/OFF", value=True)

if not token:
    st.warning("Pehle Upstox ka naya Access Token daal bhai")
    st.stop()

headers = {'Authorization': f'Bearer {token}'}

def play_beep(signal_type="FIRE"):
    try:
        if "TRAP" in signal_type:
            js_code = """
            <script>
            try {
                var ctx = new (window.AudioContext || window.webkitAudioContext)();
                function beep(freq, time, vol){
                    var o = ctx.createOscillator(); var g = ctx.createGain();
                    o.connect(g); g.connect(ctx.destination);
                    o.frequency.value = freq; g.gain.value = vol;
                    o.start(ctx.currentTime + time); o.stop(ctx.currentTime + time + 0.3);
                }
                beep(900, 0, 1); beep(900, 0.4, 1); beep(900, 0.8, 1);
            } catch(e){}
            </script>
            """
        elif "FIRE" in signal_type:
            js_code = """
            <script>
            try {
                var ctx = new (window.AudioContext || window.webkitAudioContext)();
                function beep(freq, time){
                    var o = ctx.createOscillator(); var g = ctx.createGain();
                    o.connect(g); g.connect(ctx.destination);
                    o.frequency.value = freq; g.gain.value = 1;
                    o.start(ctx.currentTime + time); o.stop(ctx.currentTime + time + 0.5);
                }
                beep(700, 0); beep(1000, 0.6);
            } catch(e){}
            </script>
            """
        else:
            js_code = """
            <script>
            try {
                var ctx = new (window.AudioContext || window.webkitAudioContext)();
                var o = ctx.createOscillator(); var g = ctx.createGain();
                o.connect(g); g.connect(ctx.destination);
                o.frequency.value = 600; g.gain.value = 1;
                o.start(); o.stop(ctx.currentTime + 0.2);
            } catch(e){}
            </script>
            """
        components.html(js_code, height=0, width=0)
    except:
        pass

# ========= YAHI HAI FIXED WALA FUNCTION - 100% =========
def get_ltp(k):
    try:
        enc = urllib.parse.quote(k, safe='')
        url = f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={enc}"
        h = {**headers, 'Accept': 'application/json'}
        r = requests.get(url, headers=h, timeout=10)
        if r.status_code != 200:
            # print(r.text) # Debug
            return None
        rj = r.json()
        data = rj.get('data', {})
        if k in data:
            return data[k].get('last_price')
        for v in data.values():
            if isinstance(v, dict) and 'last_price' in v:
                return v['last_price']
        return None
    except:
        return None

def get_candles(k, timeframe):
    try:
        enc = urllib.parse.quote(k, safe='')
        h = {**headers, 'Accept': 'application/json'}
        
        # STEP 1: Pehle LIVE Intraday try karo (Monday-Friday ko yahan se milega)
        url1 = f"https://api.upstox.com/v2/historical-candle/intraday/{enc}/1minute"
        r1 = requests.get(url1, headers=h, timeout=10)
        if r1.status_code == 200:
            candles = r1.json().get('data', {}).get('candles', [])
            if candles and len(candles) > 5:
                df = pd.DataFrame(candles, columns=['time','open','high','low','close','volume','oi'])
                df['time'] = pd.to_datetime(df['time'])
                df = df.sort_values('time').set_index('time')
                if timeframe != "1minute":
                    mins = 5 if timeframe=="5minute" else 15
                    df = df.resample(f'{mins}min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum','oi':'last'}).dropna()
                return df.reset_index()

        # STEP 2: Agar Intraday khali hai (Saturday jaise aaj) toh Last Working Day ka lo
        to_date = datetime.now()
        while to_date.weekday() >= 5: # 5=Sat, 6=Sun ko Friday pe le jao
            to_date -= timedelta(days=1)
        from_date = to_date - timedelta(days=3)
        to_str = to_date.strftime("%Y-%m-%d")
        from_str = from_date.strftime("%Y-%m-%d")
        
        url2 = f"https://api.upstox.com/v2/historical-candle/{enc}/1minute/{from_str}/{to_str}"
        r2 = requests.get(url2, headers=h, timeout=15)
        if r2.status_code != 200:
            return None
        candles = r2.json().get('data', {}).get('candles', [])
        if not candles:
            return None
        df = pd.DataFrame(candles, columns=['time','open','high','low','close','volume','oi'])
        df['time'] = pd.to_datetime(df['time'])
        df = df.sort_values('time').set_index('time')
        if timeframe != "1minute":
            mins = 5 if timeframe=="5minute" else 15
            df = df.resample(f'{mins}min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum','oi':'last'}).dropna()
        return df.reset_index()
    except Exception as e:
        return None

def get_option_chain_oi(underlying="NSE_INDEX|Nifty 50"):
    try:
        enc = urllib.parse.quote(underlying, safe='')
        url = f"https://api.upstox.com/v2/option/chain?instrument_key={enc}"
        h = {**headers, 'Accept': 'application/json'}
        r = requests.get(url, headers=h, timeout=15).json()
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
    last=df.iloc[-1]; diff=ltp-last['close'] if ltp else 0; atr_val=last['ATR'] if pd.notna(last['ATR']) else last['close']*0.002
    top_break=ltp>df['high'].iloc[-4:-1].max() if ltp else False
    score=sum([last['EMA9']>last['EMA21'], ltp>last['EMA9'] if ltp else False, last['RSI']>52, ltp>last['EMA50'] if ltp else False, top_break])
    if oi_data:
        ce_chg, pe_chg = oi_data.get('ce_chg', 0), oi_data.get('pe_chg', 0)
        if ce_chg < -500000 and top_break: return f"🔴 MINUS OI TRAP", f"SL HUNT! CE OI {ce_chg/100000:.1f}L MINUS | Neeche ayega! RES {last['Res']:.1f}", last['Res'], last['Sup'], score,