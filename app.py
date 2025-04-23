import os
from flask import Flask, render_template, redirect, url_for, request
from generate_daily_results import generar_resultados
from generate_schedule_results import generar_resultados_horario

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/resultados_dia', methods=['POST'])
def resultados_dia():
    try:
        filename = generar_resultados()
        return redirect(url_for('mostrar_imagen', nombre_imagen=filename))
    except Exception as e:
        return f"Error al generar los resultados del día: {e}", 500

@app.route('/resultados_horario', methods=['POST'])
def resultados_horario():
    try:
        seleccionado = request.form.get('horario')
        if not seleccionado:
            return "Debes elegir un horario.", 400

        archivos = generar_resultados_horario(seleccionado)
        if not archivos:
            return f"No se generó imagen para «{seleccionado}».", 404

        return render_template('show_images.html', imagenes=archivos)
    except Exception as e:
        return f"Error al generar los resultados por horario: {e}", 500

@app.route('/imagen/<nombre_imagen>')
def mostrar_imagen(nombre_imagen):
    ruta = os.path.join(app.static_folder, nombre_imagen)
    if os.path.exists(ruta):
        return render_template('show_image.html', nombre_imagen=nombre_imagen)
    else:
        return f"Imagen no encontrada: {nombre_imagen}", 404

if __name__ == '__main__':
    app.run(debug=True)
