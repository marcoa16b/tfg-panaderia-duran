"""
reporte_state.py — Estado reactivo para generación de reportes.

Arquitectura
------------
Capa State (Application Layer) para reportes. Genera tres tipos de
reporte con filtros de fecha: existencias actuales, pérdidas
(dañado/vencido) y consumo anual. Incluye exportación a CSV.

Patrón de diseño: Reflex State
    - Variables reactivas sincronizadas al frontend.
    - Tabs controladas por tab_activa que determina qué reporte cargar.
    - Delega consultas a ReporteService, nunca accede a la BD directamente.

Relación con otras capas
------------------------
    [Reportes Page] → ReporteState
                        → ReporteService.get_existencias_actuales()  → [Consultas SQL]
                        → ReporteService.get_perdidas()              → [Consultas SQL]
                        → ReporteService.get_consumo_anual()         → [Consultas SQL]

Variables de estado
-------------------
    Tab activa:
        - tab_activa: str — "existencias" | "perdidas" | "consumo".

    Datos de reporte:
        - existencias: list[dict] — Productos con stock actual y mínimo.
        - perdidas: list[dict] — Detalles de productos dañados/vencidos.
        - consumo_anual: list[dict] — Consumo agrupado por producto/año.

    Filtros:
        - filtro_fecha_inicio, filtro_fecha_fin: str (ISO) — Rango para pérdidas.
        - filtro_anio: str — Año para consumo anual.

    Resumen pérdidas:
        - total_perdida: str — Valor económico total de las pérdidas.
        - cantidad_perdidas: int — Cantidad de registros de pérdida.

    UI:
        - is_loading: Indicador de carga.
        - error_message: Mensaje de error.

Flujo de datos
--------------
1. La página se monta y llama a on_load() → inicializa fechas + carga reporte.
2. Al cambiar de tab → set_tab() → recarga el reporte correspondiente.
3. Para filtrar: filtrar() → recarga con los filtros de fecha actuales.
4. Para exportar: exportar_csv() → genera archivo CSV en temporal.

Uso desde la capa UI:
    from dev.states.reporte_state import ReporteState

    rx.tabs(ReporteState.tab_activa, on_change=ReporteState.set_tab)
    rx.foreach(ReporteState.existencias, lambda e: rx.text(e["nombre"]))
"""

import logging
from datetime import date
from typing import Optional

import reflex as rx

from dev.core.exceptions import AppException
from dev.services.reporte_service import ReporteService

logger = logging.getLogger("dev.states.reporte")


