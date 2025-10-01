# Fichier: app/packs/form_3916/adapter_final.py
# VERSION FINALE CORRIGÉE - Comprenant la structure réelle du formulaire

from datetime import datetime
from typing import Dict, Any

# COORDONNÉES FINALES CALIBRÉES
# Le formulaire a une structure particulière :
# - Section identité : une seule grande case pour nom, prénom, date et lieu de naissance
# - Cases à cocher : X à gauche du label (coordonnée X faible ~36)
# - Champs texte : écriture à droite ou en dessous du label

COORDINATE_MAPPING = {
    # Page 1 - Section Identité (TOUT dans une seule case en dessous)
    "identite_complete": (85, 520),  # Grande case unique pour toute l'identité

    # Page 1 - Adresse (case séparée en dessous)
    "adresse_ligne1": (85, 460),
    "adresse_ligne2": (85, 445),

    # Page 2 - Nature du compte (X à GAUCHE du label)
    "nature_compte_bancaire_x": (36, 585),  # Case à cocher
    "nature_compte_actifs_numeriques_x": (36, 558),  # Case à cocher
    "nature_contrat_assurance_vie_x": (36, 532),  # Case à cocher

    # Page 2 - Informations compte (écriture À DROITE ou EN DESSOUS du label)
    "numero_compte": (85, 480),  # En dessous du label "Numéro de compte"
    "type_compte_courant_x": (85, 455),  # Case à cocher type de compte
    "type_compte_epargne_x": (180, 455),  # Case à cocher
    "type_compte_autres_x": (275, 455),  # Case à cocher
    "date_ouverture": (150, 430),  # À droite du label "Date d'ouverture"
    "date_cloture": (350, 430),  # À droite du label "Date de clôture"
    "designation_etablissement": (85, 405),  # En dessous du label
    "adresse_etablissement": (85, 380),  # En dessous du label
    "modalite_titulaire_x": (85, 355),  # Case à cocher modalité
    "modalite_procuration_x": (250, 355),  # Case à cocher

    # Page 3 - Usage (X à GAUCHE du label)
    "usage_personnel_x": (36, 199),  # Case à cocher
    "usage_professionnel_x": (36, 179),  # Case à cocher
    "usage_mixte_x": (36, 159),  # Case à cocher

    # Page 4 - Signature (écriture À DROITE du label)
    "lieu_signature": (260, 93),  # À droite de "Fait à"
    "date_signature": (380, 93),  # À droite de "le"
}

