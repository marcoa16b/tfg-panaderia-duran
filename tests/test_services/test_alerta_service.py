import pytest
from datetime import date, timedelta
from decimal import Decimal

from dev.core.exceptions import ValidationException, NotFoundException
from dev.services.alerta_service import AlertaService


class TestAlertaServiceBajoStock:
    def test_detectar_bajo_stock(self, seed_producto):
        from dev.repositories.producto_repo import ProductoRepository

        ProductoRepository.update_stock(
            seed_producto["producto_id"], Decimal("3")
        )
        alertas = AlertaService.detectar_bajo_stock()
        assert len(alertas) >= 1
        assert any(seed_producto["producto_id"] == a.producto_id for a in alertas)

    def test_detectar_bajo_stock_deduplicacion(self, seed_producto):
        from dev.repositories.producto_repo import ProductoRepository

        ProductoRepository.update_stock(
            seed_producto["producto_id"], Decimal("3")
        )
        alertas1 = AlertaService.detectar_bajo_stock()
        alertas2 = AlertaService.detectar_bajo_stock()
        assert len(alertas2) == 0


class TestAlertaServiceVencimiento:
    def test_detectar_proximos_a_vencer(self, seed_producto):
        from dev.repositories.entrada_repo import EntradaRepository

        EntradaRepository.create_with_lotes(
            entrada_data={
                "tipo_id": seed_producto["tipo_compra_id"],
                "fecha": date.today(),
            },
            lotes_data=[
                {
                    "producto_id": seed_producto["producto_id"],
                    "cantidad": Decimal("50"),
                    "fecha_vencimiento": date.today() + timedelta(days=3),
                }
            ],
        )
        alertas = AlertaService.detectar_proximos_a_vencer(dias_limite=7)
        assert len(alertas) >= 1

    def test_detectar_dias_limite_invalido(self, seed_basic):
        with pytest.raises(ValidationException, match="al menos 1"):
            AlertaService.detectar_proximos_a_vencer(dias_limite=0)


class TestAlertaServiceGestion:
    def test_marcar_leida(self, seed_producto):
        from dev.repositories.producto_repo import ProductoRepository

        ProductoRepository.update_stock(
            seed_producto["producto_id"], Decimal("0")
        )
        alertas = AlertaService.detectar_bajo_stock()
        assert len(alertas) >= 1
        AlertaService.marcar_leida(alertas[0].id)
        count = AlertaService.count_activas()
        assert count == 0

    def test_marcar_leida_no_existe(self, seed_basic):
        with pytest.raises(NotFoundException):
            AlertaService.marcar_leida(999)

    def test_marcar_todas_leidas(self, seed_producto):
        from dev.repositories.producto_repo import ProductoRepository

        ProductoRepository.update_stock(
            seed_producto["producto_id"], Decimal("0")
        )
        AlertaService.detectar_bajo_stock()
        count = AlertaService.marcar_todas_leidas()
        assert count >= 1

    def test_ejecutar_deteccion_completa(self, seed_producto):
        from dev.repositories.producto_repo import ProductoRepository

        ProductoRepository.update_stock(
            seed_producto["producto_id"], Decimal("0")
        )
        result = AlertaService.ejecutar_deteccion_completa()
        assert "bajo_stock" in result
        assert "proximos_vencer" in result
        assert "total_nuevas" in result
