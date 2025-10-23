# Fichier: app/core/schemas.py

from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime

# Schémas pour la standardisation des recettes
class InputParameter(BaseModel):
    name: str
    description: str
    type: Literal['file', 'text', 'number', 'boolean', 'json']
    required: bool = True
    multiple: bool = False  # Pour gérer les inputs multiples (ex: plusieurs fichiers)

class OutputValue(BaseModel):
    name: str
    description: str
    type: Literal['file_pdf', 'file_csv', 'json', 'text', 'number']

class RecipeManifest(BaseModel):
    id: str
    name: str
    description: str
    version: str
    category: Optional[str] = None  # Ex: "fiscal", "legal", "administrative"
    author: Optional[str] = None
    inputs: List[InputParameter]
    outputs: List[OutputValue]
    tags: Optional[List[str]] = None  # Pour faciliter la recherche
    requirements: Optional[List[str]] = None  # Dépendances spécifiques

    class Config:
        from_attributes = True

# Schémas pour le tenant
class TenantBase(BaseModel):
    name: str

class TenantCreate(TenantBase):
    pass

class Tenant(TenantBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Schémas pour la configuration
class ConfigurationBase(BaseModel):
    key: str
    value: str  # La valeur sera manipulée en clair dans l'API
    pack_name: str

class ConfigurationCreate(ConfigurationBase):
    pass

class Configuration(ConfigurationBase):
    id: int
    tenant_id: int

    class Config:
        from_attributes = True

# Schémas pour l'authentification
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Schémas pour l'utilisateur
class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str
    tenant_name: Optional[str] = None  # Optional: create new tenant or use existing

class User(UserBase):
    id: int
    is_active: bool
    tenant_id: int
    tenant: Optional[Tenant] = None  # Include tenant info when needed

    class Config:
        from_attributes = True

# Schema for current user with tenant info
class CurrentUser(BaseModel):
    user: User
    tenant: Tenant

    class Config:
        from_attributes = True