"""
tabla_generica.py — Tabla reutilizable con paginación.

Capa: Components / Presentation

Descripción:
    Componente de tabla genérica que acepta columnas dinámicas y datos del State.
    Incluye estado vacío, paginación con controles anterior/siguiente y
    soporte para render personalizado de celdas.

Uso:
    from dev.components.tabla_generica import tabla_generica

    COLUMNS = [
        {"key": "nombre", "label": "Producto", "width": "30%"},
        {"key": "stock", "label": "Stock"},
    ]

    tabla_generica(
        columns=COLUMNS,
        data=MiState.items,
        total_items=MiState.total,
        pagina_actual=MiState.pagina,
        on_pagina_siguiente=MiState.pagina_siguiente,
        on_pagina_anterior=MiState.pagina_anterior,
    )

Columnas con render personalizado:
    {"key": "stock", "label": "Stock", "render": lambda row: rx.badge(row.get("stock", "0"))}
"""

import reflex as rx


class TablaState(rx.State):
    pagina_actual: int = 1
    filas_por_pagina: int = 10

    def set_pagina(self, pagina: int):
        self.pagina_actual = pagina

    def pagina_siguiente(self):
        total = self.get_total_paginas()
        if self.pagina_actual < total:
            self.pagina_actual += 1

    def pagina_anterior(self):
        if self.pagina_actual > 1:
            self.pagina_actual -= 1


def tabla_generica(
    columns: list[dict],
    data: rx.Var,
    total_items: rx.Var = rx.Var.create(0),
    pagina_actual: rx.Var = rx.Var.create(1),
    filas_por_pagina: rx.Var = rx.Var.create(10),
    on_pagina_siguiente: rx.EventHandler = None,
    on_pagina_anterior: rx.EventHandler = None,
    on_row_click: rx.EventHandler = None,
    empty_message: str = "No hay datos disponibles",
) -> rx.Component:
    return rx.box(
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    *[
                        rx.table.column_header_cell(
                            col["label"],
                            width=col.get("width", "auto"),
                        )
                        for col in columns
                    ]
                )
            ),
            rx.table.body(
                rx.cond(
                    data.length() > 0,
                    rx.foreach(
                        data,
                        lambda row: rx.table.row(
                            *[
                                rx.table.cell(
                                    col.get(
                                        "render",
                                        lambda r: rx.text(r.get(col["key"], "")),
                                    )(row)
                                    if "render" in col
                                    else rx.text(row.get(col["key"], ""), size="2"),
                                    width=col.get("width", "auto"),
                                )
                                for col in columns
                            ],
                            cursor=rx.cond(
                                on_row_click is not None,
                                "pointer",
                                "default",
                            ),
                        ),
                    ),
                    rx.table.row(
                        rx.table.cell(
                            rx.text(
                                empty_message,
                                color="gray",
                                text_align="center",
                                padding_y="2em",
                            ),
                            col_span=len(columns),
                        )
                    ),
                ),
            ),
            width="100%",
        ),
        rx.hstack(
            rx.text(
                f"Mostrando {filas_por_pagina} de {total_items} resultados",
                size="2",
                color="gray",
            ),
            rx.spacer(),
            rx.hstack(
                rx.button(
                    rx.icon("chevron-left", size=16),
                    variant="outline",
                    size="1",
                    on_click=on_pagina_anterior,
                    disabled=rx.cond(pagina_actual <= 1, True, False),
                ),
                rx.text(
                    rx.Var.create("Página ") + pagina_actual.to_string(),
                    size="2",
                    weight="medium",
                ),
                rx.button(
                    rx.icon("chevron-right", size=16),
                    variant="outline",
                    size="1",
                    on_click=on_pagina_siguiente,
                    disabled=rx.cond(
                        pagina_actual * filas_por_pagina >= total_items,
                        True,
                        False,
                    ),
                ),
                spacing="2",
                align="center",
            ),
            width="100%",
            padding_top="0.75em",
            align="center",
        ),
        width="100%",
    )
