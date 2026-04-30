"""
dashboard_state.py — Estado reactivo del dashboard principal.

Arquitectura
------------
Capa State (Application Layer) para la página principal del dashboard.
Carga KPIs, alertas recientes y resumen general, combinando datos de
ReporteService y AlertaService.

Patrón de diseño: Reflex State
    - Variables reactivas sincronizadas al frontend.
    - Event handlers llamados al montar la página o al interactuar.
    - Delega consultas a los services, nunca accede a la BD directamente.

Relación con otras capas
------------------------
    [Dashboard Page] → DashboardState.load_dashboard()
                          → ReporteService.get_resumen_dashboard() → [Consultas SQL]
                          → AlertaService.get_alertas_activas()     → [Tabla alerta_inventario]

Variables de estado
-------------------
    KPIs (números enteros):
        - total_productos: Productos activos en el sistema.
        - productos_bajo_stock: Productos con stock <= mínimo.
        - entradas_mes: Entradas registradas en los últimos 30 días.
        - salidas_mes: Salidas registradas en los últimos 30 días.
        - lotes_por_vencer: Lotes que vencen en los próximos 7 días.

    Alertas:
        - alertas_recientes: Lista de dicts con las últimas 10 alertas no leídas.
        - total_alertas_no_leidas: Cantidad total de alertas pendientes.

    UI:
        - is_loading: Indicador de carga.
        - error_message: Mensaje de error.

Flujo de datos
--------------
1. La página del dashboard se monta y llama a load_dashboard().
2. Se obtienen los KPIs via ReporteService.get_resumen_dashboard().
3. Se obtienen las alertas no leídas via AlertaService.get_alertas_activas().
4. Las vars se actualizan y Reflex sincroniza el frontend automáticamente.

Uso desde la capa UI:
    from dev.states.dashboard_state import DashboardState

    rx.text(DashboardState.total_productos)
    rx.foreach(DashboardState.alertas_recientes, lambda a: rx.text(a["mensaje"]))
"""

import logging
from typing import Optional

import reflex as rx

from dev.services.alerta_service import AlertaService
from dev.services.reporte_service import ReporteService

logger = logging.getLogger("dev.states.dashboard")


class DashboardState(rx.State):
    """
    Estado reactivo del dashboard principal.

    Carga y gestiona los KPIs del sistema y las alertas recientes
    para la página principal del dashboard.

    Métodos principales:
        - load_dashboard: Carga KPIs y alertas al montar la página.
        - ejecutar_deteccion: Fuerza la detección de alertas de bajo stock/vencimiento.
        - marcar_alerta_leida: Marca una alerta individual como leída.
        - marcar_todas_leidas: Marca todas las alertas pendientes como leídas.

    Variables reactivas:
        - total_productos, productos_bajo_stock, entradas_mes, salidas_mes, lotes_por_vencer:
          KPIs numéricos para las tarjetas del dashboard.
        - alertas_recientes: Lista de dicts con las alertas no leídas (máximo 10).
        - total_alertas_no_leidas: Entero para el badge de notificaciones.
    """

    total_productos: int = 0
    productos_bajo_stock: int = 0
    entradas_mes: int = 0
    salidas_mes: int = 0
    lotes_por_vencer: int = 0

    alertas_recientes: list[dict] = []
    alertas_todas: list[dict] = []
    total_alertas_no_leidas: int = 0

    is_loading: bool = False
    error_message: str = ""

    def load_dashboard(self):
        """
        Carga todos los datos del dashboard: KPIs y alertas recientes.

        Flujo:
            1. Obtiene KPIs via ReporteService.get_resumen_dashboard().
            2. Obtiene alertas no leídas via AlertaService.get_alertas_activas().
            3. Actualiza todas las variables de estado para que Reflex
               sincronice el frontend.

        Manejo de errores:
            Si alguna consulta falla, se captura la excepción y se muestra
            un mensaje genérico en error_message. El dashboard no se bloquea.
        """
        self.is_loading = True
        self.error_message = ""
        try:
            resumen = ReporteService.get_resumen_dashboard()
            self.total_productos = resumen.get("total_productos", 0)
            self.productos_bajo_stock = resumen.get("productos_bajo_stock", 0)
            self.entradas_mes = resumen.get("entradas_mes", 0)
            self.salidas_mes = resumen.get("salidas_mes", 0)
            self.lotes_por_vencer = resumen.get("lotes_por_vencer", 0)

            alertas = AlertaService.get_alertas_activas(only_unread=True)
            self.total_alertas_no_leidas = len(alertas)
            self.alertas_recientes = [
                {
                    "id": a.id,
                    "mensaje": a.mensaje,
                    "producto_id": a.producto_id,
                    "leida": a.leida,
                    "creado_en": str(a.creado_en) if a.creado_en else "",
                }
                for a in alertas[:10]
            ]

            todas = AlertaService.get_alertas_activas(only_unread=False)
            self.alertas_todas = [
                {
                    "id": a.id,
                    "mensaje": a.mensaje,
                    "producto_id": a.producto_id,
                    "leida": a.leida,
                    "creado_en": str(a.creado_en) if a.creado_en else "",
                }
                for a in todas
            ]

            logger.info(
                "Dashboard cargado — %s alertas no leídas", self.total_alertas_no_leidas
            )
        except Exception as e:
            logger.error("Error cargando dashboard: %s", str(e))
            self.error_message = "Error al cargar el dashboard."
        finally:
            self.is_loading = False

    def ejecutar_deteccion(self):
        """
        Fuerza la ejecución de detección de alertas.

        Llama a AlertaService.ejecutar_deteccion_completa() que detecta:
            - Productos con bajo stock.
            - Lotes próximos a vencer.

        Después de ejecutar, recarga el dashboard para mostrar
        las nuevas alertas detectadas.

        Returns:
            Recarga del dashboard (self.load_dashboard()).
            rx.toast.error si falla.
        """
        try:
            resultado = AlertaService.ejecutar_deteccion_completa()
            logger.info(
                "Detección ejecutada: %s nuevas alertas",
                resultado.get("total_nuevas", 0),
            )
            return self.load_dashboard()
        except Exception as e:
            logger.error("Error en detección: %s", str(e))
            return rx.toast.error("Error al ejecutar detección de alertas.")

    def marcar_alerta_leida(self, alerta_id: int):
        """
        Marca una alerta individual como leída.

        Args:
            alerta_id: PK de la alerta a marcar.

        Returns:
            Recarga del dashboard.
            rx.toast.error si la alerta no existe.
        """
        try:
            AlertaService.marcar_leida(alerta_id)
            return self.load_dashboard()
        except Exception as e:
            logger.error("Error marcando alerta: %s", str(e))
            return rx.toast.error("Error al marcar alerta como leída.")

    def marcar_todas_leidas(self):
        """
        Marca todas las alertas pendientes como leídas.

        Returns:
            Recarga del dashboard.
            rx.toast.error si falla.
        """
        try:
            count = AlertaService.marcar_todas_leidas()
            logger.info("%s alertas marcadas como leídas", count)
            return self.load_dashboard()
        except Exception as e:
            logger.error("Error marcando todas: %s", str(e))
            return rx.toast.error("Error al marcar alertas.")
