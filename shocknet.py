#!/usr/bin/env python3
import tkinter as tk
from tkinter import messagebox, filedialog
import requests, threading, subprocess, socket
import json, os, sys, webbrowser, tempfile
from datetime import datetime

ROOT           = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_FILE = os.path.join(ROOT, "templates.json")
HISTORY_FILE   = os.path.join(ROOT, "history.json")
sys.path.insert(0, ROOT)
from core.config import (AGENT_PORT, TIMEOUT, SCAN_TIMEOUT, DEFAULT_TITLE,
                          DEFAULT_MESSAGE, THEMES, VERSION, AES_KEY)
from core.crypto_utils import encrypt_payload
from core.stats import load_history as _load_hist, compute_stats, export_csv, export_pdf

C = {
    "bg":        "#080808",   
    "sidebar":   "#0f0f0f",   
    "panel":     "#111111",   
    "card":      "#171717",  
    "card2":     "#1e1e1e",  
    "border":    "#252525",  
    "border2":   "#333333",  
    "accent":    "#e8192c",   
    "accent2":   "#ff3347",   
    "accent_dim":"#3d0810", 
    "text":      "#eeeeee",   
    "text2":     "#999999",   
    "text3":     "#555555",   
    "success":   "#00d46a",   
    "warning":   "#ffb020",  
    "error":     "#ff3347",  
    "info":      "#4f8ef7",  
    "mono":      "Consolas", 
}

FNT_MONO  = (C["mono"], 9)
FNT_MONO_B= (C["mono"], 9, "bold")
FNT_MONO_L= (C["mono"], 11)
FNT_MONO_XL=(C["mono"], 18, "bold")
FNT_UI    = ("Segoe UI", 9)
FNT_UI_B  = ("Segoe UI", 10, "bold")
FNT_UI_SM = ("Segoe UI", 8)

SIDEBAR_W  = 188
NAV_ITEMS  = [
    ("MSG",  "✉  MENSAJE",    "message"),
    ("SCAN", "◈  SCANNER",    "scanner"),
    ("THM",  "◉  TEMAS",      "themes"),
    ("TPL",  "▦  PLANTILLAS", "templates"),
    ("HIST", "≡  HISTORIAL",  "history"),
    ("STAT", "▲  STATS",      "stats"),
    ("CFG",  "⚙  CONFIG",     "config"),
]

class Entry(tk.Entry):
    """Campo de texto estilizado."""
    def __init__(self, master, var, width=40, show=None, **kw):
        super().__init__(master, textvariable=var, width=width,
                         bg=C["card2"], fg=C["text"], insertbackground=C["accent"],
                         relief="flat", font=FNT_MONO, show=show or "",
                         highlightthickness=1, highlightbackground=C["border2"],
                         highlightcolor=C["accent"], bd=5, **kw)


class Btn(tk.Button):
    """Botón primario rojo."""
    def __init__(self, master, text, cmd, padx=14, pady=7, **kw):
        super().__init__(master, text=text, command=cmd,
                         bg=C["accent"], fg="#ffffff", activebackground=C["accent2"],
                         activeforeground="#ffffff", relief="flat", cursor="hand2",
                         font=FNT_MONO_B, padx=padx, pady=pady, bd=0, **kw)
        self.bind("<Enter>", lambda e: self.config(bg=C["accent2"]))
        self.bind("<Leave>", lambda e: self.config(bg=C["accent"]))


class BtnGhost(tk.Button):
    """Botón secundario con borde."""
    def __init__(self, master, text, cmd, padx=12, pady=6, **kw):
        super().__init__(master, text=text, command=cmd,
                         bg=C["card"], fg=C["text2"], activebackground=C["card2"],
                         activeforeground=C["text"], relief="flat", cursor="hand2",
                         font=FNT_MONO, padx=padx, pady=pady, bd=0,
                         highlightthickness=1, highlightbackground=C["border2"],
                         highlightcolor=C["accent"], **kw)
        self.bind("<Enter>", lambda e: self.config(bg=C["card2"], fg=C["text"]))
        self.bind("<Leave>", lambda e: self.config(bg=C["card"], fg=C["text2"]))


class StatusBar(tk.Frame):
    """Barra de estado inferior fija."""
    def __init__(self, master):
        super().__init__(master, bg=C["sidebar"], height=28)
        self.pack(fill="x", side="bottom")
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x")
        inner = tk.Frame(self, bg=C["sidebar"]); inner.pack(fill="x", padx=14, pady=4)
        self._dot  = tk.Label(inner, text="●", font=("Segoe UI",9), bg=C["sidebar"], fg=C["text3"])
        self._dot.pack(side="left")
        self._msg  = tk.Label(inner, text="", font=FNT_MONO, bg=C["sidebar"], fg=C["text3"])
        self._msg.pack(side="left", padx=(6,0))
        self._right= tk.Label(inner, text=f"ShockNet v{VERSION}", font=FNT_MONO,
                               bg=C["sidebar"], fg=C["text3"])
        self._right.pack(side="right")

    def set(self, msg, color=None):
        c = color or C["text3"]
        self._msg.config(text=msg, fg=c)
        self._dot.config(fg=c)

