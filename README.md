# ⚡ ShockNet v1

> Plataforma visual de mensajería remota y notificaciones en red local con interfaz cyberpunk, agente receptor y estadísticas integradas.

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.x-black?style=for-the-badge&logo=flask)
![Status](https://img.shields.io/badge/Status-Active-red?style=for-the-badge)

---

# 🚀 Descripción

**ShockNet** es una plataforma de mensajería visual y comunicación remota diseñada para redes locales. Permite enviar mensajes, alertas y contenido visual a dispositivos conectados mediante un sistema de agentes receptores.

El proyecto está enfocado en:

- ⚡ Comunicación rápida dentro de la LAN
- 🖥️ Interfaces visuales modernas
- 🔐 Comunicación segura
- 📊 Registro y estadísticas
- 🎨 Personalización mediante temas
- 📱 Compatibilidad con Android

ShockNet combina una aplicación principal en Python con agentes receptores que muestran mensajes en tiempo real usando una interfaz moderna y configurable.

Además, el proyecto incluye una base Android desarrollada con Java para futuras integraciones móviles.

---

# ✨ Características

## 🧠 Interfaz moderna

- UI construida con **Tkinter**
- Diseño oscuro estilo terminal/cyberpunk
- Sidebar interactivo
- Componentes personalizados
- Navegación modular

## 🌐 Sistema de agentes

Cada dispositivo ejecuta un agente receptor basado en **Flask** que permite:

- Recibir mensajes remotos
- Mostrar interfaces HTML dinámicas
- Ejecutar modo kiosko
- Registrar actividad
- Validar autenticación

## 🔐 Seguridad

ShockNet incorpora:

- Cifrado AES para payloads
- Tokens de autenticación
- Configuración centralizada
- Comunicación segura dentro de la LAN

## 📊 Estadísticas y reportes

- Historial de mensajes
- Exportación CSV
- Exportación PDF
- Métricas básicas
- Registro de actividad

## 🎨 Temas visuales

Sistema de temas integrado:

- Cyber
- Neon
- Dark
- Red Alert
- Variantes personalizadas

---

# 🗂️ Estructura del proyecto

```bash
ShockNet_v1/
│
├── shocknet.py              # Aplicación principal
├── agent_run.py             # Inicializador del agente
├── requirements.txt         # Dependencias
├── instalador.py            # Instalador automático
│
├── core/
│   ├── agent.py             # Servidor Flask receptor
│   ├── config.py            # Configuración global
│   ├── crypto_utils.py      # Utilidades AES
│   ├── kiosk.py             # Modo kiosko
│   └── stats.py             # Estadísticas y exportación
│
├── install/
│   ├── install_linux.sh
│   ├── install_windows.bat
│   ├── uninstall_linux.sh
│   └── uninstall_windows.bat
│
├── mobile/
│   └── apk/                 # Base Android
│
└── templates.json
```

---

# ⚙️ Instalación

## 📌 Requisitos

- Python 3.11+
- pip
- Red local activa

---

## 🪟 Windows

```bash
install/install_windows.bat
```

---

## 🐧 Linux

```bash
chmod +x install/install_linux.sh
./install/install_linux.sh
```

---

## 📦 Instalación manual

### Clonar repositorio

```bash
git clone https://github.com/tuusuario/shocknet.git
cd shocknet
```

---

### Instalar dependencias

```bash
pip install -r requirements.txt
```

Dependencias principales:

- Flask
- Requests
- Pillow
- QRCode
- PyStray
- Cryptography
- ReportLab

---

## ⚡ Instalador automático

El proyecto incluye un archivo `instalador.py` compatible con Windows y Linux que automatiza la instalación y configuración inicial.

```bash
python instalador.py
```

Este instalador:

- Instala dependencias necesarias
- Configura el entorno
- Prepara archivos del sistema
- Facilita la primera ejecución

---

# ▶️ Uso

## Iniciar ShockNet

```bash
python shocknet.py
```

---

## Ejecutar agente receptor

```bash
python agent_run.py
```

---

# 🧩 Tecnologías utilizadas

| Tecnología | Uso |
|---|---|
| Python | Backend principal |
| Flask | Servidor del agente |
| Tkinter | Interfaz gráfica |
| Cryptography | Cifrado AES |
| ReportLab | Exportación PDF |
| Requests | Comunicación HTTP |
| QRCode | Generación QR |

---

# 🔐 Seguridad

ShockNet utiliza cifrado AES para proteger la transmisión de datos y soporta autenticación mediante tokens.

> Este proyecto está pensado para entornos educativos, pruebas locales y automatización dentro de redes privadas.

---

# 📸 Vista general

## Panel principal

- Gestión de mensajes
- Historial
- Scanner de red
- Estadísticas
- Temas visuales

## Agente receptor

- Interfaz HTML dinámica
- Modo fullscreen
- Visualización de alertas
- Sistema de lectura de mensajes

---

# 📈 Posibles mejoras futuras

- 🔥 Dashboard web completo
- 📱 APK Android funcional
- ☁️ Comunicación cloud
- 🧠 IA para automatización
- 🔔 Notificaciones push
- 🛰️ Descubrimiento automático de dispositivos
- 👥 Multiusuario
- 🗃️ Base de datos integrada

---

# 🤝 Contribuciones

Las contribuciones son bienvenidas.

Puedes colaborar mediante:

- Pull Requests
- Reportes de bugs
- Nuevas funcionalidades
- Mejoras visuales
- Optimización de red

---

# 📄 Licencia

Este proyecto se distribuye bajo licencia MIT.

---

# 👨‍💻 Autor

**ShockNet v1**

Desarrollado como proyecto de automatización y comunicación visual en red local.

---

# ⭐ Support

Si te gusta el proyecto:

- Dale una estrella ⭐
- Compártelo
- Contribuye al desarrollo

---

# ⚡ ShockNet

> "Fast local messaging. Cyber control. Visual impact."

****
