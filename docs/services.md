# Arquitectura de la Capa de Services

## Visión General

Los servicios contienen la **lógica de negocio** del sistema. Son la capa intermedia entre los States (UI) y los Repositories (datos).

```
[Page/UI] → [State (Reflex)] → [Service] → [Repository] → [PostgreSQL]
```

| Capa | Responsabilidad | Qué hace | Qué NO hace |
|------|----------------|----------|-------------|
| **Services** | Lógica de negocio | Valida, calcula, orquesta | No conoce SQL directamente |
| **Repositories** | Acceso a datos | CRUD puro contra la BD | No valida reglas de negocio |

### Principios de la capa Service

1. **Validación antes de persistir**: Todo dato se valida antes de llegar al Repository.
2. **Orquestación**: Un servicio puede llamar a múltiples repositorios en una operación.
3. **Transacciones atómicas**: Operaciones complejas (entrada + lotes + stock) se hacen en una sola transacción.
4. **Excepciones de dominio**: Lanza `ValidationException`, `NotFoundException`, etc. con mensajes claros.
5. **Sin estado**: Todos los métodos son `@classmethod` — no hay instancias.

---

## Estructura de Archivos

```
dev/services/
├── __init__.py              # Re-exports de todos los servicios
├── auth_service.py          # Autenticación, registro, JWT
├── producto_service.py      # CRUD de productos + validaciones
├── inventario_service.py    # Entradas, salidas, cálculo de stock
├── receta_service.py        # Recetas, ingredientes, insumos
├── produccion_service.py    # Producción diaria, descuento FIFO
├── alerta_service.py        # Detección de bajo stock y vencimientos
└── reporte_service.py       # Reportes, estadísticas, dashboard
```

---

## Servicios por Dominio

### AuthService — Autenticación y gestión de usuarios

| Método | Qué hace | Excepciones |
|--------|----------|-------------|
| `authenticate(correo, password)` | Login → retorna usuario + JWT | None (retorna None si falla) |
| `register(nombre, correo, password, rol_id)` | Crear usuario con validaciones | `ValidationException`, `DuplicateException` |
| `change_password(usuario_id, current, new)` | Cambio de contraseña autenticado | `UnauthorizedException` |
| `reset_password(correo, new_password)` | Reset por correo (recuperación) | `ValidationException` |
| `validate_token(token)` | Verificar JWT válido y usuario activo | `UnauthorizedException` |
| `ensure_default_user_exists()` | Crear admin por defecto si no existe | — |

**Reglas de negocio:**
- Email: validación con regex.
- Password: mínimo 8 caracteres.
- Correo se normaliza (strip + lowercase).
- Token JWT contiene: `sub` (user_id), `correo`, `rol_id`, `exp`.

---

### ProductoService — Catálogo de productos

| Método | Qué hace | Excepciones |
|--------|----------|-------------|
| `create(nombre, categoria_id, ...)` | Crear producto validando categoría y unidad | `ValidationException` |
| `update(producto_id, **kwargs)` | Actualizar campos (protege stock_actual) | `NotFoundException`, `ValidationException` |
| `deactivate(producto_id)` | Soft delete | `NotFoundException` |
| `search(query)` | Búsqueda por nombre (mínimo 2 chars) | `ValidationException` |
| `get_paginated(offset, limit, query, categoria_id)` | Productos con filtros y paginación | — |
| `get_productos_below_min_stock()` | Productos con stock bajo (para alertas) | — |

**Reglas de negocio:**
- Nombre: mínimo 2 caracteres.
- `categoria_id` y `unidad_medida_id` deben existir y estar activos.
- `stock_actual` se inicializa en 0 y NO se puede modificar directamente.
- `stock_minimo` no puede ser negativo.
- Campos protegidos contra modificación directa: `id`, `stock_actual`, `creado_en`.

---

### InventarioService — Entradas, salidas y stock

| Método | Qué hace | Excepciones |
|--------|----------|-------------|
| `registrar_entrada(tipo_id, fecha, lotes_data, ...)` | Crea entrada + lotes + actualiza stock | `ValidationException` |
| `registrar_salida(tipo_id, fecha, detalles_data, ...)` | Crea salida + detalles + descuenta stock | `ValidationException` |
| `get_stock_producto(producto_id)` | Stock completo con desglose por lotes | `NotFoundException` |
| `get_lotes_proximos_a_vencer(dias)` | Lotes que vencen pronto | `ValidationException` |
| `get_entradas_by_fecha(inicio, fin)` | Entradas en un rango | `ValidationException` |
| `get_salidas_by_fecha(inicio, fin)` | Salidas en un rango | `ValidationException` |

