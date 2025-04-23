import os
import shutil
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from PIL import Image, ImageDraw, ImageFont

def generar_resultados_horario(selected_horario=None):
    # 1. Iniciar driver
    service = Service('./chromedriver.exe')
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(service=service, options=options)

    # 2. Scraping
    driver.get('https://quesalio.com')
    time.sleep(5)

    resultados_por_horario_provincia = {}
    horarios_esperados = ["10:15", "12:00", "15:00", "18:00", "21:00"]
    provincias_deseadas = ["Ciudad", "Provincia", "Santa Fe", "Córdoba", "Entre Ríos"]

    try:
        fila = driver.find_element(By.XPATH, '//div[@class="x mar3"]')
        elementos = fila.find_elements(By.CLASS_NAME, 'col.s2.m2.carobravo')
        horarios = [h.text.strip() for h in elementos if h.text.strip() in horarios_esperados]

        bloques = driver.find_elements(
            By.XPATH, '//div[@class="col s12 agui"]/div[@class="col s12 sabatini"]'
        )
        for idx, hora in enumerate(horarios):
            datos_h = {}
            for bloque in bloques:
                try:
                    prov = bloque.find_element(
                        By.XPATH, './/div[@class="col s2 m2 l2 kk9"]/h2'
                    ).text.strip()
                    if prov in provincias_deseadas:
                        nums = bloque.find_elements(By.CLASS_NAME, 'col.s2.m2')
                        if len(nums) > idx+1 and nums[idx+1].text.strip():
                            datos_h[prov] = nums[idx+1].text.strip()
                except:
                    pass
            if datos_h:
                resultados_por_horario_provincia[hora] = datos_h
    finally:
        driver.quit()

    # 3. Mapear nombres
    mostrar = {
        "10:15": "LA PREVIA",
        "12:00": "EL PRIMERO",
        "15:00": "MATUTINA",
        "18:00": "VESPERTINA",
        "21:00": "NOCTURNA"
    }
    formateados = {
        mostrar[h]: d
        for h, d in resultados_por_horario_provincia.items()
    }

    # 4. Filtrar solo el elegido (si se pasó)
    if selected_horario:
        formateados = {
            k: v for k, v in formateados.items()
            if k == selected_horario
        }

    # 5. Fuente y coordenadas
    try:
        font = ImageFont.truetype("Pragmatica-Condensed-Bold.ttf", 100)
    except IOError:
        font = ImageFont.load_default()

    coords = {
        "Ciudad": (657, 800),
        "Provincia": (657, 976),
        "Córdoba": (657, 1156),
        "Santa Fe": (657, 1352),
        "Entre Ríos": (657, 1548),
    }

    generados = []
    for titulo, datos in formateados.items():
        slug = titulo.replace(' ', '_').lower()
        plantilla = f"plantilla_{slug}.png"
        salida = f"resultado_{slug}.png"

        if not os.path.exists(plantilla):
            continue

        img = Image.open(plantilla)
        draw = ImageDraw.Draw(img)
        draw.text((292, 506), titulo, fill="white", font=font)
        for prov, num in datos.items():
            x, y = coords[prov]
            draw.text((x, y), num, fill="white", font=font)

        img.save(salida)
        shutil.copy(salida, os.path.join("static", salida))
        generados.append(salida)

    return generados
