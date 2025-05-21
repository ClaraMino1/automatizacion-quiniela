from app import app
import logging

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info("Iniciando aplicación Flask")
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True
    ) 