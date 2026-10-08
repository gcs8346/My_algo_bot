import os
import time
import requests
import numpy as np
import pandas as pd
from flask import Flask, render_template, jsonify, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super_secret_algo_key_change_this")

# =====================================================================
# 1. सुरक्षा कॉन्फ़िगरेशन (Render Dashboard से लोड होगा)
# =====================================================================
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD")

# ग्लोबल टोकन और हेडर वेरिएबल्स (अब यह सीधे Render Environment से लोड होंगे)
ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")
BASE_HEADERS = {
    'Authorization': f'Bearer {ACCESS_TOKEN}', 
    'Accept': 'application/json'
}

def generate_auto_access_token():
    """
    Render पर अटकने से बचने के लिए, टोकन सीधे Environment से उठाया जा रहा है।
    """
    global ACCESS_TOKEN, BASE_HEADERS
    ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")
    if not ACCESS_TOKEN:
        print("⚠️ एरर: Render Dashboard में 'UPSTOX_ACCESS_TOKEN' सेट नहीं है!")
        return None
    BASE_HEADERS = {'Authorization': f'Bearer {ACCESS_TOKEN}', 'Accept': 'application/json'}
    return ACCESS_TOKEN

# =====================================================================
# 2. लाइव रणनीति और डेटा मैट्रिक्स
# =====================================================================
INDEX_MAP = {
    "NIFTY50": {
        "instrument_key": "NSE_INDEX|Nifty 50", "fut_key": "NSE_FO|NIFTY26OCTFUT",
        "qty": 25, "target": 30, "sl": 15, "trail_points": 2, "ltp": 0.0, "rsi": 0.0, "st_dir": 1, "pcr": 1.0,
        "in_position": False, "trade_type": None, "entry_price": 0, "sl_price": 0, "target_price": 0, "pnl": 0, "highest_ltp": 0, "lowest_ltp": 999999
    },
    "SENSEX": {
        "instrument_key": "BSE_INDEX|SENSEX", "fut_key": "BSE_FO|SENSEX26OCTFUT",
        "qty": 10, "target": 120, "sl": 60, "trail_points": 5, "ltp": 0.0, "rsi": 0.0, "st_dir": 1, "pcr": 1.0,
        "in_position": False, "trade_type": None, "entry_price": 0, "sl_price": 0, "target_price": 0, "pnl": 0, "highest_ltp": 0, "lowest_ltp": 999999
    },
    "BANKNIFTY": {
        "instrument_key": "NSE_INDEX|Nifty Bank", "fut_key": "NSE_FO|BANKNIFTY26OCTFUT",
        "qty": 15, "target": 40, "sl": 25, "trail_points": 3, "ltp": 0.0, "rsi": 0.0, "st_dir": 1, "pcr": 1.0,
        "in_position": False, "trade_type": None, "entry_price": 0, "sl_price": 0, "target_price": 0, "pnl": 0, "highest_ltp": 0, "lowest_ltp": 999999
    }
}

ACTIVE_ALERT = {"has_alert": False, "index_name": "", "signal_type": "", "ltp": 0}

def execute_order_slice(index_name, action):
    # यह सिर्फ एक डमी फ़ंक्शन है ताकि नीचे दिया कोड क्रैश न हो।
    # अगर आपके पास आपका असली ऑर्डर फ़ंक्शन है, तो उसे यहाँ रखें।
    print(f"Executing {action} order for {index_name}")

