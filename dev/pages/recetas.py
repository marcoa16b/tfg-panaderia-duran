import reflex as rx

from ..states.receta_state import RecetaState
from ..components.layout import base_layout


def _ingrediente_row(ing: dict, index: int) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.text("Producto *", size="1", weight="medium"),
            rx.select.root(
                rx.select.trigger(placeholder="Seleccionar producto", size="2"),
                rx.select.content(
                    rx.foreach(
                        RecetaState.productos,
                        lambda p: rx.select.item(
                            p["nombre"], value=p["id"].to_string()
                        ),
                    ),
                ),
                value=rx.cond(
                    ing["producto_id"] != None,
                    ing["producto_id"].to_string(),
                    "",
                ),
                on_change=lambda v: RecetaState.set_ingrediente_producto(index, v),
            ),
            spacing="1",
            width="100%",
        ),
        rx.vstack(
            rx.text("Cantidad *", size="1", weight="medium"),
            rx.input(
                type="number",
                placeholder="0",
                value=ing["cantidad"],
                on_change=lambda v: RecetaState.set_ingrediente_cantidad(index, v),
                size="2",
                width="120px",
            ),
            spacing="1",
        ),
        rx.button(
            rx.icon("x", size=14),
            variant="ghost",
            color_scheme="red",
            size="1",
            on_click=lambda: RecetaState.eliminar_ingrediente(index),
        ),
        spacing="3",
        width="100%",
        align="end",
        padding_y="0.25em",
        border_bottom="1px solid var(--gray-4)",
    )


def _receta_row(r: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(r["nombre"], weight="medium", size="2")),
        rx.table.cell(
            rx.text(r["total_ingredientes"], size="2"),
            width="80px",
        ),
        rx.table.cell(
            rx.badge(
                rx.cond(r["activo"] == True, "Activa", "Inactiva"),
                color_scheme=rx.cond(r["activo"] == True, "green", "gray"),
            ),
            width="80px",
        ),
        rx.table.cell(
            rx.hstack(
                rx.button(
                    rx.icon("eye", size=14),
                    variant="ghost",
                    size="1",
                    on_click=lambda: RecetaState.ver_detalle(r["id"]),
                ),
                rx.button(
                    rx.icon("pencil", size=14),
                    variant="ghost",
                    size="1",
                    on_click=lambda: RecetaState.abrir_editar(r["id"]),
                ),
                rx.button(
                    rx.icon("check-circle", size=14),
                    variant="ghost",
                    size="1",
                    color_scheme="green",
                    on_click=lambda: RecetaState.abrir_verificar_disponibilidad(
                        r["id"]
                    ),
                ),
                rx.button(
                    rx.icon("trash-2", size=14),
                    variant="ghost",
                    size="1",
                    color_scheme="red",
                    on_click=lambda: RecetaState.confirmar_desactivar(r["id"]),
                ),
                spacing="1",
            )
        ),
    )


