import streamlit as st, requests, pandas as pd
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

st.set_page_config(layout="centered")
st.markdown("## 👑 TOPU V17 - ALL IN ONE")
if st.text_input("Token", value="TOPU-2026-TEST", type="password") != "TOPU-2026-TEST": st.stop()

token = st.sidebar.text_input("Upstox Token", type="password")
if not token: st.stop()
headers = {'Authorization': f'Bearer {token}'}
st_autorefresh(interval=2000, key="v17_all")
sound_on=st.sidebar.checkbox("🔊 Sound ON", True)

def play_sound():
    components.html("""<audio autoplay><source src="https://www.soundjay.com/buttons/sounds/beep-07a.mp3"></audio>""", height=0)

instrument_key="NSE_INDEX|Nifty 50"
@st.cache_data(ttl=3600)
def get_expiry():
    try:
        r=requests.get(f"https://api.upstox.com/v2/option/contract?instrument_key={instrument_key}", headers=headers, timeout=4)
        if r.status_code==200: return sorted(list(set([d['expiry'] for d in r.json().get('data',[])])))[0]
    except: pass
    return "2026-10-30"
expiry=get_expiry()

def get_nse_session():
    s=requests.Session()
    s.headers.update({'User-Agent': 'Mozilla/5.0'})
    try: s.get("https://www.nseindia.com", timeout=5)
    except: pass
    return s

