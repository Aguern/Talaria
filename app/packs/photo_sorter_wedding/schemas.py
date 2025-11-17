"""
Photo Sorter Wedding Pack - Pydantic Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PhotoAnalysis(BaseModel):
    """Analyse d'une photo individuelle"""
    file_path: str
    file_name: str
    quality_score: float = Field(..., ge=0, le=100, description="Score de qualité global (0-100)")
    composition_score: float = Field(..., ge=0, le=100, description="Score de cadrage/composition")
    lighting_score: float = Field(..., ge=0, le=100, description="Score de lumière")
    background_score: float = Field(..., ge=0, le=100, description="Score d'arrière-plan")
    subject_score: float = Field(..., ge=0, le=100, description="Score des personnes/sujets")
    sharpness_score: float = Field(..., ge=0, le=100, description="Score de netteté")
    technical_issues: List[str] = Field(default_factory=list, description="Problèmes techniques détectés")
    description: str = Field(default="", description="Description de l'image")
    is_duplicate: bool = Field(default=False, description="Indique si c'est un doublon")
    duplicate_of: Optional[str] = Field(default=None, description="Fichier dont c'est un doublon")
    selected: bool = Field(default=False, description="Indique si la photo est sélectionnée")


class SortRequest(BaseModel):
    """Requête de tri de photos"""
    photos_directory: str = Field(..., description="Chemin du dossier contenant les photos")
    output_directory: str = Field(..., description="Chemin du dossier de sortie")
    selection_percentage: float = Field(default=30.0, ge=1, le=100, description="Pourcentage de photos à conserver")
    min_quality_score: float = Field(default=70.0, ge=0, le=100, description="Score minimum requis")
    duplicate_threshold: float = Field(default=0.95, ge=0, le=1, description="Seuil de similarité pour doublons")
    batch_size: int = Field(default=10, ge=1, le=50, description="Taille des lots de traitement")
    copy_files: bool = Field(default=True, description="Copier les fichiers ou juste créer un rapport")


class SortResponse(BaseModel):
    """Réponse de tri de photos"""
    success: bool
    message: str
    task_id: Optional[str] = None
    job_id: Optional[str] = None


class JobStatus(BaseModel):
    """Statut d'un job de tri"""
    job_id: str
    status: str = Field(..., description="pending, processing, completed, failed")
    progress: float = Field(default=0.0, ge=0, le=100, description="Progression en %")
    total_photos: int = Field(default=0)
    processed_photos: int = Field(default=0)
    selected_photos: int = Field(default=0)
    duplicates_removed: int = Field(default=0)
    average_quality_score: float = Field(default=0.0)
    processing_time: float = Field(default=0.0, description="Temps en secondes")
    report_path: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class PhotoReport(BaseModel):
    """Rapport détaillé pour une photo"""
    file_name: str
    quality_score: float
    composition_score: float
    lighting_score: float
    background_score: float
    subject_score: float
    sharpness_score: float
    selected: bool
    is_duplicate: bool
    duplicate_of: Optional[str] = None
    technical_issues: List[str] = []
    description: str = ""


class SortingReport(BaseModel):
    """Rapport complet de tri"""
    job_id: str
    total_photos: int
    selected_photos: int
    duplicates_removed: int
    average_quality_score: float
    processing_time: float
    photos: List[PhotoReport]
    generated_at: datetime
