import reflex as rx

from ..states.entrada_salida_state import EntradaSalidaState
from ..components.layout import base_layout


def _lote_row(lote: dict, index: int) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.text("Producto *", size="1", weight="medium"),
            rx.select.root(
                rx.select.trigger(placeholder="Producto", size="2"),
                rx.select.content(
                    rx.foreach(
                        EntradaSalidaState.productos,
                        lambda p: rx.select.item(
                            p["nombre"], value=p["id"].to_string()
                        ),
                    ),
                ),
                value=rx.cond(
                    lote["producto_id"] != None,
                    lote["producto_id"].to_string(),
                    "",
                ),
                on_change=lambda v: EntradaSalidaState.set_lote_producto(index, v),
            ),
            spacing="1",
            width="100%",
        ),
        rx.vstack(
            rx.text("Cantidad *", size="1", weight="medium"),
            rx.input(
                type="number",
                placeholder="0",
                value=lote["cantidad"],
                on_change=lambda v: EntradaSalidaState.set_lote_cantidad(index, v),
                size="2",
                width="120px",
            ),
            spacing="1",
        ),
        rx.vstack(
            rx.text("Vencimiento", size="1", weight="medium"),
            rx.input(
                type="date",
                value=lote["fecha_vencimiento"],
                on_change=lambda v: EntradaSalidaState.set_lote_vencimiento(index, v),
                size="2",
            ),
            spacing="1",
        ),
        rx.vstack(
            rx.text("Código lote", size="1", weight="medium"),
            rx.input(
                placeholder="Lote-001",
                value=lote["codigo_lote"],
                on_change=lambda v: EntradaSalidaState.set_lote_codigo(index, v),
                size="2",
            ),
            spacing="1",
        ),
        rx.button(
            rx.icon("x", size=14),
            variant="ghost",
            color_scheme="red",
            size="1",
            on_click=lambda: EntradaSalidaState.eliminar_lote(index),
        ),
        spacing="3",
        width="100%",
        align="end",
        padding_y="0.25em",
        border_bottom="1px solid var(--gray-4)",
    )


def _entrada_row(e: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(e.get("fecha", ""), size="2")),
        rx.table.cell(rx.text(e.get("tipo", ""), size="2")),
        rx.table.cell(rx.text(e.get("factura", ""), size="2", color="gray")),
        rx.table.cell(rx.text(e.get("total_lotes", "0"), size="2")),
        rx.table.cell(
            rx.hstack(
                rx.button(
                    rx.icon("eye", size=14),
                    variant="ghost",
                    size="1",
                    on_click=lambda: EntradaSalidaState.ver_detalle_entrada(e["id"]),
                ),
                spacing="1",
            )
        ),
    )


