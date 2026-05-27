
APP_NAME    = "ShockNet"
VERSION     = "1.0"

AGENT_PORT          = 9999
TIMEOUT             = 5
SCAN_TIMEOUT        = 0.4
AUTO_SCAN_INTERVAL  = 5      # minutos 
SCREENSHOT_INTERVAL = 2      

# Seguridad
AUTH_TOKEN = ""              # vacío = sin autenticación
AES_KEY    = ""              # vacío = sin cifrado (32 chars exactos si se usa)

# Comportamiento
KIOSK_MODE     = True       
SOUND_ENABLED  = True       

#  Mensajes por defecto
DEFAULT_TITLE   = "Aviso de red"
DEFAULT_MESSAGE = "Hola"

# Temas 
THEMES = {
    "cyber": {
        "name": "⚡ Cyber",
        "bg": "#020c14",
        "card_bg": "rgba(0, 240, 255, 0.04)",
        "card_border": "rgba(0, 240, 255, 0.12)",
        "text": "#e0f8ff",
        "muted": "rgba(180, 240, 255, 0.5)",
        "accent": "#00f0ff",
        "btn_fg": "#000000",
        "icon": "⚡",
    },
    "aurora": {
        "name": "✦ Aurora",
        "bg": "#08020f",
        "card_bg": "rgba(160, 80, 255, 0.06)",
        "card_border": "rgba(200, 100, 255, 0.15)",
        "text": "#f0e8ff",
        "muted": "rgba(200, 180, 255, 0.55)",
        "accent": "#c060ff",
        "btn_fg": "#ffffff",
        "icon": "✦",
    },
}
