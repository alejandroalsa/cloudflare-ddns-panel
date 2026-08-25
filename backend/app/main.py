import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine, SessionLocal
from . import models
from .auth import hash_password
from .config import settings
from .scheduler import start_scheduler, run_check
from .routers import auth as auth_router
from .routers import users as users_router
from .routers import zones as zones_router
from .routers import settings as settings_router
from .routers import status as status_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(title="Cloudflare DDNS Panel")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(zones_router.router)
app.include_router(settings_router.router)
app.include_router(status_router.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.query(models.User).count() == 0:
            admin = models.User(
                username=settings.admin_username,
                email=settings.admin_email,
                hashed_password=hash_password(settings.admin_password),
                role=models.UserRole.admin,
                is_active=True,
            )
            db.add(admin)
            db.commit()
            logging.info(
                f"Usuario admin inicial creado: '{settings.admin_username}' "
                f"(cambia la contraseña por defecto cuanto antes)"
            )
    finally:
        db.close()

    start_scheduler()
    # Primera comprobación inmediata al arrancar
    run_check()


@app.get("/api/health")
def health():
    return {"status": "ok"}
