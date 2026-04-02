from dev.core.security import hash_password, verify_password
from dev.models.models import Usuario
from dev.repositories.usuario_repo import UsuariosRepository


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
        usuario = UsuariosRepository.get_by_correo(email_normalized)
        if not usuario:
            return None
        if not usuario.activo:
            return None
        if not cls.verify_password(password, usuario.contrasena_hash):
            return None
        return usuario

    @classmethod
    def ensure_default_user_exists(cls):
        existing = UsuariosRepository.get_by_correo("admin@panaderiaduran.com")
        if existing:
            return
        hashed = hash_password("admin123")
        UsuariosRepository.create(
            nombre="Administrador",
            correo="admin@panaderiaduran.com",
            contrasena_hash=hashed,
            rol_id=1,
        )
