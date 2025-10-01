#!/usr/bin/env python3
"""
Script de test avec réponses humaines simulées
"""
import asyncio
from pathlib import Path
import sys
import os
from datetime import datetime

# Ajouter le répertoire parent au PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from packs.form_3916.graph import form_3916_graph_app_v2, Form3916StateExpert

async def test_with_simulated_responses():
    """Test avec réponses humaines simulées"""

    # Chemins des fichiers
    base_dir = Path("/app/packs/form_3916")
    cni_path = base_dir / "CNI.pdf"
    rib_path = base_dir / "RIB Nicolas 2.pdf"

    print("🧪 TEST AVEC RÉPONSES SIMULÉES - Formulaire 3916")
    print("="*60)

    # Lire les fichiers
    with open(cni_path, "rb") as f:
        cni_bytes = f.read()
    with open(rib_path, "rb") as f:
        rib_bytes = f.read()

    # État initial
    initial_state = {
        "input_files": [
            {"CNI.pdf": cni_bytes},
            {"RIB Nicolas 2.pdf": rib_bytes}
        ],
        "classified_docs": None,
        "extracted_data_list": None,
        "consolidated_data": None,
        "missing_fields": None,
        "question_to_user": None,
        "human_response": None,
        "pdf_data": None,
        "generated_pdf": None
    }

    print("\n🚀 Phase 1: Extraction initiale...")
    print("-"*40)

    # Première exécution
    result = await form_3916_graph_app_v2.ainvoke(initial_state)

    # Afficher les données extraites
    if result.get("consolidated_data"):
        print("\n📋 Données extraites automatiquement:")
        for key, value in sorted(result["consolidated_data"].items()):
            if value and key not in ['iban', 'bic', 'bank_name', 'account_holder_name', 'adresse']:
                print(f"  ✓ {key}: {value}")

    # Si on a besoin de données humaines
    if result.get("question_to_user"):
        print(f"\n❓ Question reçue: {result['question_to_user']}")
        print(f"📝 Champs manquants: {', '.join(result.get('missing_fields', []))}")

        # Simuler les réponses humaines avec des données réalistes
        simulated_responses = {
            "date_naissance": "15.06.1985",
            "lieu_naissance": "Paris 14e",
            "adresse_etablissement": "BNPPARB ANGERS, 1 Rue du Commerce, 49000 Angers",
            "date_ouverture": "12.03.2020"
        }

        print("\n🤖 Simulation de réponses humaines:")
        for key, value in simulated_responses.items():
            if key in result.get("missing_fields", []):
                print(f"  → {key}: {value}")

        # Préparer l'état de reprise
        resume_state = result.copy()
        resume_state["human_response"] = {
            k: v for k, v in simulated_responses.items()
            if k in result.get("missing_fields", [])
        }
        resume_state["question_to_user"] = None

        print("\n🚀 Phase 2: Reprise avec les données humaines...")
        print("-"*40)

        # Deuxième exécution avec les réponses
        final_result = await form_3916_graph_app_v2.ainvoke(resume_state)

        if final_result.get("generated_pdf"):
            print("\n✅ PDF GÉNÉRÉ AVEC SUCCÈS!")

            # Trouver le PDF sauvegardé
            pdf_filled_dir = base_dir / "pdf_filled"
            if pdf_filled_dir.exists():
                latest_pdf = max(pdf_filled_dir.glob("form_3916_*.pdf"),
                               key=lambda p: p.stat().st_mtime,
                               default=None)
                if latest_pdf:
                    print(f"📄 Fichier sauvegardé: {latest_pdf.name}")
                    print(f"📊 Taille: {latest_pdf.stat().st_size:,} octets")
                    print(f"📂 Chemin complet: {latest_pdf}")

            # Afficher les données finales consolidées
            if final_result.get("consolidated_data"):
                print("\n📋 Données finales consolidées:")
                print("-"*40)
                for key, value in sorted(final_result["consolidated_data"].items()):
                    if value and key not in ['iban', 'bic', 'bank_name', 'account_holder_name', 'adresse']:
                        print(f"  • {key}: {value}")

            print("\n✨ Processus terminé avec succès!")

        else:
            print("\n⚠️ PDF non généré après reprise")
            if final_result.get("question_to_user"):
                print(f"Nouvelle question: {final_result['question_to_user']}")

    elif result.get("generated_pdf"):
        print("\n✅ PDF généré dès la première phase (toutes les données étaient présentes)!")

    else:
        print("\n⚠️ État inattendu")

    return result

if __name__ == "__main__":
    asyncio.run(test_with_simulated_responses())