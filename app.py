import os
import time
import requests
import pyotp
import numpy as np
import pandas as pd
from flask import Flask, render_template, jsonify, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super_secret_algo_key_change_this")

# =====================================================================
# 1. सुरक्षा कॉन्फ़िगरेशन (Render Dashboard से लोड होगा)
# =====================================================================
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD")

API_KEY = os.getenv("UPSTOX_API_KEY")
API_SECRET = os.getenv("UPSTOX_API_SECRET")
REDIRECT_URI = os.getenv("UPSTOX_REDIRECT_URI")
UPSTOX_PIN = os.getenv("UPSTOX_PIN")
TOTP_SECRET = os.getenv("UPSTOX_TOTP_SECRET_KEY")

def generate_auto_access_token():
    if not TOTP_SECRET or not API_KEY:
        return None
    try:
        totp = pyotp.TOTP(TOTP_SECRET.replace(" ", ""))
        return os.getenv("UPSTOX_ACCESS_TOKEN")
    except Exception:
        return None

ACCESS_TOKEN = generate_auto_access_token()
BASE_HEADERS = {'Authorization': f'Bearer {ACCESS_TOKEN}', 'Accept': 'application/json'}

# 📊 ऑल-इन-वन ट्रैकिंग मैट्रिक्स (इसमें ट्रेलिंग पॉइंट्स भी जोड़ दिए हैं)
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

# =====================================================================
# 2. लाइव रणनीति, इंडिकेटर और ऑटोमैटिक ट्रेलिंग रिस्क इंजन
# =====================================================================
def update_marketdata_and_signals():
    global ACTIVE_ALERT
    if not ACCESS_TOKEN:
        return

    for index_name, config in INDEX_MAP.items():
        try:
            # A. असली भाव (LTP) खींचना
            url_market_quote = f"https://upstox.com{config['instrument_key']}"
            response_quote = requests.get(url_market_quote, headers=BASE_HEADERS, timeout=3).json()
            
            if response_quote.get('status') == 'success':
                ltp = float(response_quote['data'][config['instrument_key']]['last_price'])
                config["ltp"] = ltp
            else:
                continue

            # B. कैंडल्स फेच करना (RSI/Supertrend)
            url_candles = f"https://upstox.com{config['instrument_key']}"
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
            url_chain = f"https://upstox.com{config['instrument_key']}"
            response_chain = requests.get(url_chain, headers=BASE_HEADERS, timeout=3).json()
            
            if response_chain.get('status') == 'success':
                data = response_chain.get('data', [])
                total_ce = sum([s.get('call_options', {}).get('market_data', {}).get('oi', 0) for s in data[:10] if s.get('call_options')])
                total_pe = sum([s.get('put_options', {}).get('market_data', {}).get('oi', 0) for s in data[:10] if s.get('put_options')])
                config["pcr"] = round(total_pe / total_ce, 2) if total_ce > 0 else 1.0

            # --- 🛠️ एक्टिव पोजीशन रिस्क मैनेजमेंट (ऑटोमैटिक ट्रेलिंग एसएल के साथ) ---
            if config["in_position"]:
                if config["trade_type"] == "CALL":
                    config["pnl"] = round((ltp - config["entry_price"]) * config["qty"], 2)
                    
                    # 🔄 ट्रेलिंग लॉजिक (CALL): अगर नया हाई बना, तो SL ऊपर खिसकाओ
                    if ltp > config["highest_ltp"]:
                        config["highest_ltp"] = ltp
                        new_sl = ltp - config["sl"]
                        if new_sl > config["sl_price"]:
                            config["sl_price"] = round(new_sl, 2)
                    
                    # टारगेट या ट्रेलिंग स्टॉप लॉस हिट होने पर एग्जिट
                    if ltp >= config["target_price"] or ltp <= config["sl_price"]:
                        execute_order_slice(index_name, "SELL")
                else:
                    config["pnl"] = round((config["entry_price"] - ltp) * config["qty"], 2)
                    
                    # 🔄 ट्रेलिंग लॉजिक (PUT): अगर नया लो बना, तो SL नीचे खिसकाओ
                    if ltp < config["lowest_ltp"]:
                        config["lowest_ltp"] = ltp
                        new_sl = ltp + config["sl"]
                        if new_sl < config["sl_price"]:
                            config["sl_price"] = round(new_sl, 2)
                            
                    # टारगेट या ट्रेलिंग स्टॉप लॉस हिट होने पर एग्जिट
                    if ltp <= config["target_price"] or ltp >= config["sl_price"]:
                        execute_order_slice(index_name, "BUY")
            else:
                # --- CALL / PUT अलर्ट जनरेटर ---
                if config["rsi"] > 60 and config["st_dir"] == 1 and config["pcr"] > 1.10 and not ACTIVE_ALERT["has_alert"]:
                    ACTIVE_ALERT = {"has_alert": True, "index_name": index_name, "signal_type": "CALL (BUY)", "ltp": ltp}
                elif config["rsi"] < 40 and config["st_dir"] == -1 and config["pcr"] < 0.85 and not ACTIVE_ALERT["has_alert"]:
                    ACTIVE_ALERT = {"has_alert": True, "index_name": index_name, "signal_type": "PUT (SHORT)", "ltp": ltp}
        except Exception:
            pass

def execute_order_slice(index_name, action):
    config = INDEX_MAP[index_name]
    url = "https://upstox.com"
    body = {"quantity": config["qty"], "product": "I", "validity": "DAY", "price": 0, "tag": "WebAlgo", "instrument_token": config["fut_key"], "order_type": "MARKET", "transaction_type": action}
    # requests.post(url, json=body, headers=BASE_HEADERS) # लाइव ट्रेड के लिए अनकमेंट करें
    config["in_position"] = False
    config["pnl"] = 0

# =====================================================================
# 3. वेब राउटिंग और ऑथेंटिकेशन गेटवे
# =====================================================================
@app.route('/', methods=['GET', 'POST'])
def login():
    if 'logged_in' in session: return redirect(url_for('dashboard'))
    error = None
    if request.method == 'POST':
        if request.form['password'] == DASHBOARD_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        error = "⚠️ गलत पासवर्ड! दोबारा कोशिश करें।"
    return render_template('login.html', error=error)

@app.route('/dashboard')
def dashboard():
    if 'logged_in' not in session: return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/api/data')
def get_data():
    if 'logged_in' not in session: return jsonify({"status": "unauthorized"}), 401
    update_marketdata_and_signals()
    return jsonify({"indices": INDEX_MAP, "alert": ACTIVE_ALERT})

@app.route('/api/action', methods=['POST'])
def handle_action():
    if 'logged_in' not in session: return jsonify({"status": "unauthorized"}), 401
    global ACTIVE_ALERT
    req = request.json
    action_type = req.get('action')
    idx = req.get('index')
    
    if action_type == 'EXECUTE' and ACTIVE_ALERT["has_alert"]:
        target_idx = ACTIVE_ALERT["index_name"]
        config = INDEX_MAP[target_idx]
        config["in_position"] = True
        config["trade_type"] = "CALL" if ACTIVE_ALERT["signal_type"] == "CALL (BUY)" else "PUT"
        config["entry_price"] = config["ltp"]

