# Despliegue con Docker + Cloudflare Tunnel

## Arquitectura

```
Usuario → Cloudflare Edge → Tunnel → cloudflared (VPS) ─┬→ app:3000 (frontend)
                                                         └→ app:8000 (backend API)
                                                         └→ db:5432  (PostgreSQL, interno)
```

- Frontend y backend corren en el mismo container Reflex
- PostgreSQL en un container separado (comunicación interna vía red Docker)
- `cloudflared` en un container que conecta con Cloudflare Edge
- **No se abren puertos públicos** en el VPS

## Requisitos previos

- VPS con Ubuntu/Debian y acceso SSH
- Dominio `nandev.online` gestionado por Cloudflare (DNS apuntando a sus nameservers)
- Docker y Docker Compose instalados en el VPS

## 1. Instalar Docker en el VPS

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Cerrar sesión y volver a entrar para que el grupo surta efecto
```

## 2. Crear el tunel en Cloudflare

### Opción A: Desde el Dashboard (recomendado)

1. Ir a [Cloudflare Zero Trust](https://one.dash.cloudflare.com/)
2. **Networks → Tunnels → Create a tunnel**
3. Seleccionar **"Cloudflared"** como connector
4. Nombrar el tunnel (ej: `panaderia-duran`)
5. Cloudflare generará un **tunnel token** — guardarlo
6. Configurar las **Public Hostname** routes:

| Subdomain | Domain | Service |
|---|---|---|
| `duran` | `nandev.online` | `http://app:3000` |
| `duran-api` | `nandev.online` | `http://app:8000` |

> **Nota:** El service usa `app` como hostname porque los containers comparten la red Docker interna. `app:3000` es el frontend del container Reflex, `app:8000` es el backend.

### Opción B: Desde CLI

```bash
# Instalar cloudflared localmente para configurar
cloudflared tunnel login
cloudflared tunnel create panaderia-duran

# Anotar el tunnel ID del output
cloudflared tunnel route dns panaderia-duran duran.nandev.online
cloudflared tunnel route dns panaderia-duran duran-api.nandev.online
```

## 3. Preparar el servidor

```bash
# Clonar el repositorio
git clone https://github.com/marcoa16b/tfg-panaderia-duran.git
cd tfg-panaderia-duran

# Copiar y editar las variables de entorno
cp .env.example .env
nano .env
```

## 4. Configurar `.env`

```bash
# ── Base de datos ──────────────────────────────────────────
DATABASE_URL=postgresql://panaderia_user:CHANGE_ME@db:5432/panaderia_duran
DB_NAME=panaderia_duran
DB_USER=panaderia_user
DB_PASSWORD=<generar-password-seguro>
DB_PORT=5432

# ── Seguridad ──────────────────────────────────────────────
SECRET_KEY=<generar-clave-aleatoria-32-chars>

# ── Aplicación ─────────────────────────────────────────────
APP_ENV=production
LOG_LEVEL=INFO
DEBUG=false
APP_PORT=3000
BACKEND_PORT=8000
ACCESS_TOKEN_EXPIRE_MINUTES=60
SEED_DEMO=false

# ── Cloudflare Tunnel ──────────────────────────────────────
TUNNEL_TOKEN=<pegar-token-de-cloudflare>
```

Generar claves seguras:

```bash
# Para SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Para DB_PASSWORD
python3 -c "import secrets; print(secrets.token_urlsafe(24))"
```

## 5. Desplegar

```bash
# Construir y levantar todos los servicios
docker compose up -d --build

# Verificar que todo está corriendo
docker compose ps

# Ver logs
docker compose logs -f app
docker compose logs -f tunnel
```

El primer build tarda varios minutos (instala dependencias Python, compila el frontend Next.js).

## 6. Verificar el despliegue

```bash
# Health check del backend
curl http://localhost:8000/health

# Verificar que el tunnel está conectado
docker compose logs tunnel | grep "Connection"
```

Abrir en el navegador:
- **Frontend:** https://duran.nandev.online
- **API:** https://duran-api.nandev.online (debería responder con 404 o health check)

## 7. Actualizar la aplicación

```bash
cd tfg-panaderia-duran

# Traer los últimos cambios
git pull origin main

# Reconstruir y reiniciar solo la app (sin tocar la base de datos)
docker compose up -d --build app

# Si cambiaron dependencias (requirements.txt)
docker compose build --no-cache app
docker compose up -d app
```

## 8. Comandos útiles

```bash
# Ver estado de los servicios
docker compose ps

# Ver logs de un servicio
docker compose logs -f app
docker compose logs -f tunnel
docker compose logs -f db

# Reiniciar un servicio
docker compose restart app

# Detener todo
docker compose down

# Detener y eliminar datos (⚠️ borra la base de datos)
docker compose down -v

# Acceder a la base de datos
docker compose exec db psql -U panaderia_user -d panaderia_duran

# Backup de la base de datos
docker compose exec db pg_dump -U panaderia_user panaderia_duran > backup.sql

# Restaurar backup
cat backup.sql | docker compose exec -T db psql -U panaderia_user panaderia_duran
```

## Troubleshooting

### El tunnel no conecta

```bash
# Verificar que el token es correcto
docker compose logs tunnel

# Si dice "authorization failed", regenerar el token en el dashboard de Cloudflare
```

### La app no arranca

```bash
# Ver logs completos del build
docker compose logs app

# Reconstruir sin cache
docker compose build --no-cache app
docker compose up -d app
```

### Error de conexión a la base de datos

```bash
# Verificar que PostgreSQL está listo
docker compose exec db pg_isready

# Verificar la URL de conexión en el .env
# DATABASE_URL debe usar "db" como host (nombre del servicio Docker)
```

### Puerto 3000 vs 3020

Los puertos internos del container son **3000** (frontend) y **8000** (backend). Esto se alinea con las variables `APP_PORT=3000` y `BACKEND_PORT=8000` del `.env` de producción. Los puertos 3020/8020 son solo para desarrollo local.

### Resetear la base de datos

```bash
docker compose down
docker volume rm tfg-panaderia-duran_pgdata
docker compose up -d
```
