import logging

from dev.core.security import hash_password, verify_password
from dev.models.models import Usuario
from dev.repositories.usuario_repo import UsuarioRepository

logger = logging.getLogger("dev.services.auth")


class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return hash_password(password)

    @staticmethod
    def verify_password(plain_password: str, password_hash: str) -> bool:
        return verify_password(plain_password, password_hash)

    @classmethod
    def authenticate(cls, email: str, password: str):
        email_normalized = email.strip().lower()
        logger.debug("Autenticando usuario: %s", email_normalized)

        usuario = UsuarioRepository.get_by_correo(email_normalized)
        if not usuario:
            logger.warning("Usuario no encontrado en BD: %s", email_normalized)
            return None

        if not usuario.activo:
            logger.warning(
                "Usuario inactivo intentó login: %s (id=%s)",
                email_normalized,
                usuario.id,
            )
            return None

        if not cls.verify_password(password, usuario.contrasena_hash):
            logger.warning(
                "Contraseña incorrecta para usuario: %s (id=%s)",
                email_normalized,
                usuario.id,
            )
            return None

        logger.info(
            "Autenticación exitosa para: %s (id=%s)", email_normalized, usuario.id
        )
        return usuario

    @classmethod
    def ensure_default_user_exists(cls):
        default_email = "admin@panaderiaduran.com"
        logger.info("Verificando existencia de usuario por defecto: %s", default_email)

        existing = UsuarioRepository.get_by_correo(default_email)
        if existing:
            logger.info("Usuario por defecto ya existe — id=%s", existing.id)
            return

        logger.info("Creando usuario por defecto: %s", default_email)
        hashed = hash_password("admin123")
        usuario = UsuarioRepository.create(
            nombre="Administrador",
            correo=default_email,
            contrasena_hash=hashed,
            rol_id=1,
        )
        logger.info("Usuario por defecto creado — id=%s", usuario.id)
