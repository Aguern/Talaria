# Fichier: app/core/crud.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import text, func
from typing import List, Dict
from . import models

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(
        select(models.User)
        .options(selectinload(models.User.tenant))
        .filter(models.User.email == email)
    )
    return result.scalar_one_or_none()

async def get_tenant_by_name(db: AsyncSession, name: str):
    result = await db.execute(select(models.Tenant).filter(models.Tenant.name == name))
    return result.scalar_one_or_none()

async def create_tenant(db: AsyncSession, name: str):
    tenant = models.Tenant(name=name)
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant

async def get_or_create_tenant(db: AsyncSession, name: str):
    """Get existing tenant or create a new one"""
    tenant = await get_tenant_by_name(db, name)
    if not tenant:
        tenant = await create_tenant(db, name)
    return tenant

# Configuration management functions
from . import security

async def create_configuration(db: AsyncSession, tenant_id: int, pack_name: str, key: str, value: str):
    """Create a new configuration with encrypted value"""
    encrypted_value = security.encrypt_value(value)
    config = models.Configuration(
        tenant_id=tenant_id,
        pack_name=pack_name,
        key=key,
        value_encrypted=encrypted_value
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return config

async def get_configuration(db: AsyncSession, tenant_id: int, pack_name: str, key: str):
    """Get a configuration value (decrypted)"""
    result = await db.execute(
        select(models.Configuration)
        .filter(models.Configuration.tenant_id == tenant_id)
        .filter(models.Configuration.pack_name == pack_name)
        .filter(models.Configuration.key == key)
    )
    config = result.scalar_one_or_none()
    if config:
        return security.decrypt_value(config.value_encrypted)
    return None

async def update_configuration(db: AsyncSession, tenant_id: int, pack_name: str, key: str, value: str):
    """Update an existing configuration or create if not exists"""
    result = await db.execute(
        select(models.Configuration)
        .filter(models.Configuration.tenant_id == tenant_id)
        .filter(models.Configuration.pack_name == pack_name)
        .filter(models.Configuration.key == key)
    )
    config = result.scalar_one_or_none()
    
    if config:
        config.value_encrypted = security.encrypt_value(value)
        await db.commit()
        await db.refresh(config)
        return config
    else:
        return await create_configuration(db, tenant_id, pack_name, key, value)

# --- DÉBUT DES NOUVELLES FONCTIONS ---

async def create_document(db: AsyncSession, tenant_id: int, bofip_id: str, title: str, url: str = None, publication_date=None) -> tuple[models.Document, bool]:
    """Create a new document or return existing one. Returns (document, should_index)"""
    # Check if document exists
    result = await db.execute(
        select(models.Document)
        .options(selectinload(models.Document.chunks))
        .filter(models.Document.bofip_id == bofip_id)
        .filter(models.Document.tenant_id == tenant_id)
    )
    db_document = result.scalar_one_or_none()

    if db_document:
        # Check if document has chunks - if not, we need to index it
        has_chunks = len(db_document.chunks) > 0
        if has_chunks:
            return db_document, False
        else:
            # Document exists but has no chunks - needs indexing
            return db_document, True

    # Create new document
    new_document = models.Document(
        bofip_id=bofip_id,
        title=title,
        url=url,
        publication_date=publication_date,
        tenant_id=tenant_id
    )
    db.add(new_document)
    await db.commit()
    await db.refresh(new_document)
    return new_document, True

async def create_chunks(db: AsyncSession, document: models.Document, chunks_data: List[Dict]) -> int:
    """Create chunks with embeddings and tsvector for a document"""
    db_chunks = [
        models.Chunk(
            document_id=document.id,
            content=item['text'],
            embedding=item['embedding'],
            content_tsv=item['content_tsv']
        )
        for item in chunks_data
    ]
    db.add_all(db_chunks)
    await db.commit()
    return len(db_chunks)

async def get_similar_chunks(db: AsyncSession, query_embedding: List[float], tenant_id: int, limit: int = 5) -> List[models.Chunk]:
    """
    Trouve les chunks les plus similaires à un embedding de requête
    en utilisant l'opérateur de distance cosinus de pgvector.
    """
    # L'opérateur <=> calcule la distance cosinus (0 = identique, 1 = différent)
    # On cherche les plus petites distances.
    query = text("""
        SELECT 
            chunks.id, chunks.content, chunks.embedding, chunks.document_id
        FROM chunks
        JOIN documents ON chunks.document_id = documents.id
        WHERE documents.tenant_id = :tenant_id
        ORDER BY chunks.embedding <=> :query_embedding
        LIMIT :limit
    """)
    
    result = await db.execute(
        query,
        {
            "tenant_id": tenant_id,
            "query_embedding": str(query_embedding), # pgvector attend le vecteur sous forme de chaîne
            "limit": limit
        }
    )
    
    # On récupère les objets Chunk complets
    similar_chunks = []
    chunk_ids = [row[0] for row in result.fetchall()]
    if chunk_ids:
        res = await db.execute(
            select(models.Chunk).options(selectinload(models.Chunk.document)).where(models.Chunk.id.in_(chunk_ids))
        )
        similar_chunks = res.scalars().all()

    return similar_chunks

async def hybrid_search(db: AsyncSession, query: str, query_embedding: List[float], tenant_id: int, limit: int = 10) -> List[models.Chunk]:
    """
    Effectue une recherche hybride (mots-clés + sémantique) et fusionne les résultats avec RRF.
    """
    # Préparer la requête FTS - nettoyer et échapper les caractères spéciaux
    import re
    # Remove special characters and keep only alphanumeric and spaces
    cleaned_query = re.sub(r'[^a-zA-Z0-9\s]', ' ', query)
    # Remove multiple spaces and trim
    cleaned_query = ' '.join(cleaned_query.split())
    # Replace spaces with & for tsquery
    fts_query_text = cleaned_query.replace(" ", " & ")

    # 1. Recherche par mots-clés (Full-Text Search)
    fts_query = text("""
        SELECT id, rank
        FROM (
            SELECT c.id, ts_rank_cd(c.content_tsv, to_tsquery('french', :query)) as rank
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE d.tenant_id = :tenant_id AND c.content_tsv @@ to_tsquery('french', :query)
        ) as ranked
        WHERE rank > 0.1
        ORDER BY rank DESC
        LIMIT 20
    """)

    fts_results = await db.execute(fts_query, {"tenant_id": tenant_id, "query": fts_query_text})
    fts_ranked_ids = {row[0]: row[1] for row in fts_results.fetchall()}

    # 2. Recherche vectorielle
    vector_query = text("""
        SELECT c.id, (1 - (c.embedding <=> :embedding)) as score
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE d.tenant_id = :tenant_id
        ORDER BY score DESC
        LIMIT 20
    """)

    vector_results = await db.execute(vector_query, {"tenant_id": tenant_id, "embedding": str(query_embedding)})
    vector_ranked_ids = {row[0]: row[1] for row in vector_results.fetchall()}

    # 3. Fusion des résultats avec Reciprocal Rank Fusion (RRF)
    fused_scores = {}
    k = 60.0  # Constante de RRF

    # Ajouter les scores FTS
    for doc_id, rank in fts_ranked_ids.items():
        fused_scores[doc_id] = fused_scores.get(doc_id, 0) + 1.0 / (k + rank)

    # Ajouter les scores vectoriels (convertir score en rang)
    for doc_id, score in vector_ranked_ids.items():
        rank = int((1.0 - score) * 100)  # Simuler un rang
        fused_scores[doc_id] = fused_scores.get(doc_id, 0) + 1.0 / (k + rank)

    # 4. Trier les résultats fusionnés et récupérer les objets Chunk
    sorted_fused_ids = sorted(fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True)
    top_ids = sorted_fused_ids[:limit]

    if not top_ids:
        return []

    # Récupérer les chunks avec leurs documents
    res = await db.execute(
        select(models.Chunk).options(selectinload(models.Chunk.document)).where(models.Chunk.id.in_(top_ids))
    )
    return list(res.scalars().unique().all())