import logging
import os
import sys


def setup_logging() -> None:
    level = os.environ.get("LOG_LEVEL", "INFO").upper()

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    if os.environ.get("DEBUG", "false").lower() == "true":
        logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)
    else:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.orm").setLevel(logging.WARNING)

    logger = logging.getLogger("dev")
    logger.info("Logging configurado — nivel: %s", level)
