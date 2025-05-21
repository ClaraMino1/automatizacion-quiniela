import os
import shutil
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image, ImageDraw, ImageFont

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Directorio base del script (ej. d:\\proyectos\\automatizacion_quiniela\\app\\services\\)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logger.info(f"BASE_DIR (ubicación del script): {BASE_DIR}")

# Directorio donde se encuentran las plantillas
# Desde BASE_DIR (app/services), subimos dos niveles (../../) y entramos en 'resources/templates'

TEMPLATES_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', '..', 'resources', 'templates'))
logger.info(f"TEMPLATES_DIR (ubicación de plantillas): {TEMPLATES_DIR}")

# Directorio donde se guardarán las imágenes generadas.
# Desde BASE_DIR (app/services), subimos dos niveles (../../) y luego entramos en 'static'
STATIC_OUTPUT_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', '..', 'static'))
logger.info(f"STATIC_OUTPUT_DIR (ubicación de salida de imágenes): {STATIC_OUTPUT_DIR}")


def crear_driver_headless():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1000")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-javascript")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    options.add_argument("--silent")

    chromium_path = os.getenv("CHROMIUM_PATH")
    if chromium_path and os.path.exists(chromium_path):
        options.binary_location = chromium_path
        logger.info(f"Usando Chrome en: {chromium_path}")
    else:
        logger.warning("Variable de entorno CHROMIUM_PATH no definida o ruta no válida. Usando ChromeDriverManager.")

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        logger.info("Driver de Chrome creado exitosamente.")
        return driver
    except Exception as e:
        logger.error(f"Error al crear el driver de Chrome: {e}")
        return None

