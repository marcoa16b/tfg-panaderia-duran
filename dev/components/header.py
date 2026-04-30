"""
header.py — Barra superior de la aplicación.

Capa: Components / Presentation

Descripción:
    Barra horizontal superior que se muestra en el layout autenticado.
    Contiene el toggle de dark/light mode, email del usuario y botón de logout.

Dependencias:
    - AuthState: Para mostrar email del usuario y cerrar sesión.

Uso:
    from dev.components.header import header

    header()  # Se usa dentro de base_layout, no directamente en páginas
"""

import reflex as rx

from dev.components.modal_confirmacion import modal_confirmacion
from dev.states.auth_state import AuthState


def header() -> rx.Component:
    return rx.hstack(
        rx.hstack(
            rx.color_mode.button(),
            spacing="3",
            align="center",
        ),
        rx.spacer(),
        rx.hstack(
            rx.text(
                AuthState.user_email,
                size="2",
                weight="medium",
                color="gray",
            ),
            modal_confirmacion(
                trigger=rx.button(
                    rx.icon("log-out", size=16),
                    rx.text("Cerrar sesión", class_name="max-sm:hidden"),
                    variant="ghost",
                    size="2",
                    color_scheme="red",
                    aria_label="Cerrar sesión",
                ),
                titulo="Cerrar sesión",
                descripcion="¿Estás seguro de que deseas cerrar tu sesión?",
                texto_confirmar="Cerrar sesión",
                on_confirm=AuthState.logout,
                color_scheme="red",
            ),
            spacing="3",
            align="center",
        ),
        width="100%",
        padding_x="1.5em",
        padding_y="0.75em",
        border_bottom=f"1px solid {rx.color_mode_cond(light='var(--gray-4)', dark='var(--gray-6)')}",
        background=rx.color_mode_cond(light="white", dark="var(--gray-1)"),
        align="center",
        role="banner",
    )
