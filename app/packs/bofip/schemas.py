# Fichier: app/packs/bofip/schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Citation(BaseModel):
    source: str
    excerpt: str
    doc_id: Optional[str] = None
    page: Optional[int] = None
    file_name: Optional[str] = None
    doc_type: Optional[str] = None

class ConversationContext(BaseModel):
    question: str
    answer: str
    citations: Optional[List[Citation]] = None

class AskRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=500)
    conversation_id: Optional[str] = None
    previous_context: Optional[List[ConversationContext]] = None
    # Plus tard, nous pourrons ajouter des filtres

class AskResponse(BaseModel):
    answer: str
    citations: List[Citation]
    suggested_questions: Optional[List[str]] = None
    conversation_id: Optional[str] = None
    timing_ms: Optional[float] = None
    confidence: Optional[float] = None
    enriched_with: Optional[str] = None