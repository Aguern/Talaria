# Fichier: app/packs/form_3916/graph_modern.py
# VERSION 5.0 - Orchestrateur Moderne avec LangGraph Sept 2025

import asyncio
from typing import TypedDict, List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.types import Command, interrupt
from langchain_openai import ChatOpenAI
import os

from tools import document_parser, document_classifier, data_extractor
from tools import pdf_generator
from .adapter_final import (
    prepare_data_for_multipage_generation,
    get_coordinates_for_type,
    COORDINATE_MAPPINGS_BY_TYPE
)

# ==================== ÉTAT MODERNISÉ ====================

class Form3916StateModern(TypedDict):
    """État modernisé avec support du contexte utilisateur."""
    input_files: List[Dict[str, bytes]]
    user_context: Optional[str]  # Contexte fourni par l'utilisateur
    classified_docs: List[Dict[str, dict]]
    extracted_data_list: List[data_extractor.ExtractedData]
    consolidated_data: dict
    missing_critical: List[str]  # Champs obligatoires manquants
    missing_optional: List[str]  # Champs optionnels manquants
    pdf_data: Optional[dict]
    generated_pdf: Optional[bytes]
    skip_optional: bool  # Flag pour ignorer les champs optionnels
    iteration_count: int  # Compteur pour éviter les boucles infinies

# ==================== DÉFINITION DES CHAMPS ====================

# Champs absolument nécessaires pour générer un PDF utile
CRITICAL_FIELDS = [
    "nom", "prenom",
    "date_naissance", "lieu_naissance",
    "adresse_complete",
    "numero_compte", "designation_etablissement"
]

# Champs souhaitables mais non bloquants
OPTIONAL_FIELDS = [
    "date_ouverture", "date_cloture",
    "adresse_etablissement",
    "lieu_signature"  # Ajout du lieu de signature (Fait à)
]

# Valeurs par défaut pour certains champs
DEFAULT_VALUES = {
    "modalite_detention": "TITULAIRE",
    "type_compte": "COURANT",
    "usage_compte": "PERSONNEL",
    "nature_compte": "COMPTE_BANCAIRE"  # Par défaut pour ce sprint
}

# ==================== NŒUDS DU WORKFLOW ====================

async def classify_documents(state: Form3916StateModern) -> dict:
    """Classification des documents uploadés."""
    if state.get("classified_docs"):
        print("--- CLASSIFICATION: Déjà fait ---")
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
        print(f"  > '{filename}' → {doc_type.name}")

    return {"classified_docs": classified_results, "input_files": []}

async def extract_from_all_documents_direct(state: Form3916StateModern) -> dict:
    """Extraction directe universelle sans classification préalable."""
    print("--- NŒUD: EXTRACTION DIRECTE UNIVERSELLE ---")

    extraction_tasks = []
    processed_files = []

    for file_info in state["input_files"]:
        filename = list(file_info.keys())[0]
        file_content = file_info[filename]
        text = document_parser.extract_text_from_file(file_content)

        # Extraction universelle - l'IA comprend le contexte et extrait ce qui est pertinent
        task = data_extractor.extract_data_from_document_universal(text, filename)
        extraction_tasks.append(task)

        processed_files.append({
            "filename": filename,
            "text": text
        })
        print(f"  > Extraction universelle: '{filename}'")

    extracted_results = await asyncio.gather(*extraction_tasks)

    # Créer une liste de documents traités pour la compatibilité
    classified_docs = [{"filename": f["filename"], "text": f["text"], "doc_type": "AUTO"}
                      for f in processed_files]

    return {
        "extracted_data_list": extracted_results,
        "classified_docs": classified_docs,
        "input_files": []  # Vider après traitement
    }

