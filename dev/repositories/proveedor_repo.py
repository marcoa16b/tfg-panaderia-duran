"""
proveedor_repo.py — Repositorio de acceso a datos para la tabla `proveedor`.

Hereda CRUD genérico de BaseRepository[Proveedor] y agrega:

    - search_by_nombre: Búsqueda parcial por nombre.
    - get_by_distrito: Filtra proveedores por distrito (ubicación geográfica).
    - search_with_filters: Búsqueda combinada (texto + distrito + paginación).

El modelo Proveedor tiene FK opcional a `distrito`, lo que permite
asociar proveedores a una ubicación geográfica (Provincia > Cantón > Distrito).
"""

import logging
from typing import Optional

import reflex as rx
from sqlmodel import select

from dev.models.models import Proveedor
from dev.repositories.base_repository import BaseRepository

logger = logging.getLogger("dev.repositories.proveedor")


class ProveedorRepository(BaseRepository[Proveedor]):
    model = Proveedor

    @classmethod
    def search_by_nombre(cls, query: str, only_active: bool = True) -> list[Proveedor]:
        """Búsqueda parcial por nombre (case-insensitive)."""
        logger.debug("Buscando proveedores por nombre: %s", query)
        with rx.session() as session:
            stmt = select(Proveedor).where(Proveedor.nombre.ilike(f"%{query}%"))
            if only_active:
                stmt = stmt.where(Proveedor.activo == True)  # noqa: E712
            return list(session.exec(stmt).all())

    @classmethod
    def get_by_distrito(
        cls, distrito_id: int, only_active: bool = True
    ) -> list[Proveedor]:
        """Filtra proveedores por distrito geográfico."""
        logger.debug("Buscando proveedores por distrito: %s", distrito_id)
        with rx.session() as session:
            stmt = select(Proveedor).where(Proveedor.distrito_id == distrito_id)
            if only_active:
                stmt = stmt.where(Proveedor.activo == True)  # noqa: E712
            return list(session.exec(stmt).all())

    @classmethod
    def search_with_filters(
        cls,
        query: Optional[str] = None,
        distrito_id: Optional[int] = None,
        only_active: bool = True,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Proveedor], int]:
        """
        Búsqueda combinada con filtros y paginación.

        Args:
            query: Búsqueda parcial por nombre.
            distrito_id: Filtrar por distrito.
            only_active: Excluir inactivos.
            offset/limit: Paginación.

        Returns:
            (resultados, total)
        """
        from sqlmodel import func

        with rx.session() as session:
            stmt = select(Proveedor)
            count_stmt = select(func.count()).select_from(Proveedor)

            if only_active:
                stmt = stmt.where(Proveedor.activo == True)  # noqa: E712
                count_stmt = count_stmt.where(Proveedor.activo == True)  # noqa: E712
            if query:
                stmt = stmt.where(Proveedor.nombre.ilike(f"%{query}%"))
                count_stmt = count_stmt.where(Proveedor.nombre.ilike(f"%{query}%"))
            if distrito_id:
                stmt = stmt.where(Proveedor.distrito_id == distrito_id)
                count_stmt = count_stmt.where(Proveedor.distrito_id == distrito_id)

            total = session.exec(count_stmt).one()
            results = session.exec(stmt.offset(offset).limit(limit)).all()
            return list(results), total
