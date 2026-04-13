import reflex as rx

from dev.components.layout import base_layout
from dev.components.stat_card import stat_card, stat_card_simple
from dev.components.alerta_card import alerta_card, alerta_stock_bajo, alerta_caducidad
from dev.components.modal_confirmacion import modal_confirmacion, modal_desactivar
from dev.components.form_producto import form_producto
from dev.components.tabla_generica import tabla_generica


class DemoState(rx.State):
    productos: list[dict] = [
        {
            "nombre": "Harina de trigo",
            "categoria": "Harinas",
            "unidad": "kg",
            "stock": 50.0,
            "stock_min": 20.0,
        },
        {
            "nombre": "Azúcar blanca",
            "categoria": "Endulzantes",
            "unidad": "kg",
            "stock": 30.0,
            "stock_min": 15.0,
        },
        {
            "nombre": "Levadura seca",
            "categoria": "Fermentos",
            "unidad": "g",
            "stock": 500.0,
            "stock_min": 200.0,
        },
        {
            "nombre": "Mantequilla",
            "categoria": "Lácteos",
            "unidad": "kg",
            "stock": 8.0,
            "stock_min": 10.0,
        },
        {
            "nombre": "Huevos",
            "categoria": "Proteínas",
            "unidad": "unidades",
            "stock": 120.0,
            "stock_min": 60.0,
        },
    ]
    total_productos: int = 5
    pagina_actual: int = 1

    form_nombre: str = ""
    form_descripcion: str = ""
    form_categoria_id: str = ""
    form_unidad_id: str = ""
    form_stock_minimo: str = "0"
    form_ubicacion: str = ""
    form_loading: bool = False

    categorias: list[dict] = [
        {"id": 1, "nombre": "Harinas"},
        {"id": 2, "nombre": "Endulzantes"},
        {"id": 3, "nombre": "Lácteos"},
    ]
    unidades_medida: list[dict] = [
        {"id": 1, "nombre": "Kilogramos (kg)"},
        {"id": 2, "nombre": "Gramos (g)"},
        {"id": 3, "nombre": "Litros (L)"},
    ]

    alertas: list[dict] = [
        {
            "tipo": "stock_bajo",
            "producto": "Mantequilla",
            "stock_actual": "8",
            "stock_minimo": "10",
        },
        {"tipo": "caducidad", "producto": "Levadura seca", "fecha": "2026-04-20"},
    ]

    def set_nombre(self, v):
        self.form_nombre = v

    def set_descripcion(self, v):
        self.form_descripcion = v

    def set_categoria(self, v):
        self.form_categoria_id = v

    def set_unidad(self, v):
        self.form_unidad_id = v

    def set_stock_minimo(self, v):
        self.form_stock_minimo = v

    def set_ubicacion(self, v):
        self.form_ubicacion = v

    def pagina_siguiente(self):
        if self.pagina_actual < 1:
            self.pagina_actual += 1

    def pagina_anterior(self):
        if self.pagina_actual > 1:
            self.pagina_actual -= 1

    def on_submit_form(self):
        self.form_loading = True
        yield
        self.form_loading = False
        return rx.toast.success("Formulario enviado (demo)")

    def on_confirm_delete(self):
        return rx.toast.success("Eliminación confirmada (demo)")

    def on_confirm_deactivate(self):
        return rx.toast.success("Desactivación confirmada (demo)")

    def on_alert_click(self):
        return rx.toast.info("Alerta clickeada (demo)")

    def on_dismiss_alert(self):
        return rx.toast.info("Alerta descartada (demo)")


TABLA_COLUMNS = [
    {"key": "nombre", "label": "Producto", "width": "30%"},
    {"key": "categoria", "label": "Categoría", "width": "20%"},
    {"key": "unidad", "label": "Unidad", "width": "15%"},
    {"key": "stock", "label": "Stock", "width": "15%"},
    {"key": "stock_min", "label": "Stock mín.", "width": "20%"},
]


def _section_heading(title: str, description: str) -> rx.Component:
    return rx.vstack(
        rx.heading(title, size="5", weight="bold"),
        rx.text(description, size="2", color="gray"),
        spacing="1",
        width="100%",
    )


