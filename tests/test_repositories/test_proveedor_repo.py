import pytest

from dev.repositories.proveedor_repo import ProveedorRepository


class TestProveedorRepository:
    def test_create(self, seed_basic):
        prov = ProveedorRepository.create(nombre="Proveedor Test")
        assert prov.id is not None
        assert prov.nombre == "Proveedor Test"

    def test_search_by_nombre(self, seed_basic):
        ProveedorRepository.create(nombre="Distribuidora ABC")
        results = ProveedorRepository.search_by_nombre("ABC")
        assert len(results) >= 1

    def test_search_with_filters(self, seed_basic):
        ProveedorRepository.create(nombre="Harinas SA")
        results, total = ProveedorRepository.search_with_filters(query="Harinas")
        assert total >= 1

    def test_search_with_filters_vacio(self, seed_basic):
        ProveedorRepository.create(nombre="Test Prov")
        results, total = ProveedorRepository.search_with_filters()
        assert total >= 1
