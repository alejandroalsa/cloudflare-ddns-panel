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
    last_ip = Column(String(64), nullable=True)
    last_updated = Column(DateTime, nullable=True)
    proxied = Column(Boolean, nullable=True)  # estado de la nube naranja (None = desconocido aún)

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
