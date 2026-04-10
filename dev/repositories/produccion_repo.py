"""
produccion_repo.py — Repositorios para producción diaria y sus detalles.

Contiene DOS repositorios (relación padre-hijo):

ProduccionRepository (tabla: produccion_diaria)
    Hereda CRUD genérico y agrega:
    - get_with_detalles: Producción + detalles de lotes consumidos.
    - get_by_fecha_range: Producciones en un rango de fechas.
    - get_by_receta: Producciones de una receta específica.
    - create_with_detalles: Transacción atómica — crea producción + detalles.

ProduccionDetalleRepository (tabla: produccion_detalle)
    Hereda CRUD genérico y agrega:
    - get_by_produccion: Detalles de una producción.
    - get_by_lote: Producciones que consumieron un lote (trazabilidad).

Flujo de producción
-------------------
1. Se selecciona una Receta y una cantidad a producir.
2. El service layer calcula los insumos necesarios (ingredientes × cantidad).
3. Se descuentan los insumos de los lotes disponibles (FIFO o manual).
4. Se registra la ProduccionDiaria (cabecera) y los ProduccionDetalle (trazabilidad).

Modelo de datos
---------------
ProduccionDiaria:
    - receta_id: Qué receta se produjo.
    - cantidad_producida: Cuántas unidades se hicieron.
    - usuario_id: Quién registró la producción.

ProduccionDetalle:
    - lote_id: De qué lote se tomó el insumo.
    - cantidad: Cuánto se consumió de ese lote.

Esto permite trazabilidad completa: qué lote se usó para cada producción.
"""

import logging
from datetime import date
from typing import Optional

import reflex as rx
from sqlmodel import select

from dev.models.models import ProduccionDetalle, ProduccionDiaria
from dev.repositories.base_repository import BaseRepository

logger = logging.getLogger("dev.repositories.produccion")


class ProduccionRepository(BaseRepository[ProduccionDiaria]):
    model = ProduccionDiaria

    @classmethod
    def get_with_detalles(cls, produccion_id: int) -> Optional[dict]:
        """
        Obtiene una producción con todos sus detalles de lotes consumidos.

        Returns:
            {"produccion": ProduccionDiaria, "detalles": list[ProduccionDetalle]}
            o None si no existe.
        """
        logger.debug("Obteniendo producción %s con detalles", produccion_id)
        with rx.session() as session:
            produccion = session.get(ProduccionDiaria, produccion_id)
            if not produccion:
                return None
            stmt = select(ProduccionDetalle).where(
                ProduccionDetalle.produccion_id == produccion_id,
                ProduccionDetalle.activo == True,  # noqa: E712
            )
            detalles = list(session.exec(stmt).all())
            return {"produccion": produccion, "detalles": detalles}

    @classmethod
    def get_by_fecha_range(
        cls,
        fecha_inicio: date,
        fecha_fin: date,
        only_active: bool = True,
    ) -> list[ProduccionDiaria]:
        """Producciones en un rango de fechas."""
        logger.debug("Buscando producciones entre %s y %s", fecha_inicio, fecha_fin)
        with rx.session() as session:
            stmt = select(ProduccionDiaria).where(
                ProduccionDiaria.fecha >= fecha_inicio,
                ProduccionDiaria.fecha <= fecha_fin,
            )
            if only_active:
                stmt = stmt.where(ProduccionDiaria.activo == True)  # noqa: E712
            return list(session.exec(stmt).all())

    @classmethod
    def get_by_receta(
        cls, receta_id: int, only_active: bool = True
    ) -> list[ProduccionDiaria]:
        """Producciones de una receta específica."""
        logger.debug("Buscando producciones de la receta: %s", receta_id)
        with rx.session() as session:
            stmt = select(ProduccionDiaria).where(
                ProduccionDiaria.receta_id == receta_id
            )
            if only_active:
                stmt = stmt.where(ProduccionDiaria.activo == True)  # noqa: E712
            return list(session.exec(stmt).all())

    @classmethod
    def create_with_detalles(
        cls,
        produccion_data: dict,
        detalles_data: list[dict],
    ) -> dict:
        """
        Crea una producción y sus detalles en una transacción atómica.

        Args:
            produccion_data: Campos de ProduccionDiaria (receta_id, fecha, cantidad_producida).
            detalles_data: Lista de dicts con lote_id y cantidad consumida.

        Returns:
            {"produccion": ProduccionDiaria, "detalles": list[ProduccionDetalle]}
        """
        logger.info("Creando producción con %s detalles de lote", len(detalles_data))
        with rx.session() as session:
            produccion = ProduccionDiaria(**produccion_data)
            session.add(produccion)
            session.flush()

            detalles = []
            for detalle_dict in detalles_data:
                detalle_dict["produccion_id"] = produccion.id
                detalle = ProduccionDetalle(**detalle_dict)
                session.add(detalle)
                detalles.append(detalle)

            session.commit()
            session.refresh(produccion)
            for detalle in detalles:
                session.refresh(detalle)

            logger.info(
                "Producción creada — id=%s con %s detalles",
                produccion.id,
                len(detalles),
            )
            return {"produccion": produccion, "detalles": detalles}


class ProduccionDetalleRepository(BaseRepository[ProduccionDetalle]):
    model = ProduccionDetalle

    @classmethod
    def get_by_produccion(
        cls, produccion_id: int, only_active: bool = True
    ) -> list[ProduccionDetalle]:
        """Detalles de lotes consumidos en una producción."""
        with rx.session() as session:
            stmt = select(ProduccionDetalle).where(
                ProduccionDetalle.produccion_id == produccion_id
            )
            if only_active:
                stmt = stmt.where(ProduccionDetalle.activo == True)  # noqa: E712
            return list(session.exec(stmt).all())

    @classmethod
    def get_by_lote(
        cls, lote_id: int, only_active: bool = True
    ) -> list[ProduccionDetalle]:
        """
        Producciones que consumieron un lote específico.
        Permite trazabilidad: ¿dónde se usó este lote?
        """
        with rx.session() as session:
            stmt = select(ProduccionDetalle).where(ProduccionDetalle.lote_id == lote_id)
            if only_active:
                stmt = stmt.where(ProduccionDetalle.activo == True)  # noqa: E712
            return list(session.exec(stmt).all())
