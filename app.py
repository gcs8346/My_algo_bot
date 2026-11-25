# pip install streamlit-autorefresh

import streamlit as st
import pandas as pd
import requests
import urllib.parse
from datetime import datetime, timedelta
import streamlit.components.v1 as components

st.set_page_config(page_title="Topu V18 MAKHAN", layout="wide")

# AUTO REFRESH FIX - V18
try:
    from streamlit_autorefresh import st_autorefresh
    auto_refresh = st.sidebar.checkbox("⚡ Auto-Refresh LIVE", value=True)
    refresh_sec = st.sidebar.slider("Refresh Sec", 2, 30, 5)
    if auto_refresh:
        st_autorefresh(interval=refresh_sec*1000, key="v18_autorefresh")
except:
    st.sidebar.warning("pip install streamlit-autorefresh")
    auto_refresh = False

if 'price_history' not in st.session_state:
    st.session_state.price_history = {}
if 'avg_entries' not in st.session_state:
    st.session_state.avg_entries = []

st.title("🔥 Topu V18 - MAKHAN | Auto-Refresh + OI Meter + Torture Alert + 3 Batti")

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
        if "TRAP" in t or "TORTURE" in t:
            js = """<script>try{var c=new(window.AudioContext||window.webkitAudioContext)();function b(f,t){var o=c.createOscillator();var g=c.createGain();o.connect(g);g.connect(c.destination);o.frequency.value=f;g.gain.value=1;o.start(c.currentTime+t);o.stop(c.currentTime+t+0.3);}b(900,0);b(900,0.4);b(900,0.8);b(400,1.2);}catch(e){}</script>"""
        else:
            js = """<script>try{var c=new(window.AudioContext||window.webkitAudioContext)();var o=c.createOscillator();var g=c.createGain();o.connect(g);g.connect(c.destination);o.frequency.value=800;g.gain.value=1;o.start();o.stop(c.currentTime+0.5);}catch(e){}</script>"""
        components.html(js, height=0, width=0)
    except: pass

def get_ltp(k):
    try:
        enc = urllib.parse.quote(k, safe='')
        url = f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={enc}"
        r = requests.get(url, headers=headers, timeout=10)
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
            if candles and len(candles) > 2:
                df = pd.DataFrame(candles, columns=['time','open','high','low','close','volume','oi'])
                df['time']=pd.to_datetime(df['time'])
                df=df.sort_values('time').set_index('time')
                if timeframe!="1minute":
                    mins=5 if timeframe=="5minute" else 15
                    df=df.resample(f'{mins}min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum','oi':'last'}).dropna()
                return df.reset_index()
        to_date = datetime.now()
        while to_date.weekday() >= 5: to_date -= timedelta(days=1)
        from_date = to_date - timedelta(days=5)
        url2 = f"https://api.upstox.com/v2/historical-candle/{enc}/1minute/{to_date.strftime('%Y-%m-%d')}/{from_date.strftime('%Y-%m-%d')}"
        r2 = requests.get(url2, headers=headers, timeout=15)
        candles = r2.json().get('data', {}).get('candles', [])
        if not candles: return None
        df = pd.DataFrame(candles, columns=['time','open','high','low','close','volume','oi'])
        df['time']=pd.to_datetime(df['time'])
        df=df.sort_values('time').set_index('time')
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
            if atm and abs(strike - atm) > 500: continue
            ce = item.get('call_options', {}); pe = item.get('put_options', {})
            ce_chg = ce.get('oi_change', 0) or ce.get('change_oi', 0)
            pe_chg = pe.get('oi_change', 0) or pe.get('change_oi', 0)
            total_ce_oi+=ce.get('oi',0); total_pe_oi+=pe.get('oi',0)
            total_ce_chg+=ce_chg; total_pe_chg+=pe_chg
            if ce_chg < -100000: minus_ce.append(f"{strike}CE {ce_chg/100000:.1f}L")
            if pe_chg < -100000: minus_pe.append(f"{strike}PE {pe_chg/100000:.1f}L")
        pcr = total_pe_oi / total_ce_oi if total_ce_oi>0 else 0
        return {"pcr": pcr, "ce_chg": total_ce_chg, "pe_chg": total_pe_chg, "minus_ce": minus_ce, "minus_pe": minus_pe, "atm": atm, "total_ce": total_ce_oi, "total_pe": total_pe_oi}
    except: return None

