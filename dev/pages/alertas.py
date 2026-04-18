import reflex as rx

from ..states.dashboard_state import DashboardState
from ..components.layout import base_layout


def _alerta_row(a: dict) -> rx.Component:
    return rx.hstack(
        rx.icon(
            rx.cond(a["leida"] == True, "bell-off", "bell"),
            size=18,
            color=rx.cond(a["leida"] == True, "gray", "var(--orange-9)"),
        ),
        rx.box(
            rx.text(a["mensaje"], size="2", weight="medium"),
            rx.text(a["creado_en"], size="1", color="gray"),
            spacing="1",
            flex="1",
        ),
        rx.cond(
            a["leida"] == False,
            rx.button(
                rx.icon("check", size=14),
                "Marcar leída",
                variant="ghost",
                size="1",
                on_click=lambda: DashboardState.marcar_alerta_leida(a["id"]),
            ),
            rx.badge("Leída", color_scheme="gray", size="1"),
        ),
        spacing="3",
        width="100%",
        padding="0.75em",
        border_bottom="1px solid var(--gray-4)",
        align="center",
        background=rx.cond(
            a["leida"] == False,
            rx.color_mode_cond(light="var(--orange-2)", dark="var(--gray-3)"),
            "transparent",
        ),
        border_radius="4px",
    )


def alertas() -> rx.Component:
    return base_layout(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.heading("Alertas", size="7", weight="bold"),
                    rx.text(
                        "Alertas de bajo stock y productos próximos a vencer",
                        size="2",
                        color="gray",
                    ),
                    spacing="1",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.button(
                        rx.icon("scan-search", size=16),
                        "Detectar alertas",
                        variant="outline",
                        on_click=DashboardState.ejecutar_deteccion,
                    ),
                    rx.cond(
                        DashboardState.total_alertas_no_leidas > 0,
                        rx.button(
                            rx.icon("check-check", size=16),
                            "Marcar todas leídas",
                            variant="soft",
                            on_click=DashboardState.marcar_todas_leidas,
                        ),
                        rx.box(),
                    ),
                    spacing="2",
                ),
                width="100%",
                align="start",
            ),
            rx.hstack(
                rx.badge(
                    DashboardState.total_alertas_no_leidas.to_string() + " no leídas",
                    color_scheme=rx.cond(
                        DashboardState.total_alertas_no_leidas > 0,
                        "orange",
                        "green",
                    ),
                    size="2",
                ),
                spacing="2",
            ),
            rx.cond(
                DashboardState.error_message != "",
                rx.callout(
                    DashboardState.error_message,
                    icon="circle-alert",
                    color_scheme="red",
                    size="1",
                ),
            ),
            rx.cond(
                DashboardState.alertas_recientes.length() > 0,
                rx.box(
                    rx.foreach(DashboardState.alertas_recientes, _alerta_row),
                    width="100%",
                    border="1px solid var(--gray-4)",
                    border_radius="8px",
                    overflow="hidden",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("bell-off", size=40, color="gray"),
                        rx.text("Sin alertas pendientes", size="4", color="gray"),
                        rx.text(
                            "Las alertas de bajo stock y caducidad aparecerán aquí.",
                            size="2",
                            color="gray",
                        ),
                        spacing="2",
                        align="center",
                    ),
                    padding="4em",
                    width="100%",
                ),
            ),
            spacing="5",
            width="100%",
        ),
    )
