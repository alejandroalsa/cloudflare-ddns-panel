import json
from sqlalchemy.orm import Session
from . import models


def _redact_settings(d):
    """Nunca guardamos contraseñas SMTP en el registro de auditoría."""
    if not isinstance(d, dict):
        return d
    clean = dict(d)
    if "mail_password" in clean and clean["mail_password"]:
        clean["mail_password"] = "••••••"
    return clean


def audit(db: Session, username: str, action: str, details: str = None, before=None, after=None):
    if isinstance(before, dict):
        before = _redact_settings(before)
    if isinstance(after, dict):
        after = _redact_settings(after)
    db.add(models.AuditLog(
        username=username,
        action=action,
        details=details,
        before_json=json.dumps(before, ensure_ascii=False, default=str) if before is not None else None,
        after_json=json.dumps(after, ensure_ascii=False, default=str) if after is not None else None,
    ))
