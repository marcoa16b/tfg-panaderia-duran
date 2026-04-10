import logging

from sqlalchemy import text
from sqlmodel import SQLModel, create_engine

from dev.core.config import DATABASE_URL

logger = logging.getLogger("dev.core.database")

engine = create_engine(DATABASE_URL, echo=False)


def check_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Conexión a BD exitosa — %s", _mask_url(DATABASE_URL))
        return True
    except Exception as e:
        logger.error("Error conectando a BD: %s", e)
        return False


def create_db_and_tables():
    if not check_connection():
        logger.error("No se pudo establecer conexión con la BD — abortando create_all")
        return
    logger.info("Creando/verificando tablas en la BD...")
    SQLModel.metadata.create_all(engine)
    logger.info("Tablas creadas/verificadas correctamente")


def _mask_url(url: str) -> str:
    try:
        if "@" in url:
            prefix, suffix = url.rsplit("@", 1)
            credentials = prefix.split("://", 1)[-1]
            if ":" in credentials:
                user = credentials.split(":", 1)[0]
                driver = prefix.split("://", 1)[0]
                return f"{driver}://{user}@{suffix}"
        return url.split("?")[0]
    except Exception:
        return "***"
