from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from PIL import Image, ImageDraw, ImageFont
import time
import os

def ejecutar():
    resultados_por_horario_provincia = {}
    horarios_esperados = ["10:15", "12:00", "15:00", "18:00", "21:00"]
    provincias_deseadas = ["Ciudad", "Provincia", "Santa Fe", "Córdoba", "Entre Ríos"]

    # Configuración de Selenium
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    service = Service('/usr/bin/chromedriver')  # En Render puede cambiar la ruta

    driver = webdriver.Chrome(service=service, options=options)
    driver.get('https://quesalio.com')
    time.sleep(5)

    try:
        fila_horarios = driver.find_element(By.XPATH, '//div[@class="x mar3"]')
        elementos_horario = fila_horarios.find_elements(By.CLASS_NAME, 'col.s2.m2.carobravo')
        horarios_encontrados = [h.text.strip() for h in elementos_horario if h.text.strip() in horarios_esperados]

        bloques_provincias = driver.find_elements(By.XPATH, '//div[@class="col s12 agui"]/div[@class="col s12 sabatini"]')

        for i, horario in enumerate(horarios_encontrados):
            resultados_horario = {}
            for bloque_provincia in bloques_provincias:
                try:
                    titulo_provincia_elemento = bloque_provincia.find_element(By.XPATH, './/div[@class="col s2 m2 l2 kk9"]/h2[@class="truncate b"]')
                    titulo_provincia = titulo_provincia_elemento.text.strip()
                    if titulo_provincia in provincias_deseadas:
                        elementos_numeros = bloque_provincia.find_elements(By.CLASS_NAME, 'col.s2.m2')
                        if len(elementos_numeros) > i + 1:
                            primer_numero = elementos_numeros[i + 1].text.strip()
                            if primer_numero:
                                resultados_horario[titulo_provincia] = [primer_numero]
                except Exception:
                    continue
            if resultados_horario:
                resultados_por_horario_provincia[horario] = resultados_horario

    finally:
        driver.quit()

    nombres_para_mostrar = {
        "10:15": "LA PREVIA",
        "12:00": "EL PRIMERO",
        "15:00": "MATUTINA",
        "18:00": "VESPERTINA",
        "21:00": "NOCTURNA"
    }

    resultados_formateados = {
        nombres_para_mostrar.get(h, h): r for h, r in resultados_por_horario_provincia.items()
    }

    try:
        fuente = ImageFont.truetype("Pragmatica-Condensed-Bold.ttf", 100)
    except IOError:
        fuente = ImageFont.load_default()

    coordenadas_texto = {
        "Ciudad": [(657, 800)],
        "Provincia": [(657, 976)],
        "Córdoba": [(657, 1156)],
        "Santa Fe": [(657, 1352)],
        "Entre Ríos": [(657, 1548)],
    }

    archivos_generados = []

    for horario_formateado, resultados in resultados_formateados.items():
        horario_para_archivo = horario_formateado.replace(" ", "_").replace(":", "_").lower()
        nombre_archivo_plantilla = f"plantilla_{horario_para_archivo}.png"
        nombre_archivo_resultado = f"resultado_{horario_para_archivo}.png"

        if not os.path.exists(nombre_archivo_plantilla):
            continue

        plantilla = Image.open(nombre_archivo_plantilla)
        draw = ImageDraw.Draw(plantilla)
        draw.text((292, 506), horario_formateado, fill="white", font=fuente)

        for provincia, numeros in resultados.items():
            if provincia in coordenadas_texto and numeros:
                x, y = coordenadas_texto[provincia][0]
                draw.text((x, y), numeros[0], fill="white", font=fuente)

        plantilla.save(nombre_archivo_resultado)
        archivos_generados.append(nombre_archivo_resultado)

    return archivos_generados
