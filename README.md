# Instrucciones cambios necesarios y ejecución

## Informacion importante sobre el proyecto

Arquitectura utilizada: "Layered Architecture with State-Service-Repository pattern"

## Cambios necesarios

1. **python version**

Deben actualizar la versión de python a 3.12 por que la 3.14 da problemas.

Entonces, en el archivo `.python-version` deben poner `3.12`.

Luego en `pyproject.toml` deben poner `requires-python = ">=3.12"`.

Deben agregar ademas el archivo `.venv` al `.gitignore`.

Tambien crear el archivo `requirements.txt` con el siguiente contenido:

```txt
reflex==0.8.26
```

---

## Ejecución

Para ejecutar la aplicación deben usar el siguiente comando:

```bash
uv run reflex run
```

---

## Sistema de autenticación

### UI

La interfaz de autenticacion se encuentra en la carpeta `pages`.

### Backend

El backend consta de varios archivos. En Reflex el estado se ejecuta del lado del servidor por lo que es seguro realizar ciertas operaciones como Encriptacion de contraseñas desde este archivo y esto no se mostrara al cliente.

- La base de datos se configura en `rxconfig.py`.
- El modelo de base de datos se crea en `./dev/models/usuario.py`.
- El estado de autenticacion se crea en `./dev/states/auth_state.py`

En cada archivo se encuentra documentacion interna para ayudar a comprender el funcionamiento.

## BASE DE DATOS

Para inicializar la base de datos:

```bash
uv run reflex db init
```

Cada vez que hagan cambios en los modelos de bases de datos deben ejecutar:

```bash
uv run reflex db migrate
```
