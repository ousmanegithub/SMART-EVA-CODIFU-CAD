import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import osmnx as ox
from math import atan2, degrees, radians, cos, sin

def validate_gdf(gdf):
    """ Vérifie et corrige les erreurs dans un GeoDataFrame """
    if gdf.crs is None or gdf.crs != "EPSG:4326":
        print("⚠️ Aucun CRS détecté, attribution manuelle à EPSG:4326")
        gdf.set_crs(epsg=4326, inplace=True)

    # Vérifier que les géométries sont valides
    gdf = gdf[gdf.is_valid]
    return gdf

def determine_utm_crs(latitude, longitude):
    """ Détermine un CRS UTM en fonction des coordonnées GPS """
    try:
        if pd.isna(latitude) or pd.isna(longitude) or latitude == 0 or longitude == 0:
            return 4326  # Retourne EPSG:4326 en cas d'erreur

        zone_number = int((longitude + 180) / 6) + 1
        epsg_code = 32600 + zone_number if latitude >= 0 else 32700 + zone_number
        return epsg_code if 32601 <= epsg_code <= 32760 else 3857  # EPSG:3857 en fallback
    except Exception:
        return 3857  # EPSG:3857 en dernier recours

def find_closest_road_point(parcelle, roads):
    """ Trouve la route la plus proche d'une parcelle """
    try:
        min_distance = float('inf')
        closest_point = None
        for _, road in roads.iterrows():
            distance = parcelle.distance(road.geometry)
            if distance < min_distance:
                min_distance = distance
                closest_point = road.geometry.interpolate(road.geometry.project(parcelle.centroid))
        return closest_point
    except Exception:
        return None

def calculate_heading(lon1, lat1, lon2, lat2):
    """ Calcul l'angle d'orientation entre la route et la parcelle """
    try:
        heading = degrees(atan2(lon2 - lon1, lat2 - lat1))
        return (heading + 360) % 360
    except Exception:
        return 0

def calculate_adjusted_view(lon, lat, heading, distance=25):
    """ Reculer légèrement pour capturer l'immeuble en entier """
    heading_rad = radians(heading + 180)  # Reculer de 180°
    lon_adjusted = lon + (distance * cos(heading_rad) / 111320)
    lat_adjusted = lat + (distance * sin(heading_rad) / 110540)
    return lon_adjusted, lat_adjusted
