import streamlit as st, requests, pandas as pd, numpy as np
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

st.set_page_config(layout="centered")
st.markdown("## 👑 TOPU V22 - SOUND FINAL")

# Sound function - ye wapas la diya
def play_sound():
    components.html("""
    <audio autoplay>
      <source src="https://www.soundjay.com/buttons/sounds/beep-07a.mp3" type="audio/mpeg">
    </audio>
    <script>setTimeout(()=>{window.parent.document.querySelector('audio')?.play()}, 100)</script>
    """, height=0)

if st.text_input("Token", value="TOPU-2026-TEST", type="password") != "TOPU-2026-TEST": st.stop()

token = st.sidebar.text_input("Upstox Token", type="password")
if not token: st.stop()

# 🔊 Sound ON/OFF - ye checkbox wapas
sound_on = st.sidebar.checkbox("🔊 Sound ON", value=True)
st.sidebar.caption("BUY/SELL pe beep bajega")

headers_up = {'Authorization': f'Bearer {token}'}
st_autorefresh(interval=2500, key="v22_sound")

instrument_key="NSE_INDEX|Nifty 50"

r_ltp=requests.get(f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={instrument_key}", headers=headers_up, timeout=4)
live=float(list(r_ltp.json()['data'].values())[0]['last_price']) if r_ltp.status_code==200 else 22600.0

def get_candle():
    try:
        r=requests.get(f"https://api.upstox.com/v2/historical-candle/intraday/{instrument_key}/1minute", headers=headers_up, timeout=5)
        if r.status_code==200:
            df=pd.DataFrame(r.json()['data']['candles'], columns=['t','o','h','l','c','v','oi'])
            df=df.sort_values('t').copy()
            df.loc[df.index[-1], 'c']=live
            df['EMA9']=df['c'].ewm(9).mean()
            df['EMA21']=df['c'].ewm(21).mean()
            df['FIDI']=df['c'].ewm(50).mean()
            delta=df['c'].diff()
            gain=delta.where(delta>0,0).ewm(14).mean()
            loss=(-delta.where(delta<0,0)).ewm(14).mean()
            df['RSI']=100 - (100/(1+gain/loss.replace(0,0.001)))
            df['hl2']=(df['h']+df['l'])/2
            df['tr']=np.maximum(df['h']-df['l'], np.maximum(abs(df['h']-df['c'].shift(1)), abs(df['l']-df['c'].shift(1))))
            df['atr']=df['tr'].ewm(10).mean()
            df['ST_dir']=np.where(df['c']>(df['hl2']+3*df['atr']).shift(1), -1, 1) # simplified
            df['ST_dir']=np.where(df['c']>(df['hl2']-3*df['atr']).shift(1), 1, df['ST_dir'])
            return df
    except: pass
    return pd.DataFrame()

df=get_candle()

# Default score
score=0
signal="WAIT"
if not df.empty:
    last=df.iloc[-1]
    ema_bull=last['EMA9']>last['EMA21']
    fidi_bull=live>last['FIDI']
    rsi_val=float(last['RSI'])
    st_bull=last['ST_dir']==1
    mid=(df['h'].max()+df['l'].min())/2

    c1,c2,c3,c4=st.columns(4)
    c1.metric("EMA 9/21", "BULL" if ema_bull else "BEAR")
    c2.metric("FIDI 50", "BULL" if fidi_bull else "BEAR")
    c3.metric(f"RSI {int(rsi_val)}", "BULL" if rsi_val>50 else "BEAR")
    c4.metric("Supertrend", "BULL" if st_bull else "BEAR")

    st.info(f"MID {int(mid)} | LIVE ₹{live} => {'CALL Heavy' if live>mid else 'PUT Heavy'}")

    score = (1 if ema_bull else 0) + (1 if fidi_bull else 0) + (1 if rsi_val>50 else 0) + (1 if st_bull else 0) + (1 if live>mid else 0)
    
    if score>=4:
        signal="BUY"
        st.success(f"🚀 FINAL BUY CALL - Score {score}/5")
        if sound_on: play_sound()
    elif score<=1:
        signal="SELL"
        st.error(f"🔻 FINAL SELL PUT - Score {score}/5")
        if sound_on: play_sound()
    else:
        st.warning(f"⏳ WAIT - Score {score}/5")

# Test sound button
if st.button("🔊 Sound Test Karo"):
    play_sound()
    st.toast("Beep baja? Agar nahi baja to browser me volume check karo")

st.caption("V22 me: EMA ✅ Supertrend ✅ RSI ✅ FIDI ✅ MID ✅ + Sound ✅ - Kal se yahi chalana")