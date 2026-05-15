# ============================================================
#  ShockNet — core/kiosk.py v1.0
# ============================================================

import platform, subprocess, time, threading, logging, os

log    = logging.getLogger("shocknet-kiosk")
SYSTEM = platform.system()


def _find_window_linux(port):
    for cmd in [
        ["xdotool","search","--name","ShockNet"],
        ["xdotool","search","--onlyvisible","--name","localhost"],
        ["xdotool","search","--onlyvisible","--name",f":{port}"],
    ]:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            ids = r.stdout.strip().splitlines()
            if ids: return ids[-1]
        except Exception: pass
    return None


def _force_focus_linux(win_id):
    env = {**os.environ, "DISPLAY": os.environ.get("DISPLAY",":0")}
    for cmd in [
        ["xdotool","windowactivate","--sync",win_id],
        ["xdotool","key","--window",win_id,"F11"],
        ["wmctrl","-i","-r",win_id,"-b","add,fullscreen"],
    ]:
        try: subprocess.run(cmd, capture_output=True, timeout=2, env=env)
        except Exception: pass


def _force_focus_windows(port):
    try:
        import win32gui, win32con
        wins = []
        def cb(hwnd, r):
            t = win32gui.GetWindowText(hwnd)
            if str(port) in t or "ShockNet" in t or "localhost" in t:
                r.append(hwnd)
        win32gui.EnumWindows(cb, wins)
        for hwnd in wins:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
    except Exception as e:
        log.debug(f"Kiosko Windows: {e}")


def start_kiosk(port: int, stop_event: threading.Event):
    log.info("Modo kiosko activado.")
    time.sleep(2)
    while not stop_event.is_set():
        try:
            if SYSTEM == "Linux":
                wid = _find_window_linux(port)
                if wid: _force_focus_linux(wid)
            elif SYSTEM == "Windows":
                _force_focus_windows(port)
        except Exception: pass
        time.sleep(1)
    log.info("Modo kiosko desactivado.")
