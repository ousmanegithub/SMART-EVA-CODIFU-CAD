import gc
import hashlib
import logging
import pandas as pd
import geopandas as gpd
import qrcode
from shapely.validation import make_valid
import numpy as np
import random
import os
import pyqrcode
from pyproj import Transformer

def create_permuted_alphabet(alphabet: str, secret_key: str) -> str:
    """
    Crée un alphabet permuté basé sur une clé secrète pour sécuriser le codage.
    """
    random.seed(secret_key)
    alphabet_list = list(alphabet)
    random.shuffle(alphabet_list)
    permuted_alphabet = ''.join(alphabet_list)
    logging.debug(f'Alphabet permuté: {permuted_alphabet}')
    return permuted_alphabet

def encode_number(num: int, alphabet: str) -> str:
    """
    Encode un nombre entier en une chaîne de caractères en utilisant un alphabet donné.
    """
    if num == 0:
        return alphabet[0]
    arr = []
    base = len(alphabet)
    is_negative = num < 0
    num = abs(num)
    while num > 0:
        num, rem = divmod(num, base)
        arr.append(alphabet[rem])
    arr = ''.join(reversed(arr))
    return ('C' if is_negative else '') + arr

def criptocentre(index: int, coord_x: pd.Series, coord_y: pd.Series, xref: float, yref: float,
                 alphabet: str, region_abbr: pd.Series, secret_key: str) -> pd.Series:
    """
    Génère un code unique de 7 caractères pour chaque parcelle, même si les coordonnées sont proches.
    """
    permuted_alphabet = create_permuted_alphabet(alphabet, secret_key)


    x0 = np.round(100 * (coord_x - xref)).astype(int)
    y0 = np.round(100 * (coord_y - yref)).astype(int)

    xcentro = encode_number(x0, permuted_alphabet)
    ycentro = encode_number(y0, permuted_alphabet)

    raw_string = f"{xcentro}{ycentro}{index}{secret_key}{random.randint(1000, 9999)}"
    hash_digest = hashlib.sha256(raw_string.encode()).hexdigest()
    unique_code = ''.join(permuted_alphabet[int(hash_digest[i:i+2], 16) % len(permuted_alphabet)] for i in range(0, 14, 2))
    insert_position = random.randint(0, 5)

    combined_code = unique_code[:insert_position] + region_abbr[:2] + unique_code[insert_position:]

    if len(combined_code) > 7:
        combined_code = combined_code[:7]  # Tronquer si trop long
    else:
        while len(combined_code) < 7:
            combined_code += random.choice(permuted_alphabet)  # Compléter si trop court

    return combined_code


