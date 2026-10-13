import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Topu Algo - FINAL", layout="wide")
st_autorefresh(interval=4000, key="datarefresh")

if 'current_token' not in st.session_state: st.session_state.current_token = ""
if 'api_connected' not in st.session_state: st.session_state.api_connected = False
if 'trades' not in st.session_state: st.session_state.trades = []
if 'logs' not in st.session_state: st.session_state.logs = []

def clean_token(t):
    t = t.strip()
    if t.lower().startswith("bearer "): t = t[7:]
    return t

def get_headers():
    return {'Authorization': f'Bearer {clean_token(st.session_state.current_token)}', 'Accept': 'application/json'}

# --- API 1: SPOT ---
def get_live_market_snapshot(index_name):
    mapping = {"NIFTY": "NSE_INDEX|Nifty 50", "BANK NIFTY": "NSE_INDEX|Nifty Bank"}
    key = mapping.get(index_name, "NSE_INDEX|Nifty 50")
    url = "https://api.upstox.com/v2/market-quote/ltp"
    params = {"instrument_key": key}
    try:
        r = requests.get(url, headers=get_headers(), params=params, timeout=10)
        data = r.json()
        # DEBUG के लिए raw दिखाएंगे
        if data.get('status') == 'success':
            price = data['data'][key]['last_price']
            return float(price), None, data
        else:
            return None, data, data
    except Exception as e:
        return None, str(e), None

# --- API 2: OPTION CHAIN ---
def fetch_option_chain(index_name, expiry):
    mapping = {"NIFTY": "NSE_INDEX|Nifty 50", "BANK NIFTY": "NSE_INDEX|Nifty Bank"}
    key = mapping.get(index_name, "NSE_INDEX|Nifty 50")
    url = "https://api.upstox.com/v2/option/chain"
    params = {"instrument_key": key, "expiry_date": expiry}
    try:
        r = requests.get(url, headers=get_headers(), params=params, timeout=15)
        j = r.json()
        if j.get('status')!= 'success':
            return None, j
        chain = j.get('data', [])
        rows = []
        total_call = total_put = 0
        for it in chain:
            strike = it.get('strike_price')
            if strike is None: continue
            c_m = (it.get('call_options') or {}).get('market_data') or {}
            p_m = (it.get('put_options') or {}).get('market_data') or {}
            c_oi = c_m.get('oi',0) or 0
            p_oi = p_m.get('oi',0) or 0
            total_call+=c_oi; total_put+=p_oi
            rows.append({
                "Strike": strike,
                "Call LTP": c_m.get('ltp',0), "Put LTP": p_m.get('ltp',0),
                "Call OI": c_oi, "Put OI": p_oi,
                "Call Chg %": c_m.get('oi_percent_change',0) or 0,
                "Put Chg %": p_m.get('oi_percent_change',0) or 0,
                "Total OI": c_oi+p_oi,
                "Call Key": (it.get('call_options') or {}).get('instrument_key',''),
                "Put Key": (it.get('put_options') or {}).get('instrument_key','')
            })
        if not rows:
            return None, {"error":"Chain khali - Expiry galat ya market band", "raw": j}
        df = pd.DataFrame(rows).sort_values("Strike").reset_index(drop=True)
        pcr = round(total_put/total_call, 3) if total_call>0 else 0
        return {"df": df, "pcr": pcr, "total_call": total_call, "total_put": total_put}, None
    except Exception as e:
        return None, str(e)

# --- UI ---
st.title("🤖 Topu Semi-Automatic Options Algo - FINAL FIXED")

st.sidebar.header("🔑 Authentication & Control")
token_input = st.sidebar.text_input("Upstox Access Token", type="password", value=st.session_state.current_token, help="Sirf token paste karo, Bearer likhne ki zarurat nahi")

if st.sidebar.button("Connect API"):
    st.session_state.current_token = clean_token(token_input)
    spot, err, raw = get_live_market_snapshot("NIFTY")
    if err is None:
        st.session_state.api_connected = True
        st.sidebar.success(f"CONNECTED 🟢 Spot: {spot}")
        st.rerun()
    else:
        st.session_state.api_connected = False
        st.sidebar.error("FAILED")
        st.sidebar.json(raw or err) # Yahan asli error dikhega

