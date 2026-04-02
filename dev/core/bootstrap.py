from dev.core.database import create_db_and_tables
from dev.services.auth_service import AuthService


def bootstrap_app() -> None:
    create_db_and_tables()
    AuthService.ensure_default_user_exists()
