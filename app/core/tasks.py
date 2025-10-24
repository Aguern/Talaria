# Fichier: app/core/tasks.py

import httpx
import tarfile
import io
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime
from langchain_text_splitters import RecursiveCharacterTextSplitter
import asyncio
import json
import importlib
import os
from typing import Dict
from sqlalchemy import text, func

from core.database import SessionLocal
from core import crud
from core.engine import get_embed_client
import structlog

log = structlog.get_logger()

BOFIP_INDEX_URL = "https://www.data.gouv.fr/api/1/datasets/r/93c981ed-a818-4e89-bb19-49756591bc2d"

# Conditional imports for Celery mode only
CELERY_MODE = os.getenv("CELERY_BROKER_URL") is not None

if CELERY_MODE:
    from redis import Redis
    from worker import celery_app

    # Connexion Redis pour les tâches (uniquement en mode Celery)
    redis_client = Redis.from_url(os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"), decode_responses=True)
    log.info("Celery mode enabled in tasks.py")
else:
    log.info("Direct mode - Celery imports skipped in tasks.py")

    # Mock celery_app for Direct mode (tasks won't be called but need to be defined)
    class MockCeleryApp:
        def task(self, *args, **kwargs):
            """Dummy decorator that does nothing in Direct mode"""
            def decorator(func):
                return func
            # Support both @celery_app.task and @celery_app.task(...)
            if args and callable(args[0]):
                return args[0]
            return decorator

    celery_app = MockCeleryApp()
    redis_client = None

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)

async def process_document_pair(tar: tarfile.TarFile, files: Dict, tenant_id: int):
    """Traite une paire de fichiers XML/HTML pour un document BOFIP"""
    # Chaque tâche crée sa propre session
    async with SessionLocal() as db_session:
        # Always require XML file
        if 'xml' not in files:
            log.warning("Pas de fichier XML", files_available=list(files.keys()))
            return

        xml_file = tar.extractfile(files['xml'])
        if not xml_file:
            log.warning("Impossible d'extraire le fichier XML")
            return

        try:
            # --- PARSING XML CORRIGÉ ---
            tree = ET.parse(xml_file)
            root = tree.getroot()
            ns = {'dc': 'http://purl.org/dc/elements/1.1'}
            
            # On récupère tous les identifiants et on cherche l'URL en Python
            all_identifiers = [elem.text for elem in root.findall('.//dc:identifier', namespaces=ns) if elem.text]
            bofip_id = all_identifiers[0] if all_identifiers else None  # Le premier est souvent l'ID court
            url = next((id for id in all_identifiers if "bofip.impots.gouv.fr" in id), None)

            title = root.findtext('.//dc:title', namespaces=ns)
            date_str = root.findtext('.//dc:date', namespaces=ns)
            
            publication_date = None
            if date_str:
                try:
                    publication_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except ValueError:
                    publication_date = datetime.now()
            else:
                publication_date = datetime.now()
            # --- FIN DU PARSING XML CORRIGÉ ---

            if not bofip_id or not title: 
                log.warning("ID ou titre manquant", xml_path=files['xml'].name, bofip_id=bofip_id, title=title)
                return

            # Créer le document dans la BDD
            db_doc, should_index = await crud.create_document(
                db_session, 
                tenant_id=tenant_id, 
                bofip_id=bofip_id, 
                title=title, 
                url=url, 
                publication_date=publication_date
            )

            if not should_index:
                log.info("Document déjà à jour, on passe.", bofip_id=bofip_id)
                return

            # Check if we have HTML file
            if 'html' not in files:
                log.info("Document sans HTML, création sans chunks", bofip_id=bofip_id)
                return

            html_file = tar.extractfile(files['html'])
            if not html_file:
                log.warning("Impossible d'extraire le fichier HTML", bofip_id=bofip_id)
                return

            # Parser HTML pour le contenu
            html_content = html_file.read()
            soup = BeautifulSoup(html_content, 'lxml')
            text_content = soup.get_text(separator=' ', strip=True)
            
            if not text_content:
                log.warning("Contenu HTML vide", html_path=files['html'].name, bofip_id=bofip_id)
                return

            log.info("Contenu HTML extrait", bofip_id=bofip_id, content_length=len(text_content))

            # Découper le texte
            chunks = text_splitter.split_text(text_content)
            if not chunks:
                log.warning("Aucun chunk généré", bofip_id=bofip_id, content_length=len(text_content))
                return
            
            log.info("Chunks générés", bofip_id=bofip_id, chunk_count=len(chunks))

            # Générer les embeddings avec le client d'embedding
            embed_client = get_embed_client()
            log.info(f"Génération de {len(chunks)} embeddings pour {bofip_id}...")
            try:
                embeddings = await embed_client.embed_documents(chunks)
                log.info("Embeddings générés avec succès", bofip_id=bofip_id, embedding_count=len(embeddings))
            except Exception as embed_error:
                log.error("Erreur lors de la génération des embeddings", bofip_id=bofip_id, error=str(embed_error))
                return
            finally:
                # Fermer le client pour éviter les fuites de ressources
                try:
                    await embed_client.close()
                except:
                    pass

            # Préparer les données pour la BDD avec tsvector
            chunks_with_embeddings_and_tsv = [
                {
                    'text': chunk,
                    'embedding': emb,
                    'content_tsv': func.to_tsvector('french', chunk)
                }
                for chunk, emb in zip(chunks, embeddings)
            ]
            
            # Sauvegarder les chunks et embeddings
            try:
                chunk_count = await crud.create_chunks(db_session, db_doc, chunks_with_embeddings_and_tsv)
                log.info("Document traité et sauvegardé.", bofip_id=bofip_id, chunks_count=chunk_count)
            except Exception as db_error:
                log.error("Erreur lors de la sauvegarde des chunks", bofip_id=bofip_id, error=str(db_error))
                return

        except Exception as e:
            log.error("Erreur lors du traitement d'un document.", 
                     xml_path=files['xml'].name, error=str(e), error_type=type(e).__name__)

