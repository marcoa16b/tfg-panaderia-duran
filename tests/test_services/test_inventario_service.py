import pytest
from datetime import date, timedelta
from decimal import Decimal

from dev.core.exceptions import ValidationException, NotFoundException
from dev.services.inventario_service import InventarioService


class TestInventarioServiceEntrada:
    def test_registrar_entrada_valida(self, seed_producto):
        result = InventarioService.registrar_entrada(
            tipo_id=seed_producto["tipo_compra_id"],
            fecha=date.today(),
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
        assert result["lotes"][0].cantidad == Decimal("50")

    def test_registrar_entrada_sin_lotes(self, seed_basic):
        with pytest.raises(ValidationException, match="lote"):
            InventarioService.registrar_entrada(
                tipo_id=seed_basic["tipo_compra_id"],
                fecha=date.today(),
                lotes_data=[],
            )

    def test_registrar_entrada_cantidad_cero(self, seed_producto):
        with pytest.raises(ValidationException, match="mayor a 0"):
            InventarioService.registrar_entrada(
                tipo_id=seed_producto["tipo_compra_id"],
                fecha=date.today(),
                lotes_data=[
                    {
                        "producto_id": seed_producto["producto_id"],
                        "cantidad": Decimal("0"),
                    }
                ],
            )

    def test_registrar_entrada_producto_inexistente(self, seed_basic):
        with pytest.raises(ValidationException, match="no existe"):
            InventarioService.registrar_entrada(
                tipo_id=seed_basic["tipo_compra_id"],
                fecha=date.today(),
                lotes_data=[
                    {
                        "producto_id": 999,
                        "cantidad": Decimal("10"),
                    }
                ],
            )

    def test_registrar_entrada_actualiza_stock(self, seed_producto):
        InventarioService.registrar_entrada(
            tipo_id=seed_producto["tipo_compra_id"],
            fecha=date.today(),
            lotes_data=[
                {
                    "producto_id": seed_producto["producto_id"],
                    "cantidad": Decimal("100"),
                }
            ],
        )
        stock = InventarioService.get_stock_producto(seed_producto["producto_id"])
        assert stock["stock_actual"] == Decimal("100")

    def test_get_entrada_with_lotes(self, seed_entrada):
        result = InventarioService.get_entrada_with_lotes(seed_entrada["entrada_id"])
        assert result["entrada"].id == seed_entrada["entrada_id"]
        assert len(result["lotes"]) == 1

    def test_get_entrada_not_found(self, seed_basic):
        with pytest.raises(NotFoundException):
            InventarioService.get_entrada_with_lotes(999)


class TestInventarioServiceSalida:
    def test_registrar_salida_valida(self, seed_entrada):
        result = InventarioService.registrar_salida(
            tipo_id=seed_entrada["tipo_consumo_id"],
            fecha=date.today(),
            detalles_data=[
                {
                    "lote_id": seed_entrada["lote_id"],
                    "cantidad": Decimal("20"),
                    "motivo": "Consumo",
                }
            ],
        )
        assert result["salida"].id is not None
        assert len(result["detalles"]) == 1

    def test_registrar_salida_sin_detalles(self, seed_basic):
        with pytest.raises(ValidationException, match="detalle"):
            InventarioService.registrar_salida(
                tipo_id=seed_basic["tipo_consumo_id"],
                fecha=date.today(),
                detalles_data=[],
            )

    def test_registrar_salida_stock_insuficiente(self, seed_entrada):
        with pytest.raises(ValidationException, match="excede"):
            InventarioService.registrar_salida(
                tipo_id=seed_entrada["tipo_consumo_id"],
                fecha=date.today(),
                detalles_data=[
                    {
                        "lote_id": seed_entrada["lote_id"],
                        "cantidad": Decimal("999"),
                    }
                ],
            )

    def test_registrar_salida_descuenta_stock(self, seed_entrada):
        InventarioService.registrar_salida(
            tipo_id=seed_entrada["tipo_consumo_id"],
            fecha=date.today(),
            detalles_data=[
                {
                    "lote_id": seed_entrada["lote_id"],
                    "cantidad": Decimal("30"),
                }
            ],
        )
        stock = InventarioService.get_stock_producto(seed_entrada["producto_id"])
        assert stock["stock_actual"] == Decimal("70")


class TestInventarioServiceLotes:
    def test_get_lotes_proximos_a_vencer(self, seed_producto):
        from dev.repositories.entrada_repo import EntradaRepository

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
        lotes = InventarioService.get_lotes_proximos_a_vencer(dias_limite=7)
        assert len(lotes) >= 1

    def test_get_lotes_proximos_dias_invalido(self, seed_basic):
        with pytest.raises(ValidationException, match="al menos 1"):
            InventarioService.get_lotes_proximos_a_vencer(dias_limite=0)


class TestInventarioServiceFechas:
    def test_get_entradas_by_fecha_validas(self, seed_entrada):
        entradas = InventarioService.get_entradas_by_fecha(
            date.today() - timedelta(days=1),
            date.today() + timedelta(days=1),
        )
        assert len(entradas) >= 1

    def test_get_entradas_fecha_invalida(self, seed_basic):
        with pytest.raises(ValidationException, match="posterior"):
            InventarioService.get_entradas_by_fecha(
                date.today() + timedelta(days=1),
                date.today() - timedelta(days=1),
            )
