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

# =====================================================================
# 3. लाइव डैशबोर्ड रूट्स (Routes)
# =====================================================================
# 🟢 इसे `@app.route('/')` के ठीक ऊपर पेस्ट करें
@app.route('/login')
def login():
    api_key = "YOUR_UPSTOX_API_KEY" # यहाँ अपनी अपस्टॉक्स एपीआई की डालें
    redirect_uri = "https://onrender.com"
    upstox_login_url = f"https://upstox.com{api_key}&redirect_uri={redirect_uri}&response_type=code"
    return redirect(upstox_login_url)
    
@app.route('/')
def home():
    # यह मुख्य डैशबोर्ड का सुंदर फ्रंट-एंड पेज लोड करेगा
    return """
    <!DOCTYPE html>
    <html lang="hi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Upstox Live Algo Dashboard</title>
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            h1 { text-align: center; color: #38bdf8; margin-bottom: 30px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .card { background-color: #1e293b; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); border: 1px solid #334155; }
            .card-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 10px; margin-bottom: 15px; }
            .index-name { font-size: 20px; font-weight: bold; color: #f1f5f9; }
            .status-badge { padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: bold; }
            .status-no { background-color: #475569; color: #cbd5e1; }
            .status-yes { background-color: #16a34a; color: #dcfce7; }
            .data-row { display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 15px; }
            .data-label { color: #94a3b8; }
            .data-value { font-weight: 600; color: #e2e8f0; }
            .pnl-box { font-size: 22px; font-weight: bold; text-align: center; padding: 10px; border-radius: 8px; margin-top: 15px; }
            .pnl-profit { background-color: rgba(22, 163, 74, 0.2); color: #4ade80; border: 1px solid #22c55e; }
            .pnl-loss { background-color: rgba(220, 38, 38, 0.2); color: #f87171; border: 1px solid #ef4444; }
            .pnl-neutral { background-color: #334155; color: #94a3b8; }
            .footer { text-align: center; margin-top: 4px; color: #64748b; font-size: 12px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Upstox Live Trading Dashboard</h1>
            <div class="grid" id="dashboard-grid">
                <!-- डेटा यहाँ जावास्क्रिप्ट के ज़रिए लोड होगा -->
            </div>
            <p class="footer">Data refreshes automatically every 2 seconds</p>
        </div>

        <script>
            function fetchMarketData() {
                // पृष्ठभूमि में डेटा अपडेट करने के लिए बैकएंड एपीआई को कॉल करना
                fetch('/api/market-data')
                    .then(response => response.json())
                    .then(data => {
                        const grid = document.getElementById('dashboard-grid');
                        grid.innerHTML = ''; // पुराना डेटा साफ़ करें

                        for (const [indexName, config] of Object.entries(data)) {
                            // PnL की स्थिति के अनुसार रंग तय करना
                            let pnlClass = 'pnl-neutral';
                            if (config.in_position) {
                                pnlClass = config.pnl >= 0 ? 'pnl-profit' : 'pnl-loss';
                            }

                            const cardHtml = `
                                <div class="card">
                                    <div class="card-header">
                                        <span class="index-name">${indexName}</span>
                                        <span class="status-badge ${config.in_position ? 'status-yes' : 'status-no'}">
                                            ${config.in_position ? 'IN POSITION (' + config.trade_type + ')' : 'NO POSITION'}
                                        </span>
                                    </div>
                                    <div class="data-row">
                                        <span class="data-label">LTP (लाइव भाव):</span>
                                        <span class="data-value" style="color: #38bdf8;">₹${config.ltp.toFixed(2)}</span>
                                    </div>
                                    <div class="data-row">
                                        <span class="data-label">RSI (1 Min):</span>
                                        <span class="data-value">${config.rsi}</span>
                                    </div>
                                    <div class="data-row">
                                        <span class="data-label">PCR (ऑप्शन चेन):</span>
                                        <span class="data-value">${config.pcr}</span>
                                    </div>
                                    <div class="data-row">
                                        <span class="data-label">Supertrend:</span>
                                        <span class="data-value" style="color: ${config.st_dir === 1 ? '#4ade80' : '#f87171'}">
                                            ${config.st_dir === 1 ? '🟢 BULLISH' : '🔴 BEARISH'}
                                        </span>
                                    </div>
                                    <div class="data-row">
                                        <span class="data-label">Qty / Target / SL:</span>
                                        <span class="data-value">${config.qty} | T: ${config.target} | SL: ${config.sl}</span>
                                    </div>
                                    <div class="pnl-box ${pnlClass}">
                                        PnL: ₹${config.pnl.toFixed(2)}
                                    </div>
                                </div>
                            `;
                            grid.innerHTML += cardHtml;
                        }
                    })
                    .catch(error => console.error('Error fetching data:', error));
            }

            // पहली बार लोड करें और फिर हर 2 सेकंड में रीफ़्रेश करें
            fetchMarketData();
            setInterval(fetchMarketData, 2000);
        </script>
    </body>
    </html>
    """

@app.route('/api/market-data')
def get_market_data():
    # यह बैकएंड फ़ंक्शन को चलाकर डेटा को ताज़ा करेगा और JSON फ़ॉर्मेट में स्क्रीन को भेजेगा
    update_marketdata_and_signals()
    return jsonify(INDEX_MAP)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)


