# Fichier: app/main.py

import os
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import timedelta
import uuid
import structlog

from core import models, schemas, auth, crud
from core.database import engine, Base, get_db, is_database_configured
from core.logging_config import setup_logging

# Conditional import for Celery tasks (only in Celery mode)
# Check if CELERY_BROKER_URL exists AND is not empty
CELERY_MODE = bool(os.getenv("CELERY_BROKER_URL", "").strip())
if CELERY_MODE:
    from core import tasks as core_tasks

from packs.bofip import router as bofip_router
from packs.form_3916 import router as form_3916_router
from packs.deme_traiteur import router as deme_traiteur_router
from api import chat as chat_router
from api import recipes as recipes_router

# Configure le logging au démarrage
setup_logging()
log = structlog.get_logger()

app = FastAPI(
    title="Talaria API",
    description="Plateforme iPaaS modulaire pour l'automatisation de workflows personnalisés",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS - Configure allowed origins from environment variable for security
# In production, specify exact origins (e.g., "https://yourdomain.com,https://www.yourdomain.com")
# In development, defaults to localhost
cors_origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de logging CORRIGÉ pour propager le contexte
@app.middleware("http")
async def logging_middleware(request, call_next):
    # Nettoyer le contexte pour la nouvelle requête
    structlog.contextvars.clear_contextvars()
    
    # Générer un ID de requête unique
    request_id = str(uuid.uuid4())
    
    # Lier les informations de base au contexte pour toute la durée de la requête
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        client_host=request.client.host
    )
    
    response = await call_next(request)
    
    # Le log final inclura automatiquement le contexte + le status code
    log.info("request processed", status_code=response.status_code)
    
    return response

@app.on_event("startup")
async def on_startup():
    log.info("application starting", app_name="SaaS NR")

    # Create token.json from environment variable if provided (for Render deployment)
    import os
    if os.getenv("GOOGLE_TOKEN_JSON"):
        try:
            with open("token.json", "w") as f:
                f.write(os.getenv("GOOGLE_TOKEN_JSON"))
            log.info("token.json created from environment variable")
        except Exception as e:
            log.warning("failed to create token.json from env var", error=str(e))

    # Database initialization (only if DATABASE_URL is configured)
    # DéMé Traiteur doesn't need PostgreSQL - it uses Notion for data storage
    if is_database_configured():
        async with engine.begin() as conn:
            # On active l'extension pgvector si elle n'existe pas
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            log.info("pgvector extension enabled")

            # Créer les tables si elles n'existent pas
            await conn.run_sync(Base.metadata.create_all)
        log.info("database tables ready")
    else:
        log.info("database not configured, skipping initialization (DéMé Traiteur mode)")

    # Initialize template pool for DéMé Traiteur (critical for Render Free)
    try:
        from pathlib import Path
        import json

        pool_file = Path(__file__).parent / "packs" / "deme_traiteur" / "template_pool.json"

        # Check if pool file exists and is valid
        pool_valid = False
        if pool_file.exists():
            try:
                with open(pool_file, 'r') as f:
                    pool = json.load(f)
                    if isinstance(pool, dict) and 'available' in pool and 'in_use' in pool:
                        pool_valid = True
                        log.info("template pool file valid",
                                available=len(pool.get('available', [])),
                                in_use=len(pool.get('in_use', [])))
            except Exception as e:
                log.warning("template pool file corrupted", error=str(e))

        # Create empty pool if missing or invalid
        if not pool_valid:
            log.warning("initializing empty template pool file")
            empty_pool = {"available": [], "in_use": []}
            with open(pool_file, 'w') as f:
                json.dump(empty_pool, f, indent=2)
            log.info("template pool initialized successfully")
    except Exception as e:
        log.error("failed to initialize template pool", error=str(e))

# Inclure les routes des packs et APIs
app.include_router(bofip_router.router)
app.include_router(form_3916_router.router)
app.include_router(deme_traiteur_router.router)
app.include_router(chat_router.router, prefix="/api")
app.include_router(recipes_router.router)  # Nouvelle API des recettes

# Mount static files for DéMé Traiteur editor
static_path = Path(__file__).parent / "packs" / "deme_traiteur" / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    log.info("static files mounted", path=str(static_path))
else:
    log.warning("static directory not found", path=str(static_path))

@app.post("/users", response_model=schemas.User, status_code=status.HTTP_201_CREATED, tags=["Auth"])
async def create_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await crud.get_user_by_email(db, email=user.email)
    if db_user:
        log.warning("user registration failed", email=user.email, reason="email_already_exists")
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create or get tenant
    tenant_name = user.tenant_name or user.email.split('@')[1] if '@' in user.email else 'default'
    tenant = await crud.get_or_create_tenant(db, tenant_name)
    log.info("tenant assigned", tenant_name=tenant.name, tenant_id=tenant.id)
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(
        email=user.email, 
        hashed_password=hashed_password,
        tenant_id=tenant.id
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Load tenant relationship before returning
    await db.refresh(new_user, ['tenant'])
    log.info("user created", user_id=new_user.id, email=new_user.email, tenant_id=new_user.tenant_id)
    return new_user

@app.post("/token", response_model=schemas.Token, tags=["Auth"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await crud.get_user_by_email(db, email=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        log.warning("login failed", email=form_data.username, reason="invalid_credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    log.info("login successful", user_id=user.id, email=user.email, tenant_id=user.tenant_id)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.CurrentUser, tags=["Auth"])
async def read_users_me(current_user: schemas.CurrentUser = Depends(auth.get_current_active_user)):
    # Ce log va maintenant automatiquement contenir le request_id et les autres infos du contexte
    log.info("fetching current user details", user_email=current_user.user.email)
    return current_user

@app.post("/admin/ingest-bofip", status_code=202, tags=["Admin"])
async def trigger_bofip_ingestion(current_user: schemas.CurrentUser = Depends(auth.get_current_active_user)):
    """
    Lance la tâche de fond pour télécharger et traiter l'index du BOFIP.
    (Note: devrait être réservé aux administrateurs dans une vraie application)
    (Note: Disponible uniquement en mode Celery - pas disponible sur Render Free)
    """
    if not CELERY_MODE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cette fonctionnalité nécessite Celery et n'est pas disponible en mode Direct (Render Free)"
        )

    task = core_tasks.ingest_bofip_task.delay()
    log.info("Tâche d'ingestion BOFIP lancée par l'utilisateur.", user_email=current_user.user.email)
    return {"message": "La tâche d'ingestion du BOFIP a été lancée en arrière-plan.", "task_id": task.id}

@app.post("/test-task", status_code=202, tags=["Tasks"])
async def run_test_task(current_user: schemas.CurrentUser = Depends(auth.get_current_active_user)):
    """
    Lance une tâche de fond de test qui attend 2 secondes.
    La réponse est immédiate.
    (Note: Disponible uniquement en mode Celery - pas disponible sur Render Free)
    """
    if not CELERY_MODE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cette fonctionnalité nécessite Celery et n'est pas disponible en mode Direct (Render Free)"
        )

    task = core_tasks.debug_task.delay(1, 2)
    return {"message": "Tâche de test lancée", "task_id": task.id}

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Bienvenue sur l'API modulaire du SaaS NR !"}