import json
import logging
import datetime as dt
import requests
from apscheduler.schedulers.background import BackgroundScheduler

from .database import SessionLocal
from . import models
from .routers.settings import _get_all as get_settings_dict
from .email_utils import send_notification_email

logger = logging.getLogger("ddns")
scheduler = BackgroundScheduler()
_last_ip_cache = {"ip": None}


def get_public_ip(settings_dict: dict) -> str:
    if settings_dict.get("app_debug"):
        debug_ip = settings_dict.get("debug_ip")
        if not debug_ip:
            raise ValueError("app_debug activo pero debug_ip no configurado")
        logger.info(f"[DEBUG] Usando IP de depuración: {debug_ip}")
        return debug_ip
    r = requests.get(settings_dict["public_ip_service"], timeout=10)
    r.raise_for_status()
    return r.text.strip()


def get_dns_records(zone_id: str, token: str) -> list:
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()["result"]


def update_dns_record(zone_id: str, record: dict, new_ip: str, token: str, proxied: bool = None):
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record['id']}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "type": "A",
        "name": record["name"],
        "content": new_ip,
        "ttl": record["ttl"],
        "proxied": record["proxied"] if proxied is None else proxied,
    }
    r = requests.put(url, headers=headers, json=payload, timeout=15)
    r.raise_for_status()
    logger.info(f"[{zone_id}] {record['name']} actualizado a {new_ip} (proxied={payload['proxied']})")
    return r.json()["result"]


def _match_target(zone, cf_record_name: str):
    """Busca en los registros configurados de la zona cuál corresponde al nombre devuelto por Cloudflare."""
    for record_obj in zone.records:
        if record_obj.name == cf_record_name or f"{record_obj.name}.{zone.domain}" == cf_record_name:
            return record_obj
    return None


def check_zone(db, zone, settings_dict: dict, current_ip: str) -> list:
    """Comprueba y actualiza los registros de UNA zona. Devuelve la lista de nombres actualizados."""
    updated_domains = []
    dns_records = get_dns_records(zone.zone_id, zone.api_token)

    for cf_record in dns_records:
        if cf_record["type"] != "A":
            continue
        matched = _match_target(zone, cf_record["name"])
        if matched is None:
            continue
        if cf_record["content"] != current_ip:
            update_dns_record(zone.zone_id, cf_record, current_ip, zone.api_token)
            matched.last_ip = current_ip
            matched.last_updated = dt.datetime.utcnow()
            matched.proxied = cf_record["proxied"]
            updated_domains.append(cf_record["name"])
        else:
            # aunque no cambie, sincronizamos el estado de proxied conocido
            matched.proxied = cf_record["proxied"]

    return updated_domains


def run_check(source: str = "scheduler"):
    """Comprueba TODAS las zonas. Se ejecuta periódicamente por el scheduler (o manualmente)."""
    db = SessionLocal()
    try:
        settings_dict = get_settings_dict(db)
        current_ip = get_public_ip(settings_dict)
        last_ip = _last_ip_cache["ip"]

        if current_ip == last_ip and source == "scheduler":
            logger.info("IP sin cambios")
            db.close()
            return

        logger.info(f"IP detectada: {current_ip}")
        updated_domains = []

        zones = db.query(models.Zone).all()
        for zone in zones:
            try:
                updated_domains += check_zone(db, zone, settings_dict, current_ip)
            except Exception as e:
                logger.error(f"Error comprobando {zone.domain}: {e}")

        _save_log_and_notify(db, settings_dict, last_ip, current_ip, updated_domains, source=source)
        _last_ip_cache["ip"] = current_ip
        db.commit()

    except Exception as e:
        logger.error(f"Error en run_check: {e}")
        db.add(models.UpdateLog(success=False, message=str(e), source=source))
        db.commit()
    finally:
        db.close()