# ============ NAYA - 3 BATTI CHECKLIST ============
def get_3batti(df, df15, ltp):
    # Default - sab RED
    b1 = False; b2 = False; b3 = False
    b1_txt = "Data nahi"; b2_txt = "Data nahi"; b3_txt = "Data nahi"
    try:
        if df is not None and len(df) >= 6 and ltp:
            # BATTI 1 - Upar uth raha hai?
            # LTP pichli 3 candle ke close se upar hai?
            last3_close = df['close'].iloc[-3:].max()
            last_low = df['low'].iloc[-1]
            # Aur LTP neeche se upar uth raha hai - last candle ka low se upar
            if ltp > last3_close or (ltp > df['close'].iloc[-2] and ltp > df['close'].iloc[-3]):
                b1 = True; b1_txt = f"Uth raha hai LTP {ltp:.1f} > {last3_close:.1f}"
            else:
                b1 = False; b1_txt = f"Atka hai LTP {ltp:.1f} < {last3_close:.1f}"

            # BATTI 2 - Pehla Low bacha hai?
            # Pichle 10 candle ka sabse neeche wala Low
            prev_low = df['low'].iloc[-11:-1].min() if len(df) >= 11 else df['low'].iloc[:-1].min()
            curr_low = df['low'].iloc[-1]
            if curr_low >= prev_low - 0.5:  # Low toda nahi
                b2 = True; b2_txt = f"Low Bacha {curr_low:.1f} >= {prev_low:.1f}"
            else:
                b2 = False; b2_txt = f"Low Toota {curr_low:.1f} < {prev_low:.1f}"
        if df15 is not None and len(df15) >= 2:
            # BATTI 3 - 15 min batti Hari hai?
            # Last CLOSED 15min candle - agar last wali abhi chal rahi hai to usse pehle wali lo
            last15 = df15.iloc[-1]
            # Agar last candle ka close > open to Hari
            if last15['close'] > last15['open']:
                b3 = True; b3_txt = f"15min Hari {last15['close']:.1f} > {last15['open']:.1f}"
            else:
                b3 = False; b3_txt = f"15min Laal {last15['close']:.1f} < {last15['open']:.1f}"
    except:
        pass
    return (b1, b1_txt), (b2, b2_txt), (b3, b3_txt)

def get_signal(df, ltp, oi_data):
    if df is None or len(df) < 2: return f"💤 WAIT", f"Data kam hai", 0, 0, 0, 0
    df['EMA9']=df['close'].ewm(span=9).mean(); df['EMA21']=df['close'].ewm(span=21).mean(); df['EMA50']=df['close'].ewm(span=50).mean()
    delta = df['close'].diff(); gain = delta.where(delta>0, 0).rolling(14).mean(); loss = -delta.where(delta<0, 0).rolling(14).mean()
    rs = gain / loss.replace(0, 0.001); df['RSI'] = 100 - (100/(1+rs)); df['RSI'] = df['RSI'].fillna(50)
    df['Res']=df['high'].rolling(5).max(); df['Sup']=df['low'].rolling(5).min()
    df['TR']=pd.concat([df['high']-df['low'], (df['high']-df['close'].shift()).abs(), (df['low']-df['close'].shift()).abs()], axis=1).max(axis=1)
    df['ATR']=df['TR'].rolling(10).mean().fillna(df['close']*0.002)
    last=df.iloc[-1]; diff=(ltp-last['close']) if ltp else 0; atr_val=last['ATR'] if pd.notna(last['ATR']) else last['close']*0.002
    top_break=(ltp>df['high'].iloc[-4:-1].max()) if len(df)>=4 and ltp else False
    e9 = last['EMA9'] if pd.notna(last['EMA9']) else last['close']; e21 = last['EMA21'] if pd.notna(last['EMA21']) else last['close']
    e50 = last['EMA50'] if pd.notna(last['EMA50']) else last['close']; rsi_val = last['RSI'] if pd.notna(last['RSI']) else 50
    score=sum([e9>e21, (ltp>e9) if ltp else False, rsi_val>52, (ltp>e50) if ltp else False, top_break])
    res_val = last['Res'] if pd.notna(last['Res']) else last['high']; sup_val = last['Sup'] if pd.notna(last['Sup']) else last['low']
    if oi_data:
        ce_chg=oi_data.get('ce_chg',0); pe_chg=oi_data.get('pe_chg',0)
        if ce_chg < -500000 and top_break: return f"🔴 MINUS OI TRAP", f"SL HUNT! CE OI {ce_chg/100000:.1f}L MINUS", res_val, sup_val, score, diff
        if pe_chg < -500000 and ltp and ltp < sup_val*1.002: return f"🟢 MINUS OI BULL", f"BULL REVERSAL! PE OI {pe_chg/100000:.1f}L MINUS", res_val, sup_val, score, diff
    if e9>e21 and diff < -15: return f"⚠️ {score}/5 TRAP", f"FAKE BUY! LIVE {diff:+.1f} gir raha", res_val, sup_val, score, diff
    if score>=4: return f"🔥 {score}/5 FIRE BUY", f"BUY OK | TGT {(ltp if ltp else last['close'])+atr_val*1.5:.1f}", res_val, sup_val, score, diff
    elif score>=2 and top_break: return f"⚡ {score}/5 SCALP BUY", f"SCALP FAST", res_val, sup_val, score, diff
    elif e9<e21: return f"🔻 {score}/5 SELL", f"SELL Trend", res_val, sup_val, score, diff
    else: return f"💤 {score}/5 WAIT", f"Sideways RSI {rsi_val:.1f}", res_val, sup_val, score, diff

