"""
alerta_service.py — Servicio de detección y gestión de alertas de inventario.

Arquitectura
------------
Capa de lógica de negocio para el sistema de alertas. Detecta automáticamente
condiciones que requieren atención (bajo stock, productos por vencer) y genera
alertas en la tabla `alerta_inventario`.

Patrón de diseño: Service Layer
    - Detecta condiciones de alerta consultando ProductoRepository y LoteRepository.
    - Genera alertas evitando duplicados (no crea alerta si ya existe una activa).
    - Permite marcar alertas como leídas (individualmente o todas).
    - Provee un método de detección completa para ejecución periódica.

Relación con otras capas
------------------------
    [Alertas Page] → [AlertaState] → AlertaService → AlertaRepository (inline)
                                                  → ProductoRepository
                                                  → LoteRepository
                                                  → [PostgreSQL]

    [Dashboard Page] → [DashboardState] → AlertaService.ejecutar_deteccion_completa()

Tipos de alertas (definidos en seed_data):
    - Bajo stock: stock_actual <= stock_minimo.
    - Próximo a vencer: fecha_vencimiento dentro de N días.

Deduplicación
-------------
Antes de crear una alerta, se verifica si ya existe una alerta ACTIVA y NO
LEÍDA para el mismo producto y tipo. Si existe, no se crea otra.

Esto evita alertas duplicadas cuando la detección se ejecuta múltiples veces.

Flujo de detección
------------------
1. AlertaService.detectar_bajo_stock():
    - Obtiene productos con stock <= mínimo via ProductoRepository.
    - Para cada uno, verifica si ya tiene alerta activa.
    - Si no, crea la alerta con mensaje descriptivo.

2. AlertaService.detectar_proximos_a_vencer():
    - Obtiene lotes próximos a vencer via LoteRepository.
    - Para cada uno, verifica si ya tiene alerta activa.
    - Si no, crea la alerta con mensaje descriptivo.

3. AlertaService.ejecutar_deteccion_completa():
    - Ejecuta ambas detecciones y retorna un resumen.

Uso desde la capa State:
    from dev.services.alerta_service import AlertaService

    result = AlertaService.ejecutar_deteccion_completa()
    # result = {"bajo_stock": 3, "proximos_vencer": 2, "total_nuevas": 5}
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

import reflex as rx
from sqlmodel import select

from dev.core.exceptions import NotFoundException, ValidationException
from dev.models.models import AlertaInventario, ListTipo, LoteInventario, Producto, Tipo
from dev.repositories.base_repository import BaseRepository
from dev.repositories.entrada_repo import LoteRepository
from dev.repositories.producto_repo import ProductoRepository

logger = logging.getLogger("dev.services.alerta")


class AlertaRepository(BaseRepository[AlertaInventario]):
    """
    Repositorio especializado para alertas (definido dentro del service
    porque sus métodos son específicos del dominio de alertas y no se
    usan desde otros services).

    Hereda CRUD genérico de BaseRepository y agrega:
        - get_activas: Alertas activas, opcionalmente solo no leídas.
        - get_by_producto: Alertas de un producto específico.
        - exists_alerta_activa: Verifica duplicados antes de crear.
        - marcar_leida: Marca una alerta como leída.
        - marcar_todas_leidas: Marca todas las alertas pendientes.
    """

    model = AlertaInventario

    @classmethod
    def get_activas(cls, only_unread: bool = False) -> list[AlertaInventario]:
        """
        Alertas activas, ordenadas por fecha de creación (más recientes primero).

        Args:
            only_unread: Si True, excluye las alertas ya leídas.
        """
        with rx.session() as session:
            stmt = select(AlertaInventario).where(AlertaInventario.activo == True)  # noqa: E712
            if only_unread:
                stmt = stmt.where(AlertaInventario.leida == False)  # noqa: E712
            stmt = stmt.order_by(AlertaInventario.creado_en.desc())  # type: ignore[union-attr]
            return list(session.exec(stmt).all())

    @classmethod
    def get_by_producto(
        cls, producto_id: int, only_active: bool = True
    ) -> list[AlertaInventario]:
        """Alertas de un producto específico."""
        with rx.session() as session:
            stmt = select(AlertaInventario).where(
                AlertaInventario.producto_id == producto_id
            )
            if only_active:
                stmt = stmt.where(AlertaInventario.activo == True)  # noqa: E712
            return list(session.exec(stmt).all())

    @classmethod
    def exists_alerta_activa(cls, producto_id: int, tipo_id: int) -> bool:
        """
        Verifica si ya existe una alerta activa y no leída para el
        producto y tipo dados. Usado para deduplicación.
        """
        with rx.session() as session:
            stmt = select(AlertaInventario).where(
                AlertaInventario.producto_id == producto_id,
                AlertaInventario.tipo_id == tipo_id,
                AlertaInventario.activo == True,  # noqa: E712
                AlertaInventario.leida == False,  # noqa: E712
            )
            return session.exec(stmt).first() is not None

    @classmethod
    def get_activa_by_producto_tipo(
        cls, producto_id: int, tipo_id: int
    ) -> Optional[AlertaInventario]:
        """Retorna la alerta activa y no leída para el producto y tipo dados."""
        with rx.session() as session:
            stmt = select(AlertaInventario).where(
                AlertaInventario.producto_id == producto_id,
                AlertaInventario.tipo_id == tipo_id,
                AlertaInventario.activo == True,  # noqa: E712
                AlertaInventario.leida == False,  # noqa: E712
            )
            return session.exec(stmt).first()

    @classmethod
    def update_mensaje(cls, alerta_id: int, nuevo_mensaje: str) -> bool:
        """Actualiza el mensaje de una alerta existente."""
        with rx.session() as session:
            alerta = session.get(AlertaInventario, alerta_id)
            if not alerta:
                return False
            alerta.mensaje = nuevo_mensaje
            session.add(alerta)
            session.commit()
            return True

    @classmethod
    def marcar_leida(cls, alerta_id: int) -> bool:
        """Marca una alerta como leída con timestamp."""
        with rx.session() as session:
            alerta = session.get(AlertaInventario, alerta_id)
            if not alerta:
                return False
            alerta.leida = True
            alerta.fecha_leida = datetime.now(timezone.utc)
            session.add(alerta)
            session.commit()
            return True

    @classmethod
    def marcar_todas_leidas(cls) -> int:
        """Marca todas las alertas pendientes como leídas. Retorna cantidad."""
        with rx.session() as session:
            stmt = select(AlertaInventario).where(
                AlertaInventario.activo == True,  # noqa: E712
                AlertaInventario.leida == False,  # noqa: E712
            )
            alertas = session.exec(stmt).all()
            count = 0
            for alerta in alertas:
                alerta.leida = True
                alerta.fecha_leida = datetime.now(timezone.utc)
                session.add(alerta)
                count += 1
            session.commit()
            return count


class AlertaService:
    """
    Servicio de detección y gestión de alertas de inventario.

    Métodos principales:
        - detectar_bajo_stock: Genera alertas para productos con stock bajo.
        - detectar_proximos_a_vencer: Genera alertas para lotes por vencer.
        - ejecutar_deteccion_completa: Ejecuta ambas detecciones.
        - get_alertas_activas: Consultar alertas pendientes.
        - marcar_leida / marcar_todas_leidas: Gestionar alertas.

    Cuándo ejecutar la detección:
        - Al iniciar la app (bootstrap).
        - Después de registrar una salida o producción.
        - Periódicamente (ej: cada hora via scheduler).
        - Manualmente desde la página de alertas.
    """

    @classmethod
    def detectar_bajo_stock(cls) -> list[AlertaInventario]:
        """
        Detecta productos con stock_actual <= stock_minimo y genera alertas.

        Para cada producto bajo stock:
            1. Verifica si ya tiene alerta activa (deduplicación).
            2. Si no, crea una alerta con mensaje descriptivo.

        Returns:
            Lista de alertas creadas (puede ser vacía).
        """
        productos = ProductoRepository.get_below_min_stock()

        tipo_id = cls._get_tipo_id("alerta", "Bajo stock")
        if not tipo_id:
            logger.warning(
                "Tipo 'Bajo stock' no encontrado — no se pueden generar alertas"
            )
            return []

        alertas_creadas = []
        for producto in productos:
            pid: int = producto.id  # type: ignore[assignment]
            if not AlertaRepository.exists_alerta_activa(pid, tipo_id):
                alerta = AlertaRepository.create(
                    tipo_id=tipo_id,
                    producto_id=pid,
                    mensaje=f"Bajo stock: {producto.nombre} — stock actual: {producto.stock_actual}, mínimo: {producto.stock_minimo}",
                )
                alertas_creadas.append(alerta)
                logger.info(
                    "Alerta de bajo stock creada: %s (id=%s)",
                    producto.nombre,
                    alerta.id,
                )

        return alertas_creadas

    @classmethod
    def detectar_proximos_a_vencer(cls, dias_limite: int = 7) -> list[AlertaInventario]:
        """
        Detecta lotes próximos a vencer y genera alertas.

        Para cada lote próximo a vencer:
            1. Verifica si ya tiene alerta activa (deduplicación).
            2. Si no, crea una alerta con información del lote.

        Args:
            dias_limite: Días hacia adelante (default: 7).

        Returns:
            Lista de alertas creadas.
        """
        if dias_limite < 1:
            raise ValidationException("El límite de días debe ser al menos 1")

        lotes = LoteRepository.get_proximos_a_vencer(dias_limite=dias_limite)

        tipo_id = cls._get_tipo_id("alerta", "Próximo a vencer")
        if not tipo_id:
            logger.warning(
                "Tipo 'Próximo a vencer' no encontrado — no se pueden generar alertas"
            )
            return []

        alertas_creadas = []
        hoy = date.today()
        for lote in lotes:
            producto_id: int = lote.producto_id  # type: ignore[assignment]
            producto = ProductoRepository.get_by_id(producto_id)
            nombre = producto.nombre if producto else "Desconocido"
            vencimiento = lote.fecha_vencimiento or "N/A"

            vencida = (
                isinstance(lote.fecha_vencimiento, date)
                and lote.fecha_vencimiento < hoy
            )
            prefijo = "Vencido" if vencida else "Próximo a vencer"
            mensaje = f"{prefijo}: {nombre} — lote {lote.codigo_lote or lote.id}, vence: {vencimiento}"

            if not AlertaRepository.exists_alerta_activa(producto_id, tipo_id):
                alerta = AlertaRepository.create(
                    tipo_id=tipo_id,
                    producto_id=producto_id,
                    mensaje=mensaje,
                )
                alertas_creadas.append(alerta)
                logger.info(
                    "Alerta de vencimiento creada: %s lote %s (id=%s)",
                    nombre,
                    lote.id,
                    alerta.id,
                )
            elif vencida:
                existente = AlertaRepository.get_activa_by_producto_tipo(
                    producto_id, tipo_id
                )
                if existente and existente.mensaje and existente.mensaje.startswith("Próximo a vencer"):
                    AlertaRepository.update_mensaje(existente.id, mensaje)
                    logger.info(
                        "Alerta actualizada a 'Vencido': %s lote %s (id=%s)",
                        nombre,
                        lote.id,
                        existente.id,
                    )

        return alertas_creadas

    @classmethod
    def ejecutar_deteccion_completa(cls) -> dict:
        """
        Ejecuta todas las detecciones de alertas en un solo llamado.

        Retorna un resumen con la cantidad de alertas nuevas por tipo.
        Usado desde el Dashboard y desde el bootstrap de la app.

        Returns:
            {"bajo_stock": N, "proximos_vencer": M, "total_nuevas": N+M}
        """
        bajo_stock = cls.detectar_bajo_stock()
        proximos_vencer = cls.detectar_proximos_a_vencer()

        logger.info(
            "Detección completa: %s alertas bajo stock, %s alertas vencimiento",
            len(bajo_stock),
            len(proximos_vencer),
        )
        return {
            "bajo_stock": len(bajo_stock),
            "proximos_vencer": len(proximos_vencer),
            "total_nuevas": len(bajo_stock) + len(proximos_vencer),
        }

    @classmethod
    def get_alertas_activas(cls, only_unread: bool = False) -> list[AlertaInventario]:
        """
        Consulta alertas activas.

        Args:
            only_unread: Si True, solo alertas no leídas.
        """
        return AlertaRepository.get_activas(only_unread=only_unread)

    @classmethod
    def get_alertas_by_producto(cls, producto_id: int) -> list[AlertaInventario]:
        """Historial de alertas de un producto."""
        return AlertaRepository.get_by_producto(producto_id)

    @classmethod
    def marcar_leida(cls, alerta_id: int) -> bool:
        """
        Marca una alerta como leída.

        Raises:
            NotFoundException: Si la alerta no existe.
        """
        result = AlertaRepository.marcar_leida(alerta_id)
        if not result:
            raise NotFoundException(f"Alerta con id={alerta_id} no encontrada")
        logger.info("Alerta marcada como leída: id=%s", alerta_id)
        return True

    @classmethod
    def marcar_todas_leidas(cls) -> int:
        """Marca todas las alertas pendientes como leídas. Retorna la cantidad."""
        count = AlertaRepository.marcar_todas_leidas()
        logger.info("%s alertas marcadas como leídas", count)
        return count

    @classmethod
    def count_activas(cls) -> int:
        """Total de alertas no leídas (para badge de notificación)."""
        alertas = AlertaRepository.get_activas(only_unread=True)
        return len(alertas)

    @classmethod
    def _get_tipo_id(cls, list_tipo_nombre: str, tipo_nombre: str) -> Optional[int]:
        """
        Busca el ID de un tipo por su nombre y grupo (ListTipo).

        Args:
            list_tipo_nombre: Nombre del grupo ("entrada", "salida", "alerta").
            tipo_nombre: Nombre del tipo ("Bajo stock", "Próximo a vencer").

        Returns:
            El ID del tipo o None si no existe.
        """
        with rx.session() as session:
            stmt = (
                select(Tipo)
                .join(ListTipo)
                .where(
                    ListTipo.nombre == list_tipo_nombre,
                    Tipo.nombre == tipo_nombre,
                    Tipo.activo == True,  # noqa: E712
                )
            )
            tipo = session.exec(stmt).first()
            return tipo.id if tipo else None
