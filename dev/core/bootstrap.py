import logging

from dev.core.database import create_db_and_tables
from dev.core.seed_data import run_all_seeds

logger = logging.getLogger("dev.core.bootstrap")


def bootstrap_app() -> None:
    logger.info("Iniciando bootstrap de la aplicación")
    create_db_and_tables()
    logger.info("Tablas de BD verificadas/creadas")
    run_all_seeds()
    logger.info("Seed de datos iniciales completado")
    _run_initial_alert_detection()
    logger.info("Bootstrap completado")


def _run_initial_alert_detection() -> None:
    """Ejecuta detección de alertas al arrancar la app."""
    try:
        from dev.services.alerta_service import AlertaService

        result = AlertaService.ejecutar_deteccion_completa()
        if result.get("total_nuevas", 0) > 0:
            logger.info(
                "Alertas iniciales detectadas: %s bajo stock, %s por vencer",
                result.get("bajo_stock", 0),
                result.get("proximos_vencer", 0),
            )
    except Exception as e:
        logger.warning("Error en detección inicial de alertas: %s", str(e))
