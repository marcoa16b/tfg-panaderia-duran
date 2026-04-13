"""
produccion_service.py — Servicio de producción diaria y descuento automático de insumos.

Arquitectura
------------
Capa de lógica de negocio para el registro de producción. Es el servicio
más crítico del sistema porque conecta recetas → insumos → lotes → stock,
realizando el descuento automático de insumos según la receta utilizada.

Patrón de diseño: Service Layer
    - Verifica disponibilidad de insumos via RecetaService.
    - Asigna lotes FIFO (los que vencen primero se consumen primero).
    - Descuenta stock automáticamente al registrar producción.
    - Registra trazabilidad: qué lote se usó para cada producción.

Relación con otras capas
------------------------
    [Producción Page] → [ProduccionState] → ProduccionService → ProduccionRepository
                                                            → RecetaService
                                                            → LoteRepository
                                                            → ProductoRepository
                                                            → [PostgreSQL]

Flujo de producción
-------------------
1. El usuario selecciona una receta y una cantidad a producir.
2. RecetaService.calcular_insumos_necesarios() calcula los insumos.
3. RecetaService.verificar_insumos_disponibles() verifica que haya stock.
4. Se asignan lotes FIFO (los que vencen primero se consumen primero).
5. Se crea ProduccionDiaria + ProduccionDetalle en transacción atómica.
6. Se descuenta el stock de cada producto insumo.

Algoritmo FIFO (First In, First Out)
-------------------------------------
Los lotes se ordenan por fecha de vencimiento (los que vencen primero primero).
Para cada insumo, se consumen lotes en orden hasta cubrir la cantidad necesaria.

Ejemplo:
    Se necesitan 5000g de Harina.
    Lote A: 3000g, vence 2025-02-01 → se consumen 3000g
    Lote B: 4000g, vence 2025-03-01 → se consumen 2000g (sobran 2000g)
    ProduccionDetalle: {lote A: 3000g, lote B: 2000g}

Trazabilidad
------------
Cada ProduccionDetalle registra:
    - produccion_id: Qué producción consumió el insumo.
    - lote_id: De qué lote específico se tomó.
    - cantidad: Cuánto se consumió de ese lote.

Esto permite responder: "¿De qué lote salió la harina usada en la
producción del 15 de enero?" → consulta por produccion_id y lote_id.

Uso desde la capa State:
    from dev.services.produccion_service import ProduccionService

    result = ProduccionService.registrar_produccion(
        receta_id=1,
        fecha=date.today(),
        cantidad_producida=Decimal("10"),
        usuario_id=1,
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
from dev.models.models import LoteInventario, ProduccionDetalle, ProduccionDiaria
from dev.repositories.entrada_repo import LoteRepository
from dev.repositories.produccion_repo import (
    ProduccionDetalleRepository,
    ProduccionRepository,
)
from dev.repositories.producto_repo import ProductoRepository
from dev.services.receta_service import RecetaService

logger = logging.getLogger("dev.services.produccion")


class ProduccionService:
    """
    Servicio de producción diaria con descuento automático de insumos.

    Métodos principales:
        - registrar_produccion: Registro completo con validación, FIFO y descuento.
        - get_with_detalles: Producción con trazabilidad de lotes consumidos.
        - get_by_fecha_range: Producciones en un rango de fechas.
        - get_by_receta: Historial de producción de una receta.
        - deactivate: Soft delete de una producción.

    Algoritmo de asignación de lotes:
        _asignar_lotes_fifo() consume lotes en orden de vencimiento.
        Si no hay suficientes lotes para algún insumo, lanza ValidationException.
    """

    @classmethod
    def get_by_id(cls, produccion_id: int) -> ProduccionDiaria:
        """Obtiene una producción por ID."""
        produccion = ProduccionRepository.get_by_id(produccion_id)
        if not produccion:
            raise NotFoundException(f"Producción con id={produccion_id} no encontrada")
        return produccion

    @classmethod
    def get_with_detalles(cls, produccion_id: int) -> dict:
        """
        Obtiene una producción con todos sus detalles de lotes consumidos.

        Returns:
            {"produccion": ProduccionDiaria, "detalles": list[ProduccionDetalle]}
        """
        result = ProduccionRepository.get_with_detalles(produccion_id)
        if not result:
            raise NotFoundException(f"Producción con id={produccion_id} no encontrada")
        return result

    @classmethod
    def get_all(cls, only_active: bool = True) -> list[ProduccionDiaria]:
        """Todas las producciones. Filtra inactivas por defecto."""
        return ProduccionRepository.get_all(only_active=only_active)

    @classmethod
    def get_by_fecha_range(
        cls, fecha_inicio: date, fecha_fin: date
    ) -> list[ProduccionDiaria]:
        """Producciones en un rango de fechas."""
        if fecha_inicio > fecha_fin:
            raise ValidationException(
                "La fecha de inicio no puede ser posterior a la fecha fin"
            )
        return ProduccionRepository.get_by_fecha_range(fecha_inicio, fecha_fin)

    @classmethod
    def get_by_receta(cls, receta_id: int) -> list[ProduccionDiaria]:
        """Historial de producción de una receta específica."""
        return ProduccionRepository.get_by_receta(receta_id)

    @classmethod
    def registrar_produccion(
        cls,
        receta_id: int,
        fecha: date,
        cantidad_producida: Decimal,
        usuario_id: Optional[int] = None,
        observaciones: Optional[str] = None,
    ) -> dict:
        """
        Registra una producción completa con descuento automático de insumos.

        Flujo:
            1. Valida cantidad_producida > 0.
            2. Obtiene la receta con sus ingredientes.
            3. Verifica que haya insumos suficientes (sino lanza ValidationException).
            4. Asigna lotes FIFO (vencimiento más próximo primero).
            5. Crea ProduccionDiaria + ProduccionDetalle en transacción atómica.
            6. Descuenta stock_actual de cada insumo.

        Args:
            receta_id: Receta que se va a producir.
            fecha: Fecha de producción.
            cantidad_producida: Unidades producidas.
            usuario_id: Usuario que registra.
            observaciones: Notas adicionales.

        Returns:
            {"produccion": ProduccionDiaria, "detalles": list[ProduccionDetalle]}

        Raises:
            ValidationException: Si cantidad <= 0 o insumos insuficientes.
            NotFoundException: Si la receta no existe.
        """
        if cantidad_producida <= 0:
            raise ValidationException("La cantidad producida debe ser mayor a 0")

        receta_data = RecetaService.get_with_detalles(receta_id)

        disponibilidad = RecetaService.verificar_insumos_disponibles(
            receta_id, cantidad_producida
        )
        if not disponibilidad["disponible"]:
            faltantes = [d for d in disponibilidad["detalle"] if not d["suficiente"]]
            msgs = [
                f"{f['nombre']}: necesita {f['cantidad_necesaria']}, hay {f['stock_actual']}"
                for f in faltantes
            ]
            raise ValidationException(f"Insumos insuficientes: {'; '.join(msgs)}")

        insumos_necesarios = RecetaService.calcular_insumos_necesarios(
            receta_id, cantidad_producida
        )

        consumo_por_lote = cls._asignar_lotes_fifo(insumos_necesarios)

        produccion_data = {
            "receta_id": receta_id,
            "fecha": fecha,
            "cantidad_producida": cantidad_producida,
            "usuario_id": usuario_id,
            "observaciones": observaciones,
        }

        detalles_data = []
        for consumo in consumo_por_lote:
            detalles_data.append(
                {
                    "lote_id": consumo["lote_id"],
                    "cantidad": consumo["cantidad"],
                }
            )

        result = ProduccionRepository.create_with_detalles(
            produccion_data, detalles_data
        )

        for consumo in consumo_por_lote:
            lote = LoteRepository.get_by_id(consumo["lote_id"])
            if lote:
                ProductoRepository.update_stock(lote.producto_id, -consumo["cantidad"])

        logger.info(
            "Producción registrada — id=%s, receta=%s, cantidad=%s, lotes consumidos=%s",
            result["produccion"].id,
            receta_id,
            cantidad_producida,
            len(consumo_por_lote),
        )
        return result

    @classmethod
    def deactivate(cls, produccion_id: int) -> bool:
        """Desactiva una producción (soft delete). Los detalles permanecen."""
        cls.get_by_id(produccion_id)
        logger.info("Producción desactivada: id=%s", produccion_id)
        return ProduccionRepository.soft_delete(produccion_id)

    @classmethod
    def _asignar_lotes_fifo(cls, insumos_necesarios: list[dict]) -> list[dict]:
        """
        Asigna lotes a cada insumo usando el algoritmo FIFO.

        Para cada insumo:
            1. Obtiene lotes del producto ordenados por fecha de vencimiento.
            2. Consume lotes en orden hasta cubrir la cantidad necesaria.
            3. Registra qué lote y cuánto se consumió de cada uno.

        Los lotes sin fecha de vencimiento se consumen últimos.

        Args:
            insumos_necesarios: [{"producto_id", "cantidad_necesaria"}, ...]

        Returns:
            [{"lote_id", "producto_id", "cantidad"}, ...]

        Raises:
            ValidationException: Si no hay suficientes lotes para algún insumo.
        """
        consumo_por_lote = []

        for insumo in insumos_necesarios:
            producto_id = insumo["producto_id"]
            cantidad_pendiente = insumo["cantidad_necesaria"]

            lotes_disponibles = cls._get_lotes_disponibles_ordenados(producto_id)

            for lote in lotes_disponibles:
                if cantidad_pendiente <= 0:
                    break

                stock_lote = cls._calcular_stock_lote_disponible(lote.id)  # type: ignore[arg-type]
                if stock_lote <= 0:
                    continue

                cantidad_a_consumir = min(cantidad_pendiente, stock_lote)

                consumo_por_lote.append(
                    {
                        "lote_id": lote.id,
                        "producto_id": producto_id,
                        "cantidad": cantidad_a_consumir,
                    }
                )

                cantidad_pendiente -= cantidad_a_consumir

            if cantidad_pendiente > 0:
                raise ValidationException(
                    f"No hay suficientes lotes disponibles para producto_id={producto_id}"
                )

        return consumo_por_lote

    @classmethod
    def _get_lotes_disponibles_ordenados(cls, producto_id: int) -> list[LoteInventario]:
        """
        Obtiene lotes de un producto ordenados por fecha de vencimiento (FIFO).

        Lotes sin fecha de vencimiento se colocan al final.
        Solo incluye lotes activos.
        """
        lotes = LoteRepository.get_by_producto(producto_id, only_active=True)

        def sort_key(lote):
            if lote.fecha_vencimiento is None:
                return (1, date.max)
            return (0, lote.fecha_vencimiento)

        return sorted(lotes, key=sort_key)

    @classmethod
    def _calcular_stock_lote_disponible(cls, lote_id: int) -> Decimal:
        """
        Calcula el stock disponible de un lote para producción.

        Fórmula: cantidad_entrante - cantidad_consumida_en_produccion.

        A diferencia de InventarioService._calcular_stock_lote(), este método
        solo descuenta el consumo por producción (no las salidas manuales,
        que ya se registran por separado via SalidaRepository).
        """
        lote = LoteRepository.get_by_id(lote_id)
        if not lote:
            return Decimal("0")

        cantidad_entrante = lote.cantidad

        with rx.session() as session:
            stmt = select(ProduccionDetalle).where(
                ProduccionDetalle.lote_id == lote_id,
                ProduccionDetalle.activo == True,  # noqa: E712
            )
            cantidad_consumida = sum(d.cantidad for d in session.exec(stmt).all())

        stock = cantidad_entrante - cantidad_consumida
        return max(stock, Decimal("0"))
