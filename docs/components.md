# Arquitectura de la Capa de Components

## Visión General

Los componentes son funciones puras que retornan `rx.Component`. No contienen lógica de negocio ni acceso directo a la BD. Reciben datos y event handlers como parámetros desde las páginas o el layout.

```
[Page/UI] → [State (Reflex)] → [Service] → [Repository] → [PostgreSQL]
     ↑              ↑
     └── Components ┘  (leen vars, disparan eventos)
```

| Capa | Responsabilidad | Qué hace | Qué NO hace |
|------|----------------|----------|-------------|
| **Components** | Presentación reutilizable | Renderiza UI con datos del State | Lógica de negocio, acceso a BD |
| **Pages** | Composición de componentes | Arma la vista usando componentes | Define lógica (va en State) |
| **States** | Estado reactivo | Maneja vars y event handlers | Renderiza UI directamente |

### Principios

1. **Sin estado**: Los componentes son funciones puras, no clases.
2. **Datos por parámetro**: Reciben `rx.Var` y `rx.EventHandler` como parámetros, no los crean.
3. **Sin lógica**: No validan, no calculan, no acceden a la BD.
4. **Reutilizables**: Un componente sirve para cualquier página que necesite esa UI.
5. **Sin dependencias circulares**: Components importa States, nunca Pages.

---

## Estructura de Archivos

```
dev/components/
├── __init__.py                # Re-exports de todos los componentes
├── sidebar.py                 # Navegación lateral
├── header.py                  # Barra superior (tema + usuario + logout)
├── layout.py                  # Template base (sidebar + header + contenido)
├── tabla_generica.py          # Tabla reutilizable con paginación
├── modal_confirmacion.py      # Diálogos de confirmación
├── alerta_card.py             # Cards de alerta (stock bajo, caducidad)
├── stat_card.py               # Cards KPI para dashboard
└── form_producto.py           # Formulario de producto
```

---

## Componentes de Layout

### `base_layout(*children) → rx.Component`

Template principal que envuelve todas las páginas. Detecta si el usuario está autenticado y muestra el layout correspondiente:

- **Autenticado**: Sidebar (250px) + Header + Contenido scrolleable.
- **Invitado**: Contenido sin decoración (para login, recovery).

```
┌──────────┬──────────────────────────────────┐
│          │  header                          │
│ sidebar  │  (dark/light toggle + user info) │
│          ├──────────────────────────────────┤
│  (nav    │                                  │
│  links)  │  *children (contenido página)    │
│          │                                  │
│  user    │                                  │
│  info    │                                  │
└──────────┴──────────────────────────────────┘
```

**Uso:**
```python
from dev.components.layout import base_layout

def mi_pagina() -> rx.Component:
    return base_layout(
        rx.heading("Mi página"),
        rx.text("Contenido aquí"),
    )
```

**Dependencias:** `AuthState` (is_authenticated), `sidebar()`, `header()`.

---

### `sidebar() → rx.Component`

Barra de navegación lateral con:
- Logo + nombre de la panadería.
- 9 enlaces de navegación (definidos en `NAV_ITEMS`).
- Email del usuario + botón de logout.

**Ancho fijo:** 250px, sticky, no scrollea con el contenido.

**Para agregar una nueva página**, editar `NAV_ITEMS`:
```python
NAV_ITEMS = [
    {"label": "Dashboard", "href": "/", "icon": "layout-dashboard"},
    {"label": "Nueva página", "href": "/nueva", "icon": "plus"},  # ← agregar aquí
]
```

