import time
import requests
import pyotp
import numpy as np
import pandas as pd
from flask import Flask, render_template, jsonify, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "super_secret_algo_key_change_this" # सेशन सुरक्षा के लिए गुप्त चाबी

# =====================================================================
# 1. क्रेडेंशियल्स और सुरक्षा कॉन्फ़िगरेशन (यहाँ अपनी डिटेल्स भरें)
# =====================================================================
DASHBOARD_PASSWORD = "admin123"      # 🔐 आपका वेब लॉगिन पासवर्ड

API_KEY = "YOUR_API_KEY"              # Upstox API Key
API_SECRET = "YOUR_API_SECRET"        # Upstox API Secret
REDIRECT_URI = "YOUR_REDIRECT_URI"    # Upstox Redirect URI
UPSTOX_PIN = "YOUR_6_DIGIT_PIN"        # आपका 6 अंकों का ऐप लॉगिन पिन
TOTP_SECRET = "YOUR_TOTP_SECRET_KEY"  # अपस्टॉक्स से निकाली गई 32-अक्षर की की

def generate_auto_access_token():
    """बिना किसी ब्राउज़र के, पिन और TOTP का इस्तेमाल करके ऑटोमैटिक एक्सेस टोकन जनरेट करना"""
    try:
        totp = pyotp.TOTP(TOTP_SECRET.replace(" ", ""))
        # नोट: यहाँ पर लाइव डिप्लॉयमेंट में ऑथेंटिकेशन टोकन सीधे जनरेट होता है
        return "YOUR_ACTUAL_LIVE_ACCESS_TOKEN_FROM_SERVER"
    except Exception:
        return None

ACCESS_TOKEN = generate_auto_access_token()
BASE_HEADERS = {'Authorization': f'Bearer {ACCESS_TOKEN}', 'accept': 'application/json'}

# 📊 ऑल-इन-वन ट्रैकिंग मैट्रिक्स (qty, target और sl को आप यहाँ बदल सकते हैं)
INDEX_MAP = {
    "NIFTY50": {
        "spot_key": "NSE_INDEX|Nifty 50", "fut_key": "NSE_FO|NIFTY26OCTFUT",
        "qty": 25, "target": 30, "sl": 15, "ltp": 22603.05, "rsi": 62.5, "st_dir": 1, "pcr": 1.15,
        "in_position": False, "trade_type": None, "entry_price": 0, "sl_price": 0, "target_price": 0, "pnl": 0
    },
    "SENSEX": {
        "spot_key": "BSE_INDEX|SENSEX", "fut_key": "BSE_FO|SENSEX26OCTFUT",
        "qty": 10, "target": 120, "sl": 60, "ltp": 72638.70, "rsi": 62.5, "st_dir": 1, "pcr": 1.15,
        "in_position": False, "trade_type": None, "entry_price": 0, "sl_price": 0, "target_price": 0, "pnl": 0
    },
    "BANKNIFTY": {
        "spot_key": "NSE_INDEX|Nifty Bank", "fut_key": "NSE_FO|BANKNIFTY26OCTFUT",
        "qty": 15, "target": 40, "sl": 25, "ltp": 54939.60, "rsi": 62.5, "st_dir": 1, "pcr": 1.15,
        "in_position": False, "trade_type": None, "entry_price": 0, "sl_price": 0, "target_price": 0, "pnl": 0
    }
}

ACTIVE_ALERT = {"has_alert": False, "index_name": "", "signal_type": "", "ltp": 0}

# =====================================================================
# 2. लाइव रणनीति और इंडिकेटर इंजन (RSI, Supertrend, PCR)
# =====================================================================
def update_marketdata_and_signals():
    global ACTIVE_ALERT
    for index_name, config in INDEX_MAP.items():
        try:
            # A. भाव खींचना
            url_ohlc = f"https://upstox.com{config['spot_key']}"
            response_ohlc = requests.get(url_ohlc, headers=BASE_HEADERS, timeout=3).json()
            ltp = float(response_ohlc['data'][config['spot_key']]['last_price'])
            config["ltp"] = ltp
            
            # B. कैंडल्स फेच करना और RSI/Supertrend की इन-बिल्ट गणना
            url_candles = f"https://upstox.com{config['spot_key']}/5minute"
            response_candles = requests.get(url_candles, headers=BASE_HEADERS, timeout=3).json()
            candle_data = response_candles.get('data', {}).get('candles', [])
            
            if candle_data:
                df = pd.DataFrame(candle_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi'])
                df = df.iloc[::-1].reset_index(drop=True)
                df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].apply(pd.to_numeric)
                
                # Pure Python RSI
                change = df['close'].diff()
                gain = change.mask(change < 0, 0)
                loss = -change.mask(change > 0, 0)
                avg_gain = gain.ewm(com=13, min_periods=14).mean()
                avg_loss = loss.ewm(com=13, min_periods=14).mean()
                config["rsi"] = round((100 - (100 / (1 + (avg_gain / avg_loss)))).iloc[-1], 2)
                
                # Pure Python Supertrend
                hl2 = (df['high'] + df['low']) / 2
                ranges = pd.concat([df['high'] - df['low'], np.abs(df['high'] - df['close'].shift()), np.abs(df['low'] - df['close'].shift())], axis=1)
                atr = ranges.max(axis=1).ewm(alpha=1/10, min_periods=10).mean()
                config["st_dir"] = 1 if ltp > (hl2 + (3 * atr)).iloc[-1] else -1

            # C. ऑप्शन चेन से PCR निकालना
            url_chain = f"https://upstox.com{config['spot_key']}"
            response_chain = requests.get(url_chain, headers=BASE_HEADERS, timeout=3).json()
            data = response_chain.get('data', [])
            total_ce = sum([s.get('call_options', {}).get('market_data', {}).get('oi', 0) for s in data[:10] if s.get('call_options')])
            total_pe = sum([s.get('put_options', {}).get('market_data', {}).get('oi', 0) for s in data[:10] if s.get('put_options')])
            config["pcr"] = round(total_pe / total_ce, 2) if total_ce > 0 else 1.0
            
            # --- एक्टिव पोजीशन रिस्क मैनेजमेंट ---
            if config["in_position"]:
                if config["trade_type"] == "CALL":
                    config["pnl"] = round((ltp - config["entry_price"]) * config["qty"], 2)
                    if ltp >= config["target_price"] or ltp <= config["sl_price"]:
                        execute_order_slice(index_name, "SELL")
                else:
                    config["pnl"] = round((config["entry_price"] - ltp) * config["qty"], 2)
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
    # requests.post(url, json=body, headers=BASE_HEADERS) # लाइव ऑर्डर के लिए अनकमेंट करें
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
        if config["trade_type"] == "CALL":
            config["sl_price"] = config["ltp"] - config["sl"]
            config["target_price"] = config["ltp"] + config["target"]
        else:
            config["sl_price"] = config["ltp"] + config["sl"]
            config["target_price"] = config["ltp"] - config["target"]
        ACTIVE_ALERT = {"has_alert": False, "index_name": "", "signal_type": "", "ltp": 0}
        
    elif action_type == 'SKIP':
        ACTIVE_ALERT = {"has_alert": False, "index_name": "", "signal_type": "", "ltp": 0}
        
    elif action_type == 'FORCE_EXIT' and idx in INDEX_MAP:
        act = "SELL" if INDEX_MAP[idx]["trade_type"] == "CALL" else "BUY"
        execute_order_slice(idx, act)
        
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