@celery_app.task
def ingest_bofip_task():
    """Tâche principale d'ingestion des documents BOFIP"""

    async def _run_ingestion():
        log.info("Démarrage de la tâche d'ingestion du BOFIP...")

        try:
            # ÉTAPE 1 : Trouver l'URL de l'archive "Stock"
            stock_archive_url = None
            with httpx.Client(follow_redirects=True) as client:
                response = client.get(BOFIP_INDEX_URL)
                response.raise_for_status()
                archives_index = response.json()
                
                # On cherche l'entrée la plus récente de type "stock"
                for archive_info in sorted(archives_index, key=lambda x: x.get('date_de_fin', ''), reverse=True):
                    if archive_info.get('type') == 'stock':
                        stock_archive_url = archive_info.get('telechargement')
                        log.info("URL de l'archive 'Stock' trouvée.", url=stock_archive_url)
                        break
            
            if not stock_archive_url:
                log.error("Aucune archive de type 'stock' n'a été trouvée dans l'index.")
                return "Échec : Impossible de trouver l'archive 'stock'."

            # ÉTAPE 2 : Télécharger et décompresser l'archive
            log.info("Téléchargement de l'archive 'Stock'...", url=stock_archive_url)
            with httpx.Client(follow_redirects=True, timeout=300) as client:
                response = client.get(stock_archive_url)
                response.raise_for_status()
                archive_buffer = io.BytesIO(response.content)
                
            log.info("Archive téléchargée. Décompression et organisation...")
            
            with tarfile.open(fileobj=archive_buffer, mode="r:gz") as tar:
                # ÉTAPE 3 : Organiser les fichiers par paires (xml, html)
                file_pairs = {}
                for member in tar.getmembers():
                    if member.isfile() and ('document.xml' in member.name or 'data.html' in member.name):
                        doc_path = "/".join(member.name.split('/')[:-1])
                        if doc_path not in file_pairs:
                            file_pairs[doc_path] = {}
                        if member.name.endswith('document.xml'):
                            file_pairs[doc_path]['xml'] = member
                        elif member.name.endswith('data.html'):
                            file_pairs[doc_path]['html'] = member
                
                log.info(f"{len(file_pairs)} documents uniques trouvés.")

                # ÉTAPE 4 : Traiter tous les documents
                # Process in smaller batches to avoid overwhelming the system
                BATCH_SIZE = 50  # Process 50 documents at a time

                all_files = list(file_pairs.items())
                total_count = len(all_files)
                processed_count = 0
                exceptions_count = 0

                log.info(f"Traitement de {total_count} documents en lots de {BATCH_SIZE}...")

                for i in range(0, total_count, BATCH_SIZE):
                    batch = all_files[i:i+BATCH_SIZE]
                    batch_tasks = [
                        process_document_pair(tar, files, tenant_id=1)
                        for path, files in batch
                    ]

                    # Process batch
                    batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

                    # Count exceptions in this batch
                    batch_exceptions = [r for r in batch_results if isinstance(r, Exception)]
                    exceptions_count += len(batch_exceptions)
                    processed_count += len(batch)

                    log.info(f"Lot traité: {processed_count}/{total_count} documents, {exceptions_count} erreurs jusqu'à présent")

                    # Small delay between batches to avoid overwhelming the system
                    await asyncio.sleep(0.5)

                # Final log
                log.info(f"Traitement terminé. {processed_count} documents traités, {exceptions_count} erreurs rencontrées.")
                    
        except Exception as e:
            log.error("Erreur dans le pipeline d'ingestion", error=str(e))
            raise

    try:
        asyncio.run(_run_ingestion())
        return f"Tâche terminée. Traitement des documents BOFIP effectué avec succès."
    except Exception as e:
        log.error("Erreur inattendue dans le runner asynchrone.", error=str(e))
        return "Échec de la tâche d'ingestion."

