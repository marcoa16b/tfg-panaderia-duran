import pytest
from decimal import Decimal

from dev.core.exceptions import NotFoundException
from dev.repositories.base_repository import BaseRepository
from dev.models.models import Rol


class RolRepository(BaseRepository[Rol]):
    model = Rol


class TestBaseRepositoryCRUD:
    def test_create(self, seed_basic):
        rol = RolRepository.create(nombre="TestRol", descripcion="Desc")
        assert rol.id is not None
        assert rol.nombre == "TestRol"

    def test_get_by_id(self, seed_basic):
        rol = RolRepository.create(nombre="GetRol")
        found = RolRepository.get_by_id(rol.id)
        assert found is not None
        assert found.nombre == "GetRol"

    def test_get_by_id_no_existe(self, seed_basic):
        assert RolRepository.get_by_id(999) is None

    def test_get_by_id_or_fail(self, seed_basic):
        rol = RolRepository.create(nombre="OrFailRol")
        found = RolRepository.get_by_id_or_fail(rol.id)
        assert found.id == rol.id

    def test_get_by_id_or_fail_not_found(self, seed_basic):
        with pytest.raises(NotFoundException):
            RolRepository.get_by_id_or_fail(999)

    def test_get_all(self, seed_basic):
        RolRepository.create(nombre="Rol1")
        RolRepository.create(nombre="Rol2")
        roles = RolRepository.get_all()
        assert len(roles) >= 2

    def test_get_paginated(self, seed_basic):
        for i in range(5):
            RolRepository.create(nombre=f"PagRol{i}")
        results, total = RolRepository.get_paginated(offset=0, limit=3)
        assert len(results) == 3
        assert total >= 5

    def test_update(self, seed_basic):
        rol = RolRepository.create(nombre="ToUpdate")
        updated = RolRepository.update(rol.id, nombre="Updated")
        assert updated.nombre == "Updated"

    def test_update_no_existe(self, seed_basic):
        with pytest.raises(NotFoundException):
            RolRepository.update(999, nombre="Nope")

    def test_soft_delete(self, seed_basic):
        rol = RolRepository.create(nombre="ToDelete")
        assert RolRepository.soft_delete(rol.id) is True
        found = RolRepository.get_by_id(rol.id)
        assert found.activo is False

    def test_soft_delete_no_existe(self, seed_basic):
        with pytest.raises(NotFoundException):
            RolRepository.soft_delete(999)

    def test_count(self, seed_basic):
        RolRepository.create(nombre="CountRol")
        count = RolRepository.count()
        assert count >= 1

    def test_exists(self, seed_basic):
        rol = RolRepository.create(nombre="ExistsRol")
        assert RolRepository.exists(rol.id) is True
        assert RolRepository.exists(999) is False
