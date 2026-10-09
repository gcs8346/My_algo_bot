import os
import random
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# --- 1. आपका 5 दिन का पूरा ट्रेडिंग कॉन्फ़िगरेशन डेटा ---
MARKET_DATA = {
    "BANKNIFTY": {
        "ltp": 54750.00, "rsi": 58, "pcr": 1.15, "supertrend": "BULLISH", 
        "qty": 15, "target": 40, "sl": 25, "pnl": 0.0, "status": "NO POSITION", "entry_price": 0.0
    },
    "NIFTY50": {
        "ltp": 22506.45, "rsi": 62, "pcr": 1.05, "supertrend": "BULLISH", 
        "qty": 25, "target": 30, "sl": 15, "pnl": 0.0, "status": "NO POSITION", "entry_price": 0.0
    },
    "SENSEX": {
        "ltp": 72362.73, "rsi": 55, "pcr": 0.98, "supertrend": "BULLISH", 
        "qty": 10, "target": 120, "sl": 60, "pnl": 0.0, "status": "NO POSITION", "entry_price": 0.0
    }
}

# --- 2. रीयल-टाइम कैलकुलेशन इंजन (A to Z लाइव सिग्नल्स) ---
def update_live_market_engine():
    for index, data in MARKET_DATA.items():
        # भाव में लाइव उतार-चढ़ाव (Live Feed Simulation)
        change = random.uniform(-12, 12) if index != "NIFTY50" else random.uniform(-4, 4)
        data["ltp"] = round(data["ltp"] + change, 2)
        data["rsi"] = random.randint(40, 75)
        
        # सुपरट्रेंड कंडीशन (RSI के आधार पर सिमुलेटेड)
        data["supertrend"] = "BULLISH" if data["rsi"] >= 50 else "BEARISH"
        
        # स्टॉप लॉस और टारगेट चेकिंग लॉजिक
        if data["status"] == "IN POSITION":
            points_gained = data["ltp"] - data["entry_price"]
            data["pnl"] = round(points_gained * data["qty"], 2)
            
            # क्या स्टॉप लॉस हिट हुआ?
            if points_gained <= -data["sl"]:
                data["status"] = "SL HIT 🔴"
                data["pnl"] = round(-data["sl"] * data["qty"], 2)
            # क्या टारगेट अचीव हुआ?
            elif points_gained >= data["target"]:
                data["status"] = "TARGET ACHIEVED 🟢"
                data["pnl"] = round(data["target"] * data["qty"], 2)
        else:
            # नई पोजीशन ट्रिगर करने का लॉजिक
            if random.random() < 0.15 and not ("HIT" in data["status"] or "ACHIEVED" in data["status"]):
                data["status"] = "IN POSITION"
                data["entry_price"] = data["ltp"]

@app.route('/api/live-data')
def live_data_endpoint():
    update_live_market_engine()
    return jsonify(MARKET_DATA)

@app.route('/')
def home():
    # यहाँ Jinja2 टेम्पलेट का इस्तेमाल किया गया है ताकि {% for %} सही से रेंडर हो
    html_layout = """
    <!DOCTYPE html>
    <html lang="hi">
    <head>
        <meta charset="UTF-8">
        <title>Upstox Super-Trend Live Engine</title>
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; background-color: #0b0f19; color: #e2e8f0; margin: 0; padding: 20px; }
            h2 { text-align: center; color: #38bdf8; font-size: 2rem; margin-bottom: 25px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; max-width: 1200px; margin: 0 auto; }
            .card { background: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
            .heading { font-size: 1.5rem; font-weight: bold; border-bottom: 2px solid #475569; padding-bottom: 8px; display: flex; justify-content: space-between; }
            .status-badge { font-size: 0.85rem; background: #475569; padding: 3px 8px; border-radius: 4px; }
            .data-row { display: flex; justify-content: space-between; margin: 12px 0; font-size: 1.05rem; }
            .bullish { color: #22c55e; font-weight: bold; }
            .bearish { color: #ef4444; font-weight: bold; }
            .pnl-style { font-size: 1.3rem; font-weight: bold; text-align: center; background: #111827; padding: 10px; border-radius: 6px; margin-top: 15px; }
            footer { text-align: center; margin-top: 4px; color: #64748b; font-size: 0.85rem; }
        </style>
    </head>
    <body>
        <h2>📊 Upstox Super-Trend Live Engine</h2>
        <div class="grid">
            {% for index in ['BANKNIFTY', 'NIFTY50', 'SENSEX'] %}
            <div class="card">
                <div class="heading">{{ index }} <span class="status-badge" id="status-{{ index }}">NO POSITION</span></div>
                <div class="data-row"><span>LTP (लाइव भाव):</span> <span id="ltp-{{ index }}">₹0.00</span></div>
                <div class="data-row"><span>Supertrend:</span> <span id="trend-{{ index }}">WAITING</span></div>
                <div class="data-row"><span>RSI (1 Min):</span> <span id="rsi-{{ index }}">0</span></div>
                <div class="data-row"><span>Rules (Qty|T|SL):</span> <span id="rules-{{ index }}">Loading...</span></div>
                <div class="pnl-style">PnL: <span id="pnl-{{ index }}">₹0.00</span></div>
            </div>
            {% endfor %}
        </div>
        <footer>Data refreshes automatically every 2 seconds</footer>

        <script>
            async function updateDashboard() {
                try {
                    const res = await fetch('/api/live-data');
                    const data = await res.json();
                    for(let key in data) {
                        document.getElementById(`ltp-${key}`).innerText = '₹' + data[key].ltp;
                        document.getElementById(`rsi-${key}`).innerText = data[key].rsi;
                        document.getElementById(`status-${key}`).innerText = data[key].status;
                        
                        let trendEl = document.getElementById(`trend-${key}`);
                        trendEl.innerText = data[key].supertrend;
                        trendEl.className = data[key].supertrend === 'BULLISH' ? 'bullish' : 'bearish';
                        
                        document.getElementById(`rules-${key}`).innerText = `${data[key].qty} | T: ${data[key].target} | SL: ${data[key].sl}`;
                        
                        let pnlEl = document.getElementById(`pnl-${key}`);
                        pnlEl.innerText = '₹' + data[key].pnl;
                        if(data[key].pnl > 0) pnlEl.style.color = '#22c55e';
                        else if(data[key].pnl < 0) pnlEl.style.color = '#ef4444';
                        else pnlEl.style.color = '#e2e8f0';
                    }
                } catch (e) { console.error("Error refreshing dashboard:", e); }
            }
            setInterval(updateDashboard, 2000);
            updateDashboard();
        </script>
    </body>
    </html>
    """
    return render_template_string(html_layout)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
            
