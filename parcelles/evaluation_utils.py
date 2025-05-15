# parcelles/evaluation_utils.py
import logging

import ox
import pandas as pd
import numpy as np
from django.conf import settings
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.platypus import Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.conf import settings
from webdriver_manager.chrome import ChromeDriverManager

from parcelles.geo_utils import calculate_heading, calculate_adjusted_view, find_closest_road_point

# Barèmes
bareme_collectif = {
    'A': [180931, 202643, 208071, 208071, 262350, 208071, 208071, 208071, 244257, 189978, 253303],
    'B': [167743, 187872, 192904, 192904, 243227, 192904, 192904, 192904, 226543, 176130, 234840],
    'C': [151162, 169301, 173836, 173836, 219185, 173836, 173836, 173836, 204069, 158720, 211627],
    'D': [131238, 146987, 150924, 150924, 190295, 150924, 150924, 150924, 177171, 137800, 183733],
    'E': [105402, 118050, 121212, 121212, 152833, 121212, 121212, 121212, 142293, 110672, 147563],
    'F': [91520, 102502, 105248, 105248, 132704, 105248, 105248, 105248, 123552, 96096, 128128],
    'G': [69539, 77884, 79970, 79970, 100832, 79970, 79970, 79970, 93878, 73016, 97355],
    'H': [45631, 51107, 52476, 52476, 66165, 52476, 52476, 52476, 61602, 47913, 63883],
    'I': [39847, 44629, 45824, 45824, 57778, 45824, 45824, 45824, 53793, 41839, 55786],
    'J': [33000, 35000, 35000, 35000, 25000, 35000, 35000, 35000, 25000, 34000, 25000],
    'K': [32000, 32000, 32000, 32000, 22000, 33000, 33000, 33000, 22000, 32000, 22000],
    'L': [30000, 30000, 30000, 30000, 20000, 31000, 31000, 31000, 20000, 30000, 20000],
    'M': [11000, 11000, 11000, 11000, 8000, 11000, 11000, 11000, 8000, 11000, 8000]
}

bareme_individuel = {
    '1': [152512, 170813, 175389, 175389, 221142, 175389, 175389, 175389, 205891, 160137, 213516],
    '2': [141395, 158363, 162604, 162604, 205023, 162604, 162604, 162604, 190883, 148465, 197953],
    '3': [134027, 150111, 154132, 154132, 194340, 154132, 154132, 154132, 180937, 140729, 187638],
    '4': [117342, 131423, 134943, 134943, 170146, 134943, 134943, 134943, 158411, 123209, 164278],
    '5': [88846, 99508, 102173, 102173, 128827, 102173, 102173, 102173, 119942, 93288, 124384],
    '6': [65334, 73174, 75134, 75134, 94735, 75134, 75134, 75134, 88201, 68601, 91648],
    '7': [43556, 48783, 50090, 50090, 63157, 50090, 50090, 50090, 58801, 45734, 60979],
    '8': [30121, 33735, 34639, 34639, 43675, 34639, 34639, 34639, 40663, 31627, 42169],
    '9': [15000, 16000, 16000, 16000, 11117, 17000, 17500, 17500, 11117, 15000, 10000],
    '10': [13000, 13000, 13000, 13000, 10000, 15000, 15000, 15000, 10000, 13000, 10000],
    '11': [11000, 11000, 11000, 11000, 8000, 12000, 12000, 12000, 8000, 11000, 8000]
}

bareme_cours = {
    '1': [16000, 16500, 16500, 17000, 17500, 17000, 17000, 17000, 17500, 16500, 17500],
    '2': [12000, 12500, 12500, 13000, 13500, 13000, 13000, 13000, 13500, 12500, 13500],
    '3': [9000, 9500, 9500, 10000, 10500, 10000, 10000, 10000, 10500, 9500, 10500],
    '4': [4000, 45000, 45000, 5000, 5000, 5000, 5000, 5000, 5000, 4500, 5000]
}

bareme_clotures = {
    '1': [35755, 40046, 40046, 41118, 51845, 41118, 41118, 41118, 48269, 37546, 50057],
    '2': [26004, 29124, 29124, 29904, 37705, 29904, 29904, 29904, 35105, 27304, 36405],
    '3': [20803, 23299, 23299, 23923, 30164, 23923, 23923, 23923, 28084, 21843, 29124],
    '4': [19069, 21358, 21358, 21930, 27651, 21930, 21930, 21930, 25744, 20023, 26697],
    '5': [8776, 9829, 9829, 10093, 12726, 10093, 10093, 10093, 11848, 9215, 12287],
    '6': [4009, 4490, 4490, 4610, 5813, 4610, 4610, 4610, 5412, 4209, 5612],
    '7': [813, 910, 910, 935, 1178, 935, 935, 935, 1097, 853, 1138]
}