def check_torture(symbol, ltp):
    now = datetime.now()
    if symbol not in st.session_state.price_history: st.session_state.price_history[symbol] = []
    st.session_state.price_history[symbol].append((now, ltp))
    st.session_state.price_history[symbol] = [(t,p) for t,p in st.session_state.price_history[symbol] if (now-t).seconds < 1200]
    if len(st.session_state.price_history[symbol]) < 3: return False, 0
    prices = [p for _,p in st.session_state.price_history[symbol]]
    if max(prices) - min(prices) < (ltp * 0.001):
        duration = (now - st.session_state.price_history[symbol][0][0]).seconds // 60
        if duration >= 12: return True, duration
    return False, 0

SYMBOLS = {"NIFTY 50": "NSE_INDEX|Nifty 50","BANKNIFTY": "NSE_INDEX|Nifty Bank","FINNIFTY": "NSE_INDEX|Nifty Fin Service","SENSEX": "BSE_INDEX|SENSEX","MIDCAP 100": "NSE_INDEX|Nifty Midcap 100","RELIANCE": "NSE_EQ|INE002A01018","HDFCBANK": "NSE_EQ|INE040A01034","ICICIBANK": "NSE_EQ|INE090A01021","TCS": "NSE_EQ|INE467B01029","INFY": "NSE_EQ|INE009A01021","SBIN": "NSE_EQ|INE062A01020","BHARTIARTL": "NSE_EQ|INE397D01024","ITC": "NSE_EQ|INE154A01025","LT": "NSE_EQ|INE018A01030","BAJFINANCE": "NSE_EQ|INE296A01024"}

st.subheader("📊 OI LIVE METER - V18")
oi_info = get_option_chain_oi("NSE_INDEX|Nifty 50")
if oi_info:
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("PCR", f"{oi_info['pcr']:.2f}", delta=f"{'BULL' if oi_info['pcr']>1 else 'BEAR'}")
    c2.metric("CE OI", f"{oi_info['total_ce']/10000000:.2f}Cr"); c3.metric("PE OI", f"{oi_info['total_pe']/10000000:.2f}Cr")
    c4.metric("CE Chg", f"{oi_info['ce_chg']/100000:.1f}L", delta_color="inverse"); c5.metric("PE Chg", f"{oi_info['pe_chg']/100000:.1f}L")
    total = oi_info['total_ce'] + oi_info['total_pe']
    if total>0:
        pe_pct = oi_info['total_pe']/total*100; ce_pct = oi_info['total_ce']/total*100
        st.progress(int(pe_pct), text=f"PE OI {pe_pct:.1f}% | CE OI {ce_pct:.1f}% | PCR {oi_info['pcr']:.2f}")
    col1, col2 = st.columns(2)
    with col1:
        if oi_info['minus_ce']: st.error(f"🔴 CE MINUS: {', '.join(oi_info['minus_ce'][:4])}")
    with col2:
        if oi_info['minus_pe']: st.success(f"🟢 PE MINUS: {', '.join(oi_info['minus_pe'][:4])}")

