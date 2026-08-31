from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas
from ..database import get_db
from ..auth import hash_password
from ..deps import require_admin, get_current_user
from ..audit import audit

router = APIRouter(prefix="/api/users", tags=["users"])


def _snapshot(user: models.User) -> dict:
    return {
        "username": user.username,
        "email": user.email,
        "role": user.role.value if hasattr(user.role, "value") else user.role,
        "is_active": user.is_active,
        "totp_enabled": user.totp_enabled,
    }


@router.get("", response_model=List[schemas.UserOut])
def list_users(db: Session = Depends(get_db), _: models.User = Depends(require_admin)):
    return db.query(models.User).order_by(models.User.id).all()


@router.post("", response_model=schemas.UserOut)
def create_user(
    payload: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    if db.query(models.User).filter(models.User.username == payload.username).first():
        raise HTTPException(400, "Ya existe un usuario con ese nombre")
    user = models.User(
        username=payload.username,
        email=payload.email,
        role=payload.role,
        is_active=payload.is_active,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.flush()
    audit(
        db, current_user.username, "user_create", f"Creó el usuario '{payload.username}' (rol {payload.role.value})",
        before=None, after=_snapshot(user),
    )
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=schemas.UserOut)
def update_user(
    user_id: int,
    payload: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(404, "Usuario no encontrado")

    before = _snapshot(user)

    if payload.username and payload.username != user.username:
        exists = (
            db.query(models.User)
            .filter(models.User.username == payload.username, models.User.id != user.id)
            .first()
        )
        if exists:
            raise HTTPException(400, "Ese nombre de usuario ya está en uso")
        user.username = payload.username
    if payload.email is not None:
        user.email = payload.email
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.password:
        user.hashed_password = hash_password(payload.password)

    audit(
        db, current_user.username, "user_update", f"Editó el usuario '{user.username}' (id={user.id})",
        before=before, after=_snapshot(user),
    )
    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/disable-2fa", response_model=schemas.UserOut)
def admin_disable_2fa(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    """Un admin puede desactivar el 2FA de cualquier usuario (por ejemplo, si perdió el acceso a su app)."""
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    if not user.totp_enabled:
        raise HTTPException(400, "Ese usuario no tiene el 2FA activado")

    user.totp_enabled = False
    user.totp_secret = None
    db.query(models.RecoveryCode).filter(models.RecoveryCode.user_id == user.id).delete()

    audit(
        db, current_user.username, "admin_disable_2fa",
        f"Desactivó el 2FA del usuario '{user.username}' (id={user.id})",
        before={"totp_enabled": True}, after={"totp_enabled": False},
    )
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    if user_id == current_user.id:
        raise HTTPException(400, "No puedes eliminar tu propio usuario")
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    audit(
        db, current_user.username, "user_delete", f"Eliminó el usuario '{user.username}' (id={user.id})",
        before=_snapshot(user), after=None,
    )
    db.delete(user)
    db.commit()
    return {"ok": True}
