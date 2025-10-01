#!/usr/bin/env python3
"""
Script de test avec les vraies données de l'utilisateur
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

async def test_with_real_user_data():
    """Test avec les vraies données de l'utilisateur"""

    # Chemins des fichiers
    base_dir = Path("/app/packs/form_3916")
    cni_path = base_dir / "CNI.pdf"
    rib_path = base_dir / "RIB Nicolas 2.pdf"

    print("🧪 TEST AVEC DONNÉES RÉELLES - Formulaire 3916")
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

    print("\n🚀 Phase 1: Extraction initiale des documents...")
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
        print(f"\n❓ Question système: {result['question_to_user']}")
        print(f"📝 Champs manquants: {', '.join(result.get('missing_fields', []))}")

        # Utiliser les vraies données fournies par l'utilisateur
        real_user_responses = {
            "date_naissance": "29.01.1998",  # Converti au format JJ.MM.AAAA
            "lieu_naissance": "Ploërmel",
            "adresse_etablissement": "Angers",
            "date_ouverture": "01.01.2022"  # Complété avec une date complète
        }

        print("\n👤 Données réelles de l'utilisateur:")
        for key, value in real_user_responses.items():
            if key in result.get("missing_fields", []):
                print(f"  → {key}: {value}")

        # Préparer l'état de reprise
        resume_state = result.copy()
        resume_state["human_response"] = {
            k: v for k, v in real_user_responses.items()
            if k in result.get("missing_fields", [])
        }
        resume_state["question_to_user"] = None

        print("\n🚀 Phase 2: Génération du PDF avec toutes les données...")
        print("-"*40)

        # Deuxième exécution avec les vraies données
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
                    print(f"📄 Fichier généré: {latest_pdf.name}")
                    print(f"📊 Taille: {latest_pdf.stat().st_size:,} octets")
                    print(f"📂 Emplacement: {latest_pdf}")

            # Afficher le récapitulatif des données finales
            if final_result.get("consolidated_data"):
                print("\n📋 RÉCAPITULATIF DES DONNÉES DU FORMULAIRE 3916:")
                print("="*60)

                print("\n🆔 IDENTITÉ DU DÉCLARANT:")
                data = final_result["consolidated_data"]
                print(f"  • Nom: {data.get('nom', 'N/A')}")
                print(f"  • Prénom: {data.get('prenom', 'N/A')}")
                print(f"  • Date de naissance: {data.get('date_naissance', 'N/A')}")
                print(f"  • Lieu de naissance: {data.get('lieu_naissance', 'N/A')}")
                print(f"  • Adresse: {data.get('adresse_complete', 'N/A')}")

                print("\n💳 COMPTE BANCAIRE:")
                print(f"  • Numéro de compte (IBAN): {data.get('numero_compte', 'N/A')}")
                print(f"  • Établissement: {data.get('designation_etablissement', 'N/A')}")
                print(f"  • Adresse établissement: {data.get('adresse_etablissement', 'N/A')}")
                print(f"  • Date d'ouverture: {data.get('date_ouverture', 'N/A')}")
                print(f"  • Nature: {data.get('nature_compte', 'N/A')}")
                print(f"  • Usage: {data.get('usage_compte', 'N/A')}")

            print("\n✨ Le formulaire 3916 a été rempli avec succès!")
            print("📎 Le PDF est prêt à être téléchargé ou envoyé.")

        else:
            print("\n⚠️ Erreur lors de la génération du PDF")
            if final_result.get("question_to_user"):
                print(f"Nouvelle question: {final_result['question_to_user']}")

    elif result.get("generated_pdf"):
        print("\n✅ PDF généré dès la première phase!")

    else:
        print("\n⚠️ État inattendu")

    return result

if __name__ == "__main__":
    print("Démarrage du test avec les données réelles de Nicolas Angougeard...")
    print()
    asyncio.run(test_with_real_user_data())