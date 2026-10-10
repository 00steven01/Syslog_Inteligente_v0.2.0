import os
from dotenv import load_dotenv

# Carga las variables definidas en el archivo .env si existe
load_dotenv()

class Config:
    """Configuración base de la aplicación Flask."""
    
    # Clave de seguridad para sesiones web (usar valor por defecto si no existe .env)
    SECRET_KEY = os.getenv('SECRET_KEY', 'clave_por_defecto_segura_alfa')
    
    # Ruta de la base de datos SQLite
    # Se creará un archivo llamado noc_syslog.db en la raíz del proyecto
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 
        f"sqlite:///{os.path.join(BASE_DIR, 'noc_syslog.db')}"
    )
    
    # Desactiva el rastreo de modificaciones de SQLAlchemy para ahorrar memoria
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Lista de comandos permitidos para la consola simulada (solo lectura)
    ALLOWED_COMMAND_PREFIXES = os.getenv('ALLOWLIST_COMMANDS', 'show,get,display').split(',')