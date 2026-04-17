"""
receta_state.py — Estado reactivo para gestión de recetas.

Arquitectura
------------
Capa State (Application Layer) para recetas. CRUD completo con gestión
de ingredientes dinámicos (agregar, quitar, modificar cantidades).
Incluye verificación de disponibilidad de insumos y visualización
de detalles.

Patrón de diseño: Reflex State
    - Variables reactivas sincronizadas al frontend.
    - Formularios con vars separadas (form_*) para no mutar la tabla.
    - Ingredientes dinámicos como list[dict] en form_ingredientes.
    - Diálogos controlados por vars booleanas (dialog_open, confirm_open,
      detalle_open, disponibilidad_open).
    - Delega toda la lógica a RecetaService.

Relación con otras capas
------------------------
    [Recetas Page] → RecetaState
                       → RecetaService.create()                         → [BD]
                       → RecetaService.update() + update_ingredientes() → [BD]
                       → RecetaService.deactivate()                     → [BD]
                       → RecetaService.search() / get_all()             → [BD]
                       → RecetaService.verificar_insumos_disponibles()  → [BD]

Variables de estado
-------------------
    Datos de tabla:
        - recetas: list[dict] — Recetas con ingredientes embebidos.
        - search_query: str — Texto de búsqueda.

    Formulario crear/editar:
        - form_nombre, form_descripcion, form_producto_id.
        - form_ingredientes: list[dict] — Lista dinámica de ingredientes.
        - dialog_open: bool — Controla visibilidad del diálogo.
        - modo_editar: bool — True=editar, False=crear.
        - editando_id: Optional[int] — PK de la receta en edición.

    Confirmación desactivar:
        - confirm_open: bool — Controla visibilidad.
        - confirm_receta_id, confirm_receta_nombre: Datos de la receta.

    Detalle:
        - detalle_open: bool — Controla visibilidad.
        - detalle_receta: dict — Datos completos con ingredientes.

    Verificación disponibilidad:
        - disponibilidad_open: bool — Controla visibilidad.
        - disponibilidad_resultado: dict — Detalle de insumos.
        - disponibilidad_cantidad: str — Cantidad a verificar.

    Catálogos:
        - productos: list[dict] — Productos activos para selectores.

Flujo de datos
--------------
1. La página se monta → on_load() carga productos y recetas.
2. El usuario puede buscar → buscar() / limpiar_busqueda().
3. Para crear: abrir_crear() → agregar ingredientes → guardar_receta().
4. Para editar: abrir_editar(id) → precarga datos e ingredientes → guardar_receta().
5. Para desactivar: confirmar_desactivar(id) → ejecutar_desactivar().
6. Para ver detalle: ver_detalle(id) → muestra ingredientes.
7. Para verificar disponibilidad: abrir_verificar_disponibilidad(id) → verificar_disponibilidad().

Uso desde la capa UI:
    from dev.states.receta_state import RecetaState

    rx.foreach(RecetaState.recetas, lambda r: rx.text(r["nombre"]))
    rx.button("Crear", on_click=RecetaState.abrir_crear)
"""

import logging
from decimal import Decimal
from typing import Optional

import reflex as rx

from dev.core.exceptions import AppException
from dev.services.receta_service import RecetaService

logger = logging.getLogger("dev.states.receta")


