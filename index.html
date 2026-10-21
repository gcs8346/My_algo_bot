<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TOPU TOWER - FINAL SUPER COMBO - LIVE ORIGINAL</title>
<script src="https://unpkg.com/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Inter,Segoe UI,sans-serif}
body{background:#0d1421;color:#e2e8f0;padding:10px}
.header{display:flex;justify-content:space-between;align-items:center;padding:12px 0}
.header h1{color:#2ea8ff;font-size:22px;letter-spacing:0.5px}
.live-dot{width:8px;height:8px;background:#22c55e;border-radius:50%;display:inline-block;animation:blink 1s infinite}
@keyframes blink{50%{opacity:0.3}}
.top-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:10px 0}
.card{background:#151e2f;border:1px solid #1f2d4a;border-radius:10px;padding:12px;text-align:center}
.card label{font-size:11px;color:#8aa0c8;letter-spacing:0.8px}
.card input,.card select{width:100%;background:#0d1421;border:1px solid #2a3a5e;color:#fff;padding:6px;border-radius:6px;text-align:center;font-weight:700;margin-top:6px}
.mid-grid{display:grid;grid-template-columns:1.2fr 1fr 1fr 1fr 1.2fr;gap:10px;margin:10px 0}
.mid-card{background:#151e2f;border:1px solid #1f2d4a;border-radius:10px;padding:10px;text-align:center}
.m-label{font-size:11px;color:#8aa0c8}
.m-val{font-size:18px;font-weight:800;margin-top:4px}
.bull{color:#22c55e}.bear{color:#ef4444}.neutral{color:#f59e0b}
.alert-bar{background:#a16207;color:#fef08a;padding:10px 14px;border-radius:8px;margin:10px 0;display:flex;justify-content:space-between;align-items:center;font-weight:700;border:1px solid #ca8a04}
.settings{background:#151e2f;border:1px solid #1f2d4a;border-radius:10px;padding:10px;margin:10px 0;display:grid;grid-template-columns:repeat(6,1fr);gap:8px;align-items:end}
.settings input{width:100%;background:#0d1421;border:1px solid #2a3a5e;color:#fff;padding:5px;border-radius:6px}
.preset-btn{background:#1e3a8a;color:#93c5fd;border:1px solid #3b82f6;padding:6px 10px;border-radius:6px;cursor:pointer;font-weight:700;font-size:12px}
.preset-btn.active{background:#2563eb;color:#fff}
.chart-box{background:#151e2f;border:1px solid #1f2d4a;border-radius:10px;padding:10px;margin:10px 0}
.chart-box h3{font-size:13px;color:#2ea8ff;margin-bottom:8px}
#tvChart{width:100%;height:380px}
#trailingChart{width:100%;height:220px}
.footer{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:10px 0;padding:12px;background:#0f1a2b;border:1px solid #22c55e;border-radius:10px;text-align:center;font-weight:800}
@media(max-width:900px){.top-grid{grid-template-columns:repeat(2,1fr)}.mid-grid{grid-template-columns:1fr 1fr}.settings{grid-template-columns:repeat(2,1fr)}.footer{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="header">
<h1>TOPU TOWER - FINAL SUPER COMBO</h1>
<div><span class="live-dot"></span> <span id="connStatus" style="color:#22c55e;font-size:12px;font-weight:700">CONNECTING...</span> <span id="lastUpdate" style="font-size:11px;color:#8aa0c8;margin-left:10px"></span></div>
</div>

<div class="top-grid">
<div class="card"><label>INDEX</label><select id="indexSelect" onchange="onIndexChange()"><option value="SENSEX">SENSEX</option><option value="NIFTY">NIFTY</option><option value="BANKNIFTY">BANKNIFTY</option><option value="FINNIFTY">FINNIFTY</option><option value="STOCK">STOCK</option></select><input id="stockInput" type="text" placeholder="RELIANCE" style="display:none;margin-top:8px" oninput="onStockSymbolChange()"><label id="stockLabel" style="display:none;margin-top:4px">ENTER STOCK SYMBOL (NSE)</label></div>
<div class="card"><label>LOT QTY</label><input id="lotQty" type="number" value="1" min="1"></div>
<div class="card"><label>SL POINTS</label><input id="slPoints" type="number" value="100"></div>
<div class="card"><label>TRAILING GAP</label><input id="trailGap" type="number" value="50"></div>
</div>

<div class="settings">
<div><label class="m-label">EMA FAST</label><input id="emaFast" type="number" value="9"><input id="emaFastColor" type="color" value="#FFD700"></div>
<div><label class="m-label">EMA MEDIUM</label><input id="emaMid" type="number" value="21"><input id="emaMidColor" type="color" value="#00BFFF"></div>
<div><label class="m-label">EMA SLOW</label><input id="emaSlow" type="number" value="50"><input id="emaSlowColor" type="color" value="#FF00FF"></div>
<div><label class="m-label">RSI PERIOD</label><input id="rsiPeriod" type="number" value="14"></div>
<div><button class="preset-btn active" id="stockPresetBtn" onclick="applyPreset('STOCK')">STOCK PRESET 9-21-50</button><button class="preset-btn" id="optionPresetBtn" onclick="applyPreset('OPTION')" style="margin-top:6px">OPTION PRESET 10-50-100</button></div>
<div><label class="m-label">LIVE SYMBOL</label><div id="liveSymbolDisplay" style="font-size:12px;font-weight:800;color:#2ea8ff;margin-top:6px">^BSESN</div><div id="liveError" style="font-size:10px;color:#ef4444;margin-top:4px"></div></div>
</div>

<div class="mid-grid">
<div class="mid-card"><div class="m-label">SENSEX LTP</div><div class="m-val" id="ltpVal">0</div><div id="ltpChange" style="font-size:11px"></div></div>
<div class="mid-card"><div class="m-label">DAY OPEN</div><div class="m-val" id="dayOpen">0</div></div>
<div class="mid-card"><div class="m-label">EMA TREND</div><div class="m-val" id="emaTrend">WAITING</div></div>
<div class="mid-card"><div class="m-label">OPEN TREND</div><div class="m-val" id="openTrend">WAITING</div></div>
<div class="mid-card"><div class="m-label">CHANNEL</div><div class="m-val" id="channelVal">0 - 0</div></div>
</div>

<div class="alert-bar" id="alertBar" style="display:none"><span id="alertText">ALERT: WAITING FOR LIVE DATA</span><button onclick="this.parentElement.style.display='none'" style="background:transparent;border:1px solid #fef08a;color:#fef08a;padding:2px 8px;border-radius:4px;cursor:pointer">DISMISS</button></div>

<div class="chart-box"><h3 id="chartTitle">SENSEX • 1MIN • CANDLESTICK • EMA 9 21 50 • LIVE ORIGINAL</h3><div id="tvChart"></div></div>

<div class="chart-box"><h3>TRAILING SL MANAGER <span id="trailingInfo" style="float:right;color:#22c55e"></span></h3><canvas id="trailingChart"></canvas></div>

<div class="footer"><div style="color:#ef4444">SL: <span id="slVal">0</span></div><div style="color:#22c55e">TGT: <span id="tgtVal">0</span></div><div style="color:#2ea8ff">LIVE: <span id="liveFooter">WAITING</span> • <span id="marketStatus" style="font-size:11px">-</span></div></div>

<script>
let tvChartInstance=null, candleSeries=null, emaFastSeries=null, emaMidSeries=null, emaSlowSeries=null, volumeSeries=null;
let liveCandles=[], trailingData=[0,0,0,0,0,0], trailingLabels=["02 PM","02:15","02:30","02:45","03 PM","03:15"];
let currentLTP=0, dayOpenPrice=0, currentTrend="WAITING";
let trailingChartJS=null;
const SYMBOL_MAP={"SENSEX":"^BSESN","NIFTY":"^NSEI","BANKNIFTY":"^NSEBANK","FINNIFTY":"^CNXFIN","STOCK":""};

function loadSavedSettings(){
let s=JSON.parse(localStorage.getItem("topuTowerFinal")||"{}");
if(s.emaFast) document.getElementById("emaFast").value=s.emaFast;
if(s.emaMid) document.getElementById("emaMid").value=s.emaMid;
if(s.emaSlow) document.getElementById("emaSlow").value=s.emaSlow;
if(s.emaFastColor) document.getElementById("emaFastColor").value=s.emaFastColor;
if(s.emaMidColor) document.getElementById("emaMidColor").value=s.emaMidColor;
if(s.emaSlowColor) document.getElementById("emaSlowColor").value=s.emaSlowColor;
if(s.rsiPeriod) document.getElementById("rsiPeriod").value=s.rsiPeriod;
}
function saveSettings(){
let obj={emaFast:document.getElementById("emaFast").value,emaMid:document.getElementById("emaMid").value,emaSlow:document.getElementById("emaSlow").value,emaFastColor:document.getElementById("emaFastColor").value,emaMidColor:document.getElementById("emaMidColor").value,emaSlowColor:document.getElementById("emaSlowColor").value,rsiPeriod:document.getElementById("rsiPeriod").value};
localStorage.setItem("topuTowerFinal",JSON.stringify(obj));
}
document.getElementById("emaFast").addEventListener("input",saveSettings);
document.getElementById("emaMid").addEventListener("input",saveSettings);
document.getElementById("emaSlow").addEventListener("input",saveSettings);
document.getElementById("emaFastColor").addEventListener("input",saveSettings);
document.getElementById("emaMidColor").addEventListener("input",saveSettings);
document.getElementById("emaSlowColor").addEventListener("input",saveSettings);

function applyPreset(type){
if(type==="STOCK"){
document.getElementById("emaFast").value=9;
document.getElementById("emaMid").value=21;
document.getElementById("emaSlow").value=50;
document.getElementById("stockPresetBtn").classList.add("active");
document.getElementById("optionPresetBtn").classList.remove("active");
}else{
document.getElementById("emaFast").value=10;
document.getElementById("emaMid").value=50;
document.getElementById("emaSlow").value=100;
document.getElementById("optionPresetBtn").classList.add("active");
document.getElementById("stockPresetBtn").classList.remove("active");
}
saveSettings();
fetchLiveOriginal();
}

function onIndexChange(){
let idx=document.getElementById("indexSelect").value;
let stockInput=document.getElementById("stockInput");
let stockLabel=document.getElementById("stockLabel");
if(idx==="STOCK"){
stockInput.style.display="block";
stockLabel.style.display="block";
stockInput.focus();
document.getElementById("liveSymbolDisplay").innerText="Enter NSE Symbol";
}else{
stockInput.style.display="none";
stockLabel.style.display="none";
document.getElementById("liveSymbolDisplay").innerText=SYMBOL_MAP[idx];
fetchLiveOriginal();
}
}
function onStockSymbolChange(){
let sym=document.getElementById("stockInput").value.trim().toUpperCase();
if(sym.length>=2){
document.getElementById("liveSymbolDisplay").innerText=sym+".NS";
fetchLiveOriginal();
}
}
function getYahooSymbol(){
let idx=document.getElementById("indexSelect").value;
if(idx!=="STOCK") return SYMBOL_MAP[idx];
let inp=document.getElementById("stockInput").value.trim().toUpperCase();
if(!inp) return null;
if(inp.includes(".NS")||inp.includes("^")) return inp;
return inp+".NS";
}
function initChart(){
let container=document.getElementById("tvChart");
container.innerHTML="";
tvChartInstance=LightweightCharts.createChart(container,{layout:{background:{color:"#151e2f"},textColor:"#8aa0c8"},grid:{vertLines:{color:"#1f2d4a"},horzLines:{color:"#1f2d4a"}},width:container.clientWidth,height:380,timeScale:{timeVisible:true,secondsVisible:false}});
candleSeries=tvChartInstance.addCandlestickSeries({upColor:"#22c55e",downColor:"#ef4444",wickUpColor:"#22c55e",wickDownColor:"#ef4444"});
volumeSeries=tvChartInstance.addHistogramSeries({priceScaleId:"",priceFormat:{type:"volume"}});
emaFastSeries=tvChartInstance.addLineSeries({color:document.getElementById("emaFastColor").value,lineWidth:2});
emaMidSeries=tvChartInstance.addLineSeries({color:document.getElementById("emaMidColor").value,lineWidth:2});
emaSlowSeries=tvChartInstance.addLineSeries({color:document.getElementById("emaSlowColor").value,lineWidth:2});
}
function calcEMA(data,period){
let k=2/(period+1);
let emaArray=[];
let ema=0;
for(let i=0;i<data.length;i++){
let close=data[i].close;
if(i===0) ema=close;
else ema=close*k+ema*(1-k);
emaArray.push({time:data[i].time,value:ema});
}
return emaArray;
}
async function fetchLiveOriginal(){
let yahooSym=getYahooSymbol();
if(!yahooSym){
document.getElementById("liveError").innerText="Enter Stock Symbol";
return;
}
document.getElementById("connStatus").innerText="FETCHING LIVE...";
document.getElementById("liveError").innerText="";
try{
let url=`https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(yahooSym)}?interval=1m&range=1d`;
let res=await fetch(url);
if(!res.ok) throw new Error("Yahoo API failed "+res.status);
let json=await res.json();
let result=json.chart.result[0];
if(!result) throw new Error("No data from Yahoo");
let timestamps=result.timestamp;
let quote=result.indicators.quote[0];
let closes=quote.close;
let opens=quote.open;
let highs=quote.high;
let lows=quote.low;
let volumes=quote.volume;
liveCandles=[];
for(let i=0;i<timestamps.length;i++){
if(closes[i]==null) continue;
liveCandles.push({time:timestamps[i],open:opens[i],high:highs[i],low:lows[i],close:closes[i],volume:volumes[i]||0});
}
if(liveCandles.length===0) throw new Error("Empty candles");
let last=liveCandles[liveCandles.length-1];
currentLTP=last.close;
dayOpenPrice=liveCandles[0].open;
document.getElementById("ltpVal").innerText=currentLTP.toFixed(2);
document.getElementById("dayOpen").innerText=dayOpenPrice.toFixed(2);
document.getElementById("liveFooter").innerText=yahooSym;
document.getElementById("chartTitle").innerText=yahooSym+" • 1MIN • EMA "+document.getElementById("emaFast").value+" "+document.getElementById("emaMid").value+" "+document.getElementById("emaSlow").value+" • LIVE ORIGINAL";
let change=currentLTP-dayOpenPrice;
let changePct=(change/dayOpenPrice)*100;
document.getElementById("ltpChange").innerText=(change>=0?"+":"")+change.toFixed(2)+" ("+changePct.toFixed(2)+"%)";
document.getElementById("ltpChange").style.color=change>=0?"#22c55e":"#ef4444";
let fastPeriod=parseInt(document.getElementById("emaFast").value)||9;
let midPeriod=parseInt(document.getElementById("emaMid").value)||21;
let slowPeriod=parseInt(document.getElementById("emaSlow").value)||50;
let emaFast=calcEMA(liveCandles,fastPeriod);
let emaMid=calcEMA(liveCandles,midPeriod);
let emaSlow=calcEMA(liveCandles,slowPeriod);
candleSeries.setData(liveCandles.map(c=>({time:c.time,open:c.open,high:c.high,low:c.low,close:c.close})));
volumeSeries.setData(liveCandles.map(c=>({time:c.time,value:c.volume,color:c.close>=c.open?"rgba(34,197,94,0.5)":"rgba(239,68,68,0.5)"})));
emaFastSeries.applyOptions({color:document.getElementById("emaFastColor").value});
emaMidSeries.applyOptions({color:document.getElementById("emaMidColor").value});
emaSlowSeries.applyOptions({color:document.getElementById("emaSlowColor").value});
emaFastSeries.setData(emaFast);
emaMidSeries.setData(emaMid);
emaSlowSeries.setData(emaSlow);
let lastFast=emaFast[emaFast.length-1].value;
let lastMid=emaMid[emaMid.length-1].value;
let lastSlow=emaSlow[emaSlow.length-1].value;
let emaTrendEl=document.getElementById("emaTrend");
if(currentLTP>lastFast && lastFast>lastMid && lastMid>lastSlow){
emaTrendEl.innerText="BULLISH";
emaTrendEl.className="m-val bull";
currentTrend="BULLISH";
}else if(currentLTP<lastFast && lastFast<lastMid && lastMid<lastSlow){
emaTrendEl.innerText="BEARISH";
emaTrendEl.className="m-val bear";
currentTrend="BEARISH";
}else{
emaTrendEl.innerText="SIDEWAYS";
emaTrendEl.className="m-val neutral";
currentTrend="SIDEWAYS";
}
let openTrendEl=document.getElementById("openTrend");
if(currentLTP>dayOpenPrice){
openTrendEl.innerText="BULLISH";
openTrendEl.className="m-val bull";
}else if(currentLTP<dayOpenPrice){
openTrendEl.innerText="BEARISH";
openTrendEl.className="m-val bear";
}else{
openTrendEl.innerText="FLAT";
openTrendEl.className="m-val neutral";
}
let recentHigh=Math.max(...liveCandles.slice(-20).map(c=>c.high));
let recentLow=Math.min(...liveCandles.slice(-20).map(c=>c.low));
document.getElementById("channelVal").innerText=recentLow.toFixed(0)+" - "+recentHigh.toFixed(0);
let slPoints=parseInt(document.getElementById("slPoints").value)||100;
let sl=currentTrend==="BULLISH"?currentLTP-slPoints:currentLTP+slPoints;
let tgt=currentTrend==="BULLISH"?currentLTP+(slPoints*2.5):currentLTP-(slPoints*2.5);
document.getElementById("slVal").innerText=Math.round(sl);
document.getElementById("tgtVal").innerText=Math.round(tgt);
let alertBar=document.getElementById("alertBar");
let alertText=document.getElementById("alertText");
if(currentTrend==="BULLISH" && currentLTP>dayOpenPrice){
alertBar.style.display="flex";
alertText.innerText="ALERT: "+yahooSym+" FINAL BULLISH - CALL READY | LTP "+currentLTP.toFixed(0);
}else if(currentTrend==="BEARISH" && currentLTP<dayOpenPrice){
alertBar.style.display="flex";
alertText.innerText="ALERT: "+yahooSym+" FINAL BEARISH - PUT READY | LTP "+currentLTP.toFixed(0);
}else{
alertBar.style.display="none";
}
document.getElementById("connStatus").innerText="CONNECTED • LIVE ORIGINAL";
document.getElementById("connStatus").style.color="#22c55e";
let now=new Date();
document.getElementById("lastUpdate").innerText="Last Updated: "+now.toLocaleString("en-IN",{timeZone:"Asia/Kolkata"})+" LIVE";
document.getElementById("marketStatus").innerText="MARKET LIVE";
}catch(e){
console.error(e);
document.getElementById("connStatus").innerText="FAILED";
document.getElementById("connStatus").style.color="#ef4444";
document.getElementById("liveError").innerText="LIVE FETCH FAILED: "+e.message;
document.getElementById("marketStatus").innerText="FETCH FAILED";
document.getElementById("alertBar").style.display="none";
}
}
function initTrailing(){
let ctx=document.getElementById("trailingChart").getContext("2d");
trailingChartJS=new Chart(ctx,{type:"line",data:{labels:trailingLabels,datasets:[{label:"Profit",data:trailingData,borderColor:"#22c55e",backgroundColor:"rgba(34,197,94,0.2)",tension:0.4}]},options:{responsive:true,plugins:{legend:{display:false}}}});
}
window.addEventListener("load",()=>{
loadSavedSettings();
initChart();
initTrailing();
fetchLiveOriginal();
setInterval(fetchLiveOriginal,60000);
});
window.addEventListener("resize",()=>{if(tvChartInstance) tvChartInstance.applyOptions({width:document.getElementById("tvChart").clientWidth});});
</script>
</body>
</html>