def consolidate_data(state: Form3916StateModern) -> dict:
    """Consolidation des données extraites."""
    print("--- NŒUD: CONSOLIDATION DES DONNÉES ---")

    # IMPORTANT: Partir des données déjà consolidées pour ne pas les perdre
    consolidated = state.get("consolidated_data", {}).copy()

    # Merger les nouvelles données extraites sans écraser les existantes
    for data in state["extracted_data_list"]:
        data_dict = data.model_dump(exclude_unset=True)
        for key, value in data_dict.items():
            # Ne pas écraser une valeur existante avec une nouvelle
            if key not in consolidated and value is not None:
                consolidated[key] = value

    # Mappages de compatibilité
    if 'adresse_complete' not in consolidated and 'adresse' in consolidated:
        consolidated['adresse_complete'] = consolidated['adresse']
    if 'numero_compte' not in consolidated and 'iban' in consolidated:
        consolidated['numero_compte'] = consolidated['iban']
    if 'designation_etablissement' not in consolidated and 'bank_name' in consolidated:
        consolidated['designation_etablissement'] = consolidated['bank_name']

    # Extraction nom/prénom depuis account_holder_name si nécessaire
    if 'nom' not in consolidated and 'account_holder_name' in consolidated:
        parts = consolidated['account_holder_name'].split()
        if len(parts) > 1:
            consolidated['prenom'] = parts[0]
            consolidated['nom'] = " ".join(parts[1:])

    print(f"  > Données consolidées: {len(consolidated)} champs")
    return {"consolidated_data": consolidated}

async def analyze_user_context(state: Form3916StateModern) -> dict:
    """Analyse du contexte utilisateur pour enrichir les données."""
    print("--- NŒUD: ANALYSE DU CONTEXTE UTILISATEUR ---")

    context = state.get("user_context", "")
    # IMPORTANT: Copier les données consolidées pour ne pas les perdre
    consolidated = state.get("consolidated_data", {}).copy()

    if context:
        print(f"  > Contexte fourni: '{context[:100]}...'")

        # Utiliser l'IA pour extraire des informations du contexte
        llm = ChatOpenAI(temperature=0)

        prompt = f"""
        Contexte utilisateur: {context}

        Extrais UNIQUEMENT les informations explicitement mentionnées:
        - Type de compte: courant, épargne, ou autre
        - Usage: personnel, professionnel, ou mixte
        - Modalité: titulaire seul, procuration
        - Dates mentionnées (format JJ/MM/AAAA)
        - Lieu de signature: ville où vit actuellement l'utilisateur (exemple: "Doussard" si mentionné)

        IMPORTANT:
        - NE PAS déduire si c'est un compte étranger
        - NE PAS inventer d'informations
        - Retourner uniquement un JSON avec les champs trouvés

        Format JSON attendu:
        {{
            "type_compte": "COURANT|EPARGNE|AUTRE",
            "usage_compte": "PERSONNEL|PROFESSIONNEL|MIXTE",
            "modalite_detention": "TITULAIRE|PROCURATION",
            "date_ouverture": "JJ/MM/AAAA",
            "lieu_signature": "ville"
        }}
        """

        try:
            response = await llm.ainvoke(prompt)
            # Parser la réponse JSON et merger avec les données
            import json
            extracted_context = json.loads(response.content)

            # Merger seulement les champs non vides
            for key, value in extracted_context.items():
                if value and key not in consolidated:
                    consolidated[key] = value
                    print(f"    • Extrait du contexte: {key} = {value}")
        except Exception as e:
            print(f"  ⚠ Erreur analyse contexte: {e}")

    # Appliquer les valeurs par défaut pour les champs non critiques
    for key, default_value in DEFAULT_VALUES.items():
        if key not in consolidated:
            consolidated[key] = default_value
            print(f"  > Valeur par défaut: {key} = {default_value}")

    return {"consolidated_data": consolidated}

