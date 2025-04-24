import os
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image, ImageDraw, ImageFont
import datetime

# --- Coordenadas ---
coords = {
    "Previa":     {"Ciudad": (225, 336),   "Provincia": (736, 336)},
    "Primero":   {"Ciudad": (225, 566),   "Provincia": (736, 566)},
    "Matutina":  {"Ciudad": (225, 830),   "Provincia": (736, 830)},
    "Vespertina":{"Ciudad": (225, 1065),  "Provincia": (736, 1065)},
    "Nocturna":  {"Ciudad": (225, 1292),  "Provincia": (736, 1292)}
}

def crear_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    chromium_path = os.getenv("CHROMIUM_PATH")
    if chromium_path and os.path.exists(chromium_path):
        options.binary_location = chromium_path

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def generar_resultados():
    driver = crear_driver()

    # --- Ir a la página y esperar ---
    driver.get('https://quesalio.com')
    WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, 'sabatini'))
    )

    # --- Capturar filas de resultados ---
    rows = driver.find_elements(By.CLASS_NAME, 'sabatini')
    print(f"DEBUG: encontré {len(rows)} filas .sabatini")

    city_row = None
    prov_row = None
    for row in rows:
        label = row.find_element(By.TAG_NAME, 'h2').text.strip()
        if label == "Ciudad":
            city_row = row
        elif label == "Provincia":
            prov_row = row

    if not city_row or not prov_row:
        print("ERROR: No encontré filas de Ciudad o Provincia")
        driver.quit()
        return

    # --- Extraer los <p class="c"> de cada fila ---
    city_texts = [p.text.strip() for p in city_row.find_elements(By.CLASS_NAME, 'c')]
    prov_texts = [p.text.strip() for p in prov_row.find_elements(By.CLASS_NAME, 'c')]
    print("DEBUG City texts:", city_texts)
    print("DEBUG Prov texts:", prov_texts)

    # --- Armar datos_numeros: lista de [ciudad, provincia] por zona ---
    datos_numeros = []
    zonas = list(coords.keys())  # ['Previa', 'Primero', ...]
    for i, zona in enumerate(zonas):
        city_val = city_texts[i] if i < len(city_texts) and city_texts[i].isdigit() else ""
        prov_val = prov_texts[i] if i < len(prov_texts) and prov_texts[i].isdigit() else ""
        datos_numeros.append([city_val, prov_val])

    print("DEBUG datos_numeros:", datos_numeros)
    driver.quit()

    # --- Obtener la fecha actual ---
    fecha_actual = datetime.date.today().strftime("%d/%m/%Y")

    # --- Preparar la plantilla de imagen ---
    img = Image.open("plantilla_canva.png")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except IOError:
        font = ImageFont.load_default()

    for zona, (city_num, prov_num) in zip(zonas, datos_numeros):
        draw.text(coords[zona]["Ciudad"], city_num, fill="black", font=font)
        draw.text(coords[zona]["Provincia"], prov_num, fill="black", font=font)

    # --- Dibujar la fecha ---
    draw.text((465, 51), fecha_actual, fill="black", font=font)

    # --- Guardar en static/ para Flask ---
    output_name = "resultado_dia.png"
    os.makedirs("static", exist_ok=True)
    img.save(output_name)
    dest = os.path.join("static", output_name)
    if os.path.exists(dest):
        os.remove(dest)
    os.rename(output_name, dest)

    return output_name

if __name__ == "__main__":
    generar_resultados()