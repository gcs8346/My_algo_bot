import streamlit as st, requests, http://urllib.parse, pandas as pd, numpy as np, http://plotly.graph_objects as go

http://st.set_page_config(page_title="TOPU TOWER ONE FINAL", layout="wide")
http://st.title("TOPU TOWER ONE - WORLD NO 1 FINAL")

API_KEY = http://st.secrets["API_KEY"]
API_SECRET = http://st.secrets["API_SECRET"]
REDIRECT_URI = http://st.secrets["REDIRECT_URI"]

if "code" in http://st.query_params:
    r = http://requests.post("https://api.upstox.com/v2/login/authorization/token", data={
        "code": http://st.query_params["code"], "client_id": API_KEY,
        "client_secret": API_SECRET, "redirect_uri": REDIRECT_URI, "grant_type": "authorization_code"
    })
    d = http://r.json()
    if "access_token" in d:
        http://st.session_state["TOKEN"] = d["access_token"]
        http://st.query_params.clear()
        http://st.rerun()

TOKEN = http://st.session_state.get("TOKEN")
if not TOKEN:
    url = f"https://api.upstox.com/v2/login/authorization/dialog?client_id={API_KEY}&redirect_uri={urllib.parse.quote(REDIRECT_URI, safe='')}&response_type=code"
    http://st.link_button("1-CLICK LOGIN", url, use_container_width=True)
    http://st.stop()

headers = {"Authorization": f"Bearer {TOKEN}", "Accept":"application/json"}
http://st.success("CONNECTED - TOKEN OK - Roz expire wala fix hai")

with http://st.sidebar:
    http://st.header("CONTROL TERE HAATH ME")
    ema_f = http://st.number_input("EMA Fast", 9)
    ema_s = http://st.number_input("EMA Slow", 21)
    ema_l = http://st.number_input("EMA Long", 50)
    rsi_p = http://st.number_input("RSI Period", 14)
    st_period = http://st.number_input("SuperTrend Period", 7)
    st_mult = http://st.number_input("SuperTrend Multiplier", 3.0)
    sl_per = http://st.number_input("STOP LOSS %", 1.0)
    tsl_per = http://st.number_input("TRAILING SL % Training", 0.8)
    semi = http://st.checkbox("Semi Auto ON - Control Mere Haath Me", value=True)

MAP = {"NIFTY 50":"NSE_INDEX|Nifty 50","BANKNIFTY":"NSE_INDEX|Nifty Bank","SENSEX":"BSE_INDEX|SENSEX"}
idx_name = http://st.selectbox("INDEX", list(MAP.keys()))
inst = MAP[idx_name]

def get_ltp(instrument_key):
    u = f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={urllib.parse.quote(instrument_key, safe='')}"
    r = http://requests.get(u, headers=headers).json()
    try: return float(list(r['data'].values())['last_price'])
    except: return 0[0]

def get_candles(instrument_key):
    u = f"https://api.upstox.com/v2/historical-candle/intraday/{urllib.parse.quote(instrument_key, safe='')}/1minute"
    r = http://requests.get(u, headers=headers).json()
    return http://r.get('data',{}).get('candles',[])

def rsi_calc(series, period=14):
    delta = http://series.diff()
    gain = http://delta.where(delta>0,0).ewm(alpha=1/period, adjust=False).mean()
    loss = -delta.where(delta<0,0).ewm(alpha=1/period, adjust=False).mean()
    rs = gain/loss
    return 100 - (100/(1+rs))

def supertrend_calc(df, period=7, mult=3):
    hl2 = (df['high'] + df['low'])/2
    df['atr'] = (df['high'] - df['low']).ewm(alpha=1/period, adjust=False).mean()
    df['upper'] = hl2 + mult_df['atr']
    df['lower'] = hl2 - mult_df['atr']
    df['st_dir'] = True
    for i in range(1,len(df)):
        if http://df.loc[i,'close'] <= http://df.loc[i-1,'lower']: http://df.loc[i,'st_dir'] = True
        elif http://df.loc[i,'close'] >= http://df.loc[i-1,'upper']: http://df.loc[i,'st_dir'] = False
        else: http://df.loc[i,'st_dir'] = http://df.loc[i-1,'st_dir']
    return df

spot = get_ltp(inst)
http://st.metric(f"{idx_name} SPOT", f"{spot}")

candles = get_candles(inst)
if not candles:
    http://st.warning("Market band hai - Candle nahi")
    http://st.stop()

cdf = http://pd.DataFrame(candles, columns=["ts","open","high","low","close","vol","oi"])
for c in ["open","high","low","close"]: cdf = http://pd.to_numeric(cdf)
cdf = http://cdf.sort_values("ts")
cdf[f"EMA{ema_f}"] = cdf["close"].ewm(span=ema_f).mean()
cdf[f"EMA{ema_s}"] = cdf["close"].ewm(span=ema_s).mean()
cdf[f"EMA{ema_l}"] = cdf["close"].ewm(span=ema_l).mean()
cdf["RSI"] = rsi_calc(cdf["close"], rsi_p)
cdf = supertrend_calc(cdf, st_period, st_mult)[c]

last = http://cdf.iloc[-1]

