import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image, ImageDraw, ImageFont

# --- Coords---
coords = {
    "Previa":    {"Ciudad": (250, 350),   "Provincia": (770, 350)},
    "Primero":   {"Ciudad": (250, 600),   "Provincia": (770, 600)},
    "Matutina":  {"Ciudad": (250, 850),   "Provincia": (770, 850)},
    "Vespertina":{"Ciudad": (250, 1080),  "Provincia": (770, 1080)},
    "Nocturna":  {"Ciudad": (250, 1300),  "Provincia": (770, 1300)}
}

def generar_resultados():
    # --- Inicializar Selenium en modo headless ---
    service = Service('./chromedriver.exe')
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(service=service, options=options)

    # --- Ir a la página y esperar ---
    driver.get('https://quesalio.com')
    WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, 'sabatini'))
    )

    # --- Capturar filas de resultados ---
    rows = driver.find_elements(By.CLASS_NAME, 'sabatini')
    print(f"DEBUG: encontré {len(rows)} filas .sabatini")

    # --- Buscar las filas de Ciudad y Provincia ---
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

    # --- Preparar la plantilla de imagen ---
    img = Image.open("plantilla_canva.png")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except IOError:
        font = ImageFont.load_default()

    # --- Dibujar números en cada zona ---
    for zona, (city_num, prov_num) in zip(zonas, datos_numeros):
        draw.text(coords[zona]["Ciudad"], city_num, fill="black", font=font)
        draw.text(coords[zona]["Provincia"], prov_num, fill="black", font=font)

    # --- Guardar en static/ para Flask ---
    output_name = "resultado_dia.png"
    img.save(output_name)
    dest = os.path.join("static", output_name)
    if os.path.exists(dest):
        os.remove(dest)
    os.rename(output_name, dest)

    return output_name

if __name__ == "__main__":
    generar_resultados()
