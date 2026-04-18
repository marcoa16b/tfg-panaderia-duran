"""
producto_state.py — Estado reactivo para gestión de productos.

Arquitectura
------------
Capa State (Application Layer) para el catálogo de productos. Maneja
el CRUD completo: listado paginado con filtros, búsqueda por nombre,
filtrado por categoría, creación, edición y desactivación.

Patrón de diseño: Reflex State
    - Variables reactivas sincronizadas al frontend.
    - Formularios con vars separadas (form_*) para no mutar la tabla.
    - Diálogos controlados por vars booleanas (dialog_open, confirm_open).
    - Paginación offset/limit calculada en el state.

Relación con otras capas
------------------------
    [Productos Page] → ProductoState
                        → ProductoService.get_paginated() → ProductoRepository → [BD]
                        → ProductoService.create()         → ProductoRepository → [BD]
                        → ProductoService.update()         → ProductoRepository → [BD]
                        → ProductoService.deactivate()     → ProductoRepository → [BD]

Variables de estado
-------------------
    Datos de tabla:
        - productos: list[dict] — Productos de la página actual.
        - total_productos: int — Total de registros con filtros.
        - pagina_actual, total_paginas: int — Control de paginación.

    Filtros:
        - search_query: str — Texto de búsqueda por nombre.
        - filtro_categoria_id: Optional[int] — Filtro por categoría.

    Formulario crear/editar:
        - form_nombre, form_descripcion, form_categoria_id, etc.
        - dialog_open: bool — Controla visibilidad del diálogo.
        - modo_editar: bool — True=editar, False=crear.
        - editando_id: Optional[int] — PK del producto en edición.

    Confirmación desactivar:
        - confirm_open: bool — Controla visibilidad del diálogo de confirmación.
        - confirm_producto_id, confirm_producto_nombre: Datos del producto a desactivar.

    Catálogos (cargados una vez):
        - categorias: list[dict] — Categorías de producto activas.
        - unidades_medida: list[dict] — Unidades de medida activas.

Flujo de datos
--------------
1. La página se monta y llama a load_productos().
2. Se cargan catálogos (categorías, unidades) y productos paginados.
3. El usuario puede buscar, filtrar o paginar → recarga la tabla.
4. Para crear: abrir_crear() → llenar formulario → guardar_producto().
5. Para editar: abrir_editar(id) → precarga datos → guardar_producto().
6. Para desactivar: confirmar_desactivar(id) → ejecutar_desactivar().

Uso desde la capa UI:
    from dev.states.producto_state import ProductoState

    rx.foreach(ProductoState.productos, lambda p: rx.text(p["nombre"]))
    rx.button("Crear", on_click=ProductoState.abrir_crear)
"""

import logging
from decimal import Decimal
from typing import Optional

import reflex as rx

from dev.core.exceptions import AppException
from dev.services.producto_service import ProductoService

logger = logging.getLogger("dev.states.producto")

PAGE_SIZE = 20


