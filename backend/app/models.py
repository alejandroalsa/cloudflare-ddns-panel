import enum
import datetime as dt
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
)
from sqlalchemy.orm import relationship
from .database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    viewer = "viewer"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(128), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.viewer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    totp_secret = Column(String(64), nullable=True)
    totp_enabled = Column(Boolean, default=False)


class Zone(Base):
    """Un dominio/zona de Cloudflare (equivalente a cada clave en config.json)"""
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(255), unique=True, index=True, nullable=False)
    api_token = Column(String(255), nullable=False)
    zone_id = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    records = relationship("Record", back_populates="zone", cascade="all, delete-orphan")


class Record(Base):
    """Un registro DNS (subdominio) a mantener actualizado dentro de una Zone"""
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    name = Column(String(255), nullable=False)  # ej: "ejemplo.com", "www.ejemplo.com", "*.ejemplo.com"
    type = Column(String(10), default="A")  # "A" (IPv4) o "AAAA" (IPv6)
    last_ip = Column(String(64), nullable=True)
    last_updated = Column(DateTime, nullable=True)
    proxied = Column(Boolean, nullable=True)  # estado de la nube naranja (None = desconocido aún)
    ttl = Column(Integer, nullable=True)  # None/1 = automático (TTL gestionado por Cloudflare)

    zone = relationship("Zone", back_populates="records")


class Setting(Base):
    """Tabla clave/valor genérica para la configuración global (SMTP, IP service, intervalo...)"""
    __tablename__ = "settings"

    key = Column(String(64), primary_key=True)
    value = Column(Text, nullable=True)


class UpdateLog(Base):
    """Historial de comprobaciones/actualizaciones de IP"""
    __tablename__ = "update_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=dt.datetime.utcnow, index=True)
    old_ip = Column(String(64), nullable=True)
    new_ip = Column(String(64), nullable=True)
    changed = Column(Boolean, default=False)
    domains_updated = Column(Text, nullable=True)  # JSON serializado (lista de nombres)
    success = Column(Boolean, default=True)
    message = Column(Text, nullable=True)
    source = Column(String(32), default="scheduler")  # scheduler | manual_global | manual_zone | manual_record


class AuditLog(Base):
    """Registro de auditoría: qué usuario hizo qué acción administrativa"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=dt.datetime.utcnow, index=True)
    username = Column(String(64), nullable=True)  # se guarda el nombre, no FK, para conservar el historial si se borra el usuario
    action = Column(String(64), nullable=False, index=True)
    details = Column(Text, nullable=True)
    before_json = Column(Text, nullable=True)  # estado antes del cambio (JSON), cuando aplica
    after_json = Column(Text, nullable=True)   # estado después del cambio (JSON), cuando aplica


class RecoveryCode(Base):
    """Códigos de recuperación de un solo uso para el 2FA de un usuario"""
    __tablename__ = "recovery_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    code_hash = Column(String(64), nullable=False, index=True)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
