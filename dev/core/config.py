import os

DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///reflex.db")
SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
    os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)
APP_NAME: str = "Panaderia Duran"
DEBUG: bool = os.environ.get("DEBUG", "true").lower() == "true"
LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO").upper()
SEED_DEMO: bool = os.environ.get("SEED_DEMO", "false").lower() == "true"
