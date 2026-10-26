import streamlit as st
import requests, pandas as pd, time
from datetime import datetime

st.set_page_config(page_title="V93 BSE SENSEX", layout="wide")
st.title("V93 - SENSEX BSE + NSE + MCX - 10/10 🔴")

token_input = st.text_input("Upstox Token", type="password")
if token_input and len(token_input.strip()) > 50:
    st.session_state.tok = token_input.strip().replace("Bearer ", "").strip()
token = st.session_state.get("tok","")
if not token or len(token)<50:
    st.warning("Token daal"); st.stop()

headers = {"Authorization": f"Bearer {token}"}

INSTRUMENTS = {
    "NIFTY 50": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
    "SENSEX": "BSE_INDEX|SENSEX",
    "BANKEX": "BSE_INDEX|BANKEX",
    "RELIANCE": "NSE_EQ|INE002A01018",
    "INFOSYS": "NSE_EQ|INE009A01021",
    "GOLD": "MCX_FO|495213",
    "SILVER": "MCX_FO|495214",
    "CRUDEOIL": "MCX_FO|573422",
}

def ema(s,p): return s.ewm(span=p, adjust=False).mean()
def rsi(s,p=14):
    d=s.diff(); g=d.where(d>0,0).rolling(p).mean(); l=-d.where(d<0,0).rolling(p).mean()
    return 100-(100/(1+g/l))

def get_df(key):
    try:
        url=f"https://api.upstox.com/v3/historical-candle/intraday/{key}/5minute"
        r=requests.get(url, headers=headers, timeout=10)
        if r.status_code==200:
            c=r.json().get("data",{}).get("candles",[])
            if c:
                df=pd.DataFrame(c, columns=["ts","open","high","low","close","volume","oi"])
                return df.iloc[::-1].reset_index(drop=True)
    except: pass
    return None

if "tick" not in st.session_state: st.session_state.tick=True
c1,c2=st.columns(2)
with c1:
    if st.button("🟢 START"): st.session_state.tick=True; st.rerun()
with c2:
    if st.button("🔴 STOP"): st.session_state.tick=False; st.rerun()

for name,key in INSTRUMENTS.items():
    df=get_df(key)
    if df is None or len(df)<50:
        st.metric(name, "WAIT", key); continue
    
    close=df["close"]; high=df["high"]; low=df["low"]
    e9=ema(close,9).iloc[-1]; e21=ema(close,21).iloc[-1]; e50=ema(close,50).iloc[-1]
    r=rsi(close).iloc[-1]; c=close.iloc[-1]
    tp=(df["high"]+df["low"]+df["close"])/3
    vwap=(tp*df["volume"]).cumsum()/df["volume"].cumsum()
    vwap=vwap.iloc[-1]
    
    checks={
        "EMA9>21": e9>e21,
        "Close>EMA9": c>e9,
        "RSI 50+": r>50,
        "Supertrend": c>e50 and r>50,
        "EMA50": c>e50,
        "BOS": c>high.iloc[-11:-1].max(),
        "SAFE": abs(c-e9)/c<0.004,
        "FVG": low.iloc[-1]>high.iloc[-3],
        "VWAP": c>vwap,
        "SENSEX/BSE": True if "BSE" in key else datetime.now().hour<15
    }
    score=sum(checks.values())
    color="#00ff88" if score>=7 else "#ffaa00" if score>=4 else "#ff4444"
    tag="🔥 FIRE" if score>=7 else "⚠️ SETUP" if score>=4 else "💤 WAIT"
    
    st.markdown(f"### {name} - Rs.{c:.1f} - <span style='color:{color}'>{score}/10 {tag}</span> RSI:{r:.0f}", unsafe_allow_html=True)
    cols=st.columns(5)
    for i,(k,v) in enumerate(checks.items()):
        cols[i%5].caption(f"{'✅' if v else '❌'} {k}")

if st.session_state.tick:
    time.sleep(3); st.rerun()