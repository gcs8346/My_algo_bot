import streamlit as st
import pandas as pd
import requests
import urllib.parse
from datetime import datetime, timedelta
import streamlit.components.v1 as components

st.set_page_config(page_title="Topu V17.2 BEEP", layout="wide")
st.title("🔥 Topu V17.2 - BEEP + TRAP + FIRE")
st.caption("App khuli ho toh BEEP bajega | MINUS OI + TRAP")

st.sidebar.header("Topu ka Upstox Setup")
token = st.sidebar.text_input("Upstox Access Token Daal", type="password")
tf = st.sidebar.selectbox("Timeframe", ["1minute", "5minute", "15minute"], index=0)
beep_on = st.sidebar.checkbox("🔊 BEEP ON/OFF", value=True)

if not token:
    st.warning("Token daal bhai")
    st.stop()

headers = {'Authorization': f'Bearer {token}'}

def play_beep(signal_type="FIRE"):
    """Phone me BEEP bajane ka function"""
    # Alag signal ke liye alag beep frequency
    if "TRAP" in signal_type:
        # TRAP ke liye tez 3 beep - danger wala
        js_code = """
        <script>
        try {
            var ctx = new (window.AudioContext || window.webkitAudioContext)();
            function beep(freq, time, vol){
                var o = ctx.createOscillator();
                var g = ctx.createGain();
                o.connect(g); g.connect(ctx.destination);
                o.frequency.value = freq; g.gain.value = vol;
                o.start(ctx.currentTime + time); o.stop(ctx.currentTime + time + 0.3);
            }
            beep(900, 0, 1); beep(900, 0.4, 1); beep(900, 0.8, 1);
        } catch(e){ console.log(e); }
        </script>
        """
    elif "FIRE" in signal_type:
        # FIRE ke liye lambi beep
        js_code = """
        <script>
        try {
            var ctx = new (window.AudioContext || window.webkitAudioContext)();
            function beep(freq, time){
                var o = ctx.createOscillator();
                var g = ctx.createGain();
                o.connect(g); g.connect(ctx.destination);
                o.frequency.value = freq; g.gain.value = 1;
                o.start(ctx.currentTime + time); o.stop(ctx.currentTime + time + 0.5);
            }
            beep(700, 0); beep(1000, 0.6);
        } catch(e){}
        </script>
        <audio autoplay><source src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" type="audio/ogg"></audio>
        """
    else: # SCALP
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
    st.markdown(f"<audio autoplay><source src='https://actions.google.com/sounds/v1/alarms/beep_short.ogg' type='audio/ogg'></audio>", unsafe_allow_html=True)

def get_ltp(k):
    try:
        enc = urllib.parse.quote(k, safe='')
        url = f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={enc}"
        r = requests.get(url, headers=headers, timeout=10).json()
        data = r.get('data', {})
        if k in data:
            return data[k].get('last_price')
        for v in data.values():
            if isinstance(v, dict) and 'last_price' in v:
                return v['last_price']
        return None
    except:
        return None

def get_candles(k, timeframe):
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
    if not candles: return None
    df = pd.DataFrame(candles, columns=['time','open','high','low','close','volume','oi'])
    df['time'] = pd.to_datetime(df['time'])
    df = df.sort_values('time').set_index('time')
    if timeframe != "1minute":
        mins = 5 if timeframe=="5minute" else 15
        df = df.resample(f'{mins}min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum','oi':'last'}).dropna()
    return df.reset_index()

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
    last=df.iloc[-1]; diff=ltp-last['close']; atr_val=last['ATR'] if pd.notna(last['ATR']) else last['close']*0.002
    top_break=ltp>df['high'].iloc[-4:-1].max()
    score=sum([last['EMA9']>last['EMA21'], ltp>last['EMA9'], last['RSI']>52, ltp>last['EMA50'], top_break])
    if oi_data:
        ce_chg, pe_chg = oi_data.get('ce_chg', 0), oi_data.get('pe_chg', 0)
        if ce_chg < -500000 and top_break: return f"🔴 MINUS OI TRAP", f"SL HUNT! CE OI {ce_chg/100000:.1f}L MINUS | Neeche ayega! RES {last['Res']:.1f}", last['Res'], last['Sup'], score, diff
        if pe_chg < -500000 and ltp < last['Sup']*1.002: return f"🟢 MINUS OI BULL", f"BULL REVERSAL! PE OI {pe_chg/100000:.1f}L MINUS", last['Res'], last['Sup'], score, diff
    if last['EMA9']>last['EMA21'] and diff < -15: return f"⚠️ {score}/5 TRAP", f"FAKE BUY! LIVE {diff:+.1f} gir raha | RES {last['Res']:.1f}", last['Res'], last['Sup'], score, diff
    if score>=4: return f"🔥 {score}/5 FIRE BUY", f"BUY OK | TGT {ltp+atr_val*1.5:.1f} | SL {ltp-atr_val*0.8:.1f}", last['Res'], last['Sup'], score, diff
    elif score>=2 and top_break: return f"⚡ {score}/5 SCALP BUY", f"SCALP FAST | TGT {ltp+atr_val*0.8:.1f}", last['Res'], last['Sup'], score, diff
    elif last['EMA9']<last['EMA21']: return f"🔻 {score}/5 SELL", f"SELL Trend | Sup {last['Sup']:.1f}", last['Res'], last['Sup'], score, diff
    else: return f"💤 {score}/5 WAIT", f"Sideways | RSI {last['RSI']:.1f}", last['Res'], last['Sup'], score, diff