def human_validation_node(state: Form3916StateModern) -> dict:
    """
    Nœud de validation humaine pour le mode conversationnel.
    Simule une demande d'aide à l'utilisateur si certains documents manquent.
    """
    print("\n🤖 === VALIDATION HUMAINE ===")

    # Analyser les documents disponibles
    documents = state.get("documents", [])
    print(f"  Documents fournis: {len(documents)}")

    # Simuler la vérification de documents manquants
    # Dans un cas réel, on analyserait le contenu des documents
    required_docs = ["RIB", "CNI", "relevé bancaire"]
    found_docs = []

    # Simulation basique - dans la réalité on analyserait le contenu
    if len(documents) >= 1:
        found_docs.append("RIB")
    if len(documents) >= 2:
        found_docs.append("CNI")
    if len(documents) >= 3:
        found_docs.append("relevé bancaire")

    missing_docs = [doc for doc in required_docs if doc not in found_docs]

    if missing_docs and len(documents) < 2:
        # Déclencher une demande d'interaction humaine
        print(f"  Documents manquants détectés: {', '.join(missing_docs)}")

        # Préparer la demande d'input utilisateur
        human_input_request = {
            "question": f"J'ai analysé vos documents et j'ai trouvé un {found_docs[0] if found_docs else 'document'}. "
                       f"Pour compléter le formulaire 3916, il me manque encore: {', '.join(missing_docs)}. "
                       f"Pouvez-vous fournir ces documents ?",
            "input_type": "file",
            "context": "Documents requis pour le formulaire 3916: RIB du compte étranger, pièce d'identité, relevés bancaires"
        }

        # Simuler la mise en pause pour attendre l'input utilisateur
        # Dans un vrai système, ceci déclencherait une mise en pause de LangGraph
        return {
            "needs_human_input": True,
            "human_input_request": human_input_request,
            "status": "waiting_for_human_input"
        }

    print("  ✅ Documents suffisants pour continuer")
    return {
        "needs_human_input": False,
        "validation_complete": True
    }

def check_completeness_adaptive(state: Form3916StateModern) -> dict:
    """Vérification adaptative de la complétude."""
    print("--- NŒUD: VÉRIFICATION COMPLÉTUDE ADAPTATIVE ---")

    # Protection contre la récursion infinie
    iteration_count = state.get("iteration_count", 0) + 1
    print(f"  > Itération #{iteration_count}")

    # Si trop d'itérations, forcer la génération du PDF
    if iteration_count > 3:
        print("  ! Limite d'itérations atteinte - génération forcée du PDF")
        return {
            "missing_critical": [],
            "missing_optional": [],
            "iteration_count": iteration_count,
            "_force_pdf": True
        }

    data = state.get("consolidated_data", {})

    # Si on a déjà essayé de collecter et échoué, ne pas réessayer
    if state.get("_needs_user_input"):
        print("  > Collecte déjà tentée, passage au PDF avec données disponibles")
        return {
            "missing_critical": [],
            "missing_optional": [],
            "_needs_user_input": False,
            "iteration_count": iteration_count
        }

    # Séparer les champs manquants en critiques et optionnels
    missing_critical = [f for f in CRITICAL_FIELDS if not data.get(f)]
    missing_optional = [f for f in OPTIONAL_FIELDS if not data.get(f)]

    # Si l'utilisateur a choisi de skip les optionnels, les ignorer
    if state.get("skip_optional", False):
        missing_optional = []

    print(f"  > Champs critiques manquants: {missing_critical}")
    print(f"  > Champs optionnels manquants: {missing_optional}")

    return {
        "missing_critical": missing_critical,
        "missing_optional": missing_optional,
        "iteration_count": iteration_count
    }

def collect_critical_data(state: Form3916StateModern) -> dict:
    """Collecte des données critiques - termine le graphe pour human-in-the-loop."""
    print("--- NŒUD: COLLECTE DONNÉES CRITIQUES ---")

    critical = state.get("missing_critical", [])

    if not critical:
        return {}

    print(f"  > Champs critiques manquants: {critical}")
    print(f"  > Terminaison du graphe pour human-in-the-loop")

    # Créer un message clair pour l'utilisateur
    field_labels = {
        "nom": "Nom",
        "prenom": "Prénom",
        "date_naissance": "Date de naissance (JJ.MM.AAAA)",
        "lieu_naissance": "Lieu de naissance",
        "adresse_complete": "Adresse complète",
        "numero_compte": "Numéro de compte",
        "designation_etablissement": "Nom de l'établissement bancaire"
    }

    message = "Pour compléter le formulaire 3916, j'ai besoin des informations suivantes :\n\n"
    for field in critical:
        label = field_labels.get(field, field)
        message += f"• {label}\n"

    # Retourner l'état avec les champs manquants - le graphe se termine ici
    return {
        "missing_critical": critical,
        "_needs_user_input": True,
        "_input_type": "critical",
        "_message": message
    }

