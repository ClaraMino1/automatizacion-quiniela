from flask import Flask
from flask_caching import Cache
import logging
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Crear directorio de logs si no existe
os.makedirs('logs', exist_ok=True)

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'app.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Inicializar Flask
app = Flask(__name__)

# Configuración de la aplicación
app.config.update(
    SECRET_KEY=os.getenv('SECRET_KEY', 'dev'),
    CHROMIUM_PATH=os.getenv('CHROMIUM_PATH'),
    CACHE_TYPE='simple',
    CACHE_DEFAULT_TIMEOUT=300  # 5 minutos
)

# Inicializar caché
cache = Cache(app)

# Importar rutas después de crear la app para evitar importaciones circulares
from app import routes