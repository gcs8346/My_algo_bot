import os
import random
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# --- TRADING CONF-PARAMETERS & INITIAL DATA ---
# आपके 5 दिन के सेटअप के अनुसार डिफॉल्ट डेटा स्ट्रक्चर
MARKET_DATA = {
    "BANKNIFTY": {
        "ltp": 54750.00, "prev_close": 54515.05, "rsi": 58, "pcr": 1.15,
        "supertrend": "BULLISH", "signal": "BUY", "qty": 15, "target": 40, "sl": 25, "trailing_sl": 5,
        "entry_price": 54710.00, "status": "NO POSITION", "pnl": 0.0
    },
    "NIFTY50": {
        "ltp": 22506.45, "prev_close": 22230.00, "rsi": 62, "pcr": 1.05,
        "supertrend": "BULLISH", "signal": "BUY", "qty": 25, "target": 30, "sl": 15, "trailing_sl": 3,
        "entry_price": 22480.00, "status": "NO POSITION", "pnl": 0.0
    },
    "SENSEX": {
        "ltp": 72362.73, "prev_close": 71600.00, "rsi": 55, "pcr": 0.98,
        "supertrend": "BULLISH", "signal": "BUY", "qty": 10, "target": 120, "sl": 60, "trailing_sl": 10,
        "entry_price": 72300.00, "status": "NO POSITION", "pnl": 0.0
    }
}

# --- REAL-TIME CALCULATION LOGIC (LIVE SIGNALS & SL/TARGET) ---
def update_live_signals():
    for index, data in MARKET_DATA.items():
        # लाइव भाव में हल्का उतार-चढ़ाव (Simulated for Live Dashboard View)
        change = random.uniform(-15, 15) if index != "NIFTY50" else random.uniform(-5, 5)
        data["ltp"] = round(data["ltp"] + change, 2)
        
        # RSI और PCR डायनामिक अपडेट
        data["rsi"] = random.randint(45, 70)
        
        # PnL और Stop Loss / Target हिट चेकिंग लॉजिक
        if data["status"] == "IN POSITION":
            points_gained = data["ltp"] - data["entry_price"]
            data["pnl"] = round(points_gained * data["qty"], 2)
            
            # Stop Loss Breached?
            if points_gained <= -data["sl"]:
                data["status"] = "SL HIT (STOP LOSS)"
                data["pnl"] = round(-data["sl"] * data["qty"], 2)
            # Target Hit?
            elif points_gained >= data["target"]:
                data["status"] = "TARGET ACHIEVED"
                data["pnl"] = round(data["target"] * data["qty"], 2)
        else:
            # रैंडमली पोजीशन ट्रिगर करने के लिए (टेस्टिंग के लिए)
            if random.random() < 0.1:
                data["status"] = "IN POSITION"
                data["entry_price"] = data["ltp"]

@app.route('/api/live-data')
def live_data():
    update_live_signals()
    return jsonify(MARKET_DATA)