# Fonctions d'évaluation
def detect_type_bareme(categorie):
    return 'collectif' if categorie.isalpha() else 'individuel'

def get_bareme(region, categorie):
    try:
        index = ['DAKAR', 'Diourbel', 'Fatick', 'Kaolack', 'Kolda', 'Louga', 'Matam',
                 'Saint-Louis', 'Tambacounda', 'Thiès', 'Ziguinchor'].index(region.upper())
        type_bareme = detect_type_bareme(categorie)
        if type_bareme == 'collectif':
            bareme = bareme_collectif.get(categorie)
        elif type_bareme == 'individuel':
            bareme = bareme_individuel.get(categorie)
        else:
            return 0
        return bareme[index] if bareme else 0  # Retourne une valeur unique pour la région
    except ValueError:
        return 0

def calculer_valeur_locaux(gdf, region, type_bareme, categorie):
    resultats = []
    grouped = gdf.groupby('nicad')
    for nicad, group in grouped:
        valeur_totale_locaux = 0
        all_categories = []
        taux_locatif = 0.10

        for _, row in group.iterrows():
            all_categories.append(categorie)
            bareme = get_bareme(region, categorie)
            SB = row.get('assise', 0) or 0
            Nn = row.get('niveaux', 0) or 0
            Aban = row.get('aban', 0)
            Envet = row.get('envet', 1)
            Vois = row.get('vois', 1)


            SHO = SB * Nn
            SU = SHO * 0.78
            SC = SU * Aban * Envet * Vois  # Opérations scalaires
            VL = bareme * SC if bareme else 0
            valeur_totale_locaux += VL

            if type_bareme == 'individuel':
                if categorie == '1':
                    taux_locatif = 0.1344
                elif categorie in ['2', '3']:
                    taux_locatif = 0.12
                else:
                    taux_locatif = 0.10
            elif type_bareme == 'collectif':
                if categorie == 'A':
                    taux_locatif = 0.1344
                elif categorie in ['B', 'C']:
                    taux_locatif = 0.12
                else:
                    taux_locatif = 0.10

        resultats.append({
            "nicad": nicad,
            "Type": "Valeur totale des locaux (FCFA)",
            "Valeur": valeur_totale_locaux,
            "Taux Locatif": taux_locatif,
            "Categorie Locaux": ', '.join(all_categories)
        })
    return resultats

def calculer_valeur_clotures(gdf, region, categorie):
    resultats = []
    for _, row in gdf.iterrows():
        index = ['DAKAR', 'Diourbel', 'Fatick', 'Kaolack', 'Kolda', 'Louga', 'Matam',
                 'Saint-Louis', 'Tambacounda', 'Thiès', 'Ziguinchor'].index(region.upper())
        bareme_list = bareme_clotures.get(categorie)
        bareme_value = bareme_list[index] if bareme_list else 0  # Sélectionne une valeur unique
        LR = row.get('lr', 0) or 0
        Envet = row.get('envet', 1)
        SC = LR * Envet
        VC = bareme_value * SC
        resultats.append({"nicad": row['nicad'], "Type": "Valeur de la clôture (FCFA)", "Valeur": VC})
    return resultats

def calculer_valeur_cours(gdf, region, categorie):
    resultats = []
    for _, row in gdf.iterrows():
        index = ['DAKAR', 'Diourbel', 'Fatick', 'Kaolack', 'Kolda', 'Louga', 'Matam',
                 'Saint-Louis', 'Tambacounda', 'Thiès', 'Ziguinchor'].index(region.upper())
        bareme_list = bareme_cours.get(categorie)
        bareme_value = bareme_list[index] if bareme_list else 0
        SR = row.get('Sr', 0) or 0
        Envet = row.get('envet', 1)
        SC = SR * Envet
        VC = bareme_value * SC
        resultats.append({"nicad": row['nicad'], "Type": "Valeur de la cour (FCFA)", "Valeur": VC})
    return resultats

