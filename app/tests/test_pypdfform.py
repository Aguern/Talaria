#!/usr/bin/env python3
"""
Script de test pour PyPDFForm - Inspection et test du formulaire 3916
"""
import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

def test_pypdfform():
    """Test PyPDFForm avec le formulaire 3916"""

    # Installer PyPDFForm si nécessaire
    try:
        from PyPDFForm import PdfWrapper
        print("✅ PyPDFForm est installé")
    except ImportError:
        print("❌ PyPDFForm n'est pas installé. Installation...")
        os.system("pip install PyPDFForm==1.4.31")
        from PyPDFForm import PdfWrapper

    # Chemin vers le formulaire
    pdf_path = Path("/app/packs/form_3916/3916_4725.pdf")

    if not pdf_path.exists():
        print(f"❌ Fichier PDF introuvable: {pdf_path}")
        return

    print(f"\n📄 Analyse du formulaire: {pdf_path.name}")
    print("="*60)

    try:
        # Créer le wrapper
        pdf = PdfWrapper(str(pdf_path))

        # Obtenir les éléments du formulaire
        # PyPDFForm utilise sample_data pour obtenir la structure
        schema = pdf.sample_data

        if schema:
            print(f"\n📊 Nombre total de champs: {len(schema)}")
            print("\n📋 Liste des champs disponibles:")
            print("-"*40)

            # Trier les champs pour une meilleure lisibilité
            sorted_fields = sorted(schema.keys())

            # Grouper les champs par type
            text_fields = []
            checkbox_fields = []
            other_fields = []

            for field_name in sorted_fields:
                field_info = schema.get(field_name, {})
                # PyPDFForm retourne des métadonnées sur les champs
                # On peut essayer de détecter le type
                if "CAC" in field_name:
                    checkbox_fields.append(field_name)
                elif field_name.startswith("a"):
                    text_fields.append(field_name)
                else:
                    other_fields.append(field_name)

            print("\n🔤 Champs texte (probablement):")
            for field in text_fields[:20]:  # Afficher les 20 premiers
                print(f"  • {field}")
            if len(text_fields) > 20:
                print(f"  ... et {len(text_fields) - 20} autres")

            print("\n☑️ Cases à cocher (probablement):")
            for field in checkbox_fields:
                print(f"  • {field}")

            if other_fields:
                print("\n❓ Autres champs:")
                for field in other_fields:
                    print(f"  • {field}")

            # Test de remplissage avec des données exemple
            print("\n🧪 Test de remplissage avec données exemple...")
            print("-"*40)

            test_data = {
                "a1": "ANGOUGEARD Nicolas",
                "a2": "Né le 29.01.1998 à Ploërmel",
                "a3": "24 BEL ORIENT LES FORGES 56120 FORGES DE LANOUEE",
                "CAC1": True,  # Case compte bancaire
                "a15": "FR7630004002010000652161601",  # IBAN
                "a16": "X",  # Compte courant (marquer avec X au lieu de True)
                "a19": "01.01.2022",  # Date ouverture
                "a21": "BNPPARB ANGERS",
                "a22": "Angers",
                "a23": "X",  # Titulaire en propre (marquer avec X au lieu de True)
                "CAC4": True,  # Usage personnel
                "a74": "Doussard",
                "a75": "26/09/2025"
            }

            # Remplir le PDF et sauvegarder
            output_path = Path("/app/packs/form_3916/pdf_filled/test_pypdfform.pdf")
            output_path.parent.mkdir(exist_ok=True)

            # PyPDFForm retourne un nouveau wrapper après fill()
            filled_pdf = pdf.fill(test_data)

            # Sauvegarder avec la méthode stream
            with open(output_path, "wb") as f:
                f.write(filled_pdf.stream)

            print(f"✅ PDF test généré: {output_path}")
            print(f"📊 Taille: {output_path.stat().st_size:,} octets")

            # Vérifier ce qui a été rempli
            print("\n🔍 Vérification du remplissage...")
            filled_wrapper = PdfWrapper(str(output_path))
            filled_data = filled_wrapper.sample_data

            filled_count = 0
            for field, value in test_data.items():
                if field in filled_data:
                    filled_count += 1

            print(f"✅ {filled_count}/{len(test_data)} champs ont été remplis")

        else:
            print("⚠️ Aucun champ trouvé dans le PDF")

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pypdfform()