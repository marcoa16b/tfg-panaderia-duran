import pytest
from unittest.mock import patch, MagicMock

from dev.states.auth_state import AuthState
from dev.core.exceptions import UnauthorizedException


class TestAuthStateLogin:
    def test_login_campos_vacios(self):
        state = AuthState()
        state.email = ""
        state.password = ""
        result = state.login()
        assert state.error_message != ""
        assert not state.is_authenticated

    def test_login_success(self, seed_basic):
        state = AuthState()
        state.email = "admin@test.com"
        state.password = "Admin123!"
        state.login()
        assert state.is_authenticated is True
        assert state.user_email == "admin@test.com"
        assert state.token != ""
        assert state.password == ""

    def test_login_credenciales_invalidas(self, seed_basic):
        state = AuthState()
        state.email = "admin@test.com"
        state.password = "wrongpassword"
        state.login()
        assert state.is_authenticated is False
        assert "inválidas" in state.error_message.lower() or "inválid" in state.error_message.lower()


class TestAuthStateLogout:
    def test_logout(self, seed_basic):
        state = AuthState()
        state.email = "admin@test.com"
        state.password = "Admin123!"
        state.login()
        assert state.is_authenticated is True
        result = state.logout()
        assert state.is_authenticated is False
        assert state.user_email == ""
        assert state.token == ""


class TestAuthStateCheckAuth:
    def test_check_auth_not_authenticated(self):
        state = AuthState()
        result = state.check_auth()
        assert result is not None

    def test_check_auth_authenticated(self, seed_basic):
        state = AuthState()
        state.email = "admin@test.com"
        state.password = "Admin123!"
        state.login()
        result = state.check_auth()
        assert result is None
