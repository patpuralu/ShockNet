#!/usr/bin/env python3

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.agent import run_flask, run_tray, get_local_ip, log, AGENT_PORT
import threading

if __name__ == "__main__":
    ip = get_local_ip()
    print("="*54)
    print(f"    ShockNet Agent v1.0")
    print(f"  IP        : {ip}")
    print(f"  Puerto    : {AGENT_PORT}")
    print(f"  PWA móvil : http://{ip}:{AGENT_PORT}/")
    print(f"  Webhook   : POST http://{ip}:{AGENT_PORT}/webhook")
    print("  Ctrl+C    para detener")
    print("="*54)
    threading.Thread(target=run_flask, daemon=True).start()
    run_tray(ip)
