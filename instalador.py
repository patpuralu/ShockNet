#!/usr/bin/env python3
import tkinter as tk
from tkinter import messagebox, scrolledtext
import subprocess, sys, os, platform, threading, socket
from datetime import datetime

ROOT   = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(ROOT, "core", "config.py")
SYSTEM = platform.system()

I = {
    "bg":       "#06080f",  
    "sidebar":  "#080d1a",   
    "panel":    "#0b1121",  
    "card":     "#111827",   
    "card2":    "#1a2236",   
    "border":   "#1e2d4a",   
    "border2":  "#2a4070",   
    "accent":   "#3b82f6",   
    "accent2":  "#60a5fa",   
    "accent_d": "#1e3a6e",   
    "ok":       "#10b981",   
    "warn":     "#f59e0b",   
    "err":      "#ef4444",   
    "text":     "#e2e8f0",   
    "text2":    "#94a3b8",   
    "text3":    "#475569",   
    "mono":     "Consolas",  

STEP_W = 200

STEPS = [
    ("01", "CONFIGURACIÓN",  "config"),
    ("02", "DEPENDENCIAS",   "deps"),
    ("03", "INSTALACIÓN",    "install"),
    ("04", "HERRAMIENTAS",   "tools"),
]

class IEntry(tk.Entry):
    def __init__(self, master, var, width=40, show=None, **kw):
        super().__init__(master, textvariable=var, width=width,
                         bg=I["card2"], fg=I["text"], insertbackground=I["accent"],
                         relief="flat", font=(I["mono"],9), show=show or "",
                         highlightthickness=1, highlightbackground=I["border2"],
                         highlightcolor=I["accent"], bd=5, **kw)


class IBtnPrimary(tk.Button):
    def __init__(self, master, text, cmd, padx=16, pady=8, **kw):
        super().__init__(master, text=text, command=cmd,
                         bg=I["accent"], fg="#ffffff",
                         activebackground=I["accent2"], activeforeground="#ffffff",
                         relief="flat", cursor="hand2",
                         font=(I["mono"],9,"bold"), padx=padx, pady=pady, bd=0, **kw)
        self.bind("<Enter>", lambda e: self.config(bg=I["accent2"]))
        self.bind("<Leave>", lambda e: self.config(bg=I["accent"]))


class IBtnGhost(tk.Button):
    def __init__(self, master, text, cmd, padx=12, pady=6, **kw):
        super().__init__(master, text=text, command=cmd,
                         bg=I["card"], fg=I["text2"],
                         activebackground=I["card2"], activeforeground=I["text"],
                         relief="flat", cursor="hand2",
                         font=(I["mono"],9), padx=padx, pady=pady, bd=0,
                         highlightthickness=1, highlightbackground=I["border2"],
                         highlightcolor=I["accent"], **kw)
        self.bind("<Enter>", lambda e: self.config(bg=I["card2"], fg=I["text"]))
        self.bind("<Leave>", lambda e: self.config(bg=I["card"], fg=I["text2"]))


class IBtnDanger(tk.Button):
    def __init__(self, master, text, cmd, padx=14, pady=7, **kw):
        super().__init__(master, text=text, command=cmd,
                         bg=I["accent_d"], fg=I["err"],
                         activebackground=I["err"], activeforeground="#fff",
                         relief="flat", cursor="hand2",
                         font=(I["mono"],9,"bold"), padx=padx, pady=pady, bd=0,
                         highlightthickness=1, highlightbackground=I["err"],
                         **kw)
        self.bind("<Enter>", lambda e: self.config(bg=I["err"], fg="#fff"))
        self.bind("<Leave>", lambda e: self.config(bg=I["accent_d"], fg=I["err"]))


#  SISTEMA
def get_ip():
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.connect(("8.8.8.8",80)); ip=s.getsockname()[0]; s.close(); return ip
    except: return "127.0.0.1"

def get_py(): return sys.executable

def is_installed():
    if SYSTEM=="Windows":
        return subprocess.run(["schtasks","/query","/tn","ShockNetAgent"],
                              capture_output=True).returncode==0
    return os.path.exists("/etc/systemd/system/shocknet-agent.service")

def is_running():
    try:
        if SYSTEM=="Windows":
            r=subprocess.run(["schtasks","/query","/tn","ShockNetAgent","/fo","LIST"],
                             capture_output=True,text=True)
            return "Running" in r.stdout or "En ejecución" in r.stdout
        r=subprocess.run(["systemctl","is-active","shocknet-agent"],
                         capture_output=True,text=True)
        return r.stdout.strip()=="active"
    except: return False

def read_cfg():
    vals={"AGENT_PORT":"9999","SCAN_TIMEOUT":"0.4","AUTH_TOKEN":"",
          "AES_KEY":"","SOUND_ENABLED":"True","KIOSK_MODE":"True",
          "DEFAULT_TITLE":"Aviso de red",
          "DEFAULT_MESSAGE":"Tienes un mensaje del administrador."}
    try:
        with open(CONFIG,"r",encoding="utf-8") as f:
            for line in f:
                s=line.strip()
                for k in vals:
                    if s.startswith(k+" ") or s.startswith(k+"="):
                        p=s.split("=",1)
                        if len(p)==2: vals[k]=p[1].strip().strip('"').strip("'")
    except: pass
    return vals

def write_cfg(vals):
    try:
        with open(CONFIG,"r",encoding="utf-8") as f: lines=f.readlines()
        new=[]
        for line in lines:
            done=False
            for k,v in vals.items():
                if line.strip().startswith(k+" ") or line.strip().startswith(k+"="):
                    if k in ("AGENT_PORT","SCAN_TIMEOUT","SOUND_ENABLED","KIOSK_MODE"):
                        new.append(f"{k} = {v}\n")
                    else:
                        new.append(f'{k} = "{v}"\n')
                    done=True; break
            if not done: new.append(line)
        with open(CONFIG,"w",encoding="utf-8") as f: f.writelines(new)
        return True
    except: return False


#  APP
class Instalador:
    def __init__(self, root):
        self.root=root
        self.root.title("ShockNet — Instalador")
        self.root.configure(bg=I["bg"])
        self.root.resizable(True,True)
        self.root.minsize(760,600)
        self.session_only=tk.BooleanVar(value=False)
        self._build()
        self._center(860,740)
        self.root.after(400,self._refresh_status)

    def _build(self):
        
        top=tk.Frame(self.root,bg=I["accent"],height=2)
        top.pack(fill="x")

        # Header 
        hdr=tk.Frame(self.root,bg=I["sidebar"])
        hdr.pack(fill="x")
        hi=tk.Frame(hdr,bg=I["sidebar"]); hi.pack(fill="x",padx=24,pady=(14,12))

        # Logo
        logo=tk.Frame(hi,bg=I["sidebar"]); logo.pack(side="left")
        tk.Label(logo,text="◈",font=("Segoe UI",24),bg=I["sidebar"],fg=I["accent"]).pack(side="left")
        nf=tk.Frame(logo,bg=I["sidebar"]); nf.pack(side="left",padx=(10,0))
        tk.Label(nf,text="ShockNet",font=("Consolas",16,"bold"),
                 bg=I["sidebar"],fg=I["text"]).pack(anchor="w")
        tk.Label(nf,text="INSTALADOR  //  SETUP",
                 font=("Consolas",8),bg=I["sidebar"],fg=I["text3"]).pack(anchor="w")

        # Estado conexión
        right=tk.Frame(hi,bg=I["sidebar"]); right.pack(side="right")
        st_f=tk.Frame(right,bg=I["card"],highlightthickness=1,
                      highlightbackground=I["border"])
        st_f.pack()
        st_i=tk.Frame(st_f,bg=I["card"]); st_i.pack(padx=14,pady=8)
        self._st_dot=tk.Label(st_i,text="●",font=("Segoe UI",11),bg=I["card"],fg=I["text3"])
        self._st_dot.pack(side="left")
        self._st_txt=tk.Label(st_i,text="comprobando...",font=("Consolas",9),
                               bg=I["card"],fg=I["text3"])
        self._st_txt.pack(side="left",padx=(8,0))

        tk.Frame(self.root,bg=I["border"],height=1).pack(fill="x")


        body=tk.Frame(self.root,bg=I["bg"]); body.pack(fill="both",expand=True)

        self._step_sidebar=tk.Frame(body,bg=I["sidebar"],width=STEP_W)
        self._step_sidebar.pack(side="left",fill="y")
        self._step_sidebar.pack_propagate(False)

        tk.Label(self._step_sidebar,text="  PASOS",font=("Consolas",8,"bold"),
                 bg=I["sidebar"],fg=I["text3"]).pack(anchor="w",padx=14,pady=(16,8))

        self._step_btns={}
        for num,label,key in STEPS:
            sf=tk.Frame(self._step_sidebar,bg=I["sidebar"]); sf.pack(fill="x")
        
            ind=tk.Frame(sf,bg=I["sidebar"],width=3)
            ind.place(x=0,y=0,relheight=1)
            btn=tk.Button(sf,relief="flat",cursor="hand2",anchor="w",
                          bg=I["sidebar"],fg=I["text3"],
                          activebackground=I["card"],activeforeground=I["text"],
                          bd=0,padx=18,pady=12,
                          command=lambda k=key:self._switch(k))
            btn.pack(fill="x")
            
            btn.config(text=f"  {num}  {label}",
                       font=("Consolas",9))
            self._step_btns[key]=(btn,ind)

        # IP info
        tk.Frame(self._step_sidebar,bg=I["sidebar"]).pack(fill="both",expand=True)
        ip_f=tk.Frame(self._step_sidebar,bg=I["sidebar"])
        ip_f.pack(fill="x",pady=(0,4))
        tk.Frame(ip_f,bg=I["border"],height=1).pack(fill="x")
        ii=tk.Frame(ip_f,bg=I["sidebar"]); ii.pack(fill="x",padx=14,pady=10)
        tk.Label(ii,text="IP LOCAL",font=("Consolas",7),bg=I["sidebar"],fg=I["text3"]).pack(anchor="w")
        self._ip_lbl=tk.Label(ii,text=get_ip(),font=("Consolas",10,"bold"),
                               bg=I["sidebar"],fg=I["accent"])
        self._ip_lbl.pack(anchor="w",pady=(2,0))
        tk.Label(ii,text=SYSTEM,font=("Consolas",8),bg=I["sidebar"],fg=I["text3"]).pack(anchor="w")

     
        tk.Frame(body,bg=I["border"],width=1).pack(side="left",fill="y")

        right_area=tk.Frame(body,bg=I["bg"]); right_area.pack(side="left",fill="both",expand=True)

        # Scroll
        right_area.grid_rowconfigure(0, weight=1)
        right_area.grid_columnconfigure(0, weight=1)
        right_area.grid_columnconfigure(1, weight=0)
        self._canvas=tk.Canvas(right_area,bg=I["panel"],highlightthickness=0)
        sb=tk.Scrollbar(right_area,orient="vertical",command=self._canvas.yview,
                        bg=I["card"],troughcolor=I["bg"])
        self._canvas.configure(yscrollcommand=sb.set)
        self._canvas.grid(row=0,column=0,sticky="nsew")
        sb.grid(row=0,column=1,sticky="ns")
        self.root.bind_all("<MouseWheel>",lambda e:self._canvas.yview_scroll(-1*(e.delta//120),"units"))
        self.root.bind_all("<Button-4>",lambda e:self._canvas.yview_scroll(-1,"units"))
        self.root.bind_all("<Button-5>",lambda e:self._canvas.yview_scroll(1,"units"))

        self._pages={}
        for _,_,key in STEPS:
            self._pages[key]=tk.Frame(self._canvas,bg=I["panel"])

        self._page_id=self._canvas.create_window(
            (0,0),window=self._pages["config"],anchor="nw")
        for f in self._pages.values():
            f.bind("<Configure>",lambda e:self._canvas.configure(
                scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",lambda e:self._canvas.itemconfig(
            self._page_id,width=e.width))

        # Consola fija 
        tk.Frame(self.root,bg=I["border"],height=1).pack(fill="x")

        cons_hdr=tk.Frame(self.root,bg=I["card"])
        cons_hdr.pack(fill="x")
        chi=tk.Frame(cons_hdr,bg=I["card"]); chi.pack(fill="x",padx=16,pady=(7,7))

        tk.Label(chi,text="▸ CONSOLA",font=("Consolas",8,"bold"),
                 bg=I["card"],fg=I["accent"]).pack(side="left")

        self._sys_lbl=tk.Label(chi,text="",font=("Consolas",8),
                                bg=I["card"],fg=I["text3"])
        self._sys_lbl.pack(side="right",padx=(0,10))

        IBtnGhost(chi,"LIMPIAR",self._clear_console,padx=8,pady=2).pack(side="right")

        self._console=scrolledtext.ScrolledText(
            self.root,height=9,
            bg="#030508",fg="#4ade80",
            insertbackground="#4ade80",
            relief="flat",font=(I["mono"],9),
            highlightthickness=0,
            selectbackground=I["card2"],
            selectforeground=I["ok"])
        self._console.pack(fill="x")
        self._console.config(state="disabled")
        self._console.tag_configure("ok",  foreground="#4ade80")
        self._console.tag_configure("err", foreground="#f87171")
        self._console.tag_configure("warn",foreground="#fbbf24")
        self._console.tag_configure("info",foreground="#60a5fa")
        self._console.tag_configure("dim", foreground=I["text3"])

        self._build_config(self._pages["config"])
        self._build_install(self._pages["install"])
        self._build_deps(self._pages["deps"])
        self._build_tools(self._pages["tools"])
        self._switch("config")

        self._log(f"ShockNet Instalador iniciado",tag="info")
        self._log(f"Sistema    :  {SYSTEM}",tag="dim")
        self._log(f"Python     :  {get_py()}",tag="dim")
        self._log(f"Directorio :  {ROOT}",tag="dim")
        self._log(f"IP local   :  {get_ip()}",tag="dim")

    def _switch(self,key):
        self._canvas.itemconfig(self._page_id,window=self._pages[key])
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        self._canvas.yview_moveto(0)
        for k,(btn,ind) in self._step_btns.items():
            if k==key:
                btn.config(fg=I["accent"],bg=I["card"],
                           font=("Consolas",9,"bold"))
                ind.config(bg=I["accent"])
            else:
                btn.config(fg=I["text3"],bg=I["sidebar"],
                           font=("Consolas",9))
                ind.config(bg=I["sidebar"])

    def _section(self,p,text,pady=(22,8)):
        f=tk.Frame(p,bg=I["panel"]); f.pack(fill="x",padx=24,pady=pady)
        tk.Label(f,text=f"//  {text}",font=("Consolas",10,"bold"),
                 bg=I["panel"],fg=I["accent"]).pack(side="left")
        tk.Frame(f,bg=I["border2"],height=1).pack(side="left",fill="x",
                                                    expand=True,padx=(12,0))

    def _card(self,p,pady=(0,10)):
        c=tk.Frame(p,bg=I["card"],highlightthickness=1,
                   highlightbackground=I["border"])
        c.pack(fill="x",padx=24,pady=pady); return c

    def _lentry(self,p,label,var,hint=None,show=None):
        f=tk.Frame(p,bg=I["panel"]); f.pack(fill="x",padx=24,pady=(10,0))
        tk.Label(f,text=label,font=("Consolas",8),bg=I["panel"],fg=I["text2"]).pack(anchor="w")
        IEntry(f,var,width=62,show=show).pack(fill="x",pady=(3,0))
        if hint:
            tk.Label(f,text=hint,font=("Consolas",8),
                     bg=I["panel"],fg=I["text3"]).pack(anchor="w",pady=(2,0))

    def _center(self,w,h):
        self.root.update_idletasks()
        sw=self.root.winfo_screenwidth(); sh=self.root.winfo_screenheight()
        h=min(h,sh-40); self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _log(self,msg,tag="ok"):
        self._console.config(state="normal")
        ts=datetime.now().strftime("%H:%M:%S")
        self._console.insert("end",f"[{ts}] ",("dim",))
        self._console.insert("end",f"{msg}\n",(tag,))
        self._console.see("end")
        self._console.config(state="disabled")

    def _clear_console(self):
        self._console.config(state="normal")
        self._console.delete("1.0","end")
        self._console.config(state="disabled")

    def _build_config(self,p):
        cfg=read_cfg()

        self._section(p,"CONEXIÓN Y RED",pady=(22,6))
        net=self._card(p)
        ni=tk.Frame(net,bg=I["card"]); ni.pack(fill="x",padx=16,pady=14)
        row=tk.Frame(ni,bg=I["card"]); row.pack(fill="x")
        l=tk.Frame(row,bg=I["card"]); l.pack(side="left",fill="x",expand=True,padx=(0,12))
        tk.Label(l,text="PUERTO DEL AGENTE",font=("Consolas",8),
                 bg=I["card"],fg=I["text2"]).pack(anchor="w")
        self._port=tk.StringVar(value=cfg["AGENT_PORT"])
        IEntry(l,self._port,width=12).pack(anchor="w",pady=(3,0))
        r=tk.Frame(row,bg=I["card"]); r.pack(side="left",fill="x",expand=True)
        tk.Label(r,text="TIMEOUT ESCANEO (seg)",font=("Consolas",8),
                 bg=I["card"],fg=I["text2"]).pack(anchor="w")
        self._scan=tk.StringVar(value=cfg["SCAN_TIMEOUT"])
        IEntry(r,self._scan,width=10).pack(anchor="w",pady=(3,0))

        self._section(p,"SEGURIDAD")
        sec=self._card(p)
        si=tk.Frame(sec,bg=I["card"]); si.pack(fill="x",padx=16,pady=14)

        tk.Label(si,text="TOKEN DE AUTENTICACIÓN",font=("Consolas",9,"bold"),
                 bg=I["card"],fg=I["text"]).pack(anchor="w")
        tk.Label(si,
                 text="Contraseña compartida entre launcher y agente.\n"
                      "Vacío = sin protección. Recomendado para redes públicas.",
                 font=("Consolas",8),bg=I["card"],fg=I["text3"],
                 justify="left").pack(anchor="w",pady=(3,8))
        tok_row=tk.Frame(si,bg=I["card"]); tok_row.pack(fill="x")
        self._auth=tk.StringVar(value=cfg["AUTH_TOKEN"])
        tok_e=IEntry(tok_row,self._auth,width=40,show="●"); tok_e.pack(side="left")
        self._show_tok=tk.BooleanVar(value=False)
        tk.Checkbutton(tok_row,text=" mostrar",variable=self._show_tok,
                       bg=I["card"],fg=I["text3"],activebackground=I["card"],
                       selectcolor=I["card2"],font=("Consolas",8),
                       command=lambda:tok_e.config(show="" if self._show_tok.get() else "●")
                       ).pack(side="left",padx=(10,0))

        # Separador
        tk.Frame(si,bg=I["border"],height=1).pack(fill="x",pady=(14,14))
        
        tk.Label(si,text="CLAVE DE CIFRADO AES-256",font=("Consolas",9,"bold"),
                 bg=I["card"],fg=I["text"]).pack(anchor="w")
        tk.Label(si,text="32 caracteres exactos. Vacío = sin cifrado.",
                 font=("Consolas",8),bg=I["card"],fg=I["text3"]).pack(anchor="w",pady=(3,8))
        aes_row=tk.Frame(si,bg=I["card"]); aes_row.pack(fill="x")
        self._aes=tk.StringVar(value=cfg["AES_KEY"])
        aes_e=IEntry(aes_row,self._aes,width=40,show="●"); aes_e.pack(side="left")
        self._show_aes=tk.BooleanVar(value=False)
        tk.Checkbutton(aes_row,text=" mostrar",variable=self._show_aes,
                       bg=I["card"],fg=I["text3"],activebackground=I["card"],
                       selectcolor=I["card2"],font=("Consolas",8),
                       command=lambda:aes_e.config(show="" if self._show_aes.get() else "●")
                       ).pack(side="left",padx=(10,0))
        self._aes_hint=tk.Label(si,text="",font=("Consolas",8),bg=I["card"],fg=I["text3"])
        self._aes_hint.pack(anchor="w",pady=(5,0))
        self._aes.trace_add("write",self._check_aes)

        #  Comportamiento 
        self._section(p,"COMPORTAMIENTO")
        beh=self._card(p)
        bi=tk.Frame(beh,bg=I["card"]); bi.pack(fill="x",padx=16,pady=14)
        self._sound=tk.BooleanVar(value=cfg["SOUND_ENABLED"]=="True")
        self._kiosk=tk.BooleanVar(value=cfg["KIOSK_MODE"]=="True")
        for var,label,hint in [
            (self._sound,"SONIDO DE ALERTA",
             "Reproduce un pitido cuando llega un aviso."),
            (self._kiosk,"MODO KIOSKO",
             "Mantiene el aviso en primer plano. El receptor no puede ignorarlo."),
        ]:
            fr=tk.Frame(bi,bg=I["card"]); fr.pack(fill="x",pady=(0,10))
            cb=tk.Checkbutton(fr,text=f"  {label}",variable=var,
                              bg=I["card"],fg=I["text"],activebackground=I["card"],
                              selectcolor=I["accent_d"],font=("Consolas",9),cursor="hand2")
            cb.pack(anchor="w")
            tk.Label(fr,text=f"     {hint}",font=("Consolas",8),
                     bg=I["card"],fg=I["text3"]).pack(anchor="w")

        self._section(p,"MENSAJES POR DEFECTO")
        msg_c=self._card(p)
        mi=tk.Frame(msg_c,bg=I["card"]); mi.pack(fill="x",padx=16,pady=14)
        self._def_title=tk.StringVar(value=cfg["DEFAULT_TITLE"])
        self._def_msg=tk.StringVar(value=cfg["DEFAULT_MESSAGE"])
        for label,var in [("TÍTULO POR DEFECTO",self._def_title),
                           ("MENSAJE POR DEFECTO",self._def_msg)]:
            tk.Label(mi,text=label,font=("Consolas",8),bg=I["card"],fg=I["text2"]).pack(anchor="w")
            IEntry(mi,var,width=65).pack(fill="x",pady=(3,10))

        bf=tk.Frame(p,bg=I["panel"]); bf.pack(fill="x",padx=24,pady=(16,28))
        IBtnPrimary(bf,"  GUARDAR CONFIGURACIÓN  ",self._save_cfg,padx=18,pady=10).pack(side="left")
        self._cfg_lbl=tk.Label(bf,text="",font=("Consolas",8),bg=I["panel"],fg=I["text3"])
        self._cfg_lbl.pack(side="left",padx=(14,0))

    def _check_aes(self,*_):
        n=len(self._aes.get())
        if n==0: self._aes_hint.config(text="sin cifrado",fg=I["text3"])
        elif n<32: self._aes_hint.config(text=f"{n}/32 — faltan {32-n} caracteres",fg=I["warn"])
        elif n==32: self._aes_hint.config(text="✓ longitud correcta",fg=I["ok"])
        else: self._aes_hint.config(text=f"⚠ demasiado largo ({n}/32)",fg=I["warn"])

    def _save_cfg(self):
        vals={
            "AGENT_PORT":     self._port.get().strip(),
            "SCAN_TIMEOUT":   self._scan.get().strip(),
            "AUTH_TOKEN":     self._auth.get().strip(),
            "AES_KEY":        self._aes.get().strip(),
            "SOUND_ENABLED":  "True" if self._sound.get() else "False",
            "KIOSK_MODE":     "True" if self._kiosk.get() else "False",
            "DEFAULT_TITLE":  self._def_title.get().strip(),
            "DEFAULT_MESSAGE":self._def_msg.get().strip(),
        }
        try: assert 1024<int(vals["AGENT_PORT"])<65535
        except: messagebox.showwarning("Puerto inválido","Debe ser entre 1025 y 65534."); return
        if write_cfg(vals):
            self._cfg_lbl.config(text="✓ configuración guardada",fg=I["ok"])
            self._log("Configuración guardada en core/config.py","ok")
        else:
            self._cfg_lbl.config(text="✗ error al guardar",fg=I["err"])
            self._log("ERROR: no se pudo escribir core/config.py","err")
   
    def _build_install(self,p):
        # Estado actual
        self._section(p,"ESTADO ACTUAL",pady=(22,6))
        st=self._card(p)
        sti=tk.Frame(st,bg=I["card"]); sti.pack(fill="x",padx=16,pady=14)
        sr=tk.Frame(sti,bg=I["card"]); sr.pack(fill="x")
        self._st_card_dot=tk.Label(sr,text="●",font=("Segoe UI",14),
                                    bg=I["card"],fg=I["text3"])
        self._st_card_dot.pack(side="left")
        self._st_card_txt=tk.Label(sr,text="comprobando...",
                                    font=("Consolas",9,"bold"),bg=I["card"],fg=I["text3"])
        self._st_card_txt.pack(side="left",padx=(10,0))
        IBtnGhost(sr,"ACTUALIZAR",self._refresh_status,padx=10,pady=4).pack(side="right")
        ip_r=tk.Frame(sti,bg=I["card"]); ip_r.pack(fill="x",pady=(8,0))
        tk.Label(ip_r,text="IP: ",font=("Consolas",8),bg=I["card"],fg=I["text3"]).pack(side="left")
        self._ip_card=tk.Label(ip_r,text=get_ip(),font=("Consolas",9,"bold"),
                                bg=I["card"],fg=I["accent"])
        self._ip_card.pack(side="left")

        # Modo
        self._section(p,"MODO DE INSTALACIÓN")
        mode=self._card(p)
        mi=tk.Frame(mode,bg=I["card"]); mi.pack(fill="x",padx=16,pady=14)
        for val,label,hint in [
            (False,"◉  ARRANQUE AUTOMÁTICO",
             "El agente arranca con el sistema. Requiere permisos de administrador/sudo."),
            (True, "◈  SOLO ESTA SESIÓN",
             "El agente corre ahora mismo. Al reiniciar se detiene."),
        ]:
            fr=tk.Frame(mi,bg=I["card"]); fr.pack(fill="x",pady=(0,10))
            tk.Radiobutton(fr,text=f"  {label}",variable=self.session_only,value=val,
                           bg=I["card"],fg=I["text"],activebackground=I["card"],
                           selectcolor=I["accent_d"],font=("Consolas",9),cursor="hand2").pack(anchor="w")
            tk.Label(fr,text=f"     {hint}",font=("Consolas",8),
                     bg=I["card"],fg=I["text3"]).pack(anchor="w")

        # Directorio
        self._section(p,"DIRECTORIO DEL PROYECTO")
        dir_c=self._card(p)
        di=tk.Frame(dir_c,bg=I["card"]); di.pack(fill="x",padx=16,pady=14)
        self._dir=tk.StringVar(value=ROOT)
        IEntry(di,self._dir,width=65).pack(fill="x")
        tk.Label(di,text="Por defecto usa la carpeta actual.",
                 font=("Consolas",7),bg=I["card"],fg=I["text3"]).pack(anchor="w",pady=(4,0))

        # Botones
        tk.Frame(p,bg=I["border"],height=1).pack(fill="x",padx=24,pady=(20,0))
        br=tk.Frame(p,bg=I["panel"]); br.pack(fill="x",padx=24,pady=(14,0))
        self._inst_btn=IBtnPrimary(br,"  ⬇  INSTALAR  ",self._install,padx=20,pady=10)
        self._inst_btn.pack(side="left")
        IBtnDanger(br,"DESINSTALAR",self._uninstall,padx=16,pady=9).pack(side="left",padx=(10,0))
        IBtnGhost(br,"▶ INICIAR",self._start,padx=12,pady=9).pack(side="left",padx=(10,0))
        IBtnGhost(br,"■ PARAR",self._stop,padx=12,pady=9).pack(side="left",padx=(8,0))
        self._inst_lbl=tk.Label(p,text="",font=("Consolas",8),bg=I["panel"],fg=I["text3"])
        self._inst_lbl.pack(anchor="w",padx=24,pady=(10,28))

    def _build_deps(self,p):
        self._section(p,"PAQUETES NECESARIOS",pady=(22,6))
        DEPS=[
            ("flask",        "Servidor web del agente",     "obligatorio"),
            ("requests",     "Cliente HTTP del launcher",   "obligatorio"),
            ("pillow",       "Imágenes y capturas",         "obligatorio"),
            ("qrcode",       "Generación de código QR",     "recomendado"),
            ("pystray",      "Icono en la bandeja",         "recomendado"),
            ("cryptography", "Cifrado AES-256",             "recomendado"),
            ("plyer",        "Notificaciones de escritorio","recomendado"),
            ("reportlab",    "Exportar historial a PDF",    "opcional"),
        ]
        self._dep_lbls={}
        for pkg,desc,level in DEPS:
            cc={
                "obligatorio": I["ok"],
                "recomendado": I["warn"],
                "opcional":    I["text3"],
            }[level]
            card=tk.Frame(p,bg=I["card"],highlightthickness=1,
                          highlightbackground=I["border"])
            card.pack(fill="x",padx=24,pady=(0,5))
            inner=tk.Frame(card,bg=I["card"]); inner.pack(fill="x",padx=14,pady=9)
            tk.Label(inner,text="▸",font=("Consolas",10,"bold"),
                     bg=I["card"],fg=cc).pack(side="left")
            info=tk.Frame(inner,bg=I["card"]); info.pack(side="left",padx=(8,0))
            tk.Label(info,text=pkg,font=("Consolas",9,"bold"),
                     bg=I["card"],fg=I["text"]).pack(anchor="w")
            tk.Label(info,text=f"{desc}  ·  {level}",font=("Consolas",8),
                     bg=I["card"],fg=I["text3"]).pack(anchor="w")
            slbl=tk.Label(inner,text="—",font=("Consolas",8),
                          bg=I["card"],fg=I["text3"])
            slbl.pack(side="right")
            self._dep_lbls[pkg]=slbl

        br=tk.Frame(p,bg=I["panel"]); br.pack(fill="x",padx=24,pady=(14,0))
        IBtnPrimary(br,"  INSTALAR TODO  ",self._install_all,padx=18,pady=9).pack(side="left")
        IBtnGhost(br,"COMPROBAR ESTADO",self._check_deps,padx=14,pady=9).pack(side="left",padx=(10,0))
        self._deps_lbl=tk.Label(p,text="",font=("Consolas",8),
                                 bg=I["panel"],fg=I["text3"])
        self._deps_lbl.pack(anchor="w",padx=24,pady=(10,28))

    def _check_deps(self):
        self._deps_lbl.config(text="comprobando...",fg=I["warn"])
        def do():
            for pkg in self._dep_lbls:
                try:
                    __import__("PIL" if pkg=="pillow" else pkg.replace("-","_"))
                    self.root.after(0,lambda p=pkg:
                        self._dep_lbls[p].config(text="✓ instalado",fg=I["ok"]))
                except ImportError:
                    self.root.after(0,lambda p=pkg:
                        self._dep_lbls[p].config(text="✗ falta",fg=I["err"]))
            self.root.after(0,lambda:self._deps_lbl.config(
                text="comprobación completada",fg=I["text2"]))
        threading.Thread(target=do,daemon=True).start()

    def _install_all(self):
        self._deps_lbl.config(text="instalando...",fg=I["warn"])
        self._log("Instalando dependencias...","info")
        pkgs=["flask","requests","pillow","qrcode","pystray",
              "cryptography","plyer","reportlab"]
        def do():
            cmd=[get_py(),"-m","pip","install"]+pkgs+["--quiet"]
            if SYSTEM=="Linux": cmd.append("--break-system-packages")
            r=subprocess.run(cmd,capture_output=True,text=True)
            if r.returncode==0:
                self._log("Dependencias instaladas correctamente","ok")
                self.root.after(0,lambda:self._deps_lbl.config(
                    text="✓ todo instalado",fg=I["ok"]))
                self.root.after(500,self._check_deps)
            else:
                err=(r.stderr or r.stdout)[:300]
                self._log(f"ERROR: {err}","err")
                self.root.after(0,lambda:self._deps_lbl.config(
                    text="✗ error — ver consola",fg=I["err"]))
        threading.Thread(target=do,daemon=True).start()


    def _build_tools(self,p):
        self._section(p,"ACCIONES RÁPIDAS",pady=(22,6))
        TOOLS=[
            ("ABRIR SHOCKNET LAUNCHER",
             "Abre el panel de control para enviar avisos.",
             self._open_launcher),
            ("PROBAR AGENTE LOCAL",
             "Comprueba si el agente responde en localhost.",
             self._test_agent),
            ("ABRIR PWA MÓVIL",
             "Abre la interfaz web para móvil en el navegador.",
             self._open_pwa),
            ("VER QR DEL AGENTE",
             "Muestra el QR con la URL del agente.",
             self._open_qr),
            ("ABRIR AGENT.LOG",
             "Abre el archivo de logs del agente.",
             self._open_log),
        ]
        for label,desc,cmd in TOOLS:
            card=tk.Frame(p,bg=I["card"],highlightthickness=1,
                          highlightbackground=I["border"])
            card.pack(fill="x",padx=24,pady=(0,8))
            inner=tk.Frame(card,bg=I["card"]); inner.pack(fill="x",padx=14,pady=12)
            info=tk.Frame(inner,bg=I["card"]); info.pack(side="left",fill="x",expand=True)
            tk.Label(info,text=label,font=("Consolas",9,"bold"),
                     bg=I["card"],fg=I["text"]).pack(anchor="w")
            tk.Label(info,text=desc,font=("Consolas",8),
                     bg=I["card"],fg=I["text3"]).pack(anchor="w")
            IBtnPrimary(inner,"EJECUTAR",cmd,padx=12,pady=5).pack(side="right")

        # Info del sistema
        self._section(p,"INFORMACIÓN DEL SISTEMA")
        sys_c=self._card(p,pady=(0,28))
        sf=tk.Frame(sys_c,bg=I["card"]); sf.pack(fill="x",padx=16,pady=14)
        import platform as pl
        data=[
            ("SISTEMA",      f"{pl.system()} {pl.release()}"),
            ("PYTHON",       pl.python_version()),
            ("EJECUTABLE",   get_py()[:55]),
            ("IP LOCAL",     get_ip()),
            ("DIRECTORIO",   ROOT[:55]),
            ("SERVICIO WIN", "ShockNetAgent"),
            ("SERVICIO LNX", "shocknet-agent.service"),
        ]
        for label,val in data:
            row=tk.Frame(sf,bg=I["card"]); row.pack(fill="x",pady=2)
            tk.Label(row,text=f"{label:<18}",font=("Consolas",8),
                     bg=I["card"],fg=I["text3"]).pack(side="left")
            tk.Label(row,text=val,font=("Consolas",8),
                     bg=I["card"],fg=I["accent"]).pack(side="left")

        self._tools_lbl=tk.Label(p,text="",font=("Consolas",8),
                                  bg=I["panel"],fg=I["text3"])
        self._tools_lbl.pack(anchor="w",padx=24,pady=(0,28))

    def _refresh_status(self):
        threading.Thread(target=self._refresh_thread,daemon=True).start()

    def _refresh_thread(self):
        inst=is_installed(); run=is_running() if inst else False
        if run:   dot,txt,col="●","ACTIVO Y CORRIENDO",I["ok"]
        elif inst:dot,txt,col="●","INSTALADO / NO CORRIENDO",I["warn"]
        else:     dot,txt,col="●","NO INSTALADO",I["text3"]
        self.root.after(0,lambda:self._st_dot.config(fg=col,text=dot))
        self.root.after(0,lambda:self._st_txt.config(text=txt,fg=col))
        if hasattr(self,"_st_card_dot"):
            self.root.after(0,lambda:self._st_card_dot.config(fg=col))
            self.root.after(0,lambda:self._st_card_txt.config(text=txt,fg=col))
        self.root.after(0,lambda:[self._ip_lbl.config(text=get_ip()),
                                   self._ip_card.config(text=get_ip())])

    def _install(self):
        self._save_cfg()
        self._inst_btn.config(state="disabled")
        self._inst_lbl.config(text="instalando...",fg=I["warn"])
        threading.Thread(target=self._install_thread,daemon=True).start()

    def _install_thread(self):
        py=get_py()
        agent=os.path.join(self._dir.get().strip(),"agent_run.py")
        self._log(f"Instalando agente: {agent}","info")
        if self.session_only.get():
            self._log("Modo sesión — sin servicio persistente","info")
            try:
                subprocess.Popen([py,agent])
                self._log("Agente lanzado para esta sesión","ok")
                self.root.after(0,lambda:self._inst_lbl.config(
                    text="✓ agente lanzado (solo sesión)",fg=I["ok"]))
            except Exception as e:
                self._log(f"ERROR: {e}","err")
                self.root.after(0,lambda:self._inst_lbl.config(text=f"✗ {e}",fg=I["err"]))
        else:
            if SYSTEM=="Windows": self._inst_windows(py,agent)
            else:                 self._inst_linux(py,agent)
        self.root.after(0,lambda:self._inst_btn.config(state="normal"))
        self.root.after(1500,self._refresh_status)

    def _inst_windows(self,py,agent):
        vbs=os.path.join(ROOT,"run_agent.vbs")
        with open(vbs,"w") as f:
            f.write(f'Set WshShell = CreateObject("WScript.Shell")\n')
            f.write(f'WshShell.Run """{py}"" ""{agent}""", 0, False\n')
        subprocess.run(["schtasks","/delete","/tn","ShockNetAgent","/f"],capture_output=True)
        r=subprocess.run(["schtasks","/create","/tn","ShockNetAgent",
                          "/tr",f'wscript.exe "{vbs}"',
                          "/sc","ONLOGON","/rl","HIGHEST","/f"],
                         capture_output=True,text=True)
        if r.returncode==0:
            subprocess.Popen(["wscript.exe",vbs])
            self._log("Tarea programada creada. Agente iniciado.","ok")
            self.root.after(0,lambda:self._inst_lbl.config(text="✓ instalado",fg=I["ok"]))
        else:
            self._log(f"ERROR: {r.stderr or r.stdout}","err")
            self._log("→ Ejecuta instalador.py como Administrador","warn")
            self.root.after(0,lambda:self._inst_lbl.config(
                text="✗ ejecuta como Administrador",fg=I["err"]))

    def _inst_linux(self,py,agent):
        user=os.environ.get("SUDO_USER") or os.environ.get("USER") or "root"
        svc=f"""[Unit]
Description=ShockNet Agent
After=network.target graphical.target

[Service]
Type=simple
User={user}
WorkingDirectory={ROOT}
ExecStart={py} {agent}
Restart=on-failure
RestartSec=5
Environment=DISPLAY=:0
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
        try:
            with open("/etc/systemd/system/shocknet-agent.service","w") as f: f.write(svc)
            subprocess.run(["systemctl","daemon-reload"],check=True)
            subprocess.run(["systemctl","enable","shocknet-agent","--quiet"],check=True)
            subprocess.run(["systemctl","start","shocknet-agent"],check=True)
            self._log("Servicio systemd creado e iniciado","ok")
            self.root.after(0,lambda:self._inst_lbl.config(text="✓ instalado",fg=I["ok"]))
        except PermissionError:
            self._log("ERROR: necesitas sudo — ejecuta: sudo python3 instalador.py","err")
            self.root.after(0,lambda:self._inst_lbl.config(text="✗ necesitas sudo",fg=I["err"]))
        except Exception as e:
            msg=str(e)
            self._log(f"ERROR: {msg}","err")
            self.root.after(0,lambda m=msg:self._inst_lbl.config(text=f"✗ {m}",fg=I["err"]))

    def _uninstall(self):
        if not messagebox.askyesno("Desinstalar","¿Desinstalar ShockNet Agent?"): return
        threading.Thread(target=self._uninstall_thread,daemon=True).start()

    def _uninstall_thread(self):
        self._log("Desinstalando...","warn")
        if SYSTEM=="Windows":
            subprocess.run(["taskkill","/f","/im","wscript.exe"],capture_output=True)
            r=subprocess.run(["schtasks","/delete","/tn","ShockNetAgent","/f"],
                             capture_output=True,text=True)
            if r.returncode==0:
                self._log("Tarea ShockNetAgent eliminada","ok")
                self.root.after(0,lambda:self._inst_lbl.config(text="✓ desinstalado",fg=I["ok"]))
            else:
                self._log(f"ERROR: {r.stderr}","err")
        else:
            for cmd in [["systemctl","stop","shocknet-agent"],
                        ["systemctl","disable","shocknet-agent","--quiet"]]:
                try: subprocess.run(cmd,check=True)
                except Exception as e: self._log(str(e),"warn")
            try:
                os.remove("/etc/systemd/system/shocknet-agent.service")
                subprocess.run(["systemctl","daemon-reload"])
                self._log("Servicio eliminado","ok")
                self.root.after(0,lambda:self._inst_lbl.config(text="✓ desinstalado",fg=I["ok"]))
            except Exception as e:
                msg=str(e)
                self._log(f"ERROR: {msg}","err")
                self.root.after(0,lambda m=msg:self._inst_lbl.config(text=f"✗ {m}",fg=I["err"]))
        self.root.after(1500,self._refresh_status)

    def _start(self):
        def do():
            self._log("Iniciando agente...","info")
            if SYSTEM=="Windows":
                vbs=os.path.join(ROOT,"run_agent.vbs")
                if os.path.exists(vbs): subprocess.Popen(["wscript.exe",vbs])
                else: subprocess.Popen([get_py(),os.path.join(ROOT,"agent_run.py")])
            else:
                try: subprocess.run(["systemctl","start","shocknet-agent"],check=True)
                except: subprocess.Popen([get_py(),os.path.join(ROOT,"agent_run.py")])
            self._log("Agente iniciado","ok")
            self.root.after(1500,self._refresh_status)
        threading.Thread(target=do,daemon=True).start()

    def _stop(self):
        def do():
            self._log("Parando agente...","warn")
            if SYSTEM=="Windows":
                subprocess.run(["taskkill","/f","/im","wscript.exe"],capture_output=True)
                subprocess.run(["taskkill","/f","/im","pythonw.exe"],capture_output=True)
            else:
                try: subprocess.run(["systemctl","stop","shocknet-agent"],check=True)
                except Exception as e: self._log(str(e),"err")
            self._log("Agente detenido","ok")
            self.root.after(1500,self._refresh_status)
        threading.Thread(target=do,daemon=True).start()

    def _open_launcher(self):
        lp=os.path.join(ROOT,"shocknet.py")
        if not os.path.exists(lp):
            messagebox.showerror("No encontrado","shocknet.py no encontrado."); return
        subprocess.Popen([get_py(),lp])
        self._log("ShockNet Launcher abierto","ok")
        self._tools_lbl.config(text="✓ ShockNet abierto",fg=I["ok"])

    def _test_agent(self):
        import requests as req
        port=int(self._port.get().strip() or "9999")
        def do():
            try:
                r=req.get(f"http://127.0.0.1:{port}/ping",timeout=3)
                host=r.json().get("host","?")
                self._log(f"Agente local activo: {host}","ok")
                self.root.after(0,lambda:self._tools_lbl.config(
                    text=f"✓ agente activo — {host}",fg=I["ok"]))
            except Exception as e:
                self._log(f"Sin respuesta del agente: {e}","err")
                self.root.after(0,lambda:self._tools_lbl.config(
                    text="✗ agente no responde",fg=I["err"]))
        threading.Thread(target=do,daemon=True).start()

    def _open_pwa(self):
        webbrowser.open(f"http://127.0.0.1:{self._port.get().strip() or '9999'}/")
        self._log("PWA móvil abierta","ok")

    def _open_qr(self):
        webbrowser.open(f"http://127.0.0.1:{self._port.get().strip() or '9999'}/qr")
        self._log("QR abierto en el navegador","ok")

    def _open_log(self):
        lp=os.path.join(ROOT,"agent.log")
        if not os.path.exists(lp): messagebox.showinfo("Sin logs","agent.log no encontrado."); return
        if SYSTEM=="Windows": os.startfile(lp)
        else: subprocess.Popen(["xdg-open",lp])
        self._log("Logs abiertos","ok")


import webbrowser
if __name__=="__main__":
    root=tk.Tk()
    Instalador(root)
    root.mainloop()
