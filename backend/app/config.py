import os
from pydantic_settings import BaseSettings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    # Base de datos
    database_url: str = f"sqlite:///{os.path.join(BASE_DIR, 'data', 'ddns.db')}"

    # JWT
    jwt_secret: str = "CHANGE_ME_SUPER_SECRET"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 días

    # Admin inicial (solo se usa si la tabla de usuarios está vacía)
    admin_username: str = "admin"
    admin_password: str = "admin"
    admin_email: str = "admin@example.com"

    # CORS (separado por comas), útil en desarrollo con el frontend en otro puerto
    cors_origins: str = "http://localhost:5173,http://localhost:80"

    class Config:
        env_file = os.path.join(BASE_DIR, ".env")
        env_file_encoding = "utf-8"


settings = Settings()
