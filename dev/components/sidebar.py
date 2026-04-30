"""
sidebar.py — Barra de navegación lateral de la aplicación.

Capa: Components / Presentation

Descripción:
    Componente de navegación lateral (sidebar) que se muestra en el layout
    autenticado. Contiene el logo, enlaces a todas las páginas del sistema
    y datos del usuario con botón de logout.

Dependencias:
    - AuthState: Para mostrar email del usuario y cerrar sesión.

Uso:
    from dev.components.sidebar import sidebar

    sidebar()  # Se usa dentro de base_layout, no directamente en páginas

Notas:
    - Los items de navegación están definidos en NAV_ITEMS (lista de dicts).
    - Para agregar una nueva página, agregar un item a NAV_ITEMS.
    - Iconos usan nombres de Lucide (https://lucide.dev/icons/).
    - El sidebar es sticky (position="sticky") y no hace scroll con el contenido.
"""

import reflex as rx

from dev.states.auth_state import AuthState


NAV_ITEMS = [
    {"label": "Dashboard", "href": "/", "icon": "layout-dashboard"},
    {"label": "Productos", "href": "/productos", "icon": "package"},
    {"label": "Proveedores", "href": "/proveedores", "icon": "truck"},
    {"label": "Entradas", "href": "/entradas", "icon": "log-in"},
    {"label": "Salidas", "href": "/salidas", "icon": "log-out"},
    {"label": "Recetas", "href": "/recetas", "icon": "chef-hat"},
    {"label": "Producción", "href": "/produccion-diaria", "icon": "factory"},
    {"label": "Alertas", "href": "/alertas", "icon": "bell"},
    {"label": "Estadísticas", "href": "/estadisticas", "icon": "bar-chart-3"},
    {"label": "Reportes", "href": "/reportes", "icon": "file-text"},
]


def nav_item(item: dict) -> rx.Component:
    return rx.link(
        rx.hstack(
            rx.icon(item["icon"], size=18),
            rx.text(item["label"], size="3", weight="medium"),
            spacing="3",
            align="center",
            width="100%",
        ),
        href=item["href"],
        width="100%",
        padding="0.5em 0.75em",
        border_radius="8px",
        _hover={
            "background": rx.color_mode_cond(
                light="var(--gray-3)", dark="var(--gray-3)"
            ),
            "text_decoration": "none",
        },
        underline="none",
        color=rx.color_mode_cond(light="var(--gray-12)", dark="var(--gray-12)"),
    )


def sidebar() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.image(
                    src="/Duran-logo.png", 
                    width="2em",
                    height="auto",
                    border_radius="50%",
                ),
                rx.vstack(
                    rx.heading(
                        "Durán",
                        size="4",
                        weight="bold",
                        margin="0",
                    ),
                    rx.text(
                        "Panadería y Repostería",
                        size="1",
                        color="gray",
                        margin="0",
                    ),
                    spacing="0",
                    align="start",
                ),
                spacing="3",
                align="center",
                width="100%",
                padding_bottom="0.5em",
            ),
            rx.divider(),
            rx.vstack(
                rx.foreach(NAV_ITEMS, nav_item),
                spacing="1",
                width="100%",
                align="start",
            ),
            rx.spacer(),
            rx.divider(),
            rx.hstack(
                rx.icon("user", size=16),
                rx.text(
                    AuthState.user_email,
                    size="2",
                    truncate=True,
                ),
                spacing="2",
                align="center",
                width="100%",
                padding_x="0.5em",
            ),
            width="100%",
            height="100%",
            spacing="3",
            padding="1em",
            align="start",
        ),
        width="250px",
        min_width="250px",
        height="100vh",
        position="sticky",
        top="0",
        border_right=f"1px solid {rx.color_mode_cond(light='var(--gray-4)', dark='var(--gray-6)')}",
        background=rx.color_mode_cond(light="var(--gray-1)", dark="var(--gray-2)"),
        overflow_y="auto",
    )
