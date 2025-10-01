#!/usr/bin/env python3
"""
Script de test pour le formulaire 3916 avec les vrais documents
"""
import asyncio
import base64
from pathlib import Path
import sys
import os

# Ajouter le répertoire parent au PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from packs.form_3916.graph import form_3916_graph_app_v2, Form3916StateExpert

async def test_with_real_documents():
    """Test avec les documents CNI.pdf et RIB Nicolas 2.pdf"""

    # Chemins des fichiers
    base_dir = Path("/app/packs/form_3916")
    cni_path = base_dir / "CNI.pdf"
    rib_path = base_dir / "RIB Nicolas 2.pdf"

    # Vérifier que les fichiers existent
    if not cni_path.exists():
        print(f"❌ Fichier CNI.pdf introuvable : {cni_path}")
        return
    if not rib_path.exists():
        print(f"❌ Fichier RIB introuvable : {rib_path}")
        return

    print("✅ Fichiers trouvés")
    print(f"  - CNI: {cni_path}")
    print(f"  - RIB: {rib_path}")

    # Lire les fichiers
    with open(cni_path, "rb") as f:
        cni_bytes = f.read()
    with open(rib_path, "rb") as f:
        rib_bytes = f.read()

    # Préparer l'état initial
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

    print("\n🚀 Démarrage du processus d'extraction...")
    print("="*60)

    # Exécuter le graph
    result = await form_3916_graph_app_v2.ainvoke(initial_state)

    # Vérifier si on a une question pour l'utilisateur (human-in-the-loop)
    if result.get("question_to_user"):
        print("\n❓ QUESTION POUR L'UTILISATEUR:")
        print("-"*40)
        print(result["question_to_user"])
        print("-"*40)
        print("\n⏸️  En attente de réponse humaine...")
        print("Le système attend votre intervention via l'API.")

        # Afficher les champs manquants pour info
        if result.get("missing_fields"):
            print(f"\nChamps manquants détectés: {', '.join(result['missing_fields'])}")

        return result

    # Si on arrive ici, le PDF a été généré
    if result.get("generated_pdf"):
        print("\n✅ PDF généré avec succès!")

        # Le PDF est déjà sauvegardé dans pdf_filled par le graph
        pdf_filled_dir = base_dir / "pdf_filled"
        latest_pdf = max(pdf_filled_dir.glob("form_3916_*.pdf"), key=lambda p: p.stat().st_mtime, default=None)

        if latest_pdf:
            print(f"📄 PDF sauvegardé : {latest_pdf}")
            print(f"📊 Taille : {latest_pdf.stat().st_size:,} octets")

        # Afficher les données consolidées
        if result.get("consolidated_data"):
            print("\n📋 Données extraites et consolidées:")
            print("-"*40)
            for key, value in result["consolidated_data"].items():
                if value:
                    print(f"  • {key}: {value}")
    else:
        print("\n⚠️ Aucun PDF généré")
        print("État final:", result.keys())

    return result

async def resume_with_human_response(session_state, human_answers):
    """
    Reprendre le processus après une réponse humaine

    Args:
        session_state: L'état retourné par le premier appel
        human_answers: Dict avec les réponses aux champs manquants
    """
    print("\n🔄 Reprise du processus avec les réponses humaines...")
    print(f"Réponses fournies: {human_answers}")

    # Préparer l'état de reprise
    resume_state = session_state.copy()
    resume_state["human_response"] = human_answers
    resume_state["question_to_user"] = None

    # Relancer le graph
    result = await form_3916_graph_app_v2.ainvoke(resume_state)

    if result.get("generated_pdf"):
        print("\n✅ PDF généré avec succès après intervention humaine!")

        base_dir = Path("/app/packs/form_3916")
        pdf_filled_dir = base_dir / "pdf_filled"
        latest_pdf = max(pdf_filled_dir.glob("form_3916_*.pdf"), key=lambda p: p.stat().st_mtime, default=None)

        if latest_pdf:
            print(f"📄 PDF final : {latest_pdf}")

    return result

if __name__ == "__main__":
    print("🧪 TEST RÉEL - Formulaire 3916 avec CNI et RIB")
    print("="*60)

    # Lancer le test
    result = asyncio.run(test_with_real_documents())

    # Si on a besoin d'une intervention humaine
    if result and result.get("question_to_user"):
        print("\n" + "="*60)
        print("ℹ️  Pour reprendre le processus, utilisez:")
        print("await resume_with_human_response(result, {'champ1': 'valeur1', ...})")