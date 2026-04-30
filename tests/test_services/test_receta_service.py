import pytest
from decimal import Decimal

from dev.core.exceptions import ValidationException, NotFoundException
from dev.services.receta_service import RecetaService


class TestRecetaServiceCreate:
    def test_create_receta_valida(self, seed_producto):
        from dev.repositories.producto_repo import ProductoRepository

        producto_final = ProductoRepository.create(
            nombre="Pan de leche",
            categoria_id=seed_producto["cat_id"],
            unidad_medida_id=seed_producto["um_id"],
            stock_actual=Decimal("0"),
        )
        result = RecetaService.create(
            nombre="Pan de leche clásico",
            producto_id=producto_final.id,
            ingredientes=[
                {"producto_id": seed_producto["producto_id"], "cantidad": Decimal("500")},
            ],
        )
        assert result["receta"].id is not None
        assert len(result["detalles"]) == 1

    def test_create_sin_ingredientes(self, seed_producto):
        with pytest.raises(ValidationException, match="ingrediente"):
            RecetaService.create(
                nombre="Receta vacía",
                producto_id=seed_producto["producto_id"],
                ingredientes=[],
            )

    def test_create_nombre_corto(self, seed_producto):
        with pytest.raises(ValidationException, match="nombre"):
            RecetaService.create(
                nombre="R",
                producto_id=seed_producto["producto_id"],
                ingredientes=[
                    {"producto_id": seed_producto["producto_id"], "cantidad": Decimal("10")},
                ],
            )

    def test_create_producto_inexistente(self, seed_producto):
        with pytest.raises(ValidationException, match="no existe"):
            RecetaService.create(
                nombre="Receta test",
                producto_id=999,
                ingredientes=[
                    {"producto_id": seed_producto["producto_id"], "cantidad": Decimal("10")},
                ],
            )

    def test_create_cantidad_cero(self, seed_producto):
        with pytest.raises(ValidationException, match="mayor a 0"):
            RecetaService.create(
                nombre="Receta test",
                producto_id=seed_producto["producto_id"],
                ingredientes=[
                    {"producto_id": seed_producto["producto_id"], "cantidad": Decimal("0")},
                ],
            )


class TestRecetaServiceCalcular:
    def test_calcular_insumos_necesarios(self, seed_producto):
        from dev.repositories.producto_repo import ProductoRepository

        producto_final = ProductoRepository.create(
            nombre="Pan",
            categoria_id=seed_producto["cat_id"],
            unidad_medida_id=seed_producto["um_id"],
            stock_actual=Decimal("0"),
        )
        result = RecetaService.create(
            nombre="Pan test",
            producto_id=producto_final.id,
            ingredientes=[
                {"producto_id": seed_producto["producto_id"], "cantidad": Decimal("500")},
            ],
        )
        insumos = RecetaService.calcular_insumos_necesarios(
            result["receta"].id, Decimal("10")
        )
        assert len(insumos) == 1
        assert insumos[0]["cantidad_necesaria"] == Decimal("5000")

    def test_verificar_insumos_disponibles(self, seed_producto):
        from dev.repositories.producto_repo import ProductoRepository

        ProductoRepository.update_stock(
            seed_producto["producto_id"], Decimal("5000")
        )
        producto_final = ProductoRepository.create(
            nombre="Pan",
            categoria_id=seed_producto["cat_id"],
            unidad_medida_id=seed_producto["um_id"],
            stock_actual=Decimal("0"),
        )
        result = RecetaService.create(
            nombre="Pan test",
            producto_id=producto_final.id,
            ingredientes=[
                {"producto_id": seed_producto["producto_id"], "cantidad": Decimal("500")},
            ],
        )
        disp = RecetaService.verificar_insumos_disponibles(
            result["receta"].id, Decimal("10")
        )
        assert disp["disponible"] is True
        assert disp["detalle"][0]["suficiente"] is True

    def test_verificar_insumos_insuficientes(self, seed_producto):
        from dev.repositories.producto_repo import ProductoRepository

        ProductoRepository.update_stock(
            seed_producto["producto_id"], Decimal("100")
        )
        producto_final = ProductoRepository.create(
            nombre="Pan",
            categoria_id=seed_producto["cat_id"],
            unidad_medida_id=seed_producto["um_id"],
            stock_actual=Decimal("0"),
        )
        result = RecetaService.create(
            nombre="Pan test",
            producto_id=producto_final.id,
            ingredientes=[
                {"producto_id": seed_producto["producto_id"], "cantidad": Decimal("500")},
            ],
        )
        disp = RecetaService.verificar_insumos_disponibles(
            result["receta"].id, Decimal("10")
        )
        assert disp["disponible"] is False
        assert disp["detalle"][0]["faltante"] == Decimal("4900")


class TestRecetaServiceSearch:
    def test_search(self, seed_producto):
        RecetaService.create(
            nombre="Receta especial",
            producto_id=seed_producto["producto_id"],
            ingredientes=[
                {"producto_id": seed_producto["producto_id"], "cantidad": Decimal("100")},
            ],
        )
        results = RecetaService.search("especial")
        assert len(results) >= 1

    def test_search_corto(self, seed_basic):
        with pytest.raises(ValidationException, match="búsqueda"):
            RecetaService.search("x")


class TestRecetaServiceUpdate:
    def test_update_ingredientes(self, seed_producto):
        from dev.repositories.producto_repo import ProductoRepository

        producto_final = ProductoRepository.create(
            nombre="Pan",
            categoria_id=seed_producto["cat_id"],
            unidad_medida_id=seed_producto["um_id"],
            stock_actual=Decimal("0"),
        )
        result = RecetaService.create(
            nombre="Receta test",
            producto_id=producto_final.id,
            ingredientes=[
                {"producto_id": seed_producto["producto_id"], "cantidad": Decimal("100")},
            ],
        )
        updated = RecetaService.update_ingredientes(
            result["receta"].id,
            [{"producto_id": seed_producto["producto_id"], "cantidad": Decimal("200")}],
        )
        assert len(updated["detalles"]) == 1
        assert updated["detalles"][0].cantidad == Decimal("200")

    def test_deactivate(self, seed_producto):
        result = RecetaService.create(
            nombre="Receta a desactivar",
            producto_id=seed_producto["producto_id"],
            ingredientes=[
                {"producto_id": seed_producto["producto_id"], "cantidad": Decimal("10")},
            ],
        )
        ok = RecetaService.deactivate(result["receta"].id)
        assert ok is True
