"""
alerta_card.py — Cards de alerta para stock bajo y caducidad.

Capa: Components / Presentation

Descripción:
    Componentes de tarjeta para mostrar alertas del sistema.
    Incluye variantes genéricas (warning, danger, info, success) y
    especializadas para stock bajo y productos próximos a vencer.

Componentes:
    - alerta_card: Card genérica con tipo, icono, título, mensaje.
    - alerta_stock_bajo: Card preconfigurada para alertas de bajo stock.
    - alerta_caducidad: Card preconfigurada para productos por vencer.

Uso:
    from dev.components.alerta_card import alerta_card, alerta_stock_bajo, alerta_caducidad

    alerta_card("Atención", rx.Var.create("Mensaje"), "warning")
    alerta_stock_bajo(rx.Var.create("Harina"), rx.Var.create("5"), rx.Var.create("20"))
    alerta_caducidad(rx.Var.create("Levadura"), rx.Var.create("2026-04-20"))

Tipos disponibles: "warning" (orange), "danger" (red), "info" (blue), "success" (green).
Iconos usan nombres de Lucide.
"""

import reflex as rx


def alerta_card(
    titulo: str,
    mensaje: rx.Var,
    tipo: str = "warning",
    icon_name: str = "triangle-alert",
    on_click: rx.EventHandler = None,
    on_dismiss: rx.EventHandler = None,
) -> rx.Component:
    color_map = {
        "warning": "orange",
        "danger": "red",
        "info": "blue",
        "success": "green",
    }
    scheme = color_map.get(tipo, "gray")

    return rx.card(
        rx.hstack(
            rx.icon(icon_name, size=20, color=f"var(--{scheme}-9)"),
            rx.vstack(
                rx.text(titulo, size="3", weight="bold"),
                rx.text(mensaje, size="2", color="gray"),
                spacing="1",
                width="100%",
            ),
            rx.spacer(),
            rx.cond(
                on_dismiss is not None,
                rx.button(
                    rx.icon("x", size=14),
                    variant="ghost",
                    size="1",
                    on_click=on_dismiss,
                ),
                rx.box(),
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        width="100%",
        border_left=f"3px solid var(--{scheme}-9)",
        padding="0.75em",
        cursor=rx.cond(on_click is not None, "pointer", "default"),
        on_click=on_click,
    )


def alerta_stock_bajo(
    producto_nombre: rx.Var,
    stock_actual: rx.Var,
    stock_minimo: rx.Var,
    on_click=None,
) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.icon("trending-down", size=20, color="var(--orange-9)"),
            rx.vstack(
                rx.text("Stock bajo", size="3", weight="bold"),
                rx.hstack(
                    rx.text(producto_nombre, size="2", color="gray"),
                    rx.text(" — Stock: ", size="2", color="gray"),
                    rx.text(stock_actual, size="2", weight="bold"),
                    rx.text(" / Mínimo: ", size="2", color="gray"),
                    rx.text(stock_minimo, size="2", weight="bold"),
                    spacing="0",
                    flex_wrap="wrap",
                ),
                spacing="1",
                width="100%",
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        width="100%",
        border_left="3px solid var(--orange-9)",
        padding="0.75em",
        cursor=rx.cond(on_click is not None, "pointer", "default"),
        on_click=on_click,
    )


def alerta_caducidad(
    producto_nombre: rx.Var,
    fecha_vencimiento: rx.Var,
    on_click=None,
) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.icon("calendar-clock", size=20, color="var(--red-9)"),
            rx.vstack(
                rx.text("Próximo a vencer", size="3", weight="bold"),
                rx.hstack(
                    rx.text(producto_nombre, size="2", color="gray"),
                    rx.text(" — Vence: ", size="2", color="gray"),
                    rx.text(fecha_vencimiento, size="2", weight="bold"),
                    spacing="0",
                    flex_wrap="wrap",
                ),
                spacing="1",
                width="100%",
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        width="100%",
        border_left="3px solid var(--red-9)",
        padding="0.75em",
        cursor=rx.cond(on_click is not None, "pointer", "default"),
        on_click=on_click,
    )
