import reflex as rx

from ..states.reporte_state import ReporteState
from ..components.layout import base_layout
from ..components.stat_card import stat_card_simple


def _existencia_row(e: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(e["nombre"], weight="medium", size="2")),
        rx.table.cell(
            rx.badge(
                rx.text(e["stock_actual"], " ", e["unidad_abrev"]),
                color_scheme=rx.cond(e["bajo_stock"] == True, "red", "green"),
            )
        ),
        rx.table.cell(rx.text(e["stock_minimo"], " ", e["unidad_abrev"], size="2")),
        rx.table.cell(rx.text(e.get("ubicacion", ""), size="2", color="gray")),
        rx.table.cell(
            rx.cond(
                e["bajo_stock"] == True,
                rx.badge("Bajo stock", color_scheme="red", size="1"),
                rx.badge("OK", color_scheme="green", size="1"),
            )
        ),
    )


def estadisticas() -> rx.Component:
    return base_layout(
        rx.vstack(
            rx.hstack(
                rx.heading("Estadísticas", size="7", weight="bold"),
                rx.spacer(),
                rx.button(
                    rx.icon("refresh-cw", size=16),
                    "Actualizar",
                    variant="soft",
                    on_click=ReporteState.load_reporte,
                    loading=ReporteState.is_loading,
                ),
                width="100%",
                align="center",
            ),
            rx.tabs.root(
                rx.tabs.list(
                    rx.tabs.trigger("Existencias", value="existencias"),
                    rx.tabs.trigger("Consumo anual", value="consumo"),
                ),
                rx.tabs.content(
                    rx.vstack(
                        rx.grid(
                            stat_card_simple(
                                "Total productos",
                                ReporteState.existencias.length(),
                                "blue",
                            ),
                            stat_card_simple(
                                "Bajo stock",
                                ReporteState.existencias_bajo_stock,
                                "red",
                            ),
                            columns="2",
                            spacing="4",
                            width="100%",
                        ),
                        rx.box(
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        rx.table.column_header_cell("Producto"),
                                        rx.table.column_header_cell("Stock actual"),
                                        rx.table.column_header_cell("Stock mín."),
                                        rx.table.column_header_cell("Ubicación"),
                                        rx.table.column_header_cell("Estado"),
                                    )
                                ),
                                rx.table.body(
                                    rx.cond(
                                        ReporteState.existencias.length() > 0,
                                        rx.foreach(
                                            ReporteState.existencias,
                                            _existencia_row,
                                        ),
                                        rx.table.row(
                                            rx.table.cell(
                                                rx.text(
                                                    "No hay datos de existencias",
                                                    color="gray",
                                                    text_align="center",
                                                    padding_y="2em",
                                                ),
                                                col_span=5,
                                            )
                                        ),
                                    ),
                                ),
                                width="100%",
                            ),
                            width="100%",
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    value="existencias",
                ),
                rx.tabs.content(
                    rx.vstack(
                        rx.hstack(
                            rx.vstack(
                                rx.text("Año", size="2", weight="medium"),
                                rx.input(
                                    type="number",
                                    value=ReporteState.filtro_anio,
                                    on_change=ReporteState.set_filtro_anio,
                                    size="2",
                                    width="100px",
                                ),
                                spacing="1",
                            ),
                            rx.button(
                                rx.icon("search", size=14),
                                "Consultar",
                                variant="soft",
                                on_click=lambda: [
                                    ReporteState.set_tab("consumo"),
                                    ReporteState.load_consumo_anual(),
                                ],
                            ),
                            spacing="3",
                            align="end",
                        ),
                        rx.box(
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        rx.table.column_header_cell("Producto"),
                                        rx.table.column_header_cell("Total consumido"),
                                        rx.table.column_header_cell("Año"),
                                    )
                                ),
                                rx.table.body(
                                    rx.cond(
                                        ReporteState.consumo_anual.length() > 0,
                                        rx.foreach(
                                            ReporteState.consumo_anual,
                                            lambda c: rx.table.row(
                                                rx.table.cell(
                                                    rx.text(
                                                        c["nombre"],
                                                        weight="medium",
                                                        size="2",
                                                    )
                                                ),
                                                rx.table.cell(
                                                    rx.badge(
                                                        c["total_consumido"],
                                                        color_scheme="purple",
                                                    )
                                                ),
                                                rx.table.cell(
                                                    rx.text(c["anio"], size="2")
                                                ),
                                            ),
                                        ),
                                        rx.table.row(
                                            rx.table.cell(
                                                rx.text(
                                                    "No hay datos de consumo para el año seleccionado",
                                                    color="gray",
                                                    text_align="center",
                                                    padding_y="2em",
                                                ),
                                                col_span=3,
                                            )
                                        ),
                                    ),
                                ),
                                width="100%",
                            ),
                            width="100%",
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    value="consumo",
                ),
                default_value="existencias",
                width="100%",
            ),
            spacing="5",
            width="100%",
        ),
    )
