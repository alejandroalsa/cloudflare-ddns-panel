from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..auth import (
    verify_password,
    create_access_token,
    hash_password,
    is_locked_out,
    register_failed_attempt,
    clear_failed_attempts,
)
from ..deps import get_current_user
from ..audit import audit
from .. import totp as totp_utils

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=schemas.LoginResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    lockout_minutes = is_locked_out(payload.username)
    if lockout_minutes is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Demasiados intentos fallidos. Inténtalo de nuevo en {lockout_minutes} minuto(s).",
        )

    user = db.query(models.User).filter(models.User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        register_failed_attempt(payload.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Usuario deshabilitado")

    if user.totp_enabled:
        if not payload.totp_code:
            return schemas.LoginResponse(totp_required=True)
        if not totp_utils.verify_totp_code(user.totp_secret, payload.totp_code):
            register_failed_attempt(payload.username)
            raise HTTPException(status_code=401, detail="Código de verificación incorrecto")

    clear_failed_attempts(payload.username)
    token = create_access_token({"sub": user.username, "role": user.role.value})
    audit(db, user.username, "login", "Inicio de sesión correcto")
    db.commit()
    return schemas.LoginResponse(access_token=token)


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=schemas.UserOut)
def update_me(
    payload: schemas.UserSelfUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if payload.username and payload.username != current_user.username:
        exists = (
            db.query(models.User)
            .filter(models.User.username == payload.username, models.User.id != current_user.id)
            .first()
        )
        if exists:
            raise HTTPException(400, "Ese nombre de usuario ya está en uso")
        current_user.username = payload.username

    if payload.email is not None:
        current_user.email = payload.email

    if payload.password:
        current_user.hashed_password = hash_password(payload.password)

    audit(db, current_user.username, "user_self_update", "El usuario actualizó su propio perfil")
    db.commit()
    db.refresh(current_user)
    return current_user


# ---------- 2FA ----------
@router.post("/2fa/setup", response_model=schemas.TwoFASetupOut)
def setup_2fa(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    secret = totp_utils.generate_secret()
    otpauth_url, qr_base64 = totp_utils.build_qr_code_base64(secret, current_user.username)
    # Guardamos el secreto pero NO activamos 2FA todavía, hasta que confirme con un código válido
    current_user.totp_secret = secret
    current_user.totp_enabled = False
    db.commit()
    return schemas.TwoFASetupOut(secret=secret, otpauth_url=otpauth_url, qr_code_base64=qr_base64)


@router.post("/2fa/confirm", response_model=schemas.UserOut)
def confirm_2fa(
    payload: schemas.TwoFAConfirmRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not current_user.totp_secret:
        raise HTTPException(400, "Primero debes iniciar la configuración de 2FA")
    if not totp_utils.verify_totp_code(current_user.totp_secret, payload.code):
        raise HTTPException(400, "Código incorrecto")
    current_user.totp_enabled = True
    audit(db, current_user.username, "2fa_enabled", "El usuario activó la verificación en dos pasos")
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/2fa/disable", response_model=schemas.UserOut)
def disable_2fa(
    payload: schemas.TwoFADisableRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not verify_password(payload.password, current_user.hashed_password):
        raise HTTPException(401, "Contraseña incorrecta")
    current_user.totp_enabled = False
    current_user.totp_secret = None
    audit(db, current_user.username, "2fa_disabled", "El usuario desactivó la verificación en dos pasos")
    db.commit()
    db.refresh(current_user)
    return current_user
