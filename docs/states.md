# Arquitectura de la Capa de States

## Visión General

Los states son la capa de presentación (Application Layer) del sistema Reflex. Manejan el estado reactivo que se sincroniza con el frontend via WebSocket y delegan toda la lógica de negocio a los Services.

```
[Page/UI] → [State (Reflex)] → [Service] → [Repository] → [PostgreSQL]
```

| Capa | Responsabilidad | Qué hace | Qué NO hace |
|------|----------------|----------|-------------|
| **States** | Estado reactivo UI | Gestiona vars, formularios, diálogos | No contiene lógica de negocio |
| **Services** | Lógica de negocio | Valida, calcula, orquesta | No conoce la UI |

### Principios de la capa State

1. **Delegación total**: Toda la lógica de negocio se delega al Service correspondiente.
2. **Variables reactivas**: Reflex sincroniza automáticamente las vars con el frontend.
3. **Formularios aislados**: Las vars `form_*` almacenan datos del formulario sin mutar la tabla.
4. **Diálogos controlados**: Vars booleanas (`dialog_open`, `confirm_open`) controlan la visibilidad.
5. **Serialización**: Los campos `Decimal` se convierten a `str` para ser JSON-serializables.
6. **Manejo de errores**: Captura excepciones y muestra mensajes genéricos en `error_message`.

---

## Estructura de Archivos

```
dev/states/
├── __init__.py                  # (vacío)
├── auth_state.py                # Autenticación, login, logout, rutas protegidas
├── dashboard_state.py           # KPIs del dashboard y alertas recientes
├── producto_state.py            # CRUD de productos con paginación y filtros
├── receta_state.py              # CRUD de recetas con ingredientes dinámicos
├── produccion_state.py          # Registro de producción con verificación FIFO
├── entrada_salida_state.py      # Entradas (lotes) y salidas (detalles) de inventario
└── reporte_state.py             # Reportes: existencias, pérdidas, consumo anual
```

---

## States por Dominio

### AuthState — Autenticación y gestión de sesión

| Método | Qué hace | Returns |
|--------|----------|---------|
| `login()` | Autentica contra AuthService | `rx.redirect("/")` si éxito |
| `logout()` | Limpia estado y redirige | `rx.redirect("/login")` |
| `check_auth()` | Protección de rutas | `rx.redirect("/login")` si no autenticado |
| `send_recovery_email()` | Inicia recuperación de contraseña | `rx.toast.info` neutral |
| `clear_error()` | Limpia mensaje de error | — |

**Variables de estado:**
- `is_authenticated`, `user_id`, `user_email`, `user_nombre`, `token`: Datos de sesión.
- `email`, `password`: Campos del formulario de login.
- `error_message`, `is_loading`: Feedback UI.

**Flujo de autenticación:**
1. Usuario ingresa correo + contraseña → `login()`.
2. AuthService.authenticate() valida credenciales.
3. Si éxito: almacena datos + JWT en estado, redirige a dashboard.
4. Si falla: muestra mensaje genérico (no revela si el usuario existe).

**Protección de rutas:**
`check_auth()` se llama desde el layout. Si `is_authenticated` es False, redirige a `/login`.

---

### DashboardState — KPIs y alertas del dashboard

| Método | Qué hace | Returns |
|--------|----------|---------|
| `load_dashboard()` | Carga KPIs + alertas no leídas | Actualiza vars reactivas |
| `ejecutar_deteccion()` | Fuerza detección de alertas | Recarga dashboard |
| `marcar_alerta_leida(id)` | Marca una alerta como leída | Recarga dashboard |
| `marcar_todas_leidas()` | Marca todas las alertas pendientes | Recarga dashboard |

**KPIs:**
```python
total_productos        # Productos activos
productos_bajo_stock   # Productos con stock <= mínimo
entradas_mes           # Entradas en los últimos 30 días
salidas_mes            # Salidas en los últimos 30 días
lotes_por_vencer       # Lotes que vencen en 7 días
```

**Alertas:**
- `alertas_recientes`: Últimas 10 alertas no leídas (id, mensaje, producto_id, fecha).
- `total_alertas_no_leidas`: Entero para badge de notificaciones.

---

### ProductoState — Catálogo de productos con paginación

| Método | Qué hace | Returns |
|--------|----------|---------|
| `load_productos()` | Carga productos paginados con filtros | Actualiza tabla |
| `buscar_productos()` | Busca por nombre (resetea a pág. 1) | Recarga tabla |
| `filtrar_por_categoria(id)` | Filtra por categoría | Recarga tabla |
| `limpiar_filtros()` | Limpia todos los filtros | Recarga tabla |
| `pagina_siguiente()` / `pagina_anterior()` | Navegación de páginas | Recarga tabla |
| `abrir_crear()` / `abrir_editar(id)` | Abren diálogo de formulario | Actualiza form_* |
| `guardar_producto()` | Crea o actualiza producto | `rx.toast.success` |
| `confirmar_desactivar(id)` / `ejecutar_desactivar()` | Soft delete con confirmación | `rx.toast.success` |

