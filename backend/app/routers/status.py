from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user, require_admin
from .. import scheduler as ddns_scheduler

router = APIRouter(prefix="/api/status", tags=["status"])


@router.get("", response_model=schemas.StatusOut)
def get_status(db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    last_log = (
        db.query(models.UpdateLog).order_by(models.UpdateLog.timestamp.desc()).first()
    )
    recent_logs = (
        db.query(models.UpdateLog).order_by(models.UpdateLog.timestamp.desc()).limit(20).all()
    )
    return schemas.StatusOut(
        current_ip=last_log.new_ip if last_log else None,
        last_check=last_log.timestamp if last_log else None,
        total_zones=db.query(models.Zone).count(),
        total_records=db.query(models.Record).count(),
        recent_logs=recent_logs,
    )


@router.post("/check")
def check_all_now(db: Session = Depends(get_db), _: models.User = Depends(require_admin)):
    """Fuerza una comprobación inmediata de TODAS las zonas (botón 'Comprobar ahora' global)."""
    try:
        ddns_scheduler.run_check(source="manual_global")
    except Exception as e:
        raise HTTPException(502, f"Error al comprobar: {e}")
    last_log = db.query(models.UpdateLog).order_by(models.UpdateLog.timestamp.desc()).first()
    return {"ok": True, "log": schemas.UpdateLogOut.model_validate(last_log) if last_log else None}


@router.delete("/logs")
def clear_logs(db: Session = Depends(get_db), _: models.User = Depends(require_admin)):
    """Elimina todo el historial de comprobaciones."""
    db.query(models.UpdateLog).delete()
    db.commit()
    return {"ok": True}