# ===== LIVE (Upstox) =====
r_ltp=requests.get(f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={instrument_key}", headers=headers, timeout=3)
live=list(r_ltp.json()['data'].values())[0]['last_price'] if r_ltp.status_code==200 else 0

# ===== CANDLE - Subah wala FIDI + EMA + MID ke liye =====
def get_candle():
    try:
        r=requests.get(f"https://api.upstox.com/v2/historical-candle/intraday/{instrument_key}/1minute", headers=headers, timeout=4)
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
fidi_status="WAIT"
ema_status="WAIT"
bottom_zone=False
top_zone=False
mid=live
day_high=day_low=live

if not df.empty:
    last=df.iloc[-1]
    fidi_status="BULL" if live>last['FIDI'] else "BEAR"
    ema_status="BULL" if last['EMA9']>last['EMA21'] else "BEAR"
    mid=(df['h'].max()+df['l'].min())/2
    day_high=df['h'].max(); day_low=df['l'].min()
    # Subah wala Bottom/Top logic
    if live < last['FIDI'] and fidi_status=="BEAR":
        bottom_zone=True
    if live > last['FIDI'] and fidi_status=="BULL" and ema_status=="BULL":
        top_zone=False

# ===== 1. ADVANCE DECLINE (Subah ke baad wala) =====
def get_ad():
    try:
        s=get_nse_session()
        r=s.get("https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050", timeout=5)
        if r.status_code==200:
            d=r.json()
            return d.get('advance',{}).get('advances',0), d.get('advance',{}).get('declines',0)
    except: pass
    return 0,0
adv, dec = get_ad()

# ===== 2. HEAT MAP 50% =====
def get_heat():
    main=["NIFTY BANK","NIFTY IT","NIFTY AUTO","NIFTY FMCG","NIFTY METAL","NIFTY PHARMA","NIFTY PSU BANK","NIFTY REALTY","NIFTY ENERGY","NIFTY FINANCIAL SERVICES"]
    try:
        s=get_nse_session()
        r=s.get("https://www.nseindia.com/api/allIndices", timeout=5)
        if r.status_code==200:
            all_data=r.json().get('data',[])
            green=0
            for sec in main:
                for item in all_data:
                    if item.get('index')==sec and item.get('percentChange',0)>0:
                        green+=1; break
            return int(green/len(main)*100), green
    except: pass
    return 0,0
heat_perc, green_count = get_heat()

# ===== 3 & 4. CHANGE IN OI + PCR + PREMIUM =====
def get_option_data():
    final_atm=round(live/50)*50
    ce_chg=pe_chg=0
    pcr=1.0
    prem_active="WAIT"
    bias="WAIT"
    try:
        # NSE Change in OI
        s=get_nse_session()
        r=s.get("https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY", timeout=6)
        if r.status_code==200:
            records=r.json().get('records',{}).get('data',[])
            near=[x for x in records if abs(x.get('strikePrice',0)-final_atm)<=300]
            max_ce=max_pe=0
            ce_st=pe_st=final_atm
            for it in near:
                ce=it.get('CE',{}).get('changeinOpenInterest',0)
                pe=it.get('PE',{}).get('changeinOpenInterest',0)
                if ce>max_ce: max_ce=ce; ce_st=it['strikePrice']
                if pe>max_pe: max_pe=pe; pe_st=it['strikePrice']
            ce_chg=max_ce; pe_chg=max_pe
            if max_pe>max_ce*1.2: final_atm=pe_st; bias=f"CALL HEAVY - PE Chg {max_pe} @ {pe_st}"
            elif max_ce>max_pe*1.2: final_atm=ce_st; bias=f"PUT HEAVY - CE Chg {max_ce} @ {ce_st}"
            else: bias=f"EQUAL - CE:{max_ce} PE:{max_pe}"
    except: pass

    try:
        # Upstox PCR + Premium
        r=requests.get(f"https://api.upstox.com/v2/option/chain?instrument_key={instrument_key}&expiry_date={expiry}", headers=headers, timeout=5)
        data=r.json().get('data') if r.status_code==200 else None
        if data:
            near10=sorted(data, key=lambda x: abs(x['strike_price']-live))[:10]
            ce_oi=sum([d.get('call_options',{}).get('market_data',{}).get('oi',0) for d in near10])
            pe_oi=sum([d.get('put_options',{}).get('market_data',{}).get('oi',0) for d in near10])
            pcr=round(pe_oi/ce_oi,2) if ce_oi else 1.0
            ce_v=sum([d.get('call_options',{}).get('market_data',{}).get('volume',0) for d in near10])
            pe_v=sum([d.get('put_options',{}).get('market_data',{}).get('volume',0) for d in near10])
            if ce_v>pe_v*1.2: prem_active="CALL ACTIVE"
            elif pe_v>ce_v*1.2: prem_active="PUT ACTIVE"
            else: prem_active=f"C:{int(ce_v)} P:{int(pe_v)}"
    except: pass

    return final_atm, ce_chg, pe_chg, pcr, prem_active, bias

final_atm, ce_chg, pe_chg, pcr_val, prem_active, bias_text = get_option_data()

# ===== DASHBOARD =====
st.markdown(f"### LIVE ₹{live} | ATM {final_atm} | PCR {pcr_val}")

# Subah wale
c1,c2,c3=st.columns(3)
c1.metric("FIDI 50", fidi_status, ema_status)
c2.metric("EMA 9/21", ema_status, f"Bottom: {bottom_zone}")
c3.metric("MID", f"{int(mid)}", f"{'CALL Heavy' if live>mid else 'PUT Heavy'}")

# Checklist wale
c4,c5=st.columns(2)
c4.metric("A/D", f"{adv}/{dec}", "BUY=CALL" if adv>dec else "SELL")
c5.metric("Heat Map", f"{heat_perc}%", f"{green_count}/10")

st.info(f"**Change OI:** {bias_text} | CE Chg {ce_chg} PE Chg {pe_chg}")
st.info(f"**Premium:** {prem_active} | PCR {pcr_val} | Mid: LIVE ₹{live} vs Mid ₹{int(mid)}")

st.markdown("---")
# FINAL SCORE - Subah + Checklist
score=0
if fidi_status=="BULL": score+=1
if ema_status=="BULL": score+=1
if adv>dec: score+=1
if heat_perc>=50: score+=1
if pe_chg>ce_chg: score+=1
if live>mid: score+=1

if bottom_zone and adv>dec and heat_perc>=50:
    st.success(f"# 🟢 BOTTOM ZONE @ ₹{live} - Candle ghum rahi hai - Score {score}/6")
    if sound_on: play_sound()
elif score>=5:
    st.success(f"# 🚀 FINAL BUY CALL @ {final_atm} - Score {score}/6")
    if sound_on: play_sound()
elif score<=2:
    st.error(f"# 🔻 FINAL SELL PUT @ {final_atm} - Score {score}/6")
else:
    st.warning(f"## ⏳ WAIT @ ₹{live} - Score {score}/6")

st.caption("Subah wale: FIDI + EMA + Bottom Zone ✅ | Checklist wale: A/D + Heat + ChgOI + Premium + Mid ✅ | Sab isme hai")