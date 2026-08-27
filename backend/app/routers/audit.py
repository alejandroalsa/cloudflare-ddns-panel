import datetime as dt
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import require_admin

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("", response_model=schemas.PaginatedAudit)
def list_audit_logs(
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    start_date: Optional[dt.date] = None,
    end_date: Optional[dt.date] = None,
    action: Optional[str] = None,
):
    q = db.query(models.AuditLog)
    if start_date:
        q = q.filter(models.AuditLog.timestamp >= dt.datetime.combine(start_date, dt.time.min))
    if end_date:
        q = q.filter(models.AuditLog.timestamp <= dt.datetime.combine(end_date, dt.time.max))
    if action:
        q = q.filter(models.AuditLog.action == action)

    total = q.count()
    items = (
        q.order_by(models.AuditLog.timestamp.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return schemas.PaginatedAudit(items=items, total=total, page=page, page_size=page_size)
