# Fichier: app/packs/bofip/logic.py

import structlog
import uuid
import asyncio
from typing import List, Optional, AsyncGenerator, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from core import crud
from core.database import SessionLocal
from core.engine import get_embed_client, get_reranker_model
from . import schemas

log = structlog.get_logger()

# Initialisation du LLM de génération (le "cerveau rédacteur")
chat_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)

# Création d'un template de prompt rigoureux
PROMPT_TEMPLATE = """
Vous êtes un assistant fiscal expert, spécialisé dans la doctrine du BOFIP. Votre mission est de répondre à la question de l'utilisateur de manière précise, factuelle et concise, en vous basant EXCLUSIVEMENT sur les extraits de documents fournis ci-dessous.

CONTEXTE (Sources numérotées) :
---
{context}
---

QUESTION : {question}

INSTRUCTIONS :
1. Ne répondez qu'à partir du contexte fourni. Si le contexte ne permet pas de répondre, dites "Je ne dispose pas d'informations suffisantes pour répondre à cette question dans les documents fournis.".
2. Rédigez une réponse claire et synthétique.
3. IMPORTANT : Insérez des marqueurs de citation [1], [2], [3], etc. dans votre réponse pour référencer les sources utilisées. Chaque numéro correspond à l'ordre des documents dans le contexte.
4. Utilisez les marqueurs immédiatement après l'information citée, par exemple : "Le crédit d'impôt recherche est de 30% [1]".
5. Ne mentionnez PAS "Selon le contexte fourni" ou des phrases similaires. Répondez directement.

Exemple de réponse avec citations :
"L'article 199 sexdecies du CGI instaure un crédit d'impôt pour l'emploi d'un salarié à domicile [1]. Le taux applicable est de 50% des dépenses [2]."
"""


