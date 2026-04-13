"""
stat_card.py — Tarjetas KPI para el dashboard.

Capa: Components / Presentation

Descripción:
    Componentes de tarjeta para mostrar métricas clave (KPIs).
    Dos variantes: stat_card (con icono y subtítulo) y stat_card_simple (solo label + valor).

Componentes:
    - stat_card: Card con icono, label, valor y subtítulo opcional.
    - stat_card_simple: Card mínima con label y valor grande.

Uso:
    from dev.components.stat_card import stat_card, stat_card_simple

    stat_card("Productos", rx.Var.create(156), "package", "blue",
              subtitle=rx.Var.create("12 nuevos este mes"))
    stat_card_simple("Entradas hoy", rx.Var.create(12), "blue")

Color schemes: "blue", "green", "red", "orange", "purple", "gray".
Iconos usan nombres de Lucide (https://lucide.dev/icons/).
"""

import reflex as rx


def stat_card(
    label: str,
    value: rx.Var,
    icon_name: str = "activity",
    color_scheme: str = "blue",
    subtitle: rx.Var = None,
) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.box(
                rx.icon(icon_name, size=24),
                padding="0.75em",
                border_radius="10px",
                background=f"var(--{color_scheme}-3)",
                color=f"var(--{color_scheme}-11)",
                display="flex",
                align_items="center",
                justify_content="center",
            ),
            rx.vstack(
                rx.text(
                    label,
                    size="2",
                    color="gray",
                    weight="medium",
                ),
                rx.heading(
                    value,
                    size="6",
                    weight="bold",
                ),
                rx.cond(
                    subtitle is not None,
                    rx.text(subtitle, size="1", color="gray"),
                    rx.box(),
                ),
                spacing="1",
                width="100%",
            ),
            spacing="4",
            align="start",
            width="100%",
        ),
        width="100%",
        padding="1em",
    )


def stat_card_simple(
    label: str,
    value: rx.Var,
    color_scheme: str = "blue",
) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.text(label, size="2", color="gray"),
            rx.heading(
                value,
                size="7",
                weight="bold",
                color=f"var(--{color_scheme}-11)",
            ),
            spacing="1",
            width="100%",
        ),
        width="100%",
        padding="1.25em",
    )