def run_check_for_zone(db, zone_id: int) -> dict:
    """Chequeo manual de UNA zona (endpoint 'Comprobar ahora' a nivel de dominio)."""
    zone = db.query(models.Zone).get(zone_id)
    if not zone:
        raise ValueError("Dominio no encontrado")

    settings_dict = get_settings_dict(db)
    current_ip = get_public_ip(settings_dict)
    last_ip = _last_ip_cache["ip"]

    updated_domains = check_zone(db, zone, settings_dict, current_ip)
    _save_log_and_notify(db, settings_dict, last_ip, current_ip, updated_domains, source="manual_zone")
    _last_ip_cache["ip"] = current_ip
    db.commit()
    return {"current_ip": current_ip, "updated": updated_domains}


def run_check_for_record(db, record_id: int) -> dict:
    """Chequeo manual de UN registro concreto."""
    record = db.query(models.Record).get(record_id)
    if not record:
        raise ValueError("Registro no encontrado")
    zone = record.zone

    settings_dict = get_settings_dict(db)
    current_ip = get_public_ip(settings_dict)
    last_ip = _last_ip_cache["ip"]

    dns_records = get_dns_records(zone.zone_id, zone.api_token)
    updated_domains = []
    for cf_record in dns_records:
        if cf_record["type"] != "A":
            continue
        if cf_record["name"] == record.name or f"{record.name}.{zone.domain}" == cf_record["name"]:
            if cf_record["content"] != current_ip:
                update_dns_record(zone.zone_id, cf_record, current_ip, zone.api_token)
                updated_domains.append(cf_record["name"])
            record.last_ip = current_ip
            record.last_updated = dt.datetime.utcnow()
            record.proxied = cf_record["proxied"]
            break

    _save_log_and_notify(db, settings_dict, last_ip, current_ip, updated_domains, source="manual_record")
    _last_ip_cache["ip"] = current_ip
    db.commit()
    return {"current_ip": current_ip, "updated": updated_domains}


def manual_update_record(db, record_id: int, ip: str, proxied: bool = None) -> dict:
    """Fija manualmente la IP (y opcionalmente el proxy) de un registro, sin pasar por la comprobación automática."""
    record = db.query(models.Record).get(record_id)
    if not record:
        raise ValueError("Registro no encontrado")
    zone = record.zone

    dns_records = get_dns_records(zone.zone_id, zone.api_token)
    cf_record = None
    for r in dns_records:
        if r["type"] != "A":
            continue
        if r["name"] == record.name or f"{record.name}.{zone.domain}" == r["name"]:
            cf_record = r
            break

    if cf_record is None:
        raise ValueError("No se encontró el registro A correspondiente en Cloudflare")

    result = update_dns_record(zone.zone_id, cf_record, ip, zone.api_token, proxied=proxied)

    record.last_ip = ip
    record.last_updated = dt.datetime.utcnow()
    record.proxied = result.get("proxied", proxied)

    db.add(models.UpdateLog(
        old_ip=cf_record["content"],
        new_ip=ip,
        changed=True,
        domains_updated=json.dumps([record.name], ensure_ascii=False),
        success=True,
        source="manual_record",
        message="Edición manual de IP/proxy",
    ))
    db.commit()
    return {"ip": record.last_ip, "proxied": record.proxied}


def _save_log_and_notify(db, settings_dict, old_ip, new_ip, updated_domains, source: str):
    log_entry = models.UpdateLog(
        old_ip=old_ip or "N/A",
        new_ip=new_ip,
        changed=bool(updated_domains),
        domains_updated=json.dumps(updated_domains, ensure_ascii=False),
        success=True,
        source=source,
    )
    db.add(log_entry)

    if updated_domains:
        try:
            send_notification_email(settings_dict, old_ip or "N/A", new_ip, updated_domains)
            logger.info(f"Correo de notificación enviado a {settings_dict.get('notification_email')}")
        except Exception as e:
            logger.error(f"No se pudo enviar el correo: {e}")


def start_scheduler():
    db = SessionLocal()
    try:
        settings_dict = get_settings_dict(db)
        interval = settings_dict.get("update_interval", 300)
    finally:
        db.close()

    scheduler.add_job(run_check, "interval", seconds=interval, id="ddns_check", replace_existing=True)
    scheduler.start()
    logger.info(f"Scheduler iniciado (cada {interval}s)")


def reschedule(interval_seconds: int):
    if scheduler.get_job("ddns_check"):
        scheduler.reschedule_job("ddns_check", trigger="interval", seconds=interval_seconds)
