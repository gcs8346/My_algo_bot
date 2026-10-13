# --- FIXED PART - Isi ko badlo ---
if chain_json and chain_json.get('status')=='success':
    data = chain_json.get('data', [])
    
    if not data or len(data)==0:
        st.error("⚠️ Option Chain खाली आया! Reason:")
        st.json(chain_json)
        st.warning("1. Expiry Date गलत है? NSE पर expiry Tue/Thu होती है\n2. Token expire हो गया? नया Token डालो\n3. Market बंद है क्या?")
        st.stop()

    rows=[]
    total_call=0
    total_put=0
    for it in data:
        try:
            strike = it.get('strike_price')
            if strike is None:
                continue
            call_m = it.get('call_options',{}).get('market_data',{}) or {}
            put_m = it.get('put_options',{}).get('market_data',{}) or {}
            call_oi = call_m.get('oi',0) or 0
            put_oi = put_m.get('oi',0) or 0
            total_call+=call_oi
            total_put+=put_oi
            rows.append({
                "Strike": strike,
                "Call LTP": call_m.get('ltp',0), "Put LTP": put_m.get('ltp',0),
                "Call OI": call_oi, "Put OI": put_oi,
                "Call Chg%": call_m.get('oi_percent_change',0) or call_m.get('oi_change_percent',0) or 0,
                "Put Chg%": put_m.get('oi_percent_change',0) or put_m.get('oi_change_percent',0) or 0,
                "Call Key": it.get('call_options',{}).get('instrument_key',''),
                "Put Key": it.get('put_options',{}).get('instrument_key',''),
                "Total OI": call_oi+put_oi
            })
        except Exception as e:
            continue
    
    if not rows:
        st.error("Rows बन नहीं पाई - Raw data देखो:")
        st.json(chain_json)
        st.stop()
        
    df = pd.DataFrame(rows).sort_values("Strike")
    # ... बाकी कोड वैसा ही ...
else:
    st.error(f"Chain Fetch Fail! Full Response:")
    st.json(chain_json)
    st.info("👉 Solution: Upstox Token रोज बदलता है। आज का नया Token डालो। Expiry Date = 2026-10-14 रखो।")
    st.stop()