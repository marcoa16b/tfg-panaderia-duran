import pytest
from datetime import date
from decimal import Decimal

from dev.services.reporte_service import ReporteService
from dev.core.exceptions import ValidationException


class TestReporteServiceExistencias:
    def test_get_existencias_actuales(self, seed_producto):
        from dev.repositories.producto_repo import ProductoRepository

        ProductoRepository.update_stock(
            seed_producto["producto_id"], Decimal("50")
        )
        result = ReporteService.get_existencias_actuales()
        assert len(result) >= 1
        p = result[0]
        assert "producto_id" in p
        assert "stock_actual" in p
        assert "bajo_stock" in p


class TestReporteServicePerdidas:
    def test_get_perdidas_sin_datos(self, seed_basic):
        result = ReporteService.get_perdidas()
        assert result["cantidad_registros"] == 0
        assert result["total_perdida"] == Decimal("0")

    def test_get_perdidas_fechas_invalidas(self, seed_basic):
        with pytest.raises(ValidationException, match="posterior"):
            ReporteService.get_perdidas(
                fecha_inicio=date(2026, 2, 1),
                fecha_fin=date(2026, 1, 1),
            )


class TestReporteServiceDashboard:
    def test_get_resumen_dashboard(self, seed_producto):
        resumen = ReporteService.get_resumen_dashboard()
        assert "total_productos" in resumen
        assert "productos_bajo_stock" in resumen
        assert "entradas_mes" in resumen
        assert "salidas_mes" in resumen
        assert "lotes_por_vencer" in resumen
        assert resumen["total_productos"] >= 1


class TestReporteServiceConsumo:
    def test_get_consumo_anual_sin_datos(self, seed_basic):
        result = ReporteService.get_consumo_anual()
        assert isinstance(result, list)

    def test_get_consumo_anual_anio_especifico(self, seed_basic):
        result = ReporteService.get_consumo_anual(anio=2025)
        assert isinstance(result, list)


class TestReporteServicePeriodos:
    def test_get_entradas_periodo_fechas_invalidas(self, seed_basic):
        with pytest.raises(ValidationException, match="posterior"):
            ReporteService.get_entradas_periodo(
                fecha_inicio=date(2026, 2, 1),
                fecha_fin=date(2026, 1, 1),
            )

    def test_get_salidas_periodo_fechas_invalidas(self, seed_basic):
        with pytest.raises(ValidationException, match="posterior"):
            ReporteService.get_salidas_periodo(
                fecha_inicio=date(2026, 2, 1),
                fecha_fin=date(2026, 1, 1),
            )