def collect_optional_data(state: Form3916StateModern) -> dict:
    """Collecte des données optionnelles avec possibilité de skip."""
    print("--- NŒUD: COLLECTE DONNÉES OPTIONNELLES ---")

    optional = state.get("missing_optional", [])

    if not optional:
        return {}

    print(f"  > Champs optionnels manquants: {optional}")

    # Si on a déjà décidé de skip (depuis une reprise manuelle)
    if state.get("skip_optional", False):
        print("  > SKIP activé - génération du PDF sans les champs optionnels")
        return {"missing_optional": [], "skip_optional": True}

    # Essayer interrupt() si checkpointer disponible
    try:
        response = interrupt({
            "type": "optional",
            "fields": optional,
            "message": f"Informations complémentaires (optionnelles):\n"
                      f"{', '.join(optional)}\n"
                      f"Vous pouvez:\n"
                      f"1. Fournir ces informations sous forme de JSON\n"
                      f"2. Répondre 'SKIP' pour générer le PDF sans ces informations",
            "example": {field: f"valeur_{field}" for field in optional}
        })

        # Gestion de la réponse
        if response == "SKIP" or response == {"skip": True}:
            print("  > Utilisateur a choisi SKIP")
            return {"skip_optional": True, "missing_optional": []}

        # Mise à jour des données si fournies
        consolidated = state.get("consolidated_data", {})

        if isinstance(response, dict) and response != {"skip": True}:
            consolidated.update(response)
            print(f"  > Données optionnelles reçues: {list(response.keys())}")

        return {"consolidated_data": consolidated, "missing_optional": []}

    except Exception as e:
        # Si interrupt() échoue, on génère le PDF avec ce qu'on a
        print(f"  ⚠ Interruption non disponible (pas de checkpointer)")
        print(f"    Génération du PDF sans les champs optionnels: {optional}")

        # Marquer qu'on skip les optionnels pour éviter la boucle
        return {
            "missing_optional": [],
            "skip_optional": True,
            "_needs_user_input": True,
            "_input_type": "optional",
            "_message": f"Les champs optionnels suivants restent vides: {optional}"
        }

def generate_pdf_flexible(state: Form3916StateModern) -> dict:
    """Génération du PDF même avec des champs manquants."""
    print("--- NŒUD: GÉNÉRATION PDF FLEXIBLE ---")

    consolidated_data = state["consolidated_data"]
    missing_optional = state.get("missing_optional", [])

    # Ajouter des métadonnées sur les champs incomplets
    if missing_optional:
        print(f"  ⚠ PDF généré avec champs manquants: {missing_optional}")
        # On pourrait ajouter une note sur le PDF
        consolidated_data["_incomplete_fields"] = missing_optional

    # Type de compte (toujours bancaire pour ce sprint)
    nature_compte = consolidated_data.get("nature_compte", "COMPTE_BANCAIRE")
    print(f"  > Type de compte: {nature_compte}")

    # Préparation des données multi-pages
    data_by_page = prepare_data_for_multipage_generation(consolidated_data)
    total_fields = sum(len(page_data) for page_data in data_by_page.values())
    print(f"  > {total_fields} champs préparés sur {len(data_by_page)} pages")

    # Récupération des coordonnées
    coordinates_by_page = get_coordinates_for_type(nature_compte)

    # Génération de l'overlay
    overlay_packet = pdf_generator.generate_multipage_pdf_overlay(
        data_by_page,
        coordinates_by_page
    )

    # Superposition sur le template
    template_path = Path(__file__).parent / "3916_4725.pdf"
    pdf_bytes = pdf_generator.superimpose_multipage_pdf(template_path, overlay_packet)
    print(f"  > PDF généré ({len(pdf_bytes):,} octets)")

    # Sauvegarde locale
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent / "pdf_filled"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / f"form_3916_{timestamp}.pdf"
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)
    print(f"  > PDF sauvegardé: {output_path}")

    return {"generated_pdf": pdf_bytes}

