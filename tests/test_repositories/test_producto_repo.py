import pytest
from decimal import Decimal

from dev.repositories.producto_repo import ProductoRepository


class TestProductoRepository:
    def test_search_by_nombre(self, seed_producto):
        results = ProductoRepository.search_by_nombre("harina")
        assert len(results) >= 1

    def test_search_by_nombre_sin_resultado(self, seed_producto):
        results = ProductoRepository.search_by_nombre("xyznoexist")
        assert len(results) == 0

    def test_get_by_categoria(self, seed_producto):
        results = ProductoRepository.get_by_categoria(seed_producto["cat_id"])
        assert len(results) >= 1

    def test_update_stock_incrementa(self, seed_producto):
        updated = ProductoRepository.update_stock(
            seed_producto["producto_id"], Decimal("50")
        )
        assert updated.stock_actual == Decimal("50")

    def test_update_stock_decrementa(self, seed_producto):
        ProductoRepository.update_stock(
            seed_producto["producto_id"], Decimal("100")
        )
        updated = ProductoRepository.update_stock(
            seed_producto["producto_id"], Decimal("-30")
        )
        assert updated.stock_actual == Decimal("70")

    def test_update_stock_producto_no_existe(self, seed_basic):
        result = ProductoRepository.update_stock(999, Decimal("10"))
        assert result is None

    def test_get_below_min_stock(self, seed_producto):
        ProductoRepository.update_stock(
            seed_producto["producto_id"], Decimal("3")
        )
        results = ProductoRepository.get_below_min_stock()
        assert any(p.id == seed_producto["producto_id"] for p in results)

    def test_search_with_filters(self, seed_producto):
        results, total = ProductoRepository.search_with_filters(
            query="harina",
            categoria_id=seed_producto["cat_id"],
        )
        assert total >= 1

    def test_search_with_filters_paginacion(self, seed_producto):
        results, total = ProductoRepository.search_with_filters(
            offset=0,
            limit=1,
        )
        assert len(results) <= 1
