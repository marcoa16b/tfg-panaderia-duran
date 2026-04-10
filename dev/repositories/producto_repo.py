"""
producto_repo.py — Repositorio de acceso a datos para la tabla `producto`.

Hereda CRUD genérico de BaseRepository[Producto] y agrega:

Métodos de búsqueda:
    - search_by_nombre: Búsqueda parcial por nombre (ilike).
    - get_by_categoria: Filtra productos por su categoría.
    - get_by_unidad_medida: Filtra por unidad de medida.
    - search_with_filters: Búsqueda combinada (texto + categoría + paginación).

Métodos de inventario:
    - update_stock: Incrementa/decrementa stock_actual de un producto.
    - get_below_min_stock: Productos cuyo stock_actual <= stock_minimo (para alertas).

Patrón de paginación:
    search_with_filters retorna tuple[list, int] → (resultados_página, total).
    El frontend usa offset/limit para navegar páginas.
"""

import logging
from decimal import Decimal
from typing import Optional

import reflex as rx
from sqlmodel import select

from dev.models.models import Producto
from dev.repositories.base_repository import BaseRepository

logger = logging.getLogger("dev.repositories.producto")


class ProductoRepository(BaseRepository[Producto]):
    model = Producto

    @classmethod
    def search_by_nombre(cls, query: str, only_active: bool = True) -> list[Producto]:
        """Búsqueda parcial por nombre (case-insensitive con ilike)."""
        logger.debug("Buscando productos por nombre: %s", query)
        with rx.session() as session:
            stmt = select(Producto).where(Producto.nombre.ilike(f"%{query}%"))
            if only_active:
                stmt = stmt.where(Producto.activo == True)  # noqa: E712
            return list(session.exec(stmt).all())

    @classmethod
    def get_by_categoria(
        cls, categoria_id: int, only_active: bool = True
    ) -> list[Producto]:
        """Filtra productos por categoría (FK a categoria_producto.id)."""
        logger.debug("Buscando productos por categoría: %s", categoria_id)
        with rx.session() as session:
            stmt = select(Producto).where(Producto.categoria_id == categoria_id)
            if only_active:
                stmt = stmt.where(Producto.activo == True)  # noqa: E712
            return list(session.exec(stmt).all())

    @classmethod
    def get_by_unidad_medida(
        cls, unidad_medida_id: int, only_active: bool = True
    ) -> list[Producto]:
        """Filtra productos por unidad de medida (FK a unidad_medida.id)."""
        with rx.session() as session:
            stmt = select(Producto).where(Producto.unidad_medida_id == unidad_medida_id)
            if only_active:
                stmt = stmt.where(Producto.activo == True)  # noqa: E712
            return list(session.exec(stmt).all())

    @classmethod
    def update_stock(cls, producto_id: int, cantidad: Decimal) -> Optional[Producto]:
        """
        Incrementa o decrementa el stock_actual de un producto.

        Importante: Este método NO valida que el stock quede en negativo.
        La validación de stock suficiente debe hacerse en la capa Service.

        Args:
            producto_id: PK del producto.
            cantidad: Puede ser positivo (entrada) o negativo (salida).
        """
        logger.info(
            "Actualizando stock producto %s — cantidad: %s", producto_id, cantidad
        )
        with rx.session() as session:
            producto = session.get(Producto, producto_id)
            if not producto:
                return None
            producto.stock_actual += cantidad
            producto.actualizado_en = __import__("datetime").datetime.now()
            session.add(producto)
            session.commit()
            session.refresh(producto)
            return producto

    @classmethod
    def get_below_min_stock(cls) -> list[Producto]:
        """
        Productos cuyo stock_actual <= stock_minimo.
        Usado por el sistema de alertas para notificar bajo stock.
        Solo retorna productos activos.
        """
        logger.debug("Buscando productos bajo stock mínimo")
        with rx.session() as session:
            stmt = select(Producto).where(
                Producto.activo == True,  # noqa: E712
                Producto.stock_actual <= Producto.stock_minimo,
            )
            return list(session.exec(stmt).all())

    @classmethod
    def search_with_filters(
        cls,
        query: Optional[str] = None,
        categoria_id: Optional[int] = None,
        only_active: bool = True,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Producto], int]:
        """
        Búsqueda combinada con filtros opcionales y paginación.

        Args:
            query: Texto para buscar en nombre (parcial, case-insensitive).
            categoria_id: Filtrar por categoría.
            only_active: Excluir registros inactivos.
            offset: Desplazamiento para paginación (0-based).
            limit: Máximo de resultados por página.

        Returns:
            (lista_resultados, total_registros_con_filtros)
        """
        logger.debug(
            "Buscando productos con filtros: query=%s, cat=%s", query, categoria_id
        )
        from sqlmodel import func

        with rx.session() as session:
            stmt = select(Producto)
            count_stmt = select(func.count()).select_from(Producto)

            if only_active:
                stmt = stmt.where(Producto.activo == True)  # noqa: E712
                count_stmt = count_stmt.where(Producto.activo == True)  # noqa: E712
            if query:
                stmt = stmt.where(Producto.nombre.ilike(f"%{query}%"))
                count_stmt = count_stmt.where(Producto.nombre.ilike(f"%{query}%"))
            if categoria_id:
                stmt = stmt.where(Producto.categoria_id == categoria_id)
                count_stmt = count_stmt.where(Producto.categoria_id == categoria_id)

            total = session.exec(count_stmt).one()
            results = session.exec(stmt.offset(offset).limit(limit)).all()
            return list(results), total