def entradas() -> rx.Component:
    return base_layout(
        rx.vstack(
            rx.hstack(
                rx.heading("Entradas de Inventario", size="7", weight="bold"),
                rx.spacer(),
                rx.button(
                    rx.icon("plus", size=16),
                    "Nueva entrada",
                    on_click=EntradaSalidaState.abrir_crear_entrada,
                ),
                width="100%",
                align="center",
            ),
            rx.hstack(
                rx.vstack(
                    rx.text("Desde", size="2", weight="medium"),
                    rx.input(
                        type="date",
                        value=EntradaSalidaState.fecha_inicio,
                        on_change=EntradaSalidaState.set_fecha_inicio,
                        size="2",
                    ),
                    spacing="1",
                ),
                rx.vstack(
                    rx.text("Hasta", size="2", weight="medium"),
                    rx.input(
                        type="date",
                        value=EntradaSalidaState.fecha_fin,
                        on_change=EntradaSalidaState.set_fecha_fin,
                        size="2",
                    ),
                    spacing="1",
                ),
                rx.button(
                    rx.icon("search", size=14),
                    "Filtrar",
                    variant="soft",
                    on_click=EntradaSalidaState.filtrar_periodo,
                ),
                spacing="3",
                align="end",
            ),
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Fecha"),
                            rx.table.column_header_cell("Tipo"),
                            rx.table.column_header_cell("Factura"),
                            rx.table.column_header_cell("Lotes"),
                            rx.table.column_header_cell("Acciones"),
                        )
                    ),
                    rx.table.body(
                        rx.cond(
                            EntradaSalidaState.entradas.length() > 0,
                            rx.foreach(EntradaSalidaState.entradas, _entrada_row),
                            rx.table.row(
                                rx.table.cell(
                                    rx.text(
                                        "No hay entradas en el periodo seleccionado",
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
                    rx.dialog.title("Registrar entrada"),
                    rx.dialog.description(
                        "Complete los datos de la entrada y agregue lotes de productos."
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.vstack(
                                rx.text("Tipo de entrada *", size="2", weight="medium"),
                                rx.select.root(
                                    rx.select.trigger(placeholder="Tipo", size="2"),
                                    rx.select.content(
                                        rx.foreach(
                                            EntradaSalidaState.tipos_entrada,
                                            lambda t: rx.select.item(
                                                t["nombre"],
                                                value=t["id"].to_string(),
                                            ),
                                        ),
                                    ),
                                    value=EntradaSalidaState.form_entrada_tipo_id,
                                    on_change=EntradaSalidaState.set_form_entrada_tipo_id,
                                ),
                                spacing="1",
                                width="100%",
                            ),
                            rx.vstack(
                                rx.text("Proveedor", size="2", weight="medium"),
                                rx.select.root(
                                    rx.select.trigger(
                                        placeholder="Proveedor (opcional)",
                                        size="2",
                                    ),
                                    rx.select.content(
                                        rx.foreach(
                                            EntradaSalidaState.proveedores,
                                            lambda p: rx.select.item(
                                                p["nombre"],
                                                value=p["id"].to_string(),
                                            ),
                                        ),
                                    ),
                                    value=EntradaSalidaState.form_entrada_proveedor_id,
                                    on_change=EntradaSalidaState.set_form_entrada_proveedor_id,
                                ),
                                spacing="1",
                                width="100%",
                            ),
                            spacing="4",
                            width="100%",
                        ),
                        rx.hstack(
                            rx.vstack(
                                rx.text("Fecha *", size="2", weight="medium"),
                                rx.input(
                                    type="date",
                                    value=EntradaSalidaState.form_entrada_fecha,
                                    on_change=EntradaSalidaState.set_form_entrada_fecha,
                                    size="2",
                                ),
                                spacing="1",
                            ),
                            rx.vstack(
                                rx.text("N° Factura", size="2", weight="medium"),
                                rx.input(
                                    placeholder="Opcional",
                                    value=EntradaSalidaState.form_entrada_factura,
                                    on_change=EntradaSalidaState.set_form_entrada_factura,
                                    size="2",
                                ),
                                spacing="1",
                            ),
                            spacing="4",
                            width="100%",
                        ),
                        rx.vstack(
                            rx.text("Observaciones", size="2", weight="medium"),
                            rx.text_area(
                                placeholder="Notas adicionales (opcional)",
                                value=EntradaSalidaState.form_entrada_observaciones,
                                on_change=EntradaSalidaState.set_form_entrada_observaciones,
                                size="2",
                            ),
                            spacing="1",
                            width="100%",
                        ),
                        rx.divider(),
                        rx.hstack(
                            rx.heading("Lotes", size="4"),
                            rx.spacer(),
                            rx.button(
                                rx.icon("plus", size=14),
                                "Agregar lote",
                                variant="soft",
                                size="1",
                                on_click=EntradaSalidaState.agregar_lote,
                            ),
                            width="100%",
                            align="center",
                        ),
                        rx.foreach(
                            EntradaSalidaState.form_entrada_lotes,
                            lambda lote, idx=0: _lote_row(lote, idx),
                        ),
                        rx.cond(
                            EntradaSalidaState.error_message != "",
                            rx.callout(
                                EntradaSalidaState.error_message,
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
                            on_click=EntradaSalidaState.cerrar_dialog_entrada,
                        ),
                        rx.button(
                            "Registrar entrada",
                            on_click=EntradaSalidaState.guardar_entrada,
                        ),
                        spacing="3",
                        justify="end",
                        padding_top="1em",
                        width="100%",
                    ),
                    max_width="700px",
                    max_height="85vh",
                    overflow_y="auto",
                ),
                open=EntradaSalidaState.dialog_entrada_open,
                on_open_change=EntradaSalidaState.cerrar_dialog_entrada,
            ),
            rx.dialog.root(
                rx.dialog.content(
                    rx.dialog.title("Detalle de entrada"),
                    rx.cond(
                        EntradaSalidaState.detalle_entrada_open,
                        rx.vstack(
                            rx.hstack(
                                rx.text("Fecha:", weight="medium", size="2"),
                                rx.text(
                                    EntradaSalidaState.detalle_entrada["fecha"],
                                    size="2",
                                ),
                                rx.text("Factura:", weight="medium", size="2"),
                                rx.text(
                                    EntradaSalidaState.detalle_entrada["factura"],
                                    size="2",
                                    color="gray",
                                ),
                                spacing="3",
                                flex_wrap="wrap",
                            ),
                            rx.text(
                                EntradaSalidaState.detalle_entrada["observaciones"],
                                size="2",
                                color="gray",
                            ),
                            rx.divider(),
                            rx.heading("Lotes", size="4"),
                            rx.foreach(
                                EntradaSalidaState.detalle_entrada_lotes,
                                lambda l: rx.hstack(
                                    rx.text(
                                        "Producto #",
                                        l["producto_id"].to_string(),
                                        size="2",
                                    ),
                                    rx.badge(l["cantidad"], color_scheme="blue"),
                                    rx.text(
                                        l["codigo_lote"],
                                        size="2",
                                        color="gray",
                                    ),
                                    rx.text(
                                        "Vence: ",
                                        l["fecha_vencimiento"],
                                        size="2",
                                        color="gray",
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
                    rx.button(
                        "Cerrar",
                        variant="soft",
                        color_scheme="gray",
                        on_click=EntradaSalidaState.cerrar_detalle_entrada,
                        width="100%",
                    ),
                    max_width="500px",
                ),
                open=EntradaSalidaState.detalle_entrada_open,
                on_open_change=EntradaSalidaState.cerrar_detalle_entrada,
            ),
            spacing="5",
            width="100%",
        ),
    )
