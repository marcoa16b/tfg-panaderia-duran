"""
layout.py — Template base de la aplicación.

Capa: Components / Layout

Descripción:
    Componente de layout que envuelve todo el contenido de las páginas.
    Usa rx.cond para mostrar el layout autenticado (sidebar + header + contenido)
    o el layout de invitado (sin navegación, para login/recovery).

Dependencias:
    - AuthState: Para verificar si el usuario está autenticado.
    - sidebar: Barra de navegación lateral.
    - header: Barra superior.

Uso:
    from dev.components.layout import base_layout

    def mi_pagina() -> rx.Component:
        return base_layout(
            rx.heading("Mi página"),
            rx.text("Contenido aquí"),
        )

Estructura del layout autenticado:
    ┌──────────┬──────────────────────────────┐
    │          │  header (toggle tema + user)  │
    │ sidebar  ├──────────────────────────────┤
    │  (nav)   │  children (contenido página)  │
    │          │                              │
    └──────────┴──────────────────────────────┘
"""

import reflex as rx

from dev.states.auth_state import AuthState
from dev.components.sidebar import sidebar
from dev.components.header import header


def base_layout(*children) -> rx.Component:
    return rx.cond(
        AuthState.is_authenticated,
        _authenticated_layout(*children),
        _guest_layout(*children),
    )


def _authenticated_layout(*children) -> rx.Component:
    return rx.hstack(
        sidebar(),
        rx.box(
            header(),
            rx.box(
                *children,
                padding="1.5em",
                width="100%",
                min_height="calc(100vh - 53px)",
                overflow_y="auto",
                class_name="max-md:p-4",
            ),
            flex="1",
            display="flex",
            flex_direction="column",
            overflow="hidden",
            min_width="0",
        ),
        width="100%",
        min_height="100vh",
        align="start",
    )


def _guest_layout(*children) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text("Redirigiendo al login..."),
            class_name="flex flex-col items-center justify-center min-h-screen",
        ),
        width="100%",
        min_height="100vh",
    )
