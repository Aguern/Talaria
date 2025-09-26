# Fichier: app/core/models.py

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import TSVECTOR
from pgvector.sqlalchemy import Vector
from .database import Base

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship with users
    users = relationship("User", back_populates="tenant")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Foreign key to tenant
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Relationship with tenant
    tenant = relationship("Tenant", back_populates="users")

class Configuration(Base):
    __tablename__ = "configurations"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, index=True, nullable=False)
    value_encrypted = Column(String, nullable=False)
    
    pack_name = Column(String, index=True, nullable=False)  # Ex: 'ir_prefill', 'rag_bofip'
    
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    tenant = relationship("Tenant")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    bofip_id = Column(String, unique=True, index=True, nullable=False)  # Ex: BOI-IF-CFE-10-30
    title = Column(Text, nullable=False)
    document_type = Column(String, nullable=True)  # Ex: 'Commentaire', 'Barème'
    url = Column(String, nullable=True)
    publication_date = Column(DateTime(timezone=True), nullable=True)
    
    # Relation avec les chunks
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    tenant = relationship("Tenant")

class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)

    # Le vecteur de 768 dimensions (taille pour paraphrase-multilingual-mpnet-base-v2)
    embedding = Column(Vector(768))

    # Colonne pour la recherche full-text
    content_tsv = Column(TSVECTOR)

    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    document = relationship("Document", back_populates="chunks")

    # Index GIN pour la recherche full-text
    __table_args__ = (
        Index('idx_content_tsv', content_tsv, postgresql_using='gin'),
    )