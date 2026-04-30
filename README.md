# Panadería Durán — Sistema de Inventario

Sistema de gestión de inventario para Panadería Durán, desarrollado con **Reflex** (Python full-stack), SQLModel y PostgreSQL.

## Arquitectura

```
Layered Architecture with State-Service-Repository pattern

[Page/UI] → [State (Reflex)] → [Service] → [Repository] → [PostgreSQL]
```

| Capa | Directorio | Responsabilidad |
|------|-----------|----------------|
| Modelos | `dev/models/` | SQLModel con `table=True` |
| Repositories | `dev/repositories/` | CRUD genérico + acceso a datos |
| Services | `dev/services/` | Lógica de negocio y validaciones |
| States | `dev/states/` | Estado reactivo (Reflex State) |
| Pages | `dev/pages/` | Vistas y componentes de página |
| Components | `dev/components/` | Componentes UI reutilizables |
| Core | `dev/core/` | Config, DB, seguridad, seed data |

## Stack Tecnológico

| Componente | Tecnología |
|-----------|-----------|
| Framework | Reflex 0.8+ |
| ORM | SQLModel |
| BD Desarrollo | SQLite |
| BD Producción | PostgreSQL 16 |
| Migraciones | Alembic (via `reflex db`) |
| Hashing | Argon2 (passlib) |
| JWT | python-jose |
| Export PDF | reportlab |
| Export Excel | openpyxl |
| Gestor de paquetes | uv |

## Requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (gestor de paquetes)
- Docker + Docker Compose (para producción)

## Desarrollo Local

### 1. Instalar dependencias

```bash
uv sync
```

### 2. Ejecutar la aplicación

```bash
uv run reflex run
```

La app arranca en `http://localhost:3000`.

### 3. Credenciales por defecto

- **Correo:** `admin@panaderiaduran.com`
- **Contraseña:** `Admin123!`

### 4. Base de datos (migraciones)

```bash
# Inicializar migraciones
uv run reflex db init

# Crear migración tras cambios en modelos
uv run reflex db migrate

# Aplicar migraciones pendientes
uv run reflex db migrate
```

> En desarrollo se usa SQLite (`reflex.db`) automáticamente. No se requiere configuración adicional.

## Tests

```bash
# Ejecutar todos los tests
uv run pytest tests/ -v

# Solo tests de services
uv run pytest tests/test_services/ -v

# Solo tests de repositories
uv run pytest tests/test_repositories/ -v

# Solo tests de states
uv run pytest tests/test_states/ -v
```

Los tests usan SQLite en memoria con monkeypatching de `rx.session()`. Se ejecutan 163+ tests que cubren services, repositories y states.

## Producción con Docker

### 1. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar `.env` con valores reales:

```env
DB_PASSWORD=tu_password_seguro
SECRET_KEY=tu_secret_key_aleatorio_de_al_menos_32_caracteres
DEBUG=false
```

### 2. Construir y levantar

```bash
docker compose up -d
```

La app estará disponible en `http://localhost:3000`.

### 3. Ver logs

```bash
docker compose logs -f app
```

### 4. Detener

```bash
docker compose down
```

> Los datos de PostgreSQL persisten en el volumen Docker `pgdata`. Para eliminar todo: `docker compose down -v`.

## Estructura del Proyecto

```
.
├── alembic/                  # Migraciones de BD
├── alembic.ini               # Config de Alembic
├── assets/                   # Imágenes y recursos estáticos
├── dev/
│   ├── components/           # Componentes UI reutilizables
│   │   ├── alerta_card.py    # Cards de alerta
│   │   ├── form_producto.py  # Formulario de producto
│   │   ├── header.py         # Barra superior
│   │   ├── layout.py         # Template base
│   │   ├── modal_confirmacion.py  # Diálogos de confirmación
│   │   ├── sidebar.py        # Navegación lateral
│   │   ├── stat_card.py      # Tarjetas KPI
│   │   └── tabla_generica.py # Tabla con paginación
│   ├── core/
│   │   ├── bootstrap.py      # Inicialización de la app
│   │   ├── config.py         # Variables de entorno
│   │   ├── database.py       # Engine SQLModel
│   │   ├── exceptions.py     # Excepciones personalizadas
│   │   ├── security.py       # Hashing y JWT
│   │   └── seed_data.py      # Datos iniciales
│   ├── models/
│   │   └── models.py         # Todos los modelos SQLModel
│   ├── pages/                # Vistas de cada página
│   ├── repositories/         # Acceso a datos (BaseRepository + especializados)
│   ├── services/             # Lógica de negocio
│   ├── states/               # Estado reactivo Reflex
│   └── dev.py                # Entry point de la app
├── tests/                    # Tests con pytest
│   ├── conftest.py           # Fixtures compartidas
│   ├── test_services/        # Tests unitarios de services
│   ├── test_repositories/    # Tests de integración de repos
│   └── test_states/          # Tests de event handlers
├── Dockerfile
├── docker-compose.yml
├── rxconfig.py               # Config de Reflex
└── pyproject.toml            # Dependencias del proyecto
```

## Variables de Entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///reflex.db` | URL de conexión a BD |
| `SECRET_KEY` | `dev-secret-key-change-in-production` | Clave para JWT |
| `DEBUG` | `true` | Modo debug |
| `LOG_LEVEL` | `INFO` | Nivel de logging |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Expiración del token JWT (min) |

## Convenciones de Git

- Ramas por fase: `feature/fase-N-descripcion`
- Commits convencionales: `feat:`, `fix:`, `refactor:`, `chore:`, `test:`, `docs:`
- Pull Request a `main` al finalizar cada fase
