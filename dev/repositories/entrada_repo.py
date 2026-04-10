"""
entrada_repo.py — Repositorios para entradas de inventario y lotes.

Contiene DOS repositorios en el mismo archivo porque `entrada_inventario` y
`lote_inventario` tienen una relación padre-hijo (una entrada tiene muchos lotes).

EntradaRepository (tabla: entrada_inventario)
    Hereda CRUD genérico de BaseRepository y agrega:
    - get_with_lotes: Obtiene entrada + todos sus lotes asociados.
    - get_by_fecha_range: Entradas en un rango de fechas.
    - get_by_proveedor: Entradas de un proveedor específico.
    - get_by_tipo: Entradas filtradas por tipo (Compra, Donación, etc.).
    - create_with_lotes: Transacción atómica — crea entrada + lotes en una sesión.

LoteRepository (tabla: lote_inventario)
    Hereda CRUD genérico y agrega:
    - get_by_producto: Lotes de un producto específico.
    - get_proximos_a_vencer: Lotes que vencen dentro de N días (para alertas).
    - get_by_entrada: Lotes pertenecientes a una entrada específica.

Transacción atómica (create_with_lotes)
---------------------------------------
El patrón `flush()` + `commit()` garantiza que la entrada y sus lotes
se guardan en una sola transacción. Si algún lote falla, se hace rollback
de todo.

    session.add(entrada)
    session.flush()          # Obtiene el ID sin hacer commit
    lote.entrada_id = entrada.id
    session.commit()         # Commit de todo junto
"""

import logging
from datetime import date
from typing import Optional

import reflex as rx
from sqlmodel import select

from dev.models.models import EntradaInventario, LoteInventario
from dev.repositories.base_repository import BaseRepository

logger = logging.getLogger("dev.repositories.entrada")


class EntradaRepository(BaseRepository[EntradaInventario]):
    model = EntradaInventario

    @classmethod
    def get_with_lotes(cls, entrada_id: int) -> Optional[dict]:
        """
        Obtiene una entrada junto con todos sus lotes asociados.

        Returns:
            {"entrada": EntradaInventario, "lotes": list[LoteInventario]}
            o None si la entrada no existe.
        """
        logger.debug("Obteniendo entrada %s con lotes", entrada_id)
        with rx.session() as session:
            entrada = session.get(EntradaInventario, entrada_id)
            if not entrada:
                return None
            stmt = select(LoteInventario).where(
                LoteInventario.entrada_id == entrada_id,
                LoteInventario.activo == True,  # noqa: E712
            )
            lotes = list(session.exec(stmt).all())
            return {"entrada": entrada, "lotes": lotes}

    @classmethod
    def get_by_fecha_range(
        cls,
        fecha_inicio: date,
        fecha_fin: date,
        only_active: bool = True,
    ) -> list[EntradaInventario]:
        """Filtra entradas por rango de fechas (ambos inclusive)."""
        logger.debug("Buscando entradas entre %s y %s", fecha_inicio, fecha_fin)
        with rx.session() as session:
            stmt = select(EntradaInventario).where(
                EntradaInventario.fecha >= fecha_inicio,
                EntradaInventario.fecha <= fecha_fin,
            )
            if only_active:
                stmt = stmt.where(EntradaInventario.activo == True)  # noqa: E712
            return list(session.exec(stmt).all())

    @classmethod
    def get_by_proveedor(
        cls, proveedor_id: int, only_active: bool = True
    ) -> list[EntradaInventario]:
        """Entradas asociadas a un proveedor específico."""
        logger.debug("Buscando entradas del proveedor: %s", proveedor_id)
        with rx.session() as session:
            stmt = select(EntradaInventario).where(
                EntradaInventario.proveedor_id == proveedor_id
            )
            if only_active:
                stmt = stmt.where(EntradaInventario.activo == True)  # noqa: E712
            return list(session.exec(stmt).all())

    @classmethod
    def get_by_tipo(
        cls, tipo_id: int, only_active: bool = True
    ) -> list[EntradaInventario]:
        """Entradas filtradas por tipo (Compra, Donación, Ajuste positivo)."""
        with rx.session() as session:
            stmt = select(EntradaInventario).where(EntradaInventario.tipo_id == tipo_id)
            if only_active:
                stmt = stmt.where(EntradaInventario.activo == True)  # noqa: E712
            return list(session.exec(stmt).all())

    @classmethod
    def create_with_lotes(
        cls,
        entrada_data: dict,
        lotes_data: list[dict],
    ) -> dict:
        """
        Crea una entrada y sus lotes en una transacción atómica.

        Flujo:
            1. Crea la EntradaInventario (sin commit).
            2. flush() → genera el ID de la entrada.
            3. Crea cada LoteInventario con entrada_id.
            4. commit() → persiste todo o nada.

        Args:
            entrada_data: Campos de EntradaInventario (sin id).
            lotes_data: Lista de dicts con campos de LoteInventario
                        (sin entrada_id, se asigna automáticamente).

        Returns:
            {"entrada": EntradaInventario, "lotes": list[LoteInventario]}
        """
        logger.info("Creando entrada con %s lotes", len(lotes_data))
        with rx.session() as session:
            entrada = EntradaInventario(**entrada_data)
            session.add(entrada)
            session.flush()

            lotes = []
            for lote_dict in lotes_data:
                lote_dict["entrada_id"] = entrada.id
                lote = LoteInventario(**lote_dict)
                session.add(lote)
                lotes.append(lote)

            session.commit()
            session.refresh(entrada)
            for lote in lotes:
                session.refresh(lote)

            logger.info("Entrada creada — id=%s con %s lotes", entrada.id, len(lotes))
            return {"entrada": entrada, "lotes": lotes}


class LoteRepository(BaseRepository[LoteInventario]):
    model = LoteInventario

    @classmethod
    def get_by_producto(
        cls, producto_id: int, only_active: bool = True
    ) -> list[LoteInventario]:
        """Todos los lotes de un producto específico."""
        logger.debug("Buscando lotes del producto: %s", producto_id)
        with rx.session() as session:
            stmt = select(LoteInventario).where(
                LoteInventario.producto_id == producto_id
            )
            if only_active:
                stmt = stmt.where(LoteInventario.activo == True)  # noqa: E712
            return list(session.exec(stmt).all())

    @classmethod
    def get_proximos_a_vencer(
        cls, dias_limite: int = 7, only_active: bool = True
    ) -> list[LoteInventario]:
        """
        Lotes cuya fecha_vencimiento está dentro de los próximos N días.
        Usado por el sistema de alertas para notificar productos por vencer.

        Args:
            dias_limite: Días hacia adelante desde hoy (default: 7).
        """
        logger.debug("Buscando lotes próximos a vencer (%s días)", dias_limite)
        from datetime import timedelta

        limite = date.today() + timedelta(days=dias_limite)
        with rx.session() as session:
            stmt = select(LoteInventario).where(
                LoteInventario.fecha_vencimiento != None,  # noqa: E711
                LoteInventario.fecha_vencimiento <= limite,
            )
            if only_active:
                stmt = stmt.where(LoteInventario.activo == True)  # noqa: E712
            return list(session.exec(stmt).all())

    @classmethod
    def get_by_entrada(
        cls, entrada_id: int, only_active: bool = True
    ) -> list[LoteInventario]:
        """Lotes pertenecientes a una entrada específica."""
        with rx.session() as session:
            stmt = select(LoteInventario).where(LoteInventario.entrada_id == entrada_id)
            if only_active:
                stmt = stmt.where(LoteInventario.activo == True)  # noqa: E712
            return list(session.exec(stmt).all())
