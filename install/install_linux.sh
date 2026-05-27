#!/usr/bin/env bash
set -e
echo ""
echo " ShockNet - Instalador Linux"
echo " ================================="
[[ $EUID -ne 0 ]] && echo " [ERROR] Ejecuta con sudo" && exit 1
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON=$(which python3); USER_NAME="${SUDO_USER:-$(logname)}"
echo " Agente  : $DIR/agent_run.py"
echo " Usuario : $USER_NAME"
echo ""
echo " [1/3] Instalando dependencias..."
pip3 install flask requests pillow qrcode pystray cryptography reportlab \
    --break-system-packages -q \
    || pip3 install flask requests pillow qrcode pystray cryptography reportlab -q
echo "       OK"
echo " [2/3] Creando servicio systemd..."
cat > /etc/systemd/system/shocknet-agent.service << SVC
[Unit]
Description=ShockNet Agent
After=network.target graphical.target
[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$DIR
ExecStart=$PYTHON $DIR/agent_run.py
Restart=on-failure
RestartSec=5
Environment=DISPLAY=:0
StandardOutput=journal
StandardError=journal
[Install]
WantedBy=multi-user.target
SVC
echo " [3/3] Activando..."
systemctl daemon-reload
systemctl enable shocknet-agent --quiet
systemctl start  shocknet-agent
sleep 1
[[ $(systemctl is-active shocknet-agent) == "active" ]] \
    && echo " ✓ Instalado y activo." \
    || echo " [AVISO] Revisar: journalctl -u shocknet-agent -n 20"
echo ""
