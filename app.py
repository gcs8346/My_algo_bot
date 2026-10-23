import streamlit as st, requests, pandas as pd, numpy as np
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

st.set_page_config(layout="centered")
st.markdown("## ⚡ TOPU V25 - FINAL LOCK 1 SEC + 5 CHECKLIST")

def play_sound():
    components.html("""<audio autoplay><source src="https://www.soundjay.com/buttons/sounds/beep-07a.mp3" type="audio/mpeg"></audio>""", height=0)

if st.text_input("Token", value="TOPU-2026-TEST", type="password") != "TOPU-2026-TEST": st.stop()
token = st.sidebar.text_input("Upstox Token", type="password")
if not token: st.stop()
sound_on = st.sidebar.checkbox("🔊 Sound ON", True)
speed = st.sidebar.select_slider("Tick Speed", ["3s","1s","0.8s"], value="1s")
interval = {"3s":3000,"1s":1000,"0.8s":800}[speed]
st_autorefresh(interval=interval, key=f"v25_{interval}")

instrument_key="NSE_INDEX|Nifty 50"
headers_up = {'Authorization': f'Bearer {token}'}

try:
    r_ltp=requests.get(f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={instrument_key}", headers=headers_up, timeout=2)
    live=float(list(r_ltp.json()['data'].values())[0]['last_price']) if r_ltp.status_code==200 else 22600.0
except: live=22600.0

@st.cache_data(ttl=1)
def get_candle(live):
    try:
        r=requests.get(f"https://api.upstox.com/v2/historical-candle/intraday/{instrument_key}/1minute", headers=headers_up, timeout=3)
        df=pd.DataFrame(r.json()['data']['candles'][:150], columns=['t','o','h','l','c','v','oi'])
        df=df.sort_values('t').copy()
        df.loc[df.index[-1], 'c']=live
        df['EMA9']=df['c'].ewm(9).mean()
        df['EMA21']=df['c'].ewm(21).mean()
        df['FIDI']=df['c'].ewm(50).mean()
        d=df['c'].diff()
        df['RSI']=100-(100/(1+d.where(d>0,0).ewm(14).mean()/(-d.where(d<0,0)).ewm(14).mean().replace(0,0.001)))
        df['ST']=np.where(df['c']> (df['h']+df['l'])/2 - 3*(df['h']-df['l']).ewm(10).mean(),1,-1)
        return df
    except: return pd.DataFrame()

@st.cache_data(ttl=5)
def get_checklist():
    adv,dec,heat,green,ce_chg,pe_chg,prem,pcr,bias,atm = 5,45,0,0,0,0,"WAIT",1.0,"WAIT",round(live/50)*50
    try:
        s=requests.Session()
        s.headers.update({'User-Agent':'Mozilla/5.0','Referer':'https://www.nseindia.com/option-chain'})
        s.get("https://www.nseindia.com/option-chain", timeout=5)
        r1=s.get("https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050", timeout=4)
        if r1.status_code==200:
            j=r1.json().get('advance',{})
            adv=j.get('advances',0) or j.get('advance',0) or 5
            dec=j.get('declines',0) or j.get('decline',0) or 45
        r2=s.get("https://www.nseindia.com/api/allIndices", timeout=4)
        if r2.status_code==200:
            main=["NIFTY BANK","NIFTY IT","NIFTY AUTO","NIFTY FMCG","NIFTY METAL","NIFTY PHARMA","NIFTY PSU BANK","NIFTY REALTY"]
            for sec in main:
                for it in r2.json().get('data',[]):
                    if it.get('index')==sec and it.get('percentChange',0)>0:
                        green+=1; break
            heat=int(green/len(main)*100)
        r3=s.get("https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY", timeout=5)
        if r3.status_code==200:
            rec=r3.json().get('records',{}).get('data',[])
            near=[x for x in rec if abs(x.get('strikePrice',0)-atm)<=500]
            max_ce=max_pe=0
            ce_s=pe_s=atm
            for it in near:
                ce=it.get('CE',{}).get('changeinOpenInterest',0)
                pe=it.get('PE',{}).get('changeinOpenInterest',0)
                if ce>max_ce: max_ce=ce; ce_s=it['strikePrice']
                if pe>max_pe: max_pe=pe; pe_s=it['strikePrice']
            ce_chg,pe_chg=max_ce,max_pe
            if pe_chg>ce_chg*1.2: bias=f"CALL HEAVY PE {pe_chg} @ {pe_s}"; atm=pe_s
            elif ce_chg>pe_chg*1.2: bias=f"PUT HEAVY CE {ce_chg} @ {ce_s}"; atm=ce_s
            else: bias=f"EQUAL C:{ce_chg} P:{pe_chg}"
        # Premium + PCR
        r4=requests.get(f"https://api.upstox.com/v2/option/chain?instrument_key={instrument_key}&expiry_date=2026-10-30", headers=headers_up, timeout=4)
        if r4.status_code==200 and r4.json().get('data'):
            data=sorted(r4.json()['data'], key=lambda x: abs(x['strike_price']-live))[:10]
            ce_oi=sum([d.get('call_options',{}).get('market_data',{}).get('oi',0) for d in data])
            pe_oi=sum([d.get('put_options',{}).get('market_data',{}).get('oi',0) for d in data])
            ce_v=sum([d.get('call_options',{}).get('market_data',{}).get('volume',0) for d in data])
            pe_v=sum([d.get('put_options',{}).get('market_data',{}).get('volume',0) for d in data])
            pcr=round(pe_oi/ce_oi,2) if ce_oi else 1.0
            if ce_v>pe_v*1.2: prem="CALL ACTIVE"
            elif pe_v>ce_v*1.2: prem="PUT ACTIVE"
            else: prem=f"CALL Vol {int(ce_v)} PUT Vol {int(pe_v)}"
    except: pass
    return adv,dec,heat,green,ce_chg,pe_chg,prem,pcr,bias,atm

df=get_candle(live)
adv,dec,heat,green,ce_chg,pe_chg,prem,pcr,bias,atm = get_checklist()

st.markdown(f"### LIVE ₹{live} | ATM {atm} | {speed} tick")
if not df.empty:
    last=df.iloc[-1]
    mid=(df['h'].max()+df['l'].min())/2
    c1,c2,c3,c4=st.columns(4)
    c1.metric("EMA 9/21", "BULL" if last['EMA9']>last['EMA21'] else "BEAR")
    c2.metric("FIDI 50", "BULL" if live>last['FIDI'] else "BEAR")
    c3.metric(f"RSI {int(last['RSI'])}", "BULL" if last['RSI']>50 else "BEAR")
    c4.metric("Supertrend", "BULL" if last['ST']==1 else "BEAR")

    st.markdown("---")
    st.markdown("**✅ 5 CHECKLIST LOGIC (Aaj ke liye change kiya tha):**")
    colA,colB=st.columns(2)
    colA.metric("1. A/D", f"{adv}/{dec}", "BUY" if adv>dec else "SELL")
    colB.metric("2. Heat Map", f"{heat}% ({green}/8)", "BULL >=50%" if heat>=50 else "BEAR")
    st.info(f"3. Change OI: {bias} | CE:{ce_chg} PE:{pe_chg}")
    st.info(f"4. Premium: {prem} | PCR {pcr} | 5. Mid: {'CALL Heavy' if live>mid else 'PUT Heavy'} (₹{live} vs MID ₹{int(mid)})")

    score = (1 if last['EMA9']>last['EMA21'] else 0)+(1 if live>last['FIDI'] else 0)+(1 if last['RSI']>50 else 0)+(1 if last['ST']==1 else 0)+(1 if live>mid else 0)+(1 if adv>dec else 0)+(1 if heat>=50 else 0)+(1 if pe_chg>ce_chg else 0)+(1 if "CALL" in prem else 0)

    if score>=6:
        st.success(f"🚀 FINAL BUY @ {atm} - Score {score}/9 (5 logic included)")
        if sound_on: play_sound()
    elif score<=3:
        st.error(f"🔻 FINAL SELL @ {atm} - Score {score}/9")
        if sound_on: play_sound()
    else:
        st.warning(f"⏳ WAIT - Score {score}/9 - Checklist dekh")

st.caption("V25 LOCK: Fast 1s ✅ + 5 Checklist ✅ + Sound ✅ - Ab kuch nahi hatayega")