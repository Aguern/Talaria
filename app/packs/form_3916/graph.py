# Fichier: app/packs/form_3916/graph.py
# VERSION 4.0 - Orchestrateur Pur
import asyncio
from typing import TypedDict, List, Optional, Dict
from pathlib import Path
from langgraph.graph import StateGraph, END
from tools import document_parser, document_classifier, data_extractor
from tools import pdf_generator  # Nouveau système de génération par superposition
from .adapter_final import (
    prepare_data_for_multipage_generation,
    get_coordinates_for_type,
    COORDINATE_MAPPINGS_BY_TYPE
)  # Adaptateur FINAL avec logique adaptative

class Form3916StateExpert(TypedDict):
    input_files: List[Dict[str, bytes]]
    classified_docs: List[Dict[str, dict]]
    extracted_data_list: List[data_extractor.ExtractedData]
    consolidated_data: dict
    missing_fields: List[str]
    question_to_user: Optional[str]
    human_response: Optional[dict]
    pdf_data: Optional[dict]
    generated_pdf: Optional[bytes]

# Champs requis selon le type de compte
REQUIRED_FIELDS_BY_TYPE = {
    "COMPTE_BANCAIRE": [
        "nom", "prenom", "date_naissance", "lieu_naissance", "adresse_complete",
        "numero_compte", "designation_etablissement", "adresse_etablissement",
        "date_ouverture", "nature_compte", "usage_compte"
    ],
    "ACTIFS_NUMERIQUES": [
        "nom", "prenom", "date_naissance", "lieu_naissance", "adresse_complete",
        "email_compte", "psan_name", "date_ouverture",
        "nature_compte", "usage_compte"
    ],
    "ASSURANCE_VIE": [
        "nom", "prenom", "date_naissance", "lieu_naissance", "adresse_complete",
        "designation_contrat", "reference_contrat", "organisme_assurance",
        "nature_compte"
    ]
}

# Fallback pour compatibilité
REQUIRED_FIELDS = REQUIRED_FIELDS_BY_TYPE["COMPTE_BANCAIRE"]

async def classify_documents(state: Form3916StateExpert) -> dict:
    if state.get("classified_docs"):
        print("--- NŒUD: CLASSIFICATION (DÉJÀ FAIT, ON PASSE) ---")
        return {}
    print("--- NŒUD: CLASSIFICATION DES DOCUMENTS ---")
    classified_results = []
    for file_info in state["input_files"]:
        filename = list(file_info.keys())[0]
        file_content = file_info[filename]
        text = document_parser.extract_text_from_file(file_content)
        doc_type = await document_classifier.classify_document(text)
        classified_results.append({
            "filename": filename,
            "text": text,
            "doc_type": doc_type
        })
        print(f"  > Document '{filename}' classifié comme : {doc_type.name}")
    return {"classified_docs": classified_results, "input_files": []}

async def extract_from_all_documents(state: Form3916StateExpert) -> dict:
    print("--- NŒUD: EXTRACTION MULTI-DOCUMENTS ---")
    extraction_tasks = []
    for doc in state["classified_docs"]:
        # IMPORTANT: Traiter TOUS les documents, même INCONNU
        # L'extracteur peut trouver des infos bancaires dans n'importe quel texte
        task = data_extractor.extract_data_from_document(doc["text"], doc["doc_type"])
        extraction_tasks.append(task)
        print(f"  > Extraction lancée pour '{doc['filename']}' (type: {doc['doc_type'].name})")
    extracted_results = await asyncio.gather(*extraction_tasks)
    return {"extracted_data_list": extracted_results}

