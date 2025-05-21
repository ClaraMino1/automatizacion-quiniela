import os
import logging
from flask import Flask
from flask_caching import Cache
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Crear directorio logs si no existe
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

cache = Cache()

def create_app():
    app = Flask(__name__)

    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev'),
        CHROMIUM_PATH=os.getenv('CHROMIUM_PATH'),
        CACHE_TYPE='simple',
        CACHE_DEFAULT_TIMEOUT=300
    )

    cache.init_app(app)

    # Importar y registrar blueprint
    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    # Hacer accesible la caché vía app.cache (opcional)
    app.cache = cache

    return app
