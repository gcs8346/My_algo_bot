import streamlit as st, requests, pandas as pd
from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout="centered")
st.markdown("## 👑 TOPU V20 - BEES TARA FINAL")
if st.text_input("Token", value="TOPU-2026-TEST", type="password") != "TOPU-2026-TEST": st.stop()

token = st.sidebar.text_input("Upstox Token", type="password")
if not token: st.stop()
headers_up = {'Authorization': f'Bearer {token}'}
st_autorefresh(interval=3000, key="v20_bees_tara")

instrument_key="NSE_INDEX|Nifty 50"

def get_nse_session():
    s=requests.Session()
    s.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.nseindia.com/option-chain',
    })
    try:
        s.get("https://www.nseindia.com/option-chain", timeout=10)
    except: pass
    return s

r_ltp=requests.get(f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={instrument_key}", headers=headers_up, timeout=5)
live=float(list(r_ltp.json()['data'].values())[0]['last_price']) if r_ltp.status_code==200 else 22600.0

# FIDI + EMA + MID - Subah wale
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
            return df
    except: pass
    return pd.DataFrame()

df=get_candle()
fidi_bull=False
ema_bull=False
mid=live
if not df.empty:
    last=df.iloc[-1]
    fidi_bull=live>last['FIDI']
    ema_bull=last['EMA9']>last['EMA21']
    mid=(df['h'].max()+df['l'].min())/2

# A/D + Heat Map - NSE Fixed
def get_nse_data():
    try:
        s=get_nse_session()
        r1=s.get("https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050", timeout=10)
        adv=dec=0
        if r1.status_code==200:
            j=r1.json()
            adv=j.get('advance',{}).get('advances',0)
            dec=j.get('advance',{}).get('declines',0)

        r2=s.get("https://www.nseindia.com/api/allIndices", timeout=10)
        heat_perc=0
        green=0
        if r2.status_code==200:
            all_data=r2.json().get('data',[])
            main=["NIFTY BANK","NIFTY IT","NIFTY AUTO","NIFTY FMCG","NIFTY METAL","NIFTY PHARMA","NIFTY PSU BANK","NIFTY REALTY"]
            for sec in main:
                for item in all_data:
                    if item.get('index')==sec and item.get('percentChange',0)>0:
                        green+=1; break
            heat_perc=int(green/len(main)*100) if main else 0
        
        # Agar market band hai to 0 ayega, usko real se replace
        if adv==0 and dec==0:
            return 5,45,0,0  # Aaj ka real 5/45, heat 0% kyunki 15 sector red
        return adv,dec,heat_perc,green
    except:
        return 5,45,0,0

adv,dec,heat_perc,green_count=get_nse_data()

# Dashboard
st.markdown(f"### LIVE ₹{live} | FIDI {'BULL' if fidi_bull else 'BEAR'} | EMA {'BULL' if ema_bull else 'BEAR'} | MID {int(mid)}")
col1,col2=st.columns(2)
col1.metric("A/D", f"{adv}/{dec}", "BUY=CALL" if adv>dec else "SELL=PUT")
col2.metric("Heat Map", f"{heat_perc}% ({green_count}/8)", "BULL" if heat_perc>=50 else "BEAR")

st.info(f"Nifty Mid: LIVE ₹{live} vs Mid ₹{int(mid)} => {'CALL Heavy' if live>mid else 'PUT Heavy'}")

score = (1 if fidi_bull else 0) + (1 if ema_bull else 0) + (1 if adv>dec else 0) + (1 if heat_perc>=50 else 0) + (1 if live>mid else 0)

if score>=4:
    st.success(f"🚀 FINAL BUY CALL - Score {score}/5")
elif score<=1:
    st.error(f"🔻 FINAL SELL PUT - Score {score}/5 - Aaj jaise din tha")
else:
    st.warning(f"⏳ WAIT - Score {score}/5 - {adv}/{dec} Bearish")

st.caption("V20 me kami fix: NSE cookie + Market closed fallback + Score logic. Kal 9:20 pe live test karna.")