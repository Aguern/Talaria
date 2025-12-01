"""
SQLAlchemy models for StrideMatch Knowledge Core (Product Catalog).

This module contains the relational database schema for the shoe product catalog,
including brands, sizing normalization, product specifications, and enrichment tags.

Architecture Decision:
- Product catalog → PostgreSQL (this file)
- User profiles (biomechanics, demographics) → MongoDB (see database/mongodb_schemas.py)
- Recommendation graph → Neo4j (see database/neo4j_init.cypher)
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey,
    DateTime, Text, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


# ============================================================================
# ENUMS - Product Attributes
# ============================================================================

class Gender(str, enum.Enum):
    """Gender for sizing and product categorization."""
    MALE = "male"
    FEMALE = "female"
    UNISEX = "unisex"


class ProductCategory(str, enum.Enum):
    """Primary product category."""
    RUNNING_ROAD = "running_road"
    RUNNING_TRAIL = "running_trail"
    RUNNING_TRACK = "running_track"
    WALKING = "walking"
    TRAINING = "training"
    OTHER = "other"


class StabilityType(str, enum.Enum):
    """Stability classification (normalized StrideMatch scale)."""
    NEUTRAL = "neutral"
    STABILITY_MILD = "stability_mild"
    STABILITY_HIGH = "stability_high"
    MOTION_CONTROL = "motion_control"


class CushioningLevel(str, enum.Enum):
    """Cushioning level (normalized StrideMatch scale)."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


class DropCategory(str, enum.Enum):
    """Drop category (normalized StrideMatch scale)."""
    ZERO = "zero"  # 0mm
    LOW = "low"  # 1-4mm
    MEDIUM = "medium"  # 5-8mm
    HIGH = "high"  # 9mm+


# ============================================================================
# BRANDS - Marques de Chaussures
# ============================================================================

class Brand(Base):
    """
    Shoe brands (Nike, Adidas, Hoka, etc.).

    This is a GLOBAL table (no tenant_id) as brands are shared across all users.
    """
    __tablename__ = "stridematch_brands"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Brand information
    name = Column(String(100), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)  # URL-friendly name

    # Metadata
    logo_url = Column(String, nullable=True)
    website_url = Column(String, nullable=True)
    country_origin = Column(String(2), nullable=True)  # ISO country code

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    products = relationship("Product", back_populates="brand")
    sizing_tables = relationship("SizingNormalization", back_populates="brand")

    def __repr__(self):
        return f"<Brand(id={self.id}, name={self.name})>"


# ============================================================================
# SIZING NORMALIZATION - Traduction des Pointures
# ============================================================================

class SizingNormalization(Base):
    """
    Sizing normalization table: Maps native brand sizes (EU/US/UK) to standard CM.

    Critical for solving "42 Nike ≠ 42 Adidas" problem.
    This is a GLOBAL table (no tenant_id).

    Example:
        (Nike, Male, EU:42, US:8.5, UK:7.5, CM:26.5)
        (Adidas, Male, EU:42, US:9, UK:8, CM:26.0)
    """
    __tablename__ = "stridematch_sizing_normalization"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key to Brand
    brand_id = Column(Integer, ForeignKey("stridematch_brands.id"), nullable=False, index=True)
    brand = relationship("Brand", back_populates="sizing_tables")

    # Gender
    gender = Column(SQLEnum(Gender), nullable=False, index=True)

    # Native sizes (as displayed by brand)
    size_eu = Column(String(10), nullable=True)  # European (e.g., "42", "42.5")
    size_us = Column(String(10), nullable=True)  # US (e.g., "8.5", "9")
    size_uk = Column(String(10), nullable=True)  # UK (e.g., "7.5", "8")

    # Normalized size in centimeters (SOURCE OF TRUTH)
    size_cm = Column(Float, nullable=False, index=True)  # e.g., 26.5

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        # Ensure uniqueness: one row per (brand, gender, size_cm)
        UniqueConstraint('brand_id', 'gender', 'size_cm', name='uq_brand_gender_size_cm'),
        # Index for fast lookups
        Index('ix_sizing_lookup', 'brand_id', 'gender', 'size_eu'),
    )

    def __repr__(self):
        return f"<SizingNormalization(brand={self.brand.name if self.brand else None}, gender={self.gender}, EU:{self.size_eu}, CM:{self.size_cm})>"


# ============================================================================
# PRODUCTS - Modèles de Chaussures
# ============================================================================

