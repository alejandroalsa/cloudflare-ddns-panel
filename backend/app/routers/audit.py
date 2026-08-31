import csv
import io
import json
import datetime as dt
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import require_admin

router = APIRouter(prefix="/api/audit", tags=["audit"])


def _filtered_query(
    db: Session,
    start_date: Optional[dt.date],
    end_date: Optional[dt.date],
    action: Optional[str],
):
    q = db.query(models.AuditLog)
    if start_date:
        q = q.filter(models.AuditLog.timestamp >= dt.datetime.combine(start_date, dt.time.min))
    if end_date:
        q = q.filter(models.AuditLog.timestamp <= dt.datetime.combine(end_date, dt.time.max))
    if action:
        q = q.filter(models.AuditLog.action == action)
    return q


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
    q = _filtered_query(db, start_date, end_date, action)
    total = q.count()
    items = (
        q.order_by(models.AuditLog.timestamp.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return schemas.PaginatedAudit(items=items, total=total, page=page, page_size=page_size)


@router.get("/export")
def export_audit_logs(
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
    format: str = Query("json", pattern="^(json|csv)$"),
    start_date: Optional[dt.date] = None,
    end_date: Optional[dt.date] = None,
    action: Optional[str] = None,
):
    q = _filtered_query(db, start_date, end_date, action)
    rows = q.order_by(models.AuditLog.timestamp.desc()).limit(5000).all()

    if format == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["fecha", "usuario", "accion", "detalles", "antes", "despues"])
        for r in rows:
            writer.writerow([
                r.timestamp.isoformat(),
                r.username or "",
                r.action,
                r.details or "",
                r.before_json or "",
                r.after_json or "",
            ])
        buf.seek(0)
        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=auditoria.csv"},
        )

    data = [
        {
            "timestamp": r.timestamp.isoformat(),
            "username": r.username,
            "action": r.action,
            "details": r.details,
            "before": json.loads(r.before_json) if r.before_json else None,
            "after": json.loads(r.after_json) if r.after_json else None,
        }
        for r in rows
    ]
    buf = io.StringIO(json.dumps(data, ensure_ascii=False, indent=2))
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=auditoria.json"},
    )
