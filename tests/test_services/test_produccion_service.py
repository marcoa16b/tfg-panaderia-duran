import pytest
from datetime import date, timedelta
from decimal import Decimal

from dev.core.exceptions import ValidationException
from dev.services.produccion_service import ProduccionService
from dev.services.receta_service import RecetaService


class TestProduccionServiceRegistrar:
    def _crear_receta_con_stock(self, seed_producto):
        from dev.repositories.producto_repo import ProductoRepository

        ProductoRepository.update_stock(
            seed_producto["producto_id"], Decimal("5000")
        )
        producto_final = ProductoRepository.create(
            nombre="Pan de leche",
            categoria_id=seed_producto["cat_id"],
            unidad_medida_id=seed_producto["um_id"],
            stock_actual=Decimal("0"),
        )
        from dev.repositories.entrada_repo import EntradaRepository

        EntradaRepository.create_with_lotes(
            entrada_data={
                "tipo_id": seed_producto["tipo_compra_id"],
                "fecha": date.today(),
            },
            lotes_data=[
                {
                    "producto_id": seed_producto["producto_id"],
                    "cantidad": Decimal("5000"),
                }
            ],
        )
        receta = RecetaService.create(
            nombre="Pan de leche test",
            producto_id=producto_final.id,
            ingredientes=[
                {"producto_id": seed_producto["producto_id"], "cantidad": Decimal("500")},
            ],
        )
        return receta

    def test_registrar_produccion_valida(self, seed_producto):
        receta = self._crear_receta_con_stock(seed_producto)
        result = ProduccionService.registrar_produccion(
            receta_id=receta["receta"].id,
            fecha=date.today(),
            cantidad_producida=Decimal("10"),
        )
        assert result["produccion"].id is not None
        assert len(result["detalles"]) >= 1

    def test_registrar_produccion_cantidad_cero(self, seed_producto):
        with pytest.raises(ValidationException, match="mayor a 0"):
            ProduccionService.registrar_produccion(
                receta_id=1,
                fecha=date.today(),
                cantidad_producida=Decimal("0"),
            )

    def test_registrar_produccion_insumos_insuficientes(self, seed_producto):
        receta = self._crear_receta_con_stock(seed_producto)
        with pytest.raises(ValidationException, match="insuficiente"):
            ProduccionService.registrar_produccion(
                receta_id=receta["receta"].id,
                fecha=date.today(),
                cantidad_producida=Decimal("9999"),
            )

    def test_registrar_produccion_descuenta_stock(self, seed_producto):
        receta = self._crear_receta_con_stock(seed_producto)
        ProduccionService.registrar_produccion(
            receta_id=receta["receta"].id,
            fecha=date.today(),
            cantidad_producida=Decimal("2"),
        )
        from dev.services.producto_service import ProductoService

        stock = ProductoService.get_current_stock(seed_producto["producto_id"])
        assert stock == Decimal("4000")


class TestProduccionServiceQueries:
    def test_get_by_fecha_range_invalido(self, seed_basic):
        with pytest.raises(ValidationException, match="posterior"):
            ProduccionService.get_by_fecha_range(
                date.today() + timedelta(days=1),
                date.today() - timedelta(days=1),
            )