# ==================== ROUTAGE CONDITIONNEL ====================

def routing_decision(state: Form3916StateModern) -> str:
    """Décide de la prochaine étape selon l'état."""

    # Si on a besoin d'input utilisateur et pas de checkpointer, aller directement au PDF
    if state.get("_needs_user_input"):
        # Si c'est critique, on ne peut pas continuer
        if state.get("_input_type") == "critical":
            print("  ! Arrêt: champs critiques requis")
            return END  # Terminer le workflow, l'utilisateur doit reprendre manuellement
        # Si c'est optionnel, on peut générer le PDF quand même
        else:
            print("  > Génération du PDF sans les champs optionnels")
            return "generate_pdf"

    if state.get("missing_critical"):
        return "collect_critical"
    elif state.get("missing_optional") and not state.get("skip_optional", False):
        return "collect_optional"
    else:
        return "generate_pdf"

# ==================== CONSTRUCTION DU GRAPHE ====================

def create_modern_form3916_graph(use_checkpointer: bool = False):
    """
    Crée le graphe modernisé avec les fonctionnalités LangGraph 2025.

    Args:
        use_checkpointer: Active la persistance avec SQLite (dev) ou PostgreSQL (prod)
    """

    # Checkpointer avec MemorySaver pour simplicité et fiabilité
    checkpointer = None
    if use_checkpointer:
        print("Configuration du checkpointer MemorySaver...")
        try:
            from langgraph.checkpoint.memory import MemorySaver
            checkpointer = MemorySaver()
            print("✓ Checkpointer MemorySaver activé - human-in-the-loop disponible")
        except Exception as e:
            print(f"❌ Impossible d'activer MemorySaver: {e}")
            print("  Le human-in-the-loop ne sera pas disponible")

    # Création du graphe d'état
    workflow = StateGraph(Form3916StateModern)

    # Ajout des nœuds
    workflow.add_node("extract_direct", extract_from_all_documents_direct)
    workflow.add_node("consolidate", consolidate_data)
    workflow.add_node("analyze_context", analyze_user_context)
    workflow.add_node("human_validation", human_validation_node)  # Nouveau nœud pour validation humaine
    workflow.add_node("check_completeness", check_completeness_adaptive)
    workflow.add_node("collect_critical", collect_critical_data)
    workflow.add_node("collect_optional", collect_optional_data)
    workflow.add_node("generate_pdf", generate_pdf_flexible)

    # Flux principal séquentiel - extraction directe sans classification
    workflow.set_entry_point("extract_direct")
    workflow.add_edge("extract_direct", "consolidate")
    workflow.add_edge("consolidate", "analyze_context")
    workflow.add_edge("analyze_context", "human_validation")
    workflow.add_edge("human_validation", "check_completeness")

    # Routage conditionnel après vérification
    workflow.add_conditional_edges(
        "check_completeness",
        routing_decision,
        {
            "collect_critical": "collect_critical",
            "collect_optional": "collect_optional",
            "generate_pdf": "generate_pdf",
            END: END  # Ajout de la possibilité de terminer
        }
    )

    # Retour après collecte de données
    # collect_critical termine le graphe directement (interrupt)
    workflow.add_edge("collect_critical", END)
    workflow.add_edge("collect_optional", "check_completeness")

    # Fin du workflow
    workflow.add_edge("generate_pdf", END)

    # Compilation avec ou sans checkpointer
    if checkpointer:
        return workflow.compile(checkpointer=checkpointer)
    else:
        return workflow.compile()

# ==================== API D'EXÉCUTION ====================

async def execute_with_context(files: List[Dict[str, bytes]], context: str = None):
    """
    Exécute le workflow avec contexte utilisateur.

    Args:
        files: Liste des fichiers uploadés
        context: Contexte optionnel fourni par l'utilisateur

    Returns:
        État final avec PDF généré
    """

    # Créer le graphe
    graph = create_modern_form3916_graph(use_checkpointer=True)

    # État initial
    initial_state = {
        "input_files": files,
        "user_context": context,
        "classified_docs": [],
        "extracted_data_list": [],
        "consolidated_data": {},
        "missing_critical": [],
        "missing_optional": [],
        "skip_optional": False,
        "pdf_data": None,
        "generated_pdf": None,
        "iteration_count": 0
    }

    # Configuration du thread pour la persistance
    thread_config = {"configurable": {"thread_id": "form3916_session"}}

    # Exécution
    result = await graph.ainvoke(initial_state, config=thread_config)

    return result

