import glob
import json
import logging
import shutil
import zipfile
from zipfile import ZipFile

import numpy as np
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from django.shortcuts import render, redirect

# Create your views here.
from django.http import JsonResponse, HttpResponse, FileResponse
from django.shortcuts import render
from django.core.serializers import serialize
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from geopandas.io.file import fiona
from pyexpat.errors import messages
from django.contrib import messages
from rest_framework.decorators import api_view
from rest_framework.response import Response
from shapely.constructive import make_valid
from shapely.geometry import MultiPolygon
from shapely.validation import make_valid

from code_bdn_project import settings
from .evaluation_utils import calculer_valeur_locaux, calculer_valeur_clotures, calculer_valeur_cours, \
    calculer_valeur_dependances, calculer_valeur_amenagements, calculer_valeur_terrains, generate_pdf_report, \
    detect_type_bareme
from .forms import GeoJSONUploadForm, GenerateBDNForm
from .geo_utils import validate_gdf, determine_utm_crs
from .models import Parcelle
from .serializers import ParcelleSerializer
import geopandas as gpd
from django.http import JsonResponse

import tempfile
import osmnx as ox
from osmnx import graph_from_point, graph_to_gdfs


import os
from .street_view import process_street_view
from .utils import process_geodataframe, generate_qr_codes

from django.urls import reverse
from django.templatetags.static import static

def map_view(request):
    return render(request, 'parcelles/map.html')

@api_view(['GET'])
def parcelle_list(request):
    parcelles = Parcelle.objects.all()
    serializer = ParcelleSerializer(parcelles, many=True)
    return Response(serializer.data)

"""def upload_shapefile(request):
    if 'shapefile' in request.FILES:
        shapefile = request.FILES['shapefile']
        gdf = gpd.read_file(shapefile)
        for _, row in gdf.iterrows():
            Parcelle.objects.create(
                name=row['name'],
                geometry=row['geometry'],
                region=row['region']
            )
        return JsonResponse({'message': 'Shapefile uploaded successfully.'})
    return JsonResponse({'error': 'No shapefile provided.'}, status=400)
import shutil
import geopandas as gpd"""


def map_view(request):
    form = GeoJSONUploadForm()
    generate_form = GenerateBDNForm()
    return render(request, 'parcelles/map.html', {'form': form}

                  )
@login_required
def home_view(request):
    context = {
        "app_cards": [
            {"name": "GENERATION DE QRCODE & DE CODIFU ", "background_image_url": static("/images/cards/aoi.PNG"),
             'url': reverse('map_view')},
            {"name": "EVALUATION DE MASSE ET INDIVIDUEL DES BIENS IMMOBILIERS", "background_image_url": static("/images/cards/dm.PNG"),
             'url': reverse('eval_view')},
        ],
    }
    return render(request, 'parcelles/home.html', context)
def about(request):
    return render(request, 'parcelles/about.html', {})
def setup(request):
    return render(request, 'parcelles/setup.html', {})

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Inscription réussie ! Veuillez vous connecter.")
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserCreationForm()
    return render(request, 'parcelles/register.html', {'form': form})


def eval_view(request):
    form = GeoJSONUploadForm()
    return render(request, 'parcelles/map_from_GEE.html', {'form': form}
                  )
def multi_step_eval_view(request):
    return render(request, 'parcelles/multi_step_eval.html')


TEMP_FILE_PATH = os.path.join('media', 'temp_uploaded_file.geojson')

@csrf_exempt
def upload_geojson(request):
    if request.method == 'POST':
        try:
            # Vérifiez que le fichier a été envoyé
            file = request.FILES.get('file')
            if not file:
                return JsonResponse({'error': 'Aucun fichier fourni.'}, status=400)

            # Lire et valider le fichier GeoJSON
            data = json.load(file)
            if 'features' not in data or not data['features']:
                return JsonResponse({'error': 'Le fichier GeoJSON est vide ou invalide.'}, status=400)

            # Sauvegarder temporairement le fichier pour une utilisation ultérieure
            if not os.path.exists('media'):
                os.makedirs('media')  # Créez le dossier s'il n'existe pas
            with open(TEMP_FILE_PATH, 'w', encoding='utf-8') as temp_file:
                json.dump(data, temp_file, ensure_ascii=False, indent=4)

            # Retourner les données pour affichage sur la carte
            return JsonResponse({'geojson': data, 'message': 'Fichier importé avec succès.'}, status=200)

        except Exception as e:
            return JsonResponse({'error': f"Erreur lors de l'importation : {str(e)}"}, status=400)
    return JsonResponse({'error': 'Requête invalide.'}, status=400)





TEMP_FILE_PATH_EVAL = os.path.join('media/upload', 'temp_uploaded_file_EVAL.geojson')

