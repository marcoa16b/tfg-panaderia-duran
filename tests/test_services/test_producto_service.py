import pytest
from decimal import Decimal

from dev.core.exceptions import ValidationException, NotFoundException
from dev.services.producto_service import ProductoService


class TestProductoServiceCreate:
    def test_create_producto_valido(self, seed_basic):
        p = ProductoService.create(
            nombre="Harina integral",
            categoria_id=seed_basic["cat_id"],
            unidad_medida_id=seed_basic["um_id"],
            stock_minimo=Decimal("5"),
        )
        assert p.id is not None
        assert p.nombre == "Harina integral"
        assert p.stock_actual == Decimal("0")

    def test_create_nombre_corto(self, seed_basic):
        with pytest.raises(ValidationException, match="nombre"):
            ProductoService.create(
                nombre="H",
                categoria_id=seed_basic["cat_id"],
                unidad_medida_id=seed_basic["um_id"],
            )

    def test_create_stock_minimo_negativo(self, seed_basic):
        with pytest.raises(ValidationException, match="negativo"):
            ProductoService.create(
                nombre="Producto test",
                categoria_id=seed_basic["cat_id"],
                unidad_medida_id=seed_basic["um_id"],
                stock_minimo=Decimal("-5"),
            )

    def test_create_categoria_inexistente(self, seed_basic):
        with pytest.raises(ValidationException, match="[Cc]ategoría"):
            ProductoService.create(
                nombre="Producto test",
                categoria_id=999,
                unidad_medida_id=seed_basic["um_id"],
            )

    def test_create_unidad_inexistente(self, seed_basic):
        with pytest.raises(ValidationException, match="[Uu]nidad"):
            ProductoService.create(
                nombre="Producto test",
                categoria_id=seed_basic["cat_id"],
                unidad_medida_id=999,
            )


class TestProductoServiceUpdate:
    def test_update_nombre(self, seed_producto):
        p = ProductoService.update(
            seed_producto["producto_id"], nombre="Harina actualizada"
        )
        assert p.nombre == "Harina actualizada"

    def test_update_nombre_corto(self, seed_producto):
        with pytest.raises(ValidationException, match="nombre"):
            ProductoService.update(
                seed_producto["producto_id"], nombre="X"
            )

    def test_update_protege_stock_actual(self, seed_producto):
        p = ProductoService.update(
            seed_producto["producto_id"],
            stock_actual=Decimal("999"),
            nombre="Test",
        )
        assert p.stock_actual == Decimal("0")


class TestProductoServiceDeactivate:
    def test_deactivate(self, seed_producto):
        result = ProductoService.deactivate(seed_producto["producto_id"])
        assert result is True

    def test_deactivate_no_existe(self, seed_basic):
        with pytest.raises(NotFoundException):
            ProductoService.deactivate(999)


class TestProductoServiceSearch:
    def test_search(self, seed_producto):
        results = ProductoService.search("harina")
        assert len(results) >= 1

    def test_search_corto(self, seed_basic):
        with pytest.raises(ValidationException, match="búsqueda"):
            ProductoService.search("h")

    def test_get_productos_below_min_stock(self, seed_producto):
        from dev.repositories.producto_repo import ProductoRepository

        ProductoRepository.update_stock(
            seed_producto["producto_id"], Decimal("5")
        )
        productos = ProductoService.get_productos_below_min_stock()
        assert any(p.id == seed_producto["producto_id"] for p in productos)
