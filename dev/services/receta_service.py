"""
receta_service.py — Servicio de gestión de recetas e ingredientes.

Arquitectura
------------
Capa de lógica de negocio para las recetas del sistema. Una receta define
qué insumos y en qué cantidades se necesitan para producir un producto final.

Patrón de diseño: Service Layer
    - Valida ingredientes antes de crear/actualizar una receta.
    - Calcula los insumos necesarios según cantidad a producir.
    - Verifica disponibilidad de insumos contra stock actual.
    - Orquesta transacciones atómicas (receta + ingredientes).

Relación con otras capas
------------------------
    [Recetas Page] → [RecetaState] → RecetaService → RecetaRepository → [PostgreSQL]
                                                  → ProductoRepository (validación)

Modelo de datos
---------------
Una Receta tiene:
    - producto_id: El producto FINAL que se elabora (ej: "Pan de leche").
    - N RecetaDetalle: Cada uno es un INGREDIENTE con cantidad.
        - producto_id: El ingrediente (ej: "Harina", "Azúcar").
        - cantidad: Cuánto se necesita POR UNIDAD de receta.

Ejemplo:
    Receta "Pan de leche" → producto_id = Pan de leche
    Detalle 1: producto_id = Harina,  cantidad = 500g
    Detalle 2: producto_id = Azúcar,  cantidad = 50g
    Detalle 3: producto_id = Levadura, cantidad = 10g

Si se producen 10 panes de leche, se necesitan:
    500×10=5000g Harina, 50×10=500g Azúcar, 10×10=100g Levadura

Relación con producción
-----------------------
ProduccionService usa RecetaService para:
    1. Calcular insumos necesarios (calcular_insumos_necesarios).
    2. Verificar que haya stock suficiente (verificar_insumos_disponibles).
    3. Luego registrar la producción y descontar insumos.

Uso desde la capa State:
    from dev.services.receta_service import RecetaService

    receta = RecetaService.create(
        nombre="Pan de leche",
        producto_id=5,
        ingredientes=[
            {"producto_id": 1, "cantidad": Decimal("500")},
            {"producto_id": 2, "cantidad": Decimal("50")},
        ],
    )
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional

from dev.core.exceptions import NotFoundException, ValidationException
from dev.models.models import Receta, RecetaDetalle
from dev.repositories.producto_repo import ProductoRepository
from dev.repositories.receta_repo import RecetaDetalleRepository, RecetaRepository

logger = logging.getLogger("dev.services.receta")


class RecetaService:
    """
    Servicio de gestión de recetas.

    Métodos principales:
        - create: Crear receta con ingredientes (transacción atómica).
        - update: Actualizar datos de la receta (sin tocar ingredientes).
        - update_ingredientes: Reemplazar todos los ingredientes de una receta.
        - calcular_insumos_necesarios: cantidad × ingredientes de la receta.
        - verificar_insumos_disponibles: compara insumos necesarios vs stock actual.
        - deactivate: Soft delete de la receta.

    Métodos de consulta:
        - get_by_id, get_all, search, get_by_producto, get_ingredientes.
    """

    @classmethod
    def get_by_id(cls, receta_id: int) -> Receta:
        """Obtiene una receta por ID. Lanza NotFoundException si no existe."""
        receta = RecetaRepository.get_by_id(receta_id)
        if not receta:
            raise NotFoundException(f"Receta con id={receta_id} no encontrada")
        return receta

    @classmethod
    def get_with_detalles(cls, receta_id: int) -> dict:
        """
        Obtiene una receta con todos sus ingredientes.

        Returns:
            {"receta": Receta, "detalles": list[RecetaDetalle]}
        """
        result = RecetaRepository.get_with_detalles(receta_id)
        if not result:
            raise NotFoundException(f"Receta con id={receta_id} no encontrada")
        return result

    @classmethod
    def get_all(cls, only_active: bool = True) -> list[Receta]:
        """Todas las recetas. Filtra inactivas por defecto."""
        return RecetaRepository.get_all(only_active=only_active)

    @classmethod
    def search(cls, query: str, only_active: bool = True) -> list[Receta]:
        """
        Búsqueda por nombre de receta (parcial, case-insensitive).

        Args:
            query: Mínimo 2 caracteres.

        Raises:
            ValidationException: Si el query es muy corto.
        """
        if not query or len(query.strip()) < 2:
            raise ValidationException("La búsqueda debe tener al menos 2 caracteres")
        return RecetaRepository.search_by_nombre(query.strip(), only_active=only_active)

    @classmethod
    def get_by_producto(cls, producto_id: int) -> list[Receta]:
        """Recetas que producen un producto específico."""
        return RecetaRepository.get_by_producto(producto_id)

    @classmethod
    def create(
        cls,
        nombre: str,
        producto_id: int,
        ingredientes: list[dict],
        descripcion: Optional[str] = None,
    ) -> dict:
        """
        Crea una receta con sus ingredientes en una transacción atómica.

        Validaciones:
            1. Nombre mínimo 2 caracteres.
            2. producto_id debe existir (es el producto final).
            3. Al menos 1 ingrediente.
            4. Cada ingrediente: producto_id existe, cantidad > 0.

        Args:
            nombre: Nombre de la receta.
            producto_id: Producto final que se elabora.
            ingredientes: Lista de {"producto_id": int, "cantidad": Decimal}.
            descripcion: Descripción opcional.

        Returns:
            {"receta": Receta, "detalles": list[RecetaDetalle]}
        """
        nombre = nombre.strip()
        if not nombre or len(nombre) < 2:
            raise ValidationException(
                "El nombre de la receta debe tener al menos 2 caracteres"
            )

        producto = ProductoRepository.get_by_id(producto_id)
        if not producto:
            raise ValidationException(f"Producto con id={producto_id} no existe")

        if not ingredientes:
            raise ValidationException("La receta debe tener al menos un ingrediente")

        cls._validate_ingredientes(ingredientes)

        receta_data = {
            "nombre": nombre,
            "producto_id": producto_id,
            "descripcion": descripcion,
        }

        detalles_data = []
        for ing in ingredientes:
            detalles_data.append(
                {
                    "producto_id": ing["producto_id"],
                    "cantidad": Decimal(str(ing["cantidad"])),
                }
            )

        result = RecetaRepository.create_with_detalles(receta_data, detalles_data)
        logger.info(
            "Receta creada: %s (id=%s) con %s ingredientes",
            nombre,
            result["receta"].id,
            len(detalles_data),
        )
        return result

    @classmethod
    def update(cls, receta_id: int, **kwargs) -> Receta:
        """
        Actualiza datos de la receta (sin tocar los ingredientes).

        Para actualizar ingredientes, usar update_ingredientes().

        Campos actualizables: nombre, descripcion, producto_id.
        Campos protegidos: id, creado_en.
        """
        cls.get_by_id(receta_id)

        if "nombre" in kwargs:
            nombre = kwargs["nombre"].strip()
            if not nombre or len(nombre) < 2:
                raise ValidationException(
                    "El nombre de la receta debe tener al menos 2 caracteres"
                )
            kwargs["nombre"] = nombre

        if "producto_id" in kwargs:
            producto = ProductoRepository.get_by_id(kwargs["producto_id"])
            if not producto:
                raise ValidationException(
                    f"Producto con id={kwargs['producto_id']} no existe"
                )

        disallowed = {"id", "creado_en"}
        for field in disallowed:
            kwargs.pop(field, None)

        updated = RecetaRepository.update(receta_id, **kwargs)
        logger.info("Receta actualizada: id=%s", receta_id)
        return updated

    @classmethod
    def update_ingredientes(cls, receta_id: int, ingredientes: list[dict]) -> dict:
        """
        Reemplaza todos los ingredientes de una receta.

        Borra los RecetaDetalle existentes y crea los nuevos en una
        transacción atómica. Esto garantiza consistencia: nunca hay
        ingredientes "huérfanos".

        Args:
            receta_id: PK de la receta.
            ingredientes: Nueva lista de {"producto_id", "cantidad"}.

        Returns:
            {"receta": Receta, "detalles": list[RecetaDetalle]}
        """
        cls.get_by_id(receta_id)

        if not ingredientes:
            raise ValidationException("La receta debe tener al menos un ingrediente")

        cls._validate_ingredientes(ingredientes)

        detalles_data = []
        for ing in ingredientes:
            detalles_data.append(
                {
                    "producto_id": ing["producto_id"],
                    "cantidad": Decimal(str(ing["cantidad"])),
                }
            )

        result = RecetaRepository.update_detalles(receta_id, detalles_data)
        logger.info(
            "Ingredientes de receta id=%s actualizados (%s ingredientes)",
            receta_id,
            len(detalles_data),
        )
        return result

    @classmethod
    def deactivate(cls, receta_id: int) -> bool:
        """Desactiva una receta (soft delete). Los detalles permanecen."""
        cls.get_by_id(receta_id)
        logger.info("Receta desactivada: id=%s", receta_id)
        return RecetaRepository.soft_delete(receta_id)

    @classmethod
    def get_ingredientes(cls, receta_id: int) -> list[RecetaDetalle]:
        """Retorna los ingredientes de una receta."""
        return RecetaDetalleRepository.get_by_receta(receta_id)

    @classmethod
    def calcular_insumos_necesarios(
        cls, receta_id: int, cantidad_producir: Decimal
    ) -> list[dict]:
        """
        Calcula los insumos necesarios para producir una cantidad dada.

        Multiplica la cantidad de cada ingrediente por la cantidad a producir:
            insumo.cantidad = detalle.cantidad × cantidad_producir

        Args:
            receta_id: PK de la receta.
            cantidad_producir: Unidades a producir.

        Returns:
            [{"producto_id": int, "cantidad_necesaria": Decimal}, ...]

        Usado por ProduccionService antes de registrar una producción.
        """
        receta_data = cls.get_with_detalles(receta_id)

        insumos = []
        for detalle in receta_data["detalles"]:
            insumos.append(
                {
                    "producto_id": detalle.producto_id,
                    "cantidad_necesaria": detalle.cantidad * cantidad_producir,
                }
            )

        logger.debug(
            "Insumos calculados para receta %s × %s: %s ingredientes",
            receta_id,
            cantidad_producir,
            len(insumos),
        )
        return insumos

    @classmethod
    def verificar_insumos_disponibles(
        cls, receta_id: int, cantidad_producir: Decimal
    ) -> dict:
        """
        Verifica si hay stock suficiente para producir una cantidad.

        Compara los insumos necesarios contra el stock_actual de cada
        producto. Retorna un desglose completo con indicadores de
        suficiencia y cantidades faltantes.

        Args:
            receta_id: PK de la receta.
            cantidad_producir: Unidades a producir.

        Returns:
            {
                "disponible": bool,  # True si TODOS los insumos alcanzan
                "detalle": [
                    {
                        "producto_id", "nombre", "cantidad_necesaria",
                        "stock_actual", "suficiente", "faltante"
                    }, ...
                ]
            }
        """
        insumos = cls.calcular_insumos_necesarios(receta_id, cantidad_producir)

        resultado = []
        todos_disponibles = True

        for insumo in insumos:
            producto = ProductoRepository.get_by_id(insumo["producto_id"])
            stock = producto.stock_actual if producto else Decimal("0")
            suficiente = stock >= insumo["cantidad_necesaria"]

            if not suficiente:
                todos_disponibles = False

            resultado.append(
                {
                    "producto_id": insumo["producto_id"],
                    "nombre": producto.nombre if producto else "Desconocido",
                    "cantidad_necesaria": insumo["cantidad_necesaria"],
                    "stock_actual": stock,
                    "suficiente": suficiente,
                    "faltante": max(insumo["cantidad_necesaria"] - stock, Decimal("0")),
                }
            )

        return {
            "disponible": todos_disponibles,
            "detalle": resultado,
        }

    @classmethod
    def _validate_ingredientes(cls, ingredientes: list[dict]):
        """
        Valida la lista de ingredientes de una receta.

        Verifica que cada ingrediente tenga producto_id y cantidad,
        que la cantidad sea > 0, y que el producto exista.
        """
        for i, ing in enumerate(ingredientes):
            if "producto_id" not in ing or "cantidad" not in ing:
                raise ValidationException(
                    f"Ingrediente {i + 1}: producto_id y cantidad son obligatorios"
                )

            cantidad = Decimal(str(ing["cantidad"]))
            if cantidad <= 0:
                raise ValidationException(
                    f"Ingrediente {i + 1}: la cantidad debe ser mayor a 0"
                )

            producto = ProductoRepository.get_by_id(ing["producto_id"])
            if not producto:
                raise ValidationException(
                    f"Ingrediente {i + 1}: producto_id={ing['producto_id']} no existe"
                )