@csrf_exempt
def upload_geojson_eval(request):
    if request.method == 'POST':
        try:
            file = request.FILES.get('file')
            if not file:
                return JsonResponse({'error': 'Aucun fichier fourni.'}, status=400)

            data = json.load(file)
            if 'features' not in data or not data['features']:
                return JsonResponse({'error': 'Le fichier GeoJSON est vide ou invalide.'}, status=400)

            os.makedirs('media/upload', exist_ok=True)
            with open(TEMP_FILE_PATH_EVAL, 'w', encoding='utf-8') as temp_file:
                json.dump(data, temp_file, ensure_ascii=False, indent=4)
            """
            gdf = gpd.GeoDataFrame.from_features(data["features"])
            gdf = validate_gdf(gdf)
            gdf["centroid"] = gdf.geometry.centroid
            gdf["latitude"] = gdf["centroid"].y
            gdf["longitude"] = gdf["centroid"].x

            # Charger les routes
            roads = ox.graph_to_gdfs(ox.graph_from_point((gdf["latitude"].mean(), gdf["longitude"].mean()), dist=500, network_type='drive'), nodes=False, edges=True)

            # Générer les images Street View
            image_paths = process_street_view(gdf, roads)
            """
            return JsonResponse({'geojson': data, """'image_paths': image_paths,""" 'message': 'Import et capture réussis.'}, status=200)

        except Exception as e:
            return JsonResponse({'error': f"Erreur : {str(e)}"}, status=400)

@csrf_exempt
def generate_street_view(request):
    if request.method == "POST":
        try:
            if not os.path.exists(TEMP_FILE_PATH_EVAL):
                return JsonResponse({'error': 'Aucun fichier GeoJSON importé.'}, status=400)

            # Charger le GeoDataFrame
            gdf = gpd.read_file(TEMP_FILE_PATH_EVAL)
            gdf = validate_gdf(gdf)
            gdf["centroid"] = gdf.geometry.centroid
            gdf["latitude"] = gdf["centroid"].y
            gdf["longitude"] = gdf["centroid"].x

            # Charger les routes
            center_point = (gdf["latitude"].mean(), gdf["longitude"].mean())
            roads = ox.graph_to_gdfs(
                ox.graph_from_point(center_point, dist=500, network_type='drive'),
                nodes=False, edges=True
            )

            # Générer les images Street View et récupérer les résultats
            results = process_street_view(gdf, roads)

            # Préparer la réponse
            response_data = {
                "status": "success",
                "images": [
                    {
                        "nicad": result["nicad"],
                        "image_url": request.build_absolute_uri('/media/street_view_images/' + os.path.basename(result["image_path"])),
                        "street_view_url": result["street_view_url"]
                    }
                    for result in results
                ]
            }
            return JsonResponse(response_data)

        except Exception as e:
            return JsonResponse({'error': f"Erreur lors de la génération des images Street View : {str(e)}"}, status=400)
    return JsonResponse({'error': 'Méthode non autorisée.'}, status=405)