with st.expander("🧮 Auto Average Calculator - V18"):
    c1,c2,c3 = st.columns(3)
    with c1: qty = st.number_input("Quantity", min_value=1, value=15)
    with c2: price = st.number_input("Entry Price", min_value=0.0, value=0.0)
    with c3:
        if st.button("Add Entry"):
            if price>0: st.session_state.avg_entries.append((qty, price))
    if st.session_state.avg_entries:
        df_avg = pd.DataFrame(st.session_state.avg_entries, columns=['Qty','Price'])
        df_avg['Total'] = df_avg['Qty']*df_avg['Price']
        total_qty = df_avg['Qty'].sum()
        avg_price = df_avg['Total'].sum()/total_qty if total_qty>0 else 0
        st.dataframe(df_avg, use_container_width=True)
        st.metric("Average Price", f"{avg_price:.2f}", f"Total Qty {total_qty}")
        if st.button("Clear All"): st.session_state.avg_entries = []

cols = st.columns(3)
beep_triggered=False; torture_alerts = []
for i, (name, key) in enumerate(SYMBOLS.items()):
    df = get_candles(key, tf); ltp = get_ltp(key)
    # 15min data sirf 3-batti ke liye - agar tf pehle se 15min hai to wahi use karo
    df15 = df if tf == "15minute" else get_candles(key, "15minute")
    with cols[i % 3]:
        st.subheader(name)
        if df is not None and ltp:
            is_torture, mins = check_torture(name, ltp)
            if is_torture:
                torture_alerts.append(f"{name} {mins}min"); st.warning(f"😫 TORTURE {mins}min - Range me atka!")
                if beep_on and not beep_triggered: play_beep("TORTURE"); beep_triggered=True
            sig, reason, res, sup, score, diff = get_signal(df, ltp, oi_info)
            st.metric(f"{name} LIVE", f"{ltp:.2f}", f"{diff:+.2f}")
            if "TRAP" in sig: st.error(f"{sig} - {reason}"); 
            elif "FIRE" in sig: st.success(f"{sig} - {reason}")
            elif "SCALP" in sig: st.info(f"{sig} - {reason}")
            elif "SELL" in sig: st.error(f"{sig} - {reason}")
            else: st.warning(f"{sig} - {reason}")
            st.caption(f"Res: {res:.1f} | Sup: {sup:.1f}")

            # ===== 3 BATTI CHECKLIST - NAYA =====
            (b1, b1_txt), (b2, b2_txt), (b3, b3_txt) = get_3batti(df, df15, ltp)
            st.markdown("**🚦 3 Batti Checklist - Trap ya Asli?**")
            c_b1, c_b2, c_b3 = st.columns(3)
            c_b1.markdown(f"{'🟢' if b1 else '🔴'} **Upar Uth?**")
            c_b1.caption(b1_txt)
            c_b2.markdown(f"{'🟢' if b2 else '🔴'} **Low Bacha?**")
            c_b2.caption(b2_txt)
            c_b3.markdown(f"{'🟢' if b3 else '🔴'} **15min Hari?**")
            c_b3.caption(b3_txt)
            if b1 and b2 and b3:
                st.success("✅ TEENO GREEN - ENTRY LE LE")
                if beep_on and not beep_triggered: play_beep("FIRE"); beep_triggered=True
            else:
                st.error(f"❌ NO ENTRY - {3 - sum([b1,b2,b3])} Batti RED hai - WAIT KAR")

if torture_alerts: st.error(f"🚨 TORTURE ALERT: {', '.join(torture_alerts)}")
st.divider()
c1,c2,c3 = st.columns(3)
with c1:
    if st.button("🔔 TEST BEEP"): play_beep("FIRE"); st.success("Beep baja?")
with c2:
    if st.button("🔄 Refresh Now"): st.rerun()
with c3:
    if st.button("🗑️ Clear Torture History"): st.session_state.price_history = {}; st.success("Cleared!")
st.caption(f"Update: {datetime.now().strftime('%H:%M:%S')} | V18 MAKHAN - AutoRefresh {'ON' if auto_refresh else 'OFF'} + 3 Batti")