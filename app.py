import streamlit as st
import requests
import time
import pandas as pd
from urllib.parse import quote

# 1. Streamlit पेज कॉन्फ़िगरेशन (यह सबसे ऊपर होना चाहिए)
st.set_page_config(page_title="Upstox Multi-Asset Live Dashboard", layout="wide")

st.title("📈 Upstox 1-Year Token Live Dashboard")
st.caption("यह डैशबोर्ड आपके 4G इंटरनेट पर बिना किसी Static IP के लाइव डेटा सिंक कर रहा है।")

# 🔴 अपना 1 साल वाला एनेलिटिक्स टोकन नीचे दिए गए डबल कोट्स (" ") के बीच पेस्ट करें
TOKEN = "YOUR_1_YEAR_ANALYTICS_TOKEN"

# 2. चारों मुख्य इंडेक्स की लिस्ट
INDEX_MAP = {
    "NSE_INDEX|Nifty 50": "NIFTY 50",
    "NSE_INDEX|Nifty Bank": "BANK NIFTY",
    "NSE_INDEX|Nifty Fin Service": "FIN NIFTY",
    "BSE_INDEX|SENSEX": "SENSEX"
}

# 3. प्रमुख शेयरों की लिस्ट (आप इसमें कॉमा लगाकर अपने पूरे 100 शेयर जोड़ सकते हैं)
STOCK_MAP = {
    "NSE_EQ|INE002A01018": "RELIANCE",
    "NSE_EQ|INE040A01034": "HDFC BANK",
    "NSE_EQ|INE154A01025": "ITC",
    "NSE_EQ|INE090A01021": "ICICI BANK",
    "NSE_EQ|INE075A01022": "WIPRO",
    "NSE_EQ|INE238A01034": "AXIS BANK",
    "NSE_EQ|INE467B01029": "TCS",
    "NSE_EQ|INE009A01021": "INFOSYS",
    "NSE_EQ|INE245A01021": "TATA STEEL",
    "NSE_EQ|INE585B01010": "MARUTI",
}

# लाइव डेटा फेच करने का फंक्शन (जो बड़ी लिस्ट को 10-10 के टुकड़ों में मंगाता है)
def fetch_all_live_data():
    all_keys = list(INDEX_MAP.keys()) + list(STOCK_MAP.keys())
    combined_data = {}
    
    # Upstox API को ब्लॉक होने से बचाने के लिए 10-10 के टुकड़ों में डेटा मंगाना
    chunk_size = 10
    for i in range(0, len(all_keys), chunk_size):
        chunk = all_keys[i:i + chunk_size]
        instrument_query = ",".join(chunk)
        
        base_url = "https://upstox.com"
        safe_query = quote(instrument_query)
        url = f"{base_url}?instrument_key={safe_query}"
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {TOKEN}'
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                chunk_data = response.json().get('data', {})
                combined_data.update(chunk_data)
            else:
                st.error(f"API एरर: {response.status_code}")
        except Exception as e:
            st.error(f"कनेक्शन एरर: {e}")
            
    return combined_data

# स्क्रीन रिफ्रेश करने के लिए खाली कंटेनर्स (Placeholders)
index_placeholder = st.empty()
stock_placeholder = st.empty()

# लाइव डेटा सिंक लूप
while True:
    live_data = fetch_all_live_data()
    
    if live_data:
        # ---- भाग 1: चारों इंडेक्स को डिस्प्ले करना (Top Grid Metrics) ----
        with index_placeholder.container():
            st.subheader("📊 Major Market Indices")
            cols = st.columns(4)
            
            for i, (key, name) in enumerate(INDEX_MAP.items()):
                api_key_v1 = key.replace("|", ":")
                symbol_data = live_data.get(key) or live_data.get(api_key_v1) or {}
                ltp = symbol_data.get('last_price', 'N/A')
                
                with cols[i]:
                    st.metric(label=name, value=f"₹{ltp}")
        
        # ---- भाग 2: सभी शेयरों को टेबल फॉर्मेट में दिखाना ----
        with stock_placeholder.container():
            st.subheader("📑 Watchlist (Stocks)")
            
            stock_list_for_table = []
            for key, name in STOCK_MAP.items():
                api_key_v1 = key.replace("|", ":")
                symbol_data = live_data.get(key) or live_data.get(api_key_v1) or {}
                ltp = symbol_data.get('last_price', '0.0')
                
                stock_list_for_table.append({
                    "Stock Name": name,
                    "Live Price (LTP)": f"₹{ltp}",
                    "Signal": "SCANNING..."  
                })
            
            df = pd.DataFrame(stock_list_for_table)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
    # हर 2 सेकंड में डेटा स्क्रीन पर अपने आप अपडेट (Refresh) होगा
    time.sleep(2)