def update_marketdata_and_signals():
    global ACTIVE_ALERT, ACCESS_TOKEN
    
    # हर डेटा रिक्वेस्ट पर टोकन की वैधता जाँचना
    if not ACCESS_TOKEN:
        generate_auto_access_token()
        if not ACCESS_TOKEN:
            return

    for index_name, config in INDEX_MAP.items():
        try:
            # A. असली भाव (LTP) खींचना
            # ध्यान दें: Upstox V2 API का सही URL स्ट्रक्चर इस्तेमाल करें, जैसे: f"https://upstox.com{config['instrument_key']}"
            url_market_quote = f"https://upstox.com{config['instrument_key']}"
            response_quote = requests.get(url_market_quote, headers=BASE_HEADERS, timeout=3).json()
            
            if response_quote.get('status') == 'success':
                # अपस्टॉक्स V2 API रिस्पांस पाथ
                instrument_data = response_quote['data'].get(config['instrument_key'])
                if instrument_data:
                    ltp = float(instrument_data['last_price'])
                    config["ltp"] = ltp
            else:
                continue

            # B. कैंडल्स फेच करना (RSI/Supertrend)
            url_candles = f"https://upstox.com{config['instrument_key']}/1minute"
            response_candles = requests.get(url_candles, headers=BASE_HEADERS, timeout=3).json()
            
            if response_candles.get('status') == 'success':
                candle_data = response_candles.get('data', {}).get('candles', [])
                if candle_data:
                    df = pd.DataFrame(candle_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi'])
                    df = df.iloc[::-1].reset_index(drop=True)
                    df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].apply(pd.to_numeric)
                    
                    change = df['close'].diff()
                    gain = change.mask(change < 0, 0)
                    loss = -change.mask(change > 0, 0)
                    avg_gain = gain.ewm(com=13, min_periods=14).mean()
                    avg_loss = loss.ewm(com=13, min_periods=14).mean()
                    config["rsi"] = round((100 - (100 / (1 + (avg_gain / avg_loss)))).iloc[-1], 2)
                    
                    hl2 = (df['high'] + df['low']) / 2
                    ranges = pd.concat([df['high'] - df['low'], np.abs(df['high'] - df['close'].shift()), np.abs(df['low'] - df['close'].shift())], axis=1)
                    atr = ranges.max(axis=1).ewm(alpha=1/10, min_periods=10).mean()
                    config["st_dir"] = 1 if ltp > (hl2 + (3 * atr)).iloc[-1] else -1

            # C. ऑप्शन चेन और PCR
            # ध्यान दें: लाइव अपस्टॉक्स API के अनुसार सही URL का उपयोग करें
            url_chain = f"https://upstox.com{config['instrument_key']}&expiry_date=2026-10-26"
            response_chain = requests.get(url_chain, headers=BASE_HEADERS, timeout=3).json()
            
            if response_chain.get('status') == 'success':
                data = response_chain.get('data', [])
                total_ce = sum([s.get('call_options', {}).get('market_data', {}).get('oi', 0) for s in data[:10] if s.get('call_options')])
                total_pe = sum([s.get('put_options', {}).get('market_data', {}).get('oi', 0) for s in data[:10] if s.get('put_options')])
                config["pcr"] = round(total_pe / total_ce, 2) if total_ce > 0 else 1.0

            # --- एक्टिव पोजीशन रिस्क मैनेजमेंट (ऑटोमैटिक ट्रेलिंग एसएल) ---
            if config["in_position"]:
                if config["trade_type"] == "CALL":
                    config["pnl"] = round((ltp - config["entry_price"]) * config["qty"], 2)
                    if ltp > config["highest_ltp"]:
                        config["highest_ltp"] = ltp
                        new_sl = ltp - config["sl"]
                        if new_sl > config["sl_price"]:
                            config["sl_price"] = round(new_sl, 2)
                    if ltp >= config["target_price"] or ltp <= config["sl_price"]:
                        execute_order_slice(index_name, "SELL")
                else:
                    config["pnl"] = round((config["entry_price"] - ltp) * config["qty"], 2)
                    if ltp < config["lowest_ltp"]:
                        config["lowest_ltp"] = ltp
                        new_sl = ltp + config["sl"]
                        if new_sl < config["sl_price"]:
                            config["sl_price"] = round(new_sl, 2)
                    if ltp <= config["target_price"] or ltp >= config["sl_price"]:
                        execute_order_slice(index_name, "SELL")
        except Exception as e:  
            
          print(f"Error updating market data for {index_name}: {str(e)}")

# 🟢 YAHAN SE LEKAR SABSE NICHE TAK PURA PASTE KAREIN:

@app.route('/')
def home():
    return "<h1>Upstox Trading Dashboard is Live!</h1><p>Backend calculations are running successfully.</p>"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