@csrf_exempt
def generate_multi_step_report(request):
    if request.method == "POST":
        try:
            if not os.path.exists(TEMP_FILE_PATH_EVAL):
                return JsonResponse({'error': 'Aucun fichier GeoJSON importé.'}, status=400)

            gdf = gpd.read_file(TEMP_FILE_PATH_EVAL)
            region = request.POST.get('region', 'DAKAR')
            for col in ['Prix_au_m', 'Superficie', 'assise', 'Surfaced', 'lr', 'sr', 'niveaux']:
                if col in gdf.columns:
                    gdf[col] = pd.to_numeric(gdf[col], errors='coerce').fillna(0)

            processed_gdf = process_geodataframe(gdf)
            qr_output_folder = os.path.join(settings.MEDIA_ROOT, 'qr_codes')
            processed_gdf = generate_qr_codes(processed_gdf, qr_output_folder)

            street_view_excel = os.path.join(settings.MEDIA_ROOT, 'street_view_links.xlsx')
            street_view_dict = {}
            if os.path.exists(street_view_excel):
                df = pd.read_excel(street_view_excel)
                df['nicad_no_zeros'] = df['nicad'].astype(str).str.lstrip('0')
                street_view_dict = df.set_index('nicad_no_zeros')['street_view_url'].to_dict()

            locaux_envet = float(request.POST.get('locaux_envet', 1))
            locaux_vois = float(request.POST.get('locaux_vois', 1))
            locaux_aban = float(request.POST.get('locaux_aban', 0))
            locaux_type_bareme = request.POST.get('locaux_type_bareme')
            locaux_categorie = request.POST.get('locaux_categorie')
            gdf['envet'] = locaux_envet
            gdf['vois'] = locaux_vois
            gdf['aban'] = locaux_aban
            locaux = calculer_valeur_locaux(gdf, region, locaux_type_bareme, locaux_categorie)
            locaux_data = pd.DataFrame(locaux)

            clotures_envet = float(request.POST.get('clotures_envet', 1))
            clotures_categorie = request.POST.get('clotures_categorie')
            gdf['envet'] = clotures_envet
            clotures = calculer_valeur_clotures(gdf, region, clotures_categorie)

            cours_envet = float(request.POST.get('cours_envet', 1))
            cours_categorie = request.POST.get('cours_categorie')
            gdf['envet'] = cours_envet
            cours = calculer_valeur_cours(gdf, region, cours_categorie)

            dependances_envet = float(request.POST.get('dependances_envet', 1))
            dependances_type_bareme = request.POST.get('dependances_type_bareme')
            dependances_categorie = request.POST.get('dependances_categorie')
            gdf['envet'] = dependances_envet
            dependances = calculer_valeur_dependances(gdf, region, dependances_type_bareme, dependances_categorie)

            amenagements = calculer_valeur_amenagements(gdf, region)
            terrains = calculer_valeur_terrains(gdf, region)

            all_data = pd.DataFrame(locaux + clotures + cours + dependances + terrains + amenagements)
            total_values_pivot = all_data.pivot_table(index='nicad', columns='Type', values='Valeur', aggfunc='sum').reset_index()
            total_values_pivot.fillna(0, inplace=True)

            columns_to_sum = ['Valeur totale des locaux (FCFA)', 'Valeur de la clôture (FCFA)',
                             'Valeur de la cour (FCFA)', 'Valeur des dépendances (FCFA)',
                             'Valeur du Sol (FCFA)', 'Valeur des aménagements particuliers (FCFA)']
            total_values_pivot['Valeur totale (FCFA)'] = total_values_pivot[columns_to_sum].sum(axis=1)

            total_values_pivot['Taux'] = total_values_pivot.apply(
                lambda row: locaux_data[locaux_data['nicad'] == row['nicad']]['Taux Locatif'].iloc[0] if row['nicad'] in locaux_data['nicad'].values else 0.10, axis=1)
            total_values_pivot['Valeur locative (FCFA)'] = total_values_pivot['Valeur totale (FCFA)'] * total_values_pivot['Taux']
            total_values_pivot['CFPB'] = total_values_pivot['Valeur locative (FCFA)'] * 0.05

            excel_path = os.path.join(settings.MEDIA_ROOT, 'Rapport_Evaluation_Multi_Etapes.xlsx')
            total_values_pivot.to_excel(excel_path, index=False)

            pdf_folder = os.path.join(settings.MEDIA_ROOT, 'pdf_reports')
            pdf_paths = []
            for _, row in total_values_pivot.iterrows():
                nicad = row['nicad']
                parcelle = gdf[gdf['nicad'] == nicad].copy()
                if parcelle.empty:
                    continue

                parcelle_projected = parcelle.to_crs(epsg=32628)
                assise = float(parcelle['assise'].iloc[0])
                niveaux = float(parcelle['niveaux'].iloc[0])
                superficie = float(parcelle['Superficie'].iloc[0])
                prix_au_m = float(parcelle['Prix_au_m'].iloc[0])
                lr = float(parcelle['lr'].iloc[0])
                sr = float(parcelle['Sr'].iloc[0])

                code_bdn = processed_gdf.loc[processed_gdf['nicad'] == nicad, 'CodeBDN'].iloc[0]
                qr_code_path = processed_gdf.loc[processed_gdf['nicad'] == nicad, 'QRCode'].iloc[0]

                nicad_no_zeros = str(nicad).lstrip('0')
                street_view_url = street_view_dict.get(nicad_no_zeros, "Non disponible")

                data = {
                    "Catégorie": locaux_categorie,
                    "Superficie Totale bâtie (en m²)": f"{assise * niveaux:.2f}",
                    "Valeur Totale des locaux (FCFA)": f"{row.get('Valeur totale des locaux (FCFA)', 0):.2f}",  # Deux décimales
                    "Barème (en FCFA le m²)": f"{prix_au_m:.2f}",  # Deux décimales
                    "Surface terrain non bâti (en m²)": f"{superficie - assise:.2f}",
                    "Surface terrain bâti (en m²)": f"{assise:.2f}",
                    "Valeur du sol (FCFA)": f"{row.get('Valeur du Sol (FCFA)', 0):.2f}",  # Deux décimales
                    "Valeur des aménagements particuliers (FCFA)": f"{row.get('Valeur des aménagements particuliers (FCFA)', 0):.2f}",  # Deux décimales
                    "Longueur de la clôture (en m)": f"{lr:.2f}",
                    "Valeur de la clôture (en FCFA)": f"{row.get('Valeur de la clôture (FCFA)', 0):.2f}",  # Deux décimales
                    "Surface des cours (en m²)": f"{sr:.2f}",
                    "Valeur des cours (en FCFA)": f"{row.get('Valeur de la cour (FCFA)', 0):.2f}",  # Deux décimales
                    "Valeur des dépendances (en FCFA)": f"{row.get('Valeur des dépendances (FCFA)', 0):.2f}",  # Deux décimales
                    "Valeur totale de l’immeuble (FCFA)": f"{row['Valeur totale (FCFA)']:.2f}",  # Deux décimales
                    "Valeur locative (FCFA)": f"{row['Valeur locative (FCFA)']:.2f}",  # Deux décimales
                    "Taux appliqué": f"{row['Taux']:.2%}",
                    "CFPB": f"{row['CFPB']:.2f}",  # Deux décimales
                    "Propriétaire": parcelle.get('proprietaire', pd.Series(['Non spécifié'])).iloc[0],
                    "CNI": parcelle.get('cni', pd.Series(['Non spécifié'])).iloc[0],
                    "Titre": parcelle.get('titre', pd.Series(['Non spécifié'])).iloc[0],
                    "Lot": parcelle.get('lot', pd.Series(['Non spécifié'])).iloc[0],
                    "Niveau": f"{int(niveaux)}",
                    "Usage": parcelle.get('usage', pd.Series(['Non spécifié'])).iloc[0],
                    "Superficie Terrain (en m²)": f"{superficie:.2f}",
                    "Téléphone": parcelle.get('telephone', pd.Series(['Non spécifié'])).iloc[0],
                    "Email": parcelle.get('email', pd.Series(['Non spécifié'])).iloc[0],
                    "NINEA": parcelle.get('ninea', pd.Series(['Non spécifié'])).iloc[0],
                    "Infos complémentaires": parcelle.get('infos_complementaires', pd.Series(['Non spécifié'])).iloc[0],
                    "latitude": parcelle_projected.geometry.centroid.y.iloc[0],
                    "longitude": parcelle_projected.geometry.centroid.x.iloc[0],
                    "CodeBDN": code_bdn,
                    "QRCode": qr_code_path
                }

                image_path = os.path.join(settings.MEDIA_ROOT, 'street_view_images', f'parcelle_{nicad}.png')
                pdf_path = generate_pdf_report(nicad, data, image_path if os.path.exists(image_path) else None, street_view_url)
                pdf_paths.append(pdf_path)

            zip_path = os.path.join(settings.MEDIA_ROOT, 'Rapport_Evaluation_Complete.zip')
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(excel_path, os.path.basename(excel_path))
                for pdf_path in pdf_paths:
                    zipf.write(pdf_path, os.path.join('pdf_reports', os.path.basename(pdf_path)))

            response = FileResponse(open(zip_path, 'rb'), as_attachment=True, filename='Rapport_Evaluation_Complete.zip')
            return response

        except Exception as e:
            return JsonResponse({'error': f"Erreur lors de la génération du rapport : {str(e)}"}, status=400)
    return JsonResponse({'error': 'Méthode non autorisée.'}, status=405)