SYMBOLS = {
    "NIFTY 50": "NSE_INDEX|Nifty 50", "BANKNIFTY": "NSE_INDEX|Nifty Bank",
    "FINNIFTY": "NSE_INDEX|Nifty Fin Service", "SENSEX": "BSE_INDEX|SENSEX", "MIDCAP": "NSE_INDEX|Nifty Mid Select",
    "RELIANCE": "NSE_EQ|INE002A01018", "HDFCBANK": "NSE_EQ|INE040A01034", "ICICIBANK": "NSE_EQ|INE090A01021",
    "TCS": "NSE_EQ|INE467B01029", "INFY": "NSE_EQ|INE009A01021", "SBIN": "NSE_EQ|INE062A01020",
    "BHARTIARTL": "NSE_EQ|INE397D01024", "ITC": "NSE_EQ|INE154A01025", "LT": "NSE_EQ|INE018A01030", "BAJFINANCE": "NSE_EQ|INE296A01024",
}

oi_info = get_option_chain_oi("NSE_INDEX|Nifty 50")
if oi_info:
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("PCR", f"{oi_info['pcr']:.2f}"); c2.metric("CE Chg", f"{oi_info['ce_chg']/100000:.1f}L", delta_color="inverse")
    c3.metric("PE Chg", f"{oi_info['pe_chg']/100000:.1f}L"); c4.metric("ATM", f"{oi_info['atm']}")
    if oi_info['minus_ce']: st.error(f"🔴 CE MINUS: {', '.join(oi_info['minus_ce'][:4])}")
    if oi_info['minus_pe']: st.success(f"🟢 PE MINUS: {', '.join(oi_info['minus_pe'][:4])}")

# Yahan BEEP trigger hoga
beep_triggered = False
cols = st.columns(3)
for i, (name, key) in enumerate(SYMBOLS.items()):
    df = get_candles(key, tf); ltp = get_ltp(key)
    with cols[i % 3]:
        st.subheader(name)
        if ltp and df is not None:
            sig, reason, res, sup, score, diff = get_signal(df, ltp, oi_info)
            st.metric(f"{name} LIVE", f"{ltp:.2f}", f"{diff:+.2f} vs Candle")
            if "MINUS OI TRAP" in sig or "TRAP" in sig:
                st.error(f"{sig} - {reason}")
                if beep_on and not beep_triggered: play_beep("TRAP"); beep_triggered=True
            elif "FIRE" in sig:
                st.success(f"{sig} - {reason}")
                if beep_on and not beep_triggered: play_beep("FIRE"); beep_triggered=True
            elif "SCALP" in sig:
                st.info(f"{sig} - {reason}")
                if beep_on and not beep_triggered: play_beep("SCALP"); beep_triggered=True
            elif "SELL" in sig: st.error(f"{sig} - {reason}")
            else: st.warning(f"{sig} - {reason}")
            st.caption(f"Res: {res:.1f} | Sup: {sup:.1f}")
        else: st.warning("Data nahi")

# --- BEEP TEST BUTTON ---
st.divider()
st.write("🔊 BEEP TEST:")
if st.button("🔔 TEST BEEP BAJA"):
    play_beep("FIRE")
    st.success("Beep baja? Volume ON hai? Agar nahi baja toh browser me Sound Allow karo!")

st.caption(f"Update: {datetime.now().strftime('%H:%M:%S')} | V17.2 BEEP FINAL")
if st.button("🔄 Refresh"):
    st.rerun()