import os
import shutil
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from PIL import Image, ImageDraw, ImageFont

def crear_driver_headless():
    # Ruta al chromedriver y chromium instalados en Linux (Render)
    chromedriver_path = "/usr/bin/chromedriver"
    chromium_path = "/usr/bin/chromium"

    options = webdriver.ChromeOptions()
    options.binary_location = chromium_path
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    service = Service(executable_path=chromedriver_path)
    return webdriver.Chrome(service=service, options=options)

def generar_resultados_horario(selected_horario=None):
    # 1. Iniciar driver usando la configuración headless adecuada
    driver = crear_driver_headless()

    # 2. Scraping
    driver.get('https://quesalio.com')
    time.sleep(5)

    resultados_por_horario_provincia = {}
    horarios_esperados = ["10:15", "12:00", "15:00", "18:00", "21:00"]
    provincias_deseadas = ["Ciudad", "Provincia", "Santa Fe", "Córdoba", "Entre Ríos"]

    try:
        fila = driver.find_element(By.XPATH, '//div[@class="x mar3"]')
        elementos = fila.find_elements(By.CLASS_NAME, 'carobravo')
        horarios = [h.text.strip() for h in elementos if h.text.strip() in horarios_esperados]

        bloques = driver.find_elements(
            By.XPATH, '//div[@class="col s12 agui"]/div[@class="col s12 sabatini"]'
        )
        for idx, hora in enumerate(horarios):
            datos_h = {}
            for bloque in bloques:
                try:
                    prov = bloque.find_element(
                        By.XPATH, './/div[contains(@class,"kk9")]/h2'
                    ).text.strip()
                    if prov in provincias_deseadas:
                        nums = bloque.find_elements(By.CLASS_NAME, 'c')
                        # Cada nums[i] corresponde a la columna del horario
                        if idx < len(nums) and nums[idx].text.strip().isdigit():
                            datos_h[prov] = nums[idx].text.strip()
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
        formateados = {k: v for k, v in formateados.items() if k == selected_horario}

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

if __name__ == '__main__':
    print(generar_resultados_horario())