class RecetaState(rx.State):
    """
    Estado reactivo para la gestión de recetas con ingredientes.

    CRUD completo de recetas con gestión dinámica de ingredientes,
    verificación de disponibilidad de insumos y desactivación con
    confirmación.

    Métodos principales:
        - on_load: Carga catálogo de productos y recetas al montar la página.
        - load_recetas: Carga recetas con búsqueda opcional.
        - buscar / limpiar_busqueda: Control de búsqueda.
        - abrir_crear / abrir_editar: Abren el diálogo de formulario.
        - agregar_ingrediente / eliminar_ingrediente: Gestionan lista dinámica.
        - guardar_receta: Crea o actualiza receta con ingredientes.
        - confirmar_desactivar / ejecutar_desactivar: Soft delete con confirmación.
        - ver_detalle: Muestra ingredientes de una receta.
        - abrir_verificar_disponibilidad / verificar_disponibilidad: Verifican insumos.

    Variables reactivas:
        - recetas: Lista de recetas con ingredientes embebidos.
        - form_ingredientes: Lista dinámica de ingredientes del formulario.
        - disponibilidad_*: Resultado de la verificación de insumos.
    """

    recetas: list[dict] = []
    search_query: str = ""

    is_loading: bool = False
    error_message: str = ""

    dialog_open: bool = False
    modo_editar: bool = False
    editando_id: Optional[int] = None

    form_nombre: str = ""
    form_descripcion: str = ""
    form_producto_id: Optional[int] = None
    form_ingredientes: list[dict] = []

    confirm_open: bool = False
    confirm_receta_id: Optional[int] = None
    confirm_receta_nombre: str = ""

    detalle_open: bool = False
    detalle_receta: dict = {}

    disponibilidad_open: bool = False
    disponibilidad_resultado: dict = {}
    disponibilidad_cantidad: str = "1"

    productos: list[dict] = []

    def on_load(self):
        """Carga el catálogo de productos y la lista de recetas al montar la página."""
        self._load_productos()
        self.load_recetas()

    def load_recetas(self):
        """
        Carga recetas con búsqueda opcional por nombre.

        Si search_query tiene al menos 2 caracteres, usa RecetaService.search().
        Si no, carga todas con RecetaService.get_all().

        Para cada receta, obtiene sus ingredientes y los embebe en el dict.
        """
        self.is_loading = True
        self.error_message = ""
        try:
            if self.search_query.strip() and len(self.search_query.strip()) >= 2:
                recetas = RecetaService.search(self.search_query.strip())
            else:
                recetas = RecetaService.get_all()

            self.recetas = []
            for r in recetas:
                ingredientes = RecetaService.get_ingredientes(r.id)
                self.recetas.append(
                    {
                        "id": r.id,
                        "nombre": r.nombre,
                        "descripcion": r.descripcion or "",
                        "producto_id": r.producto_id,
                        "activo": r.activo,
                        "total_ingredientes": len(ingredientes),
                        "ingredientes": [
                            {
                                "id": d.id,
                                "producto_id": d.producto_id,
                                "cantidad": str(d.cantidad),
                            }
                            for d in ingredientes
                        ],
                    }
                )
            logger.info("Recetas cargadas: %s", len(self.recetas))
        except Exception as e:
            logger.error("Error cargando recetas: %s", str(e))
            self.error_message = "Error al cargar recetas."
        finally:
            self.is_loading = False

    def buscar(self):
        """Recarga las recetas aplicando el texto de búsqueda actual."""
        self.load_recetas()

    def limpiar_busqueda(self):
        """Limpia el texto de búsqueda y recarga todas las recetas."""
        self.search_query = ""
        self.load_recetas()

    def abrir_crear(self):
        """
        Prepara y abre el diálogo para crear una nueva receta.

        Limpia el formulario e inicializa la lista de ingredientes
        con un ingrediente vacío.
        """
        self.modo_editar = False
        self.editando_id = None
        self.form_nombre = ""
        self.form_descripcion = ""
        self.form_producto_id = None
        self.form_ingredientes = [{"producto_id": None, "cantidad": ""}]
        self.error_message = ""
        self.dialog_open = True

    def abrir_editar(self, receta_id: int):
        """
        Carga los datos de una receta y abre el diálogo de edición.

        Args:
            receta_id: PK de la receta a editar.

        Obtiene la receta con sus ingredientes via RecetaService.get_with_detalles()
        y precarga el formulario con los datos actuales.
        """
        try:
            result = RecetaService.get_with_detalles(receta_id)
            receta = result["receta"]
            detalles = result["detalles"]
            self.modo_editar = True
            self.editando_id = receta_id
            self.form_nombre = receta.nombre
            self.form_descripcion = receta.descripcion or ""
            self.form_producto_id = receta.producto_id
            self.form_ingredientes = [
                {"producto_id": d.producto_id, "cantidad": str(d.cantidad)}
                for d in detalles
            ]
            self.error_message = ""
            self.dialog_open = True
        except Exception as e:
            logger.error("Error cargando receta: %s", str(e))
            return rx.toast.error("Error al cargar receta.")

    def cerrar_dialog(self):
        """Cierra el diálogo de crear/editar sin guardar."""
        self.dialog_open = False
        self.error_message = ""

    def agregar_ingrediente(self):
        """Agrega un ingrediente vacío a la lista dinámica del formulario."""
        self.form_ingredientes.append({"producto_id": None, "cantidad": ""})

    def eliminar_ingrediente(self, index: int):
        """
        Elimina un ingrediente de la lista dinámica.

        Args:
            index: Índice del ingrediente a eliminar.

        No permite eliminar si solo queda un ingrediente.
        """
        if len(self.form_ingredientes) > 1:
            self.form_ingredientes.pop(index)

    def set_ingrediente_producto(self, index: int, producto_id: str):
        """
        Establece el producto de un ingrediente en la lista.

        Args:
            index: Índice del ingrediente.
            producto_id: ID del producto seleccionado (string desde select).
        """
        if index < len(self.form_ingredientes):
            self.form_ingredientes[index]["producto_id"] = (
                int(producto_id) if producto_id else None
            )

    def set_ingrediente_cantidad(self, index: int, cantidad: str):
        """
        Establece la cantidad de un ingrediente en la lista.

        Args:
            index: Índice del ingrediente.
            cantidad: Cantidad ingresada como string.
        """
        if index < len(self.form_ingredientes):
            self.form_ingredientes[index]["cantidad"] = cantidad

    def guardar_receta(self):
        """
        Crea o actualiza una receta con sus ingredientes.

        Validaciones:
            - nombre: obligatorio.
            - producto_id: obligatorio (producto final).
            - Cada ingrediente: producto_id obligatorio, cantidad > 0.

        Flujo:
            Si modo_editar=True:
                1. RecetaService.update() para datos generales.
                2. RecetaService.update_ingredientes() reemplaza ingredientes.
            Si modo_editar=False:
                RecetaService.create() con ingredientes.

        Returns:
            rx.toast.success con mensaje de confirmación.
            Error en error_message si la validación o el service falla.
        """
        self.error_message = ""
        if not self.form_nombre.strip():
            self.error_message = "El nombre es obligatorio."
            return
        if not self.form_producto_id:
            self.error_message = "Seleccione el producto final."
            return

        ingredientes_data = []
        for i, ing in enumerate(self.form_ingredientes):
            if not ing.get("producto_id"):
                self.error_message = f"Ingrediente {i + 1}: seleccione un producto."
                return
            if not ing.get("cantidad") or Decimal(str(ing["cantidad"])) <= 0:
                self.error_message = (
                    f"Ingrediente {i + 1}: la cantidad debe ser mayor a 0."
                )
                return
            ingredientes_data.append(
                {
                    "producto_id": ing["producto_id"],
                    "cantidad": Decimal(str(ing["cantidad"])),
                }
            )

        try:
            if self.modo_editar and self.editando_id:
                RecetaService.update(
                    self.editando_id,
                    nombre=self.form_nombre.strip(),
                    descripcion=self.form_descripcion.strip() or None,
                    producto_id=self.form_producto_id,
                )
                RecetaService.update_ingredientes(self.editando_id, ingredientes_data)
                msg = "Receta actualizada correctamente."
            else:
                RecetaService.create(
                    nombre=self.form_nombre.strip(),
                    descripcion=self.form_descripcion.strip() or None,
                    producto_id=self.form_producto_id,
                    ingredientes=ingredientes_data,
                )
                msg = "Receta creada correctamente."

            self.dialog_open = False
            self.load_recetas()
            return rx.toast.success(msg)
        except AppException as e:
            self.error_message = e.message
        except Exception as e:
            logger.error("Error guardando receta: %s", str(e))
            self.error_message = "Error inesperado al guardar."

    def confirmar_desactivar(self, receta_id: int):
        """
        Abre el diálogo de confirmación para desactivar una receta.

        Args:
            receta_id: PK de la receta a desactivar.
        """
        try:
            receta = RecetaService.get_by_id(receta_id)
            self.confirm_receta_id = receta_id
            self.confirm_receta_nombre = receta.nombre
            self.confirm_open = True
        except Exception as e:
            logger.error("Error: %s", str(e))
            return rx.toast.error("Error al cargar receta.")

    def ejecutar_desactivar(self):
        """
        Ejecuta la desactivación de la receta confirmada.

        Llama a RecetaService.deactivate() con el ID almacenado
        en confirm_receta_id. Cierra el diálogo y recarga la lista.

        Returns:
            rx.toast.success si se desactivó correctamente.
        """
        if not self.confirm_receta_id:
            return
        try:
            RecetaService.deactivate(self.confirm_receta_id)
            self.confirm_open = False
            self.confirm_receta_id = None
            self.confirm_receta_nombre = ""
            self.load_recetas()
            return rx.toast.success("Receta desactivada.")
        except Exception as e:
            logger.error("Error desactivando: %s", str(e))
            self.confirm_open = False
            return rx.toast.error("Error al desactivar receta.")

    def cerrar_confirm(self):
        """Cierra el diálogo de confirmación sin ejecutar."""
        self.confirm_open = False
        self.confirm_receta_id = None

    def ver_detalle(self, receta_id: int):
        """
        Muestra el detalle de una receta con sus ingredientes.

        Args:
            receta_id: PK de la receta.

        Obtiene la receta con ingredientes via RecetaService.get_with_detalles()
        y los muestra en un diálogo de solo lectura.
        """
        try:
            result = RecetaService.get_with_detalles(receta_id)
            receta = result["receta"]
            detalles = result["detalles"]
            self.detalle_receta = {
                "id": receta.id,
                "nombre": receta.nombre,
                "descripcion": receta.descripcion or "",
                "ingredientes": [
                    {
                        "id": d.id,
                        "producto_id": d.producto_id,
                        "cantidad": str(d.cantidad),
                    }
                    for d in detalles
                ],
            }
            self.detalle_open = True
        except Exception as e:
            logger.error("Error: %s", str(e))
            return rx.toast.error("Error al cargar detalle.")

    def cerrar_detalle(self):
        """Cierra el diálogo de detalle de receta."""
        self.detalle_open = False

    def abrir_verificar_disponibilidad(self, receta_id: int):
        """
        Abre el diálogo de verificación de disponibilidad de insumos.

        Args:
            receta_id: PK de la receta a verificar.

        Precarga el nombre de la receta y establece cantidad por defecto "1".
        """
        try:
            receta = RecetaService.get_by_id(receta_id)
            self.editando_id = receta_id
            self.form_nombre = receta.nombre
            self.disponibilidad_cantidad = "1"
            self.disponibilidad_resultado = {}
            self.disponibilidad_open = True
        except Exception as e:
            logger.error("Error: %s", str(e))
            return rx.toast.error("Error al cargar receta.")

    def verificar_disponibilidad(self):
        """
        Ejecuta la verificación de insumos disponibles para la receta.

        Llama a RecetaService.verificar_insumos_disponibles() con la receta
        almacenada en editando_id y la cantidad ingresada.

        Actualiza disponibilidad_resultado con el detalle de cada insumo:
        nombre, cantidad necesaria, stock actual, si es suficiente y faltante.

        Returns:
            rx.toast.error si la cantidad es <= 0 o si falla la verificación.
        """
        if not self.editando_id:
            return
        try:
            cantidad = Decimal(self.disponibilidad_cantidad or "0")
            if cantidad <= 0:
                return rx.toast.error("La cantidad debe ser mayor a 0.")

            result = RecetaService.verificar_insumos_disponibles(
                self.editando_id, cantidad
            )
            self.disponibilidad_resultado = {
                "disponible": result["disponible"],
                "detalle": [
                    {
                        "producto_id": d["producto_id"],
                        "nombre": d["nombre"],
                        "cantidad_necesaria": str(d["cantidad_necesaria"]),
                        "stock_actual": str(d["stock_actual"]),
                        "suficiente": d["suficiente"],
                        "faltante": str(d["faltante"]),
                    }
                    for d in result["detalle"]
                ],
            }
        except Exception as e:
            logger.error("Error verificando: %s", str(e))
            return rx.toast.error("Error al verificar disponibilidad.")

    def cerrar_disponibilidad(self):
        """Cierra el diálogo de verificación de disponibilidad."""
        self.disponibilidad_open = False
        self.editando_id = None

    def _load_productos(self):
        """Carga los productos activos para los selectores de ingredientes."""
        from dev.models.models import Producto
        from sqlmodel import select

        with rx.session() as session:
            prods = session.exec(
                select(Producto).where(Producto.activo == True)  # noqa: E712
            ).all()
            self.productos = [{"id": p.id, "nombre": p.nombre} for p in prods]