**Iconos:** Nombres de Lucide (https://lucide.dev/icons/).

---

### `header() → rx.Component`

Barra superior con:
- Toggle dark/light mode (`rx.color_mode.button`).
- Email del usuario autenticado.
- Botón "Cerrar sesión".

**Dependencias:** `AuthState` (user_email, logout).

---

## Componentes Funcionales

### `tabla_generica(columns, data, ...) → rx.Component`

Tabla reutilizable con paginación y estado vacío.

**Parámetros:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `columns` | `list[dict]` | Definición de columnas |
| `data` | `rx.Var` | Lista de dicts con los datos (viene del State) |
| `total_items` | `rx.Var` | Total de registros para paginación |
| `pagina_actual` | `rx.Var` | Página actual del State |
| `filas_por_pagina` | `rx.Var` | Filas por página (default: 10) |
| `on_pagina_siguiente` | `EventHandler` | Event handler para avanzar página |
| `on_pagina_anterior` | `EventHandler` | Event handler para retroceder página |
| `on_row_click` | `EventHandler` | Click en una fila (opcional) |
| `empty_message` | `str` | Mensaje cuando no hay datos |

**Definición de columnas:**
```python
COLUMNS = [
    {"key": "nombre", "label": "Producto", "width": "30%"},
    {"key": "stock", "label": "Stock"},
    {
        "key": "estado",
        "label": "Estado",
        "render": lambda row: rx.badge(
            row.get("estado", ""),
            color_scheme=rx.cond(row.get("activo", True), "green", "red"),
        ),
    },
]
```

- `key`: nombre del campo en el dict de datos.
- `label`: texto del header de la columna.
- `width` (opcional): ancho CSS de la columna.
- `render` (opcional): función que recibe `row` (rx.Var dict) y retorna un componente.

---

### `stat_card(label, value, icon_name, color_scheme, subtitle) → rx.Component`

Tarjeta KPI con icono, valor grande y subtítulo opcional.

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `label` | `str` | — | Texto descriptivo (ej: "Productos") |
| `value` | `rx.Var` | — | Valor numérico a mostrar |
| `icon_name` | `str` | `"activity"` | Icono Lucide |
| `color_scheme` | `str` | `"blue"` | Color de fondo del icono y valor |
| `subtitle` | `rx.Var` | `None` | Texto secundario bajo el valor |

**Ejemplo:**
```python
stat_card("Stock bajo", rx.Var.create(8), "alert-triangle", "orange",
          subtitle=rx.Var.create("Requiere atención"))
```

### `stat_card_simple(label, value, color_scheme) → rx.Component`

Variante minimalista: solo label + valor grande centrado.

---

### `alerta_card(titulo, mensaje, tipo, icon_name, ...) → rx.Component`

Card de alerta con borde lateral de color y variantes predefinidas.

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `titulo` | `str` | — | Título de la alerta |
| `mensaje` | `rx.Var` | — | Texto descriptivo |
| `tipo` | `str` | `"warning"` | Determina el color |
| `icon_name` | `str` | `"triangle-alert"` | Icono Lucide |
| `on_click` | `EventHandler` | `None` | Click en la card |
| `on_dismiss` | `EventHandler` | `None` | Botón X para descartar |

**Tipos disponibles:**

| Tipo | Color | Uso |
|------|-------|-----|
| `"warning"` | orange | Stock bajo, atención requerida |
| `"danger"` | red | Error crítico, vencido |
| `"info"` | blue | Información general |
| `"success"` | green | Operación exitosa |

### `alerta_stock_bajo(producto_nombre, stock_actual, stock_minimo) → rx.Component`

Card preconfigurada para alertas de stock bajo. Muestra nombre del producto, stock actual y stock mínimo con borde naranja.

### `alerta_caducidad(producto_nombre, fecha_vencimiento) → rx.Component`

Card preconfigurada para productos próximos a vencer. Muestra nombre y fecha con borde rojo.

---

### `modal_confirmacion(trigger, titulo, descripcion, ...) → rx.Component`

Diálogo modal de confirmación usando `rx.alert_dialog`.

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `trigger` | `rx.Component` | — | Componente que abre el modal |
| `titulo` | `str` | `"Confirmar acción"` | Título del diálogo |
| `descripcion` | `str` | `"¿Estás seguro..."` | Texto descriptivo |
| `texto_confirmar` | `str` | `"Confirmar"` | Texto del botón de acción |
| `texto_cancelar` | `str` | `"Cancelar"` | Texto del botón cancelar |
| `on_confirm` | `EventHandler` | `None` | Event handler al confirmar |
| `color_scheme` | `str` | `"red"` | Color del botón confirmar |

**Ejemplo:**
```python
modal_confirmacion(
    trigger=rx.button("Eliminar", color_scheme="red"),
    titulo="Eliminar producto",
    descripcion="¿Eliminar este producto? No se puede deshacer.",
    on_confirm=ProductoState.eliminar,
)
```

### `modal_desactivar(trigger, on_confirm, nombre_recurso) → rx.Component`

Variante preconfigurada para soft-delete. Texto: "¿Desactivar {nombre_recurso}?". Botón naranja.

---

### `form_producto(...) → rx.Component`

Formulario completo para crear/editar productos. Envuelve campos en `rx.form.root`.

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `nombre_value` | `rx.Var` | Valor del campo nombre |
| `descripcion_value` | `rx.Var` | Valor del campo descripción |
| `categoria_id_value` | `rx.Var` | ID de categoría seleccionada |
| `unidad_medida_id_value` | `rx.Var` | ID de unidad de medida seleccionada |
| `stock_minimo_value` | `rx.Var` | Valor del stock mínimo |
| `ubicacion_value` | `rx.Var` | Valor del campo ubicación |
| `categorias` | `rx.Var` | Lista de dicts `[{id, nombre}]` para el select |
| `unidades_medida` | `rx.Var` | Lista de dicts `[{id, nombre}]` para el select |
| `on_nombre_change` | `EventHandler` | Handler para cambio de nombre |
| `on_descripcion_change` | `EventHandler` | Handler para cambio de descripción |
| `on_categoria_change` | `EventHandler` | Handler para cambio de categoría |
| `on_unidad_change` | `EventHandler` | Handler para cambio de unidad |
| `on_stock_minimo_change` | `EventHandler` | Handler para cambio de stock mínimo |
| `on_ubicacion_change` | `EventHandler` | Handler para cambio de ubicación |
| `on_submit` | `EventHandler` | Handler al enviar formulario |
| `submit_label` | `str` | Texto del botón submit (default: "Guardar") |
| `loading` | `rx.Var` | Estado loading del botón submit |

**Ejemplo:**
```python
form_producto(
    nombre_value=ProductoState.form_nombre,
    categorias=ProductoState.categorias,
    unidades_medida=ProductoState.unidades,
    on_nombre_change=ProductoState.set_nombre,
    on_submit=ProductoState.guardar_producto,
    submit_label="Crear producto",
    loading=ProductoState.is_saving,
)
```

---

## Página de Demo

Existe una página de demo en `/demo-components` (solo desarrollo) que muestra todos los componentes con datos de prueba. Es útil para:

- Verificar diseño visual antes de integrar en páginas reales.
- Probar dark/light mode en todos los componentes.
- Validar responsividad.

**Archivo:** `dev/pages/demo_components.py`
**Ruta:** `/demo-components`
**State:** `DemoState` (datos hardcodeados, sin BD)

---

## Convenciones para agregar un nuevo componente

1. Crear el archivo en `dev/components/`.
2. Agregar docstring del módulo (descripción, uso, dependencias).
3. El componente es una **función pura** que retorna `rx.Component`.
4. Datos variables van como parámetros `rx.Var`.
5. Eventos van como parámetros `rx.EventHandler`.
6. Agregar el import en `dev/components/__init__.py`.
7. Documentar en este archivo (`docs/components.md`).

### Template

```python
\"\"\"
mi_componente.py — Descripción breve.

Capa: Components / Presentation

Descripción:
    Qué hace el componente y cuándo usarlo.

Uso:
    from dev.components.mi_componente import mi_componente

    mi_componente(
        dato=MiState.var,
        on_accion=MiState.handler,
    )

Dependencias:
    - Listar states o componentes que importa.
\"\"\"

import reflex as rx


def mi_componente(
    dato: rx.Var = rx.Var.create(""),
    on_accion: rx.EventHandler = None,
) -> rx.Component:
    return rx.card(
        rx.text(dato),
        rx.button("Acción", on_click=on_accion),
    )
```

---

## Regla de imports (evitar dependencias circulares)

```
pages → components → states → models
pages → components → states (ok)
components → states (ok)
states → models (ok)
states ↛ pages (circular — prohibido)
states ↛ components (circular — prohibido)
models ↛ nada (no importa de otras capas)
```