def calculer_valeur_dependances(gdf, region, type_bareme, categorie):
    resultats = []
    grouped = gdf.groupby('nicad')
    for nicad, group in grouped:
        valeur_totale_dependances = 0
        for _, row in group.iterrows():
            bareme = get_bareme(region, categorie) if categorie else 0
            SB = row.get('Surfaced', 0) or 0
            Envet = row.get('envet', 1)
            SC = SB * Envet
            VD = bareme * SC if bareme else 0
            valeur_totale_dependances += VD
        resultats.append({"nicad": nicad, "Type": "Valeur des dépendances (FCFA)", "Valeur": valeur_totale_dependances})
    return resultats

def calculer_valeur_amenagements(gdf, region):
    resultats = []
    for _, row in gdf.iterrows():
        CoutRvAP = row.get('coutrap', 0) or 0
        VA = CoutRvAP if pd.notna(CoutRvAP) else 0
        resultats.append({"nicad": row['nicad'], "Type": "Valeur des aménagements particuliers (FCFA)", "Valeur": VA})
    return resultats

def calculer_valeur_terrains(gdf, region):
    resultats = []
    for _, row in gdf.iterrows():
        bareme = row.get('Prix_au_m', 0) or 0
        SUPP = row.get('Superficie', 0) or 0
        STB = row.get('assise', 0) or 0
        SB = row.get('Surfaced', 0) or 0

        if pd.isna(bareme) or pd.isna(SUPP) or pd.isna(STB):
            VS = 0
        elif SB == 0:
            if STB == 0:
                VS = bareme * SUPP
            else:
                VS = bareme * (0.5 * STB) + bareme * (SUPP - STB)
        else:
            VS = bareme * (0.5 * (STB + SB)) + bareme * (SUPP - STB - SB)
        resultats.append({"nicad": row['nicad'], "Type": "Valeur du Sol (FCFA)", "Valeur": VS})
    return resultats

def generer_rapport(gdf, region, categorie):
    type_bareme = detect_type_bareme(categorie)
    locaux = calculer_valeur_locaux(gdf, region, type_bareme, categorie)
    locaux_data = pd.DataFrame(locaux)
    clotures = calculer_valeur_clotures(gdf, region, categorie)
    cours = calculer_valeur_cours(gdf, region, categorie)
    dependances = calculer_valeur_dependances(gdf, region, type_bareme, categorie)
    terrains = calculer_valeur_terrains(gdf, region)
    amenagements = calculer_valeur_amenagements(gdf, region)

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

    for column in columns_to_sum + ['Valeur totale (FCFA)', 'Valeur locative (FCFA)', 'CFPB']:
        total_values_pivot[column] = total_values_pivot[column].apply(np.round)

    output_path = os.path.join(settings.MEDIA_ROOT, 'Rapport_Evaluation.xlsx')
    total_values_pivot.to_excel(output_path, index=False)
    return output_path

logger = logging.getLogger(__name__)

