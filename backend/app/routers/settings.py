from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user, require_admin

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
    _: models.User = Depends(require_admin),
):
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
    db.commit()

    if data.get("update_interval"):
        from ..scheduler import reschedule  # import local para evitar dependencia circular
        reschedule(data["update_interval"])

    return schemas.SettingsPayload(**_get_all(db))