**Paginación:**
- `PAGE_SIZE = 20` registros por página.
- `offset = (pagina_actual - 1) * PAGE_SIZE`.
- `total_paginas = ceil(total / PAGE_SIZE)`.

**Catálogos (cargados una vez):**
- `categorias`: Categorías de producto activas.
- `unidades_medida`: Unidades de medida activas.

**Convención de formularios:**
- `form_nombre`, `form_descripcion`, `form_categoria_id`, `form_unidad_medida_id`, `form_stock_minimo`, `form_ubicacion`.
- `modo_editar`: True = editar, False = crear.
- `editando_id`: PK del producto en edición.

---

### RecetaState — Recetas con ingredientes dinámicos

| Método | Qué hace | Returns |
|--------|----------|---------|
| `on_load()` | Carga productos y recetas | Actualiza catálogos + tabla |
| `load_recetas()` | Carga recetas con búsqueda opcional | Actualiza tabla |
| `buscar()` / `limpiar_busqueda()` | Control de búsqueda | Recarga tabla |
| `abrir_crear()` / `abrir_editar(id)` | Abren diálogo de formulario | Actualiza form_* |
| `agregar_ingrediente()` / `eliminar_ingrediente(i)` | Gestionan lista dinámica | Actualiza form_ingredientes |
| `set_ingrediente_producto(i, id)` / `set_ingrediente_cantidad(i, cant)` | Modifican ingrediente | Actualiza form_ingredientes |
| `guardar_receta()` | Crea o actualiza receta + ingredientes | `rx.toast.success` |
| `confirmar_desactivar(id)` / `ejecutar_desactivar()` | Soft delete con confirmación | `rx.toast.success` |
| `ver_detalle(id)` | Muestra ingredientes de una receta | Abre diálogo de detalle |
| `abrir_verificar_disponibilidad(id)` / `verificar_disponibilidad()` | Verifican insumos vs stock | Actualiza disponibilidad_resultado |

**Ingredientes dinámicos:**
```python
form_ingredientes = [
    {"producto_id": 5, "cantidad": "500"},
    {"producto_id": 3, "cantidad": "50"},
]
```

**Verificación de disponibilidad retorna:**
```python
disponibilidad_resultado = {
    "disponible": False,
    "detalle": [
        {"nombre": "Harina", "cantidad_necesaria": "5000", "stock_actual": "3000",
         "suficiente": False, "faltante": "2000"},
        ...
    ]
}
```

---

### ProduccionState — Producción diaria con FIFO

| Método | Qué hace | Returns |
|--------|----------|---------|
| `on_load()` | Inicializa fechas, recetas y producciones | Actualiza todo |
| `load_producciones()` | Carga producciones por rango de fechas | Actualiza tabla |
| `filtrar_periodo()` | Recarga con filtros de fecha | Recarga tabla |
| `abrir_crear()` | Abre diálogo de registro | Actualiza form_* |
| `on_receta_change(id)` | Cambia receta y recarga ingredientes | Actualiza ingredientes_receta |
| `verificar_disponibilidad()` | Verifica insumos antes de producir | Abre diálogo de verificación |
| `guardar_produccion()` | Registra producción + descuento FIFO | `rx.toast.success` |
| `ver_detalle(id)` | Muestra lotes consumidos (trazabilidad) | Abre diálogo de detalle |

**Flujo de producción:**
1. Seleccionar receta → carga ingredientes.
2. Ingresar cantidad → verificar_disponibilidad() muestra insumos necesarios vs disponibles.
3. Confirmar → guardar_produccion() ejecuta:
   - Verificación de insumos.
   - Asignación FIFO (lotes que vencen primero).
   - Descuento de stock de cada insumo.
   - Registro en ProduccionDetalle (trazabilidad).

**Detalle de producción (trazabilidad):**
```python
detalle_produccion = {
    "id": 15,
    "receta_nombre": "Pan de leche",
    "fecha": "2025-01-15",
    "cantidad_producida": "50",
    "detalles": [
        {"lote_id": 3, "cantidad": "15000"},  # Harina del lote 3
        {"lote_id": 5, "cantidad": "500"},     # Azúcar del lote 5
    ]
}
```

---

### EntradaSalidaState — Entradas y salidas de inventario

| Método | Qué hace | Returns |
|--------|----------|---------|
| `on_load()` | Carga catálogos, fechas, entradas y salidas | Actualiza todo |
| `set_tab(tab)` | Alterna entre entradas y salidas | Recarga lista |
| `load_entradas()` / `load_salidas()` | Cargan datos filtrados por fecha | Actualiza tabla |
| `filtrar_periodo()` | Recarga ambas listas | Recarga tablas |
| `abrir_crear_entrada()` / `guardar_entrada()` | Registro de entrada con lotes | `rx.toast.success` |
| `abrir_crear_salida()` / `guardar_salida()` | Registro de salida con detalles | `rx.toast.success` |
| `agregar_lote()` / `eliminar_lote(i)` / `set_lote_*` | Gestión dinámica de lotes | Actualiza form_entrada_lotes |
| `agregar_detalle_salida()` / `eliminar_detalle_salida(i)` / `set_detalle_*` | Gestión dinámica de detalles | Actualiza form_salida_detalles |
| `ver_detalle_entrada(id)` / `ver_detalle_salida(id)` | Visualización de operaciones | Abre diálogo |

