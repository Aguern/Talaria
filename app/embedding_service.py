# Fichier: app/embedding_service.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from core.engine import get_embed_model

app = FastAPI(title="Embedding Service")
embed_model = None

@app.on_event("startup")
def startup_event():
    """Charge le modèle au démarrage du service."""
    global embed_model
    embed_model = get_embed_model()

class EmbeddingRequest(BaseModel):
    texts: List[str]

class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]

@app.post("/embed", response_model=EmbeddingResponse)
async def create_embeddings(request: EmbeddingRequest):
    """Crée les embeddings pour une liste de textes."""
    if not embed_model:
        raise HTTPException(status_code=503, detail="Embedding model is not ready.")
    
    try:
        embeddings = embed_model.embed_documents(request.texts)
        return EmbeddingResponse(embeddings=embeddings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok" if embed_model else "loading"}