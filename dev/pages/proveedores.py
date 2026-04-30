import reflex as rx

from ..states.proveedor_state import ProveedorState
from ..components.layout import base_layout


def _proveedor_row(p: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(p["nombre"], weight="medium", size="2")),
        rx.table.cell(rx.text(p["telefono"], size="2", color="gray")),
        rx.table.cell(rx.text(p["correo"], size="2", color="gray")),
        rx.table.cell(rx.text(p["direccion"], size="2", color="gray")),
        rx.table.cell(
            rx.badge(
                rx.cond(p["activo"], "Activo", "Inactivo"),
                color_scheme=rx.cond(p["activo"], "green", "gray"),
            ),
        ),
        rx.table.cell(
            rx.hstack(
                rx.button(
                    rx.icon("pencil", size=14),
                    "Editar",
                    variant="ghost",
                    size="1",
                    on_click=lambda: ProveedorState.abrir_editar(p["id"]),
                ),
                rx.button(
                    rx.icon("trash-2", size=14),
                    "Desactivar",
                    variant="ghost",
                    size="1",
                    color_scheme="red",
                    on_click=lambda: ProveedorState.confirmar_desactivar(p["id"]),
                ),
                spacing="1",
                width="100%",
            ),
        ),
    )


def _proveedor_form() -> rx.Component:
    return rx.vstack(
        rx.vstack(
            rx.text("Nombre *", size="2", weight="medium"),
            rx.input(
                placeholder="Nombre del proveedor",
                value=ProveedorState.form_nombre,
                on_change=ProveedorState.set_form_nombre,
                size="2",
                width="100%",
            ),
            spacing="2",
            width="100%",
        ),
        rx.hstack(
            rx.vstack(
                rx.text("Teléfono", size="2", weight="medium"),
                rx.input(
                    placeholder="Ej: 8888-8888",
                    value=ProveedorState.form_telefono,
                    on_change=ProveedorState.set_form_telefono,
                    size="2",
                    width="100%",
                ),
                spacing="2",
                width="100%",
            ),
            rx.vstack(
                rx.text("Correo", size="2", weight="medium"),
                rx.input(
                    placeholder="correo@ejemplo.com",
                    value=ProveedorState.form_correo,
                    on_change=ProveedorState.set_form_correo,
                    size="2",
                    width="100%",
                ),
                spacing="2",
                width="100%",
            ),
            spacing="4",
            width="100%",
        ),
        rx.vstack(
            rx.text("Dirección", size="2", weight="medium"),
            rx.input(
                placeholder="Dirección exacta (opcional)",
                value=ProveedorState.form_direccion,
                on_change=ProveedorState.set_form_direccion,
                size="2",
                width="100%",
            ),
            spacing="2",
            width="100%",
        ),
        rx.vstack(
            rx.text("Notas", size="2", weight="medium"),
            rx.text_area(
                placeholder="Notas adicionales (opcional)",
                value=ProveedorState.form_notas,
                on_change=ProveedorState.set_form_notas,
                size="2",
                width="100%",
            ),
            spacing="2",
            width="100%",
        ),
        rx.cond(
            ProveedorState.error_message != "",
            rx.callout(
                ProveedorState.error_message,
                icon="circle-alert",
                color_scheme="red",
                size="1",
            ),
        ),
        spacing="4",
        width="100%",
    )


def proveedores() -> rx.Component:
    return base_layout(
        rx.vstack(
            rx.hstack(
                rx.heading("Proveedores", size="7", weight="bold"),
                rx.spacer(),
                rx.button(
                    rx.icon("plus", size=16),
                    "Nuevo proveedor",
                    on_click=ProveedorState.abrir_crear,
                ),
                width="100%",
                align="center",
            ),
            rx.hstack(
                rx.hstack(
                    rx.input(
                        placeholder="Buscar proveedores...",
                        value=ProveedorState.search_query,
                        on_change=ProveedorState.set_search_query,
                        size="2",
                        width="250px",
                    ),
                    rx.button(
                        rx.icon("search", size=14),
                        variant="soft",
                        on_click=ProveedorState.buscar_proveedores,
                    ),
                    rx.button(
                        rx.icon("x", size=14),
                        variant="ghost",
                        on_click=ProveedorState.limpiar_filtros,
                    ),
                    spacing="2",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.text(
                        ProveedorState.total_proveedores.to_string() + " proveedores",
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
                            rx.table.column_header_cell("Nombre"),
                            rx.table.column_header_cell("Teléfono"),
                            rx.table.column_header_cell("Correo"),
                            rx.table.column_header_cell("Dirección"),
                            rx.table.column_header_cell("Estado"),
                            rx.table.column_header_cell(""),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(ProveedorState.proveedores, _proveedor_row),
                    ),
                    width="100%",
                ),
                rx.hstack(
                    rx.text(
                        "Página "
                        + ProveedorState.pagina_actual.to_string()
                        + " de "
                        + ProveedorState.total_paginas.to_string(),
                        size="2",
                        color="gray",
                    ),
                    rx.spacer(),
                    rx.hstack(
                        rx.button(
                            rx.icon("chevron-left", size=16),
                            variant="outline",
                            size="1",
                            on_click=ProveedorState.pagina_anterior,
                        ),
                        rx.button(
                            rx.icon("chevron-right", size=16),
                            variant="outline",
                            size="1",
                            on_click=ProveedorState.pagina_siguiente,
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
                            ProveedorState.modo_editar,
                            "Editar proveedor",
                            "Nuevo proveedor",
                        )
                    ),
                    rx.dialog.description(
                        rx.cond(
                            ProveedorState.modo_editar,
                            "Modifica los datos del proveedor.",
                            "Completa los datos para registrar un nuevo proveedor.",
                        ),
                    ),
                    _proveedor_form(),
                    rx.hstack(
                        rx.button(
                            "Cancelar",
                            variant="soft",
                            color_scheme="gray",
                            on_click=ProveedorState.cerrar_dialog,
                        ),
                        rx.button(
                            rx.cond(
                                ProveedorState.modo_editar,
                                "Actualizar",
                                "Crear proveedor",
                            ),
                            on_click=ProveedorState.guardar_proveedor,
                        ),
                        spacing="3",
                        justify="end",
                        padding_top="1em",
                        width="100%",
                    ),
                    max_width="500px",
                ),
                open=ProveedorState.dialog_open,
                on_open_change=ProveedorState.cerrar_dialog,
            ),
            rx.dialog.root(
                rx.dialog.content(
                    rx.dialog.title("Desactivar proveedor"),
                    rx.dialog.description(
                        "¿Desactivar ",
                        rx.text(ProveedorState.confirm_proveedor_nombre, weight="bold"),
                        "? El proveedor se marcará como inactivo pero no se eliminará.",
                    ),
                    rx.hstack(
                        rx.button(
                            "Cancelar",
                            variant="soft",
                            color_scheme="gray",
                            on_click=ProveedorState.cerrar_confirm,
                        ),
                        rx.button(
                            "Desactivar",
                            color_scheme="orange",
                            on_click=ProveedorState.ejecutar_desactivar,
                        ),
                        spacing="3",
                        justify="end",
                        padding_top="1em",
                        width="100%",
                    ),
                    max_width="400px",
                ),
                open=ProveedorState.confirm_open,
                on_open_change=ProveedorState.cerrar_confirm,
            ),
            spacing="5",
            width="100%",
        ),
    )
