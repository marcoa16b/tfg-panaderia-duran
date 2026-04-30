import reflex as rx

from ..states.config_state import ConfigState
from ..components.layout import base_layout


def _cat_row(c: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(c["nombre"], weight="medium", size="2")),
        rx.table.cell(rx.text(c["descripcion"], size="2", color="gray")),
        rx.table.cell(
            rx.badge(
                rx.cond(c["activo"], "Activo", "Inactivo"),
                color_scheme=rx.cond(c["activo"], "green", "gray"),
            ),
        ),
        rx.table.cell(
            rx.hstack(
                rx.button(
                    rx.icon("pencil", size=14),
                    "Editar",
                    variant="ghost",
                    size="1",
                    on_click=lambda: ConfigState.cat_abrir_editar(c["id"]),
                ),
                rx.cond(
                    c["activo"],
                    rx.button(
                        rx.icon("trash-2", size=14),
                        "Desactivar",
                        variant="ghost",
                        size="1",
                        color_scheme="red",
                        on_click=lambda: ConfigState.cat_confirmar_desactivar(c["id"]),
                    ),
                ),
                spacing="1",
                width="100%",
            ),
        ),
    )


def _cat_form() -> rx.Component:
    return rx.vstack(
        rx.vstack(
            rx.text("Nombre *", size="2", weight="medium"),
            rx.input(
                placeholder="Nombre de la categoría",
                value=ConfigState.cat_form_nombre,
                on_change=ConfigState.set_cat_form_nombre,
                size="2",
                width="100%",
            ),
            spacing="2",
            width="100%",
        ),
        rx.vstack(
            rx.text("Descripción", size="2", weight="medium"),
            rx.input(
                placeholder="Descripción (opcional)",
                value=ConfigState.cat_form_descripcion,
                on_change=ConfigState.set_cat_form_descripcion,
                size="2",
                width="100%",
            ),
            spacing="2",
            width="100%",
        ),
        rx.cond(
            ConfigState.error_message != "",
            rx.callout(
                ConfigState.error_message,
                icon="circle-alert",
                color_scheme="red",
                size="1",
            ),
        ),
        spacing="4",
        width="100%",
    )


def _categorias_tab() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading("Categorías de producto", size="5", weight="bold"),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=16),
                "Nueva categoría",
                on_click=ConfigState.cat_abrir_crear,
            ),
            width="100%",
            align="center",
        ),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Nombre"),
                        rx.table.column_header_cell("Descripción"),
                        rx.table.column_header_cell("Estado"),
                        rx.table.column_header_cell(""),
                    )
                ),
                rx.table.body(
                    rx.foreach(ConfigState.categorias, _cat_row),
                ),
                width="100%",
            ),
            width="100%",
        ),
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title(
                    rx.cond(
                        ConfigState.cat_modo_editar,
                        "Editar categoría",
                        "Nueva categoría",
                    )
                ),
                rx.dialog.description(
                    rx.cond(
                        ConfigState.cat_modo_editar,
                        "Modifica los datos de la categoría.",
                        "Completa los datos para crear una nueva categoría.",
                    ),
                ),
                _cat_form(),
                rx.hstack(
                    rx.button(
                        "Cancelar",
                        variant="soft",
                        color_scheme="gray",
                        on_click=ConfigState.cat_cerrar_dialog,
                    ),
                    rx.button(
                        rx.cond(
                            ConfigState.cat_modo_editar,
                            "Actualizar",
                            "Crear",
                        ),
                        on_click=ConfigState.cat_guardar,
                    ),
                    spacing="3",
                    justify="end",
                    padding_top="1em",
                    width="100%",
                ),
                max_width="450px",
            ),
            open=ConfigState.cat_dialog_open,
            on_open_change=ConfigState.cat_cerrar_dialog,
        ),
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title("Desactivar categoría"),
                rx.dialog.description(
                    "¿Desactivar ",
                    rx.text(ConfigState.cat_confirm_nombre, weight="bold"),
                    "? La categoría se marcará como inactiva.",
                ),
                rx.hstack(
                    rx.button(
                        "Cancelar",
                        variant="soft",
                        color_scheme="gray",
                        on_click=ConfigState.cat_cerrar_confirm,
                    ),
                    rx.button(
                        "Desactivar",
                        color_scheme="orange",
                        on_click=ConfigState.cat_ejecutar_desactivar,
                    ),
                    spacing="3",
                    justify="end",
                    padding_top="1em",
                    width="100%",
                ),
                max_width="400px",
            ),
            open=ConfigState.cat_confirm_open,
            on_open_change=ConfigState.cat_cerrar_confirm,
        ),
        spacing="4",
        width="100%",
    )


