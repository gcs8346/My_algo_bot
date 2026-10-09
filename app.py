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

# ग्लोबल टोकन और हेडर वेरिएबल्स
ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")
BASE_HEADERS = {
    'Authorization': f'Bearer {ACCESS_TOKEN}', 
    'Accept': 'application/json'
}

def generate_auto_access_token():
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
    print(f"Executing {action} order for {index_name}")

def update_marketdata_and_signals():
    global ACTIVE_ALERT, ACCESS_TOKEN
    
    if not ACCESS_TOKEN:
        generate_auto_access_token()
        if not ACCESS_TOKEN:
            return

    for index_name, config in INDEX_MAP.items():
        try:
            url_market_quote = f"https://upstox.com{config['instrument_key']}"
            response_quote = requests.get(url_market_quote, headers=BASE_HEADERS, timeout=3).json()
            
            if response_quote.get('status') == 'success':
                instrument_data = response_quote['data'].get(config['instrument_key'])
                if instrument_data:
                    ltp = float(instrument_data['last_price'])
                    config["ltp"] = ltp
            else:
                continue

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

            url_chain = f"https://upstox.com{config['instrument_key']}&expiry_date=2026-10-26"
            response_chain = requests.get(url_chain, headers=BASE_HEADERS, timeout=3).json()
            
            if response_chain.get('status') == 'success':
                data = response_chain.get('data', [])
                total_ce = sum([s.get('call_options', {}).get('market_data', {}).get('oi', 0) for s in data[:10] if s.get('call_options')])
                total_pe = sum([s.get('put_options', {}).get('market_data', {}).get('oi', 0) for s in data[:10] if s.get('put_options')])
                config["pcr"] = round(total_pe / total_ce, 2) if total_ce > 0 else 1.0

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

# =====================================================================
# 3. लाइव डैशबोर्ड रूट्स (Routes)
# =====================================================================
@app.route('/login')
def login():
    api_key = os.getenv("UPSTOX_API_KEY", "YOUR_UPSTOX_API_KEY_HERE")
    redirect_uri = "https://onrender.com"
    upstox_login_url = f"https://upstox.com{api_key}&redirect_uri={redirect_uri}&response_type=code"
    return redirect(upstox_login_url)

@app.route('/callback')
def callback():
    global ACCESS_TOKEN, BASE_HEADERS
    code = request.args.get('code')
    if not code:
        return "Error: No code received from Upstox", 400
        
    url = "https://upstox.com"
    api_key = os.getenv("UPSTOX_API_KEY", "YOUR_UPSTOX_API_KEY_HERE")
    api_secret = os.getenv("UPSTOX_API_SECRET")
    
    payload = {
        'code': code,
        'client_id': api_key,
        'client_secret': api_secret,
        'redirect_uri': "https://onrender.com",
        'grant_type': 'authorization_code'
    }
    headers = {'accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
    
    response = requests.post(url, data=payload, headers=headers).json()
    if 'access_token' in response:
        ACCESS_TOKEN = response['access_token']
        BASE_HEADERS = {'Authorization': f'Bearer {ACCESS_TOKEN}', 'Accept': 'application/json'}
        return redirect(url_for('home'))
    else:
        return f"Login Failed: {str(response)}", 500
    
@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html lang="hi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Upstox Live Algo Dashboard</title>
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 0; }
            .market-header { background: #1e293b; color: #fff; padding: 15px; text-align: center; font-family: Arial, sans-serif; border-bottom: 2px solid #334155; position: fixed; top: 0; left: 0; width: 100%; z-index: 9999; box-sizing: border-box; }
            .live-time { font-size: 18px; margin-bottom: 8px; }
            .index-status { font-size: 16px; word-spacing: 5px; }
            .container { max-width: 1200px; margin: 90px auto 20px auto; padding: 20px; }
            h1 { text-align: center; color: #38bdf8; margin-bottom: 30px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .card { background-color: #1e293b; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); border: 1px solid #334155; }
            .card-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 10px; margin-bottom: 15px; }
            .index-name { font-size: 20px; font-weight: bold; color: #f1f5f9; }
    
