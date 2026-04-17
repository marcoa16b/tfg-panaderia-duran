import reflex as rx

from ..states.reporte_state import ReporteState
from ..components.layout import base_layout
from ..components.stat_card import stat_card_simple


def _existencia_row(e: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(e["nombre"], weight="medium", size="2")),
        rx.table.cell(
            rx.badge(
                e["stock_actual"],
                color_scheme=rx.cond(e["bajo_stock"] == True, "red", "green"),
            )
        ),
        rx.table.cell(rx.text(e["stock_minimo"], size="2")),
        rx.table.cell(rx.text(e.get("ubicacion", ""), size="2", color="gray")),
    )


def _perdida_row(p: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(p["fecha"], size="2")),
        rx.table.cell(rx.text(p["producto"], weight="medium", size="2")),
        rx.table.cell(rx.badge(p["cantidad"], color_scheme="red")),
        rx.table.cell(rx.text(p["motivo"], size="2")),
        rx.table.cell(rx.text(p["tipo"], size="2", color="gray")),
        rx.table.cell(rx.text(p["valor_perdida"], size="2")),
    )


def _consumo_row(c: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(c["nombre"], weight="medium", size="2")),
        rx.table.cell(rx.badge(c["total_consumido"], color_scheme="purple")),
        rx.table.cell(rx.text(c["anio"], size="2")),
    )


def reportes() -> rx.Component:
    return base_layout(
        rx.vstack(
            rx.hstack(
                rx.heading("Reportes", size="7", weight="bold"),
                rx.spacer(),
                rx.button(
                    rx.icon("download", size=16),
                    "Exportar CSV",
                    variant="outline",
                    on_click=ReporteState.exportar_csv,
                ),
                width="100%",
                align="center",
            ),
            rx.tabs.root(
                rx.tabs.list(
                    rx.tabs.trigger("Existencias", value="existencias"),
                    rx.tabs.trigger("Pérdidas", value="perdidas"),
                    rx.tabs.trigger("Consumo anual", value="consumo"),
                ),
                rx.tabs.content(
                    rx.vstack(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Producto"),
                                    rx.table.column_header_cell("Stock actual"),
                                    rx.table.column_header_cell("Stock mín."),
                                    rx.table.column_header_cell("Ubicación"),
                                )
                            ),
                            rx.table.body(
                                rx.cond(
                                    ReporteState.existencias.length() > 0,
                                    rx.foreach(
                                        ReporteState.existencias, _existencia_row
                                    ),
                                    rx.table.row(
                                        rx.table.cell(
                                            rx.text(
                                                "No hay datos de existencias",
                                                color="gray",
                                                text_align="center",
                                                padding_y="2em",
                                            ),
                                            col_span=4,
                                        )
                                    ),
                                ),
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
                                rx.text("Desde", size="2", weight="medium"),
                                rx.input(
                                    type="date",
                                    value=ReporteState.filtro_fecha_inicio,
                                    on_change=ReporteState.set_filtro_fecha_inicio,
                                    size="2",
                                ),
                                spacing="1",
                            ),
                            rx.vstack(
                                rx.text("Hasta", size="2", weight="medium"),
                                rx.input(
                                    type="date",
                                    value=ReporteState.filtro_fecha_fin,
                                    on_change=ReporteState.set_filtro_fecha_fin,
                                    size="2",
                                ),
                                spacing="1",
                            ),
                            rx.button(
                                rx.icon("search", size=14),
                                "Filtrar",
                                variant="soft",
                                on_click=ReporteState.filtrar,
                            ),
                            spacing="3",
                            align="end",
                        ),
                        rx.hstack(
                            stat_card_simple(
                                "Total pérdidas",
                                ReporteState.total_perdida,
                                "red",
                            ),
                            stat_card_simple(
                                "Registros",
                                ReporteState.cantidad_perdidas,
                                "orange",
                            ),
                            columns="2",
                            spacing="4",
                            width="100%",
                        ),
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Fecha"),
                                    rx.table.column_header_cell("Producto"),
                                    rx.table.column_header_cell("Cantidad"),
                                    rx.table.column_header_cell("Motivo"),
                                    rx.table.column_header_cell("Tipo"),
                                    rx.table.column_header_cell("Valor pérdida"),
                                )
                            ),
                            rx.table.body(
                                rx.cond(
                                    ReporteState.perdidas.length() > 0,
                                    rx.foreach(ReporteState.perdidas, _perdida_row),
                                    rx.table.row(
                                        rx.table.cell(
                                            rx.text(
                                                "No hay pérdidas en el periodo seleccionado",
                                                color="gray",
                                                text_align="center",
                                                padding_y="2em",
                                            ),
                                            col_span=6,
                                        )
                                    ),
                                ),
                            ),
                            width="100%",
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    value="perdidas",
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
                                on_click=ReporteState.filtrar,
                            ),
                            spacing="3",
                            align="end",
                        ),
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
                                        ReporteState.consumo_anual, _consumo_row
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
        on_load=ReporteState.on_load,
    )
