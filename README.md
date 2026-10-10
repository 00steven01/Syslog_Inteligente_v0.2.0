🛡️ NOC Syslog Inteligente - Enterprise Light Edition
Sistema de monitoreo, ingesta y análisis de eventos Syslog multivendor en tiempo real.
📸 Vista Previa del Dashboard

⚡ Opción 1: Ejecución Automática (En un solo comando)
Si deseas realizar la clonación, instalación y arranque de forma automática en un solo paso, abre tu consola o PowerShell y ejecuta:
En Windows (PowerShell / CMD):
git clone https://github.com/00steven01/Syslog_Inteligente_v0.2.0.git; cd Syslog_Inteligente_v0.2.0; pip install -r requirements.txt; python run.py
En Linux / Mac (Bash):
git clone https://github.com/00steven01/Syslog_Inteligente_v0.2.0.git && cd Syslog_Inteligente_v0.2.0 && pip install -r requirements.txt && python run.py
🚀 Opción 2: Guía Detallada Paso a Paso
Si prefieres realizar el procedimiento paso a paso para comprender cada etapa del despliegue local:
Paso 1: Clonar el Repositorio
Abre tu terminal o PowerShell en la carpeta donde deseas guardar el proyecto y descarga el código fuente ejecutando:
git clone https://github.com/00steven01/Syslog_Inteligente_v0.2.0.git
Paso 2: Entrar a la Carpeta del Proyecto
Navega dentro del directorio descargado para tener acceso a los archivos y scripts principales:
cd Syslog_Inteligente_v0.2.0
Paso 3: Instalar las Dependencias con PIP
Instala todas las librerías necesarias de Python (como Flask) mediante el archivo de requerimientos:
pip install -r requirements.txt
Paso 4: Iniciar el Servidor de la Aplicación
Ejecuta el script principal para poner en marcha el servidor web local:
python run.py
🌐 Acceso a la Plataforma
Una vez ejecutado el servidor (Paso 4 u Opción 1), la consola indicará que el servicio está activo. Abre tu navegador de preferencia e ingresa a la siguiente dirección:
👉 http://127.0.0.1:5000
🛠️ Tecnologías Utilizadas
Backend: Python (Flask), SQLite.
Frontend: Bootstrap 5, Chart.js, HTML5/CSS3.
Tema Visual: Enterprise Light Edition.
