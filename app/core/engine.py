# Fichier: app/core/engine.py

import httpx
from typing import List
import structlog
from langchain_huggingface import HuggingFaceEmbeddings
from sentence_transformers.cross_encoder import CrossEncoder

log = structlog.get_logger()

# L'URL de notre nouveau service, accessible via Docker Compose
EMBEDDING_SERVICE_URL = "http://embedding-api:8001/embed"

class EmbeddingClient:
    def __init__(self, url: str):
        self.url = url
        # Never share HTTP client between tasks/threads
        # Each instance creates its own client when needed

    async def _embed(self, texts: List[str]) -> List[List[float]]:
        # Create a new client for each embed operation
        # This ensures no event loop conflicts
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(self.url, json={"texts": texts})
                response.raise_for_status()
                return response.json()["embeddings"]
            except httpx.HTTPError as e:
                log.error("Erreur de communication avec le service d'embedding.", error=str(e))
                raise

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return await self._embed(texts)

    async def embed_query(self, text: str) -> List[float]:
        embeddings = await self._embed([text])
        return embeddings[0]

    async def close(self):
        """No-op since we use context managers for clients"""
        pass

def get_embed_client():
    """Create a new embedding client instance for each worker"""
    return EmbeddingClient(url=EMBEDDING_SERVICE_URL)

# Fonction legacy pour le service d'embedding
_embed_model = None

def get_embed_model():
    """
    Charge le modèle d'embedding Hugging Face via LangChain.
    C'est un singleton pour éviter de recharger le modèle en mémoire à chaque appel.
    """
    global _embed_model
    if _embed_model is None:
        log.info("Chargement du modèle d'embedding 'paraphrase-multilingual-mpnet-base-v2'...")
        _embed_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
            model_kwargs={'device': 'cpu'}  # On force l'utilisation du CPU
        )
        log.info("Modèle d'embedding chargé avec succès.")
    return _embed_model

# Modèle de re-ranking
_reranker_model = None

def get_reranker_model():
    """
    Charge le modèle de re-ranking en mémoire ou le retourne s'il est déjà chargé.
    """
    global _reranker_model
    if _reranker_model is None:
        log.info("Chargement du modèle de re-ranking 'bge-reranker-base'...")
        # Modèle très performant et léger, idéal pour le re-ranking sur CPU
        _reranker_model = CrossEncoder('BAAI/bge-reranker-base')
        log.info("Modèle de re-ranking chargé avec succès.")
    return _reranker_model