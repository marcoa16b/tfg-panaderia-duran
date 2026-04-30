import pytest
from decimal import Decimal

from dev.repositories.receta_repo import RecetaRepository, RecetaDetalleRepository


class TestRecetaRepository:
    def test_create_with_detalles(self, seed_producto):
        result = RecetaRepository.create_with_detalles(
            receta_data={
                "nombre": "Receta test",
                "producto_id": seed_producto["producto_id"],
            },
            detalles_data=[
                {
                    "producto_id": seed_producto["producto_id"],
                    "cantidad": Decimal("100"),
                }
            ],
        )
        assert result["receta"].id is not None
        assert len(result["detalles"]) == 1

    def test_get_with_detalles(self, seed_producto):
        created = RecetaRepository.create_with_detalles(
            receta_data={
                "nombre": "Receta WD",
                "producto_id": seed_producto["producto_id"],
            },
            detalles_data=[
                {
                    "producto_id": seed_producto["producto_id"],
                    "cantidad": Decimal("50"),
                }
            ],
        )
        result = RecetaRepository.get_with_detalles(created["receta"].id)
        assert result is not None
        assert len(result["detalles"]) == 1

    def test_get_with_detalles_no_existe(self, seed_basic):
        assert RecetaRepository.get_with_detalles(999) is None

    def test_search_by_nombre(self, seed_producto):
        RecetaRepository.create_with_detalles(
            receta_data={
                "nombre": "Receta especial",
                "producto_id": seed_producto["producto_id"],
            },
            detalles_data=[
                {
                    "producto_id": seed_producto["producto_id"],
                    "cantidad": Decimal("10"),
                }
            ],
        )
        results = RecetaRepository.search_by_nombre("especial")
        assert len(results) >= 1

    def test_update_detalles(self, seed_producto):
        created = RecetaRepository.create_with_detalles(
            receta_data={
                "nombre": "Receta upd",
                "producto_id": seed_producto["producto_id"],
            },
            detalles_data=[
                {
                    "producto_id": seed_producto["producto_id"],
                    "cantidad": Decimal("50"),
                }
            ],
        )
        updated = RecetaRepository.update_detalles(
            created["receta"].id,
            [
                {
                    "producto_id": seed_producto["producto_id"],
                    "cantidad": Decimal("200"),
                }
            ],
        )
        assert len(updated["detalles"]) == 1
        assert updated["detalles"][0].cantidad == Decimal("200")


class TestRecetaDetalleRepository:
    def test_get_by_receta(self, seed_producto):
        created = RecetaRepository.create_with_detalles(
            receta_data={
                "nombre": "Test",
                "producto_id": seed_producto["producto_id"],
            },
            detalles_data=[
                {
                    "producto_id": seed_producto["producto_id"],
                    "cantidad": Decimal("10"),
                }
            ],
        )
        detalles = RecetaDetalleRepository.get_by_receta(created["receta"].id)
        assert len(detalles) >= 1
