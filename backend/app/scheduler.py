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
_last_ip_cache = {"ip": None, "ipv6": None}


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


def get_public_ipv6(settings_dict: dict) -> str:
    if settings_dict.get("app_debug"):
        debug_ipv6 = settings_dict.get("debug_ipv6")
        if not debug_ipv6:
            raise ValueError("app_debug activo pero debug_ipv6 no configurado")
        logger.info(f"[DEBUG] Usando IPv6 de depuración: {debug_ipv6}")
        return debug_ipv6
    r = requests.get(settings_dict["public_ipv6_service"], timeout=10)
    r.raise_for_status()
    return r.text.strip()


def get_dns_records(zone_id: str, token: str) -> list:
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()["result"]


def test_connection(api_token: str, zone_id: str) -> dict:
    """Comprueba que el token y el zone_id son válidos consultando la zona en Cloudflare."""
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}"
    headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
    r = requests.get(url, headers=headers, timeout=15)
    if r.status_code == 200:
        data = r.json()
        if data.get("success"):
            return {"ok": True, "zone_name": data["result"]["name"]}
    try:
        message = r.json().get("errors", [{}])[0].get("message", f"HTTP {r.status_code}")
    except Exception:
        message = f"HTTP {r.status_code}"
    return {"ok": False, "message": message}


def update_dns_record(zone_id: str, record: dict, new_content: str, token: str, proxied: bool = None, ttl: int = None):
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record['id']}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "type": record["type"],
        "name": record["name"],
        "content": new_content,
        "ttl": record["ttl"] if ttl is None else ttl,
        "proxied": record["proxied"] if proxied is None else proxied,
    }
    r = requests.put(url, headers=headers, json=payload, timeout=15)
    r.raise_for_status()
    logger.info(f"[{zone_id}] {record['name']} ({record['type']}) actualizado a {new_content} (proxied={payload['proxied']})")
    return r.json()["result"]


def create_dns_record(zone_id: str, token: str, name: str, record_type: str, content: str, proxied: bool = None, ttl: int = None) -> dict:
    """Crea un registro DNS nuevo directamente en Cloudflare (no lo actualiza, lo crea desde cero)."""
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "type": record_type,
        "name": name,
        "content": content,
        "ttl": ttl if ttl else 1,  # 1 = automático en Cloudflare
        "proxied": bool(proxied),
    }
    r = requests.post(url, headers=headers, json=payload, timeout=15)
    if r.status_code >= 400:
        try:
            errors = r.json().get("errors", [])
            message = errors[0]["message"] if errors else f"HTTP {r.status_code}"
        except Exception:
            message = f"HTTP {r.status_code}"
        raise ValueError(message)
    logger.info(f"[{zone_id}] Registro {record_type} '{name}' creado en Cloudflare → {content}")
    return r.json()["result"]


def _match_target(zone, cf_record_name: str, cf_record_type: str):
    """Busca en los registros configurados de la zona cuál corresponde al nombre+tipo devuelto por Cloudflare."""
    for record_obj in zone.records:
        record_type = record_obj.type or "A"
        if record_type != cf_record_type:
            continue
        if record_obj.name == cf_record_name or f"{record_obj.name}.{zone.domain}" == cf_record_name:
            return record_obj
    return None


def _zone_has_type(zone, record_type: str) -> bool:
    return any((r.type or "A") == record_type for r in zone.records)


def check_zone(db, zone, settings_dict: dict, current_ip: str, current_ipv6: str = None) -> list:
    """Comprueba y actualiza los registros de UNA zona (A y, si procede, AAAA). Devuelve los nombres actualizados."""
    updated_domains = []
    dns_records = get_dns_records(zone.zone_id, zone.api_token)

    for cf_record in dns_records:
        if cf_record["type"] not in ("A", "AAAA"):
            continue
        if cf_record["type"] == "AAAA" and not current_ipv6:
            continue

        matched = _match_target(zone, cf_record["name"], cf_record["type"])
        if matched is None:
            continue

        target_content = current_ip if cf_record["type"] == "A" else current_ipv6

        if cf_record["content"] != target_content:
            update_dns_record(zone.zone_id, cf_record, target_content, zone.api_token)
            matched.last_ip = target_content
            matched.last_updated = dt.datetime.utcnow()
            matched.proxied = cf_record["proxied"]
            matched.ttl = cf_record["ttl"]
            updated_domains.append(cf_record["name"])
        else:
            matched.proxied = cf_record["proxied"]
            matched.ttl = cf_record["ttl"]

    return updated_domains


