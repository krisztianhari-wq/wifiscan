"""wifiscan GUI – Hackerman / Kung Fury VHS-synthwave stílus (króm cím, neon magenta-cián, laser grid).

Csak 127.0.0.1-en hallgat, minden API hívás a lapba ágyazott véletlen tokent viszi.
Indítás:  python3 gui.py [--port 8766] [--no-browser]
"""
import argparse, ipaddress, json, secrets, sys, threading, time, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import engine as wifiscan, __version__ as VERSION
from .store import Store
TOKEN = secrets.token_urlsafe(24)

HTML = r"""
<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WIFISCAN</title>
<style>
:root{--bg:#F5F9FD;--surface:rgba(255,255,255,.6);--surface-2:rgba(238,244,250,.75);--solid:#FFFFFF;--line:#DCE7F1;--line-strong:#C3D4E4;
 --ink:#1B2733;--ink-2:#55697D;--ink-3:#7F92A5;--brand:#2F6497;--brand-soft:#BFDCF5;--mag:#6C93B8;--mag-soft:#E1EEF9;
 --good:#137A4A;--good-bg:#E2F3EA;--bad:#B93B31;--bad-bg:#F8E5E3;--warn:#8A5A12;--warn-bg:#F7EBD7;--info:#3B5BA9;--info-bg:#E8EEFA;
 --shadow:0 1px 2px rgba(27,39,51,.05),0 8px 24px -16px rgba(27,39,51,.28);
 --sans:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;--mono:ui-monospace,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;--head:var(--sans);--r:14px}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0F1720;--surface:rgba(24,36,48,.6);--surface-2:rgba(24,36,48,.8);--solid:#182430;--line:#243546;--line-strong:#33485C;
 --ink:#EDF4FA;--ink-2:#A9BBCC;--ink-3:#7F94A8;--brand:#9CC7F0;--brand-soft:#2F4A66;--mag:#7FA6CC;--mag-soft:#1F3247;
 --good:#5FC38E;--good-bg:#17301F;--bad:#E97F76;--bad-bg:#331C1A;--warn:#E8B86D;--warn-bg:#33291A;--info:#9DB4F0;--info-bg:#1F2A45;
 --shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px -16px rgba(0,0,0,.8)}}
:root[data-theme=dark]{--bg:#0F1720;--surface:rgba(24,36,48,.6);--surface-2:rgba(24,36,48,.8);--solid:#182430;--line:#243546;--line-strong:#33485C;
 --ink:#EDF4FA;--ink-2:#A9BBCC;--ink-3:#7F94A8;--brand:#9CC7F0;--brand-soft:#2F4A66;--mag:#7FA6CC;--mag-soft:#1F3247;
 --good:#5FC38E;--good-bg:#17301F;--bad:#E97F76;--bad-bg:#331C1A;--warn:#E8B86D;--warn-bg:#33291A;--info:#9DB4F0;--info-bg:#1F2A45;
 --shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px -16px rgba(0,0,0,.8)}
*{box-sizing:border-box}[hidden]{display:none!important}
html,body{margin:0;min-height:100%}
body{background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:14px;line-height:1.5;-webkit-font-smoothing:antialiased;
 background-image:radial-gradient(700px 420px at 0% -10%,color-mix(in srgb,var(--brand-soft) 45%,transparent),transparent 60%),radial-gradient(600px 420px at 100% 0%,color-mix(in srgb,var(--mag-soft) 70%,transparent),transparent 60%);background-attachment:fixed}
a{color:var(--brand);text-decoration:none}
h1,h2,h3{margin:0;text-wrap:balance}
.topbar{position:sticky;top:0;z-index:30;background:color-mix(in srgb,var(--solid) 70%,transparent);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border-bottom:1px solid var(--line)}
.topbar-in{max-width:1240px;margin:0 auto;padding:10px 24px;display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:10px;margin-right:6px}
.brand .dot{width:32px;height:32px;border-radius:10px;background:var(--brand);color:var(--bg);display:grid;place-items:center;font-family:var(--head);font-weight:600;font-size:16px}
.brand b{display:block;font-family:var(--head);font-weight:600;font-size:16px;letter-spacing:.01em;line-height:1.1}.brand span{display:block;font-size:11px;color:var(--ink-3)}
nav{display:flex;gap:4px;flex-wrap:wrap}
nav a{padding:6px 12px;border-radius:999px;color:var(--ink-2);font-weight:500;font-size:13px;border:1px solid transparent}
nav a:hover{background:var(--surface-2)}nav a.on{background:var(--mag-soft);color:var(--brand);border-color:var(--line)}
nav a i{display:none}
.spacer{flex:1}
.pill{display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:999px;font-size:12px;font-weight:600;border:1px solid var(--line);background:var(--surface-2);color:var(--ink-2);white-space:nowrap}
main{max-width:1240px;margin:0 auto;padding:26px 24px 60px;width:100%}
.top{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;flex-wrap:wrap;margin-bottom:18px}
h1{font-family:var(--head);font-weight:700;font-size:28px;letter-spacing:-.02em;color:var(--ink)}
.sub{color:var(--ink-2);margin-top:2px}
.loc{display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:var(--r);background:var(--surface);border:1px solid var(--line);box-shadow:var(--shadow);backdrop-filter:blur(10px);flex-wrap:wrap}
.loc .ico{width:30px;height:30px;border-radius:9px;display:grid;place-items:center;background:var(--mag-soft);color:var(--brand)}
.loc input{font:inherit;font-weight:600;border:0;background:transparent;color:var(--ink);min-width:120px;outline:none;border-bottom:1px dashed var(--line-strong)}
.loc small{color:var(--ink-3);font-family:var(--mono);font-size:11px}
.badge{padding:2px 8px;border-radius:999px;font-size:10.5px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;border:1px solid transparent;white-space:nowrap}
.b-new{background:var(--bad-bg);color:var(--bad)}.b-known,.b-trusted{background:var(--good-bg);color:var(--good)}.b-unk{background:var(--warn-bg);color:var(--warn)}.b-seen{background:var(--info-bg);color:var(--info)}.b-me{background:var(--surface-2);color:var(--ink-3);border-color:var(--line)}
.grid{display:grid;gap:14px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:15px 16px 16px;box-shadow:var(--shadow);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);min-width:0}
.card h2{font-family:var(--head);font-weight:600;font-size:15px;color:var(--ink);margin-bottom:12px;letter-spacing:-.01em}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.seg{display:inline-flex;background:var(--surface-2);border:1px solid var(--line);border-radius:999px;padding:3px}
.seg button{background:transparent;color:var(--ink-2);box-shadow:none;padding:6px 14px;border-radius:999px;font-weight:600;font-size:13px}
.seg button.on{background:var(--solid);color:var(--brand);box-shadow:var(--shadow)}
input[type=text],input[type=password],select{font:inherit;padding:8px 12px;border-radius:10px;border:1px solid var(--line-strong);background:var(--solid);color:var(--ink);outline:none}
input:focus,select:focus{border-color:var(--brand);box-shadow:0 0 0 3px color-mix(in srgb,var(--brand) 18%,transparent)}
input.mono{font-family:var(--mono);font-size:13px}
input::placeholder{color:var(--ink-3)}
button{font:inherit;font-weight:600;border:1px solid transparent;border-radius:10px;padding:9px 16px;cursor:pointer;background:var(--brand);color:var(--bg);transition:.15s}
button.primary{background:var(--brand);color:var(--bg)}
button.primary:hover{filter:brightness(1.08)}
button.ghost{background:var(--solid);color:var(--ink);border-color:var(--line-strong)}
button.ghost:hover{background:var(--surface-2)}
button.danger{background:var(--bad-bg);color:var(--bad)}
button.sm{padding:5px 10px;font-size:12px;border-radius:9px}
button:disabled{opacity:.5;cursor:wait}
.hint{color:var(--ink-3);font-size:12px;margin-top:10px}
#log{font-family:var(--mono);font-size:12.5px;color:var(--ink);padding:10px 12px;border-radius:10px;background:var(--surface-2);border:1px solid var(--line);min-height:40px;white-space:pre-wrap}
#log::before{content:"▸ ";color:var(--brand)}
.warn{margin-top:10px;padding:10px 14px;border-radius:10px;background:var(--warn-bg);color:var(--warn);font-size:12.5px;border:1px solid var(--line)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-bottom:6px}
.kpi{padding:12px 14px;border-radius:var(--r);background:var(--surface-2);border:1px solid var(--line)}
.kpi b{display:block;font-family:var(--head);font-size:26px;font-weight:700;letter-spacing:-.02em;line-height:1.1;font-variant-numeric:tabular-nums}.kpi span{font-size:12px;color:var(--ink-2)}
.kpi.new b{color:var(--bad)}.kpi.unk b{color:var(--warn)}.kpi.trusted b{color:var(--good)}
table{width:100%;border-collapse:separate;border-spacing:0;font-size:13px}
th{text-align:left;font-size:11px;color:var(--ink-3);font-weight:600;text-transform:uppercase;letter-spacing:.06em;padding:8px 10px;border-bottom:1px solid var(--line)}
td{padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top}
tr:last-child td{border-bottom:0}
tr.click{cursor:pointer}tr.click:hover td{background:color-mix(in srgb,var(--mag-soft) 50%,transparent)}
td.mono{font-family:var(--mono);font-size:12px;color:var(--ink-2);white-space:nowrap;font-variant-numeric:tabular-nums}
td.strong{font-weight:600;min-width:120px}
td.lbl input{width:100%;padding:5px 9px;font-size:12.5px;border-radius:8px}
input[type=checkbox]{width:16px;height:16px;accent-color:var(--brand);cursor:pointer}
.sub-row td{padding-top:0;color:var(--ink-2);font-size:12px}
.sub-row b{color:var(--ink);font-weight:500;font-family:var(--mono);font-size:11.5px}
pre.svc{margin:6px 0 0;font:12px var(--mono);color:var(--ink);white-space:pre-wrap;padding:10px;border-radius:10px;background:var(--surface-2);border:1px solid var(--line)}
.toolbar{display:flex;gap:10px;flex-wrap:wrap;align-items:center;padding:10px 12px;border-radius:var(--r);background:var(--surface-2);border:1px solid var(--line);margin:12px 0}
.tabs{display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap;align-items:center}
.tabs button{background:transparent;color:var(--ink-2);padding:6px 12px;border-radius:999px}.tabs button.on{background:var(--mag-soft);color:var(--brand)}
.foot{color:var(--ink-3);font-size:11.5px;margin-top:26px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}
.two{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media (max-width:980px){.two{grid-template-columns:1fr}}
@media (max-width:700px){.topbar-in{padding:10px 14px}main{padding:18px 14px 40px}h1{font-size:24px}}
</style></head>
<body>
<header class="topbar"><div class="topbar-in">
  <div class="brand"><div class="dot">H</div><div><b>wifiscan</b><span>Hackerman edition · v__VERSION__</span></div></div>
  <nav>
    <a href="#scan" class="on"><i></i><span data-i18n="nav_scan">Scan</span></a>
    <a href="#devices"><i></i><span data-i18n="nav_devices">Devices</span></a>
    <a href="#locations"><i></i><span data-i18n="nav_locations">Locations</span></a>
    <a href="#runs"><i></i><span data-i18n="nav_runs">Runs</span></a>
  </nav>
  <div class="spacer"></div>
  <span class="pill" id="nmapstate">nmap: __NMAP__</span><button class="ghost sm" id="lang" type="button">HU</button><button class="ghost sm" id="theme" type="button" title="theme">◐</button>
</div></header>
<main>
  <div class="top">
    <div><h1 data-i18n="title">Network inventory</h1><div class="sub" data-i18n="sub"></div></div>
    <div class="loc" id="loc"><div class="ico">◎</div><div><input id="loc-label" type="text" data-i18n-ph="loc_ph"><div><small id="loc-meta">—</small></div></div><span class="badge" id="loc-badge" hidden></span></div>
  </div>

  <div class="grid">
  <section class="card" id="scan">
    <h2 data-i18n="request">Scan</h2>
    <div class="row">
      <div class="seg" id="mode"><button data-v="discover" class="on" data-i18n="m_discover"></button><button data-v="ports" data-i18n="m_ports"></button><button data-v="nmap" data-i18n="m_nmap"></button></div>
      <input id="subnet" class="mono" type="text" list="subnets" value="__NET__" style="width:190px" title="subnet (CIDR)"><datalist id="subnets"></datalist>
      <button id="run" class="primary" type="button" data-i18n="scan_btn">Scan network</button>
    </div>
    <div class="hint" id="netv"></div>
    <div class="hint" data-i18n="hint_req"></div>
    <div id="log" style="margin-top:14px"></div>
    <div class="warn" id="warnbox" hidden></div>
  </section>

  <section class="card" id="devices">
    <h2 data-i18n="response">Devices online</h2>
    <div class="kpis" id="summary"></div>
    <div class="toolbar" id="selbar" hidden>
      <button id="nmap-sel" class="primary sm" type="button" data-i18n="nmap_sel"></button>
      <button id="sel-all" class="ghost sm" type="button" data-i18n="all"></button>
      <button id="sel-none" class="ghost sm" type="button" data-i18n="none"></button>
      <button id="nmap-stop" class="danger sm" type="button" hidden>Stop</button>
      <input type="password" id="sudo" data-i18n-ph="sudo_ph" autocomplete="off" style="flex:1;min-width:240px">
      <span class="hint" id="sel-count" style="margin:0"></span>
    </div>
    <div class="hint" id="sudo-hint" hidden data-i18n="sudo_hint"></div>
    <div id="out" style="overflow:auto"></div>
  </section>

  <div class="two">
  <section class="card" id="locations">
    <h2 data-i18n="nav_locations">Locations</h2>
    <div id="nets" style="overflow:auto"></div>
    <div class="hint" data-i18n="loc_hint"></div>
  </section>
  <section class="card" id="runs">
    <h2 data-i18n="archive">Archive</h2>
    <div class="tabs"><button id="hist-runs" class="on" data-i18n="runs"></button><button id="hist-dev" data-i18n="devices"></button>
      <select id="netfilter" style="margin-left:auto"><option value="" data-i18n="all_locations"></option></select>
      <a class="pill" id="exp-csv" href="#" download="wifiscan-devices.csv">CSV</a><a class="pill" id="exp-json" href="#" download="wifiscan-devices.json">JSON</a></div>
    <div id="hist" style="overflow:auto"></div>
    <div class="hint"><span data-i18n="saved_to"></span>: <span class="mono" id="dbpath">__DBPATH__</span></div>
  </section>
  </div>
  </div>
  <div class="foot"><span>sadrobot · Krisz · Home Lab</span><span>wifiscan __VERSION__ · python stdlib + nmap · "I'm gonna hack time"</span></div>
</main>
<script>
const TOKEN="__TOKEN__";
const T={
en:{title:"Network inventory",sub:"Who is on the WiFi · vendor · device type · services · new devices per location",
 nav_scan:"Scan",nav_devices:"Devices",nav_locations:"Locations",nav_runs:"Runs",request:"Scan",response:"Devices online",archive:"Archive",
 m_discover:"Discover",m_ports:"Ports",m_nmap:"Nmap",scan_btn:"Scan network",
 hint_req:"Local server on 127.0.0.1 only. Scan only networks you own. Discover = ARP + mDNS/SSDP; Ports adds a quick port check; Nmap runs -sV on everything (slow). For targeted -O OS detection select rows and enter the sudo password.",
 nmap_sel:"Nmap on selected",all:"All",none:"None",sudo_ph:"sudo password (optional, -O OS detection)",
 sudo_hint:"The password goes only to the local server on 127.0.0.1, is passed to sudo via stdin, never stored or logged.",
 saved_to:"every run is saved to",runs:"Runs",devices:"Known devices",online:"online",new_here:"new here",unknown:"unknown",trusted:"trusted",seen:"seen",
 th:["Status","IP","MAC","Vendor","Type","Name","Label",""],label_ph:"e.g. living room TV",trust:"Trust",untrust:"Untrust",ports:"ports",
 sel_n:n=>n+" selected",sel_hint:"select rows to run nmap -sV on them",
 h_runs:["#","Time","Location","Mode","Devices","New"],h_dev:["Status","MAC","Label","Vendor","Type","Last IP","Locations","Last seen"],
 h_net:["Location","Gateway","Subnet","Runs","Devices","Last seen"],all_locations:"All locations",loc_ph:"name this location",
 loc_hint:"A location is identified by the router's MAC address (or the WiFi name when macOS lets us read it). Rename it here; NEW means first seen at this location.",
 loc_new:"new location",loc_known:"known location",elsewhere:"seen elsewhere",
 waiting:"ready",scanning:"scanning",online_msg:(n,nw,id)=>`${n} devices online · ${nw} new here · run #${id} archived`,recalled:(id,n)=>`run #${id} recalled · ${n} devices`,
 label_stored:"label stored for",specify:"select at least one device",nmap_on:(f,n)=>`nmap ${f} running on ${n} target(s)…`,nmap_done:n=>`nmap complete · ${n} target(s)`,abort:"abort requested, waiting for nmap to exit",fail:"failed",
 detected:(i,ip,c)=>`${i} ${ip} · detected subnets: ${c}`,types:{}},
hu:{title:"Hálózati eszközleltár",sub:"Ki van a WiFi-n · gyártó · eszköztípus · szolgáltatások · új eszközök helyenként",
 nav_scan:"Scan",nav_devices:"Eszközök",nav_locations:"Helyek",nav_runs:"Futások",request:"Scan",response:"Eszközök online",archive:"Archívum",
 m_discover:"Felderítés",m_ports:"Portok",m_nmap:"Nmap",scan_btn:"Hálózat scan",
 hint_req:"Helyi szerver csak 127.0.0.1-en. Csak saját hálózatot scannelj. Felderítés = ARP + mDNS/SSDP; Portok gyors portellenőrzést ad; Nmap mindenre -sV-t futtat (lassú). Célzott -O OS-felismeréshez jelölj ki sorokat és add meg a sudo jelszót.",
 nmap_sel:"Nmap a kijelöltekre",all:"Mind",none:"Egyik sem",sudo_ph:"sudo jelszó (opcionális, -O OS-felismerés)",
 sudo_hint:"A jelszó csak a helyi szervernek megy 127.0.0.1-en, stdin-en adja át a sudo-nak, nem tárolódik és nem naplózódik.",
 saved_to:"minden futás mentve",runs:"Futások",devices:"Ismert eszközök",online:"online",new_here:"új itt",unknown:"ismeretlen",trusted:"megbízható",seen:"látott",
 th:["Státusz","IP","MAC","Gyártó","Típus","Név","Címke",""],label_ph:"pl. nappali TV",trust:"Trust",untrust:"Untrust",ports:"portok",
 sel_n:n=>n+" kijelölve",sel_hint:"jelöld ki, mire fusson nmap -sV",
 h_runs:["#","Idő","Hely","Mód","Eszköz","Új"],h_dev:["Státusz","MAC","Címke","Gyártó","Típus","Utolsó IP","Helyek","Utoljára"],
 h_net:["Hely","Gateway","Alhálózat","Futás","Eszköz","Utoljára"],all_locations:"Minden hely",loc_ph:"nevezd el ezt a helyet",
 loc_hint:"A helyet a router MAC-címe azonosítja (vagy a WiFi neve, ha a macOS kiadja). Itt átnevezheted; a NEW azt jelenti, hogy ezen a helyen először látott eszköz.",
 loc_new:"új hely",loc_known:"ismert hely",elsewhere:"máshol már látott",
 waiting:"kész",scanning:"scan fut",online_msg:(n,nw,id)=>`${n} eszköz online · ${nw} új itt · #${id} futás archiválva`,recalled:(id,n)=>`#${id} futás előhívva · ${n} eszköz`,
 label_stored:"címke mentve",specify:"jelölj ki legalább egy eszközt",nmap_on:(f,n)=>`nmap ${f} fut ${n} célon…`,nmap_done:n=>`nmap kész · ${n} cél`,abort:"megszakítás kérve, várom az nmap kilépését",fail:"nem sikerült",
 detected:(i,ip,c)=>`${i} ${ip} · felismert alhálózatok: ${c}`,
 types:{"this machine":"ez a gép","unknown":"ismeretlen","?":"?","(randomized MAC – phone/laptop private address)":"(randomizált MAC – telefon/laptop privát cím)","ABORTED":"MEGSZAKÍTVA","nmap not installed":"nmap nincs telepítve",
  "Ring camera / doorbell":"Ring kamera / csengő","Roomba robot vacuum":"Roomba robotporszívó","Gree air conditioner (WiFi module)":"Gree klíma (WiFi modul)","Tesla car":"Tesla autó","Shelly smart relay":"Shelly okosrelé",
  "IoT smart home":"IoT okosotthon","LG TV / appliance":"LG TV / készülék","Denon / Marantz receiver":"Denon / Marantz erősítő","Sonos speaker":"Sonos hangszóró","HP printer / PC":"HP nyomtató / PC","Canon printer":"Canon nyomtató",
  "Brother printer":"Brother nyomtató","Epson printer":"Epson nyomtató","Samsung phone / tablet / TV":"Samsung telefon / tablet / TV","Xiaomi phone / IoT":"Xiaomi telefon / IoT","Huawei phone":"Huawei telefon","OnePlus phone":"OnePlus telefon",
  "Apple device":"Apple eszköz","Google Pixel phone":"Google Pixel telefon","Samsung phone":"Samsung telefon","Home theater receiver":"Házimozi erősítő","Printer":"Nyomtató","IP camera":"IP kamera","IoT / smart home":"IoT / okosotthon",
  "Linux device / router":"Linux eszköz / router","Phone / laptop (private MAC)":"Telefon / laptop (privát MAC)","Printer (LPD)":"Nyomtató (LPD)","RTSP (camera)":"RTSP (kamera)","IPP printer":"IPP nyomtató","Printer (JetDirect)":"Nyomtató (JetDirect)",
  "IoT / WiFi module":"IoT / WiFi modul","IoT / embedded (Murata WiFi module)":"IoT / beágyazott (Murata WiFi modul)","unknown (no ARP reply)":"ismeretlen (nincs ARP-válasz)"}}};
let LANG=(()=>{try{return localStorage.getItem('wifiscan.lang')}catch(e){return null}})()||((navigator.language||'').startsWith('hu')?'hu':'en');
const t=k=>T[LANG][k], tt=s=>T[LANG].types[s]||s;
const $=id=>document.getElementById(id);
function applyLang(){document.documentElement.lang=LANG;$('lang').textContent=LANG==='hu'?'EN':'HU';
  document.querySelectorAll('[data-i18n]').forEach(el=>{const v=t(el.dataset.i18n);if(typeof v==='string')el.textContent=v});
  document.querySelectorAll('[data-i18n-ph]').forEach(el=>el.placeholder=t(el.dataset.i18nPh));
  if(current)render(current);else $('log').textContent=t('waiting');showRuns();loadNets();try{localStorage.setItem('wifiscan.lang',LANG)}catch(e){}}
$('lang').onclick=()=>{LANG=LANG==='hu'?'en':'hu';applyLang()};
$('theme').onclick=()=>{const r=document.documentElement;const cur=r.dataset.theme||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');r.dataset.theme=cur==='dark'?'light':'dark';try{localStorage.setItem('wifiscan.theme',r.dataset.theme)}catch(e){}};
try{const th=localStorage.getItem('wifiscan.theme');if(th)document.documentElement.dataset.theme=th}catch(e){}
const log=$('log'),out=$('out'),sum=$('summary'),run=$('run');
let MODE='discover';$('mode').querySelectorAll('button').forEach(b=>b.onclick=()=>{MODE=b.dataset.v;$('mode').querySelectorAll('button').forEach(x=>x.classList.toggle('on',x===b))});
const say=m=>{log.textContent=m};
function esc(s){return String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
async function api(path,body){const r=await fetch(path,{method:'POST',headers:{'X-Token':TOKEN,'Content-Type':'application/json'},body:JSON.stringify(body||{})});if(!r.ok)throw new Error(r.status+' '+await r.text());return r.json()}
function status(h){if(h.me)return 'ME';if(h.new)return 'NEW';if(h.trusted)return 'TRUSTED';if(h.type==='?'&&!h.label)return 'UNKNOWN';return 'SEEN'}
const BC={NEW:'b-new',UNKNOWN:'b-unk',TRUSTED:'b-trusted',SEEN:'b-seen',ME:'b-me'};
const V=v=>`<span class="badge ${BC[v]||'b-seen'}">${v}</span>`;
let poll=null,current=null;const sel=new Set();
function showLocation(net,isNew){if(!net)return;$('loc-label').value=net.label||'';$('loc-label').dataset.key=net.key;
  $('loc-meta').textContent=[net.ssid?'SSID '+net.ssid:'',net.gateway_vendor?net.gateway_vendor:'',net.gateway_mac||'',net.subnet||''].filter(Boolean).join(' · ');
  const b=$('loc-badge');b.hidden=false;b.className='badge '+(isNew?'b-new':'b-known');b.textContent=isNew?t('loc_new'):t('loc_known')}
$('loc-label').onchange=()=>api('/api/network',{key:$('loc-label').dataset.key,label:$('loc-label').value}).then(()=>{loadNets();showRuns()}).catch(e=>say(e));
function render(data){
  const hosts=data.hosts;out.innerHTML="";
  const c={NEW:0,UNKNOWN:0,TRUSTED:0,SEEN:0};hosts.forEach(h=>{const s=status(h);if(s in c)c[s]++});
  sum.innerHTML=`<div class="kpi"><b>${hosts.length}</b><span>${t('online')}</span></div><div class="kpi new"><b>${c.NEW}</b><span>${t('new_here')}</span></div><div class="kpi unk"><b>${c.UNKNOWN}</b><span>${t('unknown')}</span></div><div class="kpi trusted"><b>${c.TRUSTED}</b><span>${t('trusted')}</span></div><div class="kpi"><b>${c.SEEN}</b><span>${t('seen')}</span></div>`;
  const tb=document.createElement('table');
  tb.innerHTML='<tr><th></th>'+t('th').map(x=>'<th>'+x+'</th>').join('')+'</tr>'+
    hosts.map(h=>`<tr><td>${h.me?'':`<input type="checkbox" data-ip="${esc(h.ip)}" ${sel.has(h.ip)?'checked':''}>`}</td><td>${V(status(h))}${h.known_elsewhere?` <span class="badge b-seen" title="${t('elsewhere')}">↔</span>`:''}</td><td class="mono">${esc(h.ip)}</td><td class="mono">${esc(h.mac)}</td><td>${esc(tt(h.vendor))}</td><td class="strong">${esc(tt(h.type))}</td><td class="mono">${esc(h.name)}</td>
    <td class="lbl"><input type="text" value="${esc(h.label)}" data-mac="${esc(h.mac)}" placeholder="${t('label_ph')}"></td>
    <td><button class="ghost sm" data-trust="${esc(h.mac)}" data-val="${h.trusted?0:1}">${h.trusted?t('untrust'):t('trust')}</button></td></tr>`+
    ((h.ports&&h.ports.length)||h.services?`<tr class="sub-row"><td></td><td colspan="8">${h.ports&&h.ports.length?t('ports')+': '+h.ports.map(p=>`<b>${p}</b> ${esc(tt(data.hints[p]||''))}`).join(' · '):''}${h.services?`<pre class="svc">${esc(tt(h.services))}</pre>`:''}</td></tr>`:'')).join('');
  out.appendChild(tb);current=data;$('selbar').hidden=false;$('sudo-hint').hidden=false;
  if(data.network)showLocation(data.network,data.new_location);
  tb.querySelectorAll('input[type=checkbox]').forEach(c=>c.onchange=()=>{c.checked?sel.add(c.dataset.ip):sel.delete(c.dataset.ip);selCount()});selCount();
  tb.querySelectorAll('td.lbl input').forEach(i=>i.onchange=()=>api('/api/device',{mac:i.dataset.mac,label:i.value}).then(()=>say(t('label_stored')+' '+i.dataset.mac)).catch(e=>say(e)));
  tb.querySelectorAll('button[data-trust]').forEach(b=>b.onclick=()=>api('/api/device',{mac:b.dataset.trust,trusted:+b.dataset.val}).then(()=>{const h=hosts.find(x=>x.mac===b.dataset.trust);h.trusted=!!+b.dataset.val;render(data)}).catch(e=>say(e)));
}
function selCount(){$('sel-count').textContent=sel.size?t('sel_n')(sel.size):t('sel_hint')}
$('sel-all').onclick=()=>{current.hosts.forEach(h=>{if(!h.me)sel.add(h.ip)});render(current)};
$('sel-none').onclick=()=>{sel.clear();render(current)};
function watch(onDone,onEnd){poll=setInterval(async()=>{try{const s=await api('/api/status');if(s.log)say(s.log);
  if(s.done){clearInterval(poll);onEnd();if(s.error){say(t('fail')+' · '+s.error);return}onDone(s.result)}}catch(e){clearInterval(poll);onEnd();say(e)}},700)}
$('nmap-sel').onclick=async()=>{if(!sel.size){say(t('specify'));return}const b=$('nmap-sel'),stop=$('nmap-stop');
  const end=()=>{b.disabled=false;run.disabled=false;stop.hidden=true};b.disabled=true;run.disabled=true;stop.hidden=false;
  try{const pw=$('sudo').value;await api('/api/nmap',{ips:[...sel],run_id:current.run_id,sudo:pw});say(t('nmap_on')(pw?'-O -sV':'-sV',sel.size));
    watch(r=>{for(const h of current.hosts)if(r.services[h.ip]!==undefined)h.services=r.services[h.ip];render(current);say(t('nmap_done')(Object.keys(r.services).length))},end)}
  catch(e){end();say(e)}};
$('nmap-stop').onclick=()=>api('/api/stop').then(()=>say(t('abort'))).catch(e=>say(e));
async function loadSubnets(){try{const d=await api('/api/subnets');$('subnets').innerHTML=d.candidates.map(c=>`<option value="${c.cidr}">${c.source}</option>`).join('');
  if(d.candidates.length){$('subnet').value=d.candidates[0].cidr;$('netv').textContent=t('detected')(d.iface,d.ip,d.candidates.map(c=>c.cidr+' ['+c.source+']').join(' · '))}
  if(d.network)showLocation(d.network,d.new_location)}catch(e){}}
run.onclick=async()=>{if(run.disabled)return;run.disabled=true;sel.clear();out.innerHTML="";sum.innerHTML="";$('warnbox').hidden=true;
  try{await api('/api/scan',{mode:MODE,net:$('subnet').value});say(t('scanning')+' · '+MODE);
    watch(r=>{$('subnet').value=r.network_cidr;render(r);say(t('online_msg')(r.hosts.length,r.hosts.filter(h=>h.new).length,r.run_id));if(r.warning){$('warnbox').textContent=r.warning;$('warnbox').hidden=false}showRuns();loadNets()},()=>{run.disabled=false})}
  catch(e){run.disabled=false;say(e)}};
function table(el,rows,cols,onclick){el.innerHTML='<table><tr>'+cols.map(c=>'<th>'+esc(c[0])+'</th>').join('')+'</tr>'+rows.map(r=>'<tr class="'+(onclick?'click':'')+'" data-id="'+esc(r.id??r.key??'')+'">'+cols.map(c=>'<td class="'+(c[2]||'')+'">'+(c[1](r))+'</td>').join('')+'</tr>').join('')+'</table>';
  if(onclick)el.querySelectorAll('tr.click').forEach(tr=>tr.onclick=()=>onclick(tr.dataset.id))}
const fmt=s=>esc((s||'').replace('T',' ').slice(0,16));
let HIST='runs';
async function showRuns(){HIST='runs';$('hist-runs').classList.add('on');$('hist-dev').classList.remove('on');try{const H=t('h_runs');table($('hist'),await api('/api/history',{limit:40,network_key:$('netfilter').value||null}),[[H[0],r=>r.id],[H[1],r=>fmt(r.ts),'mono'],[H[2],r=>esc(r.location||r.network),'strong'],[H[3],r=>esc(r.mode)],[H[4],r=>r.n_hosts],[H[5],r=>r.n_new?V('NEW')+' '+r.n_new:'—']],id=>loadRun(+id))}catch(e){say(e)}}
async function showDev(){HIST='dev';$('hist-dev').classList.add('on');$('hist-runs').classList.remove('on');try{const H=t('h_dev');table($('hist'),await api('/api/devices',{network_key:$('netfilter').value||null}),[[H[0],r=>V(r.trusted?'TRUSTED':'SEEN')],[H[1],r=>esc(r.mac),'mono'],[H[2],r=>esc(r.label),'strong'],[H[3],r=>esc(tt(r.vendor))],[H[4],r=>esc(tt(r.type||''))],[H[5],r=>esc(r.last_ip),'mono'],[H[6],r=>esc(r.location||'')],[H[7],r=>fmt(r.last_seen),'mono']],null)}catch(e){say(e)}}
async function loadNets(){try{const nets=await api('/api/networks');const H=t('h_net');
  table($('nets'),nets,[[H[0],n=>`<input type="text" value="${esc(n.label)}" data-key="${esc(n.key)}" style="padding:5px 8px;border-radius:8px;font-size:12.5px;width:130px">`+(n.ssid?`<div class="hint" style="margin:2px 0 0">SSID ${esc(n.ssid)}</div>`:'')],[H[1],n=>esc([n.gateway_vendor,n.gateway_mac].filter(Boolean).join(' ')),'mono'],[H[2],n=>esc(n.subnet),'mono'],[H[3],n=>n.run_count],[H[4],n=>n.n_devices],[H[5],n=>fmt(n.last_seen),'mono']],null);
  $('nets').querySelectorAll('input').forEach(i=>i.onchange=()=>api('/api/network',{key:i.dataset.key,label:i.value}).then(()=>{loadNets();showRuns();if($('loc-label').dataset.key===i.dataset.key)$('loc-label').value=i.value}).catch(e=>say(e)));
  const f=$('netfilter'),cur=f.value;f.innerHTML=`<option value="">${t('all_locations')}</option>`+nets.map(n=>`<option value="${esc(n.key)}">${esc(n.label)}</option>`).join('');f.value=cur}catch(e){}}
$('netfilter').onchange=()=>HIST==='runs'?showRuns():showDev();
async function loadRun(id){try{const d=await api('/api/run_get',{id});render(d);say(t('recalled')(id,d.hosts.length));location.hash='#devices'}catch(e){say(e)}}
$('hist-runs').onclick=showRuns;$('hist-dev').onclick=showDev;
async function exportAs(fmt,a){const r=await fetch('/api/export?format='+fmt,{method:'POST',headers:{'X-Token':TOKEN},body:'{}'});a.href=URL.createObjectURL(await r.blob())}
for(const [id,fmt] of [['exp-csv','csv'],['exp-json','json']])$(id).addEventListener('click',async function(e){if(this.dataset.ready){this.dataset.ready='';return}e.preventDefault();await exportAs(fmt,this);this.dataset.ready='1';this.click()});
document.querySelectorAll('nav a').forEach(a=>a.onclick=()=>document.querySelectorAll('nav a').forEach(x=>x.classList.toggle('on',x===a)));
applyLang();loadSubnets();
</script></body></html>
"""


