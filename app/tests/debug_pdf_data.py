#!/usr/bin/env python3
"""
Script de debug pour voir exactement ce qui est envoyé au PDF
"""
import sys
import os
sys.path.insert(0, '/app')

from packs.form_3916.adapter import prepare_data_for_pdf
from datetime import datetime

# Simuler les données consolidées
consolidated_data = {
    'nom': 'ANGOUGEARD',
    'prenom': 'NICOLAS',
    'date_naissance': '29.01.1998',
    'lieu_naissance': 'Ploërmel',
    'adresse_complete': '24 BEL ORIENT LES FORGES\n56120 FORGES DE LANOUEE',
    'numero_compte': 'FR76 3000 4002 0100 0065 2161 601',
    'designation_etablissement': 'BNPPARB ANGERS (00201)',
    'adresse_etablissement': 'Angers',
    'date_ouverture': '01.01.2022',
    'nature_compte': 'COMPTE_BANCAIRE',
    'usage_compte': 'PERSONNEL'
}

print("Données consolidées:")
print("="*50)
for k, v in consolidated_data.items():
    print(f"  {k}: {v}")

# Préparer les données
pdf_data = prepare_data_for_pdf(consolidated_data)

print("\nDonnées préparées pour le PDF:")
print("="*50)
for k, v in sorted(pdf_data.items()):
    print(f"  {k}: {v} (type: {type(v).__name__})")

print(f"\nTotal: {len(pdf_data)} champs préparés")