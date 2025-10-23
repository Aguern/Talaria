# Fichier: app/api/recipes.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body, Form, status
from fastapi.responses import Response
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
from redis import Redis
import structlog

from core.auth import get_current_active_user
from core.schemas import CurrentUser, RecipeManifest
from core.orchestrator import get_orchestrator, OrchestratorService
from core.tasks import execute_recipe_task

log = structlog.get_logger()

router = APIRouter(
    prefix="/api/recipes",
    tags=["Recipes"],
    responses={404: {"description": "Not found"}},
)

# Connexion Redis pour récupérer les résultats des tâches
redis_client = Redis.from_url("redis://redis:6379/0", decode_responses=True)

# Schémas de requête/réponse
class RecipeExecutionRequest(BaseModel):
    context: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None

class HumanInputRequest(BaseModel):
    question: str
    input_type: str = "text"  # text, file, choice, multiple_files
    choices: Optional[List[str]] = None
    context: Optional[str] = None

class ConversationMessage(BaseModel):
    id: str
    type: str  # system, user, assistant
    content: str
    timestamp: str
    input_type: Optional[str] = None
    files: Optional[List[Dict[str, Any]]] = None

class TaskStatusResponse(BaseModel):
    task_id: str
    recipe_id: str
    status: str
    progress: Optional[int] = None
    current_step: Optional[str] = None
    message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    human_input_request: Optional[HumanInputRequest] = None
    conversation_history: Optional[List[ConversationMessage]] = None

class RecipeExecutionResponse(BaseModel):
    task_id: str
    status: str
    message: str


