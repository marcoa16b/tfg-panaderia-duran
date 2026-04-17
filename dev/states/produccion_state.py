"""
produccion_state.py — Estado reactivo para producción diaria.

Arquitectura
------------
Capa State (Application Layer) para producción diaria. Registra
producciones con selección de receta, verificación de disponibilidad
de insumos y descuento automático de stock (FIFO). Incluye historial
y visualización de detalles (trazabilidad de lotes).

Patrón de diseño: Reflex State
    - Variables reactivas sincronizadas al frontend.
    - Formularios con vars separadas (form_*) para no mutar la tabla.
    - Diálogos controlados por vars booleanas (dialog_open, verificacion_open, detalle_open).
    - Delega toda la lógica a ProduccionService y RecetaService.

Relación con otras capas
------------------------
    [Producción Page] → ProduccionState
                          → ProduccionService.registrar_produccion() → [BD] + FIFO
                          → ProduccionService.get_by_fecha_range()   → [BD]
                          → ProduccionService.get_with_detalles()    → [BD]
                          → RecetaService.get_ingredientes()         → [BD]
                          → RecetaService.verificar_insumos_disponibles()

Variables de estado
-------------------
    Datos de tabla:
        - producciones: list[dict] — Producciones del periodo filtrado.
        - fecha_filtro_inicio, fecha_filtro_fin: str (ISO) — Rango de fechas.

    Formulario registro:
        - form_receta_id: Optional[int] — Receta seleccionada.
        - form_cantidad: str — Cantidad a producir.
        - form_fecha: str — Fecha de producción.
        - form_observaciones: str — Notas adicionales.
        - dialog_open: bool — Controla visibilidad del diálogo.

    Verificación de insumos:
        - verificacion_open: bool — Controla visibilidad del diálogo de verificación.
        - verificacion_resultado: dict — Detalle de insumos necesarios vs disponibles.
        - verificacion_receta_nombre: str — Nombre de la receta verificada.

    Detalle de producción:
        - detalle_open: bool — Controla visibilidad del diálogo de detalle.
        - detalle_produccion: dict — Datos de la producción con lotes consumidos.

    Catálogos:
        - recetas: list[dict] — Recetas activas para el selector.
        - ingredientes_receta: list[dict] — Ingredientes de la receta seleccionada.

Flujo de datos
--------------
1. La página se monta → on_load() inicializa fechas + carga recetas y producciones.
2. El usuario puede filtrar por periodo → filtrar_periodo() → recarga la tabla.
3. Para registrar: abrir_crear() → seleccionar receta/cantidad → verificar_disponibilidad() → guardar_produccion().
4. Al guardar, ProduccionService ejecuta FIFO y descuenta insumos automáticamente.
5. Para ver detalle: ver_detalle(id) → muestra lotes consumidos (trazabilidad).

Uso desde la capa UI:
    from dev.states.produccion_state import ProduccionState

    rx.foreach(ProduccionState.producciones, lambda p: rx.text(p["fecha"]))
    rx.button("Nueva", on_click=ProduccionState.abrir_crear)
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Optional

import reflex as rx

from dev.core.exceptions import AppException
from dev.services.produccion_service import ProduccionService
from dev.services.receta_service import RecetaService

logger = logging.getLogger("dev.states.produccion")


class ProduccionState(rx.State):
    """
    Estado reactivo para la gestión de producción diaria.

    Registra producciones asociadas a recetas, verifica disponibilidad
    de insumos antes de producir y muestra el historial con trazabilidad
    de lotes consumidos.

    Métodos principales:
        - on_load: Inicializa fechas, recetas y carga producciones.
        - load_producciones: Carga producciones filtradas por rango de fechas.
        - abrir_crear / cerrar_dialog: Abre/cierra el diálogo de registro.
        - on_receta_change: Actualiza ingredientes al cambiar de receta.
        - verificar_disponibilidad: Verifica si hay insumos suficientes.
        - guardar_produccion: Registra la producción y descuenta insumos (FIFO).
        - ver_detalle: Muestra los lotes consumidos de una producción.
        - filtrar_periodo: Recarga aplicando filtros de fecha.

    Variables reactivas:
        - producciones: Lista de producciones del periodo.
        - form_*: Datos del formulario de registro.
        - verificacion_*: Resultado de la verificación de insumos.
        - detalle_*: Datos del detalle de una producción.
        - recetas, ingredientes_receta: Catálogos de recetas.
    """

    producciones: list[dict] = []
    is_loading: bool = False
    error_message: str = ""

    dialog_open: bool = False
    form_receta_id: str = ""
    form_cantidad: str = "1"
    form_fecha: str = ""
    form_observaciones: str = ""

    verificacion_open: bool = False
    verificacion_resultado: dict = {}
    verificacion_detalle: list[dict] = []
    verificacion_receta_nombre: str = ""

    recetas: list[dict] = []
    ingredientes_receta: list[dict] = []

    detalle_open: bool = False
    detalle_produccion: dict = {}
    detalle_lotes: list[dict] = []

    fecha_filtro_inicio: str = ""
    fecha_filtro_fin: str = ""

    def on_load(self):
        """
        Inicializa la página: fechas por defecto, catálogo de recetas y producciones.

        Establece las fechas de filtro al mes actual y la fecha del
        formulario al día de hoy. Carga recetas disponibles y producciones.
        """
        hoy = date.today()
        self.form_fecha = hoy.isoformat()
        self.fecha_filtro_inicio = hoy.replace(day=1).isoformat()
        self.fecha_filtro_fin = hoy.isoformat()
        self._load_recetas()
        self.load_producciones()

    def load_producciones(self):
        """
        Carga producciones filtradas por rango de fechas.

        Si hay fechas de filtro, usa ProduccionService.get_by_fecha_range().
        Si no, carga todas con ProduccionService.get_all().

        Serializa cada producción como dict para el frontend, convirtiendo
        Decimal a str para JSON-serialización.
        """
        self.is_loading = True
        self.error_message = ""
        try:
            inicio = (
                date.fromisoformat(self.fecha_filtro_inicio)
                if self.fecha_filtro_inicio
                else None
            )
            fin = (
                date.fromisoformat(self.fecha_filtro_fin)
                if self.fecha_filtro_fin
                else None
            )
            if inicio and fin:
                producciones = ProduccionService.get_by_fecha_range(inicio, fin)
            else:
                producciones = ProduccionService.get_all()

            self.producciones = [
                {
                    "id": p.id,
                    "receta_id": p.receta_id,
                    "fecha": str(p.fecha),
                    "cantidad_producida": str(p.cantidad_producida),
                    "observaciones": p.observaciones or "",
                    "activo": p.activo,
                }
                for p in producciones
            ]
            logger.info("Producciones cargadas: %s", len(self.producciones))
        except Exception as e:
            logger.error("Error cargando producciones: %s", str(e))
            self.error_message = "Error al cargar producciones."
        finally:
            self.is_loading = False

    def filtrar_periodo(self):
        """Recarga las producciones aplicando los filtros de fecha actuales."""
        self.load_producciones()

    def abrir_crear(self):
        """
        Prepara y abre el diálogo para registrar una nueva producción.

        Selecciona la primera receta disponible, limpia el formulario
        y carga los ingredientes de la receta seleccionada.
        """
        self.form_receta_id = str(self.recetas[0]["id"]) if self.recetas else ""
        self.form_cantidad = "1"
        self.form_observaciones = ""
        self.form_fecha = date.today().isoformat()
        self.ingredientes_receta = []
        self.error_message = ""
        self.dialog_open = True
        if self.form_receta_id:
            self._load_ingredientes_receta(int(self.form_receta_id))

    def cerrar_dialog(self):
        """Cierra el diálogo de registro sin guardar."""
        self.dialog_open = False
        self.error_message = ""

    def on_receta_change(self, receta_id: str):
        """
        Actualiza la receta seleccionada y recarga sus ingredientes.

        Args:
            receta_id: ID de la receta seleccionada (como string desde el select).
        """
        self.form_receta_id = receta_id
        if self.form_receta_id:
            self._load_ingredientes_receta(int(self.form_receta_id))

    def _load_ingredientes_receta(self, receta_id: int):
        """
        Carga los ingredientes de una receta para mostrar en el formulario.

        Args:
            receta_id: PK de la receta.

        Actualiza ingredientes_receta con producto_id y cantidad de cada ingrediente.
        """
        try:
            ingredientes = RecetaService.get_ingredientes(receta_id)
            self.ingredientes_receta = [
                {
                    "producto_id": d.producto_id,
                    "cantidad": str(d.cantidad),
                }
                for d in ingredientes
            ]
        except Exception as e:
            logger.error("Error cargando ingredientes: %s", str(e))
            self.ingredientes_receta = []

    def verificar_disponibilidad(self):
        """
        Verifica si hay insumos suficientes para la producción planificada.

        Llama a RecetaService.verificar_insumos_disponibles() con la receta
        y cantidad del formulario. Muestra el resultado en un diálogo con
        el detalle de cada insumo (necesario vs disponible vs faltante).

        Returns:
            rx.toast.error si no hay receta seleccionada o cantidad <= 0.
        """
        if not self.form_receta_id:
            return rx.toast.error("Seleccione una receta.")
        cantidad = Decimal(self.form_cantidad or "0")
        if cantidad <= 0:
            return rx.toast.error("La cantidad debe ser mayor a 0.")

        try:
            receta_id_int = int(self.form_receta_id)
            result = RecetaService.verificar_insumos_disponibles(
                receta_id_int, cantidad
            )
            receta = RecetaService.get_by_id(receta_id_int)
            self.verificacion_receta_nombre = receta.nombre
            self.verificacion_detalle = [
                {
                    "nombre": d["nombre"],
                    "cantidad_necesaria": str(d["cantidad_necesaria"]),
                    "stock_actual": str(d["stock_actual"]),
                    "suficiente": d["suficiente"],
                    "faltante": str(d["faltante"]),
                }
                for d in result["detalle"]
            ]
            self.verificacion_resultado = {
                "disponible": result["disponible"],
                "cantidad": str(cantidad),
            }
            self.verificacion_open = True
        except Exception as e:
            logger.error("Error verificando: %s", str(e))
            return rx.toast.error("Error al verificar disponibilidad.")

    def cerrar_verificacion(self):
        """Cierra el diálogo de verificación de disponibilidad."""
        self.verificacion_open = False

    def guardar_produccion(self):
        """
        Registra la producción y ejecuta el descuento FIFO de insumos.

        Validaciones:
            - receta_id: obligatorio.
            - cantidad: mayor a 0.
            - fecha: obligatoria.

        Flujo:
            1. Valida los campos del formulario.
            2. Llama a ProduccionService.registrar_produccion() que ejecuta:
               - Verificación de insumos disponibles.
               - Asignación de lotes FIFO (los que vencen primero).
               - Descuento de stock de cada insumo.
            3. Cierra diálogos y recarga la tabla.

        Returns:
            rx.toast.success si se registró correctamente.
            Error en error_message si la validación o el service falla.
        """
        self.error_message = ""
        if not self.form_receta_id:
            self.error_message = "Seleccione una receta."
            return

        cantidad = Decimal(self.form_cantidad or "0")
        if cantidad <= 0:
            self.error_message = "La cantidad debe ser mayor a 0."
            return

        if not self.form_fecha:
            self.error_message = "Seleccione la fecha."
            return

        try:
            ProduccionService.registrar_produccion(
                receta_id=int(self.form_receta_id),
                fecha=date.fromisoformat(self.form_fecha),
                cantidad_producida=cantidad,
                observaciones=self.form_observaciones.strip() or None,
            )
            self.dialog_open = False
            self.verificacion_open = False
            self.load_producciones()
            return rx.toast.success(
                "Producción registrada. Insumos descontados automáticamente."
            )
        except AppException as e:
            self.error_message = e.message
        except Exception as e:
            logger.error("Error guardando producción: %s", str(e))
            self.error_message = "Error inesperado al registrar producción."

    def ver_detalle(self, produccion_id: int):
        """
        Muestra el detalle de una producción con los lotes consumidos.

        Args:
            produccion_id: PK de la producción.

        Obtiene la producción con sus detalles (lotes consumidos) y
        los datos de la receta asociada para mostrar la trazabilidad.
        """
        try:
            result = ProduccionService.get_with_detalles(produccion_id)
            produccion = result["produccion"]
            detalles = result["detalles"]
            receta = RecetaService.get_by_id(produccion.receta_id)

            self.detalle_lotes = [
                {
                    "lote_id": d.lote_id,
                    "cantidad": str(d.cantidad),
                }
                for d in detalles
            ]
            self.detalle_produccion = {
                "id": produccion.id,
                "receta_nombre": receta.nombre,
                "fecha": str(produccion.fecha),
                "cantidad_producida": str(produccion.cantidad_producida),
                "observaciones": produccion.observaciones or "",
            }
            self.detalle_open = True
        except Exception as e:
            logger.error("Error: %s", str(e))
            return rx.toast.error("Error al cargar detalle.")

    def cerrar_detalle(self):
        """Cierra el diálogo de detalle de producción."""
        self.detalle_open = False

    def _load_recetas(self):
        """Carga las recetas activas para el selector del formulario."""
        try:
            recetas = RecetaService.get_all()
            self.recetas = [{"id": r.id, "nombre": r.nombre} for r in recetas]
        except Exception as e:
            logger.error("Error cargando recetas: %s", str(e))
            self.recetas = []
