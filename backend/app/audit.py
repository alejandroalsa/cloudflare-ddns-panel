from sqlalchemy.orm import Session
from . import models


def audit(db: Session, username: str, action: str, details: str = None):
    db.add(models.AuditLog(username=username, action=action, details=details))