""" def simplify_geometry(geom):
    
    if isinstance(geom, MultiPolygon):
        return max(geom.geoms, key=lambda g: g.area)  # Garder le plus grand Polygon
    return geom




@csrf_exempt
def generate_bdn_codes(request):

        
        if request.method != "POST":
            return JsonResponse({'error': 'Méthode non autorisée.'}, status=405)

        try:
            # Vérifiez que le fichier GeoJSON existe
            uploaded_file_path = 'uploaded_geojson.json'
            if not os.path.exists(uploaded_file_path):
                return JsonResponse({'error': 'Aucun fichier GeoJSON trouvé. Veuillez uploader un fichier.'},
                                    status=400)

            # Charger le fichier GeoJSON dans un GeoDataFrame
            gdf = gpd.read_file(uploaded_file_path)

            # Assurez-vous qu'une seule colonne géométrique est active
            if gdf.geometry.name != 'geometry':
                gdf.set_geometry('geometry', inplace=True)

            # Convertir les géométries multiples en géométries simples
            gdf['geometry'] = gdf['geometry'].apply(simplify_geometry)

            # Nettoyer et générer les codes BDN
            processed_gdf = process_geodataframe(gdf)

            # Sauvegarder le GPKG enrichi
            output_gpkg_path = 'processed_geojson_with_bdn.gpkg'
            processed_gdf.to_file(output_gpkg_path, driver='GPKG')

            # Générer les QR codes
            qr_output_folder = "qr_codes"
            if os.path.exists(qr_output_folder):
                shutil.rmtree(qr_output_folder)
            os.makedirs(qr_output_folder)
            generate_qr_codes(processed_gdf, qr_output_folder)

            # Créer un fichier ZIP contenant les QR codes
            zip_file_path = os.path.join(qr_output_folder, "qr_codes.zip")
            with ZipFile(zip_file_path, 'w') as zip_file:
                for root, _, files in os.walk(qr_output_folder):
                    for file in files:
                        if file.endswith(".png"):
                            file_path = os.path.join(root, file)
                            zip_file.write(file_path, arcname=os.path.basename(file_path))

            return JsonResponse({
                'message': 'Codes BDN générés avec succès.',
                'gpkg_url': f"/{output_gpkg_path}",  # Chemin pour le fichier GPKG
                'qr_zip_url': f"/{zip_file_path}"  # Chemin pour le ZIP des QR codes
            }, status=200)

        except Exception as e:
            logging.error(f"Erreur lors de la génération des codes BDN : {e}")
            return JsonResponse({'error': f'Erreur lors de la génération des codes BDN : {e}'}, status=400)"""


