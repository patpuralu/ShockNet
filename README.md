<div align="center">

<img src="https://github.com/user-attachments/assets/0f76861b-29a4-4273-be4b-7ee407208e2d" width="220" alt="ShockNet Logo">

# ShockNet

Windows • Linux • Android

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square)
![Flask](https://img.shields.io/badge/Flask-Backend-black?style=flat-square)
![Android](https://img.shields.io/badge/Android-APK-green?style=flat-square)
![Status](https://img.shields.io/badge/Status-Activo-red?style=flat-square)

</div>

---

# Descripción

ShockNet es una aplicación de comunicación remota diseñada para funcionar dentro de redes locales. Permite enviar mensajes y mostrar contenido en dispositivos conectados mediante un sistema de agentes receptores.

El proyecto está desarrollado en Python e incluye soporte para:

- Windows
- Linux
- Android (APK)

ShockNet incluye:

- Aplicación principal para PC
- Agente receptor remoto
- Instalador automático
- Sistema de comunicación LAN
- APK Android

---

# Dispositivos compatibles

| Sistema | Compatible |
|---|---|
| Windows | Sí |
| Linux | Sí |
| Android APK | Sí |

---

# Instalación

## Requisitos

Antes de instalar ShockNet necesitas:

- Python 3.11 o superior
- pip
- Conexión en red local

---

# Instalación automática

ShockNet incluye un instalador automático llamado:

```bash
instalador.py
```

El instalador funciona mediante un menú interactivo donde puedes seleccionar distintas opciones.

Opciones disponibles:

- Instalar dependencias
- Configurar agente
- Instalar agente
- Iniciar `shocknet.py`
- Configurar entorno
- Reparar instalación
- Actualizar componentes

El objetivo es facilitar toda la instalación y configuración desde un único menú.

---

## Windows

Es necesario ejecutar la terminal como Administrador.

Abrir una terminal como Administrador y

```bash
python instalador.py
```

O usar directamente:

```bash
install/install_windows.bat
```

---

## Linux

Dar permisos y ejecutar:

```bash
chmod +x install/install_linux.sh
./install/install_linux.sh
```

También puedes usar:

```bash
python instalador.py
```

---

# Cómo usar ShockNet en PC

## Iniciar la aplicación principal

```bash
python shocknet.py
```

La aplicación abrirá la interfaz principal desde donde podrás:

- Gestionar dispositivos
- Enviar mensajes
- Controlar agentes
- Supervisar conexiones

---

## Iniciar el agente receptor

Cada dispositivo receptor debe ejecutar:

```bash
python agent_run.py
```

El agente se encargará de:

- Recibir mensajes
- Mostrar alertas
- Mantener conexión con ShockNet
- Ejecutarse dentro de la red local

---

# APK Android

El proyecto incluye una versión Android en formato APK.

Archivo incluido:

```bash
ShockNet.apk
```

---

# Cómo instalar la APK en el móvil

Puedes descargar e instalar directamente la APK desde Android:

[Descargar ShockNet APK](https://github.com/patpuralu/ShockNet/blob/main/ShockNet.apk)

## Instalación

1. Abrir el enlace desde el móvil
2. Descargar `ShockNet.apk`
3. Permitir instalación desde orígenes desconocidos
4. Instalar la aplicación
5. Abrir ShockNet

---

# Funcionamiento

ShockNet funciona mediante comunicación en red local.

La aplicación principal envía información a los agentes conectados.

Los agentes receptores:

- Escuchan conexiones
- Reciben mensajes
- Ejecutan acciones visuales
- Mantienen comunicación dentro de la LAN

---

# Estructura del proyecto

```bash
ShockNet/
│
├── shocknet.py
├── agent_run.py
├── instalador.py
├── ShockNet.apk
│
├── core/
│   ├── agent.py
│   ├── config.py
│   ├── crypto_utils.py
│   ├── kiosk.py
│   └── stats.py
│
├── install/
│   ├── install_linux.sh
│   ├── install_windows.bat
│   ├── uninstall_linux.sh
│   └── uninstall_windows.bat
│
└── mobile/
```

---

# Tecnologías utilizadas

| Tecnología | Uso |
|---|---|
| Python | Backend principal |
| Flask | Servidor del agente |
| Tkinter | Interfaz gráfica |
| Requests | Comunicación HTTP |
| Cryptography | Seguridad |
| Android Java | Aplicación móvil |

---

# Seguridad

ShockNet utiliza autenticación y comunicación protegida para el intercambio de datos dentro de la red local.

El proyecto está orientado a:

- Entornos privados
- Redes LAN
- Uso educativo
- Automatización local

---

# Licencia

Creative Commons Attribution-NonCommercial 4.0 International

Uso permitido únicamente para fines no comerciales.