class ReporteState(rx.State):
    """
    Estado reactivo para la generación de reportes del inventario.

    Gestiona tres tipos de reporte con tabs: existencias actuales,
    pérdidas (dañado/vencido) y consumo anual. Incluye filtros de
    fecha y exportación a CSV.

    Métodos principales:
        - on_load: Inicializa fechas y carga el reporte al montar la página.
        - set_tab: Cambia el tipo de reporte y lo recarga.
        - load_reporte: Despacha al loader según tab_activa.
        - load_existencias / load_perdidas / load_consumo_anual: Cargan cada reporte.
        - filtrar: Recarga aplicando los filtros de fecha actuales.
        - exportar_csv: Genera un archivo CSV del reporte activo.

    Variables reactivas:
        - tab_activa: Tab activa ("existencias", "perdidas", "consumo").
        - existencias, perdidas, consumo_anual: Datos de cada reporte.
        - filtro_fecha_inicio, filtro_fecha_fin: Rango de fechas (ISO).
        - filtro_anio: Año para el reporte de consumo.
        - total_perdida, cantidad_perdidas: Resumen del reporte de pérdidas.
    """

    tab_activa: str = "existencias"

    existencias: list[dict] = []
    perdidas: list[dict] = []
    consumo_anual: list[dict] = []

    is_loading: bool = False
    error_message: str = ""

    filtro_fecha_inicio: str = ""
    filtro_fecha_fin: str = ""
    filtro_anio: str = str(date.today().year)

    total_perdida: str = "0"
    cantidad_perdidas: int = 0

    @rx.var
    def existencias_bajo_stock(self) -> int:
        return sum(1 for e in self.existencias if e.get("bajo_stock"))

    def on_load(self):
        """
        Inicializa las fechas de filtro al mes actual y carga el reporte.

        Establece filtro_fecha_inicio al primer día del mes y
        filtro_fecha_fin al día de hoy, luego carga el reporte activo.
        """
        hoy = date.today()
        self.filtro_fecha_inicio = hoy.replace(day=1).isoformat()
        self.filtro_fecha_fin = hoy.isoformat()
        self.load_reporte()

    def set_tab(self, tab: str):
        """
        Cambia la tab activa y recarga el reporte correspondiente.

        Args:
            tab: Nombre de la tab ("existencias", "perdidas", "consumo").
        """
        self.tab_activa = tab
        self.load_reporte()

    def load_reporte(self):
        """
        Despacha la carga del reporte según la tab activa.

        Llama al método de carga específico según tab_activa:
        - "existencias" → load_existencias()
        - "perdidas" → load_perdidas()
        - "consumo" → load_consumo_anual()
        """
        if self.tab_activa == "existencias":
            self.load_existencias()
        elif self.tab_activa == "perdidas":
            self.load_perdidas()
        elif self.tab_activa == "consumo":
            self.load_consumo_anual()

    def load_existencias(self):
        """
        Carga el reporte de existencias actuales de todos los productos.

        Obtiene cada producto con su stock actual, stock mínimo e
        indicador de bajo stock via ReporteService.get_existencias_actuales().

        Los campos Decimal se convierten a str para JSON-serialización.
        """
        self.is_loading = True
        self.error_message = ""
        try:
            data = ReporteService.get_existencias_actuales()
            self.existencias = [
                {
                    "producto_id": r["producto_id"],
                    "nombre": r["nombre"],
                    "stock_actual": str(r["stock_actual"]),
                    "stock_minimo": str(r["stock_minimo"]),
                    "bajo_stock": r["bajo_stock"],
                    "ubicacion": r.get("ubicacion", ""),
                }
                for r in data
            ]
            logger.info("Existencias cargadas: %s productos", len(self.existencias))
        except Exception as e:
            logger.error("Error cargando existencias: %s", str(e))
            self.error_message = "Error al cargar existencias."
        finally:
            self.is_loading = False

    def load_perdidas(self):
        """
        Carga el reporte de pérdidas (productos dañados/vencidos).

        Aplica los filtros de fecha (filtro_fecha_inicio, filtro_fecha_fin)
        para obtener las salidas de tipo "Dañado" o "Vencido".

        Flujo:
            1. Parsea las fechas de filtro desde ISO string.
            2. Llama a ReporteService.get_perdidas() con el rango.
            3. Serializa cada registro incluyendo valor económico.
            4. Almacena total_perdida y cantidad_perdidas como resumen.

        Raises:
            AppException: Si las fechas son inválidas.
        """
        self.is_loading = True
        self.error_message = ""
        try:
            inicio = (
                date.fromisoformat(self.filtro_fecha_inicio)
                if self.filtro_fecha_inicio
                else None
            )
            fin = (
                date.fromisoformat(self.filtro_fecha_fin)
                if self.filtro_fecha_fin
                else None
            )

            result = ReporteService.get_perdidas(fecha_inicio=inicio, fecha_fin=fin)
            self.perdidas = [
                {
                    "fecha": str(r["fecha"]),
                    "producto": r["producto"],
                    "lote_id": r["lote_id"],
                    "cantidad": str(r["cantidad"]),
                    "motivo": r["motivo"],
                    "tipo": r["tipo"],
                    "precio_unitario": str(r["precio_unitario"] or "0"),
                    "valor_perdida": str(r["valor_perdida"]),
                }
                for r in result["detalles"]
            ]
            self.total_perdida = str(result["total_perdida"])
            self.cantidad_perdidas = result["cantidad_registros"]
            logger.info("Pérdidas cargadas: %s registros", self.cantidad_perdidas)
        except AppException as e:
            self.error_message = e.message
        except Exception as e:
            logger.error("Error cargando pérdidas: %s", str(e))
            self.error_message = "Error al cargar pérdidas."
        finally:
            self.is_loading = False

    def load_consumo_anual(self):
        """
        Carga el reporte de consumo anual agrupado por producto.

        Usa filtro_anio para obtener el año. Si no está establecido,
        usa el año actual como fallback.

        Flujo:
            1. Parsea filtro_anio a int (default: año actual).
            2. Llama a ReporteService.get_consumo_anual().
            3. Serializa cada registro con total_consumido como str.
        """
        self.is_loading = True
        self.error_message = ""
        try:
            anio = int(self.filtro_anio) if self.filtro_anio else date.today().year
            data = ReporteService.get_consumo_anual(anio=anio)
            self.consumo_anual = [
                {
                    "producto_id": r["producto_id"],
                    "nombre": r["nombre"],
                    "total_consumido": str(r["total_consumido"]),
                    "anio": r["anio"],
                }
                for r in data
            ]
            logger.info("Consumo anual cargado: %s productos", len(self.consumo_anual))
        except Exception as e:
            logger.error("Error cargando consumo anual: %s", str(e))
            self.error_message = "Error al cargar consumo anual."
        finally:
            self.is_loading = False

    def filtrar(self):
        """Recarga el reporte aplicando los filtros de fecha actuales."""
        self.load_reporte()

    def exportar_csv(self):
        """
        Exporta el reporte activo a CSV y lo descarga al navegador.

        Returns:
            rx.download con el archivo CSV.
            rx.toast.info si no hay datos.
            rx.toast.error si falla.
        """
        self.is_loading = True
        try:
            if self.tab_activa == "existencias":
                data = self.existencias
                filename = f"existencias_{date.today().isoformat()}.csv"
            elif self.tab_activa == "perdidas":
                data = self.perdidas
                filename = f"perdidas_{date.today().isoformat()}.csv"
            elif self.tab_activa == "consumo":
                data = self.consumo_anual
                filename = f"consumo_anual_{date.today().isoformat()}.csv"
            else:
                data = []
                filename = "reporte.csv"

            if not data:
                return rx.toast.info("No hay datos para exportar.")

            import csv
            import io

            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

            logger.info("CSV generado para descarga: %s", filename)
            return rx.download(data=output.getvalue(), filename=filename)
        except Exception as e:
            logger.error("Error exportando CSV: %s", str(e))
            return rx.toast.error("Error al exportar reporte.")
        finally:
            self.is_loading = False

    def _get_reporte_config(self) -> Optional[dict]:
        """Retorna la configuración de headers y rows según la tab activa."""
        if self.tab_activa == "existencias":
            return {
                "titulo": "Reporte de Existencias",
                "subtitulo": "Stock actual de todos los productos",
                "hoja": "Existencias",
                "headers": ["Producto", "Stock Actual", "Stock Mínimo", "Bajo Stock", "Ubicación"],
                "rows": [
                    [e.get("nombre", ""), e.get("stock_actual", ""), e.get("stock_minimo", ""),
                     "Sí" if e.get("bajo_stock") else "No", e.get("ubicacion", "")]
                    for e in self.existencias
                ],
                "filename_base": "existencias",
            }
        elif self.tab_activa == "perdidas":
            return {
                "titulo": "Reporte de Pérdidas",
                "subtitulo": "Productos dañados y vencidos",
                "hoja": "Pérdidas",
                "headers": ["Fecha", "Producto", "Cantidad", "Motivo", "Tipo", "Valor Pérdida"],
                "rows": [
                    [p.get("fecha", ""), p.get("producto", ""), p.get("cantidad", ""),
                     p.get("motivo", ""), p.get("tipo", ""), p.get("valor_perdida", "")]
                    for p in self.perdidas
                ],
                "filename_base": "perdidas",
            }
        elif self.tab_activa == "consumo":
            return {
                "titulo": "Reporte de Consumo Anual",
                "subtitulo": f"Año {self.filtro_anio}",
                "hoja": "Consumo Anual",
                "headers": ["Producto", "Total Consumido", "Año"],
                "rows": [
                    [c.get("nombre", ""), c.get("total_consumido", ""), str(c.get("anio", ""))]
                    for c in self.consumo_anual
                ],
                "filename_base": "consumo_anual",
            }
        return None

    def exportar_pdf(self):
        """
        Genera PDF en memoria y lo descarga al navegador del usuario.

        Returns:
            rx.download con los bytes del PDF.
            rx.toast.info si no hay datos.
            rx.toast.error si falla.
        """
        self.is_loading = True
        try:
            config = self._get_reporte_config()
            if not config or not config["rows"]:
                return rx.toast.info("No hay datos para exportar.")

            from dev.services.export_service import ExportService

            filename = f"{config['filename_base']}_{date.today().isoformat()}.pdf"
            pdf_bytes = ExportService.generate_pdf(
                titulo=config["titulo"],
                subtitulo=config["subtitulo"],
                headers=config["headers"],
                rows=config["rows"],
            )
            logger.info("PDF generado para descarga: %s (%s bytes)", filename, len(pdf_bytes))
            return rx.download(data=pdf_bytes, filename=filename)
        except Exception as e:
            logger.error("Error exportando PDF: %s", str(e))
            return rx.toast.error("Error al exportar PDF.")
        finally:
            self.is_loading = False

    def exportar_excel(self):
        """
        Genera Excel en memoria y lo descarga al navegador del usuario.

        Returns:
            rx.download con los bytes del Excel.
            rx.toast.info si no hay datos.
            rx.toast.error si falla.
        """
        self.is_loading = True
        try:
            config = self._get_reporte_config()
            if not config or not config["rows"]:
                return rx.toast.info("No hay datos para exportar.")

            from dev.services.export_service import ExportService

            filename = f"{config['filename_base']}_{date.today().isoformat()}.xlsx"
            xlsx_bytes = ExportService.generate_excel(
                titulo=config["hoja"],
                headers=config["headers"],
                rows=config["rows"],
            )
            logger.info("Excel generado para descarga: %s (%s bytes)", filename, len(xlsx_bytes))
            return rx.download(data=xlsx_bytes, filename=filename)
        except Exception as e:
            logger.error("Error exportando Excel: %s", str(e))
            return rx.toast.error("Error al exportar Excel.")
        finally:
            self.is_loading = False
