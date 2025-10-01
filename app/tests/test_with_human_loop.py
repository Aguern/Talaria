#!/usr/bin/env python3
"""
Script de test interactif pour le formulaire 3916 avec human-in-the-loop
"""
import asyncio
import json
from pathlib import Path
import sys
import os

# Ajouter le répertoire parent au PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from packs.form_3916.graph import form_3916_graph_app_v2, Form3916StateExpert

async def run_interactive_test():
    """Test interactif avec gestion du human-in-the-loop"""

    # Chemins des fichiers
    base_dir = Path("/app/packs/form_3916")
    cni_path = base_dir / "CNI.pdf"
    rib_path = base_dir / "RIB Nicolas 2.pdf"

    print("🧪 TEST INTERACTIF - Formulaire 3916")
    print("="*60)

    # Lire les fichiers
    with open(cni_path, "rb") as f:
        cni_bytes = f.read()
    with open(rib_path, "rb") as f:
        rib_bytes = f.read()

    # État initial
    state = {
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

    # Boucle interactive
    while True:
        print("\n🔄 Exécution du graph...")
        result = await form_3916_graph_app_v2.ainvoke(state)

        # Si on a une question pour l'utilisateur
        if result.get("question_to_user"):
            print("\n" + "="*60)
            print("❓ INTERVENTION HUMAINE REQUISE")
            print("-"*60)
            print(result["question_to_user"])
            print("-"*60)

            if result.get("missing_fields"):
                print(f"\nChamps manquants: {', '.join(result['missing_fields'])}")

            print("\n📝 Entrez les valeurs pour les champs manquants")
            print("Format: champ1:valeur1,champ2:valeur2")
            print("Exemple: date_naissance:01.01.1990,lieu_naissance:Paris")
            print("(ou 'quit' pour arrêter)")

            user_input = input("\n> ")

            if user_input.lower() == 'quit':
                print("Arrêt du test.")
                break

            # Parser la réponse
            human_response = {}
            try:
                for item in user_input.split(','):
                    if ':' in item:
                        key, value = item.split(':', 1)
                        human_response[key.strip()] = value.strip()

                print(f"\n✅ Réponses reçues: {human_response}")

                # Préparer l'état pour la reprise
                state = result.copy()
                state["human_response"] = human_response
                state["question_to_user"] = None

            except Exception as e:
                print(f"❌ Erreur de format: {e}")
                print("Veuillez réessayer.")
                continue

        # Si le PDF est généré
        elif result.get("generated_pdf"):
            print("\n" + "="*60)
            print("✅ PDF GÉNÉRÉ AVEC SUCCÈS!")
            print("-"*60)

            # Trouver le PDF sauvegardé
            pdf_filled_dir = base_dir / "pdf_filled"
            if pdf_filled_dir.exists():
                latest_pdf = max(pdf_filled_dir.glob("form_3916_*.pdf"),
                               key=lambda p: p.stat().st_mtime,
                               default=None)
                if latest_pdf:
                    print(f"📄 Fichier: {latest_pdf}")
                    print(f"📊 Taille: {latest_pdf.stat().st_size:,} octets")

            # Afficher les données consolidées
            if result.get("consolidated_data"):
                print("\n📋 Données finales consolidées:")
                print("-"*40)
                for key, value in sorted(result["consolidated_data"].items()):
                    if value:
                        print(f"  • {key}: {value}")

            print("\n✨ Processus terminé avec succès!")
            break

        else:
            print("\n⚠️ État inattendu")
            print(f"Clés disponibles: {result.keys()}")
            break

    return result

if __name__ == "__main__":
    result = asyncio.run(run_interactive_test())