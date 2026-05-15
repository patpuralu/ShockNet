@echo off
title ShockNet - Desinstalador Windows
echo.
echo  ⚡ ShockNet - Desinstalador Windows
echo  ======================================
net session >nul 2>&1
if %errorlevel% neq 0 (echo  [ERROR] Ejecuta como Administrador. & pause & exit /b 1)
echo  Parando agente...
taskkill /f /im wscript.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1
echo  Eliminando tarea programada...
schtasks /delete /tn "ShockNetAgent" /f >nul 2>&1
set "VBS=%~dp0..\run_agent.vbs"
if exist "%VBS%" del "%VBS%" >nul 2>&1
echo  ✓ Desinstalacion completada.
echo.
pause
