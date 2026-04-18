"""
entrada_salida_state.py — Estado reactivo para entradas y salidas de inventario.

Arquitectura
------------
Capa State (Application Layer) para entradas y salidas de inventario.
Gestiona el ciclo completo: entradas (compras, donaciones, ajustes)
con lotes, y salidas (consumo, dañado, vencido, ajuste) con detalles
por lote. Incluye visualización de detalles de cada operación.

Patrón de diseño: Reflex State
    - Variables reactivas sincronizadas al frontend.
    - Tabs controladas por tab_activa ("entradas" | "salidas").
    - Formularios separados para entrada y salida con vars form_entrada_*
      y form_salida_*.
    - Lotes dinámicos en entradas (form_entrada_lotes: list[dict]).
    - Detalles dinámicos en salidas (form_salida_detalles: list[dict]).
    - Diálogos controlados por vars booleanas.
    - Delega toda la lógica a InventarioService y ReporteService.

Relación con otras capas
------------------------
    [Entradas Page] → EntradaSalidaState
                        → InventarioService.registrar_entrada()    → [BD] + lotes + stock
                        → InventarioService.get_entrada_with_lotes() → [BD]
    [Salidas Page]  → EntradaSalidaState
                        → InventarioService.registrar_salida()      → [BD] + stock
                        → InventarioService.get_salida_with_detalles() → [BD]
                        → ReporteService.get_entradas_periodo()     → [Consultas SQL]
                        → ReporteService.get_salidas_periodo()      → [Consultas SQL]

Variables de estado
-------------------
    Tab activa:
        - tab_activa: str — "entradas" | "salidas".

    Datos de tabla:
        - entradas: list[dict] — Entradas del periodo filtrado.
        - salidas: list[dict] — Salidas del periodo filtrado.
        - fecha_inicio, fecha_fin: str (ISO) — Rango de fechas.

    Formulario entrada:
        - form_entrada_tipo_id, form_entrada_proveedor_id.
        - form_entrada_fecha, form_entrada_factura, form_entrada_observaciones.
        - form_entrada_lotes: list[dict] — Lotes dinámicos (producto, cantidad, vencimiento, código).
        - dialog_entrada_open: bool.

    Formulario salida:
        - form_salida_tipo_id, form_salida_fecha, form_salida_observaciones.
        - form_salida_detalles: list[dict] — Detalles dinámicos (lote, cantidad, motivo).
        - dialog_salida_open: bool.

    Detalles:
        - detalle_entrada_open / detalle_entrada: Detalle de entrada con lotes.
        - detalle_salida_open / detalle_salida: Detalle de salida con motivos.

    Catálogos:
        - productos, proveedores, tipos_entrada, tipos_salida, lotes_disponibles.

Flujo de datos
--------------
1. La página se monta → on_load() carga catálogos, fechas, entradas y salidas.
2. Al cambiar de tab → set_tab() → recarga la lista correspondiente.
3. Para registrar entrada: abrir_crear_entrada() → agregar lotes → guardar_entrada().
4. Para registrar salida: abrir_crear_salida() → seleccionar lotes → guardar_salida().
5. Para filtrar: filtrar_periodo() → recarga ambas listas.
6. Para ver detalle: ver_detalle_entrada(id) / ver_detalle_salida(id).

Uso desde la capa UI:
    from dev.states.entrada_salida_state import EntradaSalidaState

    rx.tabs(EntradaSalidaState.tab_activa, on_change=EntradaSalidaState.set_tab)
    rx.foreach(EntradaSalidaState.entradas, lambda e: rx.text(e["fecha"]))
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

import reflex as rx

from dev.core.exceptions import AppException
from dev.services.inventario_service import InventarioService

logger = logging.getLogger("dev.states.entrada_salida")


class EntradaSalidaState(rx.State):
    """
    Estado reactivo para la gestión de entradas y salidas de inventario.

    Gestiona el ciclo completo de entradas (con lotes) y salidas
    (con detalles por lote). Usa tabs para alternar entre ambas vistas.

    Métodos principales:
        - on_load: Inicializa catálogos, fechas y carga ambas listas.
        - set_tab: Alterna entre entradas y salidas.
        - load_entradas / load_salidas: Cargan datos filtrados por fecha.
        - abrir_crear_entrada / guardar_entrada: Registro de entradas con lotes.
        - abrir_crear_salida / guardar_salida: Registro de salidas con detalles.
        - agregar_lote / eliminar_lote / set_lote_*: Gestión dinámica de lotes.
        - agregar_detalle_salida / eliminar_detalle_salida / set_detalle_*: Gestión dinámica de detalles.
        - ver_detalle_entrada / ver_detalle_salida: Visualización de operaciones.
        - filtrar_periodo: Recarga aplicando filtros de fecha.

    Variables reactivas:
        - tab_activa: Tab activa ("entradas" | "salidas").
        - form_entrada_lotes: Lista dinámica de lotes para entradas.
        - form_salida_detalles: Lista dinámica de detalles para salidas.
        - productos, proveedores, tipos_entrada, tipos_salida: Catálogos.
    """

    tab_activa: str = "entradas"

    entradas: list[dict] = []
    salidas: list[dict] = []
    is_loading: bool = False
    error_message: str = ""

    fecha_inicio: str = ""
    fecha_fin: str = ""

    dialog_entrada_open: bool = False
    dialog_salida_open: bool = False

    form_entrada_tipo_id: str = ""
    form_entrada_proveedor_id: str = ""
    form_entrada_fecha: str = ""
    form_entrada_factura: str = ""
    form_entrada_observaciones: str = ""
    form_entrada_lotes: list[dict] = []

    form_salida_tipo_id: str = ""
    form_salida_fecha: str = ""
    form_salida_observaciones: str = ""
    form_salida_detalles: list[dict] = []

    productos: list[dict] = []
    proveedores: list[dict] = []
    tipos_entrada: list[dict] = []
    tipos_salida: list[dict] = []
    lotes_disponibles: list[dict] = []

    detalle_entrada_open: bool = False
    detalle_entrada: dict = {}
    detalle_entrada_lotes: list[dict] = []
    detalle_salida_open: bool = False
    detalle_salida: dict = {}
    detalle_salida_detalles: list[dict] = []

    def set_tab(self, tab: str):
        """
        Cambia la tab activa y recarga la lista correspondiente.

        Args:
            tab: "entradas" o "salidas".
        """
        self.tab_activa = tab
        if tab == "entradas":
            self.load_entradas()
        else:
            self.load_salidas()

    def on_load(self):
        """
        Inicializa la página: catálogos, fechas por defecto y ambas listas.

        Carga catálogos (productos, proveedores, tipos), establece fechas
        al mes actual y carga entradas y salidas del periodo.
        """
        self._load_catalogos()
        hoy = date.today()
        self.fecha_inicio = hoy.replace(day=1).isoformat()
        self.fecha_fin = hoy.isoformat()
        self.form_entrada_fecha = hoy.isoformat()
        self.form_salida_fecha = hoy.isoformat()
        self.load_entradas()
        self.load_salidas()

    def load_entradas(self):
        """
        Carga entradas del inventario filtradas por rango de fechas.

        Usa ReporteService.get_entradas_periodo() para obtener las entradas
        del periodo establecido en fecha_inicio / fecha_fin.
        """
        self.is_loading = True
        try:
            inicio = (
                date.fromisoformat(self.fecha_inicio) if self.fecha_inicio else None
            )
            fin = date.fromisoformat(self.fecha_fin) if self.fecha_fin else None
            if inicio and fin:
                from dev.services.reporte_service import ReporteService

                self.entradas = ReporteService.get_entradas_periodo(inicio, fin)
            else:
                self.entradas = []
        except Exception as e:
            logger.error("Error cargando entradas: %s", str(e))
            self.error_message = "Error al cargar entradas."
        finally:
            self.is_loading = False

    def load_salidas(self):
        """
        Carga salidas del inventario filtradas por rango de fechas.

        Usa ReporteService.get_salidas_periodo() para obtener las salidas
        del periodo establecido en fecha_inicio / fecha_fin.
        """
        self.is_loading = True
        try:
            inicio = (
                date.fromisoformat(self.fecha_inicio) if self.fecha_inicio else None
            )
            fin = date.fromisoformat(self.fecha_fin) if self.fecha_fin else None
            if inicio and fin:
                from dev.services.reporte_service import ReporteService

                self.salidas = ReporteService.get_salidas_periodo(inicio, fin)
            else:
                self.salidas = []
        except Exception as e:
            logger.error("Error cargando salidas: %s", str(e))
            self.error_message = "Error al cargar salidas."
        finally:
            self.is_loading = False

    def filtrar_periodo(self):
        """Recarga entradas y salidas aplicando los filtros de fecha actuales."""
        self.load_entradas()
        self.load_salidas()

    def abrir_crear_entrada(self):
        """
        Prepara y abre el diálogo para registrar una nueva entrada.

        Selecciona el primer tipo de entrada, limpia el formulario
        e inicializa la lista de lotes con un lote vacío.
        """
        self.form_entrada_tipo_id = (
            str(self.tipos_entrada[0]["id"]) if self.tipos_entrada else ""
        )
        self.form_entrada_proveedor_id = ""
        self.form_entrada_factura = ""
        self.form_entrada_observaciones = ""
        self.form_entrada_lotes = [
            {
                "producto_id": None,
                "cantidad": "",
                "fecha_vencimiento": "",
                "codigo_lote": "",
            }
        ]
        self.error_message = ""
        self.dialog_entrada_open = True

    def cerrar_dialog_entrada(self):
        """Cierra el diálogo de entrada sin guardar."""
        self.dialog_entrada_open = False
        self.error_message = ""

    def agregar_lote(self):
        """Agrega un lote vacío a la lista dinámica del formulario de entrada."""
        self.form_entrada_lotes.append(
            {
                "producto_id": None,
                "cantidad": "",
                "fecha_vencimiento": "",
                "codigo_lote": "",
            }
        )

    def eliminar_lote(self, index: int):
        """
        Elimina un lote de la lista dinámica.

        Args:
            index: Índice del lote a eliminar.

        No permite eliminar si solo queda un lote.
        """
        if len(self.form_entrada_lotes) > 1:
            self.form_entrada_lotes.pop(index)

    def set_lote_producto(self, index: int, producto_id: str):
        """
        Establece el producto de un lote.

        Args:
            index: Índice del lote.
            producto_id: ID del producto (string desde select).
        """
        if index < len(self.form_entrada_lotes):
            self.form_entrada_lotes[index]["producto_id"] = (
                int(producto_id) if producto_id else None
            )

    def set_lote_cantidad(self, index: int, cantidad: str):
        """
        Establece la cantidad de un lote.

        Args:
            index: Índice del lote.
            cantidad: Cantidad como string.
        """
        if index < len(self.form_entrada_lotes):
            self.form_entrada_lotes[index]["cantidad"] = cantidad

    def set_lote_vencimiento(self, index: int, fecha: str):
        """
        Establece la fecha de vencimiento de un lote.

        Args:
            index: Índice del lote.
            fecha: Fecha en formato ISO.
        """
        if index < len(self.form_entrada_lotes):
            self.form_entrada_lotes[index]["fecha_vencimiento"] = fecha

    def set_lote_codigo(self, index: int, codigo: str):
        """
        Establece el código de lote.

        Args:
            index: Índice del lote.
            codigo: Código identificatorio del lote.
        """
        if index < len(self.form_entrada_lotes):
            self.form_entrada_lotes[index]["codigo_lote"] = codigo

    def guardar_entrada(self):
        """
        Registra una entrada de inventario con lotes.

        Validaciones:
            - tipo_id: obligatorio.
            - fecha: obligatoria.
            - Cada lote: producto obligatorio, cantidad > 0.

        Flujo:
            1. Valida los campos obligatorios.
            2. Construye la lista de lotes con cantidad como Decimal.
            3. Incluye fecha_vencimiento y codigo_lote si están presentes.
            4. Llama a InventarioService.registrar_entrada() que:
               - Crea EntradaInventario + LoteInventario en transacción.
               - Actualiza stock_actual de cada producto.
            5. Cierra diálogo y recarga la tabla.

        Returns:
            rx.toast.success si se registró correctamente.
            Error en error_message si la validación o el service falla.
        """
        self.error_message = ""
        if not self.form_entrada_tipo_id:
            self.error_message = "Seleccione el tipo de entrada."
            return
        if not self.form_entrada_fecha:
            self.error_message = "Seleccione la fecha."
            return

        lotes_data = []
        for i, lote in enumerate(self.form_entrada_lotes):
            if not lote.get("producto_id"):
                self.error_message = f"Lote {i + 1}: seleccione un producto."
                return
            if not lote.get("cantidad") or Decimal(str(lote["cantidad"])) <= 0:
                self.error_message = f"Lote {i + 1}: la cantidad debe ser mayor a 0."
                return
            lote_dict: dict = {
                "producto_id": lote["producto_id"],
                "cantidad": Decimal(str(lote["cantidad"])),
            }
            if lote.get("fecha_vencimiento"):
                lote_dict["fecha_vencimiento"] = date.fromisoformat(
                    lote["fecha_vencimiento"]
                )
            if lote.get("codigo_lote"):
                lote_dict["codigo_lote"] = lote["codigo_lote"].strip()
            lotes_data.append(lote_dict)

        try:
            InventarioService.registrar_entrada(
                tipo_id=int(self.form_entrada_tipo_id)
                if self.form_entrada_tipo_id
                else None,
                fecha=date.fromisoformat(self.form_entrada_fecha),
                lotes_data=lotes_data,
                proveedor_id=int(self.form_entrada_proveedor_id)
                if self.form_entrada_proveedor_id
                else None,
                numero_factura=self.form_entrada_factura.strip() or None,
                observaciones=self.form_entrada_observaciones.strip() or None,
            )
            self.dialog_entrada_open = False
            self.load_entradas()
            return rx.toast.success("Entrada registrada correctamente.")
        except AppException as e:
            self.error_message = e.message
        except Exception as e:
            logger.error("Error guardando entrada: %s", str(e))
            self.error_message = "Error inesperado al registrar entrada."

    def abrir_crear_salida(self):
        """
        Prepara y abre el diálogo para registrar una nueva salida.

        Selecciona el primer tipo de salida, limpia el formulario,
        carga lotes disponibles e inicializa un detalle vacío.
        """
        self.form_salida_tipo_id = (
            str(self.tipos_salida[0]["id"]) if self.tipos_salida else ""
        )
        self.form_salida_observaciones = ""
        self.form_salida_detalles = [{"lote_id": None, "cantidad": "", "motivo": ""}]
        self.error_message = ""
        self._load_lotes_disponibles()
        self.dialog_salida_open = True

    def cerrar_dialog_salida(self):
        """Cierra el diálogo de salida sin guardar."""
        self.dialog_salida_open = False
        self.error_message = ""

    def agregar_detalle_salida(self):
        """Agrega un detalle vacío a la lista dinámica del formulario de salida."""
        self.form_salida_detalles.append(
            {"lote_id": None, "cantidad": "", "motivo": ""}
        )

    def eliminar_detalle_salida(self, index: int):
        """
        Elimina un detalle de la lista dinámica.

        Args:
            index: Índice del detalle a eliminar.

        No permite eliminar si solo queda un detalle.
        """
        if len(self.form_salida_detalles) > 1:
            self.form_salida_detalles.pop(index)

    def set_detalle_lote(self, index: int, lote_id: str):
        """
        Establece el lote de un detalle de salida.

        Args:
            index: Índice del detalle.
            lote_id: ID del lote (string desde select).
        """
        if index < len(self.form_salida_detalles):
            self.form_salida_detalles[index]["lote_id"] = (
                int(lote_id) if lote_id else None
            )

    def set_detalle_cantidad(self, index: int, cantidad: str):
        """
        Establece la cantidad de un detalle de salida.

        Args:
            index: Índice del detalle.
            cantidad: Cantidad como string.
        """
        if index < len(self.form_salida_detalles):
            self.form_salida_detalles[index]["cantidad"] = cantidad

    def set_detalle_motivo(self, index: int, motivo: str):
        """
        Establece el motivo de un detalle de salida.

        Args:
            index: Índice del detalle.
            motivo: Motivo de la salida.
        """
        if index < len(self.form_salida_detalles):
            self.form_salida_detalles[index]["motivo"] = motivo

    def guardar_salida(self):
        """
        Registra una salida de inventario con detalles por lote.

        Validaciones:
            - tipo_id: obligatorio.
            - fecha: obligatoria.
            - Cada detalle: lote obligatorio, cantidad > 0.

        Flujo:
            1. Valida los campos obligatorios.
            2. Construye la lista de detalles con cantidad como Decimal.
            3. Incluye motivo si está presente.
            4. Llama a InventarioService.registrar_salida() que:
               - Crea SalidaInventario + DetalleSalidaInventario en transacción.
               - Descuenta stock_actual de cada producto.
            5. Cierra diálogo y recarga la tabla.

        Returns:
            rx.toast.success si se registró correctamente.
            Error en error_message si la validación o el service falla.
        """
        self.error_message = ""
        if not self.form_salida_tipo_id:
            self.error_message = "Seleccione el tipo de salida."
            return
        if not self.form_salida_fecha:
            self.error_message = "Seleccione la fecha."
            return

        detalles_data = []
        for i, det in enumerate(self.form_salida_detalles):
            if not det.get("lote_id"):
                self.error_message = f"Detalle {i + 1}: seleccione un lote."
                return
            if not det.get("cantidad") or Decimal(str(det["cantidad"])) <= 0:
                self.error_message = f"Detalle {i + 1}: la cantidad debe ser mayor a 0."
                return
            d: dict = {
                "lote_id": det["lote_id"],
                "cantidad": Decimal(str(det["cantidad"])),
            }
            if det.get("motivo"):
                d["motivo"] = det["motivo"].strip()
            detalles_data.append(d)

        try:
            InventarioService.registrar_salida(
                tipo_id=int(self.form_salida_tipo_id)
                if self.form_salida_tipo_id
                else None,
                fecha=date.fromisoformat(self.form_salida_fecha),
                detalles_data=detalles_data,
                observaciones=self.form_salida_observaciones.strip() or None,
            )
            self.dialog_salida_open = False
            self.load_salidas()
            return rx.toast.success("Salida registrada correctamente.")
        except AppException as e:
            self.error_message = e.message
        except Exception as e:
            logger.error("Error guardando salida: %s", str(e))
            self.error_message = "Error inesperado al registrar salida."

    def ver_detalle_entrada(self, entrada_id: int):
        """
        Muestra el detalle de una entrada con sus lotes.

        Args:
            entrada_id: PK de la entrada.

        Obtiene la entrada con lotes via InventarioService.get_entrada_with_lotes()
        y los muestra en un diálogo de solo lectura.
        """
        try:
            result = InventarioService.get_entrada_with_lotes(entrada_id)
            entrada = result["entrada"]
            lotes = result["lotes"]
            self.detalle_entrada_lotes = [
                {
                    "id": l.id,
                    "producto_id": l.producto_id,
                    "cantidad": str(l.cantidad),
                    "codigo_lote": l.codigo_lote or "",
                    "fecha_vencimiento": str(l.fecha_vencimiento)
                    if l.fecha_vencimiento
                    else "N/A",
                }
                for l in lotes
            ]
            self.detalle_entrada = {
                "id": entrada.id,
                "fecha": str(entrada.fecha),
                "factura": entrada.numero_factura or "N/A",
                "observaciones": entrada.observaciones or "",
            }
            self.detalle_entrada_open = True
        except Exception as e:
            logger.error("Error cargando detalle: %s", str(e))
            return rx.toast.error("Error al cargar detalle.")

    def cerrar_detalle_entrada(self):
        """Cierra el diálogo de detalle de entrada."""
        self.detalle_entrada_open = False

    def ver_detalle_salida(self, salida_id: int):
        """
        Muestra el detalle de una salida con sus detalles por lote.

        Args:
            salida_id: PK de la salida.

        Obtiene la salida con detalles via InventarioService.get_salida_with_detalles()
        y los muestra en un diálogo de solo lectura.
        """
        try:
            result = InventarioService.get_salida_with_detalles(salida_id)
            salida = result["salida"]
            detalles = result["detalles"]
            self.detalle_salida_detalles = [
                {
                    "id": d.id,
                    "lote_id": d.lote_id,
                    "cantidad": str(d.cantidad),
                    "motivo": d.motivo or "",
                }
                for d in detalles
            ]
            self.detalle_salida = {
                "id": salida.id,
                "fecha": str(salida.fecha),
                "observaciones": salida.observaciones or "",
            }
            self.detalle_salida_open = True
        except Exception as e:
            logger.error("Error cargando detalle: %s", str(e))
            return rx.toast.error("Error al cargar detalle.")

    def cerrar_detalle_salida(self):
        """Cierra el diálogo de detalle de salida."""
        self.detalle_salida_open = False

    def _load_catalogos(self):
        """
        Carga todos los catálogos necesarios para los selectores.

        Obtiene de la BD:
            - productos: Productos activos.
            - proveedores: Proveedores activos.
            - tipos_entrada: Tipos de la lista "entrada".
            - tipos_salida: Tipos de la lista "salida".
        """
        from dev.models.models import (
            CategoriaProducto,
            ListTipo,
            Producto,
            Proveedor,
            Tipo,
            UnidadMedida,
        )
        from sqlmodel import select

        with rx.session() as session:
            self.productos = [
                {"id": p.id, "nombre": p.nombre}
                for p in session.exec(
                    select(Producto).where(Producto.activo == True)  # noqa: E712
                ).all()
            ]

            self.proveedores = [
                {"id": p.id, "nombre": p.nombre}
                for p in session.exec(
                    select(Proveedor).where(Proveedor.activo == True)  # noqa: E712
                ).all()
            ]

            stmt_entrada = (
                select(Tipo)
                .join(ListTipo)
                .where(ListTipo.nombre == "entrada", Tipo.activo == True)  # noqa: E712
            )
            self.tipos_entrada = [
                {"id": t.id, "nombre": t.nombre}
                for t in session.exec(stmt_entrada).all()
            ]

            stmt_salida = (
                select(Tipo)
                .join(ListTipo)
                .where(ListTipo.nombre == "salida", Tipo.activo == True)  # noqa: E712
            )
            self.tipos_salida = [
                {"id": t.id, "nombre": t.nombre}
                for t in session.exec(stmt_salida).all()
            ]

    def _load_lotes_disponibles(self):
        """
        Carga los lotes de inventario activos para el selector de salidas.

        Obtiene lotes con código, cantidad restante y fecha de vencimiento.
        Usa "Lote #id" como fallback si no tiene código de lote.
        """
        from dev.models.models import LoteInventario
        from sqlmodel import select

        with rx.session() as session:
            lotes = session.exec(
                select(LoteInventario).where(LoteInventario.activo == True)  # noqa: E712
            ).all()
            self.lotes_disponibles = [
                {
                    "id": l.id,
                    "producto_id": l.producto_id,
                    "codigo": l.codigo_lote or f"Lote #{l.id}",
                    "cantidad": str(l.cantidad),
                    "vencimiento": str(l.fecha_vencimiento)
                    if l.fecha_vencimiento
                    else "N/A",
                }
                for l in lotes
            ]
