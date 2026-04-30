import pytest
from datetime import date
from decimal import Decimal

from dev.repositories.salida_repo import SalidaRepository, DetalleSalidaRepository
from dev.repositories.entrada_repo import EntradaRepository


class TestSalidaRepository:
    def test_create_with_detalles(self, seed_entrada):
        result = SalidaRepository.create_with_detalles(
            salida_data={
                "tipo_id": seed_entrada["tipo_consumo_id"],
                "fecha": date.today(),
            },
            detalles_data=[
                {
                    "lote_id": seed_entrada["lote_id"],
                    "cantidad": Decimal("10"),
                    "motivo": "Test",
                }
            ],
        )
        assert result["salida"].id is not None
        assert len(result["detalles"]) == 1

    def test_get_with_detalles(self, seed_entrada):
        created = SalidaRepository.create_with_detalles(
            salida_data={
                "tipo_id": seed_entrada["tipo_consumo_id"],
                "fecha": date.today(),
            },
            detalles_data=[
                {
                    "lote_id": seed_entrada["lote_id"],
                    "cantidad": Decimal("5"),
                }
            ],
        )
        result = SalidaRepository.get_with_detalles(created["salida"].id)
        assert result is not None
        assert len(result["detalles"]) == 1

    def test_get_with_detalles_no_existe(self, seed_basic):
        assert SalidaRepository.get_with_detalles(999) is None


class TestDetalleSalidaRepository:
    def test_get_by_lote(self, seed_entrada):
        SalidaRepository.create_with_detalles(
            salida_data={
                "tipo_id": seed_entrada["tipo_consumo_id"],
                "fecha": date.today(),
            },
            detalles_data=[
                {
                    "lote_id": seed_entrada["lote_id"],
                    "cantidad": Decimal("10"),
                }
            ],
        )
        detalles = DetalleSalidaRepository.get_by_lote(seed_entrada["lote_id"])
        assert len(detalles) >= 1
