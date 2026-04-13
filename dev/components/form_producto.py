"""
form_producto.py — Formulario reutilizable para crear/editar productos.

Capa: Components / Presentation

Descripción:
    Formulario completo para el CRUD de productos. Envuelve todos los campos
    en un rx.form.root para compatibilidad con Radix UI Form.

Campos:
    - Nombre (requerido)
    - Descripción (opcional)
    - Categoría (select dinámico desde State)
    - Unidad de medida (select dinámico desde State)
    - Stock mínimo (numérico)
    - Ubicación (texto libre)

Uso:
    from dev.components.form_producto import form_producto

    form_producto(
        nombre_value=MiState.form_nombre,
        categorias=MiState.categorias,
        unidades_medida=MiState.unidades,
        on_nombre_change=MiState.set_nombre,
        on_submit=MiState.guardar,
    )

Notas:
    - Todos los parámetros de value son rx.Var (referencias al State).
    - Los selects usan rx.foreach para renderizar items dinámicamente.
    - El botón submit tiene soporte para estado loading.
"""

import reflex as rx


def form_producto(
    nombre_value: rx.Var = rx.Var.create(""),
    descripcion_value: rx.Var = rx.Var.create(""),
    categoria_id_value: rx.Var = rx.Var.create(""),
    unidad_medida_id_value: rx.Var = rx.Var.create(""),
    stock_minimo_value: rx.Var = rx.Var.create("0"),
    ubicacion_value: rx.Var = rx.Var.create(""),
    categorias: rx.Var = rx.Var.create([]),
    unidades_medida: rx.Var = rx.Var.create([]),
    on_nombre_change: rx.EventHandler = None,
    on_descripcion_change: rx.EventHandler = None,
    on_categoria_change: rx.EventHandler = None,
    on_unidad_change: rx.EventHandler = None,
    on_stock_minimo_change: rx.EventHandler = None,
    on_ubicacion_change: rx.EventHandler = None,
    on_submit: rx.EventHandler = None,
    submit_label: str = "Guardar",
    loading: rx.Var = rx.Var.create(False),
) -> rx.Component:
    return rx.form.root(
        rx.vstack(
            rx.vstack(
                rx.text("Nombre *", size="2", weight="medium"),
                rx.input(
                    placeholder="Ej: Harina de trigo",
                    value=nombre_value,
                    on_change=on_nombre_change,
                    size="2",
                ),
                spacing="2",
                width="100%",
            ),
            rx.vstack(
                rx.text("Descripción", size="2", weight="medium"),
                rx.text_area(
                    placeholder="Descripción del producto (opcional)",
                    value=descripcion_value,
                    on_change=on_descripcion_change,
                    size="2",
                ),
                spacing="2",
                width="100%",
            ),
            rx.hstack(
                rx.vstack(
                    rx.text("Categoría *", size="2", weight="medium"),
                    rx.select.root(
                        rx.select.trigger(
                            placeholder="Seleccionar categoría",
                        ),
                        rx.select.content(
                            rx.foreach(
                                categorias,
                                lambda c: rx.select.item(
                                    c["nombre"],
                                    value=c["id"].to_string(),
                                ),
                            ),
                        ),
                        value=categoria_id_value,
                        on_change=on_categoria_change,
                    ),
                    spacing="2",
                    width="100%",
                ),
                rx.vstack(
                    rx.text("Unidad de medida *", size="2", weight="medium"),
                    rx.select.root(
                        rx.select.trigger(
                            placeholder="Seleccionar unidad",
                        ),
                        rx.select.content(
                            rx.foreach(
                                unidades_medida,
                                lambda u: rx.select.item(
                                    u["nombre"],
                                    value=u["id"].to_string(),
                                ),
                            ),
                        ),
                        value=unidad_medida_id_value,
                        on_change=on_unidad_change,
                    ),
                    spacing="2",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            rx.hstack(
                rx.vstack(
                    rx.text("Stock mínimo", size="2", weight="medium"),
                    rx.input(
                        type="number",
                        value=stock_minimo_value,
                        on_change=on_stock_minimo_change,
                        size="2",
                    ),
                    spacing="2",
                    width="100%",
                ),
                rx.vstack(
                    rx.text("Ubicación", size="2", weight="medium"),
                    rx.input(
                        placeholder="Ej: Estante A-3",
                        value=ubicacion_value,
                        on_change=on_ubicacion_change,
                        size="2",
                    ),
                    spacing="2",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            rx.button(
                submit_label,
                type="submit",
                size="3",
                width="100%",
                loading=loading,
            ),
            spacing="4",
            width="100%",
        ),
        on_submit=on_submit,
    )
