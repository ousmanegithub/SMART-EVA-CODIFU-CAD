import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import osmnx as ox
import geopandas as gpd
import pandas as pd
from django.conf import settings
from .geo_utils import find_closest_road_point, calculate_heading, calculate_adjusted_view
STREET_VIEW_EXCEL = os.path.join(settings.MEDIA_ROOT, 'street_view_links.xlsx')
STREET_VIEW_FOLDER = os.path.join(settings.MEDIA_ROOT, 'street_view_images')
os.makedirs(STREET_VIEW_FOLDER, exist_ok=True)

def initialize_driver():
    """ Démarre Selenium pour capturer Google Street View """
    try:
        options = Options()
        options.add_argument("--headless")
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)
    except Exception as e:
        raise RuntimeError(f"❌ Erreur lors de l'initialisation de Selenium : {e}")

def open_street_view(driver, lat, lon, heading):
    """ Ouvre Street View et retourne le lien de la vue """
    street_view_url = f'https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}&heading={heading}'
    driver.get(street_view_url)
    time.sleep(2)  # Laisser charger
    return street_view_url

def capture_and_save_screenshot(driver, image_path):
    """ Capture une capture d'écran et l'enregistre """
    temp_path = image_path.replace('.png', '_temp.png')
    driver.save_screenshot(temp_path)
    image = Image.open(temp_path)
    width, height = image.size
    crop_area = (0, int(height * 0.15), width, int(height * 0.85))
    cleaned_image = image.crop(crop_area)
    cleaned_image.save(image_path)
    os.remove(temp_path)

def process_street_view(gdf, roads):
    """ Génère et enregistre les images Street View des façades des parcelles """
    print(f"Début de process_street_view avec {len(gdf)} parcelles")
    driver = initialize_driver()
    results = []

    for idx, row in gdf.iterrows():
        try:
            print(f"Traitement de la parcelle {idx} : nicad={row.get('nicad', 'N/A')}, lat={row['latitude']}, lon={row['longitude']}")
            closest_road = find_closest_road_point(row.geometry, roads)
            if not closest_road:
                print(f"Pas de route proche pour la parcelle {idx}")
                continue

            heading = calculate_heading(closest_road.x, closest_road.y, row["longitude"], row["latitude"])
            lon_adjusted, lat_adjusted = calculate_adjusted_view(closest_road.x, closest_road.y, heading)

            street_view_url = open_street_view(driver, lat_adjusted, lon_adjusted, heading)
            if street_view_url:
                image_filename = f'parcelle_{row["nicad"] if "nicad" in row else idx}.png'
                image_path = os.path.join(STREET_VIEW_FOLDER, image_filename)
                capture_and_save_screenshot(driver, image_path)
                results.append({
                    "nicad": row["nicad"] if "nicad" in row else f"parcelle_{idx}",
                    "image_path": image_path,
                    "street_view_url": street_view_url
                })
                print(f"Image et lien générés pour {row.get('nicad', idx)} : {street_view_url}")
        except Exception as e:
            print(f"❌ Erreur pour la parcelle {idx} : {e}")

    driver.quit()


    if results:
        df = pd.DataFrame(results)
        print(f"Saving Street View links to: {STREET_VIEW_EXCEL}")
        try:
            df.to_excel(STREET_VIEW_EXCEL, index=False, engine='openpyxl')
            print(f"Fichier Excel sauvegardé avec {len(results)} entrées")
        except PermissionError as e:
            print(f"❌ Erreur de permission lors de l'écriture de {STREET_VIEW_EXCEL} : {e}")
    else:
        print("Aucun résultat à sauvegarder dans le fichier Excel.")

    return results