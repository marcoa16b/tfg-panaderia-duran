"""
modal_confirmacion.py — Diálogos de confirmación reutilizables.

Capa: Components / Presentation

Descripción:
    Componentes de diálogo modal para confirmar acciones destructivas.
    Usa rx.alert_dialog (modal nativo de Radix UI).

Componentes:
    - modal_confirmacion: Modal genérico con título, descripción y botones.
    - modal_desactivar: Variante preconfigurada para soft-delete.

Uso:
    from dev.components.modal_confirmacion import modal_confirmacion, modal_desactivar

    modal_confirmacion(
        trigger=rx.button("Eliminar", color_scheme="red"),
        titulo="Eliminar producto",
        descripcion="¿Eliminar este producto?",
        on_confirm=MiState.eliminar,
    )

    modal_desactivar(
        trigger=rx.button("Desactivar"),
        on_confirm=MiState.desactivar,
        nombre_recurso="el producto 'Harina'",
    )
"""

import reflex as rx


def modal_confirmacion(
    trigger: rx.Component,
    titulo: str = "Confirmar acción",
    descripcion: str = "¿Estás seguro de que deseas continuar?",
    texto_confirmar: str = "Confirmar",
    texto_cancelar: str = "Cancelar",
    on_confirm: rx.EventHandler = None,
    color_scheme: str = "red",
) -> rx.Component:
    return rx.alert_dialog.root(
        rx.alert_dialog.trigger(trigger),
        rx.alert_dialog.content(
            rx.alert_dialog.title(titulo),
            rx.alert_dialog.description(descripcion),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button(
                        texto_cancelar,
                        variant="soft",
                        color_scheme="gray",
                    ),
                ),
                rx.alert_dialog.action(
                    rx.button(
                        texto_confirmar,
                        color_scheme=color_scheme,
                        on_click=on_confirm,
                    ),
                ),
                spacing="3",
                justify="end",
                padding_top="1em",
            ),
        ),
    )


def modal_desactivar(
    trigger: rx.Component,
    on_confirm: rx.EventHandler,
    nombre_recurso: str = "este registro",
) -> rx.Component:
    return modal_confirmacion(
        trigger=trigger,
        titulo="Desactivar registro",
        descripcion=f"¿Desactivar {nombre_recurso}? El registro se marcará como inactivo pero no se eliminará.",
        texto_confirmar="Desactivar",
        on_confirm=on_confirm,
        color_scheme="orange",
    )