class Product(Base):
    """
    Product model (e.g., "Nike Pegasus 40", "Hoka Clifton 9").

    A Product represents a shoe model. It can have multiple ProductVariants
    (different colors, sizes).

    This is a GLOBAL table (no tenant_id).
    """
    __tablename__ = "stridematch_products"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Foreign key to Brand
    brand_id = Column(Integer, ForeignKey("stridematch_brands.id"), nullable=False, index=True)
    brand = relationship("Brand", back_populates="products")

    # Product information
    model_name = Column(String(200), nullable=False, index=True)  # e.g., "Pegasus 40"
    full_name = Column(String(300), nullable=True)  # e.g., "Nike Air Zoom Pegasus 40"

    # Category
    primary_category = Column(SQLEnum(ProductCategory), nullable=False, index=True)
    gender = Column(SQLEnum(Gender), nullable=False, index=True)

    # Description
    description = Column(Text, nullable=True)

    # Release info
    release_year = Column(Integer, nullable=True, index=True)
    is_active = Column(Boolean, default=True, index=True)  # Still in production?

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    lab_specs = relationship("ProductSpecs_Lab", back_populates="product", uselist=False, cascade="all, delete-orphan")
    marketing_specs = relationship("ProductSpecs_Marketing", back_populates="product", uselist=False, cascade="all, delete-orphan")
    tags = relationship("Enrichment_Tag", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        # Composite index for fast brand+model lookups
        Index('ix_product_brand_model', 'brand_id', 'model_name'),
    )

    def __repr__(self):
        return f"<Product(id={self.id}, brand={self.brand.name if self.brand else None}, model={self.model_name})>"


# ============================================================================
# PRODUCT VARIANTS - Variantes (Couleur, Taille, Prix)
# ============================================================================

class ProductVariant(Base):
    """
    Product Variant: Represents a specific SKU (color + size combination).

    Example: "Nike Pegasus 40, Blue, Size 42" is one variant.

    This table stores e-commerce data: color, size, price, image, source URL.
    This is a GLOBAL table (no tenant_id).
    """
    __tablename__ = "stridematch_product_variants"

    # Primary key (SKU = Stock Keeping Unit)
    sku = Column(String(100), primary_key=True, index=True)

    # Foreign key to Product
    product_id = Column(UUID(as_uuid=True), ForeignKey("stridematch_products.id"), nullable=False, index=True)
    product = relationship("Product", back_populates="variants")

    # Variant attributes
    color = Column(String(100), nullable=True, index=True)
    color_hex = Column(String(7), nullable=True)  # Hex code (e.g., "#FF5733")
    size_native = Column(String(10), nullable=True, index=True)  # Native size (e.g., "42", "9 US")

    # E-commerce data
    source_url = Column(String, nullable=True)  # Product page URL
    source_site = Column(String(100), nullable=True, index=True)  # e.g., "i-run.fr"
    price_eur = Column(Float, nullable=True)  # Current price in EUR
    price_updated_at = Column(DateTime(timezone=True), nullable=True)

    # Media
    image_url = Column(String, nullable=True)

    # Availability
    is_available = Column(Boolean, default=True, index=True)
    stock_status = Column(String(50), nullable=True)  # "in_stock", "low_stock", "out_of_stock"

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index('ix_variant_product_color', 'product_id', 'color'),
    )

    def __repr__(self):
        return f"<ProductVariant(sku={self.sku}, product={self.product.model_name if self.product else None}, color={self.color})>"


# ============================================================================
# PRODUCT SPECS - Lab (Données Techniques Objectives)
# ============================================================================

class ProductSpecs_Lab(Base):
    """
    Laboratory/Technical Specifications (objective data from lab tests).

    Source: RunRepeat, Solereview, RunningShoesGuru lab tests.
    These are FACTS, not marketing claims.

    One-to-one relationship with Product.
    This is a GLOBAL table (no tenant_id).
    """
    __tablename__ = "stridematch_product_specs_lab"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Foreign key to Product (one-to-one)
    product_id = Column(UUID(as_uuid=True), ForeignKey("stridematch_products.id"), nullable=False, unique=True, index=True)
    product = relationship("Product", back_populates="lab_specs")

    # Geometry (Critical for biomechanical matching)
    drop_mm = Column(Float, nullable=True, index=True)  # Heel-to-toe drop in mm (e.g., 8.0)
    stack_heel_mm = Column(Float, nullable=True)  # Heel stack height in mm
    stack_forefoot_mm = Column(Float, nullable=True)  # Forefoot stack height in mm

    # Cushioning (Objective measurement)
    cushioning_softness_ha = Column(Float, nullable=True, index=True)  # Shore Hardness A (e.g., 11.9)
    energy_return_pct = Column(Float, nullable=True)  # Energy return percentage (e.g., 65.0)

    # Weight
    weight_g = Column(Float, nullable=True, index=True)  # Weight in grams (e.g., 285)

    # Durability
    median_lifespan_km = Column(Float, nullable=True)  # Median lifespan in km (e.g., 650)

    # Midsole Technology (Objective description)
    midsole_material = Column(String(200), nullable=True)  # e.g., "React X foam", "EVA + TPU plate"

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Data source tracking
    source_lab = Column(String(100), nullable=True)  # e.g., "RunRepeat", "Solereview"
    test_date = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<ProductSpecs_Lab(product={self.product.model_name if self.product else None}, drop={self.drop_mm}mm, weight={self.weight_g}g)>"