**Flujo de entrada:**
1. Validar lotes (producto existe, cantidad > 0).
2. Crear `EntradaInventario` + `LoteInventario` en transacción atómica.
3. Actualizar `stock_actual` de cada producto (+cantidad).

**Flujo de salida:**
1. Validar detalles (lote existe, cantidad > 0, stock suficiente).
2. Crear `SalidaInventario` + `DetalleSalidaInventario` en transacción atómica.
3. Descontar `stock_actual` de cada producto (-cantidad).

**Cálculo de stock por lote:**
```
stock_lote = cantidad_entrante
           - SUM(detalle_salida.cantidad)
           - SUM(produccion_detalle.cantidad)
```

---

### RecetaService — Recetas e ingredientes

| Método | Qué hace | Excepciones |
|--------|----------|-------------|
| `create(nombre, producto_id, ingredientes)` | Crear receta con ingredientes | `ValidationException` |
| `update(receta_id, **kwargs)` | Actualizar datos (sin ingredientes) | `NotFoundException` |
| `update_ingredientes(receta_id, ingredientes)` | Reemplazar ingredientes | `ValidationException` |
| `calcular_insumos_necesarios(receta_id, cantidad)` | Insumos = ingrediente × cantidad | `NotFoundException` |
| `verificar_insumos_disponibles(receta_id, cantidad)` | Compara insumos vs stock actual | `NotFoundException` |
| `deactivate(receta_id)` | Soft delete | `NotFoundException` |

**Modelo de datos:**
```
Receta "Pan de leche" → producto_id = Pan de leche
├── Detalle 1: producto_id = Harina,  cantidad = 500g
├── Detalle 2: producto_id = Azúcar,  cantidad = 50g
└── Detalle 3: producto_id = Levadura, cantidad = 10g
```

**Cálculo de insumos:**
- Si se producen 10 panes: Harina 500×10=5000g, Azúcar 50×10=500g, etc.

**verificar_insumos_disponibles retorna:**
```python
{
    "disponible": True/False,
    "detalle": [
        {"nombre": "Harina", "cantidad_necesaria": 5000, "stock_actual": 3000,
         "suficiente": False, "faltante": 2000},
        ...
    ]
}
```

---

### ProduccionService — Producción diaria con descuento FIFO

| Método | Qué hace | Excepciones |
|--------|----------|-------------|
| `registrar_produccion(receta_id, fecha, cantidad, ...)` | Producción completa con FIFO | `ValidationException` |
| `get_with_detalles(produccion_id)` | Producción + lotes consumidos | `NotFoundException` |
| `get_by_fecha_range(inicio, fin)` | Producciones por fecha | `ValidationException` |
| `get_by_receta(receta_id)` | Historial de una receta | — |

**Flujo completo de producción:**
1. Validar `cantidad_producida > 0`.
2. Obtener receta con ingredientes.
3. **Verificar insumos disponibles** (sino lanza excepción con detalle de faltantes).
4. **Asignar lotes FIFO**: lotes ordenados por fecha de vencimiento, se consumen primero los que vencen antes.
5. Crear `ProduccionDiaria` + `ProduccionDetalle` en transacción atómica.
6. **Descontar stock** de cada insumo.

**Ejemplo FIFO:**
```
Necesario: 5000g Harina
Lote A: 3000g, vence 2025-02-01 → consumir 3000g
Lote B: 4000g, vence 2025-03-01 → consumir 2000g (sobran 2000g)

ProduccionDetalle: [{lote A: 3000g}, {lote B: 2000g}]
```

**Trazabilidad:** Cada `ProduccionDetalle` registra qué lote se usó y cuánto se consumió.

---

### AlertaService — Detección y gestión de alertas

| Método | Qué hace | Retorna |
|--------|----------|---------|
| `detectar_bajo_stock()` | Genera alertas para stock bajo | Lista de alertas creadas |
| `detectar_proximos_a_vencer(dias)` | Genera alertas para lotes por vencer | Lista de alertas creadas |
| `ejecutar_deteccion_completa()` | Ejecuta ambas detecciones | `{"bajo_stock": N, "proximos_vencer": M}` |
| `get_alertas_activas(only_unread)` | Consultar alertas | Lista de alertas |
| `marcar_leida(alerta_id)` | Marcar una alerta como leída | True |
| `marcar_todas_leidas()` | Marcar todas como leídas | Cantidad marcada |
| `count_activas()` | Total no leídas (para badge) | Entero |