class ShockNet:
    def __init__(self, root):
        self.root   = root
        self.root.title(f"ShockNet — Launcher")
        self.root.configure(bg=C["bg"])
        self.root.resizable(True, True)
        self.root.minsize(860, 580)

        # Variables de estado
        self.manual_ip     = tk.StringVar(value="192.168.1.")
        self.theme_var     = tk.StringVar(value="oscuro")
        self.auth_token    = tk.StringVar(value="")
        self.schedule_var  = tk.StringVar(value="")
        self.image_url_var = tk.StringVar(value="")
        self._multi_sel    = {}
        self._screen_ref   = None

        self._load_history()
        self._load_templates()
        self._build()
        self._center(1000, 660)

        # Atajos de teclado
        self.root.bind("<Control-Return>", lambda e: self._send())
        self.root.bind("<Control-s>",      lambda e: self._save_current_as_template())
        self.root.bind("<F5>",             lambda e: self._scanner_and_scan())
        for i, (_, _, key) in enumerate(NAV_ITEMS, 1):
            self.root.bind(f"<Control-{i}>", lambda e, k=key: self._switch(k))

    def _load_history(self):
        try:
            with open(HISTORY_FILE,"r",encoding="utf-8") as f: self.history = json.load(f)
        except: self.history = []

    def _save_history(self, e):
        self.history.insert(0, e); self.history = self.history[:100]
        try:
            with open(HISTORY_FILE,"w",encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except: pass

    def _load_templates(self):
        try:
            with open(TEMPLATES_FILE,"r",encoding="utf-8") as f: self.templates = json.load(f)
        except: self.templates = []

    def _save_templates_file(self):
        try:
            with open(TEMPLATES_FILE,"w",encoding="utf-8") as f:
                json.dump(self.templates, f, ensure_ascii=False, indent=2)
        except: pass

    def _build(self):
        # Sidebar izquierdo
        self._sidebar = tk.Frame(self.root, bg=C["sidebar"], width=SIDEBAR_W)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        logo_f = tk.Frame(self._sidebar, bg=C["sidebar"])
        logo_f.pack(fill="x", pady=(0,0))
        tk.Frame(logo_f, bg=C["accent"], height=3).pack(fill="x")
        linner = tk.Frame(logo_f, bg=C["sidebar"]); linner.pack(fill="x", padx=16, pady=(16,12))
        tk.Label(linner, text="SHOCK", font=(C["mono"],18,"bold"),
                 bg=C["sidebar"], fg=C["accent"]).pack(anchor="w")
        tk.Label(linner, text="NET", font=(C["mono"],18,"bold"),
                 bg=C["sidebar"], fg=C["text"]).pack(anchor="w")
        tk.Label(linner, text=f"v{VERSION}  //  LAUNCHER",
                 font=FNT_MONO, bg=C["sidebar"], fg=C["text3"]).pack(anchor="w", pady=(2,0))

        tk.Frame(self._sidebar, bg=C["border"], height=1).pack(fill="x", padx=0, pady=(0,8))

        # Navegación
        self._nav_btns = {}
        for code, label, key in NAV_ITEMS:
            f = tk.Frame(self._sidebar, bg=C["sidebar"]); f.pack(fill="x")
            btn = tk.Button(f, text=label, font=FNT_MONO_B,
                            bg=C["sidebar"], fg=C["text3"],
                            activebackground=C["card"], activeforeground=C["text"],
                            relief="flat", cursor="hand2", anchor="w",
                            padx=16, pady=9, bd=0,
                            command=lambda k=key: self._switch(k))
            btn.pack(fill="x")
            ind = tk.Frame(f, bg=C["sidebar"], width=3)
            ind.place(x=0, y=0, height=36)
            self._nav_btns[key] = (btn, ind, f)

        tk.Frame(self._sidebar, bg=C["sidebar"]).pack(fill="both", expand=True)
        conn_f = tk.Frame(self._sidebar, bg=C["sidebar"])
        conn_f.pack(fill="x", pady=(0,4))
        tk.Frame(conn_f, bg=C["border"], height=1).pack(fill="x")
        ci = tk.Frame(conn_f, bg=C["sidebar"]); ci.pack(fill="x", padx=14, pady=10)
        self._conn_dot = tk.Label(ci, text="●", font=("Segoe UI",10),
                                   bg=C["sidebar"], fg=C["text3"])
        self._conn_dot.pack(side="left")
        self._conn_lbl = tk.Label(ci, text="Sin conexión", font=FNT_MONO,
                                   bg=C["sidebar"], fg=C["text3"], wraplength=130, justify="left")
        self._conn_lbl.pack(side="left", padx=(6,0))

        tk.Frame(self.root, bg=C["border"], width=1).pack(side="left", fill="y")

        #Área principal
        self._main = tk.Frame(self.root, bg=C["panel"])
        self._main.pack(side="left", fill="both", expand=True)

        self._hdr = tk.Frame(self._main, bg=C["card"], height=48)
        self._hdr.pack(fill="x")
        self._hdr.pack_propagate(False)
        self._hdr_title = tk.Label(self._hdr, text="", font=FNT_MONO_L,
                                    bg=C["card"], fg=C["text"])
        self._hdr_title.pack(side="left", padx=20, pady=14)
        tk.Frame(self._main, bg=C["border"], height=1).pack(fill="x")

        # scroll 
        scroll_container = tk.Frame(self._main, bg=C["panel"])
        scroll_container.pack(side="left", fill="both", expand=True)
        scroll_container.grid_rowconfigure(0, weight=1)
        scroll_container.grid_columnconfigure(0, weight=1)
        scroll_container.grid_columnconfigure(1, weight=0)

        self._canvas = tk.Canvas(scroll_container, bg=C["panel"],
                                 highlightthickness=0)
        self._sb = tk.Scrollbar(scroll_container, orient="vertical",
                                bg=C["card"], troughcolor=C["bg"],
                                command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._sb.set)
        self._canvas.grid(row=0, column=0, sticky="nsew")
        self._sb.grid(row=0, column=1, sticky="ns")
        self.root.bind_all("<MouseWheel>",
                           lambda e: self._canvas.yview_scroll(-1*(e.delta//120),"units"))
        self.root.bind_all("<Button-4>", lambda e: self._canvas.yview_scroll(-1,"units"))
        self.root.bind_all("<Button-5>", lambda e: self._canvas.yview_scroll(1,"units"))

        # Frames de cada sección
        self._pages = {}
        for _, _, key in NAV_ITEMS:
            f = tk.Frame(self._canvas, bg=C["panel"])
            self._pages[key] = f

        self._page_id = self._canvas.create_window(
            (0,0), window=self._pages["message"], anchor="nw")
        for f in self._pages.values():
            f.bind("<Configure>", lambda e:
                   self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e:
                          self._canvas.itemconfig(self._page_id, width=e.width))

        self._statusbar = StatusBar(self.root)

        self._build_message(self._pages["message"])
        self._build_scanner(self._pages["scanner"])
        self._build_themes(self._pages["themes"])
        self._build_templates(self._pages["templates"])
        self._build_history(self._pages["history"])
        self._build_stats(self._pages["stats"])
        self._build_config(self._pages["config"])
        self._switch("message")

    def _switch(self, key):
        self._canvas.itemconfig(self._page_id, window=self._pages[key])
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        self._canvas.yview_moveto(0)
        for k, (btn, ind, frame) in self._nav_btns.items():
            if k == key:
                btn.config(fg=C["text"], bg=C["card"])
                ind.config(bg=C["accent"])
            else:
                btn.config(fg=C["text3"], bg=C["sidebar"])
                ind.config(bg=C["sidebar"])
        labels = {k: l for _, l, k in NAV_ITEMS}
        self._hdr_title.config(text=labels.get(key,""))
        if key == "history":   self._refresh_history()
        if key == "stats":     self._refresh_stats()
        if key == "templates": self._refresh_templates()

    def _section_title(self, parent, text, pady=(22,8)):
        f = tk.Frame(parent, bg=C["panel"]); f.pack(fill="x", padx=22, pady=pady)
        tk.Label(f, text=f"// {text}", font=FNT_MONO_B,
                 bg=C["panel"], fg=C["accent"]).pack(side="left")
        tk.Frame(f, bg=C["border"], height=1).pack(side="left", fill="x", expand=True, padx=(12,0))

    def _card_frame(self, parent, pady=(0,10)):
        c = tk.Frame(parent, bg=C["card"],
                     highlightthickness=1, highlightbackground=C["border"])
        c.pack(fill="x", padx=22, pady=pady)
        return c

    def _lbl_entry(self, parent, label, var, hint=None, show=None):
        f = tk.Frame(parent, bg=C["panel"]); f.pack(fill="x", padx=22, pady=(10,0))
        tk.Label(f, text=label, font=FNT_MONO, bg=C["panel"], fg=C["text2"]).pack(anchor="w")
        Entry(f, var, width=65, show=show).pack(fill="x", pady=(3,0))
        if hint:
            tk.Label(f, text=hint, font=FNT_UI_SM, bg=C["panel"], fg=C["text3"]).pack(anchor="w",pady=(2,0))

    def _lbl_text(self, parent, label, default, attr, height=4):
        f = tk.Frame(parent, bg=C["panel"]); f.pack(fill="x", padx=22, pady=(10,0))
        tk.Label(f, text=label, font=FNT_MONO, bg=C["panel"], fg=C["text2"]).pack(anchor="w")
        txt = tk.Text(f, height=height, bg=C["card2"], fg=C["text"],
                      insertbackground=C["accent"], relief="flat", font=FNT_MONO,
                      wrap="word", highlightthickness=1, highlightbackground=C["border2"],
                      highlightcolor=C["accent"])
        txt.insert("1.0", default); txt.pack(fill="x", pady=(3,0))
        setattr(self, attr, txt)

    def _status(self, msg, color=None):
        self._statusbar.set(msg, color)

    def _center(self, w, h):
        self.root.update_idletasks()
        sw=self.root.winfo_screenwidth(); sh=self.root.winfo_screenheight()
        h=min(h,sh-60); self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build_message(self, p):
        # Destino
        self._section_title(p, "DESTINO", pady=(22,6))
        dest = self._card_frame(p)
        di = tk.Frame(dest, bg=C["card"]); di.pack(fill="x", padx=14, pady=12)

        # IP 
        tk.Label(di, text="DIRECCIÓN IP", font=FNT_MONO, bg=C["card"], fg=C["text3"]).pack(anchor="w")
        row_ip = tk.Frame(di, bg=C["card"]); row_ip.pack(fill="x", pady=(4,0))
        Entry(row_ip, self.manual_ip, width=22).pack(side="left")
        BtnGhost(row_ip, "PING", self._ping, padx=12, pady=5).pack(side="left", padx=(8,0))
        BtnGhost(row_ip, "◈ SCAN", lambda: self._switch("scanner"), padx=10, pady=5).pack(side="left", padx=(6,0))

        self._conn_status = tk.Label(di, text="", font=FNT_MONO, bg=C["card"], fg=C["text3"])
        self._conn_status.pack(anchor="w", pady=(6,0))

        # Tema 
        self._section_title(p, "TEMA VISUAL")
        theme_card = self._card_frame(p)
        ti = tk.Frame(theme_card, bg=C["card"]); ti.pack(fill="x", padx=14, pady=12)
        self._theme_btns = {}
        for col, (key, t) in enumerate(THEMES.items()):
            btn = tk.Button(ti, text=t["name"], font=FNT_MONO,
                            bg=C["card2"], fg=C["text2"], relief="flat", cursor="hand2",
                            padx=10, pady=5, activebackground=C["border2"],
                            activeforeground=C["text"],
                            command=lambda k=key: self._select_theme(k))
            btn.grid(row=0, column=col, padx=(0,6))
            self._theme_btns[key] = btn
        self._select_theme("oscuro")

        # Mensaje 
        self._section_title(p, "CONTENIDO")

        # Título
        f_t = tk.Frame(p, bg=C["panel"]); f_t.pack(fill="x", padx=22, pady=(10,0))
        tk.Label(f_t, text="TÍTULO", font=FNT_MONO, bg=C["panel"], fg=C["text2"]).pack(anchor="w")
        self.title_var = tk.StringVar(value=DEFAULT_TITLE)
        Entry(f_t, self.title_var, width=65).pack(fill="x", pady=(3,0))

        self._lbl_text(p, "MENSAJE", DEFAULT_MESSAGE, "msg_text", height=5)

        f_img = tk.Frame(p, bg=C["panel"]); f_img.pack(fill="x", padx=22, pady=(10,0))
        tk.Label(f_img, text="URL IMAGEN  (opcional)", font=FNT_MONO,
                 bg=C["panel"], fg=C["text3"]).pack(anchor="w")
        Entry(f_img, self.image_url_var, width=65).pack(fill="x", pady=(3,0))

        # Programar
        self._section_title(p, "PROGRAMAR ENVÍO  (opcional)")
        sch_card = self._card_frame(p)
        si = tk.Frame(sch_card, bg=C["card"]); si.pack(fill="x", padx=14, pady=12)
        tk.Label(si, text="HORA  HH:MM  —  vacío para enviar ahora",
                 font=FNT_MONO, bg=C["card"], fg=C["text3"]).pack(anchor="w")
        srow = tk.Frame(si, bg=C["card"]); srow.pack(fill="x", pady=(5,0))
        Entry(srow, self.schedule_var, width=10).pack(side="left")
        self._sched_lbl = tk.Label(srow, text="", font=FNT_MONO, bg=C["card"], fg=C["warning"])
        self._sched_lbl.pack(side="left", padx=(12,0))

        tk.Frame(p, bg=C["border"], height=1).pack(fill="x", padx=22, pady=(20,0))
        act = tk.Frame(p, bg=C["panel"]); act.pack(fill="x", padx=22, pady=(14,0))

        self._send_btn = Btn(act, "  ⚡  ENVIAR AVISO  ", self._send, padx=28, pady=11)
        self._send_btn.pack(side="left")

        BtnGhost(act, "  VER PANTALLA", self._open_screen,
                 padx=14, pady=10).pack(side="left", padx=(10,0))

        self._act_lbl = tk.Label(p, text="", font=FNT_MONO, bg=C["panel"], fg=C["text3"])
        self._act_lbl.pack(anchor="w", padx=22, pady=(10,24))

        # Hints de atajos
        hints = tk.Frame(p, bg=C["panel"]); hints.pack(fill="x", padx=22, pady=(0,24))
        for txt in ["Ctrl+Enter → Enviar", "Ctrl+S → Guardar plantilla", "F5 → Escanear red"]:
            tk.Label(hints, text=f"  {txt}", font=FNT_MONO, bg=C["panel"], fg=C["text3"]).pack(side="left", padx=(0,18))
          
    def _build_scanner(self, p):
        self._section_title(p, "ESCÁNER DE RED", pady=(22,6))
        tk.Label(p, text="  Busca agentes ShockNet activos en la red local.",
                 font=FNT_MONO, bg=C["panel"], fg=C["text3"]).pack(anchor="w", padx=22)

        top = tk.Frame(p, bg=C["panel"]); top.pack(fill="x", padx=22, pady=(12,10))
        self._scan_btn = Btn(top, "◈  ESCANEAR AHORA", self._scan, padx=18, pady=9)
        self._scan_btn.pack(side="left")
        self._scan_lbl = tk.Label(top, text="", font=FNT_MONO, bg=C["panel"], fg=C["text3"])
        self._scan_lbl.pack(side="left", padx=(14,0))

        self._agent_list = tk.Frame(p, bg=C["card"],
                                     highlightthickness=1, highlightbackground=C["border"])
        self._agent_list.pack(fill="x", padx=22, pady=(0,10))
        self._scan_placeholder()

        self._multi_btn = BtnGhost(p, "   ENVIAR A SELECCIONADOS", self._multi_send,
                                    padx=16, pady=9, state="disabled")
        self._multi_btn.pack(anchor="w", padx=22, pady=(0,24))

    def _scan_placeholder(self, msg="Pulsa ESCANEAR para buscar agentes"):
        for w in self._agent_list.winfo_children(): w.destroy()
        tk.Label(self._agent_list, text=f"  //  {msg}",
                 font=FNT_MONO, bg=C["card"], fg=C["text3"], pady=18).pack()

    def _scanner_and_scan(self):
        """F5: va al scanner y lanza el escaneo automáticamente."""
        self._switch("scanner")
        self.root.after(100, self._scan)

    def _scan(self):
        self._scan_btn.config(state="disabled")
        self._scan_lbl.config(text="buscando...", fg=C["warning"])
        self._multi_sel.clear()
        self._multi_btn.config(state="disabled", text="   ENVIAR A SELECCIONADOS")
        self._scan_placeholder("escaneando la red...")
        threading.Thread(target=self._scan_thread, daemon=True).start()

    def _scan_thread(self):
        import concurrent.futures
        try:
            s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            s.connect(("8.8.8.8",80)); lip=s.getsockname()[0]; s.close()
        except: lip="192.168.1.1"
        base=[f"{'.'.join(lip.split('.')[:3])}.{i}" for i in range(1,255)]
        found=[]
        def chk(ip):
            try:
                r=requests.get(f"http://{ip}:{AGENT_PORT}/ping",timeout=SCAN_TIMEOUT)
                if r.status_code==200:
                    d=r.json(); return (ip,d.get("host","?"),d.get("ip",ip))
            except: pass
            return None
        with concurrent.futures.ThreadPoolExecutor(max_workers=60) as ex:
            for i,res in enumerate(concurrent.futures.as_completed({ex.submit(chk,h):h for h in base})):
                r=res.result()
                if r: found.append(r)
                if i%30==0:
                    self.root.after(0,lambda i=i:self._scan_lbl.config(
                        text=f"escaneando {i}/254...",fg=C["warning"]))
        self.root.after(0,lambda:self._scan_done(found))

    def _scan_done(self, found):
        self._scan_btn.config(state="normal")
        for w in self._agent_list.winfo_children(): w.destroy()
        if not found:
            self._scan_lbl.config(text="sin agentes encontrados",fg=C["text3"])
            self._scan_placeholder("sin agentes ShockNet en la red")
            self._multi_btn.config(state="disabled"); return
        self._scan_lbl.config(text=f"{len(found)} agente(s) activo(s)",fg=C["success"])
        self._multi_sel.clear()
        for ip,host,real_ip in found:
            var=tk.BooleanVar(value=False); self._multi_sel[ip]=var
            row=tk.Frame(self._agent_list,bg=C["card"]); row.pack(fill="x")
            tk.Frame(row,bg=C["border"],height=1).pack(fill="x")
            inner=tk.Frame(row,bg=C["card"]); inner.pack(fill="x",padx=12,pady=9)
            tk.Checkbutton(inner,variable=var,bg=C["card"],selectcolor=C["card2"],
                           activebackground=C["card"],command=self._upd_multi).pack(side="left")
            tk.Label(inner,text="●",font=("Segoe UI",9),bg=C["card"],fg=C["success"]).pack(side="left",padx=(4,0))
            tk.Label(inner,text=f"  {host:<20} {real_ip}",font=FNT_MONO_B,
                     bg=C["card"],fg=C["text"]).pack(side="left")
            for txt,cmd in [
                ("PANTALLA", lambda i=ip: self._open_screen(i)),
                ("USAR IP",  lambda i=ip: self._use_ip(i)),
                ("ENVIAR",   lambda i=ip: self._send_to(i)),
            ]:
                BtnGhost(inner,txt,cmd,padx=8,pady=3).pack(side="right",padx=(4,0))
        self._multi_btn.config(state="normal")

    def _upd_multi(self):
        n=sum(v.get() for v in self._multi_sel.values())
        self._multi_btn.config(state="normal" if n else "disabled",
                               text=f"📤  ENVIAR A {n} SELECCIONADOS")

    def _use_ip(self,ip): self.manual_ip.set(ip); self._switch("message")
    def _send_to(self,ip): self.manual_ip.set(ip); self._switch("message"); self.root.after(100,self._send)

    def _multi_send(self):
        ips=[ip for ip,v in self._multi_sel.items() if v.get()]
        if not ips: return
        payload=self._build_payload()
        if payload is None: return
        self._multi_btn.config(state="disabled")
        threading.Thread(target=self._multi_thread,args=(ips,payload),daemon=True).start()

    def _multi_thread(self,ips,payload):
        ok=0
        for ip in ips:
            try:
                r=requests.post(f"http://{ip}:{AGENT_PORT}/notify",
                                json=payload,headers=self._auth_headers(),timeout=TIMEOUT)
                if r.status_code==200:
                    ok+=1
                    self._save_history({"ts":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "ip":ip,"title":payload.get("title",""),
                                        "theme":payload.get("theme",""),
                                        "status":"enviado","notif_id":r.json().get("id","")})
            except: pass
        self.root.after(0,lambda:self._scan_lbl.config(
            text=f"entregado a {ok}/{len(ips)}",fg=C["success"] if ok else C["error"]))
        self.root.after(0,lambda:self._multi_btn.config(state="normal"))
        if ok: self._notify_desktop(payload.get("title","Aviso"),f"Entregado a {ok}/{len(ips)} dispositivos")

    def _build_themes(self, p):
        self._section_title(p, "TEMAS VISUALES", pady=(22,6))
        tk.Label(p, text="  Vista previa abre el tema en el navegador sin necesitar agente.",
                 font=FNT_MONO, bg=C["panel"], fg=C["text3"]).pack(anchor="w", padx=22)
        self._theme_rows = {}
        for key, t in THEMES.items():
            card = tk.Frame(p, bg=C["card"], highlightthickness=1, highlightbackground=C["border"])
            card.pack(fill="x", padx=22, pady=(10,0))
            inner = tk.Frame(card, bg=C["card"]); inner.pack(fill="x", padx=14, pady=12)
            # Swatch de color
            acc = t["accent"] if t["accent"].startswith("#") else "#e63946"
            sw = tk.Frame(inner, bg=acc, width=16, height=16); sw.pack(side="left")
            sw.pack_propagate(False)
            tk.Label(inner, text=f"  {t['name']}", font=FNT_MONO_B,
                     bg=C["card"], fg=C["text"]).pack(side="left")
            Btn(inner, "SELECCIONAR", lambda k=key: self._sel_theme_tab(k),
                padx=10, pady=4).pack(side="right", padx=(6,0))
            BtnGhost(inner, "VISTA PREVIA", lambda k=key: self._local_preview(k),
                     padx=10, pady=4).pack(side="right")
            self._theme_rows[key] = card
        self._theme_status = tk.Label(p, text="", font=FNT_MONO,
                                       bg=C["panel"], fg=C["text3"])
        self._theme_status.pack(anchor="w", padx=22, pady=(12,24))

    def _local_preview(self, key):
        t = THEMES[key]
        html = self._preview_html(t)
        tmp = tempfile.NamedTemporaryFile(delete=False,suffix=".html",mode="w",encoding="utf-8")
        tmp.write(html); tmp.close()
        import platform
        opened = False
        if platform.system()=="Linux":
            for br in ["firefox","chromium-browser","google-chrome","xdg-open"]:
                try: subprocess.Popen([br,f"file://{tmp.name}"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); opened=True; break
                except FileNotFoundError: continue
        if not opened:
            try: webbrowser.open(f"file://{tmp.name}"); opened=True
            except: pass
        if not opened:
            import shutil
            dl=os.path.join(os.path.expanduser("~"),"Downloads",f"shocknet_prev_{key}.html")
            shutil.copy(tmp.name,dl)
            self._theme_status.config(text=f"  //  guardado en Descargas: shocknet_prev_{key}.html",fg=C["warning"])
            return
        self._theme_status.config(text=f"  //  vista previa '{t['name']}' abierta",fg=C["success"])

    def _preview_html(self, t):
        acc=t["accent"]
        return f"""<!DOCTYPE html><html lang="es"><head>
<meta charset="UTF-8"><title>Vista previa — {t['name']}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap');
*{{box-sizing:border-box;margin:0;padding:0}}
body{{min-height:100vh;background:{t['bg']};color:{t['text']};font-family:'Space Grotesk',sans-serif;
  display:flex;align-items:center;justify-content:center;overflow:hidden;}}
body::before{{content:'';position:fixed;inset:0;
  background:radial-gradient(ellipse at 50% -10%,{acc}33 0%,transparent 55%),
             radial-gradient(ellipse at 80% 110%,{acc}18 0%,transparent 45%);
  pointer-events:none;}}
body::after{{content:'';position:fixed;inset:0;
  background:repeating-linear-gradient(0deg,transparent,transparent 59px,{acc}07 60px),
             repeating-linear-gradient(90deg,transparent,transparent 59px,{acc}04 60px);
  pointer-events:none;}}
.badge{{position:fixed;top:14px;left:14px;font-size:.7rem;padding:5px 14px;
  background:{acc}18;border:1px solid {acc}44;color:{acc};border-radius:20px;
  font-family:monospace;letter-spacing:.06em;z-index:10;}}
.card{{position:relative;width:min(560px,94vw);padding:3rem;
  background:{t['card_bg']};border:1px solid {t['card_border']};
  border-radius:24px;text-align:center;
  backdrop-filter:blur(20px) saturate(180%);
  box-shadow:0 0 60px {acc}18,0 20px 60px rgba(0,0,0,.5);
  animation:rise .5s cubic-bezier(.22,1,.36,1) both;}}
@keyframes rise{{from{{opacity:0;transform:translateY(28px) scale(.96)}}to{{opacity:1;transform:translateY(0) scale(1)}}}}
.brand{{font-size:.75rem;text-transform:uppercase;letter-spacing:.18em;color:{t['muted']};margin-bottom:1.5rem;}}
.icon{{font-size:3.2rem;margin-bottom:1rem;display:block;}}
h1{{font-size:2rem;font-weight:700;color:{acc};margin-bottom:.8rem;text-shadow:0 0 30px {acc}55;}}
.msg{{font-size:1.05rem;color:{t['muted']};line-height:1.7;margin-bottom:2rem;}}
.div{{width:40px;height:2px;background:{acc};margin:0 auto 1.8rem;border-radius:2px;box-shadow:0 0 10px {acc};}}
.btn{{padding:.85rem 3rem;font-size:1rem;font-weight:700;background:{acc};
  color:{t['btn_fg']};border:none;border-radius:12px;cursor:pointer;font-family:inherit;
  box-shadow:0 0 20px {acc}55;transition:box-shadow .2s;}}
.btn:hover{{box-shadow:0 0 35px {acc}88;}}
</style></head><body>
<div class="badge">ShockNet · Vista previa — {t['name']}</div>
<div class="card">
  <p class="brand">ShockNet · Network Alert System</p>
  <span class="icon">{t['icon']}</span>
  <h1>Título del aviso</h1>
  <p class="msg">Aquí aparecerá el mensaje que escribas en el launcher.<br>Puede tener varias líneas.</p>
  <div class="div"></div>
  <button class="btn">Entendido</button>
</div></body></html>"""

    def _sel_theme_tab(self,key):
        self._select_theme(key)
        self._theme_status.config(text=f"  //  tema '{THEMES[key]['name']}' seleccionado",fg=C["success"])

    def _select_theme(self,key):
        self.theme_var.set(key)
        for k,b in self._theme_btns.items():
            b.config(bg=C["accent"] if k==key else C["card2"],
                     fg="#ffffff" if k==key else C["text2"])
        if hasattr(self,"_theme_rows"):
            for k,c in self._theme_rows.items():
                c.config(highlightbackground=C["accent"] if k==key else C["border"])

    def _build_templates(self, p):
        self._section_title(p, "PLANTILLAS DE MENSAJES", pady=(22,6))
        top = tk.Frame(p, bg=C["panel"]); top.pack(fill="x", padx=22, pady=(0,10))
        tk.Label(top, text="  Mensajes guardados para reutilizar con un clic.",
                 font=FNT_MONO, bg=C["panel"], fg=C["text3"]).pack(side="left")
        Btn(top, "＋  GUARDAR MENSAJE ACTUAL", self._save_current_as_template,
            padx=12, pady=5).pack(side="right")
        self._tpl_card = tk.Frame(p, bg=C["card"],
                                   highlightthickness=1, highlightbackground=C["border"])
        self._tpl_card.pack(fill="x", padx=22, pady=(0,24))
        self._tpl_list_frame = tk.Frame(self._tpl_card, bg=C["card"])
        self._tpl_list_frame.pack(fill="x")
        self._refresh_templates()

    def _refresh_templates(self):
        for w in self._tpl_list_frame.winfo_children(): w.destroy()
        if not self.templates:
            tk.Label(self._tpl_list_frame,
                     text="  //  Sin plantillas. Ve a Mensaje y guarda uno.",
                     font=FNT_MONO, bg=C["card"], fg=C["text3"], pady=18).pack(anchor="w")
            return
        for i, t in enumerate(self.templates):
            row = tk.Frame(self._tpl_list_frame, bg=C["card"]); row.pack(fill="x")
            tk.Frame(row, bg=C["border"], height=1).pack(fill="x")
            inner = tk.Frame(row, bg=C["card"]); inner.pack(fill="x", padx=14, pady=9)
            info = tk.Frame(inner, bg=C["card"]); info.pack(side="left", fill="x", expand=True)
            tk.Label(info, text=t.get("name","?"), font=FNT_MONO_B,
                     bg=C["card"], fg=C["text"]).pack(anchor="w")
            meta = f"{t.get('title','')[:45]}  ·  {t.get('saved_at','')}"
            tk.Label(info, text=meta, font=FNT_MONO, bg=C["card"], fg=C["text3"]).pack(anchor="w")
            BtnGhost(inner, "CARGAR", lambda i=i: self._load_template(i),
                     padx=10, pady=3).pack(side="right", padx=(6,0))
            tk.Button(inner, text="✕", font=FNT_MONO, bg=C["card"], fg=C["text3"],
                      relief="flat", cursor="hand2", padx=6, pady=3,
                      activebackground=C["error"], activeforeground="white",
                      command=lambda i=i: self._del_template(i)).pack(side="right")

    def _save_current_as_template(self):
        title   = self.title_var.get().strip()
        message = self.msg_text.get("1.0","end").strip() if hasattr(self,"msg_text") else ""
        if not title and not message:
            messagebox.showwarning("Campos vacíos","Escribe título y mensaje primero."); return
        win = tk.Toplevel(self.root); win.title("Guardar plantilla")
        win.configure(bg=C["bg"]); win.resizable(False,False); win.grab_set()
        tk.Frame(win, bg=C["accent"], height=3).pack(fill="x")
        f = tk.Frame(win, bg=C["bg"]); f.pack(fill="x", padx=22, pady=(18,0))
        tk.Label(f, text="NOMBRE DE LA PLANTILLA", font=FNT_MONO_B,
                 bg=C["bg"], fg=C["text"]).pack(anchor="w")
        name_var = tk.StringVar(value=title[:40] if title else "Nueva plantilla")
        e = Entry(f, name_var, width=38); e.pack(fill="x", pady=(6,0))
        e.focus_set(); e.select_range(0,"end")
        br = tk.Frame(win, bg=C["bg"]); br.pack(fill="x", padx=22, pady=(14,20))
        def confirm():
            name=name_var.get().strip()
            if not name: messagebox.showwarning("Sin nombre","Escribe un nombre.",parent=win); return
            self.templates=[t for t in self.templates if t.get("name")!=name]
            self.templates.insert(0,{"name":name,"title":title,"message":message,
                                      "theme":self.theme_var.get(),
                                      "image_url":self.image_url_var.get().strip(),
                                      "saved_at":datetime.now().strftime("%Y-%m-%d %H:%M")})
            self._save_templates_file(); win.destroy()
            self._refresh_templates()
            self._status(f"  plantilla '{name}' guardada", C["success"])
        Btn(br,"GUARDAR",confirm,padx=14,pady=7).pack(side="right")
        BtnGhost(br,"CANCELAR",win.destroy,padx=12,pady=6).pack(side="right",padx=(0,8))
        win.bind("<Return>",lambda e:confirm()); win.bind("<Escape>",lambda e:win.destroy())
        win.update_idletasks()
        rx,ry=self.root.winfo_x(),self.root.winfo_y()
        rw,rh=self.root.winfo_width(),self.root.winfo_height()
        pw,ph=win.winfo_width(),win.winfo_height()
        win.geometry(f"+{rx+(rw-pw)//2}+{ry+(rh-ph)//2}")

    def _load_template(self,i):
        t=self.templates[i]
        self.title_var.set(t.get("title",""))
        if hasattr(self,"msg_text"):
            self.msg_text.delete("1.0","end"); self.msg_text.insert("1.0",t.get("message",""))
        if t.get("theme"): self._select_theme(t["theme"])
        if t.get("image_url"): self.image_url_var.set(t["image_url"])
        self._switch("message")
        self._status(f"  plantilla '{t['name']}' cargada",C["success"])

    def _del_template(self,i):
        name=self.templates[i].get("name","?")
        if messagebox.askyesno("Eliminar",f"¿Eliminar la plantilla '{name}'?"):
            self.templates.pop(i); self._save_templates_file(); self._refresh_templates()
          
    def _build_history(self, p):
        self._section_title(p, "HISTORIAL DE AVISOS", pady=(22,6))
        top=tk.Frame(p,bg=C["panel"]); top.pack(fill="x",padx=22,pady=(0,10))
        BtnGhost(top,"ACTUALIZAR",self._refresh_history,padx=10,pady=6).pack(side="left")
        BtnGhost(top,"LIMPIAR",self._clear_history,padx=10,pady=6).pack(side="left",padx=(8,0))
        self._hist_frame=tk.Frame(p,bg=C["panel"]); self._hist_frame.pack(fill="x",padx=22,pady=(0,24))
        self._refresh_history()

    def _refresh_history(self):
        for w in self._hist_frame.winfo_children(): w.destroy()
        self._load_history()
        if not self.history:
            tk.Label(self._hist_frame,text="  //  Sin historial todavía.",
                     font=FNT_MONO,bg=C["panel"],fg=C["text3"],pady=18).pack(anchor="w"); return
        for e in self.history[:60]:
            card=tk.Frame(self._hist_frame,bg=C["card"],
                          highlightthickness=1,highlightbackground=C["border"])
            card.pack(fill="x",pady=(0,5))
            inner=tk.Frame(card,bg=C["card"]); inner.pack(fill="x",padx=12,pady=8)
            ok=e.get("status")=="enviado"
            tk.Label(inner,text="✓" if ok else "✗",font=FNT_MONO_B,bg=C["card"],
                     fg=C["success"] if ok else C["error"]).pack(side="left")
            info=tk.Frame(inner,bg=C["card"]); info.pack(side="left",padx=(10,0))
            tk.Label(info,text=e.get("title","?"),font=FNT_MONO_B,bg=C["card"],fg=C["text"]).pack(anchor="w")
            tk.Label(info,text=f"{e.get('ts','')}  {e.get('ip','')}  {e.get('theme','')}",
                     font=FNT_MONO,bg=C["card"],fg=C["text3"]).pack(anchor="w")
            nid=e.get("notif_id",""); ip=e.get("ip","")
            if nid and ip:
                BtnGhost(inner,"¿LEÍDO?",lambda i=ip,n=nid:self._check_read(i,n),
                         padx=8,pady=3).pack(side="right")

    def _check_read(self,ip,nid):
        def do():
            try:
                r=requests.get(f"http://{ip}:{AGENT_PORT}/status/{nid}",timeout=TIMEOUT)
                d=r.json()
                msg=f"Leído a las {d['read_at']}" if d.get("read") else "Aún no leído."
                self.root.after(0,lambda:messagebox.showinfo("Lectura",msg))
            except: self.root.after(0,lambda:messagebox.showerror("Error","Sin conexión."))
        threading.Thread(target=do,daemon=True).start()

    def _clear_history(self):
        if messagebox.askyesno("Limpiar","¿Borrar todo el historial?"):
            self.history=[]
            try:
                with open(HISTORY_FILE,"w") as f: json.dump([],f)
            except: pass
            self._refresh_history()

    def _build_stats(self, p):
        self._section_title(p,"ESTADÍSTICAS",pady=(22,6))
        top=tk.Frame(p,bg=C["panel"]); top.pack(fill="x",padx=22,pady=(0,12))
        BtnGhost(top,"ACTUALIZAR",self._refresh_stats,padx=10,pady=7).pack(side="left")
        BtnGhost(top,"EXPORTAR CSV",self._export_csv,padx=10,pady=7).pack(side="left",padx=(8,0))
        Btn(top,"EXPORTAR PDF",self._export_pdf,padx=10,pady=7).pack(side="left",padx=(8,0))
        self._exp_lbl=tk.Label(top,text="",font=FNT_MONO,bg=C["panel"],fg=C["text3"])
        self._exp_lbl.pack(side="left",padx=(12,0))
        self._stat_cards=tk.Frame(p,bg=C["panel"]); self._stat_cards.pack(fill="x",padx=22,pady=(0,14))
        self._section_title(p,"POR DÍA DE LA SEMANA")
        self._bar1=tk.Canvas(p,bg=C["card"],height=150,highlightthickness=1,highlightbackground=C["border"])
        self._bar1.pack(fill="x",padx=22,pady=(4,14))
        self._section_title(p,"TOP DISPOSITIVOS")
        self._bar2=tk.Canvas(p,bg=C["card"],height=130,highlightthickness=1,highlightbackground=C["border"])
        self._bar2.pack(fill="x",padx=22,pady=(4,14))
        self._section_title(p,"TEMAS USADOS")
        self._bar3=tk.Canvas(p,bg=C["card"],height=110,highlightthickness=1,highlightbackground=C["border"])
        self._bar3.pack(fill="x",padx=22,pady=(4,28))
        self._refresh_stats()

    def _refresh_stats(self):
        hist=_load_hist(); stats=compute_stats(hist)
        for w in self._stat_cards.winfo_children(): w.destroy()
        if not stats:
            tk.Label(self._stat_cards,text="  //  Sin datos todavía.",
                     font=FNT_MONO,bg=C["panel"],fg=C["text3"],pady=14).pack(anchor="w"); return
        for icon,lbl,val in [
            ("//","TOTAL",str(stats["total"])),
            ("//","ÉXITO",f"{stats['tasa_ok']}%"),
            ("//","DISPOSITIVOS",str(len(stats.get("por_ip",{})))),
            ("//","DÍAS ACTIVOS",str(len(stats.get("por_dia",{})))),
        ]:
            c=tk.Frame(self._stat_cards,bg=C["card"],highlightthickness=1,highlightbackground=C["border"])
            c.pack(side="left",fill="x",expand=True,padx=(0,8))
            tk.Label(c,text=val,font=(C["mono"],22,"bold"),bg=C["card"],fg=C["accent"]).pack(pady=(12,2))
            tk.Label(c,text=lbl,font=FNT_MONO,bg=C["card"],fg=C["text3"]).pack(pady=(0,12))
        self._bar1.update_idletasks()
        self._draw_bars(self._bar1,stats.get("por_dia",{}),C["accent"])
        self._bar2.update_idletasks()
        self._draw_hbars(self._bar2,stats.get("por_ip",{}),C["success"])
        self._bar3.update_idletasks()
        self._draw_bars(self._bar3,stats.get("por_tema",{}),C["info"])

    def _draw_bars(self,cv,data,col):
        cv.delete("all")
        if not data: return
        w=cv.winfo_width() or 600; h=cv.winfo_height() or 150
        pad=44; mv=max(data.values()) or 1; keys=list(data.keys()); n=len(keys)
        bw=max(8,(w-2*pad)//n-8)
        for i,key in enumerate(keys):
            v=data[key]; bh=int((v/mv)*(h-pad-22))
            x=pad+i*((w-2*pad)//n)+4; yb=h-pad
            cv.create_rectangle(x,yb-bh,x+bw,yb,fill=col,outline="",width=0)
            cv.create_rectangle(x,yb-bh,x+bw,yb-bh+2,fill="#ffffff22",outline="")
            cv.create_text(x+bw//2,yb-bh-9,text=str(v),fill=C["text2"],font=FNT_MONO)
            cv.create_text(x+bw//2,yb+11,text=str(key)[:6],fill=C["text3"],font=FNT_MONO)

    def _draw_hbars(self,cv,data,col):
        cv.delete("all")
        if not data: return
        w=cv.winfo_width() or 600; h=cv.winfo_height() or 130
        mv=max(data.values()) or 1; items=list(data.items())
        rh=(h-10)//max(len(items),1)
        for i,(key,val) in enumerate(items):
            y=10+i*rh; bw=int((val/mv)*(w-170))
            cv.create_text(8,y+rh//2,text=str(key)[:20],fill=C["text3"],font=FNT_MONO,anchor="w")
            cv.create_rectangle(148,y+4,148+bw,y+rh-4,fill=col,outline="")
            cv.create_text(152+bw,y+rh//2,text=str(val),fill=C["text"],font=FNT_MONO_B,anchor="w")

    def _export_csv(self):
        hist=_load_hist()
        if not hist: messagebox.showinfo("Sin datos","No hay historial."); return
        path=filedialog.asksaveasfilename(defaultextension=".csv",
             filetypes=[("CSV","*.csv")],initialfile="shocknet_historial.csv")
        if not path: return
        try: export_csv(hist,path); self._exp_lbl.config(text="✓ CSV exportado",fg=C["success"])
        except Exception as e: self._exp_lbl.config(text=f"✗ {e}",fg=C["error"])

    def _export_pdf(self):
        hist=_load_hist()
        if not hist: messagebox.showinfo("Sin datos","No hay historial."); return
        path=filedialog.asksaveasfilename(defaultextension=".pdf",
             filetypes=[("PDF","*.pdf")],initialfile="shocknet_informe.pdf")
        if not path: return
        self._exp_lbl.config(text="generando PDF...",fg=C["warning"])
        def do():
            try:
                export_pdf(hist,path)
                self.root.after(0,lambda:self._exp_lbl.config(text="✓ PDF generado",fg=C["success"]))
                if sys.platform=="win32": os.startfile(path)
                else: subprocess.Popen(["xdg-open",path])
            except ImportError:
                self.root.after(0,lambda:self._exp_lbl.config(text="✗ pip install reportlab",fg=C["error"]))
            except Exception as e:
                msg=str(e)
                self.root.after(0,lambda m=msg:self._exp_lbl.config(text=f"✗ {m}",fg=C["error"]))
        threading.Thread(target=do,daemon=True).start()

    def _build_config(self, p):
        self._section_title(p,"AUTENTICACIÓN",pady=(22,6))
        ac=self._card_frame(p)
        ai=tk.Frame(ac,bg=C["card"]); ai.pack(fill="x",padx=14,pady=14)
        tk.Label(ai,text="TOKEN",font=FNT_MONO_B,bg=C["card"],fg=C["text"]).pack(anchor="w")
        tk.Label(ai,
                 text="Contraseña compartida. El agente solo acepta mensajes con el mismo token.\n"
                      "Vacío = sin protección.",
                 font=FNT_MONO,bg=C["card"],fg=C["text3"],justify="left").pack(anchor="w",pady=(4,8))
        tok_row=tk.Frame(ai,bg=C["card"]); tok_row.pack(fill="x")
        tok_e=Entry(tok_row,self.auth_token,width=40,show="●"); tok_e.pack(side="left")
        self._show_tok=tk.BooleanVar(value=False)
        tk.Checkbutton(tok_row,text="mostrar",variable=self._show_tok,
                       bg=C["card"],fg=C["text3"],activebackground=C["card"],
                       selectcolor=C["card2"],font=FNT_MONO,
                       command=lambda:tok_e.config(show="" if self._show_tok.get() else "●")
                       ).pack(side="left",padx=(10,0))

        self._section_title(p,"HERRAMIENTAS")
        tool_row=tk.Frame(p,bg=C["panel"]); tool_row.pack(fill="x",padx=22,pady=(8,8))
        for txt,cmd in [
            ("QR DEL AGENTE",self._open_qr),
            ("PWA MÓVIL",self._open_pwa),
            ("AGENT.LOG",self._open_log),
        ]:
            BtnGhost(tool_row,txt,cmd,padx=12,pady=8).pack(side="left",padx=(0,8))

        self._section_title(p,"ACERCA DE")
        ab=self._card_frame(p,pady=(0,28))
        abi=tk.Frame(ab,bg=C["card"]); abi.pack(fill="x",padx=14,pady=14)
        tk.Label(abi,text="SHOCKNET  //  Network Alert System",
                 font=(C["mono"],13,"bold"),bg=C["card"],fg=C["accent"]).pack(anchor="w")
        for line in [f"versión {VERSION}",
                     "cifrado AES-256 · kiosko · PWA móvil · webhook · estadísticas",
                     f"Ctrl+Enter enviar · Ctrl+S plantilla · F5 escanear · Ctrl+1-7 navegar"]:
            tk.Label(abi,text=line,font=FNT_MONO,bg=C["card"],fg=C["text3"]).pack(anchor="w",pady=(2,0))

    def _open_qr(self):
        ip=self.manual_ip.get().strip()
        if not ip or ip.endswith("."): messagebox.showwarning("IP inválida","Introduce una IP primero."); return
        webbrowser.open(f"http://{ip}:{AGENT_PORT}/qr")

    def _open_pwa(self):
        ip=self.manual_ip.get().strip()
        if not ip or ip.endswith("."): messagebox.showwarning("IP inválida","Introduce una IP primero."); return
        webbrowser.open(f"http://{ip}:{AGENT_PORT}/")

    def _open_log(self):
        lp=os.path.join(ROOT,"agent.log")
        if not os.path.exists(lp): messagebox.showinfo("Sin logs","No se encontró agent.log."); return
        if sys.platform=="win32": os.startfile(lp)
        else: subprocess.Popen(["xdg-open",lp])

    def _open_screen(self, ip=None):
        ip=ip or self.manual_ip.get().strip()
        if not ip or ip.endswith("."): messagebox.showwarning("IP inválida","Introduce una IP completa."); return
        win=tk.Toplevel(self.root); win.title(f"ShockNet · Pantalla — {ip}")
        win.configure(bg=C["bg"]); win.geometry("960x580")
        tk.Frame(win,bg=C["accent"],height=3).pack(fill="x")
        hdr=tk.Frame(win,bg=C["sidebar"]); hdr.pack(fill="x")
        hi=tk.Frame(hdr,bg=C["sidebar"]); hi.pack(fill="x",padx=16,pady=(10,10))
        tk.Label(hi,text=f"//  PANTALLA REMOTA  —  {ip}",font=FNT_MONO_B,
                 bg=C["sidebar"],fg=C["text"]).pack(side="left")
        stop_var=tk.BooleanVar(value=False)
        ivl=tk.IntVar(value=2)
        for s,v in [("1s",1),("2s",2),("5s",5)]:
            tk.Radiobutton(hi,text=s,variable=ivl,value=v,
                           bg=C["sidebar"],fg=C["text2"],activebackground=C["sidebar"],
                           selectcolor=C["card"],font=FNT_MONO).pack(side="right",padx=(0,8))
        tk.Label(hi,text="intervalo:",font=FNT_MONO,bg=C["sidebar"],fg=C["text3"]).pack(side="right",padx=(0,4))
        info_l=tk.Label(hi,text="",font=FNT_MONO,bg=C["sidebar"],fg=C["text3"])
        info_l.pack(side="right",padx=(0,16))
        BtnGhost(hi,"CERRAR",lambda:[stop_var.set(True),win.destroy()],
                 padx=10,pady=4).pack(side="right",padx=(0,10))
        tk.Frame(win,bg=C["border"],height=1).pack(fill="x")
        cv=tk.Canvas(win,bg="#000000",highlightthickness=0)
        cv.pack(fill="both",expand=True,padx=16,pady=16)
        self._screen_ref=None
        def refresh():
            if stop_var.get(): return
            try:
                from PIL import Image,ImageTk; import io as _io
                r=requests.get(f"http://{ip}:{AGENT_PORT}/screenshot",timeout=5,stream=True)
                if r.status_code==200:
                    img=Image.open(_io.BytesIO(r.content))
                    cw,ch=cv.winfo_width(),cv.winfo_height()
                    if cw>10 and ch>10: img.thumbnail((cw,ch),Image.LANCZOS)
                    photo=ImageTk.PhotoImage(img)
                    cv.delete("all")
                    cv.create_image(cw//2,ch//2,image=photo,anchor="center")
                    self._screen_ref=photo
                    info_l.config(text=f"📸 {datetime.now().strftime('%H:%M:%S')}",fg=C["success"])
            except ImportError: info_l.config(text="pip install pillow",fg=C["error"])
            except Exception as e:
                info_l.config(text=f"sin señal",fg=C["error"])
                cv.delete("all")
                cv.create_text(cv.winfo_width()//2,cv.winfo_height()//2,
                               text="//  SIN SEÑAL\nComprueba que el agente está activo",
                               fill=C["text3"],font=FNT_MONO_B,justify="center")
            if not stop_var.get(): win.after(ivl.get()*1000,refresh)
        win.protocol("WM_DELETE_WINDOW",lambda:[stop_var.set(True),win.destroy()])
        win.after(500,refresh)

    def _auth_headers(self):
        t=self.auth_token.get().strip()
        return {"Authorization":f"Bearer {t}"} if t else {}

    def _ping(self):
        self._conn_status.config(text="verificando...",fg=C["text3"])
        threading.Thread(target=self._ping_thread,daemon=True).start()

    def _ping_thread(self):
        ip=self.manual_ip.get().strip()
        try:
            r=requests.get(f"http://{ip}:{AGENT_PORT}/ping",timeout=TIMEOUT)
            d=r.json(); host=d.get("host","?"); rip=d.get("ip","")
            if rip and rip!=ip: self.root.after(0,lambda i=rip:self.manual_ip.set(i))
            self.root.after(0,lambda h=host,i=rip:self._conn_status.config(
                text=f"✓  {h}  {i}",fg=C["success"]))
            self.root.after(0,lambda h=host:self._conn_dot.config(fg=C["success"]))
            self.root.after(0,lambda h=host:self._conn_lbl.config(text=h,fg=C["success"]))
        except Exception:
            self.root.after(0,lambda:self._conn_status.config(text="✗  sin respuesta",fg=C["error"]))
            self.root.after(0,lambda:self._conn_dot.config(fg=C["error"]))
            self.root.after(0,lambda:self._conn_lbl.config(text="Sin conexión",fg=C["text3"]))

    def _build_payload(self):
        title=self.title_var.get().strip()
        message=self.msg_text.get("1.0","end").strip() if hasattr(self,"msg_text") else ""
        if not title or not message:
            messagebox.showwarning("Campos vacíos","Rellena título y mensaje."); return None
        p={"title":title,"message":message,
           "theme":self.theme_var.get(),"image_url":self.image_url_var.get().strip()}
        return encrypt_payload(p,AES_KEY) if AES_KEY else p

    def _send(self):
        ip=self.manual_ip.get().strip()
        if not ip or ip.endswith("."): messagebox.showwarning("IP inválida","Introduce una IP completa."); return
        payload=self._build_payload()
        if payload is None: return
        sched=self.schedule_var.get().strip()
        if sched:
            try:
                h,m=map(int,sched.split(":"))
                now=datetime.now()
                target=now.replace(hour=h,minute=m,second=0,microsecond=0)
                from datetime import timedelta
                if target<=now: target+=timedelta(days=1)
                diff=(target-now).total_seconds()
                self._sched_lbl.config(text=f"⏱  {target.strftime('%H:%M')}",fg=C["warning"])
                self._send_btn.config(state="disabled")
                def delayed():
                    import time; time.sleep(diff)
                    self.root.after(0,lambda:self._do_send(ip,payload))
                threading.Thread(target=delayed,daemon=True).start()
                return
            except ValueError: messagebox.showwarning("Formato","Usa HH:MM."); return
        self._do_send(ip,payload)

    def _do_send(self,ip,payload):
        self._send_btn.config(state="disabled")
        self._sched_lbl.config(text="")
        self._set_act("enviando...",C["text3"])
        threading.Thread(target=self._send_thread,args=(ip,payload),daemon=True).start()

    def _send_thread(self,ip,payload):
        # Wake-up UDP
        self._udp_wakeup(ip)
        try:
            r=requests.post(f"http://{ip}:{AGENT_PORT}/notify",
                            json=payload,headers=self._auth_headers(),timeout=TIMEOUT)
            ok=r.status_code==200
            nid=r.json().get("id","") if ok else ""
            self._save_history({"ts":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                 "ip":ip,"title":payload.get("title","")[:60],
                                 "theme":payload.get("theme",""),
                                 "status":"enviado" if ok else f"error {r.status_code}",
                                 "notif_id":nid})
            self.root.after(0,lambda:self._set_act(
                "✓  aviso entregado" if ok else f"✗  error {r.status_code}",
                C["success"] if ok else C["error"]))
            if ok: self._notify_desktop(payload.get("title","Aviso"),f"Entregado a {ip}")
            else:  self._notify_desktop("Error",f"Código {r.status_code}",success=False)
        except requests.exceptions.ConnectionError:
            self.root.after(0,lambda:self._set_act("✗  sin conexión — ¿agente activo?",C["error"]))
            self._notify_desktop("Sin conexión",f"No se pudo contactar con {ip}",success=False)
        except Exception as e:
            msg=str(e)
            self.root.after(0,lambda m=msg:self._set_act(f"✗  {m}",C["error"]))
        finally:
            self.root.after(0,lambda:self._send_btn.config(state="normal"))

    def _set_act(self,msg,col):
        self._act_lbl.config(text=f"  {msg}",fg=col)
        self._statusbar.set(msg,col)

    def _udp_wakeup(self, target_ip):
        """Envía UDP broadcast para despertar agentes Android antes del aviso HTTP."""
        try:
            import socket as _sock
            udp_port = 9998  
            s = _sock.socket(_sock.AF_INET, _sock.SOCK_DGRAM)
            s.setsockopt(_sock.SOL_SOCKET, _sock.SO_BROADCAST, 1)
            s.settimeout(1)
            msg = f"SHOCK:{target_ip}".encode()
            
            s.sendto(msg, (target_ip, udp_port))
            s.sendto(msg, ("255.255.255.255", udp_port))
            s.close()
        except Exception:
            pass  

    def _notify_desktop(self,title,message,success=True):
        def do():
            try:
                from plyer import notification
                notification.notify(
                    title=f"⚡ ShockNet — {'OK' if success else 'ERROR'}",
                    message=f"{title}\n{message[:80]}",
                    app_name="ShockNet",timeout=4)
            except: pass
        threading.Thread(target=do,daemon=True).start()


if __name__=="__main__":
    root=tk.Tk()
    ShockNet(root)
    root.mainloop()