# ============================================================================
# PRODUCT SPECS - Marketing (Données Subjectives des Marques)
# ============================================================================

class ProductSpecs_Marketing(Base):
    """
    Marketing/Brand Specifications (subjective claims by manufacturers).

    Source: Brand websites, e-commerce product descriptions.
    These are CLAIMS, not lab-verified facts.

    One-to-one relationship with Product.
    This is a GLOBAL table (no tenant_id).
    """
    __tablename__ = "stridematch_product_specs_marketing"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Foreign key to Product (one-to-one)
    product_id = Column(UUID(as_uuid=True), ForeignKey("stridematch_products.id"), nullable=False, unique=True, index=True)
    product = relationship("Product", back_populates="marketing_specs")

    # Brand claims (raw text)
    stability_type_brand = Column(String(100), nullable=True)  # e.g., "Neutral", "Stability", "Motion Control"
    cushioning_type_brand = Column(String(100), nullable=True)  # e.g., "Soft", "Balanced", "Responsive"
    use_case_brand = Column(String(200), nullable=True)  # e.g., "Daily training", "Racing", "Long distance"

    # Normalized values (mapped to StrideMatch enum scale)
    stability_normalized = Column(SQLEnum(StabilityType), nullable=True, index=True)
    cushioning_normalized = Column(SQLEnum(CushioningLevel), nullable=True, index=True)
    drop_normalized = Column(SQLEnum(DropCategory), nullable=True, index=True)

    # Marketing description
    marketing_tagline = Column(String(500), nullable=True)  # e.g., "Fly like never before"

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ProductSpecs_Marketing(product={self.product.model_name if self.product else None}, stability={self.stability_normalized})>"


# ============================================================================
# ENRICHMENT TAGS - Tags Générés par IA (Règles Expertes)
# ============================================================================

class Enrichment_Tag(Base):
    """
    Enrichment Tags: AI-generated tags based on expert rules.

    These tags are created by the ETL pipeline (Phase 5) using the
    "Biomechanical Matching Matrix" logic.

    Examples:
        - "SUITED_FOR_HEEL_STRIKER"
        - "SUITED_FOR_OVERPRONATOR"
        - "SUITED_FOR_HEAVY_RUNNER"
        - "HIGH_DURABILITY"

    Multiple tags can be associated with one product (many-to-one).
    This is a GLOBAL table (no tenant_id).
    """
    __tablename__ = "stridematch_enrichment_tags"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key to Product
    product_id = Column(UUID(as_uuid=True), ForeignKey("stridematch_products.id"), nullable=False, index=True)
    product = relationship("Product", back_populates="tags")

    # Tag information
    tag_name = Column(String(100), nullable=False, index=True)  # e.g., "SUITED_FOR_HEEL_STRIKER"
    tag_category = Column(String(50), nullable=True, index=True)  # e.g., "biomechanics", "durability", "terrain"

    # Tag metadata
    confidence_score = Column(Float, nullable=True)  # Confidence 0-1 (if probabilistic)
    rule_source = Column(String(200), nullable=True)  # Which rule generated this tag

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        # Prevent duplicate tags for same product
        UniqueConstraint('product_id', 'tag_name', name='uq_product_tag'),
        Index('ix_tag_lookup', 'tag_name', 'tag_category'),
    )

    def __repr__(self):
        return f"<Enrichment_Tag(product={self.product.model_name if self.product else None}, tag={self.tag_name})>"


# ============================================================================
# SUMMARY
# ============================================================================

"""
Database Schema Summary (PostgreSQL):

GLOBAL TABLES (shared across all tenants):
1. stridematch_brands - Shoe brands (Nike, Adidas, etc.)
2. stridematch_sizing_normalization - Size conversion tables
3. stridematch_products - Shoe models (Pegasus 40, Clifton 9, etc.)
4. stridematch_product_variants - SKUs (color + size combinations)
5. stridematch_product_specs_lab - Lab-tested technical specs
6. stridematch_product_specs_marketing - Brand marketing claims
7. stridematch_enrichment_tags - AI-generated tags for matching

RELATIONSHIPS:
- Brand → Products (1-to-many)
- Brand → SizingNormalization (1-to-many)
- Product → ProductVariants (1-to-many)
- Product → ProductSpecs_Lab (1-to-1)
- Product → ProductSpecs_Marketing (1-to-1)
- Product → Enrichment_Tags (1-to-many)

NOTE: User profiles (biomechanics, demographics, gait analysis) are stored
in MongoDB (see database/mongodb_schemas.py) for flexibility and scalability.

NOTE: Recommendation graph (User-Product-Brand relationships) is stored
in Neo4j (see database/neo4j_init.cypher) for graph-based recommendations.
"""
