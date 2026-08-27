from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas
from ..database import get_db
from ..auth import hash_password
from ..deps import require_admin, get_current_user
from ..audit import audit

router = APIRouter(prefix="/api/users", tags=["users"])


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
    audit(db, current_user.username, "user_create", f"Creó el usuario '{payload.username}' (rol {payload.role.value})")
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
    audit(db, current_user.username, "user_update", f"Editó el usuario '{user.username}' (id={user.id})")
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
    audit(db, current_user.username, "user_delete", f"Eliminó el usuario '{user.username}' (id={user.id})")
    db.delete(user)
    db.commit()
    return {"ok": True}
