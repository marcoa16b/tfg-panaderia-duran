import pytest
from unittest.mock import patch, MagicMock

from dev.core.exceptions import (
    ValidationException,
    DuplicateException,
    UnauthorizedException,
    NotFoundException,
)
from dev.services.auth_service import AuthService
from dev.core.security import hash_password, verify_password, create_access_token, decode_access_token


class TestSecurity:
    def test_hash_and_verify_password(self):
        hashed = hash_password("Admin123!")
        assert verify_password("Admin123!", hashed)
        assert not verify_password("wrong", hashed)

    def test_create_and_decode_token(self):
        token = create_access_token({"sub": "1", "correo": "a@b.com", "rol_id": 1})
        payload = decode_access_token(token)
        assert payload["sub"] == "1"
        assert payload["correo"] == "a@b.com"
        assert payload["rol_id"] == 1


class TestAuthServiceRegister:
    def test_register_valid_user(self, seed_basic):
        user = AuthService.register(
            nombre="Nuevo Usuario",
            correo="nuevo@test.com",
            password="Password1!",
            rol_id=seed_basic["rol_id"],
        )
        assert user.id is not None
        assert user.correo == "nuevo@test.com"
        assert user.nombre == "Nuevo Usuario"
        assert verify_password("Password1!", user.contrasena_hash)

    def test_register_nombre_corto(self, seed_basic):
        with pytest.raises(ValidationException, match="nombre"):
            AuthService.register(
                nombre="A",
                correo="test@test.com",
                password="Password1!",
                rol_id=seed_basic["rol_id"],
            )

    def test_register_email_invalido(self, seed_basic):
        with pytest.raises(ValidationException, match="correo"):
            AuthService.register(
                nombre="Test User",
                correo="no-es-email",
                password="Password1!",
                rol_id=seed_basic["rol_id"],
            )

    def test_register_password_corto(self, seed_basic):
        with pytest.raises(ValidationException, match="contraseña"):
            AuthService.register(
                nombre="Test User",
                correo="test@test.com",
                password="123",
                rol_id=seed_basic["rol_id"],
            )

    def test_register_email_duplicado(self, seed_basic):
        AuthService.register(
            nombre="Primero",
            correo="dup@test.com",
            password="Password1!",
            rol_id=seed_basic["rol_id"],
        )
        with pytest.raises(DuplicateException):
            AuthService.register(
                nombre="Segundo",
                correo="dup@test.com",
                password="Password1!",
                rol_id=seed_basic["rol_id"],
            )

    def test_register_normaliza_email(self, seed_basic):
        user = AuthService.register(
            nombre="Test",
            correo="  UPPER@TEST.COM  ",
            password="Password1!",
            rol_id=seed_basic["rol_id"],
        )
        assert user.correo == "upper@test.com"


class TestAuthServiceAuthenticate:
    def test_authenticate_success(self, seed_basic):
        result = AuthService.authenticate("admin@test.com", "Admin123!")
        assert result is not None
        assert result["usuario"].correo == "admin@test.com"
        assert "token" in result

    def test_authenticate_user_not_found(self, seed_basic):
        result = AuthService.authenticate("noexiste@test.com", "Admin123!")
        assert result is None

    def test_authenticate_wrong_password(self, seed_basic):
        result = AuthService.authenticate("admin@test.com", "wrongpassword")
        assert result is None

    def test_authenticate_normaliza_email(self, seed_basic):
        AuthService.register(
            nombre="Norm",
            correo="norm@test.com",
            password="Password1!",
            rol_id=seed_basic["rol_id"],
        )
        result = AuthService.authenticate("  NORM@TEST.COM  ", "Password1!")
        assert result is not None


class TestAuthServiceChangePassword:
    def test_change_password_success(self, seed_basic):
        AuthService.change_password(seed_basic["admin_id"], "Admin123!", "NewPass123!")
        result = AuthService.authenticate("admin@test.com", "NewPass123!")
        assert result is not None

    def test_change_password_wrong_current(self, seed_basic):
        with pytest.raises(UnauthorizedException, match="incorrecta"):
            AuthService.change_password(seed_basic["admin_id"], "wrong", "NewPass123!")

    def test_change_password_new_too_short(self, seed_basic):
        with pytest.raises(ValidationException, match="contraseña"):
            AuthService.change_password(seed_basic["admin_id"], "Admin123!", "abc")


class TestAuthServiceResetPassword:
    def test_reset_password_success(self, seed_basic):
        result = AuthService.reset_password("admin@test.com", "ResetPass123!")
        assert result is True
        auth = AuthService.authenticate("admin@test.com", "ResetPass123!")
        assert auth is not None

    def test_reset_password_email_not_found(self, seed_basic):
        result = AuthService.reset_password("noexiste@test.com", "ResetPass123!")
        assert result is False

    def test_reset_password_too_short(self, seed_basic):
        with pytest.raises(ValidationException, match="contraseña"):
            AuthService.reset_password("admin@test.com", "abc")


class TestAuthServiceValidateToken:
    def test_validate_valid_token(self, seed_basic):
        auth_result = AuthService.authenticate("admin@test.com", "Admin123!")
        validated = AuthService.validate_token(auth_result["token"])
        assert validated["usuario"].correo == "admin@test.com"

    def test_validate_invalid_token(self, seed_basic):
        with pytest.raises(UnauthorizedException):
            AuthService.validate_token("invalid.token.here")
