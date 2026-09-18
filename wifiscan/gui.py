"""wifiscan GUI – Hackerman / Kung Fury VHS-synthwave stílus (króm cím, neon magenta-cián, laser grid).

Csak 127.0.0.1-en hallgat, minden API hívás a lapba ágyazott véletlen tokent viszi.
Indítás:  python3 gui.py [--port 8766] [--no-browser]
"""
import argparse, json, secrets, sys, threading, time, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import engine as wifiscan, __version__ as VERSION
from .store import Store
TOKEN = secrets.token_urlsafe(24)

HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WIFISCAN</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>
:root{--bg:#0b0418;--bg2:#160a2e;--panel:rgba(20,8,48,.78);--pink:#ff2bd6;--hot:#ff3f8e;--cyan:#19f0ff;--violet:#8a5cff;
 --sun:#ffb347;--chrome1:#f6f9ff;--chrome2:#8fb4d9;--chrome3:#2c4a78;--text:#e9e2ff;--dim:#9a8fc4;--red:#ff4d4d;--lime:#7dff6a;
 --mono:"Share Tech Mono","Menlo","Consolas",monospace;--head:"Orbitron","Impact",sans-serif}
*{box-sizing:border-box}
[hidden]{display:none!important}
html,body{margin:0;min-height:100%}
body{background:var(--bg);color:var(--text);font-family:var(--mono);font-size:14px;line-height:1.45;letter-spacing:.03em;overflow-x:hidden;
 background-image:radial-gradient(ellipse at 50% -20%,#3a1a6e 0%,transparent 60%),linear-gradient(180deg,var(--bg) 0%,var(--bg2) 100%)}
/* VHS: scanlines + színcsúszás + tracking csík */
body::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:9;
 background:repeating-linear-gradient(0deg,rgba(0,0,0,.28) 0 1px,transparent 1px 3px)}
body::after{content:"";position:fixed;left:0;right:0;height:90px;z-index:10;pointer-events:none;opacity:.35;
 background:linear-gradient(180deg,transparent,rgba(255,255,255,.12) 45%,rgba(25,240,255,.18) 50%,rgba(255,43,214,.18) 55%,transparent);
 animation:track 9s linear infinite}
@keyframes track{0%{top:-120px}100%{top:110%}}
/* laser grid horizont */
.grid{position:fixed;left:-20%;right:-20%;bottom:0;height:42vh;z-index:0;pointer-events:none;transform:perspective(420px) rotateX(62deg);transform-origin:top;
 background:linear-gradient(90deg,rgba(255,43,214,.55) 1px,transparent 1px) 0 0/60px 60px,linear-gradient(0deg,rgba(255,43,214,.55) 1px,transparent 1px) 0 0/60px 60px;
 mask-image:linear-gradient(180deg,transparent,#000 40%);-webkit-mask-image:linear-gradient(180deg,transparent,#000 40%);animation:grid 1.2s linear infinite}
@keyframes grid{to{background-position:0 60px,0 60px}}
.sunset{position:fixed;left:50%;bottom:26vh;width:340px;height:340px;margin-left:-170px;border-radius:50%;z-index:0;pointer-events:none;opacity:.55;
 background:linear-gradient(180deg,#ffd166 0%,#ff7a59 45%,#ff2bd6 100%);
 mask-image:repeating-linear-gradient(180deg,#000 0 14px,transparent 14px 22px),linear-gradient(#000,#000);mask-composite:intersect;
 -webkit-mask-image:repeating-linear-gradient(180deg,#000 0 14px,transparent 14px 22px);filter:blur(.5px)}
.crt{position:relative;z-index:1;min-height:100%;padding:18px 16px 60px;max-width:1180px;margin:0 auto;animation:flick 7s infinite}
@keyframes flick{0%,96%,100%{opacity:1}97%{opacity:.9;transform:translateX(1px)}98%{opacity:.96}}
/* VHS OSD sáv */
.bar{display:flex;justify-content:space-between;align-items:center;padding:6px 12px;border:1px solid rgba(25,240,255,.35);
 background:rgba(0,0,0,.35);font-size:12px;color:var(--cyan);text-shadow:0 0 6px var(--cyan)}
.bar .left{display:flex;align-items:center;gap:18px}
.sys{letter-spacing:.12em}
.cls{color:var(--red);text-shadow:0 0 8px var(--red);letter-spacing:.14em}
.cls::before{content:"● ";animation:blink 1.2s steps(1) infinite}
/* Króm cím */
h1{margin:26px 0 2px;font-family:var(--head);font-weight:900;font-size:clamp(34px,7vw,64px);line-height:1;letter-spacing:.02em;font-style:italic;text-transform:uppercase;
 background:linear-gradient(180deg,var(--chrome1) 0%,var(--chrome1) 38%,var(--chrome3) 50%,var(--chrome2) 62%,var(--chrome1) 100%);
 -webkit-background-clip:text;background-clip:text;color:transparent;
 filter:drop-shadow(0 0 2px var(--pink)) drop-shadow(0 0 14px rgba(255,43,214,.55)) drop-shadow(4px 4px 0 #3a0a5e)}
h1 small{display:block;font-family:var(--mono);font-style:normal;font-weight:normal;font-size:13px;letter-spacing:.35em;margin-top:8px;
 background:none;color:var(--cyan);-webkit-text-fill-color:var(--cyan);filter:none;text-shadow:0 0 8px var(--cyan)}
.sub{color:var(--dim);font-size:12px;margin:10px 0 20px;text-transform:uppercase;letter-spacing:.1em}
/* Panelek */
.panel{position:relative;border:1px solid var(--pink);padding:16px 14px 14px;margin-bottom:18px;background:var(--panel);
 box-shadow:0 0 18px rgba(255,43,214,.25),inset 0 0 30px rgba(138,92,255,.08);backdrop-filter:blur(2px)}
.panel::before{content:"";position:absolute;inset:-1px;border:1px solid var(--cyan);pointer-events:none;transform:translate(3px,3px);opacity:.7}
.panel h2{margin:-26px 0 12px;display:inline-block;padding:2px 10px;font-family:var(--head);font-weight:700;font-size:12px;letter-spacing:.25em;text-transform:uppercase;
 color:#fff;background:linear-gradient(90deg,var(--pink),var(--violet));box-shadow:0 0 10px var(--pink)}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
select,input[type=text],input[type=password]{background:#08031a;color:var(--cyan);border:1px solid var(--cyan);padding:9px 12px;font:inherit;outline:none;
 box-shadow:inset 0 0 12px rgba(25,240,255,.12)}
select{flex:0 0 280px;text-transform:uppercase}
input::placeholder{color:var(--dim)}
input:focus,select:focus{box-shadow:0 0 0 1px var(--pink),0 0 14px var(--pink)}
button{background:linear-gradient(180deg,var(--hot),var(--pink));color:#fff;border:0;padding:9px 22px;font:inherit;font-family:var(--head);font-weight:700;font-size:12px;
 letter-spacing:.2em;text-transform:uppercase;cursor:pointer;box-shadow:0 0 12px rgba(255,43,214,.6),inset 0 1px 0 rgba(255,255,255,.35)}
button:hover{filter:brightness(1.15);box-shadow:0 0 22px var(--pink)}
button:disabled{filter:grayscale(1) brightness(.6);cursor:wait;box-shadow:none}
.ghost,a.btn{background:transparent;color:var(--cyan);border:1px solid var(--cyan);padding:6px 14px;font:inherit;font-family:var(--head);font-size:11px;letter-spacing:.18em;
 text-transform:uppercase;text-decoration:none;cursor:pointer;box-shadow:0 0 8px rgba(25,240,255,.3)}
.ghost:hover,a.btn:hover{background:rgba(25,240,255,.12);box-shadow:0 0 16px var(--cyan)}
.ghost.sm{padding:2px 8px;font-size:10px}
input[type=checkbox]{accent-color:var(--pink);width:15px;height:15px;cursor:pointer}
.selbar{margin-top:10px}
tr.click{cursor:pointer}tr.click:hover td{background:rgba(255,43,214,.08)}
.hint{color:var(--dim);font-size:11px;margin-top:8px}
#log{white-space:pre-wrap;min-height:60px;color:var(--lime);text-shadow:0 0 6px rgba(125,255,106,.7);font-size:15px}
.cursor::after{content:"█";animation:blink 1s steps(1) infinite;margin-left:2px}
@keyframes blink{50%{opacity:0}}
table{width:100%;border-collapse:collapse;margin-top:8px;font-size:12px}
td,th{padding:5px 8px;text-align:left;vertical-align:top;border-bottom:1px solid rgba(138,92,255,.3)}
th{color:var(--pink);font-family:var(--head);font-weight:500;font-size:10px;letter-spacing:.2em;text-transform:uppercase;border-bottom:1px solid var(--pink)}
td.loc,td.note{color:var(--dim)}
td.mac{color:var(--cyan);white-space:nowrap}
td.lbl input{width:100%;padding:3px 6px;font-size:12px}
.v{display:inline-block;padding:1px 8px;border:1px solid;white-space:nowrap;font-size:11px;letter-spacing:.1em}
.v-NEW{color:#fff;background:var(--red);border-color:var(--red);box-shadow:0 0 10px var(--red);animation:alert 1.2s steps(1) infinite}
@keyframes alert{50%{background:transparent;color:var(--red)}}
.v-UNKNOWN{color:var(--sun);border-color:var(--sun);text-shadow:0 0 6px var(--sun)}
.v-TRUSTED{color:var(--lime);border-color:var(--lime);text-shadow:0 0 6px var(--lime)}
.v-SEEN{color:var(--cyan);border-color:var(--cyan)}
.v-ME{color:var(--dim);border-color:var(--dim)}
.summary{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-top:10px}
.tile{border:1px solid var(--violet);padding:10px;text-align:center;background:rgba(0,0,0,.3)}
.tile b{display:block;font-family:var(--head);font-size:30px;font-weight:900;color:#fff;text-shadow:0 0 10px var(--cyan),0 0 2px #fff}
.tile span{font-size:10px;color:var(--dim);letter-spacing:.2em;text-transform:uppercase}
.ports{color:var(--dim);font-size:11px}
.ports b{color:var(--cyan);font-weight:normal}
pre.svc{margin:4px 0 0;font:inherit;font-size:11px;color:var(--lime);white-space:pre-wrap}
.foot{margin-top:30px;height:4px;background:linear-gradient(90deg,var(--cyan),var(--pink),var(--sun))}
.footnote{color:var(--dim);font-size:11px;margin-top:8px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;letter-spacing:.1em;text-transform:uppercase}
a{color:var(--cyan)}
@media (max-width:600px){.bar{flex-direction:column;align-items:flex-start;gap:6px}select{flex:1 1 100%}.sunset{display:none}}
</style></head>
<body><div class="sunset"></div><div class="grid"></div><div class="crt">
<div class="bar">
  <div class="left"><span class="sys">▶ PLAY</span><span class="sys" id="vhsclock">SP 0:00:00</span><span class="sys">WIFISCAN v__VERSION__</span></div>
  <div class="left"><button class="ghost sm" id="lang" type="button" title="Language / Nyelv">HU</button><span class="cls">REC · MIAMI 1985</span></div>
</div>
<h1>Hackerman<small data-i18n="tagline">Network Inventory System · Power Glove Edition</small></h1>
<div class="sub" data-i18n="sub"></div>

<div class="panel">
  <h2 data-i18n="request">Request</h2>
  <div class="row">
    <select id="mode">
      <option value="discover" data-i18n="m_discover"></option>
      <option value="ports" data-i18n="m_ports"></option>
      <option value="nmap" data-i18n="m_nmap"></option>
    </select>
    <span class="sys" id="net"><span data-i18n="network"></span>: __NET__ · nmap: __NMAP__</span>
    <button id="run" type="button">Hack time</button>
  </div>
  <div class="hint" data-i18n="hint_req"></div>
</div>

<div class="panel">
  <h2 data-i18n="response">Response</h2>
  <div id="log" class="cursor">HACKERMAN: WAITING FOR INPUT</div>
  <div id="summary"></div>
  <div class="row selbar" id="selbar" hidden><button id="nmap-sel" type="button" data-i18n="nmap_sel"></button><button id="sel-all" class="ghost" type="button" data-i18n="all"></button><button id="sel-none" class="ghost" type="button" data-i18n="none"></button><button id="nmap-stop" class="ghost" type="button" hidden style="border-color:var(--red);color:var(--red)">Stop</button><input type="password" id="sudo" data-i18n-ph="sudo_ph" autocomplete="off" style="flex:1;min-width:260px"><span class="hint" id="sel-count" style="margin:0"></span></div>
  <div class="hint" id="sudo-hint" hidden data-i18n="sudo_hint"></div>
  <div id="out"></div>
</div>
<div class="panel">
  <h2 data-i18n="archive">Archive</h2><div class="hint" style="margin:-6px 0 10px"><span data-i18n="saved_to"></span>: <span id="dbpath">__DBPATH__</span></div>
  <div class="row" style="margin-bottom:8px">
    <button id="hist-runs" class="ghost" data-i18n="runs"></button>
    <button id="hist-dev" class="ghost" data-i18n="devices"></button>
    <a id="exp-csv" class="ghost btn" href="#" download="wifiscan-devices.csv">Export CSV</a>
    <a id="exp-json" class="ghost btn" href="#" download="wifiscan-devices.json">Export JSON</a>
  </div>
  <div id="hist"></div>
</div>
<div class="foot"></div>
<div class="footnote"><span>sadrobot · Krisz · Home Lab · "I'm gonna hack time"</span><span>wifiscan __VERSION__ · python stdlib + nmap · E=mc³</span></div>
</div>
<script>
const TOKEN="__TOKEN__";
const T={
en:{tagline:"Network Inventory System · Power Glove Edition",sub:"Who is on the WiFi · vendor from MAC · device type · running services (nmap) · new device alert",
 request:"Request",response:"Response",archive:"Archive",network:"network",m_discover:"DISCOVER · who is online (ARP)",m_ports:"PORTS · + quick port scan",m_nmap:"NMAP · + service detection (slow)",
 hint_req:"Server listens on 127.0.0.1 only. Run it on your own network only. Full NMAP mode runs -sV on everything; for targeted -O OS detection select IPs and enter the sudo password.",
 nmap_sel:"Nmap on selected",all:"All",none:"None",sudo_ph:"sudo password (optional, for -O OS detection)",
 sudo_hint:"The password goes only to the local server on 127.0.0.1, is passed to sudo via stdin, never stored or logged.",
 saved_to:"every run is saved to",runs:"Runs",devices:"Known devices",online:"devices online",
 th:["Status","IP","MAC","Vendor","Type","Name","Label","Action"],label_ph:"e.g. living room TV",trust:"Trust",untrust:"Untrust",ports:"ports",
 sel_n:n=>n+" selected",sel_hint:"select targets for nmap -sV",
 h_runs:["ID","Time","Mode","Network","Devices","New"],h_dev:["Status","MAC","Label","Vendor","Last IP","First seen","Last seen","Seen"],
 waiting:"WAITING FOR INPUT",scanning:"SCANNING",online_msg:(n,nw,id)=>`${n} DEVICES ONLINE · ${nw} NEW · RUN ${id} ARCHIVED`,recalled:(id,n)=>`RUN ${id} RECALLED FROM ARCHIVE · ${n} DEVICES`,
 label_stored:"LABEL STORED FOR",specify:"SPECIFY TARGET",nmap_on:(f,n)=>`NMAP ${f} ON ${n} TARGET(S) ...`,nmap_done:n=>`NMAP COMPLETE · ${n} TARGET(S)`,abort:"ABORT REQUESTED · WAITING FOR NMAP TO EXIT",fail:"UNABLE TO COMPLY",
 types:{}},
hu:{tagline:"Hálózati eszközleltár · Power Glove kiadás",sub:"Ki van a WiFi-n · gyártó a MAC-ből · eszköztípus · futó szolgáltatások (nmap) · új eszköz riasztás",
 request:"Kérés",response:"Válasz",archive:"Archívum",network:"hálózat",m_discover:"DISCOVER · ki van fent (ARP)",m_ports:"PORTS · + gyors portscan",m_nmap:"NMAP · + szolgáltatás-felismerés (lassú)",
 hint_req:"A szerver csak 127.0.0.1-en hallgat. Csak a saját hálózatodon futtasd. A teljes NMAP mód -sV-t futtat mindenre; célzott -O OS-felismeréshez jelöld ki az IP-ket és add meg a sudo jelszót.",
 nmap_sel:"Nmap a kijelöltekre",all:"Mind",none:"Egyik sem",sudo_ph:"sudo jelszó (opcionális, -O OS-felismeréshez)",
 sudo_hint:"A jelszó csak a helyi szervernek megy 127.0.0.1-en, stdin-en adja át a sudo-nak, nem tárolódik és nem naplózódik.",
 saved_to:"minden futás mentve",runs:"Futások",devices:"Ismert eszközök",online:"eszköz online",
 th:["Státusz","IP","MAC","Gyártó","Típus","Név","Címke","Ok"],label_ph:"pl. nappali TV",trust:"Trust",untrust:"Untrust",ports:"portok",
 sel_n:n=>n+" kijelölve",sel_hint:"jelöld ki, mire fusson nmap -sV",
 h_runs:["ID","Idő","Mód","Hálózat","Eszköz","Új"],h_dev:["Státusz","MAC","Címke","Gyártó","Utolsó IP","Először","Utoljára","Látva"],
 waiting:"VÁROM A PARANCSOT",scanning:"SCAN INDUL",online_msg:(n,nw,id)=>`${n} ESZKÖZ ONLINE · ${nw} ÚJ · FUTÁS ${id} ARCHIVÁLVA`,recalled:(id,n)=>`FUTÁS ${id} ELŐHÍVVA AZ ARCHÍVUMBÓL · ${n} ESZKÖZ`,
 label_stored:"CÍMKE MENTVE",specify:"ADJ MEG CÉLT",nmap_on:(f,n)=>`NMAP ${f} FUT ${n} CÉLON ...`,nmap_done:n=>`NMAP KÉSZ · ${n} CÉL`,abort:"MEGSZAKÍTÁS KÉRVE · VÁROM AZ NMAP KILÉPÉSÉT",fail:"NEM TELJESÍTHETŐ",
 types:{"this machine":"ez a gép","unknown":"ismeretlen","?":"?","(randomized MAC – phone/laptop private address)":"(randomizált MAC – telefon/laptop privát cím)","ABORTED":"MEGSZAKÍTVA","nmap not installed":"nmap nincs telepítve",
  "UniFi router / AP / switch":"UniFi router / AP / switch","Router / AP":"Router / AP","Router":"Router","Amazon Echo / Fire TV":"Amazon Echo / Fire TV","Ring camera / doorbell":"Ring kamera / csengő","Roomba robot vacuum":"Roomba robotporszívó",
  "Nintendo Switch":"Nintendo Switch","PlayStation":"PlayStation","Xbox / PC":"Xbox / PC","Gree air conditioner (WiFi module)":"Gree klíma (WiFi modul)","Tesla car":"Tesla autó","Shelly smart relay":"Shelly okosrelé",
  "IoT (ESP32/ESP8266)":"IoT (ESP32/ESP8266)","IoT smart home":"IoT okosotthon","LG TV / appliance":"LG TV / készülék","Android TV box":"Android TV box","Denon / Marantz receiver":"Denon / Marantz erősítő","Sonos speaker":"Sonos hangszóró",
  "Philips Hue / TV":"Philips Hue / TV","Google Nest / Chromecast":"Google Nest / Chromecast","Raspberry Pi":"Raspberry Pi","Synology NAS":"Synology NAS","QNAP NAS":"QNAP NAS","HP printer / PC":"HP nyomtató / PC","Canon printer":"Canon nyomtató",
  "Brother printer":"Brother nyomtató","Epson printer":"Epson nyomtató","PC / laptop":"PC / laptop","Samsung phone / tablet / TV":"Samsung telefon / tablet / TV","Xiaomi phone / IoT":"Xiaomi telefon / IoT","Huawei phone":"Huawei telefon",
  "OnePlus phone":"OnePlus telefon","Apple device":"Apple eszköz","iPhone":"iPhone","iPad":"iPad","MacBook":"MacBook","iMac":"iMac","Apple TV":"Apple TV","Google Pixel phone":"Google Pixel telefon","Samsung tablet":"Samsung tablet",
  "Samsung phone":"Samsung telefon","TV":"TV","LG webOS TV":"LG webOS TV","Laptop":"Laptop","PC":"PC","Home theater receiver":"Házimozi erősítő","UniFi gateway":"UniFi gateway","UniFi AP":"UniFi AP","UniFi switch":"UniFi switch",
  "Printer":"Nyomtató","NAS":"NAS","Amazon Echo":"Amazon Echo","Chromecast":"Chromecast","iPhone/iPad":"iPhone/iPad","Chromecast / Android TV":"Chromecast / Android TV","IP camera":"IP kamera","Apple TV / AirPlay":"Apple TV / AirPlay",
  "IoT / smart home":"IoT / okosotthon","NAS / PC":"NAS / PC","Linux device / router":"Linux eszköz / router","Phone / laptop (private MAC)":"Telefon / laptop (privát MAC)",
  "Printer (LPD)":"Nyomtató (LPD)","RTSP (camera)":"RTSP (kamera)","IPP printer":"IPP nyomtató","Printer (JetDirect)":"Nyomtató (JetDirect)"}}};
let LANG=(()=>{try{return localStorage.getItem('wifiscan.lang')}catch(e){return null}})()||((navigator.language||'').startsWith('hu')?'hu':'en');
const t=k=>T[LANG][k], tt=s=>T[LANG].types[s]||s;
function applyLang(){document.documentElement.lang=LANG;document.getElementById('lang').textContent=LANG==='hu'?'EN':'HU';
  document.querySelectorAll('[data-i18n]').forEach(el=>{const v=t(el.dataset.i18n);if(typeof v==='string')el.textContent=v});
  document.querySelectorAll('[data-i18n-ph]').forEach(el=>el.placeholder=t(el.dataset.i18nPh));
  if(!current)log.textContent='HACKERMAN: '+t('waiting');else render(current);showRuns();try{localStorage.setItem('wifiscan.lang',LANG)}catch(e){}}
document.getElementById('lang').onclick=()=>{LANG=LANG==='hu'?'en':'hu';applyLang()};
const log=document.getElementById('log'),out=document.getElementById('out'),sum=document.getElementById('summary'),run=document.getElementById('run'),mode=document.getElementById('mode');
let typer=null;function type(text){if(typer)clearInterval(typer);log.textContent="";let i=0;typer=setInterval(()=>{log.textContent+=text[i++]||"";if(i>=text.length){clearInterval(typer);typer=null}},8)}
const say=m=>type('HACKERMAN: '+m);
function esc(s){return String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
async function api(path,body){const r=await fetch(path,{method:'POST',headers:{'X-Token':TOKEN,'Content-Type':'application/json'},body:JSON.stringify(body||{})});if(!r.ok)throw new Error(r.status+' '+await r.text());return r.json()}
function status(h){if(h.me)return 'ME';if(h.new)return 'NEW';if(h.trusted)return 'TRUSTED';if(h.type==='?'&&!h.label)return 'UNKNOWN';return 'SEEN'}
const V=v=>`<span class="v v-${v}">${v}</span>`;
let poll=null,current=null;const sel=new Set();
function render(data){
  const hosts=data.hosts;out.innerHTML="";
  const c={NEW:0,UNKNOWN:0,TRUSTED:0,SEEN:0};hosts.forEach(h=>{const s=status(h);if(s in c)c[s]++});
  sum.innerHTML='<div class="summary">'+`<div class="tile"><b>${hosts.length}</b><span>${t('online')}</span></div>`+
    Object.entries(c).filter(([k,v])=>v).map(([k,v])=>`<div class="tile"><b class="v-${k}" style="border:0;animation:none">${v}</b><span>${k}</span></div>`).join('')+'</div>';
  const tb=document.createElement('table');
  tb.innerHTML='<tr><th></th>'+t('th').map(x=>'<th>'+x+'</th>').join('')+'</tr>'+
    hosts.map(h=>`<tr><td>${h.me?'':`<input type="checkbox" data-ip="${esc(h.ip)}" ${sel.has(h.ip)?'checked':''}>`}</td><td>${V(status(h))}</td><td class="mac">${esc(h.ip)}</td><td class="mac">${esc(h.mac)}</td><td class="loc">${esc(tt(h.vendor))}</td><td>${esc(tt(h.type))}</td><td class="loc">${esc(h.name)}</td>
    <td class="lbl"><input type="text" value="${esc(h.label)}" data-mac="${esc(h.mac)}" placeholder="${t('label_ph')}"></td>
    <td><button class="ghost sm" data-trust="${esc(h.mac)}" data-val="${h.trusted?0:1}">${h.trusted?t('untrust'):t('trust')}</button></td></tr>`+
    ((h.ports&&h.ports.length)||h.services?`<tr><td></td><td></td><td colspan="7" class="ports">${h.ports&&h.ports.length?t('ports')+': '+h.ports.map(p=>`<b>${p}</b> ${esc(tt(data.hints[p]||''))}`).join(' · '):''}${h.services?`<pre class="svc">${esc(tt(h.services))}</pre>`:''}</td></tr>`:'')).join('');
  out.appendChild(tb);current=data;document.getElementById('selbar').hidden=false;document.getElementById('sudo-hint').hidden=false;
  tb.querySelectorAll('input[type=checkbox]').forEach(c=>c.onchange=()=>{c.checked?sel.add(c.dataset.ip):sel.delete(c.dataset.ip);selCount()});selCount();
  tb.querySelectorAll('td.lbl input').forEach(i=>i.onchange=()=>api('/api/device',{mac:i.dataset.mac,label:i.value}).then(()=>say(t('label_stored')+' '+i.dataset.mac)).catch(e=>say(e)));
  tb.querySelectorAll('button[data-trust]').forEach(b=>b.onclick=()=>api('/api/device',{mac:b.dataset.trust,trusted:+b.dataset.val}).then(()=>{const h=hosts.find(x=>x.mac===b.dataset.trust);h.trusted=!!+b.dataset.val;render(data)}).catch(e=>say(e)));
}
function selCount(){document.getElementById('sel-count').textContent=sel.size?t('sel_n')(sel.size):t('sel_hint')}
document.getElementById('sel-all').onclick=()=>{current.hosts.forEach(h=>{if(!h.me)sel.add(h.ip)});render(current)};
document.getElementById('sel-none').onclick=()=>{sel.clear();render(current)};
function watch(onDone,onEnd){poll=setInterval(async()=>{try{const s=await api('/api/status');if(s.log&&!typer)log.textContent='HACKERMAN: '+s.log;
  if(s.done){clearInterval(poll);onEnd();if(s.error){say(t('fail')+' · '+s.error);return}onDone(s.result)}}catch(e){clearInterval(poll);onEnd();say(e)}},700)}
document.getElementById('nmap-sel').onclick=async()=>{if(!sel.size){say(t('specify'));return}const b=document.getElementById('nmap-sel'),stop=document.getElementById('nmap-stop');
  const end=()=>{b.disabled=false;run.disabled=false;stop.hidden=true};b.disabled=true;run.disabled=true;stop.hidden=false;
  try{const pw=document.getElementById('sudo').value;await api('/api/nmap',{ips:[...sel],run_id:current.run_id,sudo:pw});say(t('nmap_on')(pw?'-O -sV':'-sV',sel.size));
    watch(r=>{for(const h of current.hosts)if(r.services[h.ip]!==undefined)h.services=r.services[h.ip];render(current);say(t('nmap_done')(Object.keys(r.services).length))},end)}
  catch(e){end();say(e)}};
document.getElementById('nmap-stop').onclick=()=>api('/api/stop').then(()=>say(t('abort'))).catch(e=>say(e));
run.onclick=async()=>{if(run.disabled)return;run.disabled=true;sel.clear();out.innerHTML="";sum.innerHTML="";
  try{await api('/api/scan',{mode:mode.value});say(t('scanning')+' '+mode.value.toUpperCase()+' ...');
    watch(r=>{render(r);say(t('online_msg')(r.hosts.length,r.hosts.filter(h=>h.new).length,r.run_id)+(r.warning?' · '+r.warning:''));showRuns()},()=>{run.disabled=false})}
  catch(e){run.disabled=false;say(e)}};
function histTable(rows,cols,onclick){const h=document.getElementById('hist');
  h.innerHTML='<table><tr>'+cols.map(c=>'<th>'+esc(c[0])+'</th>').join('')+'</tr>'+rows.map(r=>'<tr class="'+(onclick?'click':'')+'" data-id="'+esc(r.id)+'">'+cols.map(c=>'<td class="'+(c[2]||'')+'">'+(c[1](r))+'</td>').join('')+'</tr>').join('')+'</table>';
  if(onclick)h.querySelectorAll('tr.click').forEach(tr=>tr.onclick=()=>onclick(+tr.dataset.id))}
async function showRuns(){try{const H=t('h_runs');histTable(await api('/api/history',{limit:40}),[[H[0],r=>r.id],[H[1],r=>esc(r.ts.replace('T',' ')),'loc'],[H[2],r=>esc(r.mode)],[H[3],r=>esc(r.network),'loc'],[H[4],r=>r.n_hosts],[H[5],r=>r.n_new?V('NEW')+' '+r.n_new:'—']],loadRun)}catch(e){say(e)}}
async function showDev(){try{const H=t('h_dev');histTable(await api('/api/devices'),[[H[0],r=>V(r.trusted?'TRUSTED':'SEEN')],[H[1],r=>esc(r.mac),'mac'],[H[2],r=>esc(r.label),'loc'],[H[3],r=>esc(tt(r.vendor)),'loc'],[H[4],r=>esc(r.last_ip),'mac'],[H[5],r=>esc(r.first_seen.replace('T',' ')),'loc'],[H[6],r=>esc(r.last_seen.replace('T',' ')),'loc'],[H[7],r=>r.seen_count]],null)}catch(e){say(e)}}
async function loadRun(id){try{const d=await api('/api/run_get',{id});render(d);say(t('recalled')(id,d.hosts.length));window.scrollTo({top:log.offsetTop-80,behavior:'smooth'})}catch(e){say(e)}}
document.getElementById('hist-runs').onclick=showRuns;document.getElementById('hist-dev').onclick=showDev;
async function exportAs(fmt,a){const r=await fetch('/api/export?format='+fmt,{method:'POST',headers:{'X-Token':TOKEN},body:'{}'});a.href=URL.createObjectURL(await r.blob())}
for(const [id,fmt] of [['exp-csv','csv'],['exp-json','json']])document.getElementById(id).addEventListener('click',async function(e){if(this.dataset.ready){this.dataset.ready='';return}e.preventDefault();await exportAs(fmt,this);this.dataset.ready='1';this.click()});
applyLang();
const t0=Date.now(),clk=document.getElementById('vhsclock');setInterval(()=>{const d=Math.floor((Date.now()-t0)/1000),h=Math.floor(d/3600),m=String(Math.floor(d%3600/60)).padStart(2,'0'),s=String(d%60).padStart(2,'0');clk.textContent=`SP ${h}:${m}:${s}`},1000);
</script></body></html>
"""


class Job:
    def __init__(self):
        self.lock = threading.Lock()
        self.reset()

    def reset(self):
        self.running = False; self.done = False; self.error = ""; self.log = ""; self.result = None
        self.cancel = False; self.proc = None

    def start(self, mode, store):
        with self.lock:
            if self.running:
                raise ValueError("scan already running")
            self.reset(); self.running = True
        threading.Thread(target=self._work, args=(mode, store), daemon=True).start()

    def start_nmap(self, ips, run_id, store, sudo_pw=None):
        with self.lock:
            if self.running:
                raise ValueError("scan already running")
            self.reset(); self.running = True
        threading.Thread(target=self._nmap, args=(ips, run_id, store, sudo_pw), daemon=True).start()

    def _nmap(self, ips, run_id, store, sudo_pw):
        try:
            services = {}
            for i, ip in enumerate(ips, 1):
                if self.cancel:
                    break
                self.log = "NMAP %s %d/%d · %s" % ("-O -sV" if sudo_pw else "-sV", i, len(ips), ip)
                services[ip] = wifiscan.nmap_services(ip, sudo_pw, on_proc=self._set_proc)
                if self.cancel:
                    services[ip] = "ABORTED"
                if services[ip].startswith("SUDO REJECTED"):
                    raise ValueError("sudo rejected the password")
            if run_id:
                store.update_services(run_id, services)
            self.result = {"services": services}
        except Exception as e:
            self.error = str(e)
        finally:
            sudo_pw = None
            self.done = True; self.running = False

    def _set_proc(self, proc):
        self.proc = proc
        if self.cancel:
            proc.terminate()

    def stop(self):
        self.cancel = True
        p = self.proc
        if p and p.poll() is None:
            p.terminate()

    def _work(self, mode, store):
        try:
            iface, my_ip, net = wifiscan.local_network()
            warn = wifiscan.vpn_warning(iface, net)
            self.log = (warn + " · " if warn else "") + "PING SWEEP %s" % net
            wifiscan.ping_sweep(net)
            hosts = list(wifiscan.arp_table(net).values())
            if not any(h["ip"] == my_ip for h in hosts):
                hosts.append({"ip": my_ip, "mac": "00:00:00:00:00:00"})
            self.log = "%d HOSTS · VENDOR LOOKUP" % len(hosts)
            oui = wifiscan.load_oui()
            for i, h in enumerate(hosts, 1):
                h["me"] = h["ip"] == my_ip
                h["vendor"] = "this machine" if h["me"] else wifiscan.vendor(h["mac"], oui)
                h["name"] = wifiscan.reverse_name(h["ip"])
                if mode in ("ports", "nmap"):
                    self.log = "PORT SCAN %d/%d · %s" % (i, len(hosts), h["ip"])
                    h["ports"] = wifiscan.scan_ports(h["ip"])
                if mode == "nmap":
                    self.log = "NMAP -sV %d/%d · %s" % (i, len(hosts), h["ip"])
                    h["services"] = wifiscan.nmap_services(h["ip"])
                h["type"] = "this machine" if h["me"] else wifiscan.guess_type(h)
            hosts.sort(key=lambda h: [int(x) for x in h["ip"].split(".")])
            run_id, new = store.save_run(str(net), mode, hosts)
            store.decorate(hosts)
            self.result = {"hosts": hosts, "run_id": run_id, "network": str(net), "hints": wifiscan.PORT_HINTS, "warning": warn}
        except Exception as e:
            self.error = str(e)
        finally:
            self.done = True; self.running = False


class Handler(BaseHTTPRequestHandler):
    server_version = "wifiscan/" + VERSION

    def log_message(self, fmt, *args):
        if self.server.verbose:
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, code, body, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.split("?")[0] != "/":
            return self._send(404, b"not found", "text/plain")
        try:
            net = str(wifiscan.local_network()[2])
        except SystemExit:
            net = "nincs aktív interfész"
        page = (HTML.replace("__TOKEN__", TOKEN).replace("__VERSION__", VERSION)
                .replace("__DBPATH__", self.server.store.path).replace("__NET__", net)
                .replace("__NMAP__", ("bundled" if wifiscan.bundled_nmap() else ("system" if wifiscan.shutil_which("nmap") else "MISSING"))))
        self._send(200, page.encode(), "text/html")

    def do_POST(self):
        if self.headers.get("X-Token") != TOKEN:
            return self._send(403, b"bad token", "text/plain")
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(min(length, 1 << 20))
        req = json.loads(body.decode() or "{}")
        st, job = self.server.store, self.server.job
        path = self.path.split("?")[0]
        try:
            if path == "/api/scan":
                mode = req.get("mode", "discover")
                if mode not in ("discover", "ports", "nmap"):
                    raise ValueError("bad mode")
                job.start(mode, st)
                out = {"started": True}
            elif path == "/api/nmap":
                ips = [str(ip) for ip in req.get("ips", [])][:64]
                import ipaddress
                for ip in ips:
                    ipaddress.ip_address(ip)          # ValueError ha nem IP
                if not ips:
                    raise ValueError("no targets")
                job.start_nmap(ips, int(req.get("run_id") or 0), st, (req.get("sudo") or None))
                out = {"started": True}
            elif path == "/api/stop":
                job.stop()
                out = {"stopped": True}
            elif path == "/api/status":
                out = {"done": job.done, "log": job.log, "error": job.error, "result": job.result if job.done else None}
            elif path == "/api/history":
                out = st.runs(int(req.get("limit", 40)) or 40)
            elif path == "/api/run_get":
                out = {"hosts": st.run_hosts(int(req.get("id", 0))), "hints": wifiscan.PORT_HINTS}
            elif path == "/api/devices":
                out = st.devices()
            elif path == "/api/device":
                st.set_device(str(req["mac"]), req.get("label"), req.get("trusted"))
                out = {"ok": True}
            elif path == "/api/export":
                fmt = "json" if "format=json" in self.path else "csv"
                return self._send(200, st.export(fmt).encode(), "application/json" if fmt == "json" else "text/csv")
            else:
                return self._send(404, b"not found", "text/plain")
        except (ValueError, KeyError) as e:
            return self._send(400, str(e).encode(), "text/plain")
        self._send(200, json.dumps(out, ensure_ascii=False).encode())


def serve(port=8766, open_browser=True, verbose=False, db_path=None):
    try:
        httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    except OSError:
        print("wifiscan gui: port %d busy, picking a free one" % port, file=sys.stderr)
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    httpd.verbose = verbose
    httpd.store = Store(db_path)
    httpd.job = Job()
    url = "http://127.0.0.1:%d/" % httpd.server_address[1]
    print("wifiscan gui: %s  (Ctrl-C stops) · database: %s" % (url, httpd.store.path))
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