@celery_app.task
def diagnose_bofip_completeness():
    """Diagnostique l'état complet de l'ingestion BOFIP"""

    async def _run_diagnosis():
        log.info("Diagnostic de l'ingestion BOFIP...")

        async with SessionLocal() as db_session:
            # 1. Documents sans chunks
            query_no_chunks = text("""
                SELECT COUNT(*) as count
                FROM documents d
                LEFT JOIN chunks c ON d.id = c.document_id
                WHERE c.id IS NULL AND d.tenant_id = :tenant_id
            """)
            result = await db_session.execute(query_no_chunks, {"tenant_id": 1})
            docs_without_chunks = result.scalar()

            # 2. Total documents
            query_total = text("""
                SELECT COUNT(*) as total,
                       COUNT(DISTINCT CASE WHEN c.id IS NOT NULL THEN d.id END) as with_chunks
                FROM documents d
                LEFT JOIN chunks c ON d.id = c.document_id
                WHERE d.tenant_id = :tenant_id
            """)
            result = await db_session.execute(query_total, {"tenant_id": 1})
            stats = result.fetchone()

            # 3. Statistiques des chunks
            query_chunk_stats = text("""
                SELECT COUNT(*) as total_chunks,
                       MIN(chunk_count) as min_chunks,
                       MAX(chunk_count) as max_chunks,
                       ROUND(AVG(chunk_count)::numeric, 2) as avg_chunks
                FROM (
                    SELECT document_id, COUNT(*) as chunk_count
                    FROM chunks
                    GROUP BY document_id
                ) t
            """)
            result = await db_session.execute(query_chunk_stats)
            chunk_stats = result.fetchone()

            diagnosis = f"""
Diagnostic BOFIP:
- Documents attendus: 7407
- Documents en base: {stats.total}
- Documents manquants: {7407 - stats.total}
- Documents avec chunks: {stats.with_chunks}
- Documents SANS chunks: {docs_without_chunks}
- Total chunks: {chunk_stats.total_chunks if chunk_stats else 0}
- Moyenne chunks/document: {chunk_stats.avg_chunks if chunk_stats else 0}

Problèmes identifiés:
1. {7407 - stats.total} documents n'ont pas été créés (fichiers XML sans HTML)
2. {docs_without_chunks} documents existent mais n'ont pas de chunks
3. Taux de complétude: {round(stats.with_chunks / 7407 * 100, 2)}%
"""
            log.info(diagnosis)
            return diagnosis

    try:
        return asyncio.run(_run_diagnosis())
    except Exception as e:
        log.error("Erreur lors du diagnostic", error=str(e))
        return f"Erreur: {str(e)}"

@celery_app.task
def debug_task(x: int, y: int):
    """Tâche de débogage gardée pour les tests"""
    log.info("Tâche de débogage démarrée...", x=x, y=y)
    import time
    time.sleep(2)
    result = x + y
    log.info("Tâche de débogage terminée.", result=result)
    return result

