# Fichier: app/packs/bofip/router.py

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from typing import List
import json
from core import auth
from core.schemas import CurrentUser
from . import logic, schemas

router = APIRouter(
    prefix="/packs/bofip",
    tags=["BOFIP Pack"],
    responses={404: {"description": "Not found"}},
)

@router.post("/ask", response_model=schemas.AskResponse)
async def ask_bofip_agent(
    request: schemas.AskRequest,
    current_user: CurrentUser = Depends(auth.get_current_active_user)
):
    """
    Interroge l'agent RAG sur la base documentaire du BOFIP.
    """
    # On utilise l'instance unique de notre agent
    response = await logic.bofip_agent.ask(
        question=request.question,
        tenant_id=current_user.tenant.id,
        conversation_id=request.conversation_id,
        previous_context=request.previous_context
    )
    return response

@router.get("/suggestions", response_model=List[str])
async def get_suggestions(
    query: str = Query(..., min_length=2, max_length=100),
    limit: int = Query(5, ge=1, le=10),
    current_user: CurrentUser = Depends(auth.get_current_active_user)
):
    """
    Retourne des suggestions de recherche basées sur la query et le contexte BOFIP.
    """
    suggestions = await logic.bofip_agent.get_suggestions(
        query=query,
        tenant_id=current_user.tenant.id,
        limit=limit
    )
    return suggestions


@router.post("/ask-stream")
async def ask_bofip_agent_stream(
    request: schemas.AskRequest,
    current_user: CurrentUser = Depends(auth.get_current_active_user)
):
    """
    Interroge l'agent RAG avec streaming SSE en temps réel.
    """
    async def generate_stream():
        # Envoyer un padding initial pour forcer le début du streaming
        yield ": " + " " * 2048 + "\n\n"

        try:
            async for event in logic.bofip_agent.ask_stream(
                question=request.question,
                tenant_id=current_user.tenant.id,
                conversation_id=request.conversation_id,
                previous_context=request.previous_context
            ):
                # Format SSE: data: {json}\n\n avec padding pour forcer le flush
                data_line = f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                yield data_line

                # Ajouter un petit délai pour s'assurer que chaque événement est envoyé séparément
                if event.get("type") == "token":
                    import asyncio
                    await asyncio.sleep(0.001)  # 1ms pour forcer le flush

        except Exception as e:
            # Envoyer l'erreur comme événement SSE
            error_event = {
                "type": "error",
                "message": str(e)
            }
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "Content-Encoding": "none",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )