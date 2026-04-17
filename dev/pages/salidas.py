import reflex as rx

from ..states.entrada_salida_state import EntradaSalidaState
from ..components.layout import base_layout


def _detalle_salida_row(d: dict, index: int) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.text("Lote *", size="1", weight="medium"),
            rx.select.root(
                rx.select.trigger(placeholder="Seleccionar lote", size="2"),
                rx.select.content(
                    rx.foreach(
                        EntradaSalidaState.lotes_disponibles,
                        lambda l: rx.select.item(
                            l["codigo"],
                            " (",
                            l["cantidad"],
                            ")",
                            value=l["id"].to_string(),
                        ),
                    ),
                ),
                value=rx.cond(
                    d["lote_id"] != None,
                    d["lote_id"].to_string(),
                    "",
                ),
                on_change=lambda v: EntradaSalidaState.set_detalle_lote(index, v),
            ),
            spacing="1",
            width="100%",
        ),
        rx.vstack(
            rx.text("Cantidad *", size="1", weight="medium"),
            rx.input(
                type="number",
                placeholder="0",
                value=d["cantidad"],
                on_change=lambda v: EntradaSalidaState.set_detalle_cantidad(index, v),
                size="2",
                width="120px",
            ),
            spacing="1",
        ),
        rx.vstack(
            rx.text("Motivo", size="1", weight="medium"),
            rx.input(
                placeholder="Ej: Consumo diario",
                value=d["motivo"],
                on_change=lambda v: EntradaSalidaState.set_detalle_motivo(index, v),
                size="2",
            ),
            spacing="1",
        ),
        rx.button(
            rx.icon("x", size=14),
            variant="ghost",
            color_scheme="red",
            size="1",
            on_click=lambda: EntradaSalidaState.eliminar_detalle_salida(index),
        ),
        spacing="3",
        width="100%",
        align="end",
        padding_y="0.25em",
        border_bottom="1px solid var(--gray-4)",
    )


def _salida_row(s: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(s.get("fecha", ""), size="2")),
        rx.table.cell(rx.text(s.get("tipo", ""), size="2")),
        rx.table.cell(rx.text(s.get("observaciones", ""), size="2", color="gray")),
        rx.table.cell(rx.text(s.get("total_detalles", "0"), size="2")),
        rx.table.cell(
            rx.button(
                rx.icon("eye", size=14),
                variant="ghost",
                size="1",
                on_click=lambda: EntradaSalidaState.ver_detalle_salida(s["id"]),
            )
        ),
    )


def salidas() -> rx.Component:
    return base_layout(
        rx.vstack(
            rx.hstack(
                rx.heading("Salidas de Inventario", size="7", weight="bold"),
                rx.spacer(),
                rx.button(
                    rx.icon("plus", size=16),
                    "Nueva salida",
                    on_click=EntradaSalidaState.abrir_crear_salida,
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
                            rx.table.column_header_cell("Observaciones"),
                            rx.table.column_header_cell("Detalles"),
                            rx.table.column_header_cell("Acciones"),
                        )
                    ),
                    rx.table.body(
                        rx.cond(
                            EntradaSalidaState.salidas.length() > 0,
                            rx.foreach(EntradaSalidaState.salidas, _salida_row),
                            rx.table.row(
                                rx.table.cell(
                                    rx.text(
                                        "No hay salidas en el periodo seleccionado",
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
                    rx.dialog.title("Registrar salida"),
                    rx.dialog.description(
                        "Seleccione los lotes a descontar del inventario."
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.vstack(
                                rx.text("Tipo de salida *", size="2", weight="medium"),
                                rx.select.root(
                                    rx.select.trigger(placeholder="Tipo", size="2"),
                                    rx.select.content(
                                        rx.foreach(
                                            EntradaSalidaState.tipos_salida,
                                            lambda t: rx.select.item(
                                                t["nombre"],
                                                value=t["id"].to_string(),
                                            ),
                                        ),
                                    ),
                                    value=EntradaSalidaState.form_salida_tipo_id,
                                    on_change=EntradaSalidaState.set_form_salida_tipo_id,
                                ),
                                spacing="1",
                                width="100%",
                            ),
                            rx.vstack(
                                rx.text("Fecha *", size="2", weight="medium"),
                                rx.input(
                                    type="date",
                                    value=EntradaSalidaState.form_salida_fecha,
                                    on_change=EntradaSalidaState.set_form_salida_fecha,
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
                                value=EntradaSalidaState.form_salida_observaciones,
                                on_change=EntradaSalidaState.set_form_salida_observaciones,
                                size="2",
                            ),
                            spacing="1",
                            width="100%",
                        ),
                        rx.divider(),
                        rx.hstack(
                            rx.heading("Detalles", size="4"),
                            rx.spacer(),
                            rx.button(
                                rx.icon("plus", size=14),
                                "Agregar detalle",
                                variant="soft",
                                size="1",
                                on_click=EntradaSalidaState.agregar_detalle_salida,
                            ),
                            width="100%",
                            align="center",
                        ),
                        rx.foreach(
                            EntradaSalidaState.form_salida_detalles,
                            lambda det, idx=0: _detalle_salida_row(det, idx),
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
                            on_click=EntradaSalidaState.cerrar_dialog_salida,
                        ),
                        rx.button(
                            "Registrar salida",
                            on_click=EntradaSalidaState.guardar_salida,
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
                open=EntradaSalidaState.dialog_salida_open,
                on_open_change=EntradaSalidaState.cerrar_dialog_salida,
            ),
            rx.dialog.root(
                rx.dialog.content(
                    rx.dialog.title("Detalle de salida"),
                    rx.cond(
                        EntradaSalidaState.detalle_salida_open,
                        rx.vstack(
                            rx.hstack(
                                rx.text("Fecha:", weight="medium", size="2"),
                                rx.text(
                                    EntradaSalidaState.detalle_salida["fecha"],
                                    size="2",
                                ),
                                spacing="3",
                            ),
                            rx.text(
                                EntradaSalidaState.detalle_salida["observaciones"],
                                size="2",
                                color="gray",
                            ),
                            rx.divider(),
                            rx.heading("Detalles", size="4"),
                            rx.foreach(
                                EntradaSalidaState.detalle_salida_detalles,
                                lambda d: rx.hstack(
                                    rx.text(
                                        "Lote #",
                                        d["lote_id"].to_string(),
                                        size="2",
                                    ),
                                    rx.badge(d["cantidad"], color_scheme="red"),
                                    rx.text(
                                        d["motivo"],
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
                        on_click=EntradaSalidaState.cerrar_detalle_salida,
                        width="100%",
                    ),
                    max_width="500px",
                ),
                open=EntradaSalidaState.detalle_salida_open,
                on_open_change=EntradaSalidaState.cerrar_detalle_salida,
            ),
            spacing="5",
            width="100%",
        ),
    )