def recetas() -> rx.Component:
    return base_layout(
        rx.vstack(
            rx.hstack(
                rx.heading("Recetas", size="7", weight="bold"),
                rx.spacer(),
                rx.hstack(
                    rx.input(
                        placeholder="Buscar recetas...",
                        value=RecetaState.search_query,
                        on_change=RecetaState.set_search_query,
                        size="2",
                        width="220px",
                    ),
                    rx.button(
                        rx.icon("search", size=14),
                        variant="soft",
                        on_click=RecetaState.buscar,
                    ),
                    rx.button(
                        rx.icon("plus", size=16),
                        "Nueva receta",
                        on_click=RecetaState.abrir_crear,
                    ),
                    spacing="2",
                ),
                width="100%",
                align="center",
            ),
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Receta"),
                            rx.table.column_header_cell("Ingredientes", width="80px"),
                            rx.table.column_header_cell("Estado", width="80px"),
                            rx.table.column_header_cell("Acciones"),
                        )
                    ),
                    rx.table.body(
                        rx.cond(
                            RecetaState.recetas.length() > 0,
                            rx.foreach(RecetaState.recetas, _receta_row),
                            rx.table.row(
                                rx.table.cell(
                                    rx.text(
                                        "No hay recetas registradas",
                                        color="gray",
                                        text_align="center",
                                        padding_y="2em",
                                    ),
                                    col_span=4,
                                )
                            ),
                        ),
                    ),
                    width="100%",
                ),
                width="100%",
            ),
            rx.dialog.root(
                rx.dialog.content(
                    rx.dialog.title(
                        rx.cond(
                            RecetaState.modo_editar,
                            "Editar receta",
                            "Nueva receta",
                        )
                    ),
                    rx.vstack(
                        rx.vstack(
                            rx.text("Nombre *", size="2", weight="medium"),
                            rx.input(
                                placeholder="Ej: Pan francés",
                                value=RecetaState.form_nombre,
                                on_change=RecetaState.set_form_nombre,
                                size="2",
                                width="100%",
                            ),
                            spacing="1",
                            width="100%",
                        ),
                        rx.vstack(
                            rx.text("Descripción", size="2", weight="medium"),
                            rx.text_area(
                                placeholder="Descripción de la receta (opcional)",
                                value=RecetaState.form_descripcion,
                                on_change=RecetaState.set_form_descripcion,
                                size="2",
                                width="100%",
                            ),
                            spacing="1",
                            width="100%",
                        ),
                        rx.vstack(
                            rx.text("Producto final *", size="2", weight="medium"),
                            rx.select.root(
                                rx.select.trigger(
                                    placeholder="Producto que se obtiene"
                                ),
                                rx.select.content(
                                    rx.foreach(
                                        RecetaState.productos,
                                        lambda p: rx.select.item(
                                            p["nombre"],
                                            value=p["id"].to_string(),
                                        ),
                                    ),
                                ),
                                value=RecetaState.form_producto_id,
                                on_change=RecetaState.set_form_producto_id,
                            ),
                            spacing="1",
                            width="100%",
                        ),
                        rx.divider(),
                        rx.hstack(
                            rx.heading("Ingredientes", size="4"),
                            rx.spacer(),
                            rx.button(
                                rx.icon("plus", size=14),
                                "Agregar",
                                variant="soft",
                                size="1",
                                on_click=RecetaState.agregar_ingrediente,
                            ),
                            width="100%",
                            align="center",
                        ),
                        rx.foreach(
                            RecetaState.form_ingredientes,
                            lambda ing, idx=0: _ingrediente_row(ing, idx),
                        ),
                        rx.cond(
                            RecetaState.error_message != "",
                            rx.callout(
                                RecetaState.error_message,
                                icon="circle-alert",
                                color_scheme="red",
                                size="1",
                            ),
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    rx.hstack(
                        rx.button(
                            "Cancelar",
                            variant="soft",
                            color_scheme="gray",
                            on_click=RecetaState.cerrar_dialog,
                        ),
                        rx.button(
                            rx.cond(
                                RecetaState.modo_editar,
                                "Actualizar",
                                "Crear receta",
                            ),
                            on_click=RecetaState.guardar_receta,
                        ),
                        spacing="3",
                        justify="end",
                        padding_top="1em",
                        width="100%",
                    ),
                    max_width="600px",
                    max_height="85vh",
                    overflow_y="auto",
                ),
                open=RecetaState.dialog_open,
                on_open_change=RecetaState.cerrar_dialog,
            ),
            rx.dialog.root(
                rx.dialog.content(
                    rx.dialog.title("Detalle de receta"),
                    rx.cond(
                        RecetaState.detalle_open,
                        rx.vstack(
                            rx.heading(
                                RecetaState.detalle_receta["nombre"],
                                size="5",
                            ),
                            rx.text(
                                RecetaState.detalle_receta["descripcion"],
                                size="2",
                                color="gray",
                            ),
                            rx.divider(),
                            rx.heading("Ingredientes", size="4"),
                            rx.foreach(
                                RecetaState.detalle_ingredientes,
                                lambda d: rx.hstack(
                                    rx.text(
                                        "Producto #",
                                        d["producto_id"].to_string(),
                                        size="2",
                                    ),
                                    rx.badge(d["cantidad"], color_scheme="blue"),
                                    spacing="3",
                                    width="100%",
                                    padding_y="0.25em",
                                    border_bottom="1px solid var(--gray-4)",
                                ),
                            ),
                            spacing="3",
                            width="100%",
                        ),
                        rx.box(),
                    ),
                    rx.box(padding_top="1em"),
                    rx.button(
                        "Cerrar",
                        variant="soft",
                        color_scheme="gray",
                        on_click=RecetaState.cerrar_detalle,
                        width="100%",
                    ),
                    max_width="500px",
                ),
                open=RecetaState.detalle_open,
                on_open_change=RecetaState.cerrar_detalle,
            ),
            rx.dialog.root(
                rx.dialog.content(
                    rx.dialog.title("Verificar disponibilidad"),
                    rx.dialog.description(
                        "Verifica si hay insumos suficientes para producir esta receta."
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.text("Cantidad a producir:", size="2", weight="medium"),
                            rx.input(
                                type="number",
                                value=RecetaState.disponibilidad_cantidad,
                                on_change=RecetaState.set_disponibilidad_cantidad,
                                size="2",
                                width="100px",
                            ),
                            rx.button(
                                "Verificar",
                                on_click=RecetaState.verificar_disponibilidad,
                            ),
                            spacing="3",
                            align="center",
                        ),
                        rx.cond(
                            RecetaState.disponibilidad_resultado != {},
                            rx.vstack(
                                rx.badge(
                                    rx.cond(
                                        RecetaState.disponibilidad_resultado.get(
                                            "disponible", False
                                        ),
                                        "Insumos disponibles",
                                        "Insumos insuficientes",
                                    ),
                                    color_scheme=rx.cond(
                                        RecetaState.disponibilidad_resultado.get(
                                            "disponible", False
                                        ),
                                        "green",
                                        "red",
                                    ),
                                    size="2",
                                ),
                                rx.foreach(
                                    RecetaState.disponibilidad_detalle,
                                    lambda d: rx.hstack(
                                        rx.text(d["nombre"], size="2"),
                                        rx.text(
                                            "Necesario: ",
                                            d["cantidad_necesaria"],
                                            size="1",
                                            color="gray",
                                        ),
                                        rx.text(
                                            "Stock: ",
                                            d["stock_actual"],
                                            size="1",
                                        ),
                                        rx.badge(
                                            rx.cond(
                                                d["suficiente"],
                                                rx.text("OK", size="1"),
                                                rx.text(
                                                    "Falta: ", d["faltante"], size="1"
                                                ),
                                            ),
                                            color_scheme=rx.cond(
                                                d["suficiente"], "green", "red"
                                            ),
                                        ),
                                        spacing="3",
                                        width="100%",
                                        padding_y="0.25em",
                                        border_bottom="1px solid var(--gray-4)",
                                    ),
                                ),
                                spacing="3",
                                width="100%",
                            ),
                            rx.box(),
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    rx.box(padding_top="1em"),
                    rx.button(
                        "Cerrar",
                        variant="soft",
                        color_scheme="gray",
                        on_click=RecetaState.cerrar_disponibilidad,
                        width="100%",
                    ),
                    max_width="500px",
                ),
                open=RecetaState.disponibilidad_open,
                on_open_change=RecetaState.cerrar_disponibilidad,
            ),
            rx.dialog.root(
                rx.dialog.content(
                    rx.dialog.title("Desactivar receta"),
                    rx.dialog.description(
                        "¿Desactivar ",
                        rx.text(RecetaState.confirm_receta_nombre, weight="bold"),
                        "? La receta se marcará como inactiva.",
                    ),
                    rx.hstack(
                        rx.button(
                            "Cancelar",
                            variant="soft",
                            color_scheme="gray",
                            on_click=RecetaState.cerrar_confirm,
                        ),
                        rx.button(
                            "Desactivar",
                            color_scheme="orange",
                            on_click=RecetaState.ejecutar_desactivar,
                        ),
                        spacing="3",
                        justify="end",
                        padding_top="1em",
                        width="100%",
                    ),
                    max_width="400px",
                ),
                open=RecetaState.confirm_open,
                on_open_change=RecetaState.cerrar_confirm,
            ),
            spacing="5",
            width="100%",
        ),
    )
