import streamlit as st
import pandas as pd
import requests, urllib.parse
import pytz
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Topu Algo - Full Fixed", layout="wide")
st_autorefresh(interval=3000, key="datarefresh")

if 'execution_logs' not in st.session_state: st.session_state.execution_logs = []
if 'current_token' not in st.session_state: st.session_state.current_token = ""
if 'api_connected' not in st.session_state: st.session_state.api_connected = False
if 'last_valid_spot' not in st.session_state: st.session_state.last_valid_spot = 22500.00
if 'trades' not in st.session_state: st.session_state.trades = []

def get_headers():
    return {'Authorization': f'Bearer {st.session_state.current_token.strip()}', 'Accept': 'application/json'}

def get_live_market_snapshot(index_name, access_token):
    instrument_mapping = {"NIFTY": "NSE_INDEX|Nifty 50", "BANK NIFTY": "NSE_INDEX|Nifty Bank"}
    instrument_key = instrument_mapping.get(index_name, "NSE_INDEX|Nifty 50")
    key_encoded = urllib.parse.quote(instrument_key)
    # FIXED URL
    url = f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={key_encoded}"
    try:
        response = requests.get(url, headers=get_headers(), timeout=5).json()
        if response.get('status') == 'success' and response.get('data', {}).get(instrument_key):
            spot = float(response['data'][instrument_key]['last_price'])
            st.session_state.last_valid_spot = spot
            return spot, None
        else:
            err = response.get('errors', [{}])[0].get('message', 'Invalid Response')
            return None, err
    except Exception as e:
        return None, str(e)

def fetch_live_option_chain_data(index_name, expiry_date, access_token):
    instrument_mapping = {"NIFTY": "NSE_INDEX|Nifty 50", "BANK NIFTY": "NSE_INDEX|Nifty Bank"}
    instrument_key = instrument_mapping.get(index_name, "NSE_INDEX|Nifty 50")
    key_encoded = urllib.parse.quote(instrument_key)
    # FIXED URL
    url = f"https://api.upstox.com/v2/option/chain?instrument_key={key_encoded}&expiry_date={expiry_date}"
    try:
        response = requests.get(url, headers=get_headers(), timeout=10).json()
        if response.get('status') == 'success':
            chain_list = response.get('data', [])
            if not chain_list:
                return None, "Chain Empty - Expiry galat hai ya Market band hai"
            records = []
            total_call_oi = 0
            total_put_oi = 0
            for item in chain_list:
                strike = item.get('strike_price')
                if strike is None: continue
                call_data = item.get('call_options', {}).get('market_data', {}) or {}
                put_data = item.get('put_options', {}).get('market_data', {}) or {}

                c_oi = call_data.get('oi', 0) or 0
                c_chg_oi = call_data.get('oi_percent_change', 0) or call_data.get('oi_change_percent',0) or 0
                p_oi = put_data.get('oi', 0) or 0
                p_chg_oi = put_data.get('oi_percent_change', 0) or put_data.get('oi_change_percent',0) or 0

                total_call_oi += c_oi
                total_put_oi += p_oi

                records.append({
                    "Strike": strike,
                    "Call OI": c_oi, "Call Chg OI %": round(float(c_chg_oi), 2),
                    "Put OI": p_oi, "Put Chg OI %": round(float(p_chg_oi), 2),
                    "Call LTP": call_data.get('ltp',0), "Put LTP": put_data.get('ltp',0),
                    "Call Key": item.get('call_options',{}).get('instrument_key',''),
                    "Put Key": item.get('put_options',{}).get('instrument_key',''),
                    "Total OI": c_oi+p_oi
                })
            df_chain = pd.DataFrame(records).sort_values("Strike")
            live_pcr = round(total_put_oi / total_call_oi, 3) if total_call_oi > 0 else 0.0
            return {"df": df_chain, "pcr": live_pcr, "total_call": total_call_oi, "total_put": total_put_oi}, None
        else:
            err = response.get('errors', [{}])[0].get('message', 'Chain Fetch Error')
            return None, err
    except Exception as e:
        return None, str(e)

def fetch_real_live_positions(access_token):
    # FIXED URL
    url = 'https://api.upstox.com/v2/portfolio/short-term-positions'
    try:
        response = requests.get(url, headers=get_headers(), timeout=5).json()
        if response.get('status') == 'success':
            pos_list = response.get('data', [])
            if not pos_list: return pd.DataFrame(), None
            records = []
            for pos in pos_list:
                net_qty = int(pos.get('quantity', 0))
                buy_avg = float(pos.get('average_price', 0.0))
                ltp = float(pos.get('last_price', 0.0))
                live_pnl = round((ltp - buy_avg) * net_qty, 2)
                records.append({"Symbol": pos.get('trading_symbol'), "Net Qty": net_qty, "Avg Buy Price": buy_avg, "Live LTP": ltp, "Live PNL (MTM)": live_pnl})
            return pd.DataFrame(records), None
        else:
            return pd.DataFrame(), response.get('errors', [{}])[0].get('message','')
    except Exception as e:
        return pd.DataFrame(), str(e)

# ================= UI =================
st.title("🤖 Topu Semi-Automatic Options Algo Dashboard - FIXED")

st.sidebar.header("🔑 Authentication & Control")
token_input = st.sidebar.text_input("Upstox Access Token", type="password", value=st.session_state.current_token)
if st.sidebar.button("Connect API"):
    if token_input:
        st.session_state.current_token = token_input.strip()
        spot, err = get_live_market_snapshot("NIFTY", st.session_state.current_token)
        if err is None:
            st.session_state.api_connected = True
            st.sidebar.success("CONNECTED TO LIVE MARKET 🟢")
            st.rerun()
        else:
            st.session_state.api_connected = False
            st.sidebar.error(f"Failed: {err}")