@app.route('/')
def home():
    # आपका पूरा HTML UI, CSS स्टाइल और लाइव जावास्क्रिप्ट सिंक मैकेनिज्म
    return """<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Upstox Super-Trend Live Terminal</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; background-color: #0b0f19; color: #e2e8f0; margin: 0; padding: 15px; }
        .dashboard-header { text-align: center; padding: 15px; background: #111827; border-radius: 8px; border-bottom: 3px solid #3b82f6; margin-bottom: 20px; }
        .main-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 20px; max-width: 1300px; margin: 0 auto; }
        .index-card { background: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155; position: relative; overflow: hidden; }
        .index-name { font-size: 1.6rem; font-weight: 800; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #475569; padding-bottom: 8px; }
        .pos-badge { font-size: 0.8rem; padding: 3px 8px; border-radius: 6px; background: #475569; color: #fff; }
        .pos-in { background: #ea580c !important; animation: pulse 2s infinite; }
        .pos-sl { background: #dc2626 !important; }
        .pos-target { background: #16a34a !important; }
        .metrics-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px; }
        .metric-box { background: #0f172a; padding: 10px; border-radius: 6px; border: 1px solid #1e293b; }
        .label { font-size: 0.85rem; color: #94a3b8; display: block; margin-bottom: 3px; }
        .value { font-size: 1.15rem; font-weight: bold; }
        .bullish-text { color: #22c55e; font-weight: bold; }
        .bearish-text { color: #ef4444; font-weight: bold; }
        .pnl-box { grid-column: span 2; text-align: center; background: #111827; padding: 12px; border-radius: 8px; font-size: 1.3rem; margin-top: 10px; }
        .footer-banner { text-align: center; margin-top: 30px; color: #64748b; font-size: 0.85rem; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.6; } 100% { opacity: 1; } }
    </style>
</head>
<body>

<div class="dashboard-header">
    <h1 style="margin:0; font-size: 1.8rem;">📊 Upstox Live Trading Dashboard (A to Z Super Terminal)</h1>
</div>

<div class="main-container">
    <!-- BANKNIFTY -->
    <div class="index-card" id="card-BANKNIFTY">
        <div class="index-name">BANKNIFTY <span class="pos-badge" id="status-BANKNIFTY">NO POSITION</span></div>
        <div class="metrics-grid">
            <div class="metric-box"><span class="label">LTP (लाइव भाव):</span><span class="value" id="ltp-BANKNIFTY">₹0.00</span></div>
            <div class="metric-box"><span class="label">Supertrend:</span><span id="supertrend-BANKNIFTY">🟢 BULLISH</span></div>
            <div class="metric-box"><span class="label">RSI (1 Min):</span><span class="value" id="rsi-BANKNIFTY">0</span></div>
            <div class="metric-box"><span class="label">PCR (ऑप्शन चेन):</span><span class="value" id="pcr-BANKNIFTY">1</span></div>
            <div class="metric-box" style="grid-column: span 2;"><span class="label">Qty / Target / SL / Trailing SL:</span><span class="value" style="font-size:1rem;" id="rules-BANKNIFTY">15 | T: 40 | SL: 25 | TSL: 5</span></div>
            <div class="pnl-box">PnL: <span id="pnl-BANKNIFTY">₹0.00</span></div>
        </div>
    </div>

    <!-- NIFTY50 -->
    <div class="index-card" id="card-NIFTY50">
        <div class="index-name">NIFTY50 <span class="pos-badge" id="status-NIFTY50">NO POSITION</span></div>
        <div class="metrics-grid">
            <div class="metric-box"><span class="label">LTP (लाइव भाव):</span><span class="value" id="ltp-NIFTY50">₹0.00</span></div>
            <div class="metric-box"><span class="label">Supertrend:</span><span id="supertrend-NIFTY50">🟢 BULLISH</span></div>
            <div class="metric-box"><span class="label">RSI (1 Min):</span><span class="value" id="rsi-NIFTY50">0</span></div>
            <div class="metric-box"><span class="label">PCR (ऑप्शन चेन):</span><span class="value" id="pcr-NIFTY50">1</span></div>
            <div class="metric-box" style="grid-column: span 2;"><span class="label">Qty / Target / SL / Trailing SL:</span><span class="value" style="font-size:1rem;" id="rules-NIFTY50">25 | T: 30 | SL: 15 | TSL: 3</span></div>
            <div class="pnl-box">PnL: <span id="pnl-NIFTY50">₹0.00</span></div>
        </div>
    </div>

    <!-- SENSEX -->
    <div class="index-card" id="card-SENSEX">
        <div class="index-name">SENSEX <span class="pos-badge" id="status-SENSEX">NO POSITION</span></div>
        <div class="metrics-grid">
            <div class="metric-box"><span class="label">LTP (लाइव भाव):</span><span class="value" id="ltp-SENSEX">₹0.00</span></div>
            <div class="metric-box"><span class="label">Supertrend:</span><span id="supertrend-SENSEX">🟢 BULLISH</span></div>
            <div class="metric-box"><span class="label">RSI (1 Min):</span><span class="value" id="rsi-SENSEX">0</span></div>
            <div class="metric-box"><span class="label">PCR (ऑप्शन चेन):</span><span class="value" id="pcr-SENSEX">1</span></div>
            <div class="metric-box" style="grid-column: span 2;"><span class="label">Qty / Target / SL / Trailing SL:</span><span class="value" style="font-size:1rem;" id="rules-SENSEX">10 | T: 120 | SL: 60 | TSL: 10</span></div>
            <div class="pnl-box">PnL: <span id="pnl-SENSEX">₹0.00</span></div>
        </div>
    </div>
</div>

<div class="footer-banner">🔄 Data refreshes automatically every 2 seconds via WebSocket/API Stream</div>

<script>
    async function fetchLiveTerminalData() {
        try {
            const response = await fetch('/api/live-data');
            const data = await response.json();
            
            for (const key in data) {
                const item = data[key];
                document.getElementById(`ltp-${key}`).innerText = '₹' + item.ltp;
                document.getElementById(`rsi-${key}`).innerText = item.rsi;
                document.getElementById(`pcr-${key}`).innerText = item.pcr;
                
                // PnL Color Update
                const pnlEl = document.getElementById(`pnl-${key}`);
                pnlEl.innerText = '₹' + item.pnl;
                if(item.pnl > 0) pnlEl.style.color = '#22c55e';
                else if(item.pnl < 0) pnlEl.style.color = '#ef4444';
                else pnlEl.style.color = '#94a3b8';

                // Status Badge Control
                const statusEl = document.getElementById(`status-${key}`);
                statusEl.innerText = item.status;
                statusEl.className = "pos-badge";
                if(item.status === "IN POSITION") statusEl.classList.add("pos-in");
                if(item.status.includes("SL")) statusEl.classList.add("pos-sl");
                if(item.status.includes("TARGET")) statusEl.classList.add("pos-target");
            }
        } catch (error) {
            console.error("Error fetching trading data:", error);
        }
    }
    setInterval(fetchLiveTerminalData, 2000);
    fetchLiveTerminalData();
</script>
</body>
</html>"""

if __name__ == '__main__':
    # Render और लोकल होस्ट दोनों के लिए पोर्ट बाइंडिंग फिक्स
    port = int(os.environ.get("PORT", 10000))
                
