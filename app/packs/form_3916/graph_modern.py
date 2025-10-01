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

async def extract_from_all_documents(state: Form3916StateModern) -> dict:
    """Extraction parallèle depuis tous les documents."""
    print("--- NŒUD: EXTRACTION MULTI-DOCUMENTS ---")

    extraction_tasks = []
    for doc in state["classified_docs"]:
        # Extraire de TOUS les documents, même INCONNU
        task = data_extractor.extract_data_from_document(
            doc["text"], doc["doc_type"]
        )
        extraction_tasks.append(task)
        print(f"  > Extraction: '{doc['filename']}' ({doc['doc_type'].name})")

    extracted_results = await asyncio.gather(*extraction_tasks)
    return {"extracted_data_list": extracted_results}

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

def check_completeness_adaptive(state: Form3916StateModern) -> dict:
    """Vérification adaptative de la complétude."""
    print("--- NŒUD: VÉRIFICATION COMPLÉTUDE ADAPTATIVE ---")

    data = state.get("consolidated_data", {})

    # Si on a déjà essayé de collecter et échoué, ne pas réessayer
    if state.get("_needs_user_input"):
        print("  > Collecte déjà tentée, passage au PDF avec données disponibles")
        return {
            "missing_critical": [],
            "missing_optional": [],
            "_needs_user_input": False
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
        "missing_optional": missing_optional
    }

def collect_critical_data(state: Form3916StateModern) -> dict:
    """Collecte des données critiques avec interruption."""
    print("--- NŒUD: COLLECTE DONNÉES CRITIQUES ---")

    critical = state.get("missing_critical", [])

    if not critical:
        return {}

    print(f"  > Champs critiques manquants: {critical}")

    # Si on a un checkpointer, utiliser interrupt()
    # Sinon, juste retourner l'état pour que l'utilisateur puisse le reprendre
    try:
        response = interrupt({
            "type": "critical",
            "fields": critical,
            "message": f"Ces informations sont obligatoires pour générer le formulaire:\n"
                      f"{', '.join(critical)}\n"
                      f"Veuillez fournir ces informations sous forme de dictionnaire JSON.",
            "example": {field: f"valeur_{field}" for field in critical}
        })

        # Mise à jour des données consolidées
        consolidated = state.get("consolidated_data", {})

        if isinstance(response, dict):
            consolidated.update(response)
            print(f"  > Données reçues: {list(response.keys())}")

        return {"consolidated_data": consolidated}

    except Exception as e:
        # Si interrupt() échoue (pas de checkpointer), retourner l'état tel quel
        print(f"  ⚠ Interruption non disponible (pas de checkpointer)")
        print(f"    Les champs suivants sont requis: {critical}")

        # Créer un message clair pour l'utilisateur
        field_labels = {
            "nom": "Nom",
            "prenom": "Prénom",
            "date_naissance": "Date de naissance (JJ/MM/AAAA)",
            "lieu_naissance": "Lieu de naissance",
            "adresse_complete": "Adresse complète"
        }

        message = "Pour compléter le formulaire 3916, j'ai besoin des informations suivantes :\n\n"
        for field in critical:
            label = field_labels.get(field, field)
            message += f"• {label}\n"

        # Marquer qu'on a besoin d'intervention
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

    # Checkpointer optionnel pour la persistance
    checkpointer = None
    if use_checkpointer:
        # Détection automatique selon l'environnement
        database_url = os.getenv("DATABASE_URL", "")

        if "postgresql" in database_url:
            # Production: PostgreSQL
            try:
                from langgraph.checkpoint.postgres import PostgresSaver
                # Extract connection params from DATABASE_URL
                # Format: postgresql+asyncpg://user:pass@host:port/db
                import re
                match = re.match(r'postgresql\+asyncpg://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
                if match:
                    user, password, host, port, dbname = match.groups()
                    checkpointer = PostgresSaver.from_conn_string(
                        f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
                    )
                    print("✓ Checkpointer PostgreSQL activé")
            except ImportError:
                print("⚠ PostgreSQL checkpointer non disponible, désactivé")
        else:
            # Développement: SQLite
            try:
                from langgraph.checkpoint.sqlite import SqliteSaver
                checkpointer = SqliteSaver.from_conn_string("sqlite:///form3916_states.db")
                print("✓ Checkpointer SQLite activé")
            except ImportError:
                print("⚠ SQLite checkpointer non disponible, désactivé")

    # Création du graphe d'état
    workflow = StateGraph(Form3916StateModern)

    # Ajout des nœuds
    workflow.add_node("classify", classify_documents)
    workflow.add_node("extract", extract_from_all_documents)
    workflow.add_node("consolidate", consolidate_data)
    workflow.add_node("analyze_context", analyze_user_context)
    workflow.add_node("check_completeness", check_completeness_adaptive)
    workflow.add_node("collect_critical", collect_critical_data)
    workflow.add_node("collect_optional", collect_optional_data)
    workflow.add_node("generate_pdf", generate_pdf_flexible)

    # Flux principal séquentiel
    workflow.set_entry_point("classify")
    workflow.add_edge("classify", "extract")
    workflow.add_edge("extract", "consolidate")
    workflow.add_edge("consolidate", "analyze_context")
    workflow.add_edge("analyze_context", "check_completeness")

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

    # Retour après collecte de données - Seulement si interrupt a fonctionné
    # Si pas de checkpointer, collect_critical et collect_optional terminent directement
    # pour éviter la boucle infinie
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
        "generated_pdf": None
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

# Export pour utilisation
form_3916_graph_modern = create_modern_form3916_graph(use_checkpointer=False)