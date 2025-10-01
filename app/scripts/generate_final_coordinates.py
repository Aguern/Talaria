#!/usr/bin/env python3
"""
Script pour générer le code des coordonnées finales à intégrer dans adapter_final.py
"""

# COORDONNÉES FINALES VALIDÉES
FINAL_COORDS = {
    # PAGE 1
    "identite_complete": (100, 535),
    "adresse_ligne1": (100, 465),
    "adresse_ligne2": (100, 450),

    # PAGE 2 - Nature du compte
    "nature_compte_bancaire_x": (68, 763),
    "nature_compte_actifs_numeriques_x": (68, 745),
    "nature_contrat_assurance_vie_x": (68, 730),

    # PAGE 2 - Détails compte bancaire
    "numero_compte": (160, 662),
    "type_compte_courant_x": (70, 625),
    "type_compte_epargne_x": (70, 610),
    "type_compte_autres_x": (70, 595),
    "designation_etablissement": (70, 537),
    "adresse_etablissement": (80, 510),
    "modalite_titulaire_x": (70, 475),

    # PAGE 2 - Actifs numériques
    "email_compte": (80, 365),
    "titulaire_propre_actifs_x": (69, 160),

    # PAGE 3 - Usage
    "usage_personnel_x": (66, 770),
    "usage_professionnel_x": (66, 743),
    "usage_mixte_x": (66, 716),

    # PAGE 4 - Signature
    "lieu_signature": (250, 405),
    "date_signature": (410, 405),
}

print("# COORDONNÉES FINALES VALIDÉES POUR adapter_final.py")
print("# Copier-coller ce code pour remplacer COORDINATE_MAPPINGS_BY_TYPE")
print()
print("COORDINATE_MAPPINGS_BY_TYPE = {")
print('    "COMPTE_BANCAIRE": {')
print('        0: {  # Page 1 - Identité et adresse')
print(f'            "identite_complete": {FINAL_COORDS["identite_complete"]},')
print(f'            "adresse_ligne1": {FINAL_COORDS["adresse_ligne1"]},')
print(f'            "adresse_ligne2": {FINAL_COORDS["adresse_ligne2"]},')
print('        },')
print('        1: {  # Page 2 - Nature compte bancaire + détails')
print(f'            "nature_compte_bancaire_x": {FINAL_COORDS["nature_compte_bancaire_x"]},')
print(f'            "numero_compte": {FINAL_COORDS["numero_compte"]},')
print(f'            "type_compte_courant_x": {FINAL_COORDS["type_compte_courant_x"]},')
print(f'            "type_compte_epargne_x": {FINAL_COORDS["type_compte_epargne_x"]},')
print(f'            "type_compte_autres_x": {FINAL_COORDS["type_compte_autres_x"]},')
print(f'            "designation_etablissement": {FINAL_COORDS["designation_etablissement"]},')
print(f'            "adresse_etablissement": {FINAL_COORDS["adresse_etablissement"]},')
print(f'            "modalite_titulaire_x": {FINAL_COORDS["modalite_titulaire_x"]},')
print('        },')
print('        2: {  # Page 3 - Usage')
print(f'            "usage_personnel_x": {FINAL_COORDS["usage_personnel_x"]},')
print(f'            "usage_professionnel_x": {FINAL_COORDS["usage_professionnel_x"]},')
print(f'            "usage_mixte_x": {FINAL_COORDS["usage_mixte_x"]},')
print('        },')
print('        3: {  # Page 4 - Signature')
print(f'            "lieu_signature": {FINAL_COORDS["lieu_signature"]},')
print(f'            "date_signature": {FINAL_COORDS["date_signature"]},')
print('        }')
print('    },')
print('    "ACTIFS_NUMERIQUES": {')
print('        0: {  # Page 1')
print(f'            "identite_complete": {FINAL_COORDS["identite_complete"]},')
print(f'            "adresse_ligne1": {FINAL_COORDS["adresse_ligne1"]},')
print(f'            "adresse_ligne2": {FINAL_COORDS["adresse_ligne2"]},')
print('        },')
print('        1: {  # Page 2')
print(f'            "nature_compte_actifs_numeriques_x": {FINAL_COORDS["nature_compte_actifs_numeriques_x"]},')
print(f'            "email_compte": {FINAL_COORDS["email_compte"]},')
print(f'            "titulaire_propre_actifs_x": {FINAL_COORDS["titulaire_propre_actifs_x"]},')
print('        },')
print('        2: {  # Page 3')
print(f'            "usage_personnel_x": {FINAL_COORDS["usage_personnel_x"]},')
print(f'            "usage_professionnel_x": {FINAL_COORDS["usage_professionnel_x"]},')
print(f'            "usage_mixte_x": {FINAL_COORDS["usage_mixte_x"]},')
print('        },')
print('        3: {  # Page 4')
print(f'            "lieu_signature": {FINAL_COORDS["lieu_signature"]},')
print(f'            "date_signature": {FINAL_COORDS["date_signature"]},')
print('        }')
print('    },')
print('    "ASSURANCE_VIE": {')
print('        0: {  # Page 1')
print(f'            "identite_complete": {FINAL_COORDS["identite_complete"]},')
print(f'            "adresse_ligne1": {FINAL_COORDS["adresse_ligne1"]},')
print(f'            "adresse_ligne2": {FINAL_COORDS["adresse_ligne2"]},')
print('        },')
print('        1: {  # Page 2')
print(f'            "nature_contrat_assurance_vie_x": {FINAL_COORDS["nature_contrat_assurance_vie_x"]},')
print('        },')
print('        3: {  # Page 4')
print(f'            "lieu_signature": {FINAL_COORDS["lieu_signature"]},')
print(f'            "date_signature": {FINAL_COORDS["date_signature"]},')
print('        }')
print('    }')
print('}')