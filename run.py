from app import create_app
import logging

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info("Iniciando aplicación Flask")
    app = create_app()
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True
    )
