"""
salida_repo.py — Repositorios para salidas de inventario y sus detalles.

Contiene DOS repositorios (relación padre-hijo):

SalidaRepository (tabla: salida_inventario)
    Hereda CRUD genérico y agrega:
    - get_with_detalles: Salida + todos sus DetalleSalidaInventario.
    - get_by_fecha_range: Salidas en un rango de fechas.
    - get_by_tipo: Filtra por tipo (Consumo, Dañado, Vencido, Ajuste negativo).
    - create_with_detalles: Transacción atómica — crea salida + detalles.

DetalleSalidaRepository (tabla: detalle_salida_inventario)
    Hereda CRUD genérico y agrega:
    - get_by_salida: Detalles de una salida específica.
    - get_by_lote: Detalles asociados a un lote (para trazabilidad).

Flujo de datos típico
---------------------
1. Se registra una SalidaInventario (cabecera: tipo, fecha, observaciones).
2. Se crean N DetalleSalidaInventario (cada uno referencia un lote y cantidad).
3. El service layer se encarga de descontar stock de los lotes correspondientes.

Tipos de salida (definidos en seed_data.py):
    - Consumo: Uso en producción.
    - Dañado: Producto dañado o defectuoso.
    - Vencido: Producto que pasó su fecha de vencimiento.
    - Ajuste negativo: Corrección manual de inventario.
"""

import logging
from datetime import date
from typing import Optional

import reflex as rx
from sqlmodel import select

from dev.models.models import DetalleSalidaInventario, SalidaInventario
from dev.repositories.base_repository import BaseRepository

logger = logging.getLogger("dev.repositories.salida")


class SalidaRepository(BaseRepository[SalidaInventario]):
    model = SalidaInventario

    @classmethod
    def get_with_detalles(cls, salida_id: int) -> Optional[dict]:
        """
        Obtiene una salida junto con todos sus detalles.

        Returns:
            {"salida": SalidaInventario, "detalles": list[DetalleSalidaInventario]}
            o None si la salida no existe.
        """
        logger.debug("Obteniendo salida %s con detalles", salida_id)
        with rx.session() as session:
            salida = session.get(SalidaInventario, salida_id)
            if not salida:
                return None
            stmt = select(DetalleSalidaInventario).where(
                DetalleSalidaInventario.salida_id == salida_id,
                DetalleSalidaInventario.activo == True,  # noqa: E712
            )
            detalles = list(session.exec(stmt).all())
            return {"salida": salida, "detalles": detalles}

    @classmethod
    def get_by_fecha_range(
        cls,
        fecha_inicio: date,
        fecha_fin: date,
        only_active: bool = True,
    ) -> list[SalidaInventario]:
        """Filtra salidas por rango de fechas (ambos inclusive)."""
        logger.debug("Buscando salidas entre %s y %s", fecha_inicio, fecha_fin)
        with rx.session() as session:
            stmt = select(SalidaInventario).where(
                SalidaInventario.fecha >= fecha_inicio,
                SalidaInventario.fecha <= fecha_fin,
            )
            if only_active:
                stmt = stmt.where(SalidaInventario.activo == True)  # noqa: E712
            return list(session.exec(stmt).all())

    @classmethod
    def get_by_tipo(
        cls, tipo_id: int, only_active: bool = True
    ) -> list[SalidaInventario]:
        """Salidas filtradas por tipo (Consumo, Dañado, Vencido, etc.)."""
        with rx.session() as session:
            stmt = select(SalidaInventario).where(SalidaInventario.tipo_id == tipo_id)
            if only_active:
                stmt = stmt.where(SalidaInventario.activo == True)  # noqa: E712
            return list(session.exec(stmt).all())

    @classmethod
    def create_with_detalles(
        cls,
        salida_data: dict,
        detalles_data: list[dict],
    ) -> dict:
        """
        Crea una salida y sus detalles en una transacción atómica.
        Usa flush() para obtener el ID antes de crear los detalles.

        Returns:
            {"salida": SalidaInventario, "detalles": list[DetalleSalidaInventario]}
        """
        logger.info("Creando salida con %s detalles", len(detalles_data))
        with rx.session() as session:
            salida = SalidaInventario(**salida_data)
            session.add(salida)
            session.flush()

            detalles = []
            for detalle_dict in detalles_data:
                detalle_dict["salida_id"] = salida.id
                detalle = DetalleSalidaInventario(**detalle_dict)
                session.add(detalle)
                detalles.append(detalle)

            session.commit()
            session.refresh(salida)
            for detalle in detalles:
                session.refresh(detalle)

            logger.info(
                "Salida creada — id=%s con %s detalles", salida.id, len(detalles)
            )
            return {"salida": salida, "detalles": detalles}


class DetalleSalidaRepository(BaseRepository[DetalleSalidaInventario]):
    model = DetalleSalidaInventario

    @classmethod
    def get_by_salida(
        cls, salida_id: int, only_active: bool = True
    ) -> list[DetalleSalidaInventario]:
        """Detalles de una salida específica."""
        logger.debug("Buscando detalles de salida: %s", salida_id)
        with rx.session() as session:
            stmt = select(DetalleSalidaInventario).where(
                DetalleSalidaInventario.salida_id == salida_id
            )
            if only_active:
                stmt = stmt.where(DetalleSalidaInventario.activo == True)  # noqa: E712
            return list(session.exec(stmt).all())

    @classmethod
    def get_by_lote(
        cls, lote_id: int, only_active: bool = True
    ) -> list[DetalleSalidaInventario]:
        """
        Detalles de salida asociados a un lote.
        Útil para trazabilidad: saber cuánto se sacó de un lote específico.
        """
        with rx.session() as session:
            stmt = select(DetalleSalidaInventario).where(
                DetalleSalidaInventario.lote_id == lote_id
            )
            if only_active:
                stmt = stmt.where(DetalleSalidaInventario.activo == True)  # noqa: E712
            return list(session.exec(stmt).all())