class BofipAgent:
    async def ask(
        self,
        question: str,
        tenant_id: int,
        conversation_id: Optional[str] = None,
        previous_context: Optional[List[schemas.ConversationContext]] = None
    ) -> schemas.AskResponse:
        log.info("Agent RAG BOFIP interrogé", question=question, tenant_id=tenant_id)
        
        # Obtenir le client d'embedding et une session de BDD
        embed_client = get_embed_client()
        try:
            async with SessionLocal() as db_session:
                # 1. Vectoriser la question de l'utilisateur
                log.info("Vectorisation de la question...")
                question_embedding = await embed_client.embed_query(question)
                
                # 2. Recherche hybride (vectorielle + full-text) - Phase 1
                log.info("Lancement de la recherche hybride (phase 1)...")
                initial_chunks = await crud.hybrid_search(
                    db=db_session,
                    query=question,
                    query_embedding=question_embedding,
                    tenant_id=tenant_id,
                    limit=25  # On récupère 25 candidats pour le re-ranking
                )
                
                if not initial_chunks:
                    return schemas.AskResponse(
                        answer="Je n'ai trouvé aucun document pertinent pour répondre à votre question.",
                        citations=[]
                    )

                # 3. Re-ranking des chunks
                log.info(f"Re-ranking de {len(initial_chunks)} chunks...")
                reranker = get_reranker_model()

                # Préparer les paires [question, passage] pour le modèle
                pairs = [[question, chunk.content] for chunk in initial_chunks]

                # Le modèle prédit un score de similarité pour chaque paire
                scores = reranker.predict(pairs)

                # Combiner chunks et scores, puis trier par score décroissant
                reranked_chunks_with_scores = sorted(
                    zip(initial_chunks, scores),
                    key=lambda x: x[1],
                    reverse=True
                )

                # Ne garder que le top 5 final
                final_chunks = [chunk for chunk, score in reranked_chunks_with_scores[:5]]
                log.info("Re-ranking terminé.", final_count=len(final_chunks))

                # Construire le contexte avec numérotation des sources
                context_parts = []
                for i, chunk in enumerate(final_chunks, 1):
                    source_id = chunk.document.bofip_id if chunk.document else f"Document-{chunk.id}"
                    context_parts.append(f"[SOURCE {i}] ({source_id}):\n{chunk.content}")

                context_text = "\n\n---\n\n".join(context_parts)
                log.info("Contexte assemblé à partir des chunks re-classés.", count=len(final_chunks))

                # 3. Construire le prompt final (Augmentation)
                prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
                chain = prompt | chat_llm
                
                # 4. Générer la réponse (Generation)
                log.info("Génération de la réponse finale avec le LLM...")
                llm_response = await chain.ainvoke({
                    "context": context_text,
                    "question": question
                })
                answer = llm_response.content

                # 5. Formater les citations à partir des chunks re-classés
                citations = [
                    schemas.Citation(
                        source=chunk.document.bofip_id if chunk.document else "Source inconnue",
                        excerpt=chunk.content[:300] + "..." # On tronque l'extrait pour l'affichage
                    )
                    for chunk in final_chunks
                ]
                
                log.info("Réponse de l'agent générée avec succès.", tenant_id=tenant_id)

                # Générer un ID de conversation si nécessaire
                if not conversation_id:
                    conversation_id = str(uuid.uuid4())

                # Générer des questions suggérées basées sur la réponse
                suggested_questions = await self._generate_suggested_questions(
                    question, answer, final_chunks
                )

                return schemas.AskResponse(
                    answer=answer,
                    citations=citations,
                    suggested_questions=suggested_questions,
                    conversation_id=conversation_id
                )
        finally:
            # Fermer le client pour éviter les fuites de ressources
            try:
                await embed_client.close()
            except:
                pass

    async def ask_stream(
        self,
        question: str,
        tenant_id: int,
        conversation_id: Optional[str] = None,
        previous_context: Optional[List[schemas.ConversationContext]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Version streaming de la méthode ask qui yield des événements SSE."""
        log.info("Agent RAG BOFIP streaming interrogé", question=question, tenant_id=tenant_id)

        # Générer un ID de conversation si nécessaire
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        embed_client = get_embed_client()
        try:
            async with SessionLocal() as db_session:
                # Étape 1: Vectorisation
                log.info("Yielding status: vectorisation")
                yield {
                    "type": "status",
                    "message": "Vectorisation de la question...",
                    "conversation_id": conversation_id
                }

                question_embedding = await embed_client.embed_query(question)

                # Étape 2: Recherche hybride
                yield {
                    "type": "status",
                    "message": "Recherche dans les documents BOFIP...",
                    "conversation_id": conversation_id
                }

                initial_chunks = await crud.hybrid_search(
                    db=db_session,
                    query=question,
                    query_embedding=question_embedding,
                    tenant_id=tenant_id,
                    limit=25
                )

                if not initial_chunks:
                    yield {
                        "type": "error",
                        "message": "Aucun document pertinent trouvé",
                        "conversation_id": conversation_id
                    }
                    return

                # Étape 3: Re-ranking
                yield {
                    "type": "status",
                    "message": "Analyse et classement des sources...",
                    "conversation_id": conversation_id
                }

                reranker = get_reranker_model()
                pairs = [[question, chunk.content] for chunk in initial_chunks]
                scores = reranker.predict(pairs)

                reranked_chunks_with_scores = sorted(
                    zip(initial_chunks, scores),
                    key=lambda x: x[1],
                    reverse=True
                )
                final_chunks = [chunk for chunk, score in reranked_chunks_with_scores[:5]]

                # Construire le contexte
                context_parts = []
                for i, chunk in enumerate(final_chunks, 1):
                    source_id = chunk.document.bofip_id if chunk.document else f"Document-{chunk.id}"
                    context_parts.append(f"[SOURCE {i}] ({source_id}):\n{chunk.content}")
                context_text = "\n\n---\n\n".join(context_parts)

                # Étape 4: Génération streaming
                yield {
                    "type": "status",
                    "message": "Génération de la réponse...",
                    "conversation_id": conversation_id
                }

                # LLM avec streaming - approche recommandée LangChain
                streaming_llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0.1,
                    streaming=True
                )

                prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
                chain = prompt | streaming_llm

                # Utiliser astream() pour un vrai streaming
                log.info("Starting LLM streaming...")
                final_answer = ""
                async for chunk in chain.astream({
                    "context": context_text,
                    "question": question
                }):
                    # Les chunks contiennent le contenu incrémental
                    if chunk.content:
                        log.info(f"Streaming token: {repr(chunk.content)}")
                        final_answer += chunk.content
                        yield {
                            "type": "token",
                            "content": chunk.content,
                            "conversation_id": conversation_id
                        }

                # Étape 5: Citations
                citations = [
                    schemas.Citation(
                        source=chunk.document.bofip_id if chunk.document else "Source inconnue",
                        excerpt=chunk.content[:300] + "..."
                    )
                    for chunk in final_chunks
                ]

                yield {
                    "type": "citations",
                    "citations": [c.dict() for c in citations],
                    "conversation_id": conversation_id
                }

                # Étape 6: Questions suggérées
                suggested_questions = await self._generate_suggested_questions(
                    question, final_answer, final_chunks
                )

                yield {
                    "type": "suggested_questions",
                    "questions": suggested_questions,
                    "conversation_id": conversation_id
                }

                # Événement final
                yield {
                    "type": "done",
                    "conversation_id": conversation_id
                }

        finally:
            try:
                await embed_client.close()
            except:
                pass

    async def _generate_suggested_questions(
        self, question: str, answer: str, chunks: List
    ) -> List[str]:
        """Génère des questions de suivi pertinentes basées sur la réponse."""
        try:
            prompt = ChatPromptTemplate.from_template("""
Basé sur cette question et réponse, suggérez 3 questions de suivi pertinentes.
Les questions doivent être en français, concises et explorer des aspects connexes du sujet.

Question originale : {question}
Réponse : {answer}

Format : Listez uniquement les 3 questions, une par ligne, sans numérotation.
""")
            chain = prompt | chat_llm
            result = await chain.ainvoke({"question": question, "answer": answer[:500]})

            # Parse les questions du résultat
            questions = [q.strip() for q in result.content.split('\n') if q.strip()]
            return questions[:3]  # Limite à 3 questions
        except Exception as e:
            log.warning("Échec de génération des questions suggérées", error=str(e))
            return []

    async def get_suggestions(
        self, query: str, tenant_id: int, limit: int = 5
    ) -> List[str]:
        """Retourne des suggestions de recherche basées sur la query."""
        # Liste de suggestions BOFIP courantes
        common_suggestions = [
            "Crédit d'impôt recherche (CIR)",
            "TVA intracommunautaire",
            "Plus-values immobilières",
            "Réduction d'impôt Pinel",
            "Déficit foncier",
            "Prélèvement à la source",
            "Contribution économique territoriale (CET)",
            "Taxe sur les salaires",
            "Crédit d'impôt pour l'emploi d'un salarié à domicile",
            "Exonération de taxe d'habitation",
            "Régime réel simplifié",
            "Micro-BIC",
            "Régime des sociétés mères et filiales",
            "Intégration fiscale",
            "Provision pour dépréciation"
        ]

        # Filtrer les suggestions qui commencent par la query
        query_lower = query.lower()
        filtered = [
            s for s in common_suggestions
            if query_lower in s.lower()
        ]

        # Si pas assez de suggestions, ajouter celles qui contiennent la query
        if len(filtered) < limit:
            additional = [
                s for s in common_suggestions
                if query_lower in s.lower() and s not in filtered
            ]
            filtered.extend(additional)

        return filtered[:limit]

# On crée une instance unique de l'agent pour être utilisée par l'API
bofip_agent = BofipAgent()