@router.get("/", response_model=List[RecipeManifest])
async def list_recipes(
    orchestrator: OrchestratorService = Depends(get_orchestrator),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """
    Liste toutes les recettes disponibles découvertes automatiquement.

    Cette route scanne les dossiers de packs, charge et valide les manifests,
    puis retourne la liste complète des recettes disponibles.
    """
    try:
        recipes = await orchestrator.discover_recipes()
        log.info("Recettes découvertes pour l'utilisateur",
                user_email=current_user.user.email,
                recipe_count=len(recipes))
        return recipes

    except Exception as e:
        log.error("Erreur lors de la découverte des recettes", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la découverte des recettes"
        )


@router.get("/{recipe_id}", response_model=RecipeManifest)
async def get_recipe(
    recipe_id: str,
    orchestrator: OrchestratorService = Depends(get_orchestrator),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """
    Récupère les détails d'une recette spécifique par son ID.
    """
    try:
        manifest = await orchestrator.get_recipe_manifest(recipe_id)
        if not manifest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recette '{recipe_id}' introuvable"
            )

        log.info("Détails de recette récupérés",
                recipe_id=recipe_id,
                user_email=current_user.user.email)
        return manifest

    except HTTPException:
        raise
    except Exception as e:
        log.error("Erreur lors de la récupération de la recette",
                 recipe_id=recipe_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération de la recette"
        )


@router.post("/{recipe_id}/run", response_model=RecipeExecutionResponse)
async def run_recipe(
    recipe_id: str,
    request: str = Form(...),
    files: Optional[List[UploadFile]] = File(None),
    orchestrator: OrchestratorService = Depends(get_orchestrator),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """
    Lance l'exécution d'une recette et retourne immédiatement le task_id.

    Cette route :
    1. Valide la recette
    2. Prépare les inputs selon le manifest
    3. Lance la tâche Celery via l'orchestrateur
    4. Retourne immédiatement sans attendre l'exécution

    Le client doit ensuite utiliser GET /api/recipes/tasks/{task_id} pour
    suivre la progression et récupérer les résultats.
    """
    try:
        # Parse JSON request from FormData
        request_data = RecipeExecutionRequest.model_validate_json(request)

        # Vérifier que la recette existe
        manifest = await orchestrator.get_recipe_manifest(recipe_id)
        if not manifest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recette '{recipe_id}' introuvable"
            )

        # Préparer les inputs selon le manifest de la recette
        inputs = await prepare_recipe_inputs(manifest, files, request_data)

        log.info("Lancement de la recette",
                recipe_id=recipe_id,
                user_email=current_user.user.email,
                input_keys=list(inputs.keys()))

        # Lancer la tâche via l'orchestrateur (délégation complète)
        task_id = await orchestrator.run_recipe(recipe_id, inputs)

        return RecipeExecutionResponse(
            task_id=task_id,
            status="pending",
            message=f"Recette '{recipe_id}' lancée avec succès. Utilisez le task_id pour suivre la progression."
        )

    except HTTPException:
        raise
    except ValueError as e:
        log.error("Erreur de validation des inputs",
                 recipe_id=recipe_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        log.error("Erreur lors du lancement de la recette",
                 recipe_id=recipe_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du lancement de la recette"
        )


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """
    Récupère le statut et les résultats d'une tâche d'exécution de recette.

    Cette route interroge Redis pour obtenir l'état actuel de la tâche.
    Les statuts possibles sont :
    - "pending": Tâche en attente de traitement
    - "completed": Tâche terminée avec succès
    - "error": Erreur lors de l'exécution
    """
    try:
        task_data = redis_client.get(f"task:{task_id}")
        if not task_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tâche '{task_id}' introuvable"
            )

        task_info = json.loads(task_data)

        log.info("Statut de tâche récupéré",
                task_id=task_id,
                status=task_info.get("status", "unknown"),
                user_email=current_user.user.email)

        return TaskStatusResponse(**task_info)

    except json.JSONDecodeError as e:
        log.error("Erreur de décodage JSON pour la tâche",
                 task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur de format des données de la tâche"
        )
    except HTTPException:
        raise
    except Exception as e:
        log.error("Erreur lors de la récupération du statut",
                 task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération du statut"
        )


@router.get("/tasks/{task_id}/download/{output_name}")
async def download_task_output(
    task_id: str,
    output_name: str,
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """
    Télécharge un fichier généré par une tâche de recette.

    Cette route permet de télécharger les fichiers produits par les recettes
    (ex: PDF générés, CSV, etc.) en fonction du nom d'output défini dans le manifest.
    """
    try:
        # Récupérer les résultats de la tâche
        task_data = redis_client.get(f"task:{task_id}")
        if not task_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tâche '{task_id}' introuvable"
            )

        task_info = json.loads(task_data)

        if task_info.get("status") != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La tâche n'est pas terminée"
            )

        result = task_info.get("result", {})
        if output_name not in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Output '{output_name}' introuvable dans les résultats"
            )

        file_path = result[output_name]

        # Vérifier que le fichier existe
        from pathlib import Path
        if not Path(file_path).exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fichier introuvable sur le serveur"
            )

        # Lire et retourner le fichier
        with open(file_path, 'rb') as f:
            file_content = f.read()

        # Déterminer le type MIME selon l'extension
        content_type = "application/octet-stream"
        if file_path.endswith('.pdf'):
            content_type = "application/pdf"
        elif file_path.endswith('.csv'):
            content_type = "text/csv"

        log.info("Fichier téléchargé",
                task_id=task_id,
                output_name=output_name,
                file_size=len(file_content),
                user_email=current_user.user.email)

        return Response(
            content=file_content,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={output_name}_{task_id}.{file_path.split('.')[-1]}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error("Erreur lors du téléchargement",
                 task_id=task_id, output_name=output_name, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du téléchargement"
        )


async def prepare_recipe_inputs(
    manifest: RecipeManifest,
    files: Optional[List[UploadFile]],
    request: RecipeExecutionRequest
) -> Dict[str, Any]:
    """
    Prépare les inputs pour l'exécution de la recette selon son manifest.

    Cette fonction convertit les fichiers uploadés et les données de la requête
    en un dictionnaire conforme aux attentes de la fonction execute() de la recette.
    """
    inputs = {}

    # Traiter chaque input défini dans le manifest
    for input_param in manifest.inputs:
        input_name = input_param.name

        if input_param.type == "file":
            if input_param.multiple:
                # Input multiple de fichiers
                if files:
                    file_contents = []
                    for file in files:
                        content = await file.read()
                        file_contents.append(content)
                    inputs[input_name] = file_contents
                elif input_param.required:
                    raise ValueError(f"Input requis '{input_name}' manquant (fichiers)")
            else:
                # Input de fichier unique
                if files and len(files) > 0:
                    content = await files[0].read()
                    inputs[input_name] = content
                elif input_param.required:
                    raise ValueError(f"Input requis '{input_name}' manquant (fichier)")

        elif input_param.type == "text":
            # Input texte depuis la requête
            if input_name == "context" and request.context:
                inputs[input_name] = request.context
            elif (request.additional_data and
                  input_name in request.additional_data):
                inputs[input_name] = request.additional_data[input_name]
            elif input_param.required:
                raise ValueError(f"Input requis '{input_name}' manquant (texte)")

        elif input_param.type in ["number", "boolean", "json"]:
            # Autres types depuis additional_data
            if (request.additional_data and
                input_name in request.additional_data):
                inputs[input_name] = request.additional_data[input_name]
            elif input_param.required:
                raise ValueError(f"Input requis '{input_name}' manquant")

    return inputs


@router.post("/tasks/{task_id}/resume")
async def resume_task(
    task_id: str,
    response: str = Body(...),
    files: Optional[List[UploadFile]] = File(None),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """
    Reprend une tâche en pause en fournissant la réponse de l'utilisateur.

    Cette route est utilisée lorsqu'une tâche est en statut 'waiting_for_human_input'
    et que l'utilisateur fournit la réponse demandée par l'agent.
    """
    try:
        # Vérifier que la tâche existe et est en attente d'input
        task_data = redis_client.get(f"task:{task_id}")
        if not task_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tâche '{task_id}' introuvable"
            )

        task_info = json.loads(task_data)

        if task_info.get("status") != "waiting_for_human_input":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La tâche n'est pas en attente d'input utilisateur (statut: {task_info.get('status')})"
            )

        # Préparer la réponse utilisateur
        user_response = {
            "response": response,
            "timestamp": f"{__import__('datetime').datetime.now().isoformat()}"
        }

        # Traiter les fichiers si fournis
        if files:
            file_contents = []
            for file in files:
                content = await file.read()
                file_contents.append({
                    "name": file.filename,
                    "content": content,
                    "type": file.content_type
                })
            user_response["files"] = file_contents

        # Mettre à jour le statut de la tâche
        task_info.update({
            "status": "running",
            "human_input_response": user_response,
            "message": "Traitement de la réponse utilisateur...",
            "current_step": "Reprise de l'exécution",
            "updated_at": f"{__import__('datetime').datetime.now().isoformat()}"
        })

        # Ajouter la réponse à l'historique de conversation
        if "conversation_history" not in task_info:
            task_info["conversation_history"] = []

        # Ajouter la réponse utilisateur à l'historique
        task_info["conversation_history"].append({
            "id": f"user_{len(task_info['conversation_history'])}",
            "type": "user",
            "content": response,
            "timestamp": user_response["timestamp"],
            "files": [{"name": f.filename} for f in files] if files else None
        })

        # Sauvegarder dans Redis
        redis_client.set(f"task:{task_id}", json.dumps(task_info))

        # Déclencher la reprise de la tâche Celery avec la réponse utilisateur
        original_inputs = task_info.get("inputs", {})

        # Vérifier si les documents sont présents dans les inputs originaux
        if "documents" not in original_inputs:
            log.warning("Documents manquants dans inputs originaux, récupération depuis l'état sauvegardé", task_id=task_id)
            # Essayer de récupérer les documents depuis l'état sauvegardé
            if "graph_state" in task_info and "input_files" in task_info["graph_state"]:
                input_files = task_info["graph_state"]["input_files"]
                # Reconstituer les documents depuis input_files
                documents = []
                for file_dict in input_files:
                    for name, content in file_dict.items():
                        documents.append(content)
                original_inputs["documents"] = documents
                log.info("Documents reconstitués depuis l'état sauvegardé", task_id=task_id, count=len(documents))

        # Ajouter la réponse utilisateur aux inputs pour la reprise
        resume_inputs = {
            **original_inputs,
            "is_resume": True,
            "human_input_response": user_response,
            "task_id": task_id  # Pour que la tâche puisse récupérer l'état depuis Redis
        }

        # Relancer la tâche avec les nouvelles données
        execute_recipe_task.apply_async(
            args=[task_info.get("recipe_id"), task_id, resume_inputs],
            task_id=f"resume_{task_id}"
        )

        log.info("Tâche reprise avec succès",
                task_id=task_id,
                user_email=current_user.user.email,
                response_length=len(response),
                files_count=len(files) if files else 0)

        return {
            "success": True,
            "message": "Réponse enregistrée, reprise de l'exécution en cours",
            "task_id": task_id
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error("Erreur lors de la reprise de la tâche",
                 task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la reprise de la tâche"
        )