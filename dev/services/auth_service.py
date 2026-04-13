"""
auth_service.py — Servicio de autenticación y gestión de usuarios.

Arquitectura
------------
Capa de lógica de negocio para todo lo relacionado con usuarios:
autenticación, registro, cambio/restauración de contraseña y validación
de tokens JWT. Es el ÚNICO punto de entrada para operaciones de auth.

Patrón de diseño: Service Layer
    - Orquesta llamadas al repositorio (UsuarioRepository).
    - Aplica reglas de negocio (validación de email, longitud de password).
    - Genera y valida tokens JWT.
    - NO contiene SQL ni acceso directo a la BD.

Relación con otras capas
------------------------
    [Login Page] → [AuthState] → AuthService → UsuarioRepository → [PostgreSQL]

Flujo de autenticación
----------------------
1. El usuario ingresa correo + contraseña en el login.
2. AuthState llama a AuthService.authenticate().
3. El service busca el usuario, verifica contraseña y genera JWT.
4. AuthState almacena el token y los datos del usuario en el estado.

Registro de usuarios
--------------------
1. Se validan los datos: nombre (mínimo 2 chars), email (regex), password (mínimo 8).
2. Se verifica que el correo no exista (DuplicateException).
3. Se hashea la contraseña con Argon2.
4. Se crea el usuario via UsuarioRepository.

Token JWT
---------
El token contiene: {"sub": user_id, "correo": "...", "rol_id": N, "exp": timestamp}.
Expira según ACCESS_TOKEN_EXPIRE_MINUTES (default: 60 min, ver config.py).

Excepciones
-----------
    - ValidationException: Datos de entrada inválidos.
    - DuplicateException: Correo ya registrado.
    - UnauthorizedException: Contraseña incorrecta o token inválido.
    - NotFoundException: Usuario no encontrado (via get_by_id_or_fail).
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from dev.core.exceptions import (
    DuplicateException,
    UnauthorizedException,
    ValidationException,
)
from dev.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from dev.models.models import Usuario
from dev.repositories.usuario_repo import UsuarioRepository

logger = logging.getLogger("dev.services.auth")

_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
_PASSWORD_MIN_LENGTH = 8


class AuthService:
    """
    Servicio de autenticación y gestión de usuarios.

    Métodos principales:
        - authenticate: Login con correo + password → retorna usuario + token JWT.
        - register: Crear nuevo usuario con validaciones.
        - change_password: Cambio de contraseña (requiere contraseña actual).
        - reset_password: Resetear contraseña por correo (para recuperación).
        - validate_token: Verificar que un JWT es válido y el usuario está activo.
        - ensure_default_user_exists: Crear admin por defecto si no existe.

    Uso desde la capa State:
        from dev.services.auth_service import AuthService

        result = AuthService.authenticate("admin@panaderiaduran.com", "Admin123!")
        # result = {"usuario": Usuario(...), "token": "eyJ..."}
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """Delegado a core.security. Hashea contraseña con Argon2."""
        return hash_password(password)

    @staticmethod
    def verify_password(plain_password: str, password_hash: str) -> bool:
        """Delegado a core.security. Verifica contraseña contra hash."""
        return verify_password(plain_password, password_hash)

    @classmethod
    def authenticate(cls, correo: str, password: str) -> Optional[dict]:
        """
        Autentica un usuario por correo y contraseña.

        Flujo:
            1. Normaliza el correo (strip + lowercase).
            2. Busca el usuario en la BD (incluye inactivos).
            3. Verifica que esté activo.
            4. Verifica la contraseña contra el hash.
            5. Genera un token JWT con id, correo y rol.

        Args:
            correo: Email del usuario.
            password: Contraseña en texto plano.

        Returns:
            {"usuario": Usuario, "token": str} si la autenticación es exitosa.
            None si el usuario no existe, está inactivo o la contraseña es incorrecta.

        Nota de seguridad:
            Retorna None (no lanza excepción) para no revelar si el usuario
            existe o no. Siempre muestra el mismo mensaje de error genérico.
        """
        correo_normalized = correo.strip().lower()
        logger.debug("Autenticando usuario: %s", correo_normalized)

        usuario = UsuarioRepository.get_by_correo(correo_normalized)
        if not usuario:
            logger.warning("Usuario no encontrado: %s", correo_normalized)
            return None

        if not usuario.activo:
            logger.warning(
                "Usuario inactivo intentó login: %s (id=%s)",
                correo_normalized,
                usuario.id,
            )
            return None

        if not cls.verify_password(password, usuario.contrasena_hash):
            logger.warning(
                "Contraseña incorrecta: %s (id=%s)", correo_normalized, usuario.id
            )
            return None

        token = create_access_token(
            {"sub": str(usuario.id), "correo": usuario.correo, "rol_id": usuario.rol_id}
        )

        logger.info("Autenticación exitosa: %s (id=%s)", correo_normalized, usuario.id)
        return {"usuario": usuario, "token": token}

    @classmethod
    def register(cls, nombre: str, correo: str, password: str, rol_id: int) -> Usuario:
        """
        Registra un nuevo usuario con validaciones completas.

        Validaciones:
            - Nombre: mínimo 2 caracteres.
            - Correo: formato válido (regex).
            - Password: mínimo 8 caracteres.
            - Correo único: no debe existir en la BD.

        Args:
            nombre: Nombre completo del usuario.
            correo: Email (será normalizado a lowercase).
            password: Contraseña en texto plano (se hashea antes de guardar).
            rol_id: ID del rol asignado (FK a tabla 'rol').

        Returns:
            El usuario creado con su ID generado por la BD.

        Raises:
            ValidationException: Si algún campo no pasa la validación.
            DuplicateException: Si ya existe un usuario con ese correo.
        """
        correo_normalized = correo.strip().lower()

        if not nombre or len(nombre.strip()) < 2:
            raise ValidationException("El nombre debe tener al menos 2 caracteres")

        if not _EMAIL_REGEX.match(correo_normalized):
            raise ValidationException("Formato de correo electrónico inválido")

        if len(password) < _PASSWORD_MIN_LENGTH:
            raise ValidationException(
                f"La contraseña debe tener al menos {_PASSWORD_MIN_LENGTH} caracteres"
            )

        if UsuarioRepository.exists_by_correo(correo_normalized):
            raise DuplicateException(
                f"Ya existe un usuario con el correo {correo_normalized}"
            )

        hashed = hash_password(password)
        usuario = UsuarioRepository.create(
            nombre=nombre.strip(),
            correo=correo_normalized,
            contrasena_hash=hashed,
            rol_id=rol_id,
        )
        logger.info("Usuario registrado: %s (id=%s)", correo_normalized, usuario.id)
        return usuario

    @classmethod
    def change_password(
        cls, usuario_id: int, current_password: str, new_password: str
    ) -> bool:
        """
        Cambia la contraseña de un usuario autenticado.

        Requiere la contraseña actual como medida de seguridad.
        La nueva contraseña se valida con la misma regla de longitud mínima.

        Args:
            usuario_id: PK del usuario.
            current_password: Contraseña actual (para verificación).
            new_password: Nueva contraseña (mínimo 8 caracteres).

        Returns:
            True si el cambio fue exitoso.

        Raises:
            ValidationException: Si la nueva contraseña es muy corta.
            UnauthorizedException: Si la contraseña actual es incorrecta.
            NotFoundException: Si el usuario no existe.
        """
        if len(new_password) < _PASSWORD_MIN_LENGTH:
            raise ValidationException(
                f"La nueva contraseña debe tener al menos {_PASSWORD_MIN_LENGTH} caracteres"
            )

        usuario = UsuarioRepository.get_by_id_or_fail(usuario_id)

        if not cls.verify_password(current_password, usuario.contrasena_hash):
            raise UnauthorizedException("Contraseña actual incorrecta")

        UsuarioRepository.update(
            usuario_id, contrasena_hash=hash_password(new_password)
        )
        logger.info("Contraseña cambiada para usuario id=%s", usuario_id)
        return True

    @classmethod
    def reset_password(cls, correo: str, new_password: str) -> bool:
        """
        Resetea la contraseña de un usuario por correo (flujo de recuperación).

        A diferencia de change_password, NO requiere la contraseña actual.
        En producción, este método debería llamarse solo después de verificar
        un código/token de recuperación enviado por email.

        Args:
            correo: Email del usuario (se normaliza).
            new_password: Nueva contraseña.

        Returns:
            True si se reseteó exitosamente.
            False si el correo no corresponde a un usuario activo.

        Raises:
            ValidationException: Si la nueva contraseña es muy corta.
        """
        correo_normalized = correo.strip().lower()
        usuario = UsuarioRepository.get_active_by_correo(correo_normalized)

        if not usuario:
            logger.warning(
                "Intento de reset para correo inexistente: %s", correo_normalized
            )
            return False

        if len(new_password) < _PASSWORD_MIN_LENGTH:
            raise ValidationException(
                f"La nueva contraseña debe tener al menos {_PASSWORD_MIN_LENGTH} caracteres"
            )

        user_id: int = usuario.id  # type: ignore[assignment]
        UsuarioRepository.update(user_id, contrasena_hash=hash_password(new_password))
        logger.info(
            "Contraseña reseteada para usuario: %s (id=%s)", correo_normalized, user_id
        )
        return True

    @classmethod
    def validate_token(cls, token: str) -> dict:
        """
        Valida un token JWT y retorna los datos del usuario.

        Verifica:
            1. El token es decodificable (firma válida, no expirado).
            2. El usuario referenciado existe.
            3. El usuario está activo.

        Args:
            token: JWT generado por authenticate().

        Returns:
            {"usuario": Usuario, "payload": dict} con el usuario y el contenido del token.

        Raises:
            UnauthorizedException: Si el token es inválido, expirado o el usuario
                no existe / está inactivo.
        """
        try:
            payload = decode_access_token(token)
            user_id = int(payload.get("sub", 0))
            usuario = UsuarioRepository.get_by_id(user_id)
            if not usuario or not usuario.activo:
                raise UnauthorizedException("Usuario no válido o inactivo")
            return {"usuario": usuario, "payload": payload}
        except UnauthorizedException:
            raise
        except Exception as e:
            logger.warning("Token inválido: %s", str(e))
            raise UnauthorizedException("Token inválido o expirado")

    @classmethod
    def get_usuario_by_id(cls, usuario_id: int) -> Usuario:
        """Obtiene un usuario por ID. Lanza NotFoundException si no existe."""
        return UsuarioRepository.get_by_id_or_fail(usuario_id)

    @classmethod
    def ensure_default_user_exists(cls):
        """
        Garantiza que el usuario admin por defecto exista en la BD.

        Credenciales: admin@panaderiaduran.com / Admin123!
        Se llama desde el bootstrap de la app. Es idempotente: si el usuario
        ya existe, no hace nada.
        """
        default_email = "admin@panaderiaduran.com"
        logger.info("Verificando existencia de usuario por defecto: %s", default_email)

        existing = UsuarioRepository.get_by_correo(default_email)
        if existing:
            logger.info("Usuario por defecto ya existe — id=%s", existing.id)
            return

        logger.info("Creando usuario por defecto: %s", default_email)
        hashed = hash_password("Admin123!")
        usuario = UsuarioRepository.create(
            nombre="Administrador",
            correo=default_email,
            contrasena_hash=hashed,
            rol_id=1,
        )
        logger.info("Usuario por defecto creado — id=%s", usuario.id)
