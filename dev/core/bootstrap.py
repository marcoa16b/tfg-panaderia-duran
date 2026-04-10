import logging

from dev.core.database import create_db_and_tables
from dev.core.seed_data import run_all_seeds

logger = logging.getLogger("dev.core.bootstrap")


def bootstrap_app() -> None:
    logger.info("Iniciando bootstrap de la aplicación")
    create_db_and_tables()
    logger.info("Tablas de BD verificadas/creadas")
    run_all_seeds()
    logger.info("Bootstrap completado")
