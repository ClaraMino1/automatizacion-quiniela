from flask import Flask, send_file
from generar_imagenes import ejecutar

app = Flask(__name__)

@app.route('/generar', methods=['GET'])
def generar():
    archivos_generados = ejecutar()
    return send_file(archivos_generados[-1], mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
