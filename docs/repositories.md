# Arquitectura de la Capa de Repositories

## Visión General

Este proyecto sigue el patrón **Repository + Service Layer**, donde cada capa tiene una responsabilidad clara:

```
[Page/UI] → [State (Reflex)] → [Service] → [Repository] → [PostgreSQL]
```

| Capa | Responsabilidad | Qué hace | Qué NO hace |
|------|----------------|----------|-------------|
| **Pages** | Presentación visual | Renderiza componentes | Lógica de negocio |
| **States** | Estado reactivo UI | Maneja vars y eventos | Acceso directo a BD |
| **Services** | Lógica de negocio | Valida, calcula, orquesta | No conoce SQL |
| **Repositories** | Acceso a datos | CRUD puro contra la BD | No valida reglas |
| **Models** | Definición de tablas | ORM (SQLModel) | No tiene comportamiento |

---

## Estructura de Archivos

```
dev/repositories/
├── __init__.py              # Re-exports de todos los repos
├── base_repository.py       # CRUD genérico (clase base)
├── usuario_repo.py          # Repo de usuarios (auth)
├── producto_repo.py         # Repo de productos (inventario)
├── proveedor_repo.py        # Repo de proveedores
├── entrada_repo.py          # Repo de entradas + lotes
├── salida_repo.py           # Repo de salidas + detalles
├── receta_repo.py           # Repo de recetas + ingredientes
└── produccion_repo.py       # Repo de producción + detalles
```

---

## BaseRepository — Cómo funciona la herencia

Todos los repos heredan de `BaseRepository[T]` donde `T` es un modelo SQLModel:

```python
class ProductoRepository(BaseRepository[Producto]):
    model = Producto  # Solo necesitas definir el modelo
```

### Métodos que hereda automáticamente

| Método | Firma | Qué hace |
|--------|-------|----------|
| `get_by_id` | `(id: int) → Optional[T]` | Busca por PK |
| `get_by_id_or_fail` | `(id: int) → T` | Busca por PK o lanza NotFoundException |
| `get_all` | `(only_active=True) → list[T]` | Todos los registros (filtra inactivos) |
| `get_paginated` | `(offset, limit, only_active) → (list, int)` | Página + total |
| `create` | `(**kwargs) → T` | Crea un registro |
| `update` | `(id, **kwargs) → T` | Actualiza campos específicos |
| `soft_delete` | `(id: int) → bool` | Pone activo=False (no borra) |
| `count` | `(only_active=True) → int` | Cuenta registros |
| `exists` | `(id: int) → bool` | Verifica si existe |

### Sesiones de BD

Cada método abre su propia sesión con `rx.session()`:

```python
with rx.session() as session:
    # ...operaciones...
    session.commit()  # Opcional: el context manager hace commit/rollback
```

Reflex maneja el pool de conexiones automáticamente.

---

## Soft Delete

**Nunca se borran registros de la BD.** Todos los modelos tienen un campo `activo: bool`.

- `soft_delete(id)` → pone `activo = False`
- Todos los métodos de consulta aceptan `only_active=True` por defecto
- Los registros inactivos permanecen para auditoría y trazabilidad

---

## Transacciones Atómicas (Patrón cabecera-detalle)

Varios repos implementan `create_with_detalles()` para crear registros padre-hijo en una sola transacción:

```python
def create_with_lotes(cls, entrada_data, lotes_data):
    with rx.session() as session:
        # 1. Crear la cabecera (entrada)
        entrada = EntradaInventario(**entrada_data)
        session.add(entrada)
        session.flush()  # Genera el ID sin hacer commit

        # 2. Crear los detalles (lotes) usando el ID generado
        for lote_dict in lotes_data:
            lote_dict["entrada_id"] = entrada.id
            session.add(LoteInventario(**lote_dict))

        # 3. Commit de todo junto (atómico)
        session.commit()
```

Este patrón se usa en:
- `EntradaRepository.create_with_lotes()` — entrada + lotes
- `SalidaRepository.create_with_detalles()` — salida + detalles
- `RecetaRepository.create_with_detalles()` — receta + ingredientes
- `ProduccionRepository.create_with_detalles()` — producción + consumo de lotes

---

## Repos por Dominio

### UsuarioRepository
- **Tabla:** `usuario`
- **Especial:** `get_by_correo()` para autenticación, `search()` por nombre/correo

### ProductoRepository
- **Tabla:** `producto`
- **Especial:** `update_stock()` para incrementar/decrementar stock, `get_below_min_stock()` para alertas
- **Búsqueda:** `search_with_filters()` con texto + categoría + paginación

### ProveedorRepository
- **Tabla:** `proveedor`
- **Especial:** Búsqueda por distrito geográfico

### EntradaRepository + LoteRepository
- **Tablas:** `entrada_inventario` (cabecera) + `lote_inventario` (detalle)
- **Flujo:** Una compra/entrada genera N lotes (uno por producto)
- **Alertas:** `LoteRepository.get_proximos_a_vencer()` para productos por vencer

### SalidaRepository + DetalleSalidaRepository
- **Tablas:** `salida_inventario` (cabecera) + `detalle_salida_inventario` (detalle)
- **Tipos de salida:** Consumo, Dañado, Vencido, Ajuste negativo
- **Trazabilidad:** Cada detalle referencia un lote específico

### RecetaRepository + RecetaDetalleRepository
- **Tablas:** `receta` (cabecera) + `receta_detalle` (ingredientes)
- **Modelo:** Una receta produce UN producto final usando N ingredientes
- **Update especial:** `update_detalles()` borra ingredientes anteriores y crea nuevos

### ProduccionRepository + ProduccionDetalleRepository
- **Tablas:** `produccion_diaria` (cabecera) + `produccion_detalle` (consumo de lotes)
- **Flujo:** Se selecciona receta → se calculan insumos → se descuentan de lotes
- **Trazabilidad:** Cada detalle indica de qué lote se tomó el insumo

---

## Cómo agregar un nuevo repositorio

1. Crear el modelo en `dev/models/models.py` (si no existe)
2. Crear el archivo en `dev/repositories/`

```python
# dev/repositories/mi_repo.py
import reflex as rx
from sqlmodel import select
from dev.models.models import MiModelo
from dev.repositories.base_repository import BaseRepository

class MiRepository(BaseRepository[MiModelo]):
    model = MiModelo

    # Agregar métodos específicos aquí...
```

3. Agregar el import en `dev/repositories/__init__.py`
4. Usar desde la capa Service:

```python
from dev.repositories import MiRepository

resultado = MiRepository.create(campo1="valor1")
```

---

## Diagrama de Relaciones entre Tablas

```
provincia ──→ canton ──→ distrito ──→ proveedor
                                     ↓
rol ──→ usuario              entrada_inventario ←── tipo
                                     ↓
list_tipo ──→ tipo          lote_inventario ──→ producto
                                  ↓              ↑       ↓
                    detalle_salida_inventario  categoria  unidad_medida
                                  ↓
                    salida_inventario ←── tipo

                    receta ──→ receta_detalle ──→ producto
                      ↓
                    produccion_diaria
                      ↓
                    produccion_detalle ──→ lote_inventario

                    alerta_inventario ←── tipo + producto
```