async def resume_with_response(thread_id: str, user_response: Any):
    """
    Reprend l'exécution après une interruption.

    Args:
        thread_id: Identifiant du thread
        user_response: Réponse de l'utilisateur (dict ou "SKIP")

    Returns:
        État mis à jour
    """

    # Recréer le graphe avec le même checkpointer
    graph = create_modern_form3916_graph(use_checkpointer=True)

    # Configuration du thread
    thread_config = {"configurable": {"thread_id": thread_id}}

    # Utilisation de Command pour reprendre
    result = await graph.ainvoke(
        Command(resume=user_response),
        config=thread_config
    )

    return result

# ==================== HELPER POUR REPRISE MANUELLE ====================

async def resume_workflow_with_data(
    graph,
    previous_state: Dict[str, Any],
    user_data: Dict[str, Any] = None,
    skip_optional: bool = False
) -> Dict[str, Any]:
    """
    Reprend le workflow après une interruption manuelle.

    Args:
        graph: Le graphe compilé
        previous_state: L'état retourné par l'exécution précédente
        user_data: Données fournies par l'utilisateur (dict)
        skip_optional: Si True, ignore les champs optionnels

    Returns:
        L'état final avec le PDF généré
    """
    # Copier l'état précédent
    resumed_state = previous_state.copy()

    # Merger les données utilisateur
    if user_data:
        consolidated = resumed_state.get("consolidated_data", {})
        consolidated.update(user_data)
        resumed_state["consolidated_data"] = consolidated
        resumed_state["_manual_data"] = user_data

        # Retirer des champs manquants ceux qui ont été fournis
        for field_type in ["missing_critical", "missing_optional"]:
            if field_type in resumed_state:
                resumed_state[field_type] = [
                    f for f in resumed_state[field_type]
                    if f not in user_data
                ]

    # Gérer le skip des optionnels
    if skip_optional:
        resumed_state["skip_optional"] = True
        resumed_state["missing_optional"] = []

    # Relancer le workflow
    result = await graph.ainvoke(resumed_state)

    return result

# Export pour utilisation - réactivation du checkpointer
form_3916_graph_modern = create_modern_form3916_graph(use_checkpointer=True)

# ==================== FONCTION STANDARDISÉE POUR L'ORCHESTRATEUR ====================

