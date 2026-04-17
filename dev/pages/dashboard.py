import reflex as rx

from ..states.auth_state import AuthState
from ..states.dashboard_state import DashboardState
from ..components.layout import base_layout
from ..components.stat_card import stat_card
from ..components.alerta_card import alerta_stock_bajo, alerta_caducidad


def _quick_access_card(label: str, href: str, icon: str, color: str) -> rx.Component:
    return rx.link(
        rx.card(
            rx.hstack(
                rx.box(
                    rx.icon(icon, size=20),
                    padding="0.6em",
                    border_radius="8px",
                    background=f"var(--{color}-3)",
                    color=f"var(--{color}-11)",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.text(label, size="3", weight="medium"),
                rx.spacer(),
                rx.icon("chevron-right", size=16, color="gray"),
                spacing="3",
                align="center",
                width="100%",
            ),
            width="100%",
            padding="0.75em 1em",
            _hover={"border_color": f"var(--{color}-8)"},
        ),
        href=href,
        underline="none",
        width="100%",
        color=rx.color_mode_cond(light="var(--gray-12)", dark="var(--gray-12)"),
    )


def index() -> rx.Component:
    return rx.box(
        base_layout(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.heading("Dashboard", size="7", weight="bold"),
                        rx.text(
                            "Bienvenido, ",
                            rx.text(AuthState.user_nombre, weight="bold"),
                            size="3",
                            color="gray",
                        ),
                        spacing="1",
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.icon("refresh-cw", size=16),
                        "Actualizar",
                        variant="soft",
                        on_click=DashboardState.load_dashboard,
                        loading=DashboardState.is_loading,
                    ),
                    width="100%",
                    align="center",
                ),
                rx.grid(
                    stat_card(
                        "Productos",
                        DashboardState.total_productos,
                        "package",
                        "blue",
                    ),
                    stat_card(
                        "Bajo stock",
                        DashboardState.productos_bajo_stock,
                        "trending-down",
                        "orange",
                    ),
                    stat_card(
                        "Entradas (mes)",
                        DashboardState.entradas_mes,
                        "log-in",
                        "green",
                    ),
                    stat_card(
                        "Salidas (mes)",
                        DashboardState.salidas_mes,
                        "log-out",
                        "red",
                    ),
                    stat_card(
                        "Por vencer",
                        DashboardState.lotes_por_vencer,
                        "calendar-clock",
                        "purple",
                    ),
                    columns="5",
                    spacing="4",
                    width="100%",
                ),
                rx.divider(),
                rx.grid(
                    rx.vstack(
                        rx.hstack(
                            rx.heading("Alertas recientes", size="5", weight="bold"),
                            rx.spacer(),
                            rx.cond(
                                DashboardState.total_alertas_no_leidas > 0,
                                rx.badge(
                                    DashboardState.total_alertas_no_leidas,
                                    color_scheme="red",
                                ),
                                rx.badge("0", color_scheme="green"),
                            ),
                            width="100%",
                            align="center",
                        ),
                        rx.cond(
                            DashboardState.total_alertas_no_leidas > 0,
                            rx.button(
                                "Marcar todas como leídas",
                                variant="ghost",
                                size="1",
                                on_click=DashboardState.marcar_todas_leidas,
                            ),
                            rx.text("Sin alertas pendientes", size="2", color="gray"),
                        ),
                        rx.foreach(
                            DashboardState.alertas_recientes,
                            lambda a: rx.hstack(
                                rx.icon(
                                    "bell",
                                    size=16,
                                    color=rx.cond(
                                        a["leida"], "gray", "var(--orange-9)"
                                    ),
                                ),
                                rx.text(a["mensaje"], size="2", flex="1"),
                                rx.text(a["creado_en"], size="1", color="gray"),
                                rx.cond(
                                    a["leida"] == False,
                                    rx.button(
                                        rx.icon("check", size=14),
                                        variant="ghost",
                                        size="1",
                                        on_click=lambda: (
                                            DashboardState.marcar_alerta_leida(a["id"])
                                        ),
                                    ),
                                    rx.box(),
                                ),
                                spacing="3",
                                width="100%",
                                padding="0.5em",
                                border_bottom="1px solid var(--gray-4)",
                                align="center",
                            ),
                        ),
                        rx.link(
                            rx.hstack(
                                rx.text("Ver todas las alertas", size="2"),
                                rx.icon("arrow-right", size=14),
                                spacing="1",
                                align="center",
                            ),
                            href="/alertas",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.heading("Accesos rápidos", size="5", weight="bold"),
                        _quick_access_card(
                            "Productos", "/productos", "package", "blue"
                        ),
                        _quick_access_card(
                            "Registrar entrada", "/entradas", "log-in", "green"
                        ),
                        _quick_access_card(
                            "Registrar salida", "/salidas", "log-out", "red"
                        ),
                        _quick_access_card("Recetas", "/recetas", "chef-hat", "purple"),
                        _quick_access_card(
                            "Producción diaria",
                            "/produccion-diaria",
                            "factory",
                            "orange",
                        ),
                        _quick_access_card(
                            "Reportes", "/reportes", "file-text", "gray"
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    columns="2",
                    spacing="6",
                    width="100%",
                ),
                spacing="5",
                width="100%",
            ),
        ),
        on_load=DashboardState.load_dashboard,
    )
