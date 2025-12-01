"""
Pydantic schemas for StrideMatch API validation.

These schemas define the structure of request and response data
for the gait analysis endpoints.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from enum import Enum


class AnalysisMode(str, Enum):
    """Analysis mode enum."""
    QUICK = "quick"
    DETAILED = "detailed"
    PROFESSIONAL = "professional"


class GaitType(str, Enum):
    """Gait type classification."""
    HEEL_STRIKE = "heel_strike"
    MIDFOOT_STRIKE = "midfoot_strike"
    FOREFOOT_STRIKE = "forefoot_strike"
    UNKNOWN = "unknown"


class ArchType(str, Enum):
    """Foot arch type classification."""
    FLAT = "flat"
    NORMAL = "normal"
    HIGH = "high"


class PronationType(str, Enum):
    """Pronation type classification."""
    NEUTRAL = "neutral"
    OVERPRONATION = "overpronation"
    UNDERPRONATION = "underpronation"


# ============================================================================
# Request Schemas
# ============================================================================

class GaitAnalysisRequest(BaseModel):
    """Request schema for gait analysis creation."""

    runner_name: Optional[str] = Field(None, description="Optional runner name")
    analysis_mode: AnalysisMode = Field(
        default=AnalysisMode.QUICK,
        description="Analysis mode: quick, detailed, or professional"
    )
    save_annotated_video: bool = Field(
        default=False,
        description="Whether to save the annotated video with skeleton overlay"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "runner_name": "John Doe",
                "analysis_mode": "detailed",
                "save_annotated_video": True
            }
        }


class BiomechanicalAngles(BaseModel):
    """Biomechanical joint angles."""

    knee: Optional[float] = Field(None, description="Knee angle in degrees")
    ankle: Optional[float] = Field(None, description="Ankle angle in degrees")
    hip: Optional[float] = Field(None, description="Hip angle in degrees")

    class Config:
        json_schema_extra = {
            "example": {
                "knee": 145.2,
                "ankle": 92.3,
                "hip": 170.5
            }
        }


# ============================================================================
# Response Schemas
# ============================================================================

class GaitAnalysisResponse(BaseModel):
    """Response schema for gait analysis results."""

    # Identifiers
    analysis_id: UUID = Field(..., description="Unique analysis ID")
    tenant_id: int = Field(..., description="Tenant ID")
    user_id: Optional[int] = Field(None, description="User ID if authenticated")

    # Metadata
    runner_name: Optional[str] = Field(None, description="Runner name")
    analysis_mode: str = Field(..., description="Analysis mode used")

    # Video info
    video_filename: Optional[str] = Field(None, description="Original video filename")
    video_duration_sec: Optional[float] = Field(None, description="Video duration in seconds")

    # Analysis results
    gait_type: Optional[str] = Field(None, description="Detected gait type")
    confidence_score: Optional[float] = Field(None, description="Confidence score (0-100)")
    angles: Optional[Dict[str, float]] = Field(None, description="Joint angles in degrees")

    # Performance metrics
    avg_latency_ms: Optional[float] = Field(None, description="Average processing latency per frame")
    frame_count: Optional[int] = Field(None, description="Total frames processed")
    frames_with_detection: Optional[int] = Field(None, description="Frames with successful detection")
    landmarks_detected: bool = Field(..., description="Whether landmarks were detected")

    # Additional metrics
    stride_frequency: Optional[float] = Field(None, description="Cadence (steps/min)")
    contact_time_ms: Optional[float] = Field(None, description="Ground contact time")

    # Output files
    annotated_video_url: Optional[str] = Field(None, description="URL to annotated video")

    # Timestamps
    created_at: datetime = Field(..., description="Analysis creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "analysis_id": "123e4567-e89b-12d3-a456-426614174000",
                "tenant_id": 1,
                "user_id": 42,
                "runner_name": "John Doe",
                "analysis_mode": "detailed",
                "video_filename": "running_video.mp4",
                "video_duration_sec": 10.5,
                "gait_type": "heel_strike",
                "confidence_score": 87.5,
                "angles": {
                    "knee": 145.2,
                    "ankle": 92.3,
                    "hip": 170.5
                },
                "avg_latency_ms": 85.3,
                "frame_count": 315,
                "frames_with_detection": 312,
                "landmarks_detected": True,
                "stride_frequency": 172.0,
                "contact_time_ms": 245.0,
                "annotated_video_url": "/static/analyses/123e4567_annotated.mp4",
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": None
            }
        }


class GaitAnalysisListResponse(BaseModel):
    """Response schema for list of analyses."""

    total: int = Field(..., description="Total number of analyses")
    analyses: List[GaitAnalysisResponse] = Field(..., description="List of analyses")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 2,
                "analyses": [
                    # ... (same structure as GaitAnalysisResponse)
                ]
            }
        }


class BiomechanicalProfileResponse(BaseModel):
    """Response schema for biomechanical profile."""

    # Identifiers
    profile_id: UUID = Field(..., description="Profile ID")
    user_id: int = Field(..., description="User ID")
    tenant_id: int = Field(..., description="Tenant ID")

    # Gait characteristics
    primary_gait_type: Optional[str] = Field(None, description="Most common gait type")
    avg_cadence: Optional[float] = Field(None, description="Average cadence (steps/min)")
    avg_contact_time_ms: Optional[float] = Field(None, description="Average ground contact time")

    # Biomechanical angles
    avg_knee_angle: Optional[float] = Field(None, description="Average knee angle")
    avg_ankle_angle: Optional[float] = Field(None, description="Average ankle angle")
    avg_hip_angle: Optional[float] = Field(None, description="Average hip angle")

    # Foot morphology
    foot_length_cm: Optional[float] = Field(None, description="Foot length in cm")
    foot_width_cm: Optional[float] = Field(None, description="Foot width in cm")
    arch_type: Optional[str] = Field(None, description="Arch type classification")
    pronation_type: Optional[str] = Field(None, description="Pronation type")

    # Activity data
    weekly_mileage_km: Optional[float] = Field(None, description="Average weekly mileage")
    running_experience_years: Optional[float] = Field(None, description="Years of running experience")

    # Statistics
    total_analyses: int = Field(..., description="Number of analyses performed")
    last_analysis_at: Optional[datetime] = Field(None, description="Last analysis timestamp")

    # Timestamps
    created_at: datetime = Field(..., description="Profile creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True


class AnalysisStatsResponse(BaseModel):
    """Response schema for analysis statistics."""

    total_analyses: int = Field(..., description="Total number of analyses")
    avg_latency_ms: float = Field(..., description="Average processing latency")
    success_rate: float = Field(..., description="Success rate (0-100%)")
    most_common_gait_type: Optional[str] = Field(None, description="Most common gait type detected")

    class Config:
        json_schema_extra = {
            "example": {
                "total_analyses": 150,
                "avg_latency_ms": 82.5,
                "success_rate": 94.7,
                "most_common_gait_type": "heel_strike"
            }
        }


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "VideoProcessingError",
                "message": "Failed to detect landmarks in video",
                "details": {
                    "video_duration": 5.2,
                    "frames_processed": 156,
                    "frames_with_detection": 0
                }
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(..., description="Service status")
    mediapipe_available: bool = Field(..., description="MediaPipe availability")
    opencv_available: bool = Field(..., description="OpenCV availability")
    version: str = Field(..., description="Pack version")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "mediapipe_available": True,
                "opencv_available": True,
                "version": "0.1.0"
            }
        }
