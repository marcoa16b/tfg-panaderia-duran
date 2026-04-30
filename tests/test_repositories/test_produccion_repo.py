import pytest
from datetime import date
from decimal import Decimal

from dev.repositories.produccion_repo import ProduccionRepository, ProduccionDetalleRepository


class TestProduccionRepository:
    def test_create_with_detalles(self, seed_producto):
        from dev.repositories.entrada_repo import EntradaRepository

        EntradaRepository.create_with_lotes(
            entrada_data={
                "tipo_id": seed_producto["tipo_compra_id"],
                "fecha": date.today(),
            },
            lotes_data=[
                {
                    "producto_id": seed_producto["producto_id"],
                    "cantidad": Decimal("1000"),
                }
            ],
        )
        from dev.repositories.entrada_repo import LoteRepository

        lote = LoteRepository.get_by_producto(seed_producto["producto_id"])[0]

        result = ProduccionRepository.create_with_detalles(
            produccion_data={
                "receta_id": 1,
                "fecha": date.today(),
                "cantidad_producida": Decimal("10"),
            },
            detalles_data=[
                {
                    "lote_id": lote.id,
                    "cantidad": Decimal("500"),
                }
            ],
        )
        assert result["produccion"].id is not None
        assert len(result["detalles"]) == 1

    def test_get_with_detalles(self, seed_producto):
        from dev.repositories.entrada_repo import EntradaRepository, LoteRepository

        EntradaRepository.create_with_lotes(
            entrada_data={
                "tipo_id": seed_producto["tipo_compra_id"],
                "fecha": date.today(),
            },
            lotes_data=[
                {
                    "producto_id": seed_producto["producto_id"],
                    "cantidad": Decimal("1000"),
                }
            ],
        )
        lote = LoteRepository.get_by_producto(seed_producto["producto_id"])[0]

        created = ProduccionRepository.create_with_detalles(
            produccion_data={
                "receta_id": 1,
                "fecha": date.today(),
                "cantidad_producida": Decimal("5"),
            },
            detalles_data=[
                {
                    "lote_id": lote.id,
                    "cantidad": Decimal("100"),
                }
            ],
        )
        result = ProduccionRepository.get_with_detalles(created["produccion"].id)
        assert result is not None
        assert len(result["detalles"]) == 1

    def test_get_with_detalles_no_existe(self, seed_basic):
        assert ProduccionRepository.get_with_detalles(999) is None


class TestProduccionDetalleRepository:
    def test_get_by_lote(self, seed_producto):
        from dev.repositories.entrada_repo import EntradaRepository

        EntradaRepository.create_with_lotes(
            entrada_data={
                "tipo_id": seed_producto["tipo_compra_id"],
                "fecha": date.today(),
            },
            lotes_data=[
                {
                    "producto_id": seed_producto["producto_id"],
                    "cantidad": Decimal("1000"),
                }
            ],
        )
        from dev.repositories.entrada_repo import LoteRepository

        lote = LoteRepository.get_by_producto(seed_producto["producto_id"])[0]

        ProduccionRepository.create_with_detalles(
            produccion_data={
                "receta_id": 1,
                "fecha": date.today(),
                "cantidad_producida": Decimal("3"),
            },
            detalles_data=[
                {
                    "lote_id": lote.id,
                    "cantidad": Decimal("200"),
                }
            ],
        )
        detalles = ProduccionDetalleRepository.get_by_lote(lote.id)
        assert len(detalles) >= 1
