@echo off
setlocal EnableDelayedExpansion
title ShockNet - Instalador Windows
echo.
echo  =========================================
echo       ShockNet - Instalador Windows
echo  =========================================
echo.
net session >nul 2>&1
if %errorlevel% neq 0 (echo  [ERROR] Ejecuta como Administrador. & pause & exit /b 1)
set "DIR=%~dp0..\"
set "AGENT=%DIR%agent_run.py"
if not exist "%AGENT%" (echo  [ERROR] No se encuentra agent_run.py & pause & exit /b 1)
echo  [1/3] Buscando Python...
for /f "tokens=*" %%i in ('where python 2^>nul') do (set "PYTHON=%%i" & goto :found)
echo  [ERROR] Python no encontrado. & pause & exit /b 1
:found
echo       Python: %PYTHON%
echo  [2/3] Instalando dependencias...
"%PYTHON%" -m pip install flask requests pillow qrcode pystray cryptography reportlab --quiet > "%DIR%install_log.txt" 2>&1
echo       OK
echo  [3/3] Registrando en inicio de Windows...
set "VBS=%DIR%run_agent.vbs"
(echo Set WshShell = CreateObject^("WScript.Shell"^) & echo WshShell.Run """"%PYTHON%"""" """"%AGENT%"""", 0, False) > "%VBS%"
schtasks /delete /tn "ShockNetAgent" /f >nul 2>&1
schtasks /create /tn "ShockNetAgent" /tr "wscript.exe \"%VBS%\"" /sc ONLOGON /rl HIGHEST /f >nul 2>&1
if %errorlevel% equ 0 (echo       ✓ Tarea creada.) else (echo  [AVISO] Error creando tarea. Ejecuta como Admin.)
echo.
echo  Iniciando agente ahora...
start "" wscript.exe "%VBS%"
timeout /t 2 /nobreak >nul
echo  =========================================
echo   ✓ Instalacion completada.
echo   Arranca automaticamente al iniciar sesion.
echo  =========================================
echo.
pause