from django.http import JsonResponse
from .models import Parcelle
import geopandas as gpd

"""def upload_geospatial_file(request, load_wkt=None):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        try:
            # Chargement dans un GeoDataFrame
            gdf = gpd.read_file(uploaded_file)

            # Vérifiez et nettoyez les colonnes géométriques
            if 'geometry' not in gdf.columns:
                raise ValueError("Aucune colonne 'geometry' trouvée dans le fichier.")
            if gdf.select_dtypes(include=['geometry']).shape[1] > 1:
                gdf = gdf.set_geometry('geometry')
                gdf.drop(columns=[col for col in gdf.columns if col != 'geometry'], inplace=True)

            # Conversion des colonnes WKT en géométrie
            if 'geometry' in gdf.columns and not isinstance(gdf['geometry'].iloc[0], gpd.GeoSeries):
                gdf['geometry'] = gdf['geometry'].apply(load_wkt)

            # Corrigez les géométries invalides
            if not gdf.is_valid.all():
                gdf['geometry'] = gdf['geometry'].apply(make_valid)

            # Enregistrez dans la base de données
            for _, row in gdf.iterrows():
                Parcelle.objects.create(
                    geometry=row.geometry,
                    nom=row.get('NOM', None),
                    theme=row.get('THEME', None),
                    pays=row.get('PAYS', None),
                    iduu=row.get('IDUU', None),
                    sum_superf=row.get('SUM_SUPERF', None),
                    shape_leng=row.get('Shape_Leng', None),
                    shape_area=row.get('Shape_Area', None),
                )

            return JsonResponse({'message': 'Fichier importé avec succès !'}, status=200)

        except Exception as e:
            logging.error(f"Erreur lors de l'importation : {e}")
            return JsonResponse({'error': f"Erreur lors de l'importation : {e}"}, status=400)

    return JsonResponse({'error': 'Aucun fichier fourni.'}, status=400)"""


from django.http import JsonResponse
from .models import Parcelle
import geopandas as gpd
from shapely.constructive import make_valid
from shapely.geometry import MultiPolygon


from django.http import JsonResponse
from .models import Parcelle
import geopandas as gpd
from datetime import datetime
import os

import pandas as pd

import shutil
from zipfile import ZipFile


@csrf_exempt
def generate_bdn_codes(request):
    if request.method != "POST":
        return JsonResponse({
            'alert': {
                'type': 'error',
                'message': 'Méthode non autorisée. Utilisez POST.'
            }
        }, status=405)

    try:
        # Vérifiez si le fichier temporaire existe
        if not os.path.exists(TEMP_FILE_PATH):
            return JsonResponse({
                'alert': {
                    'type': 'error',
                    'message': 'Aucun fichier importé trouvé. Veuillez importer un fichier avant de générer les codes BDN.'
                }
            }, status=400)

        # Chargez le fichier temporaire
        gdf = gpd.read_file(TEMP_FILE_PATH)

        # Traitement de gdf
        processed_gdf = process_geodataframe(gdf)

        # Assurez-vous qu'il n'y a qu'une seule colonne géométrique
        if 'geometry' in processed_gdf.columns:
            processed_gdf = processed_gdf.set_geometry('geometry')
            other_geo_columns = [
                col for col in processed_gdf.select_dtypes(include=['geometry']).columns if col != 'geometry'
            ]
            if other_geo_columns:
                processed_gdf = processed_gdf.drop(columns=other_geo_columns)
        else:
            geo_cols = processed_gdf.select_dtypes(include=['geometry']).columns
            if geo_cols:
                processed_gdf = processed_gdf.set_geometry(geo_cols[0])
                processed_gdf = processed_gdf.drop(columns=[col for col in geo_cols if col != geo_cols[0]])
            else:
                raise ValueError("Aucune colonne géométrique valide trouvée dans le GeoDataFrame.")

        # Générez les QR codes et ajoutez les colonnes associées
        qr_output_folder = os.path.join('media', 'qr_codes')
        processed_gdf = generate_qr_codes(processed_gdf, qr_output_folder)

        # Créer un nom de fichier unique pour le GeoJSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_geojson_path = os.path.join('media', f'processed_with_bdn_{timestamp}.geojson')

        # Sauvegarder le fichier GeoJSON enrichi
        processed_gdf.to_file(output_geojson_path, driver="GeoJSON")

        # Créer un fichier ZIP contenant les QR codes
        zip_filename = os.path.join('media', f'qr_codes_{timestamp}.zip')
        with ZipFile(zip_filename, 'w') as zip_file:
            for root, _, files in os.walk(qr_output_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, qr_output_folder)  # Relatif au dossier QR codes
                    zip_file.write(file_path, arcname)

        # Construire les URLs pour le téléchargement
        geojson_url = request.build_absolute_uri(f'/media/{os.path.basename(output_geojson_path)}')
        zip_url = request.build_absolute_uri(f'/media/{os.path.basename(zip_filename)}')

        return JsonResponse({
            'geojson_url': geojson_url,
            'zip_url': zip_url,
            'alert': {
                'type': 'success',
                'message': 'Les codes BDN et QR codes ont été générés avec succès. Vous pouvez télécharger les fichiers.'
            }
        }, status=200)

    except Exception as e:
        logging.error(f"Erreur lors de la génération des codes BDN : {e}")
        return JsonResponse({
            'alert': {
                'type': 'error',
                'message': f"Erreur lors de la génération : {e}"
            }
        }, status=400)





