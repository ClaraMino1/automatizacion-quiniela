from flask import Blueprint, render_template, request, current_app, redirect, url_for
import time
import logging
from app.services.quiniela import generar_resultados_horario

logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)

HORARIOS = {
    "LA PREVIA": "10:15",
    "EL PRIMERO": "12:00",
    "MATUTINA": "15:00",
    "VESPERTINA": "18:00",
    "NOCTURNA": "21:00"
}

@bp.route('/')
def index():
    try:
        logger.info("Accediendo a la página principal")
        return render_template('index.html', horarios=HORARIOS.keys())
    except Exception as e:
        logger.error(f"Error en la página principal: {str(e)}")
        return "Error al cargar la página", 500

@bp.route('/generar', methods=['POST'])
def generar():
    try:
        horario = request.form.get('horario')
        logger.info(f"Solicitud de generación para horario: {horario}")

        if not horario:
            logger.warning("No se seleccionó horario")
            # Mejor redirigir a la página principal si no se seleccionó horario
            return redirect(url_for('main.index'))

        request_id = f"{horario}_{int(time.time())}"

        cached_result = current_app.cache.get(request_id)
        if cached_result:
            logger.info("Imagen obtenida del caché")
            return render_template('resultado.html', imagen=cached_result)

        imagenes = generar_resultados_horario(horario)
        if not imagenes:
            logger.error("No se pudieron generar las imágenes")
            return "Error al generar la imagen", 500

        logger.info(f"Imagen generada exitosamente: {imagenes[0]}")

        current_app.cache.set(request_id, imagenes[0])

        from os.path import basename
        return render_template('resultado.html', imagen=basename(imagenes[0]))

    except Exception as e:
        logger.error(f"Error en la generación: {str(e)}")
        return "Error al procesar la solicitud", 500