def consolidate_data(state: Form3916StateExpert) -> dict:
    print("--- NŒUD: CONSOLIDATION DES DONNÉES ---")
    consolidated = {}
    for data in state["extracted_data_list"]:
        data_dict = data.model_dump(exclude_unset=True)
        for key, value in data_dict.items():
            if key not in consolidated and value is not None:
                consolidated[key] = value

    # Mappage des champs de compatibilité
    if 'adresse_complete' not in consolidated and 'adresse' in consolidated:
        consolidated['adresse_complete'] = consolidated['adresse']
    if 'numero_compte' not in consolidated and 'iban' in consolidated:
        consolidated['numero_compte'] = consolidated['iban']
    if 'designation_etablissement' not in consolidated and 'bank_name' in consolidated:
        consolidated['designation_etablissement'] = consolidated['bank_name']

    # Renommer 'account_holder_name' en 'nom' et 'prenom' si l'identité n'a pas été trouvée ailleurs
    if 'nom' not in consolidated and 'account_holder_name' in consolidated and consolidated['account_holder_name']:
        parts = consolidated['account_holder_name'].split()
        if len(parts) > 1:
            consolidated['prenom'] = parts[0]
            consolidated['nom'] = " ".join(parts[1:])

    # Détection automatique du type de compte si non spécifié
    if 'nature_compte' not in consolidated:
        # Détecter selon les données présentes
        if 'iban' in consolidated or 'numero_compte' in consolidated or 'bic' in consolidated:
            consolidated['nature_compte'] = 'COMPTE_BANCAIRE'
            print("  > Type détecté automatiquement: COMPTE_BANCAIRE (présence IBAN/BIC)")
        elif 'crypto_address' in consolidated or 'wallet_address' in consolidated:
            consolidated['nature_compte'] = 'ACTIFS_NUMERIQUES'
            print("  > Type détecté automatiquement: ACTIFS_NUMERIQUES (présence adresse crypto)")
        elif 'police_number' in consolidated or 'contrat_reference' in consolidated:
            consolidated['nature_compte'] = 'ASSURANCE_VIE'
            print("  > Type détecté automatiquement: ASSURANCE_VIE (présence référence contrat)")
        # Si on ne peut pas détecter, on laissera le human-in-the-loop demander

    print(f"  > Données consolidées: {consolidated}")
    return {"consolidated_data": consolidated}

def check_completeness(state: Form3916StateExpert) -> dict:
    print("--- NŒUD: VÉRIFICATION COMPLÉTUDE ---")
    form_data = state.get("consolidated_data", {})

    # Déterminer le type de compte
    nature_compte = form_data.get("nature_compte")

    # Si le type n'est pas défini, c'est un champ manquant critique
    if not nature_compte:
        return {
            "missing_fields": ["nature_compte"],
            "question_to_user": None
        }

    # Sélectionner les champs requis selon le type
    required_fields = REQUIRED_FIELDS_BY_TYPE.get(
        nature_compte,
        REQUIRED_FIELDS_BY_TYPE["COMPTE_BANCAIRE"]
    )

    # Vérifier les champs manquants
    missing = [field for field in required_fields if not form_data.get(field)]

    print(f"  > Type de compte: {nature_compte}")
    print(f"  > Champs manquants: {missing}")

    return {"missing_fields": missing, "question_to_user": None}

def request_human_input(state: Form3916StateExpert) -> dict:
    missing_fields = state.get("missing_fields", [])
    if not missing_fields:
        return {}

    # Question spécifique pour le type de compte
    if "nature_compte" in missing_fields:
        question = (
            "Quel type de compte souhaitez-vous déclarer ?\n"
            "1. Compte bancaire à l'étranger\n"
            "2. Compte d'actifs numériques (crypto-monnaies)\n"
            "3. Contrat d'assurance-vie ou placement similaire\n"
            "Veuillez répondre avec 'COMPTE_BANCAIRE', 'ACTIFS_NUMERIQUES' ou 'ASSURANCE_VIE'"
        )
        return {"question_to_user": question}

    # Questions adaptées selon le type de compte
    form_data = state.get("consolidated_data", {})
    nature_compte = form_data.get("nature_compte")

    # Personnaliser les questions selon le type
    if nature_compte == "ACTIFS_NUMERIQUES" and "email_compte" in missing_fields:
        fields_str = ", ".join(f"'{field}'" for field in missing_fields)
        question = f"Pour votre compte d'actifs numériques, veuillez fournir: {fields_str}"
    elif nature_compte == "ASSURANCE_VIE" and "designation_contrat" in missing_fields:
        fields_str = ", ".join(f"'{field}'" for field in missing_fields)
        question = f"Pour votre contrat d'assurance-vie, veuillez fournir: {fields_str}"
    else:
        fields_str = ", ".join(f"'{field}'" for field in missing_fields)
        question = f"Veuillez fournir les valeurs pour les champs suivants: {fields_str}"

    return {"question_to_user": question}

