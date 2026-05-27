#!/usr/bin/env bash
set -e
echo ""
echo "  ShockNet - Desinstalador Linux"
echo " ===================================="
[[ $EUID -ne 0 ]] && echo " [ERROR] Ejecuta con sudo" && exit 1
systemctl is-active  --quiet shocknet-agent 2>/dev/null && systemctl stop    shocknet-agent && echo " ✓ Servicio parado."
systemctl is-enabled --quiet shocknet-agent 2>/dev/null && systemctl disable shocknet-agent --quiet && echo " ✓ Arranque desactivado."
[[ -f /etc/systemd/system/shocknet-agent.service ]] && rm -f /etc/systemd/system/shocknet-agent.service && systemctl daemon-reload && echo " ✓ Archivo de servicio eliminado."
echo ""
echo " ✓ Desinstalacion completada."
echo " Los archivos del proyecto NO se han borrado."
echo ""
