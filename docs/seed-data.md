# Datos Iniciales (Seed Data)

## Archivo: `dev/core/seed_data.py`

El seed pobla la BD con datos mínimos necesarios para que el sistema funcione.
Se ejecuta automáticamente en cada arranque de la app (ver `dev/core/bootstrap.py`).

## Principio: Idempotente

Todas las funciones verifican si los datos ya existen antes de insertar. Es seguro
ejecutar el seed múltiples veces sin duplicar registros.

## Datos que se insertan

### 1. Roles del sistema (`rol`)
| Rol | Descripción | Permisos |
|-----|-------------|----------|
| Administrador | Acceso total al sistema | CRUD completo |
| Operario | Gestión de inventario y producción | Entradas, salidas, producción |
| Consultor | Solo lectura de reportes y estadísticas | Solo lectura |

### 2. Grupos de tipos (`list_tipo`)
| Grupo | Descripción |
|-------|-------------|
| entrada | Tipos de entrada de inventario |
| salida | Tipos de salida de inventario |
| alerta | Tipos de alertas del sistema |

### 3. Tipos específicos (`tipo`)
| Grupo | Tipos |
|-------|-------|
| entrada | Compra, Donación, Ajuste positivo |
| salida | Consumo, Dañado, Vencido, Ajuste negativo |
| alerta | Bajo stock, Próximo a vencer |

### 4. Unidades de medida (`unidad_medida`)
| Unidad | Abreviatura |
|--------|-------------|
| Kilogramo | kg |
| Gramo | g |
| Libra | lb |
| Litro | L |
| Mililitro | ml |
| Unidad | u |
| Docena | dz |
| Caja | cj |
| Bolsa | bolsa |
| Saco | saco |

### 5. Categorías de producto (`categoria_producto`)
Harinas, Azúcares, Grasas, Lácteos, Huevos, Levaduras, Rellenos, Frutas, Empaques, Condimentos

### 6. Geografía de Costa Rica
- **San José:** Provincia → Cantón Central → 11 distritos
- **Alajuela:** Provincia → Cantón Central → 6 distritos

### 7. Usuario administrador
- **Correo:** `admin@panaderiaduran.com`
- **Contraseña:** `Admin123!`
- **Rol:** Administrador

## Orden de ejecución

El orden importa por las dependencias de FK:

```
1. Roles           (sin dependencias)
2. ListTipo        (sin dependencias)
3. Tipo            (depende de ListTipo)
4. UnidadMedida    (sin dependencias)
5. CategoriaProd   (sin dependencias)
6. Geografía       (Provincia → Canton → Distrito)
7. Admin user      (depende de Rol)
```

## Cómo agregar más datos de seed

1. Crear una función `seed_xxx()` que retorne el número de registros insertados.
2. Usar `_seed_if_empty(model, data)` para inserts simples.
3. Para inserts con dependencias, abrir sesión manualmente (ver `seed_tipos()`).
4. Agregar la llamada en `run_all_seeds()` respetando el orden de dependencias.
