import os
import shutil
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image, ImageDraw, ImageFont


def crear_driver_headless():
    # Opciones para Chrome en modo headless
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    # webdriver_manager para obtener chromedriver adecuado
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    chromium_path = os.getenv("CHROMIUM_PATH")

    if chromium_path and os.path.exists(chromium_path):
        driver.options.binary_location = chromium_path
        print(f"DEBUG: Forcing Chromium binary location to: {driver.options.binary_location}")

    return driver

    


def generar_resultados_horario(selected_horario=None):
    # 1. Iniciar driver en modo headless
    driver = crear_driver_headless()

    # 2. Scraping
    driver.get('https://quesalio.com')
    time.sleep(5)

    resultados = {}
    horarios_esperados = ["10:15", "12:00", "15:00", "18:00", "21:00"]
    provincias = ["Ciudad", "Provincia", "Santa Fe", "Córdoba", "Entre Ríos"]

    try:
        fila = driver.find_element(By.XPATH, '//div[@class="x mar3"]')
        elementos = fila.find_elements(By.CLASS_NAME, 'carobravo')
        horarios = [h.text.strip() for h in elementos if h.text.strip() in horarios_esperados]

        bloques = driver.find_elements(
            By.XPATH,
            '//div[@class="col s12 agui"]/div[@class="col s12 sabatini"]'
        )
        for idx, hora in enumerate(horarios):
            datos_h = {}
            for bloque in bloques:
                try:
                    prov = bloque.find_element(
                        By.XPATH, './/div[contains(@class,"kk9")]/h2'
                    ).text.strip()
                except:
                    continue
                if prov in provincias:
                    nums = bloque.find_elements(By.CLASS_NAME, 'c')
                    if idx < len(nums):
                        texto = nums[idx].text.strip()
                        if texto.isdigit():
                            datos_h[prov] = texto
            if datos_h:
                resultados[hora] = datos_h
    finally:
        driver.quit()

    # 3. Traducir horarios a títulos
    mapping = {
        "10:15": "LA PREVIA",
        "12:00": "EL PRIMERO",
        "15:00": "MATUTINA",
        "18:00": "VESPERTINA",
        "21:00": "NOCTURNA"
    }
    formateados = {mapping[h]: d for h, d in resultados.items()}

    # 4. Filtrar horario específico si se indicó
    if selected_horario:
        formateados = {k: v for k, v in formateados.items() if k == selected_horario}

    # 5. Carga de fuentes y coordenadas
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
            x, y = coords.get(prov, (0, 0))
            draw.text((x, y), num, fill="white", font=font)

        img.save(salida)
        os.makedirs("static", exist_ok=True)
        shutil.copy(salida, os.path.join("static", salida))
        generados.append(salida)

    return generados


if __name__ == '__main__':
    print(generar_resultados_horario())