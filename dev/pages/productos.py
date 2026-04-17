import reflex as rx

from ..states.producto_state import ProductoState
from ..components.layout import base_layout
from ..components.modal_confirmacion import modal_confirmacion


PRODUCTO_COLUMNS = [
    {"key": "nombre", "label": "Producto", "width": "25%"},
    {"key": "stock_actual", "label": "Stock actual", "width": "12%"},
    {"key": "stock_minimo", "label": "Stock mín.", "width": "12%"},
    {"key": "ubicacion", "label": "Ubicación", "width": "18%"},
    {"key": "activo", "label": "Estado", "width": "10%"},
    {"key": "acciones", "label": "", "width": "23%"},
]


def _product_row(p: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(p["nombre"], weight="medium", size="2"), width="25%"),
        rx.table.cell(
            rx.badge(
                p["stock_actual"],
                color_scheme=rx.cond(
                    p["stock_actual"] <= p["stock_minimo"], "red", "green"
                ),
            ),
            width="12%",
        ),
        rx.table.cell(rx.text(p["stock_minimo"], size="2"), width="12%"),
        rx.table.cell(rx.text(p["ubicacion"], size="2", color="gray"), width="18%"),
        rx.table.cell(
            rx.badge(
                rx.cond(p["activo"] == True, "Activo", "Inactivo"),
                color_scheme=rx.cond(p["activo"] == True, "green", "gray"),
            ),
            width="10%",
        ),
        rx.table.cell(
            rx.hstack(
                rx.button(
                    rx.icon("pencil", size=14),
                    "Editar",
                    variant="ghost",
                    size="1",
                    on_click=lambda: ProductoState.abrir_editar(p["id"]),
                ),
                rx.button(
                    rx.icon("trash-2", size=14),
                    "Desactivar",
                    variant="ghost",
                    size="1",
                    color_scheme="red",
                    on_click=lambda: ProductoState.confirmar_desactivar(p["id"]),
                ),
                spacing="1",
                width="100%",
            ),
            width="23%",
        ),
    )


def _producto_form() -> rx.Component:
    return rx.vstack(
        rx.vstack(
            rx.text("Nombre *", size="2", weight="medium"),
            rx.input(
                placeholder="Ej: Harina de trigo",
                value=ProductoState.form_nombre,
                on_change=ProductoState.set_form_nombre,
                size="2",
                width="100%",
            ),
            spacing="2",
            width="100%",
        ),
        rx.vstack(
            rx.text("Descripción", size="2", weight="medium"),
            rx.text_area(
                placeholder="Descripción del producto (opcional)",
                value=ProductoState.form_descripcion,
                on_change=ProductoState.set_form_descripcion,
                size="2",
                width="100%",
            ),
            spacing="2",
            width="100%",
        ),
        rx.hstack(
            rx.vstack(
                rx.text("Categoría *", size="2", weight="medium"),
                rx.select.root(
                    rx.select.trigger(placeholder="Seleccionar categoría"),
                    rx.select.content(
                        rx.foreach(
                            ProductoState.categorias,
                            lambda c: rx.select.item(
                                c["nombre"], value=c["id"].to_string()
                            ),
                        ),
                    ),
                    value=ProductoState.form_categoria_id,
                    on_change=ProductoState.set_form_categoria_id,
                ),
                spacing="2",
                width="100%",
            ),
            rx.vstack(
                rx.text("Unidad de medida *", size="2", weight="medium"),
                rx.select.root(
                    rx.select.trigger(placeholder="Seleccionar unidad"),
                    rx.select.content(
                        rx.foreach(
                            ProductoState.unidades_medida,
                            lambda u: rx.select.item(
                                u["nombre"], value=u["id"].to_string()
                            ),
                        ),
                    ),
                    value=ProductoState.form_unidad_medida_id,
                    on_change=ProductoState.set_form_unidad_medida_id,
                ),
                spacing="2",
                width="100%",
            ),
            spacing="4",
            width="100%",
        ),
        rx.hstack(
            rx.vstack(
                rx.text("Stock mínimo", size="2", weight="medium"),
                rx.input(
                    type="number",
                    value=ProductoState.form_stock_minimo,
                    on_change=ProductoState.set_form_stock_minimo,
                    size="2",
                    width="100%",
                ),
                spacing="2",
                width="100%",
            ),
            rx.vstack(
                rx.text("Ubicación", size="2", weight="medium"),
                rx.input(
                    placeholder="Ej: Estante A-3",
                    value=ProductoState.form_ubicacion,
                    on_change=ProductoState.set_form_ubicacion,
                    size="2",
                    width="100%",
                ),
                spacing="2",
                width="100%",
            ),
            spacing="4",
            width="100%",
        ),
        rx.cond(
            ProductoState.error_message != "",
            rx.callout(
                ProductoState.error_message,
                icon="circle-alert",
                color_scheme="red",
                size="1",
            ),
        ),
        spacing="4",
        width="100%",
    )


