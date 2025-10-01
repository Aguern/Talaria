# Fichier: app/packs/form_3916/router.py
# VERSION 2.0 - Asynchrone avec Redis

import uuid
import json
import base64
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Dict, List
from redis import Redis

from core import auth
from core.schemas import CurrentUser
from core.tasks import execute_recipe_graph

# Connexion à Redis (partagée avec les tâches)
redis_client = Redis.from_url("redis://redis:6379/0", decode_responses=True)

router = APIRouter(
    prefix="/packs/form3916",
    tags=["Pack Formulaire 3916"],
)

# Définitions Pydantic
class StartResponse(BaseModel):
    task_id: str

class StatusResponse(BaseModel):
    task_id: str
    status: str
    question: str | None = None
    result_url: str | None = None
    error: str | None = None

class ContinueRequest(BaseModel):
    response: Dict[str, str]


@router.post("/start", response_model=StartResponse)
async def start_recipe(
    files: List[UploadFile] = File(...),
    current_user: CurrentUser = Depends(auth.get_current_active_user)
):
    """Lance la recette en uploadant un ou plusieurs documents."""
    task_id = str(uuid.uuid4())

    input_files_data = []
    for file in files:
        content = await file.read()
        # Important: Le contenu des fichiers ne peut pas être directement sérialisé en JSON.
        # On ne le passera pas à Celery. On le traite ici et on ne passe que le texte.
        # Pour des fichiers volumineux, on les sauvegarderait sur un S3 et on ne passerait que l'URL.
        input_files_data.append({file.filename: content})

    initial_state = { "input_files": input_files_data }

    # 1. Sauvegarder l'état initial dans Redis pour indiquer que la tâche existe
    redis_client.set(f"task:{task_id}", json.dumps({"status": "PENDING"}))

    # 2. Lancer la tâche de fond avec Celery
    execute_recipe_graph.delay(task_id=task_id, state=initial_state)

    return {"task_id": task_id}


@router.get("/status/{task_id}", response_model=StatusResponse)
async def get_status(task_id: str, current_user: CurrentUser = Depends(auth.get_current_active_user)):
    """Récupère le statut et l'état actuel d'une tâche depuis Redis."""
    state_json = redis_client.get(f"task:{task_id}")
    if not state_json:
        raise HTTPException(status_code=404, detail="Task not found")

    state = json.loads(state_json)

    if state.get("error"):
        return {"task_id": task_id, "status": "FAILED", "error": state["error"]}
    if state.get("question_to_user"):
        return {"task_id": task_id, "status": "WAITING_FOR_INPUT", "question": state["question_to_user"]}
    if state.get("generated_pdf"):
        # Dans une vraie app, on générerait une URL sécurisée pour télécharger le fichier
        return {"task_id": task_id, "status": "COMPLETED", "result_url": f"/files/{task_id}.pdf"}

    return {"task_id": task_id, "status": state.get("status", "PROCESSING")}


@router.post("/continue/{task_id}", response_model=StartResponse)
async def continue_recipe(
    task_id: str,
    request: ContinueRequest,
    current_user: CurrentUser = Depends(auth.get_current_active_user)
):
    """Fournit une réponse humaine et relance l'exécution de la tâche."""
    state_json = redis_client.get(f"task:{task_id}")
    if not state_json:
        raise HTTPException(status_code=404, detail="Task not found")

    current_state = json.loads(state_json)
    if not current_state.get("question_to_user"):
        raise HTTPException(status_code=400, detail="Task is not waiting for input.")

    current_state["human_response"] = request.response
    current_state["question_to_user"] = None  # Efface la question pour indiquer qu'on a reçu la réponse

    # Mettre à jour l'état dans Redis pour montrer que le traitement reprend
    current_state["status"] = "PROCESSING"
    redis_client.set(f"task:{task_id}", json.dumps(current_state, default=str))

    # Lancer la tâche de fond pour continuer le graphe
    execute_recipe_graph.delay(task_id=task_id, state=current_state)

    return {"task_id": task_id}


@router.get("/files/{task_id}.pdf")
async def download_pdf(task_id: str, current_user: CurrentUser = Depends(auth.get_current_active_user)):
    """
    Sert le fichier PDF généré pour une tâche terminée.
    """
    state_json = redis_client.get(f"task:{task_id}")
    if not state_json:
        raise HTTPException(status_code=404, detail="Task not found")

    state = json.loads(state_json)

    pdf_b64 = state.get("generated_pdf")
    if not pdf_b64:
        raise HTTPException(status_code=404, detail="PDF not generated for this task or task not complete.")

    try:
        # Décoder la chaîne base64 en bytes
        pdf_bytes = base64.b64decode(pdf_b64)

        # Retourner une réponse HTTP avec le bon type de contenu
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=formulaire_3916_{task_id}.pdf"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to decode or serve PDF: {e}")