def prepare_data_for_pdf_generation(consolidated_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prépare les données consolidées pour la génération par superposition.
    Gère la structure particulière du formulaire 3916.
    """
    pdf_data = {}
    data = consolidated_data.copy()

    # SECTION 1 - IDENTITÉ COMPLÈTE DANS UNE SEULE CASE
    # Format : "NOM Prénom - Né(e) le JJ/MM/AAAA à Ville"
    identite_parts = []

    # Nom et prénom
    nom = data.get('nom', '').upper()
    prenom = data.get('prenom', '')
    if nom or prenom:
        identite_parts.append(f"{nom} {prenom}".strip())

    # Date et lieu de naissance
    date_naissance = data.get('date_naissance', '')
    lieu_naissance = data.get('lieu_naissance', '')
    if date_naissance or lieu_naissance:
        naissance = []
        if date_naissance:
            naissance.append(f"Né(e) le {date_naissance}")
        if lieu_naissance:
            naissance.append(f"à {lieu_naissance}")
        identite_parts.append(" ".join(naissance))

    if identite_parts:
        pdf_data["identite_complete"] = " - ".join(identite_parts)

    # SECTION 2 - ADRESSE (sur deux lignes si nécessaire)
    adresse = data.get('adresse_complete', data.get('adresse', ''))
    if adresse:
        lignes = adresse.split('\n')
        if len(lignes) >= 1:
            pdf_data["adresse_ligne1"] = lignes[0][:60]  # Max 60 caractères
        if len(lignes) >= 2:
            pdf_data["adresse_ligne2"] = ' '.join(lignes[1:])[:60]

    # SECTION 3 - NATURE DU COMPTE (cases à cocher)
    nature = data.get("nature_compte", "COMPTE_BANCAIRE")
    if nature == "COMPTE_BANCAIRE":
        pdf_data["nature_compte_bancaire_x"] = "X"
    elif nature == "COMPTE_ACTIFS_NUMERIQUES":
        pdf_data["nature_compte_actifs_numeriques_x"] = "X"
    elif nature == "CONTRAT_ASSURANCE_VIE":
        pdf_data["nature_contrat_assurance_vie_x"] = "X"

    # SECTION 4 - INFORMATIONS COMPTE
    if data.get("numero_compte"):
        # Formater l'IBAN avec espaces pour lisibilité
        iban = data["numero_compte"].replace(" ", "")
        if len(iban) >= 27 and iban.startswith("FR"):
            # Format standard français
            iban_formate = f"{iban[0:4]} {iban[4:8]} {iban[8:12]} {iban[12:16]} {iban[16:20]} {iban[20:24]} {iban[24:27]}"
            pdf_data["numero_compte"] = iban_formate
        else:
            pdf_data["numero_compte"] = data["numero_compte"]

    # Type de compte (cases à cocher)
    type_compte = data.get("type_compte", "COURANT")
    if type_compte == "COURANT":
        pdf_data["type_compte_courant_x"] = "X"
    elif type_compte == "EPARGNE":
        pdf_data["type_compte_epargne_x"] = "X"
    else:
        pdf_data["type_compte_autres_x"] = "X"

    # Dates
    if data.get("date_ouverture"):
        pdf_data["date_ouverture"] = data["date_ouverture"]

    if data.get("date_cloture"):
        pdf_data["date_cloture"] = data["date_cloture"]

    # Établissement
    if data.get("designation_etablissement"):
        pdf_data["designation_etablissement"] = data["designation_etablissement"][:50]

    if data.get("adresse_etablissement"):
        pdf_data["adresse_etablissement"] = data["adresse_etablissement"][:60]

    # Modalité de détention (cases à cocher)
    modalite = data.get("modalite_detention", "TITULAIRE")
    if modalite == "TITULAIRE":
        pdf_data["modalite_titulaire_x"] = "X"
    elif modalite == "PROCURATION":
        pdf_data["modalite_procuration_x"] = "X"

    # SECTION 5 - USAGE (cases à cocher)
    usage = data.get("usage_compte", "PERSONNEL")
    if usage == "PERSONNEL":
        pdf_data["usage_personnel_x"] = "X"
    elif usage == "PROFESSIONNEL":
        pdf_data["usage_professionnel_x"] = "X"
    elif usage == "MIXTE":
        pdf_data["usage_mixte_x"] = "X"

    # SECTION 6 - SIGNATURE
    pdf_data["lieu_signature"] = data.get("lieu_signature", "Doussard")
    pdf_data["date_signature"] = data.get("date_signature", datetime.now().strftime("%d/%m/%Y"))

    return pdf_data

# Mapping adaptatif par type de compte
# Chaque type de compte a ses propres coordonnées de pages

COORDINATE_MAPPINGS_BY_TYPE = {
    "COMPTE_BANCAIRE": {
        0: {  # Page 1 - Identité et adresse
            "identite_complete": (100, 535),  # Coordonnées validées dans test_single_pdf.py
            "adresse_ligne1": (100, 465),
            "adresse_ligne2": (100, 450),
        },
        1: {  # Page 2 - Nature compte bancaire + détails bancaires
            "nature_compte_bancaire_x": (68, 763),  # Case à cocher validée
            "numero_compte": (160, 662),
            "type_compte_courant_x": (70, 625),
            "type_compte_epargne_x": (70, 610),
            "type_compte_autres_x": (70, 595),
            "designation_etablissement": (70, 537),
            "adresse_etablissement": (80, 510),
            "modalite_titulaire_x": (70, 475),
        },
        2: {  # Page 3 - Usage
            "usage_personnel_x": (66, 770),
            "usage_professionnel_x": (66, 743),
            "usage_mixte_x": (66, 716),
        },
        3: {  # Page 4 - Signature
            "lieu_signature": (250, 405),
            "date_signature": (410, 405),
        }
    },
    "ACTIFS_NUMERIQUES": {
        0: {  # Page 1 - Identité et adresse (mêmes que compte bancaire)
            "identite_complete": (100, 535),
            "adresse_ligne1": (100, 465),
            "adresse_ligne2": (100, 450),
        },
        1: {  # Page 2 - Nature actifs numériques + détails crypto
            "nature_compte_actifs_numeriques_x": (68, 745),  # Case à cocher validée
            "email_compte": (80, 365),  # Email ou numéro de compte validé
            "titulaire_propre_actifs_x": (69, 160),  # Coordonnée validée (+3 en X)
            "date_ouverture_crypto": (150, 430),
            "date_cloture_crypto": (350, 430),
            "psan_name": (85, 390),  # Nom du PSAN
            "psan_address": (85, 365),  # Adresse du PSAN
            "psan_url": (85, 340),  # URL du PSAN
        },
        2: {  # Page 3 - Usage (mêmes coordonnées)
            "usage_personnel_x": (66, 770),
            "usage_professionnel_x": (66, 743),
            "usage_mixte_x": (66, 716),
        },
        3: {  # Page 4 - Signature
            "lieu_signature": (250, 405),
            "date_signature": (410, 405),
        }
    },
    "ASSURANCE_VIE": {
        0: {  # Page 1 - Identité et adresse (mêmes coordonnées validées)
            "identite_complete": (100, 535),
            "adresse_ligne1": (100, 465),
            "adresse_ligne2": (100, 450),
        },
        1: {  # Page 2 - Nature assurance-vie
            "nature_contrat_assurance_vie_x": (68, 730),  # Case à cocher validée
        },
        2: {  # Page 3 - Détails contrat assurance-vie
            "designation_contrat": (85, 380),
            "reference_contrat": (85, 355),
            "organisme_assurance": (85, 330),
            "adresse_organisme": (85, 305),
        },
        3: {  # Page 4 - Suite assurance-vie + Signature
            "nature_risques": (85, 450),
            "date_souscription": (150, 420),
            "valeur_rachat": (85, 380),
            "lieu_signature": (250, 405),
            "date_signature": (410, 405),
        }
    }
}

# Keep backward compatibility
COORDINATE_MAPPING_BY_PAGE = COORDINATE_MAPPINGS_BY_TYPE.get("COMPTE_BANCAIRE", {})

def prepare_data_for_multipage_generation(consolidated_data: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    """
    Prépare les données pour génération multi-pages adaptative selon le type de compte.
    """
    # Déterminer le type de compte
    nature = consolidated_data.get("nature_compte", "COMPTE_BANCAIRE")

    # Sélectionner le mapping approprié
    if nature not in COORDINATE_MAPPINGS_BY_TYPE:
        # Fallback to banking account if unknown type
        nature = "COMPTE_BANCAIRE"

    coordinate_mapping = COORDINATE_MAPPINGS_BY_TYPE[nature]

    # Préparer les données selon le type
    all_data = prepare_data_for_pdf_generation(consolidated_data)
    data_by_page = {}

    for page_num, page_fields in coordinate_mapping.items():
        page_data = {}
        for field_name in page_fields.keys():
            if field_name in all_data:
                page_data[field_name] = all_data[field_name]
        if page_data:
            data_by_page[page_num] = page_data

    return data_by_page

def get_coordinates_for_type(account_type: str) -> Dict[int, Dict[str, tuple]]:
    """
    Retourne les coordonnées appropriées pour un type de compte donné.
    """
    if account_type not in COORDINATE_MAPPINGS_BY_TYPE:
        account_type = "COMPTE_BANCAIRE"
    return COORDINATE_MAPPINGS_BY_TYPE[account_type]