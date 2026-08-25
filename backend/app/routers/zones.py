from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user, require_admin
from .. import scheduler as ddns_scheduler

router = APIRouter(prefix="/api/zones", tags=["zones"])


def _to_out(zone: models.Zone) -> schemas.ZoneOut:
    out = schemas.ZoneOut.model_validate(zone)
    out.api_token_preview = (zone.api_token[:4] + "…" + zone.api_token[-4:]) if zone.api_token else None
    return out


@router.get("", response_model=List[schemas.ZoneOut])
def list_zones(db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    zones = db.query(models.Zone).order_by(models.Zone.domain).all()
    return [_to_out(z) for z in zones]


@router.post("", response_model=schemas.ZoneOut)
def create_zone(
    payload: schemas.ZoneCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    if db.query(models.Zone).filter(models.Zone.domain == payload.domain).first():
        raise HTTPException(400, "Ese dominio ya está registrado")
    zone = models.Zone(domain=payload.domain, api_token=payload.api_token, zone_id=payload.zone_id)
    db.add(zone)
    db.flush()
    for record_name in payload.records:
        db.add(models.Record(zone_id=zone.id, name=record_name))
    db.commit()
    db.refresh(zone)
    return _to_out(zone)


@router.put("/{zone_id}", response_model=schemas.ZoneOut)
def update_zone(
    zone_id: int,
    payload: schemas.ZoneUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    zone = db.query(models.Zone).get(zone_id)
    if not zone:
        raise HTTPException(404, "Dominio no encontrado")
    if payload.api_token is not None:
        zone.api_token = payload.api_token
    if payload.zone_id is not None:
        zone.zone_id = payload.zone_id
    db.commit()
    db.refresh(zone)
    return _to_out(zone)


@router.delete("/{zone_id}")
def delete_zone(
    zone_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    zone = db.query(models.Zone).get(zone_id)
    if not zone:
        raise HTTPException(404, "Dominio no encontrado")
    db.delete(zone)
    db.commit()
    return {"ok": True}


# ---------- Records ----------
@router.post("/{zone_id}/records", response_model=schemas.RecordOut)
def add_record(
    zone_id: int,
    payload: schemas.RecordCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    zone = db.query(models.Zone).get(zone_id)
    if not zone:
        raise HTTPException(404, "Dominio no encontrado")
    record = models.Record(zone_id=zone.id, name=payload.name)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/records/{record_id}")
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    record = db.query(models.Record).get(record_id)
    if not record:
        raise HTTPException(404, "Registro no encontrado")
    db.delete(record)
    db.commit()
    return {"ok": True}


# ---------- Checks manuales ----------
@router.post("/{zone_id}/check")
def check_zone_now(
    zone_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    try:
        return ddns_scheduler.run_check_for_zone(db, zone_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(502, f"Error comprobando el dominio: {e}")


@router.post("/records/{record_id}/check")
def check_record_now(
    record_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    try:
        return ddns_scheduler.run_check_for_record(db, record_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(502, f"Error comprobando el registro: {e}")


# ---------- Edición manual de IP / proxy ----------
@router.put("/records/{record_id}/manual", response_model=schemas.RecordOut)
def manual_update_record(
    record_id: int,
    payload: schemas.RecordManualUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    try:
        ddns_scheduler.manual_update_record(db, record_id, payload.ip, payload.proxied)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(502, f"Error actualizando en Cloudflare: {e}")

    record = db.query(models.Record).get(record_id)
    return record


# ---------- Import / Export ----------
@router.get("/export", response_model=schemas.ImportPayload)
def export_all(db: Session = Depends(get_db), _: models.User = Depends(require_admin)):
    zones = db.query(models.Zone).all()
    domains = {
        z.domain: schemas.ZoneImportEntry(
            api_token=z.api_token, zone_id=z.zone_id, records=[r.name for r in z.records]
        )
        for z in zones
    }
    return schemas.ImportPayload(domains=domains)


@router.get("/{zone_id}/export", response_model=schemas.ImportPayload)
def export_zone(
    zone_id: int, db: Session = Depends(get_db), _: models.User = Depends(require_admin)
):
    zone = db.query(models.Zone).get(zone_id)
    if not zone:
        raise HTTPException(404, "Dominio no encontrado")
    return schemas.ImportPayload(
        domains={
            zone.domain: schemas.ZoneImportEntry(
                api_token=zone.api_token,
                zone_id=zone.zone_id,
                records=[r.name for r in zone.records],
            )
        }
    )


@router.post("/import", response_model=schemas.ImportResult)
def import_zones(
    payload: schemas.ImportPayload,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    result = schemas.ImportResult()
    for domain, entry in payload.domains.items():
        existing = db.query(models.Zone).filter(models.Zone.domain == domain).first()
        if existing:
            existing.api_token = entry.api_token
            existing.zone_id = entry.zone_id
            existing_names = {r.name for r in existing.records}
            for record_name in entry.records:
                if record_name not in existing_names:
                    db.add(models.Record(zone_id=existing.id, name=record_name))
            result.updated.append(domain)
        else:
            zone = models.Zone(domain=domain, api_token=entry.api_token, zone_id=entry.zone_id)
            db.add(zone)
            db.flush()
            for record_name in entry.records:
                db.add(models.Record(zone_id=zone.id, name=record_name))
            result.created.append(domain)
    db.commit()
    return result