def get_parcelles_geojson(request):
    geojson = serialize('geojson', Parcelle.objects.all(), geometry_field='geometry', fields=('nom', 'code_bdn', 'theme'))
    return JsonResponse({'geojson': geojson}, safe=False)


def list_parcelles(request):
    parcelles = Parcelle.objects.all()
    data = serialize('geojson', parcelles, geometry_field='geometry', fields=('nom', 'theme', 'code_bdn'))
    return JsonResponse({'geojson': data}, safe=False)


def pagination_range(page_obj, num_pages_to_show=3):
    """
    Calcule une plage de pages pour afficher un nombre limité de numéros de page.
    """
    current_page = page_obj.number
    total_pages = page_obj.paginator.num_pages


    start_page = max(1, current_page - num_pages_to_show // 2)
    end_page = min(total_pages, start_page + num_pages_to_show - 1)

    if end_page - start_page < num_pages_to_show - 1:
        start_page = max(1, end_page - num_pages_to_show + 1)

    page_range = list(range(start_page, end_page + 1))

    if start_page > 1:
        page_range.insert(0, "...")
        page_range.insert(0, 1)
    if end_page < total_pages:
        page_range.append("...")
        page_range.append(total_pages)

    return page_range


def view_generated_data(request):
    """
    Vue pour afficher les données du fichier généré sous forme de table.
    """
    media_dir = os.path.join(settings.BASE_DIR, 'media')
    pattern = os.path.join(media_dir, 'processed_with_bdn_*.geojson')
    file_paths = glob.glob(pattern)

    if not file_paths:
        return render(request, 'parcelles/data_table.html', {
            'error': 'Aucun fichier généré trouvé.'
        })

    file_path = max(file_paths, key=os.path.getctime)

    try:
        gdf = gpd.read_file(file_path)

        if gdf.empty:
            return render(request, 'parcelles/data_table.html', {
                'error': 'Le fichier généré est vide.'
            })

        if 'geometry' in gdf.columns:
            gdf = gdf.drop(columns=['geometry'])

        if 'QRCode' in gdf.columns:
            gdf['QRCode'] = gdf['QRCode'].apply(
                lambda path: os.path.relpath(path, settings.MEDIA_ROOT).replace("\\", "/")
            )

        search_query = request.GET.get('search', '').strip().lower()
        if search_query:
            # Filtrer le DataFrame basé sur la colonne NOM
            gdf = gdf[gdf['region'].str.lower().str.contains(search_query)]

        data = gdf.to_dict(orient='records')
        columns = list(gdf.columns)

        paginator = Paginator(data, 100)  # 4 entrées par page
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        # Calculer la plage de pages
        page_range = pagination_range(page_obj, num_pages_to_show=3)

        return render(request, 'parcelles/data_table.html', {
            'columns': columns,
            'data': page_obj.object_list,
            'paginator': paginator,
            'page_obj': page_obj,
            'page_range': page_range, # Transmettre directement la plage calculée
            'search_query': search_query,
            'MEDIA_URL': settings.MEDIA_URL,
        })
    except Exception as e:
        return render(request, 'parcelles/data_table.html', {
            'error': f"Erreur lors du chargement des données : {e}"
        })















@csrf_exempt
def generate_individual_report(request):
    if request.method == "POST":
        print(f"Requête POST reçue : {request.POST}")
        try:
            nicad = request.POST.get('nicad')
            region = request.POST.get('region', 'DAKAR')
            categorie = request.POST.get('categorie') or request.POST.get('locaux_categorie')
            print(f"nicad: {nicad}, region: {region}, categorie: {categorie}")

            if not nicad or not categorie:
                return JsonResponse({'error': 'NICAD ou catégorie manquants.'}, status=400)

            if not os.path.exists(TEMP_FILE_PATH_EVAL):
                return JsonResponse({'error': 'Aucun fichier GeoJSON importé.'}, status=400)

            # Charger le GeoDataFrame et trouver la parcelle
            gdf = gpd.read_file(TEMP_FILE_PATH_EVAL)
            parcelle = gdf[gdf['nicad'] == nicad].copy()
            if parcelle.empty:
                return JsonResponse({'error': f'Parcelle {nicad} non trouvée dans le GeoJSON.'}, status=400)

            numeric_cols = ['Prix_au_m', 'Superficie', 'assise', 'Surfaced', 'lr', 'Sr', 'niveaux', 'coutrap']
            for col in numeric_cols:
                if col in parcelle.columns:
                    parcelle.loc[:, col] = pd.to_numeric(parcelle[col], errors='coerce').fillna(0)
                    print(f"Colonne {col} après conversion : {parcelle[col].iloc[0]} (type: {type(parcelle[col].iloc[0])})")

            locaux_envet = float(request.POST.get('locaux_envet', 1))
            locaux_vois = float(request.POST.get('locaux_vois', 1))
            locaux_aban = float(request.POST.get('locaux_aban', 0))
            locaux_type_bareme = request.POST.get('locaux_type_bareme', detect_type_bareme(categorie))
            parcelle.loc[:, 'envet'] = locaux_envet
            parcelle.loc[:, 'vois'] = locaux_vois
            parcelle.loc[:, 'aban'] = locaux_aban
            locaux = calculer_valeur_locaux(parcelle, region, locaux_type_bareme, categorie)
            locaux_data = pd.DataFrame(locaux)
            print(f"locaux_data['Valeur']: {locaux_data['Valeur'].iloc[0]} (type: {type(locaux_data['Valeur'].iloc[0])})")

            clotures_envet = float(request.POST.get('clotures_envet', 1))
            clotures_categorie = request.POST.get('clotures_categorie', '1')
            parcelle.loc[:, 'envet'] = clotures_envet
            clotures = calculer_valeur_clotures(parcelle, region, clotures_categorie)
            print(f"clotures[0]['Valeur']: {clotures[0]['Valeur']} (type: {type(clotures[0]['Valeur'])})")

            cours_envet = float(request.POST.get('cours_envet', 1))
            cours_categorie = request.POST.get('cours_categorie', '1')
            parcelle.loc[:, 'envet'] = cours_envet
            cours = calculer_valeur_cours(parcelle, region, cours_categorie)
            print(f"cours[0]['Valeur']: {cours[0]['Valeur']} (type: {type(cours[0]['Valeur'])})")

            dependances_envet = float(request.POST.get('dependances_envet', 1))
            dependances_type_bareme = request.POST.get('dependances_type_bareme', locaux_type_bareme)
            dependances_categorie = request.POST.get('dependances_categorie', categorie)
            parcelle.loc[:, 'envet'] = dependances_envet
            dependances = calculer_valeur_dependances(parcelle, region, dependances_type_bareme, dependances_categorie)
            print(f"dependances[0]['Valeur']: {dependances[0]['Valeur']} (type: {type(dependances[0]['Valeur'])})")

            amenagements = calculer_valeur_amenagements(parcelle, region)
            print(f"amenagements[0]['Valeur']: {amenagements[0]['Valeur']} (type: {type(amenagements[0]['Valeur'])})")

            terrains = calculer_valeur_terrains(parcelle, region)
            print(f"terrains[0]['Valeur']: {terrains[0]['Valeur']} (type: {type(terrains[0]['Valeur'])})")

            combined_list = locaux + clotures + cours + dependances + terrains + amenagements
            print(f"combined_list : {combined_list}")
            all_data = pd.DataFrame(combined_list)
            print(f"all_data avant groupby : {all_data.to_dict()}")
            total_values = all_data.groupby('nicad').agg({'Valeur': 'sum'}).reset_index()
            print(f"total_values après groupby : {total_values.to_dict()}")

            if len(total_values) != 1:
                raise ValueError(f"Plusieurs lignes trouvées pour nicad {nicad} dans total_values : {len(total_values)}")

            valeur_totale = float(total_values['Valeur'].iloc[0])
            taux = float(locaux_data['Taux Locatif'].iloc[0]) if 'Taux Locatif' in locaux_data.columns and not locaux_data['Taux Locatif'].empty else 0.10
            print(f"taux avant calcul : {taux} (type: {type(taux)})")
            valeur_locative = valeur_totale * taux
            cfpb = valeur_locative * 0.05
            print(f"valeur_totale: {valeur_totale}, taux: {taux}, valeur_locative: {valeur_locative}, cfpb: {cfpb}")

            processed_gdf = process_geodataframe(gdf)
            qr_output_folder = os.path.join(settings.MEDIA_ROOT, 'qr_codes')
            processed_gdf = generate_qr_codes(processed_gdf, qr_output_folder)
            code_bdn = processed_gdf.loc[processed_gdf['nicad'] == nicad, 'CodeBDN'].iloc[0]
            qr_code_path = processed_gdf.loc[processed_gdf['nicad'] == nicad, 'QRCode'].iloc[0]

            parcelle_projected = parcelle.to_crs(epsg=32628)
            assise = float(parcelle['assise'].iloc[0])
            niveaux = float(parcelle['niveaux'].iloc[0])
            superficie = float(parcelle['Superficie'].iloc[0])
            prix_au_m = float(parcelle['Prix_au_m'].iloc[0])
            lr = float(parcelle['lr'].iloc[0])
            sr = float(parcelle['Sr'].iloc[0])

            data = {
                "Catégorie": categorie,
                "Superficie Totale bâtie (en m²)": f"{assise * niveaux:.2f}",
                "Valeur Totale des locaux (FCFA)": f"{float(locaux_data['Valeur'].iloc[0]):.2f}",  # Deux décimales
                "Barème (en FCFA le m²)": f"{prix_au_m:.2f}",  # Deux décimales
                "Surface terrain non bâti (en m²)": f"{superficie - assise:.2f}",
                "Surface terrain bâti (en m²)": f"{assise:.2f}",
                "Valeur du sol (FCFA)": f"{float(terrains[0]['Valeur']):.2f}",  # Deux décimales
                "Valeur des aménagements particuliers (FCFA)": f"{float(amenagements[0]['Valeur']):.2f}",  # Deux décimales
                "Longueur de la clôture (en m)": f"{lr:.2f}",
                "Valeur de la clôture (en FCFA)": f"{float(clotures[0]['Valeur']):.2f}",  # Deux décimales
                "Surface des cours (en m²)": f"{sr:.2f}",
                "Valeur des cours (en FCFA)": f"{float(cours[0]['Valeur']):.2f}",  # Deux décimales
                "Valeur des dépendances (en FCFA)": f"{float(dependances[0]['Valeur']):.2f}",  # Deux décimales
                "Valeur totale de l’immeuble (FCFA)": f"{valeur_totale:.2f}",  # Deux décimales
                "Valeur locative (FCFA)": f"{valeur_locative:.2f}",  # Deux décimales
                "Taux appliqué": f"{taux:.2%}",
                "CFPB": f"{cfpb:.2f}",  # Deux décimales
                "Propriétaire": parcelle.get('proprietaire', pd.Series(['Non spécifié'])).iloc[0],
                "CNI": parcelle.get('cni', pd.Series(['Non spécifié'])).iloc[0],
                "Titre": parcelle.get('titre', pd.Series(['Non spécifié'])).iloc[0],
                "Lot": parcelle.get('lot', pd.Series(['Non spécifié'])).iloc[0],
                "Niveau": f"{int(niveaux)}",
                "Usage": parcelle.get('usage', pd.Series(['Non spécifié'])).iloc[0],
                "Superficie Terrain (en m²)": f"{superficie:.2f}",
                "Téléphone": parcelle.get('telephone', pd.Series(['Non spécifié'])).iloc[0],
                "Email": parcelle.get('email', pd.Series(['Non spécifié'])).iloc[0],
                "NINEA": parcelle.get('ninea', pd.Series(['Non spécifié'])).iloc[0],
                "Infos complémentaires": parcelle.get('infos_complementaires', pd.Series(['Non spécifié'])).iloc[0],
                "latitude": parcelle_projected.geometry.centroid.y.iloc[0],
                "longitude": parcelle_projected.geometry.centroid.x.iloc[0],
                "CodeBDN": code_bdn,
                "QRCode": qr_code_path
            }

            image_path = os.path.join(settings.MEDIA_ROOT, 'street_view_images', f'parcelle_{nicad}.png')
            print(f"Chemin de l'image Street View : {image_path}, existe : {os.path.exists(image_path)}")

            street_view_excel = os.path.join(settings.MEDIA_ROOT, 'street_view_links.xlsx')
            street_view_url = "Non disponible"
            if os.path.exists(street_view_excel):
                try:
                    df = pd.read_excel(street_view_excel)
                    nicad_no_zeros = str(nicad).lstrip('0')
                    df['nicad_no_zeros'] = df['nicad'].astype(str).str.lstrip('0')
                    matching_row = df[df['nicad_no_zeros'] == nicad_no_zeros]
                    if not matching_row.empty:
                        street_view_url = matching_row['street_view_url'].iloc[0]
                        print(f"Street View URL trouvé pour {nicad} (comparé sans zéros : {nicad_no_zeros}): {street_view_url}")
                    else:
                        print(f"Aucune correspondance trouvée dans {street_view_excel} pour nicad {nicad} (comparé sans zéros : {nicad_no_zeros})")
                    df = df.drop(columns=['nicad_no_zeros'])
                except Exception as e:
                    print(f"Erreur lors de la lecture de {street_view_excel} : {e}")
            else:
                print(f"Fichier {street_view_excel} non trouvé")

            pdf_path = generate_pdf_report(nicad, data, image_path if os.path.exists(image_path) else None, street_view_url)

            with open(pdf_path, 'rb') as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename=rapport_{nicad}.pdf'
                return response

        except Exception as e:
            print(f"Erreur dans generate_individual_report : {str(e)}")
            return JsonResponse({'error': f"Erreur lors de la génération du rapport : {str(e)}"}, status=400)
    return JsonResponse({'error': 'Méthode non autorisée.'}, status=405)