def _um_row(u: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(u["nombre"], weight="medium", size="2")),
        rx.table.cell(rx.code(u["abreviatura"], size="2")),
        rx.table.cell(
            rx.badge(
                rx.cond(u["activo"], "Activo", "Inactivo"),
                color_scheme=rx.cond(u["activo"], "green", "gray"),
            ),
        ),
        rx.table.cell(
            rx.hstack(
                rx.button(
                    rx.icon("pencil", size=14),
                    "Editar",
                    variant="ghost",
                    size="1",
                    on_click=lambda: ConfigState.um_abrir_editar(u["id"]),
                ),
                rx.cond(
                    u["activo"],
                    rx.button(
                        rx.icon("trash-2", size=14),
                        "Desactivar",
                        variant="ghost",
                        size="1",
                        color_scheme="red",
                        on_click=lambda: ConfigState.um_confirmar_desactivar(u["id"]),
                    ),
                ),
                spacing="1",
                width="100%",
            ),
        ),
    )


def _um_form() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text("Nombre *", size="2", weight="medium"),
                rx.input(
                    placeholder="Ej: Kilogramo",
                    value=ConfigState.um_form_nombre,
                    on_change=ConfigState.set_um_form_nombre,
                    size="2",
                    width="100%",
                ),
                spacing="2",
                width="100%",
            ),
            rx.vstack(
                rx.text("Abreviatura *", size="2", weight="medium"),
                rx.input(
                    placeholder="Ej: kg",
                    value=ConfigState.um_form_abreviatura,
                    on_change=ConfigState.set_um_form_abreviatura,
                    size="2",
                    width="120px",
                ),
                spacing="2",
                width="100%",
            ),
            spacing="4",
            width="100%",
        ),
        rx.cond(
            ConfigState.error_message != "",
            rx.callout(
                ConfigState.error_message,
                icon="circle-alert",
                color_scheme="red",
                size="1",
            ),
        ),
        spacing="4",
        width="100%",
    )


def _unidades_tab() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading("Unidades de medida", size="5", weight="bold"),
            rx.spacer(),
            rx.button(
                rx.icon("plus", size=16),
                "Nueva unidad",
                on_click=ConfigState.um_abrir_crear,
            ),
            width="100%",
            align="center",
        ),
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Nombre"),
                        rx.table.column_header_cell("Abreviatura"),
                        rx.table.column_header_cell("Estado"),
                        rx.table.column_header_cell(""),
                    )
                ),
                rx.table.body(
                    rx.foreach(ConfigState.unidades, _um_row),
                ),
                width="100%",
            ),
            width="100%",
        ),
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title(
                    rx.cond(
                        ConfigState.um_modo_editar,
                        "Editar unidad de medida",
                        "Nueva unidad de medida",
                    )
                ),
                rx.dialog.description(
                    rx.cond(
                        ConfigState.um_modo_editar,
                        "Modifica los datos de la unidad.",
                        "Completa los datos para registrar una nueva unidad.",
                    ),
                ),
                _um_form(),
                rx.hstack(
                    rx.button(
                        "Cancelar",
                        variant="soft",
                        color_scheme="gray",
                        on_click=ConfigState.um_cerrar_dialog,
                    ),
                    rx.button(
                        rx.cond(
                            ConfigState.um_modo_editar,
                            "Actualizar",
                            "Crear",
                        ),
                        on_click=ConfigState.um_guardar,
                    ),
                    spacing="3",
                    justify="end",
                    padding_top="1em",
                    width="100%",
                ),
                max_width="450px",
            ),
            open=ConfigState.um_dialog_open,
            on_open_change=ConfigState.um_cerrar_dialog,
        ),
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title("Desactivar unidad de medida"),
                rx.dialog.description(
                    "¿Desactivar ",
                    rx.text(ConfigState.um_confirm_nombre, weight="bold"),
                    "? La unidad se marcará como inactiva.",
                ),
                rx.hstack(
                    rx.button(
                        "Cancelar",
                        variant="soft",
                        color_scheme="gray",
                        on_click=ConfigState.um_cerrar_confirm,
                    ),
                    rx.button(
                        "Desactivar",
                        color_scheme="orange",
                        on_click=ConfigState.um_ejecutar_desactivar,
                    ),
                    spacing="3",
                    justify="end",
                    padding_top="1em",
                    width="100%",
                ),
                max_width="400px",
            ),
            open=ConfigState.um_confirm_open,
            on_open_change=ConfigState.um_cerrar_confirm,
        ),
        spacing="4",
        width="100%",
    )