def productos() -> rx.Component:
    return rx.box(
        base_layout(
            rx.vstack(
                rx.hstack(
                    rx.heading("Productos", size="7", weight="bold"),
                    rx.spacer(),
                    rx.button(
                        rx.icon("plus", size=16),
                        "Nuevo producto",
                        on_click=ProductoState.abrir_crear,
                    ),
                    width="100%",
                    align="center",
                ),
                rx.hstack(
                    rx.hstack(
                        rx.input(
                            placeholder="Buscar productos...",
                            value=ProductoState.search_query,
                            on_change=ProductoState.set_search_query,
                            size="2",
                            width="250px",
                        ),
                        rx.button(
                            rx.icon("search", size=14),
                            variant="soft",
                            on_click=ProductoState.buscar_productos,
                        ),
                        rx.button(
                            rx.icon("x", size=14),
                            variant="ghost",
                            on_click=ProductoState.limpiar_filtros,
                        ),
                        spacing="2",
                    ),
                    rx.spacer(),
                    rx.select.root(
                        rx.select.trigger(placeholder="Categoría", size="2"),
                        rx.select.content(
                            rx.select.item("Todas", value="0"),
                            rx.foreach(
                                ProductoState.categorias,
                                lambda c: rx.select.item(
                                    c["nombre"], value=c["id"].to_string()
                                ),
                            ),
                        ),
                        on_change=ProductoState.filtrar_por_categoria,
                    ),
                    rx.hstack(
                        rx.text(
                            ProductoState.total_productos.to_string() + " productos",
                            size="2",
                            color="gray",
                        ),
                        spacing="2",
                        align="center",
                    ),
                    width="100%",
                    align="center",
                ),
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                *[
                                    rx.table.column_header_cell(
                                        col["label"], width=col["width"]
                                    )
                                    for col in PRODUCTO_COLUMNS
                                ]
                            )
                        ),
                        rx.table.body(
                            rx.foreach(ProductoState.productos, _product_row),
                        ),
                        width="100%",
                    ),
                    rx.hstack(
                        rx.text(
                            "Página "
                            + ProductoState.pagina_actual.to_string()
                            + " de "
                            + ProductoState.total_paginas.to_string(),
                            size="2",
                            color="gray",
                        ),
                        rx.spacer(),
                        rx.hstack(
                            rx.button(
                                rx.icon("chevron-left", size=16),
                                variant="outline",
                                size="1",
                                on_click=ProductoState.pagina_anterior,
                            ),
                            rx.button(
                                rx.icon("chevron-right", size=16),
                                variant="outline",
                                size="1",
                                on_click=ProductoState.pagina_siguiente,
                            ),
                            spacing="2",
                            align="center",
                        ),
                        width="100%",
                        padding_top="0.75em",
                        align="center",
                    ),
                    width="100%",
                ),
                rx.dialog.root(
                    rx.dialog.content(
                        rx.dialog.title(
                            rx.cond(
                                ProductoState.modo_editar,
                                "Editar producto",
                                "Nuevo producto",
                            )
                        ),
                        rx.dialog.description(
                            rx.cond(
                                ProductoState.modo_editar,
                                "Modifica los datos del producto.",
                                "Completa los datos para crear un nuevo producto.",
                            ),
                        ),
                        _producto_form(),
                        rx.hstack(
                            rx.button(
                                "Cancelar",
                                variant="soft",
                                color_scheme="gray",
                                on_click=ProductoState.cerrar_dialog,
                            ),
                            rx.button(
                                rx.cond(
                                    ProductoState.modo_editar,
                                    "Actualizar",
                                    "Crear producto",
                                ),
                                on_click=ProductoState.guardar_producto,
                            ),
                            spacing="3",
                            justify="end",
                            padding_top="1em",
                            width="100%",
                        ),
                        max_width="500px",
                    ),
                    open=ProductoState.dialog_open,
                    on_open_change=ProductoState.cerrar_dialog,
                ),
                rx.dialog.root(
                    rx.dialog.content(
                        rx.dialog.title("Desactivar producto"),
                        rx.dialog.description(
                            "¿Desactivar ",
                            rx.text(
                                ProductoState.confirm_producto_nombre, weight="bold"
                            ),
                            "? El producto se marcará como inactivo pero no se eliminará.",
                        ),
                        rx.hstack(
                            rx.button(
                                "Cancelar",
                                variant="soft",
                                color_scheme="gray",
                                on_click=ProductoState.cerrar_confirm,
                            ),
                            rx.button(
                                "Desactivar",
                                color_scheme="orange",
                                on_click=ProductoState.ejecutar_desactivar,
                            ),
                            spacing="3",
                            justify="end",
                            padding_top="1em",
                            width="100%",
                        ),
                        max_width="400px",
                    ),
                    open=ProductoState.confirm_open,
                    on_open_change=ProductoState.cerrar_confirm,
                ),
                spacing="5",
                width="100%",
            ),
        ),
        on_load=ProductoState.load_productos,
    )