class Job:
    def __init__(self):
        self.lock = threading.Lock()
        self.reset()

    def reset(self):
        self.running = False; self.done = False; self.error = ""; self.log = ""; self.result = None
        self.cancel = False; self.proc = None

    def start(self, mode, store, net_override=None):
        with self.lock:
            if self.running:
                raise ValueError("scan already running")
            self.reset(); self.running = True
        threading.Thread(target=self._work, args=(mode, store, net_override), daemon=True).start()

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

    def _work(self, mode, store, net_override=None):
        try:
            iface, my_ip, net = wifiscan.local_network()
            if net_override:
                n = ipaddress.ip_network(net_override, strict=False)
                if n.prefixlen < 22 or n.prefixlen > 30:
                    raise ValueError("subnet must be between /22 and /30")
                if not n.is_private and ipaddress.ip_address(my_ip) not in n:
                    raise ValueError("only private ranges or your own subnet can be scanned")
                net = n
            self.log = "SUBNET %s" % net
            warn = wifiscan.vpn_warning(iface, net)
            self.log = (warn + " · " if warn else "") + "PING SWEEP %s" % net
            hosts = list(wifiscan.discover(net).values())
            if not any(h["ip"] == my_ip for h in hosts):
                hosts.append({"ip": my_ip, "mac": "00:00:00:00:00:00"})
            self.log = "%d HOSTS · VENDOR LOOKUP" % len(hosts)
            oui = wifiscan.load_oui()
            wifiscan.resolve_names(hosts)
            for i, h in enumerate(hosts, 1):
                h["me"] = h["ip"] == my_ip
                h["vendor"] = "this machine" if h["me"] else wifiscan.vendor(h["mac"], oui)
                h["name"] = h.get("name") or h.get("hint", "")
                if mode in ("ports", "nmap"):
                    self.log = "PORT SCAN %d/%d · %s" % (i, len(hosts), h["ip"])
                    h["ports"] = wifiscan.scan_ports(h["ip"])
                if mode == "nmap":
                    self.log = "NMAP -sV %d/%d · %s" % (i, len(hosts), h["ip"])
                    h["services"] = wifiscan.nmap_services(h["ip"])
                h["type"] = "this machine" if h["me"] else wifiscan.guess_type(h)
            hosts.sort(key=lambda h: [int(x) for x in h["ip"].split(".")])
            diag = wifiscan.diagnose_empty(hosts, my_ip)
            warn = " · ".join(x for x in (warn, diag) if x)
            self.log = "LOCATION"
            ident = wifiscan.network_identity(iface, net, oui)
            run_id, new = store.save_run(str(net), mode, hosts, ident)
            store.decorate(hosts)
            self.result = {"hosts": hosts, "run_id": run_id, "network": str(net), "hints": wifiscan.PORT_HINTS, "warning": warn,
                           "network": store.network_of_run(run_id), "new_location": store.last_location_new}
            self.result["network_cidr"] = str(net)
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
                job.start(mode, st, (req.get("net") or "").strip() or None)
                out = {"started": True}
            elif path == "/api/subnets":
                iface, my_ip, net = wifiscan.local_network()
                ident = wifiscan.network_identity(iface, net, wifiscan.load_oui())
                nets = st.networks()
                known = next((n for n in nets if n["key"] == ident["key"]), None) or \
                        next((n for n in nets if n["key"] == "net:" + ident["subnet"]), None)
                cur = known or dict(ident, label=ident["default_label"], run_count=0)
                out = {"iface": iface, "ip": my_ip, "candidates": wifiscan.detect_subnets(iface, my_ip),
                       "network": cur, "new_location": known is None}
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
                out = st.runs(int(req.get("limit", 40)) or 40, req.get("network_key") or None)
            elif path == "/api/run_get":
                rid = int(req.get("id", 0))
                out = {"hosts": st.run_hosts(rid), "hints": wifiscan.PORT_HINTS, "run_id": rid, "network": st.network_of_run(rid), "new_location": False}
            elif path == "/api/devices":
                out = st.devices(req.get("network_key") or None)
            elif path == "/api/networks":
                out = st.networks()
            elif path == "/api/network":
                st.set_network_label(str(req["key"]), str(req.get("label", ""))[:80])
                out = {"ok": True}
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