def _perfil_tab() -> rx.Component:
    return rx.vstack(
        rx.heading("Mi perfil", size="5", weight="bold"),
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("user", size=20, color="var(--gray-11)"),
                    rx.text("Información personal", size="4", weight="bold"),
                    spacing="2",
                    align="center",
                ),
                rx.divider(),
                rx.hstack(
                    rx.vstack(
                        rx.text("Nombre", size="2", weight="medium"),
                        rx.input(
                            value=ConfigState.perfil_nombre,
                            on_change=ConfigState.set_perfil_nombre,
                            size="2",
                            width="100%",
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("Correo electrónico", size="2", weight="medium"),
                        rx.input(
                            value=ConfigState.perfil_correo,
                            on_change=ConfigState.set_perfil_correo,
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
                    ConfigState.error_message != "",
                    rx.callout(
                        ConfigState.error_message,
                        icon="circle-alert",
                        color_scheme="red",
                        size="1",
                    ),
                ),
                rx.cond(
                    ConfigState.success_message != "",
                    rx.callout(
                        ConfigState.success_message,
                        icon="check-circle",
                        color_scheme="green",
                        size="1",
                    ),
                ),
                rx.hstack(
                    rx.spacer(),
                    rx.button(
                        rx.icon("save", size=16),
                        "Guardar cambios",
                        on_click=ConfigState.guardar_perfil,
                    ),
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            width="100%",
        ),
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("lock", size=20, color="var(--gray-11)"),
                    rx.text("Seguridad", size="4", weight="bold"),
                    spacing="2",
                    align="center",
                ),
                rx.divider(),
                rx.hstack(
                    rx.text(
                        "Cambia tu contraseña de acceso periódicamente para mantener tu cuenta segura.",
                        size="2",
                        color="gray",
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.icon("key-round", size=16),
                        "Cambiar contraseña",
                        variant="outline",
                        on_click=ConfigState.pw_abrir_dialog,
                    ),
                    width="100%",
                    align="center",
                ),
                spacing="4",
                width="100%",
            ),
            width="100%",
        ),
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title("Cambiar contraseña"),
                rx.dialog.description(
                    "Ingresa tu contraseña actual y la nueva contraseña."
                ),
                rx.vstack(
                    rx.vstack(
                        rx.text("Contraseña actual", size="2", weight="medium"),
                        rx.input(
                            type="password",
                            placeholder="Contraseña actual",
                            value=ConfigState.perfil_actual_pw,
                            on_change=ConfigState.set_perfil_actual_pw,
                            size="2",
                            width="100%",
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("Nueva contraseña", size="2", weight="medium"),
                        rx.input(
                            type="password",
                            placeholder="Mínimo 8 caracteres",
                            value=ConfigState.perfil_nueva_pw,
                            on_change=ConfigState.set_perfil_nueva_pw,
                            size="2",
                            width="100%",
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("Confirmar nueva contraseña", size="2", weight="medium"),
                        rx.input(
                            type="password",
                            placeholder="Repetir nueva contraseña",
                            value=ConfigState.perfil_confirm_pw,
                            on_change=ConfigState.set_perfil_confirm_pw,
                            size="2",
                            width="100%",
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    rx.cond(
                        ConfigState.error_message != "",
                        rx.callout(
                            ConfigState.error_message,
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
                        on_click=ConfigState.pw_cerrar_dialog,
                    ),
                    rx.button(
                        "Cambiar contraseña",
                        on_click=ConfigState.cambiar_password,
                    ),
                    spacing="3",
                    justify="end",
                    padding_top="1em",
                    width="100%",
                ),
                max_width="450px",
            ),
            open=ConfigState.perfil_pw_dialog_open,
            on_open_change=ConfigState.pw_cerrar_dialog,
        ),
        spacing="4",
        width="100%",
    )


def configuracion() -> rx.Component:
    return base_layout(
        rx.vstack(
            rx.heading("Configuración", size="7", weight="bold"),
            rx.tabs.root(
                rx.tabs.list(
                    rx.tabs.trigger(
                        rx.icon("tag", size=14),
                        "Categorías",
                        value="categorias",
                    ),
                    rx.tabs.trigger(
                        rx.icon("ruler", size=14),
                        "Unidades",
                        value="unidades",
                    ),
                    rx.tabs.trigger(
                        rx.icon("user-cog", size=14),
                        "Mi perfil",
                        value="perfil",
                    ),
                ),
                rx.tabs.content(
                    _categorias_tab(),
                    value="categorias",
                ),
                rx.tabs.content(
                    _unidades_tab(),
                    value="unidades",
                ),
                rx.tabs.content(
                    _perfil_tab(),
                    value="perfil",
                ),
                value=ConfigState.tab_actual,
                on_change=ConfigState.set_tab,
                width="100%",
            ),
            spacing="5",
            width="100%",
        ),
    )