# Importations pour l'exécution de recettes
import base64
import importlib
import sys
import os
sys.path.append('/app')
from packs.form_3916.graph_modern import form_3916_graph_modern

@celery_app.task(name="execute_recipe_task")
def execute_recipe_task(recipe_id: str, task_id: str, inputs: dict):
    """
    Tâche Celery générique pour l'exécution de recettes avec support conversationnel.

    Cette tâche :
    1. Importe dynamiquement le module de la recette
    2. Appelle la fonction execute() standardisée
    3. Gère les interruptions pour l'interaction humaine
    4. Sauvegarde le résultat dans Redis avec statuts enrichis

    Args:
        recipe_id: L'identifiant de la recette (ex: 'form_3916')
        task_id: L'identifiant unique de la tâche
        inputs: Les données d'entrée validées par l'orchestrateur
    """
    # Vérifier s'il s'agit d'une reprise
    is_resume = inputs.get("is_resume", False)
    human_input_response = inputs.get("human_input_response", None)

    if is_resume:
        log.info("Reprise de l'exécution de recette après input utilisateur",
                 recipe_id=recipe_id,
                 task_id=task_id,
                 input_keys=list(inputs.keys()))
    else:
        log.info("Démarrage de l'exécution de recette",
                 recipe_id=recipe_id,
                 task_id=task_id,
                 input_keys=list(inputs.keys()))

    def update_task_status(status: str, **kwargs):
        """Helper pour mettre à jour le statut dans Redis"""
        task_data = {
            "task_id": task_id,
            "recipe_id": recipe_id,
            "status": status,
            "updated_at": datetime.now().isoformat(),
            **kwargs
        }
        redis_client.set(f"task:{task_id}", json.dumps(task_data, default=str))
        log.info("Statut mis à jour", task_id=task_id, status=status)

    try:
        # Mettre à jour le statut à "running"
        update_task_status("running", current_step="Initialisation de la recette")

        # Import dynamique du module de la recette
        module_name = f'packs.{recipe_id}.graph_modern'
        module = importlib.import_module(module_name)

        if not hasattr(module, 'execute'):
            raise AttributeError(f"Le module {module_name} n'a pas de fonction 'execute'")

        log.info("Module importé avec succès", module_name=module_name)

        # Exécution de la recette avec gestion des interruptions
        update_task_status("running", current_step="Exécution de la recette")

        async def run_recipe():
            """Fonction async wrapper pour l'exécution"""
            try:
                # Si c'est une reprise, ajouter les données de reprise aux inputs
                if is_resume and human_input_response:
                    # Récupérer l'état sauvegardé depuis Redis
                    saved_task_data = redis_client.get(f"task:{task_id}")
                    if saved_task_data:
                        saved_data = json.loads(saved_task_data)
                        # Ajouter l'état sauvegardé et la réponse utilisateur aux inputs
                        inputs["saved_state"] = saved_data
                        inputs["human_input_response"] = human_input_response
                        log.info("État sauvegardé récupéré pour reprise", task_id=task_id)

                result = await module.execute(inputs)

                # Debug: Log du type et contenu du résultat pour diagnostic
                print(f"WORKER DEBUG: Type de résultat: {type(result)}")
                print(f"WORKER DEBUG: Contenu résultat (is dict): {isinstance(result, dict)}")
                if isinstance(result, dict):
                    print(f"WORKER DEBUG: Clés du résultat: {list(result.keys())}")
                    print(f"WORKER DEBUG: needs_human_input = {result.get('needs_human_input')}")

                # Vérifier si la recette a été interrompue pour interaction humaine
                if isinstance(result, dict) and result.get("needs_human_input"):
                    log.info("Interaction humaine requise", task_id=task_id)

                    # Créer correctement l'objet human_input_request
                    current_question = result.get("current_question", "Informations requises")
                    missing_fields = result.get("missing_fields", [])
                    conversation_history = result.get("conversation_history", [])

                    human_input_request = {
                        "question": current_question,
                        "input_type": "form",
                        "context": f"Champs manquants: {', '.join(missing_fields)}" if missing_fields else None
                    }

                    # Mettre le statut en attente d'input avec l'état complet du graphe
                    update_task_status(
                        "waiting_for_human_input",
                        current_step="Attente de la réponse utilisateur",
                        human_input_request=human_input_request,
                        conversation_history=conversation_history,
                        message="L'agent attend votre réponse pour continuer",
                        graph_state=result  # Sauvegarder l'état complet pour la reprise
                    )

                    # Log pour debug
                    print(f"WORKER: État sauvegardé pour human-in-the-loop - task {task_id}")
                    if result.get("consolidated_data"):
                        print(f"WORKER: Données consolidées sauvegardées: {len(result.get('consolidated_data', {}))} champs")

                    return None  # Signal que la tâche est en pause

                # Vérifier si le graphe LangGraph a été interrompu à l'état waiting_for_human_input
                elif hasattr(result, '__dict__') and hasattr(result, 'get'):
                    current_state = getattr(result, 'values', lambda: {})()
                    if current_state.get('_current_state') == 'waiting_for_human_input':
                        log.info("Graphe LangGraph interrompu pour interaction humaine", task_id=task_id)

                        # Extraire les informations du checkpoint
                        missing_critical = current_state.get('missing_critical', [])
                        current_question = current_state.get('current_question', '')

                        # Mettre à jour le statut pour le frontend
                        update_task_status(
                            "waiting_for_human_input",
                            current_step="Collecte d'informations manquantes",
                            missing_fields=missing_critical,
                            current_question=current_question,
                            message=current_question,
                            checkpoint_id=getattr(result, 'config', {}).get('configurable', {}).get('thread_id')
                        )

                        return None  # Signal que la tâche est en pause

                return result

            except Exception as e:
                # Vérifier si c'est une interruption LangGraph normale
                error_str = str(e)
                if "GraphInterrupt" in error_str or "waiting_for_human_input" in error_str:
                    log.info("Interruption LangGraph détectée pour interaction humaine", task_id=task_id, error=error_str)

                    # Extraire les informations d'erreur pour le human-in-the-loop
                    update_task_status(
                        "waiting_for_human_input",
                        current_step="Collecte d'informations manquantes",
                        message="L'agent a besoin d'informations supplémentaires pour continuer",
                        error_context=error_str
                    )

                    return None  # Signal que la tâche est en pause

                log.error("Erreur dans l'exécution async", error=str(e))
                raise

        # Exécuter la recette
        result = asyncio.run(run_recipe())

        # Si result est None, la tâche est en pause - ne rien faire de plus
        if result is None:
            log.info("Tâche en pause pour interaction utilisateur", task_id=task_id)
            return

        log.info("Exécution terminée avec succès",
                recipe_id=recipe_id,
                task_id=task_id,
                result_keys=list(result.keys()) if isinstance(result, dict) else "non-dict")

        # Sauvegarde du résultat final
        update_task_status(
            "completed",
            result=result,
            message="Recette exécutée avec succès",
            current_step="Terminé"
        )

    except ImportError as e:
        error_msg = f"Impossible d'importer le module de la recette '{recipe_id}': {str(e)}"
        log.error(error_msg, recipe_id=recipe_id, task_id=task_id)
        update_task_status("error", error=error_msg, error_type="import_error")

    except AttributeError as e:
        error_msg = f"Fonction 'execute' manquante dans la recette '{recipe_id}': {str(e)}"
        log.error(error_msg, recipe_id=recipe_id, task_id=task_id)
        update_task_status("error", error=error_msg, error_type="missing_function")

    except Exception as e:
        error_msg = f"Erreur lors de l'exécution de la recette '{recipe_id}': {str(e)}"
        log.error(error_msg, recipe_id=recipe_id, task_id=task_id, error=str(e))
        update_task_status("error", error=error_msg, error_type="execution_error")


