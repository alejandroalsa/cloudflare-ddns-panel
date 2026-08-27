import datetime as dt
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user, require_admin
from .. import scheduler as ddns_scheduler
from ..audit import audit

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


@router.get("/logs", response_model=schemas.PaginatedLogs)
def list_logs(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    start_date: Optional[dt.date] = None,
    end_date: Optional[dt.date] = None,
):
    """Historial paginado, con filtro opcional por rango de fechas."""
    q = db.query(models.UpdateLog)
    if start_date:
        q = q.filter(models.UpdateLog.timestamp >= dt.datetime.combine(start_date, dt.time.min))
    if end_date:
        q = q.filter(models.UpdateLog.timestamp <= dt.datetime.combine(end_date, dt.time.max))

    total = q.count()
    items = (
        q.order_by(models.UpdateLog.timestamp.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return schemas.PaginatedLogs(items=items, total=total, page=page, page_size=page_size)


@router.get("/ip-history", response_model=list[schemas.UpdateLogOut])
def ip_history(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
    limit: int = Query(50, ge=5, le=500),
):
    """Últimas N comprobaciones en orden cronológico ascendente, para graficar la evolución de la IP."""
    items = (
        db.query(models.UpdateLog)
        .order_by(models.UpdateLog.timestamp.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(items))


@router.post("/check")
def check_all_now(db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    """Fuerza una comprobación inmediata de TODAS las zonas (botón 'Comprobar ahora' global)."""
    try:
        ddns_scheduler.run_check(source="manual_global")
    except Exception as e:
        raise HTTPException(502, f"Error al comprobar: {e}")
    audit(db, current_user.username, "manual_check_global", "Comprobación manual de todos los dominios")
    db.commit()
    last_log = db.query(models.UpdateLog).order_by(models.UpdateLog.timestamp.desc()).first()
    return {"ok": True, "log": schemas.UpdateLogOut.model_validate(last_log) if last_log else None}


@router.delete("/logs")
def clear_logs(db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    """Elimina todo el historial de comprobaciones."""
    count = db.query(models.UpdateLog).count()
    db.query(models.UpdateLog).delete()
    audit(db, current_user.username, "logs_cleared", f"Borró el historial ({count} entradas)")
    db.commit()
    return {"ok": True}