**Formulario de entrada (lotes dinámicos):**
```python
form_entrada_lotes = [
    {"producto_id": 5, "cantidad": "50", "fecha_vencimiento": "2025-06-01", "codigo_lote": "L001"},
    {"producto_id": 3, "cantidad": "100", "fecha_vencimiento": "", "codigo_lote": ""},
]
```

**Formulario de salida (detalles dinámicos):**
```python
form_salida_detalles = [
    {"lote_id": 3, "cantidad": "20", "motivo": "Uso en producción"},
    {"lote_id": 5, "cantidad": "5", "motivo": "Dañado"},
]
```

**Catálogos:**
- `productos`, `proveedores`: Entidades activas.
- `tipos_entrada`: Tipos de la lista "entrada" (compra, donación, ajuste).
- `tipos_salida`: Tipos de la lista "salida" (consumo, dañado, vencido, ajuste).
- `lotes_disponibles`: Lotes activos con stock para salidas.

---

### ReporteState — Reportes y estadísticas

| Método | Qué hace | Returns |
|--------|----------|---------|
| `on_load()` | Inicializa fechas y carga reporte | Actualiza todo |
| `set_tab(tab)` | Cambia tipo de reporte | Recarga reporte |
| `load_reporte()` | Despacha al loader según tab | — |
| `load_existencias()` | Stock actual de todos los productos | Actualiza existencias |
| `load_perdidas()` | Productos dañados/vencidos con valor | Actualiza perdidas + resumen |
| `load_consumo_anual()` | Consumo por producto en un año | Actualiza consumo_anual |
| `filtrar()` | Recarga aplicando filtros de fecha | Recarga reporte |
| `exportar_csv()` | Exporta reporte activo a CSV | `rx.toast.success` |

**Tabs:**
- `"existencias"`: Stock actual, mínimo, indicador de bajo stock, ubicación.
- `"perdidas"`: Fecha, producto, lote, cantidad, motivo, tipo, valor económico.
- `"consumo"`: Producto, total consumido, año.

**Resumen de pérdidas:**
```python
total_perdida = "1250.50"      # Valor económico total
cantidad_perdidas = 8          # Número de registros
```

---

## Diagrama de dependencias entre States y Services

```
AuthState ────────────→ AuthService

DashboardState ───────→ ReporteService (KPIs)
                    ──→ AlertaService (alertas)

ProductoState ────────→ ProductoService (CRUD)

RecetaState ──────────→ RecetaService (CRUD + ingredientes + disponibilidad)

ProduccionState ──────→ ProduccionService (registro FIFO)
                    ──→ RecetaService (ingredientes + disponibilidad)

EntradaSalidaState ───→ InventarioService (entradas + salidas)
                    ──→ ReporteService (listados por periodo)

ReporteState ─────────→ ReporteService (existencias, pérdidas, consumo)
```

---

## Convenciones para agregar un nuevo State

1. Crear el archivo en `dev/states/`.
2. Heredar de `rx.State`.
3. Agregar docstring del módulo (arquitectura, flujo, relación con services, variables, uso).
4. Agregar docstring de clase (métodos principales, variables reactivas).
5. Agregar docstring en cada método (flujo, args, returns, excepciones).
6. Variables de formulario con prefijo `form_*`.
7. Variables de diálogo booleanas con sufijo `_open`.
8. Manejar errores con try/except y `error_message`.
9. Delegar toda la lógica de negocio al Service correspondiente.
10. Documentar en este archivo (`docs/states.md`).

### Template

```python
"""
nombre_state.py — Estado reactivo para [dominio].

Arquitectura
------------
Capa State (Application Layer) para [descripción]. [Qué hace].

Patrón de diseño: Reflex State
    - Variables reactivas sincronizadas al frontend.
    - [Patrones específicos del state].

Relación con otras capas
------------------------
    [Page] → NombreState → NombreService → [Repository] → [BD]

Variables de estado
-------------------
    [Grupo de variables con descripción].

Flujo de datos
--------------
1. [Paso 1].
2. [Paso 2].

Uso desde la capa UI:
    from dev.states.nombre_state import NombreState
    rx.foreach(NombreState.items, lambda i: rx.text(i["nombre"]))
"""

import reflex as rx
from dev.services.nombre_service import NombreService


class NombreState(rx.State):
    """
    Estado reactivo para [dominio].

    Métodos principales:
        - load_items: Carga items paginados.
        - guardar: Crea o actualiza un item.
    """

    items: list[dict] = []
    is_loading: bool = False
    error_message: str = ""

    def load_items(self):
        """
        Carga items con filtros activos.

        Flujo:
            1. [Paso 1].
            2. [Paso 2].
        """
        self.is_loading = True
        try:
            items = NombreService.get_all()
            self.items = [{"id": i.id, "nombre": i.nombre} for i in items]
        except Exception as e:
            self.error_message = "Error al cargar items."
        finally:
            self.is_loading = False
```
