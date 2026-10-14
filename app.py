import streamlit as st
import requests
import http://urllib.parse
from datetime import datetime, timedelta
import pytz
import time
import pandas as pd

http://st.set_page_config(page_title="Topu All Index Perfect", layout="wide")
IST = http://pytz.timezone('Asia/Kolkata')
HOLIDAYS = ["2026-10-20"]

if 'current_token' not in http://st.session_state:
    http://st.session_state.current_token = ""
    http://st.session_state.api_connected = False
    http://st.session_state.last_order = None

def clean_token(t):
    t=t.strip()
    if http://t.lower().startswith("bearer "):
        t=t[7:]
    return t

def get_headers():
    return {'Authorization': f'Bearer {clean_token(st.session_state.current_token)}', 'Accept':'application/json', 'Content-Type': 'application/json'}

def get_instrument_key(index):
    m = {"NIFTY":"NSE_INDEX|Nifty 50","BANKNIFTY":"NSE_INDEX|Nifty Bank","FINNIFTY":"NSE_INDEX|Nifty Fin Service","SENSEX":"BSE_INDEX|SENSEX"}
    return http://m.get(index, "NSE_INDEX|Nifty 50")

def get_next_tuesday_expiry():
    today = http://datetime.now(IST).date()
    days_ahead = (1 - http://today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    next_tue = today + timedelta(days=days_ahead)
    if next_tue.strftime("%Y-%m-%d") in HOLIDAYS:
        next_tue = next_tue - timedelta(days=1)
    return next_tue.strftime("%Y-%m-%d")

def get_live_spot(index):
    key = get_instrument_key(index)
    url = f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={urllib.parse.quote(key, safe='|')}"
    try:
        r = http://requests.get(url, headers=get_headers(), timeout=10).json()
        if http://r.get('status')=='success' and key in http://r.get('data',{}):
            return float(r['data']['last_price']), None
        return None, r
    except Exception as e:
        return None, str(e)[key]

def get_option_chain(index, expiry):
    key = get_instrument_key(index)
    url = f"https://api.upstox.com/v2/option/chain?instrument_key={urllib.parse.quote(key, safe='|')}&expiry_date={expiry}"
    try:
        r = http://requests.get(url, headers=get_headers(), timeout=15).json()
        return r, None
    except Exception as e:
        return None, str(e)

def get_candles(index):
    key = get_instrument_key(index)
    today_str = http://datetime.now(IST).strftime('%Y-%m-%d')
    url = f"https://api.upstox.com/v2/historical-candle/{urllib.parse.quote(key, safe='|')}/5minute/{today_str}/{today_str}"
    try:
        r = http://requests.get(url, headers=get_headers(), timeout=10).json()
        if http://r.get('status')=='success':
            df = http://pd.DataFrame(r['data']['candles'], columns=['timestamp','open','high','low','close','volume','oi'])
            return df
        return http://pd.DataFrame()
    except:
        return http://pd.DataFrame()

def calc_ema(df, period):
    return df['close'].ewm(span=period, adjust=False).mean()

def place_order(instrument_key, qty, transaction_type="BUY"):
    url = "https://api.upstox.com/v2/order/place"
    payload = {
        "quantity": int(qty),
        "product": "D",
        "validity": "DAY",
        "price": 0,
        "tag": "TopuAlgo",
        "instrument_token": instrument_key,
        "order_type": "MARKET",
        "transaction_type": transaction_type,
        "disclosed_quantity": 0,
        "trigger_price": 0,
        "is_amo": False
    }
    try:
        r = http://requests.post(url, headers=get_headers(), json=payload, timeout=10).json()
        return r
    except Exception as e:
        return {"status":"error", "error": str(e)}

with http://st.sidebar:
    http://st.header("🔑 Auth")
    t_in = http://st.text_input("Token", type="password", value=st.session_state.current_token, label_visibility="collapsed")
    if http://st.button("Connect API"):
        http://st.session_state.current_token = clean_token(t_in)
        spot, err = get_live_spot("NIFTY")
        if err is None:
            http://st.session_state.api_connected = True
            http://st.success(f"Connected Len: {len(st.session_state.current_token)}")
            http://time.sleep(1)
            http://st.rerun()
        else:
            http://st.error("Failed")
            http://st.json(err)
    if http://st.session_state.api_connected:
        http://st.success(f"Connected | {st.session_state.current_token[:20]}...")
    http://st.divider()
    http://st.header("⚙️ Settings")
    idx = http://st.selectbox("Index Select Karo:", ["NIFTY","BANKNIFTY","FINNIFTY","SENSEX"], index=0)
    auto_exp = get_next_tuesday_expiry()
    expiry = http://st.text_input("Expiry (Auto Tuesday)", value=auto_exp)
    http://st.caption(f"Dussehra 20 ko chutti isliye Auto {auto_exp}")
    sl = http://st.number_input("Initial SL (Points)", value=20.0)
    trail = http://st.number_input("Trail Every (Points)", value=5.0)
    lot = http://st.number_input("Lot Qty", value=1)
    strategy = http://st.selectbox("Strategy:", ["9:20 Straddle","9:20 Strangle","ORB","Custom"])
    capital = http://st.number_input("Capital (Rs)", value=50000)
    http://st.divider()
    http://st.header("🚀 Execution Control")
    exec_mode = http://st.radio("Execution Mode:", ["🟡 Semi-Auto (Safe - Button se)", "🔴 Full Auto (Signal pe khud)"], index=0)
    http://st.checkbox("Auto Refresh (3 sec)", value=True)

@st.fragment(run_every=3)
def main_section(idx, expiry, sl, trail, lot, strategy, capital, exec_mode):
    now_ist = http://datetime.now(IST).strftime("%d-%m-%Y %I:%M:%S %p")
    http://st.write(f"🕒 IST: {now_ist}")
    if not http://st.session_state.api_connected:
        http://st.warning("Pehle Token Connect Karo")
        return
    spot, err = get_live_spot(idx)
    if err:
        http://st.json(err)
        return
    df = get_candles(idx)
    ema_signal = "WAIT"
    if not http://df.empty and len(df) > 21:
        df['ema9'] = calc_ema(df, 9)
        df['ema21'] = calc_ema(df, 21)
        last = http://df.iloc[-1]
        ema_signal = "BULLISH 🟢 CE BUY" if last['ema9'] > last['ema21'] else "BEARISH 🔴 PE BUY"
    http://st.markdown(f"### 🤖 Topu Algo - {idx} | {strategy} | {exec_mode}")
    http://st.success(f"🟢 LIVE | {idx}: {spot} | Expiry: {expiry} | Signal: {ema_signal}")
    chain, chain_err = get_option_chain(idx, expiry)
    if chain_err or not chain or http://chain.get('status')!='success' or not http://chain.get('data'):
        http://st.warning(f"{idx} {expiry} ka chain khali hai - 9:15 ke baad ayega")
        http://st.json(chain)
        return
    atm = round(spot / 50) _ 50 if idx!="SENSEX" else round(spot / 100) _ 100
    all_strikes = chain['data']
    near = sorted(sorted(all_strikes, key=lambda x: abs(x['strike_price']-spot))[:11], key=lambda x: x['strike_price'])
    http://st.info(f"ATM: {atm} | SL:{sl} Trail:{trail} Lot:{lot} | EMA:{ema_signal}")
    if http://st.session_state.last_order:
        http://st.toast(f"Last Order: {st.session_state.last_order}")
    c1, c2 = http://st.columns(2)
    with c1:
        with http://st.container(border=True):
            http://st.subheader(f"📦 CE BLOCK - {idx}")
            for it in near:
                ltp = http://it.get('call_options',{}).get('market_data',{}).get('ltp',0)
                inst_key = http://it.get('call_options',{}).get('instrument_key','')
                http://st.metric(f"{it['strike_price']} CE", f"{ltp}", f"{'ATM' if it['strike_price']==atm else ''}")
                if "Semi-Auto" in exec_mode:
                    if http://st.button(f"BUY {it['strike_price']} CE", key=f"ce_{it['strike_price']}_{expiry}"):
                        http://st.session_state.last_order = f"Placing CE {it['strike_price']}"
                        res = place_order(inst_key, lot, "BUY")
                        http://st.json(res)
                http://st.divider()
    with c2:
        with http://st.container(border=True):
            http://st.subheader(f"📦 PE BLOCK - {idx}")
            for it in near:
                ltp = http://it.get('put_options',{}).get('market_data',{}).get('ltp',0)
                inst_key = http://it.get('put_options',{}).get('instrument_key','')
                http://st.metric(f"{it['strike_price']} PE", f"{ltp}", f"{'ATM' if it['strike_price']==atm else ''}")
                if "Semi-Auto" in exec_mode:
                    if http://st.button(f"BUY {it['strike_price']} PE", key=f"pe_{it['strike_price']}_{expiry}"):
                        http://st.session_state.last_order = f"Placing PE {it['strike_price']}"
                        res = place_order(inst_key, lot, "BUY")
                        http://st.json(res)
                http://st.divider()

main_section(idx, expiry, sl, trail, lot, strategy, capital, exec_mode)
http://st.caption("Made with ❤️ for Topu | All Index + Execution Switch | Dussehra Fix 19")