"""
producto_service.py — Servicio de gestión de productos/insumos.

Arquitectura
------------
Capa de lógica de negocio para el catálogo de productos. Orquesta las
operaciones CRUD delegando al ProductoRepository y aplicando reglas de
negocio como validación de categoría, unidad de medida y stock mínimo.

Patrón de diseño: Service Layer
    - Valida que la categoría exista y esté activa antes de crear un producto.
    - Valida que la unidad de medida exista y esté activa.
    - Impide que se establezca un stock mínimo negativo.
    - Protege campos internos (stock_actual, id, creado_en) contra modificación directa.

Relación con otras capas
------------------------
    [Productos Page] → [ProductoState] → ProductoService → ProductoRepository → [PostgreSQL]

Validaciones de negocio
-----------------------
    - Nombre: mínimo 2 caracteres.
    - Categoría (categoria_id): debe existir en tabla 'categoria_producto'.
    - Unidad de medida (unidad_medida_id): debe existir en tabla 'unidad_medida'.
    - Stock mínimo: no puede ser negativo.
    - stock_actual se inicializa en 0 al crear (no se puede setear manualmente).
      Se actualiza exclusivamente via InventarioService (entradas/salidas/producción).

Uso desde la capa State:
    from dev.services.producto_service import ProductoService

    producto = ProductoService.create(
        nombre="Harina de trigo",
        categoria_id=1,
        unidad_medida_id=1,
        stock_minimo=Decimal("10"),
    )
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional

import reflex as rx
from sqlmodel import select

from dev.core.exceptions import NotFoundException, ValidationException
from dev.models.models import CategoriaProducto, Producto, UnidadMedida
from dev.repositories.producto_repo import ProductoRepository

logger = logging.getLogger("dev.services.producto")


class ProductoService:
    """
    Servicio de gestión del catálogo de productos.

    Métodos principales:
        - create: Crear producto con validación de categoría y unidad.
        - update: Actualizar campos (protege campos internos).
        - deactivate: Soft delete (activo=False).
        - search: Búsqueda por nombre (mínimo 2 caracteres).
        - get_paginated: Productos con filtros y paginación.
        - get_productos_below_min_stock: Productos con stock bajo (para alertas).

    Relación con alertas:
        ProductoService.get_productos_below_min_stock() es usado por
        AlertaService para detectar productos que necesitan reposición.
    """

    @classmethod
    def get_by_id(cls, producto_id: int) -> Producto:
        """
        Obtiene un producto por ID.

        Args:
            producto_id: PK del producto.

        Returns:
            La instancia de Producto.

        Raises:
            NotFoundException: Si el producto no existe.
        """
        producto = ProductoRepository.get_by_id(producto_id)
        if not producto:
            raise NotFoundException(f"Producto con id={producto_id} no encontrado")
        return producto

    @classmethod
    def get_all(cls, only_active: bool = True) -> list[Producto]:
        """Retorna todos los productos. Filtra inactivos por defecto."""
        return ProductoRepository.get_all(only_active=only_active)

    @classmethod
    def get_paginated(
        cls,
        offset: int = 0,
        limit: int = 20,
        query: Optional[str] = None,
        categoria_id: Optional[int] = None,
    ) -> tuple[list[Producto], int]:
        """
        Productos paginados con filtros opcionales.

        Args:
            offset: Desplazamiento (0-based).
            limit: Máximo de resultados por página.
            query: Búsqueda parcial por nombre.
            categoria_id: Filtrar por categoría.

        Returns:
            (lista_resultados, total_registros)
        """
        return ProductoRepository.search_with_filters(
            query=query,
            categoria_id=categoria_id,
            offset=offset,
            limit=limit,
        )

    @classmethod
    def search(cls, query: str, only_active: bool = True) -> list[Producto]:
        """
        Búsqueda textual por nombre de producto.

        Args:
            query: Texto de búsqueda (mínimo 2 caracteres).

        Raises:
            ValidationException: Si el query tiene menos de 2 caracteres.
        """
        if not query or len(query.strip()) < 2:
            raise ValidationException("La búsqueda debe tener al menos 2 caracteres")
        return ProductoRepository.search_by_nombre(
            query.strip(), only_active=only_active
        )

    @classmethod
    def get_by_categoria(cls, categoria_id: int) -> list[Producto]:
        """Productos de una categoría. Valida que la categoría exista."""
        cls._validate_categoria_exists(categoria_id)
        return ProductoRepository.get_by_categoria(categoria_id)

    @classmethod
    def create(
        cls,
        nombre: str,
        categoria_id: int,
        unidad_medida_id: int,
        stock_minimo: Decimal = Decimal("0"),
        descripcion: Optional[str] = None,
        ubicacion: Optional[str] = None,
        imagen_url: Optional[str] = None,
    ) -> Producto:
        """
        Crea un nuevo producto con validaciones de negocio.

        Reglas:
            1. Nombre mínimo 2 caracteres.
            2. categoría_id debe existir en 'categoria_producto' y estar activo.
            3. unidad_medida_id debe existir en 'unidad_medida' y estar activo.
            4. stock_minimo no puede ser negativo.
            5. stock_actual se inicializa en 0 (se actualiza via entradas/salidas).

        Args:
            nombre: Nombre del producto.
            categoria_id: FK a categoria_producto.
            unidad_medida_id: FK a unidad_medida.
            stock_minimo: Cantidad mínima de stock para alertas.
            descripcion: Descripción opcional.
            ubicacion: Ubicación física en la panadería.
            imagen_url: URL de la imagen del producto.

        Returns:
            El producto creado con ID generado.
        """
        nombre = nombre.strip()
        if not nombre or len(nombre) < 2:
            raise ValidationException(
                "El nombre del producto debe tener al menos 2 caracteres"
            )

        if stock_minimo < 0:
            raise ValidationException("El stock mínimo no puede ser negativo")

        cls._validate_categoria_exists(categoria_id)
        cls._validate_unidad_medida_exists(unidad_medida_id)

        producto = ProductoRepository.create(
            nombre=nombre,
            descripcion=descripcion,
            categoria_id=categoria_id,
            unidad_medida_id=unidad_medida_id,
            stock_minimo=stock_minimo,
            stock_actual=Decimal("0"),
            ubicacion=ubicacion,
            imagen_url=imagen_url,
        )
        logger.info("Producto creado: %s (id=%s)", nombre, producto.id)
        return producto

    @classmethod
    def update(cls, producto_id: int, **kwargs) -> Producto:
        """
        Actualiza campos de un producto existente.

        Protege campos internos: stock_actual, id, creado_en no se pueden
        modificar directamente. El stock se actualiza exclusivamente a través
        de InventarioService (entradas/salidas/producción).

        Args:
            producto_id: PK del producto.
            **kwargs: Campos a actualizar (nombre, descripcion, stock_minimo, etc.)

        Raises:
            NotFoundException: Si el producto no existe.
            ValidationException: Si algún campo no pasa validación.
        """
        cls.get_by_id(producto_id)

        if "nombre" in kwargs:
            nombre = kwargs["nombre"].strip()
            if not nombre or len(nombre) < 2:
                raise ValidationException(
                    "El nombre del producto debe tener al menos 2 caracteres"
                )
            kwargs["nombre"] = nombre

        if "stock_minimo" in kwargs and kwargs["stock_minimo"] < 0:
            raise ValidationException("El stock mínimo no puede ser negativo")

        if "categoria_id" in kwargs:
            cls._validate_categoria_exists(kwargs["categoria_id"])

        if "unidad_medida_id" in kwargs:
            cls._validate_unidad_medida_exists(kwargs["unidad_medida_id"])

        disallowed = {"stock_actual", "id", "creado_en"}
        for field in disallowed:
            kwargs.pop(field, None)

        updated = ProductoRepository.update(producto_id, **kwargs)
        logger.info("Producto actualizado: id=%s", producto_id)
        return updated

    @classmethod
    def deactivate(cls, producto_id: int) -> bool:
        """
        Desactiva un producto (soft delete).

        El producto permanece en la BD para auditoría pero no aparece en
        consultas normales. Si tiene lotes activos o recetas asociadas,
        esas relaciones se mantienen.

        Raises:
            NotFoundException: Si el producto no existe.
        """
        cls.get_by_id(producto_id)
        logger.info("Producto desactivado: id=%s", producto_id)
        return ProductoRepository.soft_delete(producto_id)

    @classmethod
    def get_current_stock(cls, producto_id: int) -> Decimal:
        """Retorna el stock actual de un producto."""
        producto = cls.get_by_id(producto_id)
        return producto.stock_actual

    @classmethod
    def get_productos_below_min_stock(cls) -> list[Producto]:
        """
        Productos cuyo stock_actual <= stock_minimo.

        Usado por AlertaService para generar alertas de bajo stock.
        Solo retorna productos activos.
        """
        return ProductoRepository.get_below_min_stock()

    @classmethod
    def count(cls, only_active: bool = True) -> int:
        """Total de productos. Filtra inactivos por defecto."""
        return ProductoRepository.count(only_active=only_active)

    @classmethod
    def _validate_categoria_exists(cls, categoria_id: int):
        """Verifica que una categoría exista y esté activa."""
        with rx.session() as session:
            cat = session.get(CategoriaProducto, categoria_id)
            if not cat or not cat.activo:
                raise ValidationException(
                    f"Categoría con id={categoria_id} no existe o está inactiva"
                )

    @classmethod
    def _validate_unidad_medida_exists(cls, unidad_medida_id: int):
        """Verifica que una unidad de medida exista y esté activa."""
        with rx.session() as session:
            um = session.get(UnidadMedida, unidad_medida_id)
            if not um or not um.activo:
                raise ValidationException(
                    f"Unidad de medida con id={unidad_medida_id} no existe o está inactiva"
                )
