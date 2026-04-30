import pytest
from datetime import date, timedelta
from decimal import Decimal

from dev.repositories.entrada_repo import EntradaRepository, LoteRepository


class TestEntradaRepository:
    def test_create_with_lotes(self, seed_producto):
        result = EntradaRepository.create_with_lotes(
            entrada_data={
                "tipo_id": seed_producto["tipo_compra_id"],
                "fecha": date.today(),
            },
            lotes_data=[
                {
                    "producto_id": seed_producto["producto_id"],
                    "cantidad": Decimal("50"),
                    "codigo_lote": "LT001",
                }
            ],
        )
        assert result["entrada"].id is not None
        assert len(result["lotes"]) == 1
        assert result["lotes"][0].entrada_id == result["entrada"].id

    def test_get_with_lotes(self, seed_producto):
        created = EntradaRepository.create_with_lotes(
            entrada_data={
                "tipo_id": seed_producto["tipo_compra_id"],
                "fecha": date.today(),
            },
            lotes_data=[
                {
                    "producto_id": seed_producto["producto_id"],
                    "cantidad": Decimal("30"),
                }
            ],
        )
        result = EntradaRepository.get_with_lotes(created["entrada"].id)
        assert result is not None
        assert len(result["lotes"]) == 1

    def test_get_with_lotes_no_existe(self, seed_basic):
        assert EntradaRepository.get_with_lotes(999) is None

    def test_get_by_fecha_range(self, seed_producto):
        EntradaRepository.create_with_lotes(
            entrada_data={
                "tipo_id": seed_producto["tipo_compra_id"],
                "fecha": date.today(),
            },
            lotes_data=[
                {
                    "producto_id": seed_producto["producto_id"],
                    "cantidad": Decimal("10"),
                }
            ],
        )
        results = EntradaRepository.get_by_fecha_range(
            date.today() - timedelta(days=1),
            date.today() + timedelta(days=1),
        )
        assert len(results) >= 1


class TestLoteRepository:
    def test_get_by_producto(self, seed_producto):
        EntradaRepository.create_with_lotes(
            entrada_data={
                "tipo_id": seed_producto["tipo_compra_id"],
                "fecha": date.today(),
            },
            lotes_data=[
                {
                    "producto_id": seed_producto["producto_id"],
                    "cantidad": Decimal("25"),
                }
            ],
        )
        lotes = LoteRepository.get_by_producto(seed_producto["producto_id"])
        assert len(lotes) >= 1

    def test_get_proximos_a_vencer(self, seed_producto):
        EntradaRepository.create_with_lotes(
            entrada_data={
                "tipo_id": seed_producto["tipo_compra_id"],
                "fecha": date.today(),
            },
            lotes_data=[
                {
                    "producto_id": seed_producto["producto_id"],
                    "cantidad": Decimal("20"),
                    "fecha_vencimiento": date.today() + timedelta(days=3),
                }
            ],
        )
        lotes = LoteRepository.get_proximos_a_vencer(dias_limite=7)
        assert len(lotes) >= 1
