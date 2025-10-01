#!/usr/bin/env python3
"""
Script pour générer le PDF avec les données utilisateur.
Utilise la nouvelle approche de reprise manuelle.
"""

import asyncio
from pathlib import Path
import sys
from datetime import datetime
sys.path.append(str(Path(__file__).parent.parent))

from packs.form_3916.graph_modern import (
    create_modern_form3916_graph,
    resume_workflow_with_data
)

async def generate_pdf_with_user_data():
    """Génère le PDF avec les données de l'utilisateur."""

    print("=" * 70)
    print("GÉNÉRATION DU FORMULAIRE 3916 AVEC VOS DONNÉES")
    print("=" * 70)

    # 1. Charger les documents
    print("\n📁 Chargement des documents...")
    docs_path = Path(__file__).parent.parent / "packs" / "form_3916"
    documents = []

    revolut_path = docs_path / "Revolut.txt"
    if revolut_path.exists():
        with open(revolut_path, 'rb') as f:
            documents.append({"Revolut.txt": f.read()})
        print("  ✅ Revolut.txt chargé")

    cni_path = docs_path / "CNI.pdf"
    if cni_path.exists():
        with open(cni_path, 'rb') as f:
            documents.append({"CNI.pdf": f.read()})
        print("  ✅ CNI.pdf chargé")

    # 2. Contexte utilisateur
    user_context = """
    J'ai ouvert un compte Revolut en janvier 2023 pour mon usage personnel.
    Je vis actuellement à Doussard.
    C'est un compte courant que j'utilise principalement pour mes voyages.
    Je suis le seul titulaire du compte.
    """

    print("\n📝 Contexte utilisateur:")
    print(user_context)

    # 3. Créer le graphe
    print("\n⚙️ Création du workflow...")
    graph = create_modern_form3916_graph(use_checkpointer=False)

    # 4. État initial
    initial_state = {
        "input_files": documents,
        "user_context": user_context,
        "classified_docs": [],
        "extracted_data_list": [],
        "consolidated_data": {},
        "missing_critical": [],
        "missing_optional": [],
        "skip_optional": False,
        "pdf_data": None,
        "generated_pdf": None
    }

    # 5. Première exécution
    print("\n" + "=" * 50)
    print("ÉTAPE 1: EXTRACTION ET ANALYSE")
    print("=" * 50)

    first_result = await graph.ainvoke(initial_state)

    # 6. Vérifier ce qui manque
    missing_critical = first_result.get("missing_critical", [])
    missing_optional = first_result.get("missing_optional", [])

    if missing_critical:
        print(f"\n⚠ Champs critiques manquants: {missing_critical}")

    if missing_optional:
        print(f"\n📝 Champs optionnels manquants: {missing_optional}")

    # 7. Fournir les données utilisateur
    print("\n" + "=" * 50)
    print("ÉTAPE 2: AJOUT DES DONNÉES UTILISATEUR")
    print("=" * 50)

    # Les données fournies par l'utilisateur
    user_data = {
        "date_naissance": "29/01/1998",
        "lieu_naissance": "Ploërmel",
        "adresse_complete": "135 impasse du Planay, 74210 DOUSSARD",
        "lieu_signature": "Doussard",  # Lieu de signature (Fait à)
        # date_cloture reste vide (pas de clôture)
    }

    print("\n📝 Vos données:")
    for key, value in user_data.items():
        print(f"  • {key}: {value}")

    # 8. Reprendre avec les données mergées directement
    print("\n" + "=" * 50)
    print("ÉTAPE 3: GÉNÉRATION DU PDF AVEC DONNÉES COMPLÈTES")
    print("=" * 50)

    # Créer un état complet avec toutes les données
    complete_state = first_result.copy()

    # Merger les données utilisateur dans consolidated_data
    consolidated = complete_state.get("consolidated_data", {})
    consolidated.update(user_data)
    complete_state["consolidated_data"] = consolidated

    # Retirer les champs manquants qui ont été fournis
    complete_state["missing_optional"] = []
    complete_state["skip_optional"] = True  # Pour éviter la boucle

    # Relancer le workflow depuis la vérification
    final_result = await graph.ainvoke(complete_state)

    # 9. Vérifier le résultat
    if final_result.get("generated_pdf"):
        print("\n" + "=" * 70)
        print("✅ PDF GÉNÉRÉ AVEC SUCCÈS !")
        print("=" * 70)

        # Sauvegarder le PDF
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(__file__).parent.parent / "packs" / "form_3916" / "pdf_filled"
        output_dir.mkdir(exist_ok=True)

        output_path = output_dir / f"form_3916_{timestamp}.pdf"

        with open(output_path, "wb") as f:
            f.write(final_result["generated_pdf"])

        print(f"\n📄 PDF sauvegardé: {output_path}")
        print(f"   Taille: {len(final_result['generated_pdf']):,} octets")

        # Afficher les données consolidées
        print("\n📝 Données dans le formulaire:")
        consolidated = final_result.get("consolidated_data", {})
        for key, value in sorted(consolidated.items()):
            if not key.startswith("_") and value:
                print(f"  • {key}: {value}")

        # Vérifier s'il reste des champs manquants
        if final_result.get("missing_optional"):
            print(f"\n⚠ Champs optionnels non remplis: {final_result['missing_optional']}")
            print("  (Ces champs restent vides dans le PDF)")

        print("\n✅ Processus terminé avec succès!")
        return output_path

    else:
        print("\n❌ Échec de la génération du PDF")
        print(f"État final: {final_result.keys()}")
        return None

if __name__ == "__main__":
    result = asyncio.run(generate_pdf_with_user_data())
    if result:
        print(f"\n✨ Votre formulaire 3916 est prêt: {result}")