import reflex as rx

from ..states.produccion_state import ProduccionState
from ..components.layout import base_layout


def _produccion_row(p: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(p["fecha"], size="2")),
        rx.table.cell(rx.text(p.get("receta_nombre", ""), size="2", weight="medium")),
        rx.table.cell(
            rx.badge(p["cantidad_producida"], color_scheme="green"),
        ),
        rx.table.cell(
            rx.text(p.get("observaciones", ""), size="2", color="gray"),
        ),
        rx.table.cell(
            rx.button(
                rx.icon("eye", size=14),
                variant="ghost",
                size="1",
                on_click=lambda: ProduccionState.ver_detalle(p["id"]),
            )
        ),
    )


def produccion_diaria() -> rx.Component:
    return rx.box(
        base_layout(
            rx.vstack(
                rx.hstack(
                    rx.heading("Producción Diaria", size="7", weight="bold"),
                    rx.spacer(),
                    rx.button(
                        rx.icon("plus", size=16),
                        "Nueva producción",
                        on_click=ProduccionState.abrir_crear,
                    ),
                    width="100%",
                    align="center",
                ),
                rx.hstack(
                    rx.vstack(
                        rx.text("Desde", size="2", weight="medium"),
                        rx.input(
                            type="date",
                            value=ProduccionState.fecha_filtro_inicio,
                            on_change=ProduccionState.set_fecha_filtro_inicio,
                            size="2",
                        ),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Hasta", size="2", weight="medium"),
                        rx.input(
                            type="date",
                            value=ProduccionState.fecha_filtro_fin,
                            on_change=ProduccionState.set_fecha_filtro_fin,
                            size="2",
                        ),
                        spacing="1",
                    ),
                    rx.button(
                        rx.icon("search", size=14),
                        "Filtrar",
                        variant="soft",
                        on_click=ProduccionState.filtrar_periodo,
                    ),
                    spacing="3",
                    align="end",
                ),
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Fecha"),
                                rx.table.column_header_cell("Receta"),
                                rx.table.column_header_cell("Cantidad", width="100px"),
                                rx.table.column_header_cell("Observaciones"),
                                rx.table.column_header_cell("Acciones", width="60px"),
                            )
                        ),
                        rx.table.body(
                            rx.cond(
                                ProduccionState.producciones.length() > 0,
                                rx.foreach(
                                    ProduccionState.producciones, _produccion_row
                                ),
                                rx.table.row(
                                    rx.table.cell(
                                        rx.text(
                                            "No hay producciones en el periodo seleccionado",
                                            color="gray",
                                            text_align="center",
                                            padding_y="2em",
                                        ),
                                        col_span=5,
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
                        rx.dialog.title("Registrar producción"),
                        rx.dialog.description(
                            "Seleccione una receta y la cantidad a producir. El sistema descontará los insumos automáticamente (FIFO)."
                        ),
                        rx.vstack(
                            rx.vstack(
                                rx.text("Receta *", size="2", weight="medium"),
                                rx.select.root(
                                    rx.select.trigger(placeholder="Seleccionar receta"),
                                    rx.select.content(
                                        rx.foreach(
                                            ProduccionState.recetas,
                                            lambda r: rx.select.item(
                                                r["nombre"], value=r["id"].to_string()
                                            ),
                                        ),
                                    ),
                                    value=ProduccionState.form_receta_id,
                                    on_change=ProduccionState.on_receta_change,
                                ),
                                spacing="1",
                                width="100%",
                            ),
                            rx.hstack(
                                rx.vstack(
                                    rx.text("Cantidad *", size="2", weight="medium"),
                                    rx.input(
                                        type="number",
                                        value=ProduccionState.form_cantidad,
                                        on_change=ProduccionState.set_form_cantidad,
                                        size="2",
                                        width="120px",
                                    ),
                                    spacing="1",
                                ),
                                rx.vstack(
                                    rx.text("Fecha *", size="2", weight="medium"),
                                    rx.input(
                                        type="date",
                                        value=ProduccionState.form_fecha,
                                        on_change=ProduccionState.set_form_fecha,
                                        size="2",
                                    ),
                                    spacing="1",
                                ),
                                spacing="4",
                                width="100%",
                            ),
                            rx.cond(
                                ProduccionState.ingredientes_receta.length() > 0,
                                rx.vstack(
                                    rx.text(
                                        "Insumos requeridos (x1):",
                                        size="2",
                                        weight="medium",
                                    ),
                                    rx.foreach(
                                        ProduccionState.ingredientes_receta,
                                        lambda i: rx.hstack(
                                            rx.text(
                                                "Producto #"
                                                + i["producto_id"].to_string(),
                                                size="2",
                                            ),
                                            rx.badge(
                                                i["cantidad"], color_scheme="blue"
                                            ),
                                            spacing="3",
                                            width="100%",
                                            padding_y="0.15em",
                                        ),
                                    ),
                                    spacing="2",
                                    width="100%",
                                    padding="0.75em",
                                    background="var(--gray-2)",
                                    border_radius="8px",
                                ),
                                rx.box(),
                            ),
                            rx.vstack(
                                rx.text("Observaciones", size="2", weight="medium"),
                                rx.text_area(
                                    placeholder="Notas adicionales (opcional)",
                                    value=ProduccionState.form_observaciones,
                                    on_change=ProduccionState.set_form_observaciones,
                                    size="2",
                                    width="100%",
                                ),
                                spacing="1",
                                width="100%",
                            ),
                            rx.cond(
                                ProduccionState.error_message != "",
                                rx.callout(
                                    ProduccionState.error_message,
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
                                "Verificar disponibilidad",
                                variant="outline",
                                color_scheme="green",
                                on_click=ProduccionState.verificar_disponibilidad,
                            ),
                            rx.spacer(),
                            rx.button(
                                "Cancelar",
                                variant="soft",
                                color_scheme="gray",
                                on_click=ProduccionState.cerrar_dialog,
                            ),
                            rx.button(
                                "Registrar",
                                on_click=ProduccionState.guardar_produccion,
                            ),
                            spacing="3",
                            padding_top="1em",
                            width="100%",
                        ),
                        max_width="550px",
                        max_height="85vh",
                        overflow_y="auto",
                    ),
                    open=ProduccionState.dialog_open,
                    on_open_change=ProduccionState.cerrar_dialog,
                ),
                rx.dialog.root(
                    rx.dialog.content(
                        rx.dialog.title("Verificar disponibilidad"),
                        rx.cond(
                            ProduccionState.verificacion_open,
                            rx.vstack(
                                rx.hstack(
                                    rx.text(
                                        "Receta: ",
                                        size="2",
                                        weight="medium",
                                    ),
                                    rx.text(
                                        ProduccionState.verificacion_receta_nombre,
                                        size="2",
                                    ),
                                    rx.text(
                                        " x"
                                        + ProduccionState.verificacion_resultado.get(
                                            "cantidad", "1"
                                        ),
                                        size="2",
                                        weight="bold",
                                    ),
                                    spacing="2",
                                ),
                                rx.badge(
                                    rx.cond(
                                        ProduccionState.verificacion_resultado.get(
                                            "disponible", False
                                        ),
                                        "Insumos disponibles",
                                        "Insumos insuficientes",
                                    ),
                                    color_scheme=rx.cond(
                                        ProduccionState.verificacion_resultado.get(
                                            "disponible", False
                                        ),
                                        "green",
                                        "red",
                                    ),
                                    size="2",
                                ),
                                rx.foreach(
                                    ProduccionState.verificacion_resultado.get(
                                        "detalle", []
                                    ),
                                    lambda d: rx.hstack(
                                        rx.text(d["nombre"], size="2", width="150px"),
                                        rx.text(
                                            "Necesario: " + d["cantidad_necesaria"],
                                            size="1",
                                            color="gray",
                                        ),
                                        rx.text(
                                            "Stock: " + d["stock_actual"],
                                            size="1",
                                        ),
                                        rx.badge(
                                            rx.cond(
                                                d["suficiente"],
                                                "OK",
                                                "Falta: " + d["faltante"],
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
                        rx.box(padding_top="1em"),
                        rx.hstack(
                            rx.spacer(),
                            rx.button(
                                "Cerrar",
                                variant="soft",
                                color_scheme="gray",
                                on_click=ProduccionState.cerrar_verificacion,
                            ),
                            width="100%",
                        ),
                        max_width="500px",
                    ),
                    open=ProduccionState.verificacion_open,
                    on_open_change=ProduccionState.cerrar_verificacion,
                ),
                rx.dialog.root(
                    rx.dialog.content(
                        rx.dialog.title("Detalle de producción"),
                        rx.cond(
                            ProduccionState.detalle_open,
                            rx.vstack(
                                rx.hstack(
                                    rx.text("Receta:", weight="medium", size="2"),
                                    rx.text(
                                        ProduccionState.detalle_produccion[
                                            "receta_nombre"
                                        ],
                                        size="2",
                                    ),
                                    spacing="3",
                                ),
                                rx.hstack(
                                    rx.text("Fecha:", weight="medium", size="2"),
                                    rx.text(
                                        ProduccionState.detalle_produccion["fecha"],
                                        size="2",
                                    ),
                                    rx.text("Cantidad:", weight="medium", size="2"),
                                    rx.badge(
                                        ProduccionState.detalle_produccion[
                                            "cantidad_producida"
                                        ],
                                        color_scheme="green",
                                    ),
                                    spacing="3",
                                ),
                                rx.divider(),
                                rx.heading("Lotes consumidos (FIFO)", size="4"),
                                rx.foreach(
                                    ProduccionState.detalle_produccion["detalles"],
                                    lambda d: rx.hstack(
                                        rx.text(
                                            "Lote #" + d["lote_id"].to_string(),
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
                            on_click=ProduccionState.cerrar_detalle,
                            width="100%",
                        ),
                        max_width="500px",
                    ),
                    open=ProduccionState.detalle_open,
                    on_open_change=ProduccionState.cerrar_detalle,
                ),
                spacing="5",
                width="100%",
            ),
        ),
        on_load=ProduccionState.on_load,
    )