async def execute(inputs: dict) -> dict:
    """
    Point d'entrée standardisé pour l'orchestrateur de recettes.

    Cette fonction respecte le contrat strict défini par l'architecture modulaire :
    - En entrée : dictionnaire avec clés correspondant au manifest.json
    - En sortie : dictionnaire avec clés correspondant aux outputs du manifest

    Args:
        inputs: Dict avec les clés définies dans manifest.json :
            - "documents": List[bytes] - Contenu des fichiers uploadés
            - "context": str (optionnel) - Contexte additionnel

    Returns:
        Dict avec les clés définies dans les outputs du manifest :
            - "pdf_form": str - Chemin absolu vers le PDF généré
            - "extracted_data": dict - Données extraites et consolidées

    Raises:
        ValueError: Si les inputs ne respectent pas le contrat
        Exception: En cas d'erreur lors de l'exécution
    """
    import uuid
    import os
    from pathlib import Path

    print("=== DÉBUT EXÉCUTION RECETTE FORM_3916 ===")
    print(f"Inputs reçus: {list(inputs.keys())}")
    print(f"GRAPH DEBUG: execute() appelée avec inputs: {inputs}")

    # Détecter si c'est une reprise
    is_resume = inputs.get("is_resume", False)

    if is_resume:
        print("=== MODE REPRISE DÉTECTÉ ===")
        # En mode reprise, pas besoin de documents car l'extraction a déjà été faite
        documents = []  # Vide car pas nécessaire
        context = inputs.get("context", "")
    else:
        # Validation normale des inputs pour un démarrage initial
        if "documents" not in inputs:
            raise ValueError("Input 'documents' requis manquant")

        documents = inputs["documents"]
        context = inputs.get("context", "")

    if not isinstance(documents, list):
        raise ValueError("Input 'documents' doit être une liste")

    print(f"Nombre de documents: {len(documents)}")
    print(f"Contexte fourni: {'Oui' if context else 'Non'}")

    try:
        # En mode reprise, on skip la conversion des documents car pas nécessaire
        if is_resume:
            input_files = []  # Vide car nous utiliserons les données consolidées
        else:
            # Conversion des inputs au format attendu par le graphe existant
            input_files = []
            for i, content in enumerate(documents):
                # Chaque document est encapsulé dans un dict avec un nom générique
                document_name = f"document_{i+1}"
                input_files.append({document_name: content})

        print(f"Fichiers d'entrée préparés: {len(input_files)}")

        # Préparation de l'état initial pour le graphe
        initial_state = {
            "input_files": input_files,
            "user_context": context,
            "classified_docs": [],
            "extracted_data_list": [],
            "consolidated_data": {},
            "missing_critical": [],
            "missing_optional": [],
            "skip_optional": False,
            "pdf_data": None,
            "generated_pdf": None,
            "iteration_count": 0
        }

        # Vérifier s'il s'agit d'une reprise avec des données utilisateur
        if inputs.get("is_resume") and inputs.get("human_input_response"):
            print("=== REPRISE DÉTECTÉE ===")
            human_response = inputs.get("human_input_response", {})
            saved_state = inputs.get("saved_state", {})

            # Récupérer l'état sauvegardé pour reprendre où on s'était arrêté
            if saved_state:
                print("=== RESTAURATION DE L'ÉTAT SAUVEGARDÉ ===")
                print(f"Clés disponibles dans saved_state: {list(saved_state.keys())}")

                # Récupérer les données de l'état précédent
                if "graph_state" in saved_state:
                    graph_state = saved_state["graph_state"]
                    print(f"Clés dans graph_state: {list(graph_state.keys())}")

                    for key, value in graph_state.items():
                        if key in initial_state:
                            initial_state[key] = value
                            if key == "consolidated_data" and isinstance(value, dict):
                                print(f"Restauré consolidated_data: {len(value)} champs - {list(value.keys())}")
                            else:
                                print(f"Restauré: {key}")

                # Vérification de la consolidation des données après restauration
                restored_data = initial_state.get("consolidated_data", {})
                print(f"  > Données consolidées restaurées: {len(restored_data)} champs")
                if restored_data:
                    print(f"  > Champs disponibles: {list(restored_data.keys())}")
            else:
                print("=== AUCUN ÉTAT SAUVEGARDÉ TROUVÉ ===")
                print("Ceci peut indiquer un problème de sauvegarde lors du human-in-the-loop")

            # Traiter la réponse utilisateur (JSON string contenant les champs)
            user_response_str = human_response.get("response", "{}")
            try:
                import json
                user_data = json.loads(user_response_str)
                print(f"Données utilisateur reçues: {list(user_data.keys())}")

                # Ajouter les données utilisateur aux données consolidées
                if not initial_state.get("consolidated_data"):
                    initial_state["consolidated_data"] = {}

                print(f"  > Avant fusion - données consolidées: {len(initial_state['consolidated_data'])} champs")
                print(f"  > Données utilisateur à fusionner: {len(user_data)} champs - {list(user_data.keys())}")

                # Fusionner les données utilisateur avec les données existantes
                initial_state["consolidated_data"].update(user_data)

                # Marquer les champs comme complétés
                initial_state["missing_critical"] = []
                initial_state["iteration_count"] = initial_state.get("iteration_count", 0) + 1

                print(f"  > Après fusion - données consolidées: {len(initial_state['consolidated_data'])} champs")
                print(f"  > Tous champs disponibles: {list(initial_state['consolidated_data'].keys())}")

            except json.JSONDecodeError as e:
                print(f"Erreur lors du parsing des données utilisateur: {e}")

        print("État initial préparé, lancement du graphe...")

        # Configuration pour le checkpointer
        thread_config = {"configurable": {"thread_id": f"recipe_execution_{uuid.uuid4()}"}}

        # Exécution du graphe existant avec configuration
        final_state = await form_3916_graph_modern.ainvoke(initial_state, config=thread_config)

        print("Exécution du graphe terminée")
        print(f"État final: {list(final_state.keys())}")

        # Vérification que le PDF a été généré ou si on a besoin d'input utilisateur
        if not final_state.get("generated_pdf"):
            # Si des champs critiques manquent, toujours retourner l'état human-in-the-loop
            missing_critical = final_state.get("missing_critical", [])
            input_message = final_state.get("_message", "")

            if missing_critical:
                print(f"INTERRUPTION: Human-in-the-loop requis pour: {missing_critical}")

                # Créer un message par défaut si nécessaire
                if not input_message:
                    field_labels = {
                        "nom": "Nom", "prenom": "Prénom",
                        "date_naissance": "Date de naissance (JJ.MM.AAAA)",
                        "lieu_naissance": "Lieu de naissance",
                        "adresse_complete": "Adresse complète",
                        "numero_compte": "Numéro de compte",
                        "designation_etablissement": "Nom de l'établissement bancaire"
                    }
                    input_message = "Pour compléter le formulaire 3916, j'ai besoin des informations suivantes :\n\n"
                    for field in missing_critical:
                        label = field_labels.get(field, field)
                        input_message += f"• {label}\n"

                # Retourner un état spécial pour le human-in-the-loop
                print(f"GRAPH DEBUG: Retour human-in-the-loop avec {len(final_state.get('consolidated_data', {}))} champs consolidés")
                result = {
                    "needs_human_input": True,
                    "missing_fields": missing_critical,
                    "current_question": input_message,
                    "consolidated_data": final_state.get("consolidated_data", {}),
                    "checkpoint_id": f"recipe_execution_{uuid.uuid4()}",  # ID unique pour reprise
                    "status": "waiting_for_human_input",
                    "graph_state": final_state  # Sauvegarder l'état complet du graphe pour reprise
                }
                print(f"GRAPH DEBUG: result keys = {list(result.keys())}")
                return result
            else:
                raise Exception("Échec de la génération du PDF pour une raison inconnue")

        # Sauvegarde du PDF généré
        pdf_bytes = final_state["generated_pdf"]

        # Créer un répertoire temporaire pour les outputs si nécessaire
        output_dir = Path("/tmp/recipe_outputs")
        output_dir.mkdir(exist_ok=True)

        # Générer un nom de fichier unique
        pdf_filename = f"form_3916_{uuid.uuid4()}.pdf"
        pdf_path = output_dir / pdf_filename

        # Écrire le PDF sur le disque
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)

        print(f"PDF sauvegardé: {pdf_path}")
        print(f"Taille du PDF: {len(pdf_bytes):,} octets")

        # Préparer les données extraites pour la sortie
        extracted_data = final_state.get("consolidated_data", {})

        # Ajouter des métadonnées sur le traitement
        from datetime import datetime
        extracted_data["_metadata"] = {
            "processing_date": datetime.now().isoformat(),
            "document_count": len(documents),
            "context_provided": bool(context),
            "missing_optional": final_state.get("missing_optional", []),
            "pdf_size_bytes": len(pdf_bytes)
        }

        print(f"Données extraites: {len(extracted_data)} champs")

        # Construction de la réponse selon le contrat de sortie
        result = {
            "pdf_form": str(pdf_path.absolute()),  # Chemin absolu requis
            "extracted_data": extracted_data
        }

        print("=== EXÉCUTION TERMINÉE AVEC SUCCÈS ===")
        print(f"Outputs générés: {list(result.keys())}")

        return result

    except Exception as e:
        print(f"=== ERREUR LORS DE L'EXÉCUTION ===")
        print(f"Type d'erreur: {type(e).__name__}")
        print(f"Message: {str(e)}")
        raise