#!/usr/bin/env python3
# ============================================================
#  ShockNet — core/agent.py  v1.0
# ============================================================

import sys, os, threading, webbrowser, socket, subprocess, platform
import logging, io
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, send_file

CORE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CORE_DIR)
sys.path.insert(0, ROOT_DIR)

from core.config import (AGENT_PORT, THEMES, AUTH_TOKEN, AES_KEY,
                          SOUND_ENABLED, APP_NAME, KIOSK_MODE)
from core.crypto_utils import decrypt_payload

LOG_FILE    = os.path.join(ROOT_DIR, "agent.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
log        = logging.getLogger("shocknet-agent")
app        = Flask(__name__)
pending    = {}
read_status= {}
kiosk_stop = threading.Event()

# HTML
HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ShockNet</title>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Bebas+Neue&family=Space+Grotesk:wght@700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body{width:100%;height:100%;overflow:hidden}

/* ═══════════════════════════════════════════════════════
   CYBER — intrusión en terminal, sin card, todo en bruto
═══════════════════════════════════════════════════════ */
{% if t.accent == "#00f0ff" %}
body{background:#000;color:#00f0ff;font-family:'Share Tech Mono',monospace;position:relative;}

/* ruido de TV */
@keyframes noise{
  0%{background-position:0 0}
  10%{background-position:-5% -10%}
  20%{background-position:-15% 5%}
  30%{background-position:7% -25%}
  40%{background-position:20% 25%}
  50%{background-position:-25% 10%}
  60%{background-position:15% 5%}
  70%{background-position:0% 15%}
  80%{background-position:25% 35%}
  90%{background-position:-10% 10%}
  100%{background-position:0 0}
}
body::before{
  content:'';position:fixed;inset:0;z-index:0;opacity:.03;
  background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  background-size:200px 200px;
  animation:noise .4s steps(1) infinite;
  pointer-events:none;
}
/* scanlines */
body::after{
  content:'';position:fixed;inset:0;z-index:0;
  background:repeating-linear-gradient(0deg,rgba(0,0,0,.18) 0,rgba(0,0,0,.18) 1px,transparent 1px,transparent 2px);
  pointer-events:none;
}

.kiosk-badge{position:fixed;top:8px;right:10px;z-index:999;font-size:.6rem;color:rgba(0,240,255,.4);letter-spacing:.1em;{% if not kiosk %}display:none;{% endif %}}
.enc-badge{position:fixed;top:8px;left:10px;z-index:999;font-size:.6rem;color:rgba(0,240,255,.35);letter-spacing:.1em;{% if not encrypted %}display:none!important;{% endif %}}

/* layout full screen dividido en filas */
.screen{
  position:fixed;inset:0;z-index:1;
  display:flex;flex-direction:column;
  padding:clamp(1.5rem,4vw,3rem);
}
/* fila 1: id del proceso y timestamp */
.row-top{
  display:flex;justify-content:space-between;align-items:center;
  border-bottom:1px solid rgba(0,240,255,.1);
  padding-bottom:.6rem;margin-bottom:1.2rem;
  font-size:.65rem;color:rgba(0,240,255,.3);letter-spacing:.08em;
}
.blink{animation:blink .8s step-start infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0}}
/* fila 2: el título ocupa toda la pantalla de ancho */
.row-title{
  flex:0 0 auto;
  margin-bottom:clamp(.8rem,2vw,1.4rem);
}
h1{
  font-family:'Bebas Neue',sans-serif;
  font-size:clamp(3.5rem,10vw,8rem);
  line-height:.9;letter-spacing:.02em;
  color:#00f0ff;
  text-shadow:
    0 0 20px rgba(0,240,255,.6),
    0 0 80px rgba(0,240,255,.2),
    2px 0 rgba(255,0,80,.3),
    -2px 0 rgba(0,240,255,.3);
  word-break:break-word;
  /* glitch */
  position:relative;
  animation:hglitch 7s step-start infinite;
}
@keyframes hglitch{
  0%,93%,100%{clip-path:none;transform:none}
  94%{clip-path:inset(30% 0 40% 0);transform:translate(-3px)}
  95%{clip-path:inset(60% 0 10% 0);transform:translate(3px)}
  96%{clip-path:none;transform:none}
}
/* fila 3: mensaje con cursor de escritura */
.row-msg{
  flex:1 1 auto;
  border-left:3px solid rgba(0,240,255,.4);
  padding-left:1.2rem;
  margin-bottom:1.5rem;
  overflow:hidden;
}
.msg-text{
  font-size:clamp(.8rem,2vw,.95rem);
  color:rgba(0,240,255,.6);
  line-height:1.8;white-space:pre-wrap;
  overflow:hidden;
  border-right:.1em solid #00f0ff;
  animation:typing 1.5s steps(40,end),cursor .8s step-start infinite;
}
@keyframes typing{from{max-height:0}to{max-height:9999px}}
@keyframes cursor{0%,100%{border-color:#00f0ff}50%{border-color:transparent}}
/* fila 4: botón */
.row-btn{flex:0 0 auto;display:flex;align-items:center;gap:1.5rem;}
.btn{
  font-family:'Share Tech Mono',monospace;
  font-size:.9rem;letter-spacing:.2em;text-transform:uppercase;
  padding:.65rem 2.2rem;
  background:transparent;color:#00f0ff;
  border:1px solid rgba(0,240,255,.5);
  cursor:pointer;
  transition:background .2s,box-shadow .2s;
}
.btn:hover{background:rgba(0,240,255,.08);box-shadow:0 0 18px rgba(0,240,255,.3);}
.ts{font-size:.6rem;color:rgba(0,240,255,.2);letter-spacing:.06em;}
{% endif %}

/* ═══════════════════════════════════════════════════════
   AURORA — editorial brutal, split asimétrico, tipografía XL
═══════════════════════════════════════════════════════ */
{% if t.accent == "#c060ff" %}
body{
  background:#07000e;
  color:#f0e0ff;
  font-family:'Space Grotesk',sans-serif;
  overflow:hidden;
}
/* fondo aurora */
body::before{
  content:'';position:fixed;inset:0;z-index:0;
  background:
    radial-gradient(ellipse 120% 70% at -20% 120%, rgba(100,0,200,.55) 0%,transparent 55%),
    radial-gradient(ellipse 90%  60% at 120%  -10%,rgba(200,50,255,.4)  0%,transparent 50%);
  animation:amove 12s ease-in-out infinite alternate;
  pointer-events:none;
}
@keyframes amove{
  from{filter:hue-rotate(0deg) brightness(.9)}
  to  {filter:hue-rotate(20deg) brightness(1.1)}
}
/* grain */
body::after{
  content:'';position:fixed;inset:0;z-index:0;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='400'%3E%3Cfilter id='g'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='400' height='400' filter='url(%23g)' opacity='0.04'/%3E%3C/svg%3E");
  background-size:300px 300px;pointer-events:none;
}
.kiosk-badge{position:fixed;top:10px;right:12px;z-index:999;font-size:.62rem;color:rgba(192,96,255,.5);letter-spacing:.1em;{% if not kiosk %}display:none;{% endif %}}
.enc-badge{position:fixed;top:10px;left:12px;z-index:999;font-size:.62rem;color:rgba(192,96,255,.4);letter-spacing:.1em;{% if not encrypted %}display:none!important;{% endif %}}

/* LAYOUT: 2 columnas asimétricas */
.screen{
  position:fixed;inset:0;z-index:1;
  display:grid;
  grid-template-columns:1fr 1fr;
  grid-template-rows:1fr;
}
/* columna izquierda: solo el título gigante */
.col-left{
  display:flex;flex-direction:column;justify-content:flex-end;
  padding:clamp(1.5rem,4vw,3.5rem);
  border-right:1px solid rgba(192,96,255,.12);
  position:relative;overflow:hidden;
}
/* número de alerta decorativo al fondo */
.col-left::before{
  content:'!';
  position:absolute;bottom:-10%;left:-5%;
  font-family:'Bebas Neue',sans-serif;
  font-size:55vw;line-height:1;
  color:rgba(192,96,255,.04);
  user-select:none;pointer-events:none;
}
.alert-label{
  font-size:.7rem;letter-spacing:.22em;text-transform:uppercase;
  color:rgba(192,96,255,.45);margin-bottom:1rem;
  display:flex;align-items:center;gap:.6rem;
}
.alert-label::before{
  content:'';display:inline-block;
  width:20px;height:1px;background:rgba(192,96,255,.4);
}
h1{
  font-family:'Bebas Neue',sans-serif;
  font-size:clamp(3rem,7vw,6rem);
  line-height:.88;letter-spacing:-.01em;
  word-break:break-word;
  background:linear-gradient(170deg,
    #ffffff 0%,
    #e0b0ff 25%,
    #c060ff 65%,
    #6010aa 100%
  );
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  background-clip:text;
  filter:drop-shadow(0 0 30px rgba(192,96,255,.4));
}
/* columna derecha: mensaje + botón */
.col-right{
  display:flex;flex-direction:column;justify-content:center;
  padding:clamp(1.5rem,4vw,3.5rem);
  gap:2rem;
}
.logo-img{max-width:80px;max-height:50px;object-fit:contain;opacity:.8;}
.icon-c{
  font-size:2.8rem;
  filter:drop-shadow(0 0 20px rgba(192,96,255,.7));
  animation:ipulse 3s ease-in-out infinite;
}
@keyframes ipulse{
  0%,100%{filter:drop-shadow(0 0 15px rgba(192,96,255,.6))}
  50%    {filter:drop-shadow(0 0 35px rgba(192,96,255,1))}
}
.div{width:36px;height:2px;background:#c060ff;box-shadow:0 0 10px rgba(192,96,255,.7);}
.msg-text{
  font-size:clamp(.85rem,1.8vw,.98rem);
  color:rgba(200,160,255,.6);
  line-height:1.85;white-space:pre-wrap;
  max-height:40vh;overflow-y:auto;
}
.msg-text::-webkit-scrollbar{width:2px}
.msg-text::-webkit-scrollbar-thumb{background:rgba(192,96,255,.3)}
.btn{
  align-self:flex-start;
  padding:.8rem 2.5rem;
  font-family:'Space Grotesk',sans-serif;
  font-size:.9rem;font-weight:700;
  letter-spacing:.12em;text-transform:uppercase;
  background:rgba(192,96,255,.1);
  color:#d090ff;
  border:1px solid rgba(192,96,255,.4);
  cursor:pointer;
  box-shadow:0 0 24px rgba(192,96,255,.12),inset 0 1px 0 rgba(255,255,255,.04);
  transition:all .25s;
}
.btn:hover{
  background:rgba(192,96,255,.2);
  box-shadow:0 0 40px rgba(192,96,255,.3),inset 0 1px 0 rgba(255,255,255,.06);
  transform:translateY(-1px);
}
.ts{font-size:.62rem;color:rgba(192,96,255,.2);letter-spacing:.06em;}

/* móvil: apilar columnas */
@media(max-width:600px){
  .screen{grid-template-columns:1fr;grid-template-rows:auto 1fr;}
  .col-left{padding:2rem 1.5rem 1rem;border-right:none;border-bottom:1px solid rgba(192,96,255,.12);}
  h1{font-size:clamp(2.8rem,12vw,4.5rem);}
}
{% endif %}
</style>
</head>
<body>
<span class="kiosk-badge">// KIOSKO</span>
{% if encrypted %}<span class="enc-badge">// AES-256</span>{% endif %}

<div class="screen">

  {% if t.accent == "#00f0ff" %}
  <!-- CYBER layout terminal -->
  <div class="row-top">
    <span>SHOCKNET :: PID {{ notif_id[:8] }}</span>
    <span><span class="blink">▮</span> ALERTA ACTIVA</span>
  </div>
  <div class="row-title"><h1>{{ title }}</h1></div>
  <div class="row-msg"><p class="msg-text">{{ message }}</p></div>
  <div class="row-btn">
    <button class="btn" onclick="cerrar()">&gt; ACK_</button>
    <span class="ts" id="ts"></span>
  </div>
  {% endif %}

  {% if t.accent == "#c060ff" %}
  <!-- AURORA layout split -->
  <div class="col-left">
    <span class="alert-label">ShockNet · Alerta</span>
    <h1>{{ title }}</h1>
  </div>
  <div class="col-right">
    {% if image_url %}
      <img class="logo-img" src="{{ image_url }}" alt="">
    {% else %}
      <span class="icon-c">{{ t.icon }}</span>
    {% endif %}
    <div class="div"></div>
    <p class="msg-text">{{ message }}</p>
    <button class="btn" onclick="cerrar()">Entendido</button>
    <span class="ts" id="ts"></span>
  </div>
  {% endif %}

</div>

<script>
document.getElementById('ts').textContent =
  '{{ t.accent == "#00f0ff" and "//" or "·" }} ' + new Date().toLocaleTimeString();
var kiosk={{ kiosk|tojson }};
function goFull(){
  var el=document.documentElement;
  var r=el.requestFullscreen||el.webkitRequestFullscreen||el.mozRequestFullScreen;
  if(r){try{r.call(el)}catch(e){}}
}
goFull();
if(kiosk){
  setInterval(goFull,1000);
  window.addEventListener('keydown',function(e){
    if(['Escape','F11','F4'].includes(e.key)||(e.altKey&&e.key==='Tab')){
      e.preventDefault();e.stopPropagation();goFull();}},true);
  window.addEventListener('blur',function(){window.focus();goFull();});
}
var nid={{ notif_id|tojson }};
function cerrar(){
  try{fetch('/read',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({id:nid})});}catch(x){}
  document.body.style.transition='opacity .35s';
  document.body.style.opacity='0';
  setTimeout(function(){window.close();},380);
}
</script>
</body>
</html>"""
PWA_HOME = """<!DOCTYPE html>
<html lang="es"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="apple-mobile-web-app-capable" content="yes">
<link rel="manifest" href="/manifest.json">
<title>ShockNet Agent</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
body{min-height:100vh;background:#0d0d0d;color:#fff;
  font-family:'Space Grotesk',sans-serif;
  display:flex;flex-direction:column;align-items:center;
  justify-content:center;padding:2rem;}
.icon{font-size:3.5rem;margin-bottom:.8rem}
h1{font-size:1.8rem;font-weight:700;color:#e63946;margin-bottom:.4rem}
.sub{font-size:.9rem;color:rgba(255,255,255,.45);margin-bottom:2rem;text-align:center}
.card{width:100%;max-width:380px;background:rgba(255,255,255,.05);
  border:1px solid rgba(255,255,255,.1);border-radius:16px;
  padding:1.5rem;text-align:center;margin-bottom:1.2rem;}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:7px;
  background:#2ecc71;box-shadow:0 0 8px #2ecc71aa}
.hint{font-size:.8rem;color:rgba(255,255,255,.3);margin-top:1.5rem;
  text-align:center;line-height:1.7}
.install{font-size:.82rem;color:rgba(255,255,255,.35);
  border:1px solid rgba(255,255,255,.07);border-radius:10px;
  padding:.9rem;margin-top:.8rem;max-width:380px;text-align:center}
#ov{display:none;position:fixed;inset:0;background:#0d0d0d;
  z-index:999;align-items:center;justify-content:center}
#ov.show{display:flex}
.notif{width:min(500px,92vw);padding:2.5rem;
  background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);
  border-radius:20px;text-align:center}
.ni{font-size:2.8rem;margin-bottom:1rem}
.nt{font-size:1.6rem;font-weight:700;color:#e63946;margin-bottom:.8rem}
.nm{font-size:1rem;color:rgba(255,255,255,.7);line-height:1.7;
  margin-bottom:2rem;white-space:pre-wrap}
.btn{padding:.85rem 3rem;font-size:1rem;font-weight:700;
  background:#e63946;color:#fff;border:none;border-radius:12px;
  cursor:pointer;font-family:inherit}
</style></head><body>
<div class="icon">⚡</div>
<h1>ShockNet</h1>
<p class="sub">Agente activo · Esperando avisos</p>
<div class="card">
  <span class="dot"></span>
  <span style="font-size:1rem;font-weight:600">Escuchando...</span><br><br>
  <small style="color:rgba(255,255,255,.3)" id="last">Sin avisos recientes</small>
</div>
<div class="install">
  📲 <strong>Añadir a pantalla de inicio</strong><br>
  iOS: Compartir → "Añadir a pantalla inicio"<br>
  Android: Menú ⋮ → "Añadir a pantalla inicio"
</div>
<p class="hint">Se actualiza automáticamente cada 2 segundos.</p>
<div id="ov">
  <div class="notif">
    <div class="ni" id="ni">⚠️</div>
    <div class="nt" id="nt"></div>
    <div class="nm" id="nm"></div>
    <button class="btn" onclick="closeN()">Entendido</button>
  </div>
</div>
<script>
var lastId=null;
function poll(){fetch('/pwa_check').then(r=>r.json()).then(d=>{
  if(d.id&&d.id!==lastId){lastId=d.id;showN(d);}}).catch(()=>{});}
function showN(d){
  document.getElementById('ni').textContent=d.icon||'⚠️';
  document.getElementById('nt').textContent=d.title||'Aviso';
  document.getElementById('nm').textContent=d.message||'';
  document.getElementById('ov').classList.add('show');
  document.getElementById('last').textContent='Último: '+new Date().toLocaleTimeString();
  var el=document.documentElement;
  var req=el.requestFullscreen||el.webkitRequestFullscreen;
  if(req){try{req.call(el)}catch(e){}}
  if(Notification&&Notification.permission==='granted')
    new Notification('ShockNet: '+d.title,{body:d.message});
}
function closeN(){
  document.getElementById('ov').classList.remove('show');
  if(lastId)fetch('/read',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({id:lastId})});
}
if(Notification&&Notification.permission==='default')Notification.requestPermission();
setInterval(poll,2000);poll();
</script></body></html>"""

MANIFEST = ('{"name":"ShockNet Agent","short_name":"ShockNet","start_url":"/",'
            '"display":"fullscreen","background_color":"#0d0d0d","theme_color":"#e63946",'
            '"icons":[{"src":"/icon.png","sizes":"192x192","type":"image/png"}]}')


def check_auth():
    if not AUTH_TOKEN: return True
    return request.headers.get("Authorization","") == f"Bearer {AUTH_TOKEN}"

def get_local_ip():
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.connect(("8.8.8.8",80)); ip=s.getsockname()[0]; s.close(); return ip
    except: return "127.0.0.1"


@app.route("/")
def home(): return render_template_string(PWA_HOME)

@app.route("/manifest.json")
def manifest(): return app.response_class(MANIFEST, mimetype="application/json")

@app.route("/icon.png")
def icon():
    try:
        from PIL import Image, ImageDraw
        img=Image.new("RGB",(192,192),"#0d0d0d")
        d=ImageDraw.Draw(img)
        d.ellipse([16,16,176,176],fill="#e63946")
        d.rectangle([88,40,104,120],fill="white")
        d.rectangle([88,132,104,152],fill="white")
        buf=io.BytesIO(); img.save(buf,"PNG"); buf.seek(0)
        return send_file(buf, mimetype="image/png")
    except ImportError: return "",404

@app.route("/notify", methods=["POST"])
def notify():
    global pending, kiosk_stop
    if not check_auth():
        log.warning(f"Auth fallida desde {request.remote_addr}")
        return jsonify({"ok":False,"error":"Unauthorized"}),401
    raw  = request.get_json(force=True) or {}
    data = decrypt_payload(raw, AES_KEY) if AES_KEY else raw
    if not data: return jsonify({"ok":False,"error":"Descifrado fallido"}),400
    notif_id  = datetime.now().strftime("%Y%m%d%H%M%S%f")
    encrypted = bool(raw.get("_encrypted"))
    pending   = {
        "notif_id": notif_id, "title": data.get("title","Aviso"),
        "message": data.get("message",""), "theme": data.get("theme","oscuro"),
        "image_url": data.get("image_url",""),
        "encrypted": encrypted, "kiosk": KIOSK_MODE,
    }
    log.info(f"Aviso de {request.remote_addr} | '{pending['title']}' | "
             f"cifrado={'sí' if encrypted else 'no'} | kiosko={'sí' if KIOSK_MODE else 'no'}")
    threading.Thread(target=_open_browser, daemon=True).start()
    if SOUND_ENABLED:
        threading.Thread(target=_play_sound, daemon=True).start()
    if KIOSK_MODE:
        kiosk_stop.set(); kiosk_stop = threading.Event()
        from core.kiosk import start_kiosk
        threading.Thread(target=start_kiosk,
                         args=(AGENT_PORT, kiosk_stop), daemon=True).start()
    return jsonify({"ok":True,"id":notif_id}),200

@app.route("/webhook", methods=["POST"])
def webhook():
    if not check_auth(): return jsonify({"ok":False,"error":"Unauthorized"}),401
    raw     = request.get_json(force=True) or {}
    title   = raw.get("title") or raw.get("subject") or raw.get("ruleName") or "Alerta externa"
    message = raw.get("message") or raw.get("body") or "Sin detalles"
    if isinstance(message, list): message = "\n".join(str(m) for m in message)
    state   = raw.get("state","")
    theme   = "emergencia" if state in ("alerting","PROBLEM") else "alerta"
    global pending, kiosk_stop
    notif_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
    pending  = {"notif_id":notif_id,"title":str(title),"message":str(message),
                "theme":theme,"image_url":"","encrypted":False,"kiosk":KIOSK_MODE}
    log.info(f"Webhook de {request.remote_addr} | '{title}'")
    threading.Thread(target=_open_browser, daemon=True).start()
    if SOUND_ENABLED: threading.Thread(target=_play_sound, daemon=True).start()
    if KIOSK_MODE:
        kiosk_stop.set(); kiosk_stop = threading.Event()
        from core.kiosk import start_kiosk
        threading.Thread(target=start_kiosk,args=(AGENT_PORT,kiosk_stop),daemon=True).start()
    return jsonify({"ok":True,"id":notif_id}),200

@app.route("/webhook/test")
def webhook_test():
    return jsonify({"ok":True,
                    "endpoint":f"POST http://{get_local_ip()}:{AGENT_PORT}/webhook",
                    "example":{"title":"CPU alta","message":"CPU al 95%","state":"alerting"}}),200

@app.route("/screen")
def screen():
    if not pending: return "Sin notificación activa.",404
    t = THEMES.get(pending.get("theme","oscuro"),THEMES["oscuro"])
    return render_template_string(HTML, t=t, **pending)

@app.route("/preview/<theme_key>")
def preview(theme_key):
    t = THEMES.get(theme_key,THEMES["oscuro"])
    fake = {"notif_id":"preview","title":"Vista previa — "+t["name"],
            "message":"Así se verá el aviso en el dispositivo destino.",
            "image_url":"","encrypted":False,"kiosk":False}
    return render_template_string(HTML, t=t, **fake)

@app.route("/pwa_check")
def pwa_check():
    if not pending: return jsonify({"id":None}),200
    t = THEMES.get(pending.get("theme","oscuro"),THEMES["oscuro"])
    return jsonify({"id":pending["notif_id"],"title":pending["title"],
                    "message":pending["message"],"icon":t["icon"]}),200

@app.route("/read", methods=["POST"])
def read():
    data = request.get_json(force=True) or {}
    nid  = data.get("id","")
    ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    read_status[nid] = {"read_at":ts,"ip":request.remote_addr}
    log.info(f"Aviso {nid} leído a las {ts}")
    if KIOSK_MODE: kiosk_stop.set()
    return jsonify({"ok":True}),200

@app.route("/status/<notif_id>")
def status(notif_id):
    info = read_status.get(notif_id)
    if info: return jsonify({"ok":True,"read":True,**info}),200
    return jsonify({"ok":True,"read":False}),200

@app.route("/screenshot")
def screenshot():
    try:
        b = _take_screenshot()
        if b: return send_file(io.BytesIO(b), mimetype="image/jpeg")
        return "No disponible.",503
    except Exception as e: return str(e),500

@app.route("/ping")
def ping():
    return jsonify({"ok":True,"host":socket.gethostname(),"ip":get_local_ip()}),200

@app.route("/qr")
def qr_code():
    try:
        import qrcode
        img = qrcode.make(f"http://{get_local_ip()}:{AGENT_PORT}")
        buf = io.BytesIO(); img.save(buf,"PNG"); buf.seek(0)
        return send_file(buf, mimetype="image/png")
    except ImportError: return "pip install qrcode",500


def _take_screenshot():
    try:
        if platform.system()=="Windows":
            from PIL import ImageGrab; img=ImageGrab.grab()
        else:
            tmp="/tmp/shocknet_shot.png"
            env={**os.environ,"DISPLAY":os.environ.get("DISPLAY",":0")}
            for cmd in [["scrot",tmp],["gnome-screenshot","-f",tmp],
                        ["import","-window","root",tmp]]:
                try:
                    subprocess.run(cmd,env=env,timeout=5,capture_output=True)
                    if os.path.exists(tmp):
                        from PIL import Image; img=Image.open(tmp).copy(); break
                except: continue
            else: return None
        from PIL import Image
        img.thumbnail((1280,720),Image.LANCZOS)
        buf=io.BytesIO(); img.save(buf,"JPEG",quality=70); return buf.getvalue()
    except Exception as e: log.debug(f"Screenshot: {e}"); return None

def _open_browser():
    url=f"http://127.0.0.1:{AGENT_PORT}/screen"
    env={**os.environ,"DISPLAY":os.environ.get("DISPLAY",":0")}
    if platform.system()=="Linux":
        for br in ["firefox","chromium","chromium-browser","google-chrome","xdg-open"]:
            try:
                subprocess.Popen([br,url],env=env,stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL); return
            except FileNotFoundError: continue
    try: webbrowser.open(url,new=1)
    except: pass

def _play_sound():
    try:
        if platform.system()=="Windows":
            import winsound
            for _ in range(3): winsound.Beep(1000,200); import time; time.sleep(.1)
        else:
            for cmd in [["paplay","/usr/share/sounds/freedesktop/stereo/message.oga"],
                        ["aplay","/usr/share/sounds/alsa/Front_Center.wav"]]:
                try: subprocess.run(cmd,timeout=3,capture_output=True); return
                except: continue
    except: pass

def run_flask():
    import logging as lg; lg.getLogger("werkzeug").setLevel(lg.ERROR)
    app.run(host="0.0.0.0",port=AGENT_PORT,debug=False,use_reloader=False)

def run_tray(ip):
    try:
        import pystray
        from PIL import Image as PI, ImageDraw
        img=PI.new("RGB",(64,64),"#0d0d0d")
        d=ImageDraw.Draw(img)
        d.ellipse([6,6,58,58],fill="#e63946")
        d.rectangle([29,14,35,38],fill="white")
        d.rectangle([29,42,35,50],fill="white")
        menu=pystray.Menu(
            pystray.MenuItem(f"ShockNet v3  ({ip})",None,enabled=False),
            pystray.MenuItem("Abrir PWA",lambda i,it: webbrowser.open(f"http://127.0.0.1:{AGENT_PORT}")),
            pystray.MenuItem("Ver QR",  lambda i,it: webbrowser.open(f"http://127.0.0.1:{AGENT_PORT}/qr")),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Detener", lambda i,it: (log.info("Detenido."),i.stop(),os._exit(0))),
        )
        pystray.Icon("ShockNet",img,"ShockNet Agent",menu).run()
    except ImportError:
        log.info("pystray no disponible — modo terminal.")
        try:
            while True: import time; time.sleep(60)
        except KeyboardInterrupt: log.info("Detenido.")

if __name__ == "__main__":
    ip = get_local_ip()
    print("="*54)
    print(f"  ⚡ ShockNet Agent v3.0")
    print(f"  IP        : {ip}")
    print(f"  Puerto    : {AGENT_PORT}")
    print(f"  PWA móvil : http://{ip}:{AGENT_PORT}/")
    print(f"  Webhook   : POST http://{ip}:{AGENT_PORT}/webhook")
    print(f"  Cifrado   : {'AES-256 activado' if AES_KEY else 'desactivado'}")
    print(f"  Kiosko    : {'activado' if KIOSK_MODE else 'desactivado'}")
    print("="*54)
    threading.Thread(target=run_flask,daemon=True).start()
    run_tray(ip)
