import streamlit as st, requests urllib.parse, pandas as pd, plotly.graph_objects as go
st.set_page_config(page_title="TOPU TOWER ONE FINAL", layout="wide")
API_KEY = http://st.secrets["API_KEY"]
API_SECRET = http://st.secrets["API_SECRET"]
REDIRECT_URI = http://st.secrets["REDIRECT_URI"]
if "code" in http://st.query_params:
    r = http://requests.post("https://api.upstox.com/v2/login/authorization/token", data={"code": http://st.query_params["code"], "client_id": API_KEY, "client_secret": API_SECRET, "redirect_uri": REDIRECT_URI, "grant_type": "authorization_code"})
    d=r.json()
    if "access_token" in d:
        http://st.session_state["TOKEN"]=d["access_token"]
        http://st.query_params.clear()
        http://st.rerun()
TOKEN = http://st.session_state.get("TOKEN")
if not TOKEN:
    url = f"https://api.upstox.com/v2/login/authorization/dialog?client_id={API_KEY}&redirect_uri={urllib.parse.quote(REDIRECT_URI, safe='')}&response_type=code"
    http://st.link_button("1-CLICK LOGIN", url, use_container_width=True)
    http://st.stop()
headers = {"Authorization": f"Bearer {TOKEN}"}
http://st.success("CONNECTED")
MAP = {"NIFTY 50":"NSE_INDEX|Nifty 50","BANKNIFTY":"NSE_INDEX|Nifty Bank"}
idx = http://st.selectbox("INDEX", list(MAP.keys()))
inst = MAP
def get_chain():
    exps_req = http://requests.get(f"https://api.upstox.com/v2/option/contract?instrument_key={urllib.parse.quote(inst, safe='')}", headers=headers).json()
    exps = sorted(list(set([x['expiry'] for x in exps_req.get('data',[])])))
    expiry = http://st.selectbox("Expiry", exps)
    if http://st.button("CHAIN LOAD - 10 STRIKE 5 UP 5 DOWN"):
        u = f"https://api.upstox.com/v2/option/chain?instrument_key={urllib.parse.quote(inst, safe='')}&expiry_date={expiry}"
        http://st.session_state['chain']=requests.get(u, headers=headers).json()
get_chain()
if 'chain' not in http://st.session_state:
    http://st.stop()
rows=[]
spot_req = http://requests.get(f"https://api.upstox.com/v2/market-quote/ltp?instrument_key={urllib.parse.quote(inst, safe='')}", headers=headers).json()
spot = float(list(spot_req['data'].values())['last_price'])
for s in http://st.session_state['chain'].get('data',[]):
    ce = http://s.get('call_options',{}).get('market_data',{})
    pe = http://s.get('put_options',{}).get('market_data',{})
    http://rows.append({"Strike":s['strike_price'],"CE LTP":ce.get('ltp',0),"CE OI":ce.get('oi',0),"PE LTP":pe.get('ltp',0),"PE OI":pe.get('oi',0)})
df = http://pd.DataFrame(rows).sort_values("Strike")
atm_pos = (df["Strike"]-spot).abs().idxmin()
pos = http://df.index.get_loc(atm_pos)
df10 = http://df.iloc[max(0,pos-5):min(len(df),pos+6)]
http://st.metric(f"{idx} SPOT", spot)
http://st.dataframe(df10, use_container_width=True)
http://st.button("JUST EXECUTE - SEMI AUTO CONTROL TERE HAATH ME", use_container_width=True)[idx][0]

Ab isko ungli se dabake copy kar le Pappu, ho jayega.