class ProductoState(rx.State):
    """
    Estado reactivo para la gestión del catálogo de productos.

    Métodos principales:
        - load_productos: Carga productos paginados con filtros.
        - buscar_productos: Busca por nombre (mínimo 2 caracteres).
        - filtrar_por_categoria: Filtra por categoría.
        - abrir_crear / abrir_editar: Abren el diálogo de formulario.
        - guardar_producto: Crea o actualiza un producto.
        - confirmar_desactivar / ejecutar_desactivar: Soft delete con confirmación.

    Paginación:
        - PAGE_SIZE = 20 registros por página.
        - pagina_siguiente / pagina_anterior para navegar.

    Convención de formularios:
        - Las vars form_* almacenan los datos del formulario.
        - modo_editar distingue entre crear (False) y editar (True).
        - Al guardar, se validan los campos antes de llamar al service.
    """

    productos: list[dict] = []
    total_productos: int = 0
    pagina_actual: int = 1
    total_paginas: int = 1

    search_query: str = ""
    filtro_categoria_id: Optional[int] = None

    is_loading: bool = False
    error_message: str = ""
    success_message: str = ""

    dialog_open: bool = False
    modo_editar: bool = False
    editando_id: Optional[int] = None

    form_nombre: str = ""
    form_descripcion: str = ""
    form_categoria_id: str = ""
    form_unidad_medida_id: str = ""
    form_stock_minimo: str = "0"
    form_ubicacion: str = ""

    confirm_open: bool = False
    confirm_producto_id: Optional[int] = None
    confirm_producto_nombre: str = ""

    categorias: list[dict] = []
    unidades_medida: list[dict] = []

    def load_productos(self):
        """
        Carga productos paginados aplicando filtros activos.

        Flujo:
            1. Carga catálogos de categorías y unidades de medida.
            2. Calcula offset = (pagina_actual - 1) * PAGE_SIZE.
            3. Llama a ProductoService.get_paginated() con filtros.
            4. Serializa cada producto como dict para el frontend.
            5. Calcula total_paginas = ceil(total / PAGE_SIZE).

        Filtros aplicados:
            - search_query: Búsqueda parcial por nombre.
            - filtro_categoria_id: Filtra por categoría.
        """
        self.is_loading = True
        self.error_message = ""
        try:
            self._load_categorias()
            self._load_unidades_medida()

            offset = (self.pagina_actual - 1) * PAGE_SIZE
            productos, total = ProductoService.get_paginated(
                offset=offset,
                limit=PAGE_SIZE,
                query=self.search_query if self.search_query.strip() else None,
                categoria_id=self.filtro_categoria_id,
            )
            self.productos = [self._producto_to_dict(p) for p in productos]
            self.total_productos = total
            self.total_paginas = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
            logger.info("Productos cargados: %s de %s", len(self.productos), total)
        except Exception as e:
            logger.error("Error cargando productos: %s", str(e))
            self.error_message = "Error al cargar productos."
        finally:
            self.is_loading = False

    def buscar_productos(self):
        """Resetea a página 1 y recarga con el texto de búsqueda actual."""
        self.pagina_actual = 1
        self.load_productos()

    def filtrar_por_categoria(self, categoria_id: str):
        """
        Filtra productos por categoría.

        Args:
            categoria_id: ID de la categoría. "0" o vacío limpia el filtro.
        """
        self.filtro_categoria_id = (
            int(categoria_id) if categoria_id and categoria_id != "0" else None
        )
        self.pagina_actual = 1
        self.load_productos()

    def limpiar_filtros(self):
        """Limpia todos los filtros y recarga la primera página."""
        self.search_query = ""
        self.filtro_categoria_id = None
        self.pagina_actual = 1
        self.load_productos()

    def pagina_siguiente(self):
        """Avanza a la siguiente página si existe."""
        if self.pagina_actual < self.total_paginas:
            self.pagina_actual += 1
            self.load_productos()

    def pagina_anterior(self):
        """Retrocede a la página anterior si no es la primera."""
        if self.pagina_actual > 1:
            self.pagina_actual -= 1
            self.load_productos()

    def abrir_crear(self):
        """
        Prepara y abre el diálogo para crear un nuevo producto.

        Limpia todas las vars del formulario y establece modo_editar=False.
        """
        self.modo_editar = False
        self.editando_id = None
        self.form_nombre = ""
        self.form_descripcion = ""
        self.form_categoria_id = ""
        self.form_unidad_medida_id = ""
        self.form_stock_minimo = "0"
        self.form_ubicacion = ""
        self.error_message = ""
        self.dialog_open = True

    def abrir_editar(self, producto_id: int):
        """
        Carga los datos de un producto y abre el diálogo de edición.

        Args:
            producto_id: PK del producto a editar.

        Flujo:
            1. Obtiene el producto via ProductoService.get_by_id().
            2. Precarga las vars del formulario con los datos actuales.
            3. Establece modo_editar=True y editando_id.
        """
        try:
            producto = ProductoService.get_by_id(producto_id)
            self.modo_editar = True
            self.editando_id = producto_id
            self.form_nombre = producto.nombre
            self.form_descripcion = producto.descripcion or ""
            self.form_categoria_id = (
                str(producto.categoria_id) if producto.categoria_id else ""
            )
            self.form_unidad_medida_id = (
                str(producto.unidad_medida_id) if producto.unidad_medida_id else ""
            )
            self.form_stock_minimo = str(producto.stock_minimo)
            self.form_ubicacion = producto.ubicacion or ""
            self.error_message = ""
            self.dialog_open = True
        except Exception as e:
            logger.error("Error cargando producto: %s", str(e))
            return rx.toast.error("Error al cargar producto.")

    def cerrar_dialog(self):
        """Cierra el diálogo de crear/editar sin guardar."""
        self.dialog_open = False
        self.error_message = ""

    def guardar_producto(self):
        """
        Crea o actualiza un producto según el modo actual.

        Validaciones:
            - nombre: obligatorio.
            - categoria_id: obligatorio.
            - unidad_medida_id: obligatorio.
            - stock_minimo: se convierte a Decimal (default "0").

        Flujo:
            Si modo_editar=True: llama a ProductoService.update().
            Si modo_editar=False: llama a ProductoService.create().

        Returns:
            rx.toast.success con mensaje de confirmación.
            Error en error_message si la validación o el service falla.
        """
        self.error_message = ""
        if not self.form_nombre.strip():
            self.error_message = "El nombre es obligatorio."
            return
        if not self.form_categoria_id:
            self.error_message = "La categoría es obligatoria."
            return
        if not self.form_unidad_medida_id:
            self.error_message = "La unidad de medida es obligatoria."
            return

        try:
            stock_minimo = Decimal(self.form_stock_minimo or "0")
            categoria_id = (
                int(self.form_categoria_id) if self.form_categoria_id else None
            )
            unidad_medida_id = (
                int(self.form_unidad_medida_id) if self.form_unidad_medida_id else None
            )
            if self.modo_editar and self.editando_id:
                ProductoService.update(
                    self.editando_id,
                    nombre=self.form_nombre.strip(),
                    descripcion=self.form_descripcion.strip() or None,
                    categoria_id=categoria_id,
                    unidad_medida_id=unidad_medida_id,
                    stock_minimo=stock_minimo,
                    ubicacion=self.form_ubicacion.strip() or None,
                )
                msg = "Producto actualizado correctamente."
            else:
                ProductoService.create(
                    nombre=self.form_nombre.strip(),
                    descripcion=self.form_descripcion.strip() or None,
                    categoria_id=categoria_id,
                    unidad_medida_id=unidad_medida_id,
                    stock_minimo=stock_minimo,
                    ubicacion=self.form_ubicacion.strip() or None,
                )
                msg = "Producto creado correctamente."

            self.dialog_open = False
            self.load_productos()
            return rx.toast.success(msg)
        except AppException as e:
            self.error_message = e.message
        except Exception as e:
            logger.error("Error guardando producto: %s", str(e))
            self.error_message = "Error inesperado al guardar."

    def confirmar_desactivar(self, producto_id: int):
        """
        Abre el diálogo de confirmación para desactivar un producto.

        Args:
            producto_id: PK del producto a desactivar.
        """
        try:
            producto = ProductoService.get_by_id(producto_id)
            self.confirm_producto_id = producto_id
            self.confirm_producto_nombre = producto.nombre
            self.confirm_open = True
        except Exception as e:
            logger.error("Error: %s", str(e))
            return rx.toast.error("Error al cargar producto.")

    def ejecutar_desactivar(self):
        """
        Ejecuta la desactivación del producto confirmado.

        Llama a ProductoService.deactivate() con el ID almacenado
        en confirm_producto_id. Cierra el diálogo y recarga la tabla.

        Returns:
            rx.toast.success si se desactivó correctamente.
        """
        if not self.confirm_producto_id:
            return
        try:
            ProductoService.deactivate(self.confirm_producto_id)
            self.confirm_open = False
            self.confirm_producto_id = None
            self.confirm_producto_nombre = ""
            self.load_productos()
            return rx.toast.success("Producto desactivado.")
        except Exception as e:
            logger.error("Error desactivando: %s", str(e))
            self.confirm_open = False
            return rx.toast.error("Error al desactivar producto.")

    def cerrar_confirm(self):
        """Cierra el diálogo de confirmación sin ejecutar."""
        self.confirm_open = False
        self.confirm_producto_id = None

    def _load_categorias(self):
        """Carga las categorías de producto activas para el selector del formulario."""
        from dev.models.models import CategoriaProducto

        with rx.session() as session:
            from sqlmodel import select

            cats = session.exec(
                select(CategoriaProducto).where(CategoriaProducto.activo == True)  # noqa: E712
            ).all()
            self.categorias = [{"id": c.id, "nombre": c.nombre} for c in cats]

    def _load_unidades_medida(self):
        """Carga las unidades de medida activas para el selector del formulario."""
        from dev.models.models import UnidadMedida

        with rx.session() as session:
            from sqlmodel import select

            ums = session.exec(
                select(UnidadMedida).where(UnidadMedida.activo == True)  # noqa: E712
            ).all()
            self.unidades_medida = [
                {"id": u.id, "nombre": u.nombre, "abreviatura": u.abreviatura}
                for u in ums
            ]

    @staticmethod
    def _producto_to_dict(p) -> dict:
        """
        Serializa un modelo Producto a dict para el frontend.

        Los campos Decimal se convierten a str para ser JSON-serializables.

        Args:
            p: Instancia de Producto (modelo SQLModel).

        Returns:
            Dict con todos los campos necesarios para la tabla y formularios.
        """
        return {
            "id": p.id,
            "nombre": p.nombre,
            "descripcion": p.descripcion or "",
            "categoria_id": p.categoria_id,
            "unidad_medida_id": p.unidad_medida_id,
            "stock_actual": str(p.stock_actual),
            "stock_minimo": str(p.stock_minimo),
            "bajo_stock": p.stock_actual <= p.stock_minimo,
            "ubicacion": p.ubicacion or "",
            "activo": p.activo,
        }
