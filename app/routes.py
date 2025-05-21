from flask import Flask, render_template, request, send_from_directory, send_file
from app import app, cache
import os
import logging
from app.services.quiniela import generar_resultados_horario
import time

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)





HORARIOS = {
    "LA PREVIA": "10:15",
    "EL PRIMERO": "12:00",
    "MATUTINA": "15:00",
    "VESPERTINA": "18:00",
    "NOCTURNA": "21:00"
}

@app.route('/')
def index():
    try:
        logger.info("Accediendo a la página principal")
        return render_template('index.html', horarios=HORARIOS.keys())
    except Exception as e:
        logger.error(f"Error en la página principal: {str(e)}")
        return "Error al cargar la página", 500

@app.route('/generar', methods=['POST'])
def generar():
    try:
        horario = request.form.get('horario')
        logger.info(f"Solicitud de generación para horario: {horario}")
        
        if not horario:
            logger.warning("No se seleccionó horario")
            return "Por favor seleccione un horario", 400
        
        # Generar un ID único para esta solicitud
        request_id = f"{horario}_{int(time.time())}"
        
        # Intentar obtener del caché primero
        cached_result = cache.get(request_id)
        if cached_result:
            logger.info("Imagen obtenida del caché")
            return render_template('resultado.html', imagen=cached_result)
        
        imagenes = generar_resultados_horario(horario)
        if not imagenes:
            logger.error("No se pudieron generar las imágenes")
            return "Error al generar la imagen", 500

        logger.info(f"Imagen generada exitosamente: {imagenes[0]}")

        # Guardar en caché
        cache.set(request_id, os.path.basename(imagenes[0]))

        # Aquí usá solo el nombre del archivo para que url_for('static', filename=...) funcione bien
        return render_template('resultado.html', imagen=os.path.basename(imagenes[0]))
    except Exception as e:
        logger.error(f"Error en la generación: {str(e)}")
        return "Error al procesar la solicitud", 500

STATIC_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'static'))

@app.route('/static/<path:filename>')
def serve_static(filename):
    try:
        logger.info(f"Sirviendo archivo estático: {filename}")
        return send_from_directory(STATIC_FOLDER, filename)
    except Exception as e:
        logger.error(f"Error al servir archivo estático {filename}: {str(e)}")
        return "Archivo no encontrado", 404



if __name__ == '__main__':
    logger.info("Iniciando aplicación Flask")
    # Asegurarse de que el directorio static existe
    os.makedirs("static", exist_ok=True)
    app.run(debug=True, port=5000)