**Deduplicación:**
Antes de crear una alerta, verifica si ya existe una activa y no leída para el mismo producto y tipo. Si existe, no crea duplicado.

**Cuándo ejecutar detección:**
- Al iniciar la app (bootstrap).
- Después de registrar una salida o producción.
- Periódicamente (ej: cada hora).
- Manualmente desde la página de alertas.

---

### ReporteService — Reportes y estadísticas

| Método | Qué hace | Retorna |
|--------|----------|---------|
| `get_existencias_actuales()` | Stock de todos los productos con indicadores | `list[dict]` |
| `get_perdidas(inicio, fin)` | Productos dañados/vencidos con valor económico | `dict` con detalles y total |
| `get_consumo_anual(anio)` | Consumo por producto en un año | `list[dict]` ordenado por consumo |
| `get_resumen_dashboard()` | KPIs para el dashboard | `dict` con 5 métricas |
| `get_entradas_periodo(inicio, fin)` | Entradas con totales por periodo | `list[dict]` |
| `get_salidas_periodo(inicio, fin)` | Salidas con totales por periodo | `list[dict]` |

**KPIs del dashboard:**
```python
{
    "total_productos": 45,           # Productos activos
    "productos_bajo_stock": 3,       # stock_actual <= stock_minimo
    "entradas_mes": 12,              # Entradas últimos 30 días
    "salidas_mes": 28,               # Salidas últimos 30 días
    "lotes_por_vencer": 2,           # Lotes que vencen en 7 días
}
```

**Cálculo de pérdidas:**
```
valor_pérdida = cantidad × precio_unitario_del_lote
```
Solo considera salidas de tipo "Dañado" o "Vencido".

---

## Excepciones utilizadas

| Excepción | Cuándo se usa | Código |
|-----------|---------------|--------|
| `ValidationException` | Datos de entrada inválidos | 422 |
| `NotFoundException` | Registro no encontrado | 404 |
| `DuplicateException` | Registro duplicado (correo) | 409 |
| `UnauthorizedException` | Contraseña incorrecta / token inválido | 401 |

Todas heredan de `AppException` (definida en `dev/core/exceptions.py`).

---

## Diagrama de dependencias entre Services

```
ProduccionService ──→ RecetaService (calcula insumos, verifica disponibilidad)
                  ──→ InventarioService (descuenta stock)
                  
AlertaService ──→ ProductoService (detectar bajo stock)
              ──→ InventarioService (detectar vencimientos)

ReporteService ──→ (consultas directas con JOINs, no depende de otros services)
```

---

## Convenciones para agregar un nuevo Service

1. Crear el archivo en `dev/services/`.
2. Usar `@classmethod` en todos los métodos (sin estado).
3. Agregar docstring del módulo (arquitectura, flujo, uso).
4. Agregar docstring de clase (métodos principales, reglas de negocio).
5. Agregar docstring en cada método (args, returns, raises).
6. Validar datos de entrada antes de llamar al repositorio.
7. Lanzar excepciones del dominio (no Exception genérico).
8. Agregar el import en `dev/services/__init__.py`.
9. Documentar en este archivo (`docs/services.md`).

### Template

```python
"""
nombre_service.py — Descripción del servicio.

Arquitectura
------------
[Explicación de la responsabilidad del servicio]

Relación con otras capas
------------------------
[Page] → [State] → NombreService → [Repository] → [PostgreSQL]
"""

from __future__ import annotations
import logging

from dev.core.exceptions import NotFoundException, ValidationException
from dev.repositories.algun_repo import AlgunRepository

logger = logging.getLogger("dev.services.nombre")


class NombreService:
    """
    Servicio de [dominio].
    
    Métodos principales:
        - metodo1: Descripción breve.
    """
    
    @classmethod
    def metodo1(cls, parametro: str) -> Algo:
        """
        Descripción del método.
        
        Args:
            parametro: Descripción.
            
        Returns:
            Lo que retorna.
            
        Raises:
            ValidationException: Si X.
        """
        # Validación
        if not parametro:
            raise ValidationException("Parámetro requerido")
        
        # Delegar al repositorio
        resultado = AlgunRepository.create(parametro=parametro)
        logger.info("Operación exitosa: id=%s", resultado.id)
        return resultado
```
