"""
MongoDB Schemas for StrideMatch User Profiles (Pydantic validation).

This module defines the data structure for user profiles stored in MongoDB,
including demographics, biomechanics, goals, and preferences.

Architecture Decision:
- PostgreSQL → Product catalog (see models.py)
- MongoDB → User profiles (this file) - Flexible schema for evolving user data
- Neo4j → Recommendation graph (see neo4j_init.cypher)

MongoDB Collections:
1. users - Complete user profiles with biomechanical data
2. gait_analyses - Historical gait analysis results (migrated from PostgreSQL)
3. foot_scans - Historical 3D foot scans (migrated from PostgreSQL)
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


# ============================================================================
# ENUMS - Biomechanical Classifications
# ============================================================================

class FootStrike(str, Enum):
    """Foot strike pattern classification."""
    HEEL_STRIKE = "heel_strike"
    MIDFOOT_STRIKE = "midfoot_strike"
    FOREFOOT_STRIKE = "forefoot_strike"
    UNKNOWN = "unknown"


class PronationType(str, Enum):
    """Pronation type classification."""
    NEUTRAL = "neutral"
    OVERPRONATION = "overpronation"
    UNDERPRONATION = "underpronation"  # Also called "supination"
    UNKNOWN = "unknown"


class ArchType(str, Enum):
    """Foot arch type classification."""
    FLAT = "flat"
    NORMAL = "normal"
    HIGH = "high"
    UNKNOWN = "unknown"


class TerrainType(str, Enum):
    """Primary running terrain."""
    ROAD = "road"
    TRAIL = "trail"
    TRACK = "track"
    MIXED = "mixed"
    TREADMILL = "treadmill"


class RunningLevel(str, Enum):
    """Running experience level."""
    BEGINNER = "beginner"  # < 1 year
    INTERMEDIATE = "intermediate"  # 1-3 years
    ADVANCED = "advanced"  # 3-5 years
    EXPERT = "expert"  # 5+ years


# ============================================================================
# SUB-SCHEMAS - Nested Documents
# ============================================================================

class Demographics(BaseModel):
    """User demographic information."""
    age: Optional[int] = Field(None, ge=13, le=120, description="Age in years")
    weight_kg: Optional[float] = Field(None, ge=30, le=300, description="Weight in kilograms")
    height_cm: Optional[float] = Field(None, ge=120, le=250, description="Height in centimeters")
    gender: Optional[str] = Field(None, description="Gender (male/female/other)")

    # Location (for recommendations, weather, terrain suggestions)
    country: Optional[str] = Field(None, max_length=2, description="ISO country code")
    city: Optional[str] = Field(None, max_length=100, description="City name")

    class Config:
        json_schema_extra = {
            "example": {
                "age": 35,
                "weight_kg": 75.0,
                "height_cm": 175.0,
                "gender": "male",
                "country": "FR",
                "city": "Annecy"
            }
        }


class RunningGoals(BaseModel):
    """User running goals and activity level."""
    primary_terrain: TerrainType = Field(default=TerrainType.ROAD, description="Primary running terrain")
    weekly_km: Optional[float] = Field(None, ge=0, le=500, description="Average weekly distance in km")
    weekly_sessions: Optional[int] = Field(None, ge=0, le=21, description="Number of runs per week")

    # Experience
    running_level: RunningLevel = Field(default=RunningLevel.BEGINNER, description="Running experience level")
    running_experience_years: Optional[float] = Field(None, ge=0, le=80, description="Years of running experience")

    # Goals
    target_distance: Optional[str] = Field(None, description="Target race distance (e.g., '10K', 'Half Marathon', 'Marathon')")
    target_pace_min_per_km: Optional[float] = Field(None, ge=3, le=12, description="Target pace in min/km")

    # Preferences
    prefers_cushioning: Optional[str] = Field(None, description="Cushioning preference: 'soft', 'balanced', 'responsive'")
    prefers_lightweight: Optional[bool] = Field(None, description="Prefers lightweight shoes")

    class Config:
        json_schema_extra = {
            "example": {
                "primary_terrain": "road",
                "weekly_km": 40.0,
                "weekly_sessions": 4,
                "running_level": "intermediate",
                "running_experience_years": 2.5,
                "target_distance": "Half Marathon",
                "target_pace_min_per_km": 5.5,
                "prefers_cushioning": "balanced",
                "prefers_lightweight": False
            }
        }


class BiomechanicalProfile(BaseModel):
    """
    Biomechanical profile from gait analysis (POC 1 output).

    This data comes from MediaPipe video analysis and is the KEY to solving
    the cold start problem in recommendations.
    """
    # Gait characteristics
    foot_strike: FootStrike = Field(default=FootStrike.UNKNOWN, description="Foot strike pattern")
    pronation_type: PronationType = Field(default=PronationType.UNKNOWN, description="Pronation type")

    # Joint angles (average from multiple analyses)
    avg_knee_angle_deg: Optional[float] = Field(None, ge=90, le=180, description="Average knee angle at contact (degrees)")
    avg_ankle_angle_deg: Optional[float] = Field(None, ge=60, le=120, description="Average ankle angle at contact (degrees)")
    avg_hip_angle_deg: Optional[float] = Field(None, ge=140, le=200, description="Average hip angle (degrees)")

    # Cadence and stride
    avg_cadence_spm: Optional[int] = Field(None, ge=120, le=220, description="Average cadence (steps per minute)")
    avg_stride_length_cm: Optional[float] = Field(None, ge=50, le=250, description="Average stride length (cm)")
    avg_contact_time_ms: Optional[float] = Field(None, ge=100, le=500, description="Average ground contact time (ms)")

    # Confidence metrics
    confidence_foot_strike: Optional[float] = Field(None, ge=0, le=100, description="Confidence in foot strike classification (%)")
    confidence_pronation: Optional[float] = Field(None, ge=0, le=100, description="Confidence in pronation classification (%)")

    # Analysis metadata
    total_analyses: int = Field(default=0, ge=0, description="Number of gait analyses performed")
    last_analysis_date: Optional[datetime] = Field(None, description="Date of last gait analysis")

    class Config:
        json_schema_extra = {
            "example": {
                "foot_strike": "heel_strike",
                "pronation_type": "overpronation",
                "avg_knee_angle_deg": 145.2,
                "avg_ankle_angle_deg": 92.3,
                "avg_hip_angle_deg": 170.5,
                "avg_cadence_spm": 172,
                "avg_stride_length_cm": 115.0,
                "avg_contact_time_ms": 245.0,
                "confidence_foot_strike": 87.5,
                "confidence_pronation": 82.0,
                "total_analyses": 3,
                "last_analysis_date": "2025-01-15T10:30:00Z"
            }
        }


class FootMorphology(BaseModel):
    """
    Foot morphology from 3D scan (POC 2+ feature).

    This data comes from smartphone photogrammetry (future implementation).
    """
    # Measurements (in cm)
    length_cm: Optional[float] = Field(None, ge=18, le=35, description="Foot length in cm")
    width_forefoot_cm: Optional[float] = Field(None, ge=6, le=15, description="Forefoot width in cm")
    width_heel_cm: Optional[float] = Field(None, ge=5, le=12, description="Heel width in cm")
    arch_height_cm: Optional[float] = Field(None, ge=0, le=8, description="Arch height in cm")

    # Classifications
    arch_type: ArchType = Field(default=ArchType.UNKNOWN, description="Arch type")
    foot_type: Optional[str] = Field(None, description="Foot shape type: 'egyptian', 'roman', 'greek'")

    # Scan metadata
    scan_date: Optional[datetime] = Field(None, description="Date of foot scan")
    scan_quality: Optional[float] = Field(None, ge=0, le=100, description="Scan quality score (0-100%)")

    class Config:
        json_schema_extra = {
            "example": {
                "length_cm": 26.5,
                "width_forefoot_cm": 10.2,
                "width_heel_cm": 7.8,
                "arch_height_cm": 3.5,
                "arch_type": "normal",
                "foot_type": "egyptian",
                "scan_date": "2025-01-10T14:00:00Z",
                "scan_quality": 92.0
            }
        }


class InjuryHistory(BaseModel):
    """User injury history (for recommendations and risk prevention)."""
    has_injury_history: bool = Field(default=False, description="Has previous running injuries")

    # Common running injuries
    plantar_fasciitis: bool = Field(default=False, description="History of plantar fasciitis")
    achilles_tendinitis: bool = Field(default=False, description="History of Achilles tendinitis")
    shin_splints: bool = Field(default=False, description="History of shin splints")
    knee_pain: bool = Field(default=False, description="History of knee pain (runner's knee, etc.)")
    stress_fractures: bool = Field(default=False, description="History of stress fractures")

    # Free text for other injuries
    other_injuries: Optional[str] = Field(None, max_length=500, description="Other injuries or conditions")

    # Current status
    currently_injured: bool = Field(default=False, description="Currently has an active injury")
    recovery_notes: Optional[str] = Field(None, max_length=500, description="Recovery notes")

    class Config:
        json_schema_extra = {
            "example": {
                "has_injury_history": True,
                "plantar_fasciitis": False,
                "achilles_tendinitis": True,
                "shin_splints": False,
                "knee_pain": True,
                "stress_fractures": False,
                "other_injuries": "Minor hip discomfort during long runs",
                "currently_injured": False,
                "recovery_notes": "Fully recovered after 3 months of PT"
            }
        }


class ShoePreferences(BaseModel):
    """User preferences for shoe features (style, brands, price)."""
    # Budget
    max_price_eur: Optional[float] = Field(None, ge=50, le=500, description="Maximum price willing to pay (EUR)")

    # Brand preferences
    preferred_brands: List[str] = Field(default_factory=list, description="List of preferred brands")
    excluded_brands: List[str] = Field(default_factory=list, description="List of brands to exclude")

    # Style preferences
    preferred_colors: List[str] = Field(default_factory=list, description="Preferred colors")
    prefers_minimalist: Optional[bool] = Field(None, description="Prefers minimalist/barefoot shoes")
    prefers_vegan: Optional[bool] = Field(None, description="Prefers vegan materials")

    # Fit preferences
    prefers_wide_fit: Optional[bool] = Field(None, description="Prefers wide fit shoes")
    prefers_cushioned_collar: Optional[bool] = Field(None, description="Prefers cushioned collar/heel")

    class Config:
        json_schema_extra = {
            "example": {
                "max_price_eur": 150.0,
                "preferred_brands": ["Nike", "Hoka", "Asics"],
                "excluded_brands": ["Adidas"],
                "preferred_colors": ["black", "blue", "gray"],
                "prefers_minimalist": False,
                "prefers_vegan": True,
                "prefers_wide_fit": False,
                "prefers_cushioned_collar": True
            }
        }


class HealthData(BaseModel):
    """
    Health data from HealthKit (iOS) or Health Connect (Android).

    Collected with user consent for personalized recommendations.
    """
    # Activity data
    avg_daily_steps: Optional[int] = Field(None, ge=0, le=100000, description="Average daily steps")
    avg_weekly_active_minutes: Optional[int] = Field(None, ge=0, le=10080, description="Average weekly active minutes")

    # Running metrics (from wearables)
    avg_heart_rate_bpm: Optional[int] = Field(None, ge=40, le=220, description="Average running heart rate (bpm)")
    vo2_max: Optional[float] = Field(None, ge=20, le=85, description="VO2 max (ml/kg/min)")

    # Data sync
    healthkit_connected: bool = Field(default=False, description="HealthKit sync enabled (iOS)")
    health_connect_connected: bool = Field(default=False, description="Health Connect sync enabled (Android)")
    last_sync_date: Optional[datetime] = Field(None, description="Last health data sync")

    class Config:
        json_schema_extra = {
            "example": {
                "avg_daily_steps": 8500,
                "avg_weekly_active_minutes": 240,
                "avg_heart_rate_bpm": 155,
                "vo2_max": 48.5,
                "healthkit_connected": True,
                "health_connect_connected": False,
                "last_sync_date": "2025-01-15T08:00:00Z"
            }
        }


# ============================================================================
# MAIN SCHEMA - User Profile (MongoDB Document)
# ============================================================================

class UserProfile(BaseModel):
    """
    Complete user profile stored in MongoDB.

    This is the main document structure for the 'users' collection.
    MongoDB ObjectId is stored as _id (auto-generated).
    """
    # User identification
    user_id: int = Field(..., description="User ID from PostgreSQL users table (for cross-DB joins)")
    tenant_id: int = Field(..., description="Tenant ID for multi-tenancy")

    # Contact
    email: str = Field(..., max_length=255, description="User email (unique)")

    # Nested profiles
    demographics: Demographics = Field(default_factory=Demographics, description="Demographic information")
    goals: RunningGoals = Field(default_factory=RunningGoals, description="Running goals and activity")
    biomechanics: BiomechanicalProfile = Field(default_factory=BiomechanicalProfile, description="Biomechanical profile (POC 1)")
    foot_morphology: FootMorphology = Field(default_factory=FootMorphology, description="Foot morphology (POC 2+)")
    injury_history: InjuryHistory = Field(default_factory=InjuryHistory, description="Injury history")
    preferences: ShoePreferences = Field(default_factory=ShoePreferences, description="Shoe preferences")
    health_data: HealthData = Field(default_factory=HealthData, description="Health data sync")

    # Recommendation cache (updated by recommendation engine)
    recommended_product_ids: List[str] = Field(default_factory=list, description="Cached recommended product UUIDs")
    recommendations_updated_at: Optional[datetime] = Field(None, description="Last recommendations update")

    # Metadata
    profile_completeness: float = Field(default=0.0, ge=0, le=100, description="Profile completeness score (0-100%)")
    onboarding_completed: bool = Field(default=False, description="Has completed onboarding flow")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Profile creation date")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last profile update")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 42,
                "tenant_id": 1,
                "email": "john.doe@example.com",
                "demographics": {
                    "age": 35,
                    "weight_kg": 75.0,
                    "height_cm": 175.0,
                    "gender": "male",
                    "country": "FR",
                    "city": "Annecy"
                },
                "goals": {
                    "primary_terrain": "road",
                    "weekly_km": 40.0,
                    "weekly_sessions": 4,
                    "running_level": "intermediate",
                    "running_experience_years": 2.5
                },
                "biomechanics": {
                    "foot_strike": "heel_strike",
                    "pronation_type": "overpronation",
                    "avg_cadence_spm": 172
                },
                "profile_completeness": 75.0,
                "onboarding_completed": True,
                "created_at": "2025-01-10T10:00:00Z",
                "updated_at": "2025-01-15T14:30:00Z"
            }
        }


# ============================================================================
# GAIT ANALYSIS HISTORY (Migrated from PostgreSQL)
# ============================================================================

class GaitAnalysisDocument(BaseModel):
    """
    Historical gait analysis result (migrated from PostgreSQL GaitAnalysis model).

    Stored in MongoDB 'gait_analyses' collection for flexible schema.
    """
    # IDs
    analysis_id: UUID = Field(..., description="Unique analysis ID")
    user_id: int = Field(..., description="User ID")
    tenant_id: int = Field(..., description="Tenant ID")

    # Video metadata
    video_filename: Optional[str] = Field(None, description="Original video filename")
    video_duration_sec: Optional[float] = Field(None, description="Video duration")

    # Analysis results
    gait_type: str = Field(..., description="Detected gait type")
    confidence_score: Optional[float] = Field(None, ge=0, le=100, description="Confidence score")

    # Biomechanical data
    angles: Dict[str, float] = Field(default_factory=dict, description="Joint angles (knee, ankle, hip)")
    cadence: Optional[int] = Field(None, description="Cadence (steps/min)")
    contact_time_ms: Optional[float] = Field(None, description="Ground contact time")

    # Performance
    avg_latency_ms: Optional[float] = Field(None, description="Processing latency")
    frame_count: Optional[int] = Field(None, description="Total frames")

    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Analysis date")

    class Config:
        json_schema_extra = {
            "example": {
                "analysis_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": 42,
                "tenant_id": 1,
                "video_filename": "running_video.mp4",
                "video_duration_sec": 10.5,
                "gait_type": "heel_strike",
                "confidence_score": 87.5,
                "angles": {
                    "knee": 145.2,
                    "ankle": 92.3,
                    "hip": 170.5
                },
                "cadence": 172,
                "contact_time_ms": 245.0,
                "avg_latency_ms": 85.3,
                "frame_count": 315,
                "created_at": "2025-01-15T10:30:00Z"
            }
        }


# ============================================================================
# FOOT SCAN HISTORY (Migrated from PostgreSQL)
# ============================================================================

class FootScanDocument(BaseModel):
    """
    Historical 3D foot scan (migrated from PostgreSQL FootScan model).

    Stored in MongoDB 'foot_scans' collection.
    """
    # IDs
    scan_id: UUID = Field(..., description="Unique scan ID")
    user_id: int = Field(..., description="User ID")
    tenant_id: int = Field(..., description="Tenant ID")

    # Scan metadata
    scan_type: str = Field(default="photo", description="Scan type: photo, depth_sensor, lidar")
    images_count: Optional[int] = Field(None, description="Number of images used")

    # Measurements
    length_cm: Optional[float] = Field(None, description="Foot length (cm)")
    width_forefoot_cm: Optional[float] = Field(None, description="Forefoot width (cm)")
    arch_height_cm: Optional[float] = Field(None, description="Arch height (cm)")

    # Classification
    arch_type: Optional[str] = Field(None, description="Arch type: flat, normal, high")
    foot_type: Optional[str] = Field(None, description="Foot type: egyptian, roman, greek")

    # Quality
    reconstruction_quality: Optional[float] = Field(None, ge=0, le=100, description="Reconstruction quality (0-100%)")

    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Scan date")

    class Config:
        json_schema_extra = {
            "example": {
                "scan_id": "987e6543-e21b-12d3-a456-426614174111",
                "user_id": 42,
                "tenant_id": 1,
                "scan_type": "photo",
                "images_count": 12,
                "length_cm": 26.5,
                "width_forefoot_cm": 10.2,
                "arch_height_cm": 3.5,
                "arch_type": "normal",
                "foot_type": "egyptian",
                "reconstruction_quality": 92.0,
                "created_at": "2025-01-10T14:00:00Z"
            }
        }


# ============================================================================
# MONGODB COLLECTION NAMES (Constants)
# ============================================================================

COLLECTION_USERS = "users"
COLLECTION_GAIT_ANALYSES = "gait_analyses"
COLLECTION_FOOT_SCANS = "foot_scans"


# ============================================================================
# MONGODB INDEXES (To be created in init script)
# ============================================================================

"""
MongoDB Indexes to Create:

1. users collection:
   - { "user_id": 1, "tenant_id": 1 } (unique)
   - { "email": 1 } (unique)
   - { "tenant_id": 1, "biomechanics.foot_strike": 1 }
   - { "tenant_id": 1, "biomechanics.pronation_type": 1 }
   - { "tenant_id": 1, "demographics.age": 1 }

2. gait_analyses collection:
   - { "user_id": 1, "created_at": -1 }
   - { "tenant_id": 1, "created_at": -1 }
   - { "analysis_id": 1 } (unique)

3. foot_scans collection:
   - { "user_id": 1, "created_at": -1 }
   - { "tenant_id": 1, "created_at": -1 }
   - { "scan_id": 1 } (unique)
"""
