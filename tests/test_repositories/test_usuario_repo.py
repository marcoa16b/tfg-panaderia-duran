import pytest

from dev.repositories.usuario_repo import UsuarioRepository
from dev.core.security import hash_password


class TestUsuarioRepository:
    def test_get_by_correo(self, seed_basic):
        user = UsuarioRepository.get_by_correo("admin@test.com")
        assert user is not None
        assert user.correo == "admin@test.com"

    def test_get_by_correo_no_existe(self, seed_basic):
        assert UsuarioRepository.get_by_correo("no@existe.com") is None

    def test_get_active_by_correo(self, seed_basic):
        user = UsuarioRepository.get_active_by_correo("admin@test.com")
        assert user is not None

    def test_get_active_by_correo_inactivo(self, seed_basic):
        UsuarioRepository.create(
            nombre="Inactivo",
            correo="inactivo@test.com",
            contrasena_hash="xxx",
            rol_id=seed_basic["rol_id"],
        )
        UsuarioRepository.create(
            nombre="Inactivo",
            correo="inactivo2@test.com",
            contrasena_hash="xxx",
            rol_id=seed_basic["rol_id"],
        )
        uid = UsuarioRepository.get_by_correo("inactivo2@test.com").id
        UsuarioRepository.soft_delete(uid)
        user = UsuarioRepository.get_active_by_correo("inactivo2@test.com")
        assert user is None

    def test_search(self, seed_basic):
        results = UsuarioRepository.search("admin")
        assert len(results) >= 1

    def test_exists_by_correo(self, seed_basic):
        assert UsuarioRepository.exists_by_correo("admin@test.com") is True
        assert UsuarioRepository.exists_by_correo("no@existe.com") is False