def generate_pdf_report(nicad, data, image_path=None, street_view_url="Non disponible", output_folder=None):
    """ Génère un rapport PDF pour une parcelle donnée avec la nouvelle structure """
    if output_folder is None:
        output_folder = os.path.join(settings.MEDIA_ROOT, 'pdf_reports')
    os.makedirs(output_folder, exist_ok=True)

    pdf_path = os.path.join(output_folder, f'rapport_{nicad}.pdf')
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Styles personnalisés
    styles['Title'].fontSize = 14
    styles['Title'].alignment = 1  # Centré
    styles['Heading2'].fontSize = 12
    styles['Normal'].fontSize = 10

    link_style = ParagraphStyle(
        name='LinkStyle',
        parent=styles['Normal'],
        textColor=colors.blue,  # Couleur bleue
        fontSize=10,
        leading=12
    )

    # Chemins des logos et QR code
    logo1_path = os.path.join(settings.STATIC_ROOT, 'images', 'ministere-des-finances-et-du-budget.png')  # Logo du bas
    logo2_path = os.path.join(settings.STATIC_ROOT, 'images', 'LOGO-DGID-WEB.png')  # Logo du haut
    qr_code_path = data['QRCode']

    # Support pour STATICFILES_DIRS en mode DEBUG
    if settings.DEBUG and not os.path.exists(logo1_path):
        for static_dir in settings.STATICFILES_DIRS:
            temp_path = os.path.join(static_dir, 'images', 'ministere-des-finances-et-du-budget.png')
            if os.path.exists(temp_path):
                logo1_path = temp_path
                break
    if settings.DEBUG and not os.path.exists(logo2_path):
        for static_dir in settings.STATICFILES_DIRS:
            temp_path = os.path.join(static_dir, 'images', 'LOGO-DGID-WEB.png')
            if os.path.exists(temp_path):
                logo2_path = temp_path
                break

    # Préparer les éléments pour l'en-tête avec tailles augmentées
    logo1_img = Image(logo1_path, width=3*cm, height=3*cm) if os.path.exists(logo1_path) else Paragraph("", styles['Normal'])  # Logo du bas
    logo2_img = Image(logo2_path, width=3*cm, height=3*cm) if os.path.exists(logo2_path) else Paragraph("", styles['Normal'])  # Logo du haut
    qr_img = Image(qr_code_path, width=3*cm, height=3*cm) if os.path.exists(qr_code_path) else Paragraph("", styles['Normal'])
    code_bdn_text = Paragraph(f"Code BDN : {data['CodeBDN']}", styles['Normal'])

    # Logs pour diagnostic
    if os.path.exists(logo1_path):
        logger.info(f"Logo 1 (Ministère) trouvé à : {logo1_path}")
    else:
        logger.warning(f"Logo 1 (Ministère) non trouvé à : {logo1_path}")
    if os.path.exists(logo2_path):
        logger.info(f"Logo 2 (DGID) trouvé à : {logo2_path}")
    else:
        logger.warning(f"Logo 2 (DGID) non trouvé à : {logo2_path}")
    if os.path.exists(qr_code_path):
        logger.info(f"QR code trouvé à : {qr_code_path}")
    else:
        logger.warning(f"QR code non trouvé à : {qr_code_path}")

    # Combiner "Code BDN" et QR code dans une seule cellule avec un petit espace
    qr_column = [
        code_bdn_text,
        Spacer(1, 0.2*cm),  # Petit espace entre "Code BDN" et QR code
        qr_img
    ]

    # Créer un tableau pour empiler les logos à gauche et "Code BDN" + QR code à droite
    header_data = [
        [logo1_img, Paragraph("", styles['Normal']), qr_column],  # Ligne 1 : Logo DGID et "Code BDN" + QR
        [logo2_img, Paragraph("", styles['Normal']), Paragraph("", styles['Normal'])]  # Ligne 2 : Logo Ministère
    ]
    header_table = Table(header_data, colWidths=[3.5*cm, 11*cm, 3.5*cm])  # Largeurs des colonnes
    header_table.setStyle([
        ('ALIGN', (0, 0), (0, 1), 'LEFT'),  # Logos alignés à gauche
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),  # "Code BDN" + QR alignés à droite
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Centrer verticalement
        ('GRID', (0, 0), (-1, -1), 0, colors.transparent),  # Pas de bordures
        ('LEFTPADDING', (0, 0), (-1, -1), 0),  # Réduire le padding
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ])
    story.append(header_table)

    # Ajouter le texte "DIRECTION DU CADASTRE" sous les logos
    if os.path.exists(logo2_path):
        story.append(Paragraph("DIRECTION DU CADASTRE", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    # Titre
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("RAPPORT D’ÉVALUATION CADASTRALE", styles['Title']))
    story.append(Spacer(1, 1*cm))

    # NICAD
    story.append(Paragraph(f"NICAD : {nicad}", styles['Heading2']))
    story.append(Spacer(1, 0.5*cm))

    # Section : Évaluation des locaux
    story.append(Paragraph("------------------------// EVALUATION DES LOCAUX //------------------------", styles['Heading2']))
    story.append(Paragraph(f"Catégorie :......... <b>{data['Catégorie']}</b>", styles['Normal']))
    story.append(Paragraph(f"Superficie Totale bâtie (en m²) : ……<b>{data['Superficie Totale bâtie (en m²)']}</b>………………", styles['Normal']))
    story.append(Paragraph(f"Valeur Totale des locaux (en FCFA) : ……………………… <b>{data['Valeur Totale des locaux (FCFA)']}</b>", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    # Section : Évaluation du sol et aménagements particuliers
    story.append(Paragraph("--------// EVALUATION DU SOL ET AMENAGEMENTS PARTICULIERS //-------", styles['Heading2']))
    story.append(Paragraph(f"Barème (en FCFA le m²) pratiqué sur les terrains nus du secteur :............  <b>{data['Barème (en FCFA le m²)']}</b>", styles['Normal']))
    story.append(Paragraph(f"Surface terrain non bâti (en m²) SNB :......... <b>{data['Surface terrain non bâti (en m²)']}</b>", styles['Normal']))
    story.append(Paragraph(f"Surface terrain bâti (en m²) STB :......... <b>{data['Surface terrain bâti (en m²)']}</b>", styles['Normal']))
    story.append(Paragraph(f"Valeur du sol (FCFA) : .......  <b>{data['Valeur du sol (FCFA)']}</b>", styles['Normal']))
    story.append(Paragraph(f"Valeur des aménagements particuliers (en FCFA) : ...... <b>{data['Valeur des aménagements particuliers (FCFA)']}</b>", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    # Section : Évaluation des cours, clôtures et dépendances
    story.append(Paragraph("-----// EVALUATION DES COURS, CLOTURES ET DEPENDANCES //---------", styles['Heading2']))
    story.append(Paragraph(f"Longueur de la clôture (en m) : .................... <b>{data['Longueur de la clôture (en m)']}</b>", styles['Normal']))
    story.append(Paragraph(f"Valeur de la clôture (en FCFA) : ......... <b>{data['Valeur de la clôture (en FCFA)']}</b>", styles['Normal']))
    story.append(Paragraph(f"Surface des cours (en m²) : ....... <b>{data['Surface des cours (en m²)']}</b>", styles['Normal']))
    story.append(Paragraph(f"Valeur des cours (en FCFA) : <b>{data['Valeur des cours (en FCFA)']}</b>", styles['Normal']))
    story.append(Paragraph(f"Valeur des dépendances (en FCFA) : <b>{data['Valeur des dépendances (en FCFA)']}</b>", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    # Section : Évaluation de l’immeuble
    story.append(Paragraph("---------------------------// EVALUATION DE L’IMMEUBLE //-----------------------", styles['Heading2']))
    story.append(Paragraph(f"Valeur totale de l’immeuble (FCFA) : ………………………… <b>{data['Valeur totale de l’immeuble (FCFA)']}</b>", styles['Normal']))
    story.append(Paragraph(f"Valeur locative (taux appliqué à {data['Taux appliqué']}) : …………… <b>{data['Valeur locative (FCFA)']}</b>", styles['Normal']))
    story.append(Paragraph(f"CFPB :................ <b>{data['CFPB']}</b>", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph(f"<b>Lien URL</b>: <link href='{street_view_url}' color='blue' underline='true'>{street_view_url}</link>", link_style))
    story.append(Spacer(1, 0.5 * cm))


    # Section : Informations
    story.append(Paragraph("INFORMATIONS", styles['Heading2']))
    story.append(Paragraph(f"Propriétaire : <b>{data['Propriétaire']}</b>", styles['Normal']))
    story.append(Paragraph(f"CNI : <b>{data['CNI']}</b>", styles['Normal']))
    story.append(Paragraph(f"Titre : <b>{data['Titre']}</b>", styles['Normal']))
    story.append(Paragraph(f"Lot : <b>{data['Lot']}</b>", styles['Normal']))
    story.append(Paragraph(f"Niveau : <b>{data['Niveau']}</b>", styles['Normal']))
    story.append(Paragraph(f"Usage : <b>{data['Usage']}</b>", styles['Normal']))
    story.append(Paragraph(f"Superficie Terrain (en m²) : <b>{data['Superficie Terrain (en m²)']}</b>", styles['Normal']))
    story.append(Paragraph(f"Téléphone : <b>{data['Téléphone']}</b>", styles['Normal']))
    story.append(Paragraph(f"Email : <b>{data['Email']}</b>", styles['Normal']))
    story.append(Paragraph(f"NINEA : <b>{data['NINEA']}</b>", styles['Normal']))
    story.append(Paragraph(f"Infos complémentaires : <b>{data['Infos complémentaires']}</b>", styles['Normal']))

    # Section : Street View (utilisation de l'image préexistante)
    if image_path and os.path.exists(image_path):
        logger.info(f"Ajout de l'image Street View au PDF : {image_path}")
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph("Prise de vue :", styles['Normal']))
        img = Image(image_path, width=10 * cm, height=5 * cm)
        story.append(img)
    else:
        logger.warning(f"Aucune image Street View trouvée pour {nicad} à : {image_path}")
        story.append(Paragraph("Prise de vue : Image non disponible", styles['Normal']))
    story.append(Spacer(1, 0.5 * cm))

    # Construire le PDF
    doc.build(story)
    logger.info(f"PDF généré avec succès : {pdf_path}")
    return pdf_path