if st.sidebar.button("Disconnect API"):
    st.session_state.current_token = ""; st.session_state.api_connected = False; st.rerun()
st.sidebar.markdown(f"**API Status:** {'🟢 CONNECTED' if st.session_state.api_connected else '🔴 DISCONNECTED'}")

st.sidebar.header("⚙️ SL & Trailing Settings")
initial_sl = st.sidebar.number_input("Initial Stop Loss (Points)", 1.0, 100.0, 20.0, 1.0)
trail_every = st.sidebar.number_input("Trail Every (Points)", 1.0, 50.0, 5.0, 1.0)
qty = st.sidebar.number_input("Lot Qty", 1, 10, 1)

st.header("📈 Live Derivatives Tracker & Analytics")
index_choice = st.selectbox("🎯 SELECT INDEX", ["NIFTY", "BANK NIFTY"])
expiry_choice = st.text_input("📅 Expiry Date (YYYY-MM-DD format)", value="2026-10-16")

if st.session_state.api_connected:
    live_spot, spot_err = get_live_market_snapshot(index_choice, st.session_state.current_token)
    chain_data, chain_err = fetch_live_option_chain_data(index_choice, expiry_choice, st.session_state.current_token)

    if spot_err: st.error(f"Spot Error: {spot_err}")
    if chain_err: st.error(f"Chain Error: {chain_err} - Expiry check karo: {expiry_choice}")

    if chain_data and not spot_err:
        df = chain_data['df']
        pcr = chain_data['pcr']

        c1,c2,c3,c4 = st.columns(4)
        c1.metric(f"🔥 {index_choice} Live Spot", f"₹{live_spot:.2f}" if live_spot else "N/A")
        c2.metric("📊 PCR", pcr, delta="BULLISH" if pcr >= 1.0 else "BEARISH")
        c3.metric("💼 Total Call OI", f"{chain_data['total_call']:,}")
        c4.metric("🏢 Total Put OI", f"{chain_data['total_put']:,}")

        # === YAHI WO LOGIC HAI JO GAYAB THA ===
        atm_strike = df.loc[(df['Strike']-live_spot).abs().idxmin(), 'Strike'] if live_spot else 0
        max_pain = df.loc[df['Total OI'].idxmax(), 'Strike']
        st.info(f"ATM: {atm_strike} | Max Pain: {max_pain} | Spot: {live_spot}")

        atm_near = df[(df['Strike']>=atm_strike-200) & (df['Strike']<=atm_strike+200)]
        avg_put_chg = atm_near['Put Chg OI %'].mean()
        avg_call_chg = atm_near['Call Chg OI %'].mean()

        signal_text = "WAIT"; buy_type = ""; reason = ""
        if pcr >= 1.3 and avg_put_chg >= 10:
            signal_text = f"🟢 BUY {atm_strike} CE"; buy_type="CE"
            reason = f"PCR {pcr} >=1.3 + Put Chg +{avg_put_chg:.1f}% = BULLISH"
        elif pcr <= 0.7 and avg_call_chg >= 10:
            signal_text = f"🔴 BUY {atm_strike} PE"; buy_type="PE"
            reason = f"PCR {pcr} <=0.7 + Call Chg +{avg_call_chg:.1f}% = BEARISH"
        else:
            reason = f"Neutral - PCR {pcr}, Put Chg {avg_put_chg:.1f}%, Call Chg {avg_call_chg:.1f}%"

        st.subheader(f"🤖 Signal: {signal_text}")
        st.write(reason)

        col_y, col_n = st.columns(2)
        with col_y:
            if st.button("✅ YES - BUY NOW", type="primary", use_container_width=True, disabled=("WAIT" in signal_text)):
                st.session_state.trades.append({"Time": datetime.now().strftime('%H:%M:%S'), "Signal": signal_text, "Strike": atm_strike, "SL": initial_sl, "Trail": trail_every, "Qty": qty})
                st.session_state.execution_logs.append(f"{datetime.now().strftime('%H:%M:%S')} - EXECUTED {signal_text}")
                st.balloons(); st.success(f"Executed {signal_text} - SL {initial_sl}, Trail {trail_every}")
        with col_n:
            if st.button("❌ NO - SKIP", use_container_width=True):
                st.session_state.execution_logs.append(f"{datetime.now().strftime('%H:%M:%S')} - SKIPPED {signal_text}")

        st.subheader("🔥 Real-Time Option Chain (Change in OI)")
        st.dataframe(df, use_container_width=True, height=500)

        st.divider()
        pos_df, pos_err = fetch_real_live_positions(st.session_state.current_token)
        c_mtm1, c_mtm2 = st.columns(2)
        with c_mtm1:
            st.subheader("💼 Live Positions & MTM")
            if not pos_df.empty: st.dataframe(pos_df, use_container_width=True)
            else: st.caption("No live position / API se data nahi aaya")
            if st.session_state.trades:
                st.write("**Local Trades:**"); st.dataframe(pd.DataFrame(st.session_state.trades), use_container_width=True)
        with c_mtm2:
            st.subheader("📝 Execution Logs")
            for l in reversed(st.session_state.execution_logs[-15:]): st.text(l)
    else:
        if not chain_data: st.warning("Chain load nahi hua - Token ya Expiry check karo")
else:
    st.warning("Pehle Token daal ke Connect karo - Token har din subah 6 baje expire hota hai")