def process_geodataframe(parcellaire: gpd.GeoDataFrame,
                         previous_parcellaire: gpd.GeoDataFrame = None,
                         alphabet: str = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
                         secret_key: str = "65432796856") -> gpd.GeoDataFrame:
    """
    Traite un GeoDataFrame de parcelles pour générer des codes BDN uniques de 7 caractères.
    """
    invalid_geom_mask = ~parcellaire.is_valid
    if invalid_geom_mask.any():
        parcellaire.loc[invalid_geom_mask, 'geometry'] = parcellaire.loc[invalid_geom_mask, 'geometry'].apply(
            make_valid)
        logging.info(f"{invalid_geom_mask.sum()} géométries invalides ont été corrigées.")

    parcellaire['representative_point'] = parcellaire.geometry.representative_point()
    parcellaire['coord_x'] = parcellaire['representative_point'].x
    parcellaire['coord_y'] = parcellaire['representative_point'].y

    if parcellaire.crs.is_projected:
        parcellaire['area'] = parcellaire.geometry.area
    else:
        parcellaire_projected = parcellaire.to_crs(epsg=3395)
        parcellaire['area'] = parcellaire_projected.geometry.area
        logging.warning("Les superficies ont été calculées en reprojetant temporairement les données.")

    # Abréviations des régions
    region_abbreviations = {
        'DAKAR': 'DK', 'Diourbel': 'DL', 'Fatick': 'FK', 'Kaffrine': 'KF',
        'Kaolack': 'KL', 'Kédougou': 'KG', 'Kolda': 'KD', 'Louga': 'LG',
        'Matam': 'MT', 'Saint-Louis': 'SL', 'Sédhiou': 'SD', 'Tambacounda': 'TC',
        'Thiès': 'TH', 'Ziguinchor': 'ZG'
    }

    parcellaire['abbr'] = parcellaire['region'].map(region_abbreviations).fillna('XX')

    parcellaire['historique'] = ""

    if previous_parcellaire is not None:
        required_columns = ['parcel_id', 'area', 'CodeBDN']
        if not all(col in previous_parcellaire.columns for col in required_columns):
            raise ValueError(f"Le GeoDataFrame précédent doit contenir les colonnes {required_columns}")

        merged = parcellaire.merge(
            previous_parcellaire[required_columns],
            on='parcel_id',
            how='left',
            suffixes=('', '_prev')
        )

        merged['area_diff'] = (merged['area'] - merged['area_prev']).abs()
        tolerance = 3.0

        significant_change = (merged['area_diff'] > tolerance) | merged['area_prev'].isnull()

        merged.loc[~significant_change, 'CodeBDN'] = merged.loc[~significant_change, 'CodeBDN_prev']
        merged.loc[significant_change & merged['CodeBDN_prev'].notnull(), 'historique'] = merged.loc[
            significant_change & merged['CodeBDN_prev'].notnull(), 'CodeBDN_prev']
        parcellaire = merged.drop(columns=['area_prev', 'CodeBDN_prev', 'area_diff'])

    # Génération des codes uniques en passant l'index pour éviter les doublons
    parcellaire['CodeBDN'] = parcellaire.apply(lambda row: criptocentre(
        row.name, row['coord_x'], row['coord_y'], parcellaire['coord_x'].mean(), parcellaire['coord_y'].mean(),
        alphabet, row['abbr'], secret_key), axis=1)

    # Vérification d'unicité
    if parcellaire['CodeBDN'].duplicated().any():
        duplicated_codes = parcellaire['CodeBDN'][parcellaire['CodeBDN'].duplicated()]
        logging.error(f"Les codes BDN suivants ne sont pas uniques : {duplicated_codes.tolist()}")
        raise ValueError(
            "Les codes BDN générés ne sont pas uniques. Veuillez vérifier le processus de génération des codes.")

    parcellaire.drop(columns=['representative_point'], inplace=True)
    return parcellaire


def generate_qr_codes(parcellaire: gpd.GeoDataFrame, output_folder: str, batch_size=100):
    logging.info(f"Nombre de parcelles à traiter : {len(parcellaire)}")
    transformer = Transformer.from_crs(parcellaire.crs, "EPSG:4326", always_xy=True)
    parcellaire['centroid_lon'], parcellaire['centroid_lat'] = transformer.transform(parcellaire['coord_x'], parcellaire['coord_y'])
    parcellaire['geo_uri'] = parcellaire.apply(lambda row: f"geo:{row['centroid_lat']},{row['centroid_lon']}", axis=1)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    qr_paths = []
    for start in range(0, len(parcellaire), batch_size):
        batch = parcellaire.iloc[start:start + batch_size].copy()
        logging.info(f"Traitement du lot {start} à {start + batch_size}")
        for index, row in batch.iterrows():
            try:
                if not row['geo_uri'] or not isinstance(row['geo_uri'], str):
                    logging.warning(f"geo_uri invalide pour parcelle {row['CodeBDN']}: {row['geo_uri']}")
                    qr_paths.append(None)
                    continue
                qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=5, border=1)
                qr.add_data(row['geo_uri'])
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                qr_filename = os.path.join(output_folder, f"CODIF_{row['CodeBDN']}.png")
                img.save(qr_filename)
                qr_paths.append(qr_filename)
            except Exception as e:
                logging.error(f"Erreur lors de la génération du QR code pour {row['CodeBDN']}: {e}")
                qr_paths.append(None)
        del batch
        gc.collect()

    parcellaire['QRCode'] = pd.Series(qr_paths, index=parcellaire.index)
    parcellaire.drop(columns=['centroid_lon', 'centroid_lat', 'geo_uri'], inplace=True)
    return parcellaire