@celery_app.task(name="execute_recipe_graph")
def execute_recipe_graph(task_id: str, state: dict):
    """
    Tâche Celery qui exécute ou continue un graphe de recette.

    DEPRECATED: Cette fonction sera remplacée par execute_recipe_task
    dans la nouvelle architecture. Conservée pour compatibilité temporaire.
    """
    print(f"WORKER: Exécution du graphe pour la tâche {task_id}")

    # LangGraph n'est pas nativement compatible avec l'async dans Celery,
    # nous utilisons donc asyncio.run pour exécuter la coroutine.
    import asyncio
    import os
    import importlib.util

    try:
        # CORRECTION: Utiliser la même logique que execute_recipe_task
        # pour supporter la reprise et les human_input_response

        # Récupérer les inputs originaux depuis Redis si possible
        task_data = redis_client.get(f"task:{task_id}")
        original_inputs = {}
        if task_data:
            saved_data = json.loads(task_data)
            original_inputs = saved_data.get("inputs", {})

        # Détecter si c'est une reprise avec human_input_response
        is_resume = state.get("is_resume", False) or "human_input_response" in state

        print(f"=== EXECUTE_RECIPE_GRAPH (LEGACY) ===")
        print(f"Task ID: {task_id}")
        print(f"Is resume: {is_resume}")
        print(f"State keys: {list(state.keys())}")

        if is_resume:
            print("LEGACY: Reprise détectée, utilisation du nouveau système")
            # Utiliser le module d'exécution comme dans execute_recipe_task
            recipe_path = os.path.join(os.path.dirname(__file__), "..", "packs", "form_3916")

            # Importer dynamiquement le module
            spec = importlib.util.spec_from_file_location("form_3916_pack", os.path.join(recipe_path, "graph_modern.py"))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Préparer les inputs pour la reprise
            resume_inputs = {
                **original_inputs,
                **state,
                "is_resume": True,
                "task_id": task_id
            }

            print(f"LEGACY: Resume inputs keys: {list(resume_inputs.keys())}")

            # Exécuter avec le nouveau système
            final_state = asyncio.run(module.execute(resume_inputs))
        else:
            print("LEGACY: Exécution normale (pas de reprise)")
            # Comportement original pour compatibilité
            final_state = asyncio.run(form_3916_graph_modern.ainvoke(state))

        # Déterminer le statut selon l'état retourné
        task_status = {"task_id": task_id}

        # Check for different states
        missing_critical = final_state.get("missing_critical", [])

        if missing_critical and not final_state.get("generated_pdf"):
            # Des champs critiques manquent et pas de PDF = besoin d'input utilisateur
            task_status["status"] = "AWAITING_USER_INPUT"

            # Créer le message pour l'utilisateur
            field_labels = {
                "nom": "Nom",
                "prenom": "Prénom",
                "date_naissance": "Date de naissance (JJ/MM/AAAA)",
                "lieu_naissance": "Lieu de naissance",
                "adresse_complete": "Adresse complète",
                "numero_compte": "Numéro de compte",
                "designation_etablissement": "Nom de l'établissement bancaire"
            }

            message = "Pour compléter le formulaire 3916, j'ai besoin des informations suivantes :\n\n"
            for field in missing_critical:
                label = field_labels.get(field, field)
                message += f"• {label}\n"

            task_status["current_question"] = final_state.get("_message", message)
            task_status["missing_fields"] = missing_critical
            task_status["result"] = {
                "consolidated_data": final_state.get("consolidated_data", {}),
                "missing_critical": missing_critical
            }
        elif final_state.get("generated_pdf"):
            # PDF généré avec succès
            pdf_bytes = final_state["generated_pdf"]
            task_status["status"] = "COMPLETED"
            task_status["generated_pdf"] = base64.b64encode(pdf_bytes).decode('utf-8')
            task_status["result"] = {
                "consolidated_data": final_state.get("consolidated_data", {}),
                "missing_critical": [],
                "missing_optional": final_state.get("missing_optional", [])
            }
        else:
            # État intermédiaire avec données consolidées
            task_status["status"] = "PROCESSING"
            task_status["result"] = {
                "consolidated_data": final_state.get("consolidated_data", {}),
                "missing_critical": missing_critical,
                "missing_optional": final_state.get("missing_optional", [])
            }

        # Sauvegarder l'état dans Redis
        redis_client.set(f"task:{task_id}", json.dumps(task_status, default=str))
        print(f"WORKER: État final sauvegardé pour la tâche {task_id}, status: {task_status['status']}")

    except Exception as e:
        # Gérer les erreurs et les sauvegarder dans l'état
        error_state = {
            "task_id": task_id,
            "status": "ERROR",
            "error": str(e)
        }
        redis_client.set(f"task:{task_id}", json.dumps(error_state, default=str))
        print(f"WORKER: Erreur lors de l'exécution de la tâche {task_id}: {e}")