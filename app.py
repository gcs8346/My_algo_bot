import streamlit as st
import requests
import time
import pandas as pd

# Streamlit पेज कॉन्फ़िगरेशन (यह सबसे ऊपर होना चाहिए)
st.set_page_config(page_title="Upstox Multi-Asset Live Dashboard", layout="wide")

st.title("📈 Upstox 1-Year Token Live Dashboard")
st.caption("यह डैशबोर्ड आपके 4G इंटरनेट पर बिना किसी Static IP के लाइव डेटा सिंक करेगा।")

# 🔴 अपना 1 साल वाला एनेलिटिक्स टोकन यहाँ डालें
TOKEN = "YOUR_1_YEAR_ANALYTICS_TOKEN"

# 1. चारों मुख्य इंडेक्स की लिस्ट
INDEX_MAP = {
    "NSE_INDEX|Nifty 50": "NIFTY 50",
    "NSE_INDEX|Nifty Bank": "BANK NIFTY",
    "NSE_INDEX|Nifty Fin Service": "FIN NIFTY",
    "BSE_INDEX|SENSEX": "SENSEX"
}

# 2. आपके 100 स्टॉक की लिस्ट (उदाहरण के लिए मुख्य स्टॉक दिए हैं, आप इसमें और जोड़ सकते हैं)
# फॉर्मेट हमेशा "NSE_EQ|ISIN_CODE" या सीधे ट्रेडिंग सिंबल होना चाहिए। Upstox LTP API में आप सीधे प्रमुख NSE सिंबल भी पास कर सकते हैं।
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
    # आप इसी तरह कॉमा लगाकर पूरे 100 स्टॉक की लिस्ट यहाँ बना सकते हैं...
}

# सभी इंस्ट्रूमेंट की चाबियों (Keys) को एक साथ जोड़ना
all_keys = list(INDEX_MAP.keys()) + list(STOCK_MAP.keys())
instrument_query = ",".join(all_keys)

# लाइव डेटा फेच करने का फंक्शन (सिर्फ LTP API - नो स्टैटिक आईपी रिक्वायर्ड)
def fetch_live_ltp():
    url = f"https://upstox.com{instrument_query}"
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {TOKEN}'
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('data', {})
        else:
            st.error(f"API एरर: {response.text}")
            return None
    except Exception as e:
        st.error(f"कनेक्शन एरर: {e}")
        return None

# स्क्रीन पर डेटा रेंडर करने के लिए प्लेसहोल्डर्स
index_placeholder = st.empty()
stock_placeholder = st.empty()

# लाइव डेटा सिंक लूप
while True:
    live_data = fetch_live_ltp()
    
    if live_data:
        # ---- भाग 1: चारों इंडेक्स को डिस्प्ले करना (Top Grid Layout) ----
        with index_placeholder.container():
            st.subheader("📊 Major Market Indices")
            cols = st.columns(4)
            
            for i, (key, name) in enumerate(INDEX_MAP.items()):
                # Upstox API रिस्पॉन्स में कीज़ का फॉर्मेट 'NSE_INDEX:Nifty 50' होता है
                api_key = key.replace("|", ":")
                symbol_data = live_data.get(api_key, {})
                ltp = symbol_data.get('last_price', 'N/A')
                
                with cols[i]:
                    st.metric(label=name, value=f"₹{ltp}")
        
        # ---- भाग 2: सभी 100 शेयरों को टेबल फॉर्मेट में दिखाना ----
        with stock_placeholder.container():
            st.subheader("📑 Watchlist (Stocks)")
            
            stock_list_for_table = []
            for key, name in STOCK_MAP.items():
                api_key = key.replace("|", ":")
                symbol_data = live_data.get(api_key, {})
                ltp = symbol_data.get('last_price', '0.0')
                
                # यहाँ आप अपना EMA क्रॉसओवर चेक करने का लॉजिक लगाकर सिग्नल (BUY/SELL) भी जोड़ सकते हैं
                stock_list_for_table.append({
                    "Stock Name": name,
                    "Live Price (LTP)": f"₹{ltp}",
                    "Signal": "SCANNING..."  # यहाँ कंडीशन के आधार पर 'BUY' या 'SELL' प्रिंट कराएं
                })
            
            # डेटा को सुंदर टेबल (DataFrame) में कनवर्ट करके दिखाना
            df = pd.DataFrame(stock_list_for_table)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
    # हर 2 सेकंड में डेटा स्क्रीन पर अपने आप अपडेट (Refresh) होगा
    time.sleep(2)