def generar_resultados_horario(selected_horario=None):
    logger.info(f"Generando resultados para horario: {selected_horario if selected_horario else 'todos'}")
    driver = crear_driver_headless()
    if driver is None:
        return []

    try:
        logger.info("Navegando a https://quesalio.com")
        driver.get('https://quesalio.com')
        time.sleep(3) 

        wait = WebDriverWait(driver, 20)

        logger.info("Esperando elementos carobravo...")
        elems = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.carobravo')))
        logger.info(f"Elementos carobravo encontrados: {len(elems)}")
        
        horarios_esperados = ["10:15", "12:00", "15:00", "18:00", "21:00"]
        horarios = [e.text.strip() for e in elems if e.text.strip() in horarios_esperados]
        if not horarios:
            logger.warning("No se detectaron horarios esperados en la página.")
            return []
        logger.info(f"Horarios detectados: {horarios}")

        logger.info("Esperando rows de resultados sabatini...")
        rows = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.sabatini')))
        logger.info(f"Rows sabatini encontradas: {len(rows)}")

        prov_data = {}
        for row in rows:
            try:
                label_elem = row.find_element(By.CSS_SELECTOR, 'h2')
                label = label_elem.text.strip()
                nums = [p.text.strip() for p in row.find_elements(By.CSS_SELECTOR, '.c')]
                if label and nums:
                    prov_data[label] = nums
                else:
                    logger.warning(f"Fila sabatini sin label o números: {row.text}")
            except Exception as e:
                logger.warning(f"Error al procesar una fila sabatini: {e}. Fila: {row.text}")
                continue
        logger.info(f"Datos por provincia recolectados: {list(prov_data.keys())}")

        resultados = {}
        provincias = ["Ciudad", "Provincia", "Santa Fe", "Córdoba", "Entre Ríos"]
        for idx, hora in enumerate(horarios):
            datos_h = {}
            for prov in provincias:
                nums = prov_data.get(prov, [])
                if idx < len(nums) and nums[idx].isdigit():
                    datos_h[prov] = nums[idx]
                else:
                    logger.warning(f"Dato faltante o no numérico para {prov} en horario {hora} (índice {idx}). Datos disponibles: {nums}")
            if datos_h:
                resultados[hora] = datos_h
            else:
                logger.warning(f"No se recolectaron datos para el horario {hora}.")
        logger.info(f"Resultados crudos: {resultados}")

    except Exception:
        logger.exception("Error durante scraping de horarios. No se pudieron obtener los datos.")
        return []
    finally:
        driver.quit()
        logger.info("Driver de Chrome cerrado.")

    mapping = {
        "10:15": "LA PREVIA",
        "12:00": "EL PRIMERO",
        "15:00": "MATUTINA",
        "18:00": "VESPERTINA",
        "21:00": "NOCTURNA"
    }
    formateados = {mapping[h]: d for h, d in resultados.items() if h in mapping}
    if selected_horario:
        formateados = {k: v for k, v in formateados.items() if k == selected_horario}
    
    if not formateados:
        logger.warning("No hay resultados formateados para generar imágenes.")
        return []

    logger.info(f"Resultados formateados para generación de imágenes: {formateados}")

    try:
        # ¡CAMBIO CLAVE AQUÍ!
        # La fuente ahora se busca subiendo dos niveles desde BASE_DIR y entrando en 'resources/fonts/'
        font_path = os.path.join(BASE_DIR, '..', '..', 'resources', 'fonts', "Pragmatica-Condensed-Bold.ttf")
        
        if os.path.exists(font_path):
            font = ImageFont.truetype(font_path, 100) # Tamaño de fuente inicial (puedes ajustarlo)
            logger.info(f"Fuente cargada exitosamente desde: {font_path} con tamaño 250.")
        else:
            logger.warning(f"Archivo de fuente NO ENCONTRADO en: {font_path}. Usando fuente por defecto. Asegúrate de que la ruta sea correcta.")
            font = ImageFont.load_default()
    except IOError as e:
        logger.error(f"Error de I/O al cargar la fuente TrueType: {e}. Usando fuente por defecto.", exc_info=True)
        font = ImageFont.load_default()

    coords = {
        "Ciudad": (657, 800),
        "Provincia": (657, 976),
        "Córdoba": (657, 1156),
        "Santa Fe": (657, 1352),
        "Entre Ríos": (657, 1548),
    }
    
    generados = []
    # Crear el directorio de salida 'static' si no existe
    os.makedirs(STATIC_OUTPUT_DIR, exist_ok=True)
    logger.info(f"Asegurado que el directorio de salida existe en: {STATIC_OUTPUT_DIR}")

    for titulo, datos in formateados.items():
        slug = titulo.replace(' ', '_').lower()
        
        # La plantilla se busca con el prefijo "resultado_"
        # dentro del directorio TEMPLATES_DIR.
        plantilla_filename = f"plantilla_{slug}.png"
        plantilla_path = os.path.join(TEMPLATES_DIR, plantilla_filename)
        
        # El archivo de salida se guarda en STATIC_OUTPUT_DIR con el mismo nombre.
        salida_final_path = os.path.join(STATIC_OUTPUT_DIR, plantilla_filename) 
        

        if not os.path.exists(plantilla_path):
            logger.error(f"Plantilla faltante: {plantilla_path}. No se generará la imagen para {titulo}. Por favor, asegúrate que la plantilla existe y se llama '{plantilla_filename}'.")
            continue
            
        try:
            logger.info(f"Cargando plantilla: {plantilla_path}")
            img = Image.open(plantilla_path)
            draw = ImageDraw.Draw(img)
            
            draw.text((292, 506), titulo, fill="white", font=font)
            logger.info(f"Dibujado título '{titulo}' en la imagen.")
            
            for prov, num in datos.items():
                x, y = coords.get(prov, (None, None))
                if x is not None and y is not None:
                    draw.text((x, y), num, fill="white", font=font)
                    logger.info(f"Dibujado {num} para {prov} en ({x}, {y}).")
                else:
                    logger.warning(f"Coordenadas no definidas para la provincia: {prov}")
            
            logger.info(f"Guardando imagen final en: {salida_final_path}")
            # Guardamos la imagen directamente en el directorio 'static'
            img.save(salida_final_path, optimize=True, quality=95)
            logger.info(f"Imagen generada exitosamente en: {salida_final_path}")
            generados.append(os.path.basename(salida_final_path))

        except FileNotFoundError:
            logger.error(f"Error FileNotFoundError: El archivo {plantilla_path} no fue encontrado. Esto sugiere que la plantilla no existe o está mal nombrada.", exc_info=True)
        except IOError as e:
            logger.error(f"Error de I/O al guardar la imagen {salida_final_path}: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Error inesperado al procesar la imagen para {titulo}: {e}", exc_info=True)

    return generados

if __name__ == '__main__':
    generated_files = generar_resultados_horario()
    if generated_files:
        print(f"Archivos generados en el directorio static: {generated_files}")
    else:
        print("No se generaron archivos de resultados.")