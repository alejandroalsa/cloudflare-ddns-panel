import datetime as dt
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from .models import UserRole


# ---------- Auth ----------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


# ---------- Users ----------
class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    role: UserRole = UserRole.viewer
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None  # si se envía, se cambia


class UserSelfUpdate(BaseModel):
    """Lo que un usuario puede cambiar de sí mismo (sin rol ni is_active)."""
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: dt.datetime


# ---------- Records ----------
class RecordBase(BaseModel):
    name: str


class RecordCreate(RecordBase):
    pass


class RecordOut(RecordBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    zone_id: int
    last_ip: Optional[str] = None
    last_updated: Optional[dt.datetime] = None
    proxied: Optional[bool] = None


class RecordManualUpdate(BaseModel):
    ip: str
    proxied: Optional[bool] = None


# ---------- Zones ----------
class ZoneBase(BaseModel):
    domain: str
    zone_id: str


class ZoneCreate(ZoneBase):
    api_token: str
    records: List[str] = []  # nombres de subdominios iniciales


class ZoneUpdate(BaseModel):
    api_token: Optional[str] = None
    zone_id: Optional[str] = None


class ZoneOut(ZoneBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: dt.datetime
    records: List[RecordOut] = []
    # api_token nunca se devuelve completo por seguridad
    api_token_preview: Optional[str] = None


# ---------- Settings ----------
class SettingsPayload(BaseModel):
    update_interval: int = 300
    public_ip_service: str = "https://api.ipify.org"
    app_debug: bool = False
    debug_ip: Optional[str] = None

    mail_host: Optional[str] = None
    mail_port: int = 465
    mail_username: Optional[str] = None
    mail_password: Optional[str] = None
    mail_from_address: Optional[str] = None
    mail_from_name: str = "Cloudflare DDNS Updater"
    notification_email: Optional[str] = None       # "To" - varios separados por coma
    notification_cc: Optional[str] = None          # CC - varios separados por coma
    notification_bcc: Optional[str] = None         # CCO - varios separados por coma


# ---------- Status / Logs ----------
class UpdateLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    timestamp: dt.datetime
    old_ip: Optional[str]
    new_ip: Optional[str]
    changed: bool
    domains_updated: Optional[str]
    success: bool
    message: Optional[str]
    source: str = "scheduler"


class StatusOut(BaseModel):
    current_ip: Optional[str]
    last_check: Optional[dt.datetime]
    total_zones: int
    total_records: int
    recent_logs: List[UpdateLogOut]


# ---------- Import / Export (formato compatible con el antiguo config.json) ----------
class ZoneImportEntry(BaseModel):
    api_token: str
    zone_id: str
    records: List[str] = []


class ImportPayload(BaseModel):
    domains: dict[str, ZoneImportEntry]


class ImportResult(BaseModel):
    created: List[str] = []
    updated: List[str] = []
    skipped: List[str] = []