def demo_components() -> rx.Component:
    return base_layout(
        rx.container(
            rx.vstack(
                rx.heading("Demo de Componentes", size="8", weight="bold"),
                rx.text(
                    "Página de prueba para validar diseño y funcionamiento de cada componente UI.",
                    size="3",
                    color="gray",
                ),
                spacing="1",
                width="100%",
                padding_bottom="1em",
            ),
            rx.divider(),
            rx.vstack(
                _section_heading("Stat Cards", "Tarjetas KPI para el dashboard"),
                rx.grid(
                    stat_card(
                        "Productos",
                        rx.Var.create(156),
                        "package",
                        "blue",
                        rx.Var.create("12 nuevos este mes"),
                    ),
                    stat_card(
                        "Stock bajo",
                        rx.Var.create(8),
                        "flag_triangle_left",
                        "orange",
                        rx.Var.create("Requiere atención"),
                    ),
                    stat_card(
                        "Por vencer",
                        rx.Var.create(3),
                        "calendar-clock",
                        "red",
                        rx.Var.create("Próximos 7 días"),
                    ),
                    stat_card(
                        "Recetas activas",
                        rx.Var.create(24),
                        "chef-hat",
                        "green",
                        rx.Var.create("3 modificadas hoy"),
                    ),
                    columns="4",
                    spacing="4",
                    width="100%",
                ),
                rx.grid(
                    stat_card_simple("Entradas hoy", rx.Var.create(12), "blue"),
                    stat_card_simple("Salidas hoy", rx.Var.create(7), "red"),
                    stat_card_simple("Producción", rx.Var.create(35), "green"),
                    stat_card_simple("Proveedores", rx.Var.create(18), "purple"),
                    columns="4",
                    spacing="4",
                    width="100%",
                ),
                spacing="4",
                width="100%",
                class_name="py-4",
            ),
            rx.divider(),
            rx.vstack(
                _section_heading(
                    "Alertas", "Cards de alerta para stock bajo y caducidad"
                ),
                rx.vstack(
                    alerta_card(
                        "Advertencia genérica",
                        rx.Var.create("Este es un mensaje de alerta warning"),
                        "warning",
                        "triangle-alert",
                    ),
                    alerta_card(
                        "Error crítico",
                        rx.Var.create("Se requiere acción inmediata"),
                        "danger",
                        "shield-alert",
                    ),
                    alerta_card(
                        "Información",
                        rx.Var.create("Nuevo lote registrado correctamente"),
                        "info",
                        "info",
                    ),
                    alerta_card(
                        "Éxito",
                        rx.Var.create("Producción diaria registrada"),
                        "success",
                        "circle-check",
                    ),
                    spacing="3",
                    width="100%",
                ),
                rx.hstack(
                    alerta_stock_bajo(
                        rx.Var.create("Mantequilla"),
                        rx.Var.create("8"),
                        rx.Var.create("10"),
                    ),
                    alerta_caducidad(
                        rx.Var.create("Levadura seca"),
                        rx.Var.create("2026-04-20"),
                    ),
                    spacing="4",
                    width="100%",
                ),
                spacing="4",
                width="100%",
                class_name="py-4",
            ),
            rx.divider(),
            rx.vstack(
                _section_heading("Tabla Genérica", "Tabla reutilizable con paginación"),
                tabla_generica(
                    columns=TABLA_COLUMNS,
                    data=DemoState.productos,
                    total_items=DemoState.total_productos,
                    pagina_actual=DemoState.pagina_actual,
                    filas_por_pagina=rx.Var.create(10),
                    on_pagina_siguiente=DemoState.pagina_siguiente,
                    on_pagina_anterior=DemoState.pagina_anterior,
                    empty_message="No hay productos registrados",
                ),
                spacing="4",
                width="100%",
                class_name="py-4",
            ),
            rx.divider(),
            rx.vstack(
                _section_heading(
                    "Modal de Confirmación", "Diálogos de confirmación y desactivación"
                ),
                rx.hstack(
                    modal_confirmacion(
                        trigger=rx.button(
                            "Eliminar registro", color_scheme="red", variant="solid"
                        ),
                        titulo="Eliminar producto",
                        descripcion="¿Estás seguro de eliminar este producto? Esta acción no se puede deshacer.",
                        texto_confirmar="Eliminar",
                        on_confirm=DemoState.on_confirm_delete,
                        color_scheme="red",
                    ),
                    modal_desactivar(
                        trigger=rx.button(
                            "Desactivar registro",
                            color_scheme="orange",
                            variant="outline",
                        ),
                        on_confirm=DemoState.on_confirm_deactivate,
                        nombre_recurso="el producto 'Harina de trigo'",
                    ),
                    spacing="4",
                ),
                spacing="4",
                width="100%",
                class_name="py-4",
            ),
            rx.divider(),
            rx.vstack(
                _section_heading(
                    "Formulario de Producto",
                    "Formulario reutilizable para crear/editar productos",
                ),
                rx.card(
                    form_producto(
                        nombre_value=DemoState.form_nombre,
                        descripcion_value=DemoState.form_descripcion,
                        categoria_id_value=DemoState.form_categoria_id,
                        unidad_medida_id_value=DemoState.form_unidad_id,
                        stock_minimo_value=DemoState.form_stock_minimo,
                        ubicacion_value=DemoState.form_ubicacion,
                        categorias=DemoState.categorias,
                        unidades_medida=DemoState.unidades_medida,
                        on_nombre_change=DemoState.set_nombre,
                        on_descripcion_change=DemoState.set_descripcion,
                        on_categoria_change=DemoState.set_categoria,
                        on_unidad_change=DemoState.set_unidad,
                        on_stock_minimo_change=DemoState.set_stock_minimo,
                        on_ubicacion_change=DemoState.set_ubicacion,
                        on_submit=DemoState.on_submit_form,
                        submit_label="Crear producto (demo)",
                        loading=DemoState.form_loading,
                    ),
                    width="100%",
                    max_width="600px",
                ),
                spacing="4",
                width="100%",
                class_name="py-4",
            ),
            spacing="6",
            width="100%",
            class_name="bg-white rounded-lg px-10 shadow-sm",
        ),
    )