if st.sidebar.button("Disconnect API"):
    st.session_state.current_token = ""; st.session_state.api_connected=False; st.rerun()

st.sidebar.write(f"**API Status:** {'🟢 CONNECTED' if st.session_state.api_connected else '🔴 DISCONNECTED'}")

st.sidebar.header("⚙️ SL & Trailing Settings")
initial_sl = st.sidebar.number_input("Initial SL (Points)", 1.0, 100.0, 20.0)
trail_every = st.sidebar.number_input("Trail Every (Points)", 1.0, 50.0, 5.0)
qty = st.sidebar.number_input("Lot Qty", 1, 10, 1)

st.header("📈 Live Tracker")
index_choice = st.selectbox("🎯 INDEX", ["NIFTY", "BANK NIFTY"])
expiry_choice = st.text_input("📅 Expiry (YYYY-MM-DD)", value="2026-10-16")

if not st.session_state.api_connected:
    st.warning("Pehle Connect API dabao. Token sahi hote hi sab data aa jayega.")
    st.stop()

spot, err, raw = get_live_market_snapshot(index_choice)
chain_data, chain_err = fetch_option_chain(index_choice, expiry_choice)

if err:
    st.error("Spot API Error - Niche dekho Upstox kya bol raha hai")
    st.json(raw)
    st.stop()

if chain_err:
    st.error(f"Chain Error for {expiry_choice}")
    st.json(chain_err)
    st.stop()

if chain_data:
    df = chain_data['df']
    pcr = chain_data['pcr']

    c1,c2,c3,c4 = st.columns(4)
    c1.metric(f"🔥 {index_choice} Spot", f"{spot}")
    c2.metric("📊 PCR", pcr, "BULLISH" if pcr>=1 else "BEARISH")
    c3.metric("Call OI Total", f"{chain_data['total_call']:,}")
    c4.metric("Put OI Total", f"{chain_data['total_put']:,}")

    atm_strike = df.loc[(df['Strike']-spot).abs().idxmin(), 'Strike']
    max_pain = df.loc[df['Total OI'].idxmax(), 'Strike']
    st.info(f"ATM: {atm_strike} | Max Pain: {max_pain} | Spot: {spot}")

    # Signal Logic
    atm_near = df[(df['Strike']>=atm_strike-200) & (df['Strike']<=atm_strike+200)]
    avg_put = atm_near['Put Chg %'].mean()
    avg_call = atm_near['Call Chg %'].mean()

    signal = "WAIT"; btype=""
    if pcr >= 1.3 and avg_put >= 10:
        signal = f"🟢 BUY {atm_strike} CE"; btype="CE"
        reason = f"PCR {pcr} + Put OI +{avg_put:.1f}%"
    elif pcr <= 0.7 and avg_call >= 10:
        signal = f"🔴 BUY {atm_strike} PE"; btype="PE"
        reason = f"PCR {pcr} + Call OI +{avg_call:.1f}%"
    else:
        reason = f"Neutral - PCR {pcr}, Put Chg {avg_put:.1f}%, Call Chg {avg_call:.1f}%"

    st.subheader(signal); st.write(reason)

    col1,col2 = st.columns(2)
    with col1:
        if st.button("✅ YES - BUY NOW", type="primary", use_container_width=True, disabled=("WAIT" in signal)):
            st.session_state.trades.append({"Time": datetime.now().strftime('%H:%M:%S'), "Signal": signal, "Qty": qty, "SL": initial_sl, "Trail": trail_every})
            st.session_state.logs.append(f"EXECUTED {signal}")
            st.balloons()
    with col2:
        if st.button("❌ NO - SKIP", use_container_width=True):
            st.session_state.logs.append(f"SKIPPED {signal}")

    st.subheader("🔥 Option Chain - Change in OI")
    st.dataframe(df, use_container_width=True, height=600)

    st.divider()
    st.subheader("📝 Logs")
    for l in reversed(st.session_state.logs[-10:]): st.text(l)
    if st.session_state.trades: st.dataframe(pd.DataFrame(st.session_state.trades))