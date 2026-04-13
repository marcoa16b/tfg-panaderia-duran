"""
inventario_service.py — Servicio de entradas, salidas y cálculo de stock.

Arquitectura
------------
Capa de lógica de negocio para todo el flujo de inventario. Es el servicio
más complejo del sistema porque orquesta múltiples repositorios y tablas
para mantener la consistencia del stock.

Patrón de diseño: Service Layer
    - Valida datos de entrada/salida antes de delegar al repositorio.
    - Calcula stock por lote (entrante - salidas - producción).
    - Actualiza automáticamente el stock_actual de los productos.
    - Mantiene trazabilidad: cada movimiento queda registrado con su lote.

Relación con otras capas
------------------------
    [Entradas Page] → [EntradaSalidaState] → InventarioService → EntradaRepository
                                                              → SalidaRepository
                                                              → LoteRepository
                                                              → ProductoRepository
                                                              → [PostgreSQL]

Flujo de entrada de inventario
------------------------------
1. Se registra una EntradaInventario (cabecera: tipo, fecha, proveedor).
2. Se crean N LoteInventario (uno por producto, con cantidad y vencimiento).
3. Se actualiza el stock_actual de cada producto (+cantidad).
4. Todo en una transacción atómica via EntradaRepository.create_with_lotes().

Flujo de salida de inventario
-----------------------------
1. Se valida que cada lote tenga stock suficiente.
2. Se registra una SalidaInventario (cabecera: tipo, fecha, observaciones).
3. Se crean N DetalleSalidaInventario (cada uno referencia un lote y cantidad).
4. Se descuenta el stock_actual de cada producto (-cantidad).

Cálculo de stock por lote
-------------------------
El stock de un lote se calcula dinámicamente:
    stock_lote = cantidad_entrante
                 - SUM(detalle_salida.cantidad)   -- salidas manuales
                 - SUM(produccion_detalle.cantidad) -- consumo por producción

Tipos de salida (definidos en seed_data):
    - Consumo: Uso en producción.
    - Dañado: Producto dañado o defectuoso.
    - Vencido: Producto que pasó su fecha de vencimiento.
    - Ajuste negativo: Corrección manual de inventario.

Uso desde la capa State:
    from dev.services.inventario_service import InventarioService

    result = InventarioService.registrar_entrada(
        tipo_id=1, fecha=date.today(),
        lotes_data=[{"producto_id": 1, "cantidad": Decimal("50")}],
    )
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Optional

import reflex as rx
from sqlmodel import select

from dev.core.exceptions import NotFoundException, ValidationException
from dev.models.models import (
    EntradaInventario,
    LoteInventario,
    Producto,
    SalidaInventario,
)
from dev.repositories.entrada_repo import EntradaRepository, LoteRepository
from dev.repositories.producto_repo import ProductoRepository
from dev.repositories.salida_repo import DetalleSalidaRepository, SalidaRepository

logger = logging.getLogger("dev.services.inventario")


class InventarioService:
    """
    Servicio de gestión de entradas, salidas y stock de inventario.

    Métodos principales:
        - registrar_entrada: Crea entrada + lotes + actualiza stock (atómico).
        - registrar_salida: Crea salida + detalles + descuenta stock (valida stock).
        - get_stock_producto: Stock actual de un producto con desglose por lotes.
        - get_lotes_proximos_a_vencer: Lotes que vencen pronto (para alertas).

    Reglas de negocio:
        - Entradas sin lotes son rechazadas (ValidationException).
        - Salidas sin detalles son rechazadas.
        - Cada lote en una salida debe tener stock suficiente.
        - El stock se descuenta como valor negativo (-abs(cantidad)).
    """

    @classmethod
    def registrar_entrada(
        cls,
        tipo_id: int,
        fecha: date,
        lotes_data: list[dict],
        proveedor_id: Optional[int] = None,
        numero_factura: Optional[str] = None,
        observaciones: Optional[str] = None,
        usuario_id: Optional[int] = None,
    ) -> dict:
        """
        Registra una entrada de inventario con sus lotes.

        Flujo:
            1. Valida que haya al menos un lote.
            2. Valida cada lote: producto existe, cantidad > 0.
            3. Crea la entrada + lotes en transacción atómica.
            4. Actualiza stock_actual de cada producto (+cantidad).

        Args:
            tipo_id: FK a tipo (Compra, Donación, Ajuste positivo).
            fecha: Fecha de la entrada.
            lotes_data: Lista de dicts con {"producto_id", "cantidad",
                        "codigo_lote"?, "precio_unitario"?, "fecha_vencimiento"?}.
            proveedor_id: FK opcional a proveedor.
            numero_factura: Número de factura (opcional).
            observaciones: Notas adicionales.
            usuario_id: Usuario que registra.

        Returns:
            {"entrada": EntradaInventario, "lotes": list[LoteInventario]}

        Raises:
            ValidationException: Si no hay lotes, o algún lote tiene datos inválidos.
        """
        if not lotes_data:
            raise ValidationException("La entrada debe tener al menos un lote")

        for i, lote in enumerate(lotes_data):
            if "producto_id" not in lote or "cantidad" not in lote:
                raise ValidationException(
                    f"Lote {i + 1}: producto_id y cantidad son obligatorios"
                )
            if Decimal(str(lote["cantidad"])) <= 0:
                raise ValidationException(
                    f"Lote {i + 1}: la cantidad debe ser mayor a 0"
                )
            producto = ProductoRepository.get_by_id(lote["producto_id"])
            if not producto:
                raise ValidationException(
                    f"Lote {i + 1}: producto_id={lote['producto_id']} no existe"
                )

        entrada_data = {
            "tipo_id": tipo_id,
            "fecha": fecha,
            "proveedor_id": proveedor_id,
            "numero_factura": numero_factura,
            "observaciones": observaciones,
            "usuario_id": usuario_id,
        }

        result = EntradaRepository.create_with_lotes(entrada_data, lotes_data)

        for lote in result["lotes"]:
            ProductoRepository.update_stock(lote.producto_id, lote.cantidad)

        logger.info(
            "Entrada registrada — id=%s, lotes=%s, stock actualizado",
            result["entrada"].id,
            len(result["lotes"]),
        )
        return result

    @classmethod
    def get_entrada_with_lotes(cls, entrada_id: int) -> dict:
        """
        Obtiene una entrada con todos sus lotes.

        Returns:
            {"entrada": EntradaInventario, "lotes": list[LoteInventario]}

        Raises:
            NotFoundException: Si la entrada no existe.
        """
        result = EntradaRepository.get_with_lotes(entrada_id)
        if not result:
            raise NotFoundException(f"Entrada con id={entrada_id} no encontrada")
        return result

    @classmethod
    def get_entradas_by_fecha(
        cls, fecha_inicio: date, fecha_fin: date
    ) -> list[EntradaInventario]:
        """Entradas en un rango de fechas. Valida que inicio <= fin."""
        if fecha_inicio > fecha_fin:
            raise ValidationException(
                "La fecha de inicio no puede ser posterior a la fecha fin"
            )
        return EntradaRepository.get_by_fecha_range(fecha_inicio, fecha_fin)

    @classmethod
    def get_entradas_by_proveedor(cls, proveedor_id: int) -> list[EntradaInventario]:
        """Todas las entradas de un proveedor específico."""
        return EntradaRepository.get_by_proveedor(proveedor_id)

    @classmethod
    def registrar_salida(
        cls,
        tipo_id: int,
        fecha: date,
        detalles_data: list[dict],
        observaciones: Optional[str] = None,
        usuario_id: Optional[int] = None,
    ) -> dict:
        """
        Registra una salida de inventario con sus detalles.

        Flujo:
            1. Valida que haya al menos un detalle.
            2. Valida cada detalle: lote existe, cantidad > 0, stock suficiente.
            3. Crea la salida + detalles en transacción atómica.
            4. Descuenta stock_actual de cada producto (-cantidad).

        El stock por lote se calcula considerando tanto las salidas manuales
        como el consumo por producción (ProduccionDetalle).

        Args:
            tipo_id: FK a tipo (Consumo, Dañado, Vencido, Ajuste negativo).
            fecha: Fecha de la salida.
            detalles_data: Lista de dicts con {"lote_id", "cantidad", "motivo"?}.
            observaciones: Notas adicionales.
            usuario_id: Usuario que registra.

        Returns:
            {"salida": SalidaInventario, "detalles": list[DetalleSalidaInventario]}

        Raises:
            ValidationException: Si no hay detalles, lote no existe, o stock insuficiente.
        """
        if not detalles_data:
            raise ValidationException("La salida debe tener al menos un detalle")

        for i, detalle in enumerate(detalles_data):
            if "lote_id" not in detalle or "cantidad" not in detalle:
                raise ValidationException(
                    f"Detalle {i + 1}: lote_id y cantidad son obligatorios"
                )
            cantidad = Decimal(str(detalle["cantidad"]))
            if cantidad <= 0:
                raise ValidationException(
                    f"Detalle {i + 1}: la cantidad debe ser mayor a 0"
                )

            lote = LoteRepository.get_by_id(detalle["lote_id"])
            if not lote:
                raise ValidationException(
                    f"Detalle {i + 1}: lote_id={detalle['lote_id']} no existe"
                )

            stock_lote = cls._calcular_stock_lote(lote.id)  # type: ignore[arg-type]
            if cantidad > stock_lote:
                raise ValidationException(
                    f"Detalle {i + 1}: cantidad ({cantidad}) excede stock del lote ({stock_lote})"
                )

        salida_data = {
            "tipo_id": tipo_id,
            "fecha": fecha,
            "observaciones": observaciones,
            "usuario_id": usuario_id,
        }

        result = SalidaRepository.create_with_detalles(salida_data, detalles_data)

        for detalle in result["detalles"]:
            cantidad_negativa = -abs(detalle.cantidad)
            ProductoRepository.update_stock(detalle.lote.producto_id, cantidad_negativa)

        logger.info(
            "Salida registrada — id=%s, detalles=%s, stock descontado",
            result["salida"].id,
            len(result["detalles"]),
        )
        return result

    @classmethod
    def get_salida_with_detalles(cls, salida_id: int) -> dict:
        """
        Obtiene una salida con todos sus detalles.

        Returns:
            {"salida": SalidaInventario, "detalles": list[DetalleSalidaInventario]}

        Raises:
            NotFoundException: Si la salida no existe.
        """
        result = SalidaRepository.get_with_detalles(salida_id)
        if not result:
            raise NotFoundException(f"Salida con id={salida_id} no encontrada")
        return result

    @classmethod
    def get_salidas_by_fecha(
        cls, fecha_inicio: date, fecha_fin: date
    ) -> list[SalidaInventario]:
        """Salidas en un rango de fechas. Valida que inicio <= fin."""
        if fecha_inicio > fecha_fin:
            raise ValidationException(
                "La fecha de inicio no puede ser posterior a la fecha fin"
            )
        return SalidaRepository.get_by_fecha_range(fecha_inicio, fecha_fin)

    @classmethod
    def get_stock_producto(cls, producto_id: int) -> dict:
        """
        Retorna el stock completo de un producto.

        Incluye:
            - stock_actual del producto (campo denormalizado).
            - stock_por_lotes (suma calculada de lotes disponibles).
            - Cantidad de lotes.
            - Indicador de bajo stock.

        Returns:
            {
                "producto_id", "nombre", "stock_actual", "stock_minimo",
                "stock_por_lotes", "total_lotes", "bajo_stock"
            }
        """
        producto = ProductoRepository.get_by_id(producto_id)
        if not producto:
            raise NotFoundException(f"Producto con id={producto_id} no encontrado")

        lotes = LoteRepository.get_by_producto(producto_id)
        stock_por_lotes = sum(cls._calcular_stock_lote(l.id) for l in lotes)  # type: ignore[arg-type]

        return {
            "producto_id": producto.id,
            "nombre": producto.nombre,
            "stock_actual": producto.stock_actual,
            "stock_minimo": producto.stock_minimo,
            "stock_por_lotes": stock_por_lotes,
            "total_lotes": len(lotes),
            "bajo_stock": producto.stock_actual <= producto.stock_minimo,
        }

    @classmethod
    def get_lotes_by_producto(cls, producto_id: int) -> list[LoteInventario]:
        """Todos los lotes de un producto (para trazabilidad)."""
        return LoteRepository.get_by_producto(producto_id)

    @classmethod
    def get_lotes_proximos_a_vencer(cls, dias_limite: int = 7) -> list[LoteInventario]:
        """
        Lotes que vencen dentro de los próximos N días.

        Usado por AlertaService para generar alertas de vencimiento.

        Args:
            dias_limite: Días hacia adelante desde hoy (default: 7).

        Raises:
            ValidationException: Si dias_limite < 1.
        """
        if dias_limite < 1:
            raise ValidationException("El límite de días debe ser al menos 1")
        return LoteRepository.get_proximos_a_vencer(dias_limite=dias_limite)

    @classmethod
    def _calcular_stock_lote(cls, lote_id: int) -> Decimal:
        """
        Calcula el stock disponible de un lote.

        Fórmula:
            stock = cantidad_entrante
                    - SUM(salidas_manuales)
                    - SUM(consumo_por_produccion)

        Este cálculo dinámico permite trazabilidad completa: cada lote
        sabe exactamente cuánto se ha usado y cuánto queda.

        Args:
            lote_id: PK del lote.

        Returns:
            Stock disponible (mínimo 0, nunca negativo).
        """
        lote = LoteRepository.get_by_id(lote_id)
        if not lote:
            return Decimal("0")

        cantidad_entrante = lote.cantidad

        detalles_salida = DetalleSalidaRepository.get_by_lote(lote_id)
        cantidad_salida = sum(d.cantidad for d in detalles_salida)

        from dev.repositories.produccion_repo import ProduccionDetalleRepository

        detalles_produccion = ProduccionDetalleRepository.get_by_lote(lote_id)
        cantidad_produccion = sum(d.cantidad for d in detalles_produccion)

        stock = cantidad_entrante - cantidad_salida - cantidad_produccion
        return max(stock, Decimal("0"))