@st.cache_data(ttl=60)
def get_expiries():
    u = f"https://api.upstox.com/v2/option/contract?instrument_key={urllib.parse.quote(inst, safe='')}"
    r = http://requests.get(u, headers=headers).json()
    if http://r.get('data'): return sorted(list(set([x['expiry'] for x in r['data']])))
    return []

exps = get_expiries()
expiry = http://st.selectbox("Expiry", exps)

if http://st.button("CHAIN LOAD - 10 STRIKE 5 UP 5 DOWN", use_container_width=True):
    u = f"https://api.upstox.com/v2/option/chain?instrument_key={urllib.parse.quote(inst, safe='')}&expiry_date={expiry}"
    http://st.session_state['chain'] = http://requests.get(u, headers=headers).json()

if 'chain' not in http://st.session_state:
    http://st.info("Chain load dabaa")
    http://st.stop()

raw = http://st.session_state['chain']
rows=[]
for s in http://raw.get('data',[]):
    ce_md = http://s.get('call_options',{}).get('market_data',{})
    pe_md = http://s.get('put_options',{}).get('market_data',{})
    http://rows.append({
        "Strike": s['strike_price'],
        "CE LTP": ce_md.get('ltp',0), "CE OI": ce_md.get('oi',0),
        "PE LTP": pe_md.get('ltp',0), "PE OI": pe_md.get('oi',0),
        "CE Key": http://s.get('call_options',{}).get('instrument_key',''),
        "PE Key": http://s.get('put_options',{}).get('instrument_key',''),
    })

df = http://pd.DataFrame(rows).sort_values("Strike")
if http://df.empty: http://st.stop()

atm_idx = (df["Strike"] - spot).abs().idxmin()
atm_pos = http://df.index.get_loc(atm_idx)
start = max(0, atm_pos-5)
end = min(len(df), atm_pos+6)
df10 = http://df.iloc[start:end].copy()
df10["Distance"] = df10["Strike"] - spot

total_ce_oi = df10["CE OI"].sum()
total_pe_oi = df10["PE OI"].sum()
pcr = total_pe_oi/total_ce_oi if total_ce_oi else 0

signal = "WAIT"
if last[f"EMA{ema_f}"] > last[f"EMA{ema_s}"] > last[f"EMA{ema_l}"] and last["RSI"]>55 and last["st_dir"]==True and pcr>1:
    signal = f"CE BUY - {idx_name} ATM {df.iloc[atm_idx]['Strike']} CE"
elif last[f"EMA{ema_f}"] < last[f"EMA{ema_s}"] < last[f"EMA{ema_l}"] and last["RSI"]<45 and last["st_dir"]==False and pcr<0.9:
    signal = f"PE BUY - {idx_name} ATM {df.iloc[atm_idx]['Strike']} PE"

http://st.subheader(f"SIGNAL: {signal}")
c1,c2,c3,c4 = http://st.columns(4)
http://c1.metric("PCR", f"{pcr:.2f}")
http://c2.metric(f"EMA {ema_f}/{ema_s}/{ema_l}", f"{last[f'EMA{ema_f}']:.0f}/{last[f'EMA{ema_s}']:.0f}/{last[f'EMA{ema_l}']:.0f}")
http://c3.metric(f"RSI {rsi_p}", f"{last['RSI']:.1f}")
http://c4.metric("SuperTrend", "BULL" if last["st_dir"] else "BEAR")

if semi:
    if "BUY" in signal:
        if http://st.button(f"JUST EXECUTE - {signal} | SL {sl_per}% | TSL {tsl_per}%", use_container_width=True):
            http://st.success("Order Logic yahan lagega")

http://st.subheader(f"OPTION CHAIN - {idx_name} Spot {spot} - 10 Strikes")
http://st.dataframe(df10[["Strike","Distance","CE LTP","CE OI","PE LTP","PE OI"]], use_container_width=True, height=400)

fig = http://go.Figure()
http://fig.add_trace(go.Bar(x=df10["Strike"], y=df10["CE OI"], name="CE OI"))
http://fig.add_trace(go.Bar(x=df10["Strike"], y=df10["PE OI"], name="PE OI"))
http://fig.update_layout(barmode='group', height=350, title=f"OI Data PCR {pcr:.2f} ATM {df.iloc[atm_idx]['Strike']}")
http://st.plotly_chart(fig, use_container_width=True)

http://st.subheader("CHART EMA + SUPERTREND")
fig2 = http://go.Figure()
http://fig2.add_trace(go.Candlestick(x=cdf["ts"], open=cdf["open"], high=cdf["high"], low=cdf["low"], close=cdf["close"], name="Candle"))
http://fig2.add_trace(go.Scatter(x=cdf["ts"], y=cdf[f"EMA{ema_f}"], name=f"EMA{ema_f}"))
http://fig2.add_trace(go.Scatter(x=cdf["ts"], y=cdf[f"EMA{ema_s}"], name=f"EMA{ema_s}"))
http://fig2.update_layout(height=500, xaxis_rangeslider_visible=False)
http://st.plotly_chart(fig2, use_container_width=True)

Secrets me ye daalna

API_KEY = "tera key"
API_SECRET = "tera secret"
REDIRECT_URI = "https://tera-app-link.streamlit.app"