def run_check(source: str = "scheduler"):
    """Comprueba TODAS las zonas. Se ejecuta periódicamente por el scheduler (o manualmente)."""
    db = SessionLocal()
    try:
        settings_dict = get_settings_dict(db)
        current_ip = get_public_ip(settings_dict)
        last_ip = _last_ip_cache["ip"]

        current_ipv6 = None
        zones_all = db.query(models.Zone).all()
        needs_ipv6 = settings_dict.get("enable_ipv6") and any(_zone_has_type(z, "AAAA") for z in zones_all)
        if needs_ipv6:
            try:
                current_ipv6 = get_public_ipv6(settings_dict)
            except Exception as e:
                logger.error(f"No se pudo obtener la IPv6 pública: {e}")

        if current_ip == last_ip and current_ipv6 == _last_ip_cache["ipv6"] and source == "scheduler":
            logger.info("IP sin cambios")
            db.close()
            return

        logger.info(f"IP detectada: {current_ip}" + (f" / IPv6: {current_ipv6}" if current_ipv6 else ""))
        updated_domains = []

        for zone in zones_all:
            try:
                updated_domains += check_zone(db, zone, settings_dict, current_ip, current_ipv6)
            except Exception as e:
                logger.error(f"Error comprobando {zone.domain}: {e}")

        _save_log_and_notify(db, settings_dict, last_ip, current_ip, updated_domains, source=source)
        _last_ip_cache["ip"] = current_ip
        _last_ip_cache["ipv6"] = current_ipv6
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

    current_ipv6 = None
    if settings_dict.get("enable_ipv6") and _zone_has_type(zone, "AAAA"):
        try:
            current_ipv6 = get_public_ipv6(settings_dict)
        except Exception as e:
            logger.error(f"No se pudo obtener la IPv6 pública: {e}")

    updated_domains = check_zone(db, zone, settings_dict, current_ip, current_ipv6)
    _save_log_and_notify(db, settings_dict, last_ip, current_ip, updated_domains, source="manual_zone")
    _last_ip_cache["ip"] = current_ip
    if current_ipv6:
        _last_ip_cache["ipv6"] = current_ipv6
    db.commit()
    return {"current_ip": current_ip, "updated": updated_domains}


def run_check_for_record(db, record_id: int) -> dict:
    """Chequeo manual de UN registro concreto."""
    record = db.query(models.Record).get(record_id)
    if not record:
        raise ValueError("Registro no encontrado")
    zone = record.zone
    record_type = record.type or "A"

    settings_dict = get_settings_dict(db)
    last_ip = _last_ip_cache["ip"]

    if record_type == "AAAA":
        current_target = get_public_ipv6(settings_dict)
    else:
        current_target = get_public_ip(settings_dict)

    dns_records = get_dns_records(zone.zone_id, zone.api_token)
    updated_domains = []
    for cf_record in dns_records:
        if cf_record["type"] != record_type:
            continue
        if cf_record["name"] == record.name or f"{record.name}.{zone.domain}" == cf_record["name"]:
            if cf_record["content"] != current_target:
                update_dns_record(zone.zone_id, cf_record, current_target, zone.api_token)
                updated_domains.append(cf_record["name"])
            record.last_ip = current_target
            record.last_updated = dt.datetime.utcnow()
            record.proxied = cf_record["proxied"]
            record.ttl = cf_record["ttl"]
            break

    _save_log_and_notify(
        db, settings_dict, last_ip if record_type == "A" else "N/A",
        current_target if record_type == "A" else (last_ip or "N/A"),
        updated_domains, source="manual_record",
    )
    if record_type == "A":
        _last_ip_cache["ip"] = current_target
    db.commit()
    return {"current_ip": current_target, "updated": updated_domains}


def manual_update_record(db, record_id: int, ip: str, proxied: bool = None, ttl: int = None) -> dict:
    """Fija manualmente la IP/proxy/TTL de un registro, sin pasar por la comprobación automática."""
    record = db.query(models.Record).get(record_id)
    if not record:
        raise ValueError("Registro no encontrado")
    zone = record.zone
    record_type = record.type or "A"

    dns_records = get_dns_records(zone.zone_id, zone.api_token)
    cf_record = None
    for r in dns_records:
        if r["type"] != record_type:
            continue
        if r["name"] == record.name or f"{record.name}.{zone.domain}" == r["name"]:
            cf_record = r
            break

    if cf_record is None:
        raise ValueError(f"No se encontró el registro {record_type} correspondiente en Cloudflare")

    result = update_dns_record(zone.zone_id, cf_record, ip, zone.api_token, proxied=proxied, ttl=ttl)

    record.last_ip = ip
    record.last_updated = dt.datetime.utcnow()
    record.proxied = result.get("proxied", proxied)
    record.ttl = result.get("ttl", ttl)

    db.add(models.UpdateLog(
        old_ip=cf_record["content"],
        new_ip=ip,
        changed=True,
        domains_updated=json.dumps([record.name], ensure_ascii=False),
        success=True,
        source="manual_record",
        message="Edición manual de IP/proxy/TTL",
    ))
    db.commit()
    return {"ip": record.last_ip, "proxied": record.proxied, "ttl": record.ttl}


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
