from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user, require_admin
from ..audit import audit
from ..email_utils import send_notification_email

router = APIRouter(prefix="/api/settings", tags=["settings"])

DEFAULTS = schemas.SettingsPayload().model_dump()


def _get_all(db: Session) -> dict:
    rows = db.query(models.Setting).all()
    values = {r.key: r.value for r in rows}
    result = dict(DEFAULTS)
    for key, default in DEFAULTS.items():
        if key in values and values[key] is not None:
            raw = values[key]
            if isinstance(default, bool):
                result[key] = raw.lower() == "true"
            elif isinstance(default, int):
                result[key] = int(raw)
            else:
                result[key] = raw
    return result


@router.get("", response_model=schemas.SettingsPayload)
def get_settings(db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    return schemas.SettingsPayload(**_get_all(db))


@router.put("", response_model=schemas.SettingsPayload)
def update_settings(
    payload: schemas.SettingsPayload,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    before = _get_all(db)
    data = payload.model_dump()
    for key, value in data.items():
        # No sobreescribir la contraseña de correo si viene vacía (para no borrarla sin querer)
        if key == "mail_password" and not value:
            continue
        row = db.query(models.Setting).get(key)
        str_value = "" if value is None else str(value)
        if row:
            row.value = str_value
        else:
            db.add(models.Setting(key=key, value=str_value))

    after = _get_all(db)
    audit(db, current_user.username, "settings_update", "Actualizó la configuración global", before=before, after=after)
    db.commit()

    if data.get("update_interval"):
        from ..scheduler import reschedule  # import local para evitar dependencia circular
        reschedule(data["update_interval"])

    return schemas.SettingsPayload(**_get_all(db))


@router.post("/test-email", response_model=schemas.TestEmailResult)
def test_email(db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    settings_dict = _get_all(db)
    try:
        send_notification_email(
            settings_dict,
            old_ip="192.0.2.1",
            new_ip="192.0.2.2",
            domains=["prueba.ejemplo.com"],
        )
        audit(db, current_user.username, "test_email", "Envió un email de prueba")
        db.commit()
        return schemas.TestEmailResult(ok=True, message=f"Correo de prueba enviado a {settings_dict.get('notification_email')}")
    except Exception as e:
        return schemas.TestEmailResult(ok=False, message=str(e))