def process_human_response(state: Form3916StateExpert) -> dict:
    print("--- NŒUD: TRAITEMENT RÉPONSE HUMAINE ---")
    human_response = state.get("human_response")
    if not human_response:
        print("  > Aucune réponse humaine à traiter")
        return {}

    current_data = state.get("consolidated_data", {})
    current_data.update(human_response)
    print(f"  > Données mises à jour avec réponse humaine: {human_response}")

    return {
        "consolidated_data": current_data,
        "question_to_user": None,
        "human_response": None
    }

# --- Nœuds finaux simplifiés ---
def prepare_and_fill_pdf(state: Form3916StateExpert) -> dict:
    """Nœud final qui génère le PDF par superposition multi-pages adaptative."""
    print("--- NŒUD: GÉNÉRATION PDF PAR SUPERPOSITION MULTI-PAGES ---")

    consolidated_data = state["consolidated_data"]
    nature_compte = consolidated_data.get("nature_compte", "COMPTE_BANCAIRE")

    print(f"  > Type de compte: {nature_compte}")

    # 1. Préparer les données pour multi-pages selon le type
    data_by_page = prepare_data_for_multipage_generation(consolidated_data)
    total_fields = sum(len(page_data) for page_data in data_by_page.values())
    print(f"  > {total_fields} champs préparés sur {len(data_by_page)} pages")

    # 2. Récupérer les coordonnées pour ce type de compte
    coordinates_by_page = get_coordinates_for_type(nature_compte)

    # 3. Générer l'overlay multi-pages
    overlay_packet = pdf_generator.generate_multipage_pdf_overlay(
        data_by_page,
        coordinates_by_page
    )

    # 4. Superposer sur le template multi-pages
    template_path = Path(__file__).parent / "3916_4725.pdf"
    pdf_bytes = pdf_generator.superimpose_multipage_pdf(template_path, overlay_packet)
    print(f"  > PDF multi-pages généré ({len(pdf_bytes):,} octets)")

    # 3. Sauvegarder le PDF généré dans le dossier pdf_filled
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent / "pdf_filled"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / f"form_3916_{timestamp}.pdf"
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)
    print(f"  > PDF sauvegardé : {output_path}")

    return {"generated_pdf": pdf_bytes}

def should_request_human_input(state: Form3916StateExpert) -> str:
    return "request_human_input" if state.get("missing_fields") else "prepare_and_fill_pdf"

def entry_point_router(state: Form3916StateExpert) -> str:
    """Aiguille le flux au démarrage/reprise."""
    print("--- AIGUILLAGE D'ENTRÉE ---")
    if state.get("human_response"):
        print(" > Décision: Reprise après intervention humaine.")
        return "process_human_response"
    else:
        print(" > Décision: Démarrage d'une nouvelle tâche.")
        return "classify_documents"

def create_form_3916_graph_expert():
    workflow = StateGraph(Form3916StateExpert)

    # Ajouter tous les nœuds de base
    workflow.add_node("classify_documents", classify_documents)
    workflow.add_node("extract_from_all_documents", extract_from_all_documents)
    workflow.add_node("consolidate_data", consolidate_data)
    workflow.add_node("check_completeness", check_completeness)
    workflow.add_node("request_human_input", request_human_input)
    workflow.add_node("process_human_response", process_human_response)
    workflow.add_node("prepare_and_fill_pdf", prepare_and_fill_pdf)  # Notre nouveau nœud final

    # Point d'entrée conditionnel
    workflow.set_conditional_entry_point(
        entry_point_router,
        {
            "process_human_response": "process_human_response",
            "classify_documents": "classify_documents"
        }
    )

    # Arêtes normales
    workflow.add_edge("classify_documents", "extract_from_all_documents")
    workflow.add_edge("extract_from_all_documents", "consolidate_data")
    workflow.add_edge("consolidate_data", "check_completeness")
    workflow.add_edge("process_human_response", "check_completeness")

    # L'arête de succès pointe maintenant vers le nœud final unifié
    workflow.add_conditional_edges(
        "check_completeness",
        should_request_human_input,
        {
            "request_human_input": "request_human_input",
            "prepare_and_fill_pdf": "prepare_and_fill_pdf",  # <-- MODIFICATION
        },
    )
    workflow.add_edge("prepare_and_fill_pdf", END)

    return workflow.compile()

form_3916_graph_app_v2 = create_form_3916_graph_expert()