"""
reporte_service.py — Servicio de generación de reportes y estadísticas.

Arquitectura
------------
Capa de lógica de negocio para la generación de reportes. Realiza consultas
agregadas complejas que involucran múltiples tablas (entradas, salidas,
lotes, productos, tipos) para producir información útil para la toma
de decisiones.

Patrón de diseño: Service Layer
    - Realiza consultas agregadas con JOINs entre tablas.
    - Calcula totales, promedios y desgloses por periodo.
    - Formatea resultados como listas de dicts (fáciles de consumir por States).
    - NO escribe en la BD (solo lecturas).

Relación con otras capas
------------------------
    [Reportes Page] → [ReporteState] → ReporteService → [Consultas SQL directas]
    [Dashboard Page] → [DashboardState] → ReporteService.get_resumen_dashboard()

Reportes disponibles
--------------------
1. get_existencias_actuales: Stock de todos los productos con indicador de bajo stock.
2. get_perdidas: Productos dañados/vencidos con valor económico de la pérdida.
3. get_consumo_anual: Total consumido por producto en un año (agrupado por producto).
4. get_resumen_dashboard: KPIs para el dashboard (totales, bajo stock, por vencer).
5. get_entradas_periodo: Entradas en un rango de fechas con totales.
6. get_salidas_periodo: Salidas en un rango de fechas con totales.

Cálculo de pérdidas
-------------------
Las pérdidas se calculan a partir de salidas de tipo "Dañado" o "Vencido".
Para cada detalle de salida:
    valor_pérdida = cantidad × precio_unitario_del_lote

Esto permite saber no solo QUÉ se perdió sino CUÁNTO costó.

Consumo anual
-------------
Agrupa las salidas de tipo "Consumo" por producto en un rango de un año.
Usado para análisis de tendencias y planificación de compras.

Uso desde la capa State:
    from dev.services.reporte_service import ReporteService

    existencias = ReporteService.get_existencias_actuales()
    perdidas = ReporteService.get_perdidas(fecha_inicio=date(2025, 1, 1))
    dashboard = ReporteService.get_resumen_dashboard()
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

import reflex as rx
from sqlmodel import func, select

from dev.core.exceptions import ValidationException
from dev.models.models import (
    DetalleSalidaInventario,
    EntradaInventario,
    LoteInventario,
    Producto,
    SalidaInventario,
)

logger = logging.getLogger("dev.services.reporte")


class ReporteService:
    """
    Servicio de generación de reportes y estadísticas.

    Todos los métodos son de solo lectura (no modifican la BD).
    Retornan listas de dicts o dicts estructurados, listos para
    ser consumidos por la capa State.

    Métodos principales:
        - get_existencias_actuales: Stock de todos los productos.
        - get_perdidas: Productos dañados/vencidos con valor.
        - get_consumo_anual: Consumo por producto en un año.
        - get_resumen_dashboard: KPIs del dashboard.
        - get_entradas_periodo / get_salidas_periodo: Movimientos por periodo.
    """

    @classmethod
    def get_existencias_actuales(cls) -> list[dict]:
        """
        Reporte de existencias actuales de todos los productos activos.

        Retorna una lista con el stock de cada producto e indicador de
        bajo stock (stock_actual <= stock_minimo).

        Returns:
            [{
                "producto_id", "nombre", "categoria_id", "unidad_medida_id",
                "stock_actual", "stock_minimo", "bajo_stock", "ubicacion"
            }, ...]
        """
        with rx.session() as session:
            stmt = select(Producto).where(Producto.activo == True)  # noqa: E712
            productos = session.exec(stmt).all()

            resultado = []
            for p in productos:
                resultado.append(
                    {
                        "producto_id": p.id,
                        "nombre": p.nombre,
                        "categoria_id": p.categoria_id,
                        "unidad_medida_id": p.unidad_medida_id,
                        "stock_actual": p.stock_actual,
                        "stock_minimo": p.stock_minimo,
                        "bajo_stock": p.stock_actual <= p.stock_minimo,
                        "ubicacion": p.ubicacion,
                    }
                )

            logger.info("Reporte de existencias: %s productos", len(resultado))
            return resultado

    @classmethod
    def get_perdidas(
        cls,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
    ) -> dict:
        """
        Reporte de pérdidas por productos dañados o vencidos.

        Filtra las salidas de tipo "Dañado" o "Vencido" y calcula el
        valor económico de la pérdida usando el precio_unitario del lote.

        Args:
            fecha_inicio: Inicio del periodo (opcional).
            fecha_fin: Fin del periodo (opcional).

        Returns:
            {
                "detalles": [{
                    "fecha", "producto", "lote_id", "cantidad", "motivo",
                    "tipo", "precio_unitario", "valor_perdida"
                }, ...],
                "total_perdida": Decimal,
                "cantidad_registros": int
            }
        """
        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            raise ValidationException(
                "La fecha de inicio no puede ser posterior a la fecha fin"
            )

        with rx.session() as session:
            from dev.models.models import ListTipo, Tipo

            stmt_tipos = (
                select(Tipo.id)
                .join(ListTipo)
                .where(
                    ListTipo.nombre == "salida",
                    Tipo.nombre.in_(["Dañado", "Vencido"]),
                    Tipo.activo == True,  # noqa: E712
                )
            )
            tipos_perdida = [t for t in session.exec(stmt_tipos).all()]

            if not tipos_perdida:
                return {
                    "detalles": [],
                    "total_perdida": Decimal("0"),
                    "cantidad_registros": 0,
                }

            stmt = (
                select(DetalleSalidaInventario, SalidaInventario)
                .join(
                    SalidaInventario,
                    DetalleSalidaInventario.salida_id == SalidaInventario.id,
                )
                .where(
                    SalidaInventario.tipo_id.in_(tipos_perdida),
                    DetalleSalidaInventario.activo == True,  # noqa: E712
                    SalidaInventario.activo == True,  # noqa: E712
                )
            )

            if fecha_inicio:
                stmt = stmt.where(SalidaInventario.fecha >= fecha_inicio)
            if fecha_fin:
                stmt = stmt.where(SalidaInventario.fecha <= fecha_fin)

            rows = session.exec(stmt).all()

            detalles = []
            total_perdida = Decimal("0")

            for detalle, salida in rows:
                lote = session.get(LoteInventario, detalle.lote_id)
                producto = session.get(Producto, lote.producto_id) if lote else None
                tipo = session.get(Tipo, salida.tipo_id)

                precio_unitario = lote.precio_unitario if lote else Decimal("0")
                valor_perdida = detalle.cantidad * (precio_unitario or Decimal("0"))

                detalles.append(
                    {
                        "fecha": salida.fecha,
                        "producto": producto.nombre if producto else "Desconocido",
                        "lote_id": detalle.lote_id,
                        "cantidad": detalle.cantidad,
                        "motivo": detalle.motivo or "",
                        "tipo": tipo.nombre if tipo else "Desconocido",
                        "precio_unitario": precio_unitario,
                        "valor_perdida": valor_perdida,
                    }
                )

                total_perdida += valor_perdida

            logger.info(
                "Reporte de pérdidas: %s registros, total=%s",
                len(detalles),
                total_perdida,
            )
            return {
                "detalles": detalles,
                "total_perdida": total_perdida,
                "cantidad_registros": len(detalles),
            }

    @classmethod
    def get_consumo_anual(cls, anio: Optional[int] = None) -> list[dict]:
        """
        Reporte de consumo anual agrupado por producto.

        Filtra las salidas de tipo "Consumo" en el año especificado y
        agrupa por producto. Útil para análisis de tendencias y
        planificación de compras.

        Args:
            anio: Año a consultar (default: año actual).

        Returns:
            [{
                "producto_id", "nombre", "total_consumido", "anio"
            }, ...]
            Ordenado por total_consumido descendente.
        """
        if anio is None:
            anio = date.today().year

        fecha_inicio = date(anio, 1, 1)
        fecha_fin = date(anio, 12, 31)

        with rx.session() as session:
            from dev.models.models import ListTipo, Tipo

            stmt_tipo = (
                select(Tipo.id)
                .join(ListTipo)
                .where(
                    ListTipo.nombre == "salida",
                    Tipo.nombre == "Consumo",
                    Tipo.activo == True,  # noqa: E712
                )
            )
            tipo_consumo = session.exec(stmt_tipo).first()

            if not tipo_consumo:
                return []

            stmt = (
                select(
                    LoteInventario.producto_id,
                    func.sum(DetalleSalidaInventario.cantidad).label("total_consumido"),
                )
                .join(
                    DetalleSalidaInventario,
                    DetalleSalidaInventario.lote_id == LoteInventario.id,
                )
                .join(
                    SalidaInventario,
                    DetalleSalidaInventario.salida_id == SalidaInventario.id,
                )
                .where(
                    SalidaInventario.tipo_id == tipo_consumo,
                    SalidaInventario.fecha >= fecha_inicio,
                    SalidaInventario.fecha <= fecha_fin,
                    SalidaInventario.activo == True,  # noqa: E712
                    DetalleSalidaInventario.activo == True,  # noqa: E712
                )
                .group_by(LoteInventario.producto_id)
            )

            rows = session.exec(stmt).all()

            resultado = []
            for producto_id, total_consumido in rows:
                producto = session.get(Producto, producto_id)
                resultado.append(
                    {
                        "producto_id": producto_id,
                        "nombre": producto.nombre if producto else "Desconocido",
                        "total_consumido": total_consumido,
                        "anio": anio,
                    }
                )

            resultado.sort(key=lambda x: x["total_consumido"], reverse=True)
            logger.info("Reporte consumo anual %s: %s productos", anio, len(resultado))
            return resultado

    @classmethod
    def get_resumen_dashboard(cls) -> dict:
        """
        KPIs para el dashboard principal.

        Retorna un resumen con:
            - total_productos: Productos activos.
            - productos_bajo_stock: Productos con stock <= mínimo.
            - entradas_mes: Entradas en los últimos 30 días.
            - salidas_mes: Salidas en los últimos 30 días.
            - lotes_por_vencer: Lotes que vencen en los próximos 7 días.

        Returns:
            {
                "total_productos", "productos_bajo_stock",
                "entradas_mes", "salidas_mes", "lotes_por_vencer"
            }
        """
        with rx.session() as session:
            total_productos = session.exec(
                select(func.count())
                .select_from(Producto)
                .where(Producto.activo == True)  # noqa: E712
            ).one()

            productos_bajo_stock = session.exec(
                select(func.count())
                .select_from(Producto)
                .where(
                    Producto.activo == True,  # noqa: E712
                    Producto.stock_actual <= Producto.stock_minimo,
                )
            ).one()

            hoy = date.today()
            hace_30 = hoy - timedelta(days=30)

            entradas_mes = session.exec(
                select(func.count())
                .select_from(EntradaInventario)
                .where(
                    EntradaInventario.fecha >= hace_30,
                    EntradaInventario.activo == True,  # noqa: E712
                )
            ).one()

            salidas_mes = session.exec(
                select(func.count())
                .select_from(SalidaInventario)
                .where(
                    SalidaInventario.fecha >= hace_30,
                    SalidaInventario.activo == True,  # noqa: E712
                )
            ).one()

            lotes_por_vencer = session.exec(
                select(func.count())
                .select_from(LoteInventario)
                .where(
                    LoteInventario.fecha_vencimiento != None,  # noqa: E711
                    LoteInventario.fecha_vencimiento <= hoy + timedelta(days=7),
                    LoteInventario.activo == True,  # noqa: E712
                )
            ).one()

            return {
                "total_productos": total_productos,
                "productos_bajo_stock": productos_bajo_stock,
                "entradas_mes": entradas_mes,
                "salidas_mes": salidas_mes,
                "lotes_por_vencer": lotes_por_vencer,
            }

    @classmethod
    def get_entradas_periodo(
        cls,
        fecha_inicio: date,
        fecha_fin: date,
    ) -> list[dict]:
        """
        Entradas de inventario en un rango de fechas.

        Incluye el total de cantidad por entrada (suma de lotes) y
        datos del proveedor y tipo de entrada.

        Args:
            fecha_inicio: Inicio del periodo.
            fecha_fin: Fin del periodo.

        Returns:
            [{
                "id", "fecha", "tipo", "proveedor", "total_cantidad",
                "numero_factura", "observaciones"
            }, ...]
        """
        if fecha_inicio > fecha_fin:
            raise ValidationException(
                "La fecha de inicio no puede ser posterior a la fecha fin"
            )

        with rx.session() as session:
            from dev.models.models import Proveedor, Tipo

            stmt = (
                select(EntradaInventario)
                .where(
                    EntradaInventario.fecha >= fecha_inicio,
                    EntradaInventario.fecha <= fecha_fin,
                    EntradaInventario.activo == True,  # noqa: E712
                )
                .order_by(EntradaInventario.fecha.desc(), EntradaInventario.id.desc())
            )

            entradas = session.exec(stmt).all()
            resultado = []

            for entrada in entradas:
                proveedor = (
                    session.get(Proveedor, entrada.proveedor_id)
                    if entrada.proveedor_id
                    else None
                )
                tipo = session.get(Tipo, entrada.tipo_id)

                stmt_lotes = select(func.sum(LoteInventario.cantidad)).where(
                    LoteInventario.entrada_id == entrada.id,
                    LoteInventario.activo == True,  # noqa: E712
                )
                total_cantidad = session.exec(stmt_lotes).one() or Decimal("0")

                resultado.append(
                    {
                        "id": entrada.id,
                        "fecha": entrada.fecha,
                        "tipo": tipo.nombre if tipo else "Desconocido",
                        "proveedor": proveedor.nombre if proveedor else "N/A",
                        "total_cantidad": total_cantidad,
                        "numero_factura": entrada.numero_factura,
                        "observaciones": entrada.observaciones,
                    }
                )

            return resultado

    @classmethod
    def get_salidas_periodo(
        cls,
        fecha_inicio: date,
        fecha_fin: date,
    ) -> list[dict]:
        """
        Salidas de inventario en un rango de fechas.

        Incluye el total de cantidad por salida (suma de detalles) y
        el tipo de salida.

        Args:
            fecha_inicio: Inicio del periodo.
            fecha_fin: Fin del periodo.

        Returns:
            [{
                "id", "fecha", "tipo", "total_cantidad", "observaciones"
            }, ...]
        """
        if fecha_inicio > fecha_fin:
            raise ValidationException(
                "La fecha de inicio no puede ser posterior a la fecha fin"
            )

        with rx.session() as session:
            from dev.models.models import Tipo

            stmt = (
                select(SalidaInventario)
                .where(
                    SalidaInventario.fecha >= fecha_inicio,
                    SalidaInventario.fecha <= fecha_fin,
                    SalidaInventario.activo == True,  # noqa: E712
                )
                .order_by(SalidaInventario.fecha.desc(), SalidaInventario.id.desc())
            )

            salidas = session.exec(stmt).all()
            resultado = []

            for salida in salidas:
                tipo = session.get(Tipo, salida.tipo_id)

                stmt_detalles = select(
                    func.sum(DetalleSalidaInventario.cantidad)
                ).where(
                    DetalleSalidaInventario.salida_id == salida.id,
                    DetalleSalidaInventario.activo == True,  # noqa: E712
                )
                total_cantidad = session.exec(stmt_detalles).one() or Decimal("0")

                resultado.append(
                    {
                        "id": salida.id,
                        "fecha": salida.fecha,
                        "tipo": tipo.nombre if tipo else "Desconocido",
                        "total_cantidad": total_cantidad,
                        "observaciones": salida.observaciones,
                    }
                )

            return resultado
