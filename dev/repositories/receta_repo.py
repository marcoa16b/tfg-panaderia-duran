"""
receta_repo.py — Repositorios para recetas y sus ingredientes (detalles).

Contiene DOS repositorios (relación padre-hijo):

RecetaRepository (tabla: receta)
    Hereda CRUD genérico y agrega:
    - get_with_detalles: Receta + todos sus ingredientes (RecetaDetalle).
    - get_by_producto: Recetas que producen un producto específico.
    - search_by_nombre: Búsqueda parcial por nombre de receta.
    - create_with_detalles: Transacción atómica — crea receta + ingredientes.
    - update_detalles: Reemplaza todos los ingredientes de una receta (borra + crea).

RecetaDetalleRepository (tabla: receta_detalle)
    Hereda CRUD genérico y agrega:
    - get_by_receta: Ingredientes de una receta.
    - get_by_producto: Recetas que usan un producto como ingrediente.

Modelo de datos
---------------
Una Receta tiene:
    - producto_id: El producto FINAL que se elabora (ej: "Pan de leche").
    - N RecetaDetalle: Cada uno es un INGREDIENTE con cantidad.
      - producto_id: El ingrediente (ej: "Harina", "Azúcar").
      - cantidad: Cuánto se necesita por unidad de receta.

Ejemplo:
    Receta: "Pan de leche" → producto_id = Pan de leche
    Detalle 1: producto_id = Harina, cantidad = 500g
    Detalle 2: producto_id = Azúcar, cantidad = 50g
    Detalle 3: producto_id = Levadura, cantidad = 10g
"""

import logging
from typing import Optional

import reflex as rx
from sqlmodel import select

from dev.models.models import Receta, RecetaDetalle
from dev.repositories.base_repository import BaseRepository

logger = logging.getLogger("dev.repositories.receta")


class RecetaRepository(BaseRepository[Receta]):
    model = Receta

    @classmethod
    def get_with_detalles(cls, receta_id: int) -> Optional[dict]:
        """
        Obtiene una receta con todos sus ingredientes.

        Returns:
            {"receta": Receta, "detalles": list[RecetaDetalle]}
            o None si no existe.
        """
        logger.debug("Obteniendo receta %s con ingredientes", receta_id)
        with rx.session() as session:
            receta = session.get(Receta, receta_id)
            if not receta:
                return None
            stmt = select(RecetaDetalle).where(
                RecetaDetalle.receta_id == receta_id,
                RecetaDetalle.activo == True,  # noqa: E712
            )
            detalles = list(session.exec(stmt).all())
            return {"receta": receta, "detalles": detalles}

    @classmethod
    def get_by_producto(
        cls, producto_id: int, only_active: bool = True
    ) -> list[Receta]:
        """Recetas que producen un producto específico."""
        logger.debug("Buscando recetas del producto: %s", producto_id)
        with rx.session() as session:
            stmt = select(Receta).where(Receta.producto_id == producto_id)
            if only_active:
                stmt = stmt.where(Receta.activo == True)  # noqa: E712
            return list(session.exec(stmt).all())

    @classmethod
    def search_by_nombre(cls, query: str, only_active: bool = True) -> list[Receta]:
        """Búsqueda parcial por nombre de receta."""
        logger.debug("Buscando recetas por nombre: %s", query)
        with rx.session() as session:
            stmt = select(Receta).where(Receta.nombre.ilike(f"%{query}%"))
            if only_active:
                stmt = stmt.where(Receta.activo == True)  # noqa: E712
            return list(session.exec(stmt).all())

    @classmethod
    def create_with_detalles(
        cls,
        receta_data: dict,
        detalles_data: list[dict],
    ) -> dict:
        """
        Crea una receta y sus ingredientes en una transacción atómica.

        Args:
            receta_data: Campos de Receta (sin id).
            detalles_data: Lista de dicts con producto_id y cantidad.

        Returns:
            {"receta": Receta, "detalles": list[RecetaDetalle]}
        """
        logger.info("Creando receta con %s ingredientes", len(detalles_data))
        with rx.session() as session:
            receta = Receta(**receta_data)
            session.add(receta)
            session.flush()

            detalles = []
            for detalle_dict in detalles_data:
                detalle_dict["receta_id"] = receta.id
                detalle = RecetaDetalle(**detalle_dict)
                session.add(detalle)
                detalles.append(detalle)

            session.commit()
            session.refresh(receta)
            for detalle in detalles:
                session.refresh(detalle)

            logger.info(
                "Receta creada — id=%s con %s ingredientes", receta.id, len(detalles)
            )
            return {"receta": receta, "detalles": detalles}

    @classmethod
    def update_detalles(
        cls,
        receta_id: int,
        nuevos_detalles: list[dict],
    ) -> dict:
        """
        Reemplaza todos los ingredientes de una receta.
        Borra los detalles existentes y crea los nuevos en una transacción.

        Args:
            receta_id: PK de la receta.
            nuevos_detalles: Lista de dicts con producto_id y cantidad.

        Returns:
            {"receta": Receta, "detalles": list[RecetaDetalle]}
        """
        logger.info("Actualizando ingredientes de receta %s", receta_id)
        with rx.session() as session:
            receta = session.get(Receta, receta_id)
            if not receta:
                return None

            # Borrar detalles anteriores
            stmt = select(RecetaDetalle).where(RecetaDetalle.receta_id == receta_id)
            existing = session.exec(stmt).all()
            for d in existing:
                session.delete(d)
            session.flush()

            # Crear nuevos detalles
            detalles = []
            for detalle_dict in nuevos_detalles:
                detalle_dict["receta_id"] = receta_id
                detalle = RecetaDetalle(**detalle_dict)
                session.add(detalle)
                detalles.append(detalle)

            session.commit()
            session.refresh(receta)
            for detalle in detalles:
                session.refresh(detalle)

            return {"receta": receta, "detalles": detalles}


class RecetaDetalleRepository(BaseRepository[RecetaDetalle]):
    model = RecetaDetalle

    @classmethod
    def get_by_receta(
        cls, receta_id: int, only_active: bool = True
    ) -> list[RecetaDetalle]:
        """Ingredientes de una receta."""
        with rx.session() as session:
            stmt = select(RecetaDetalle).where(RecetaDetalle.receta_id == receta_id)
            if only_active:
                stmt = stmt.where(RecetaDetalle.activo == True)  # noqa: E712
            return list(session.exec(stmt).all())

    @classmethod
    def get_by_producto(
        cls, producto_id: int, only_active: bool = True
    ) -> list[RecetaDetalle]:
        """
        Recetas que usan un producto como ingrediente.
        Útil para saber qué recetas se ven afectadas si un insumo cambia.
        """
        with rx.session() as session:
            stmt = select(RecetaDetalle).where(RecetaDetalle.producto_id == producto_id)
            if only_active:
                stmt = stmt.where(RecetaDetalle.activo == True)  # noqa: E712
            return list(session.exec(stmt).all())
