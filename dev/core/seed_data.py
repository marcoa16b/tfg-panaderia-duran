"""
seed_data.py — Datos iniciales para poblar la base de datos.

Este módulo se ejecuta automáticamente en el bootstrap de la aplicación
(ver `dev/core/bootstrap.py`) y pobla las tablas de referencia con datos
mínimos necesarios para que el sistema funcione.

Principio: Idempotente
----------------------
Todas las funciones de seed verifican si los datos ya existen antes de insertar.
Es seguro ejecutar `run_all_seeds()` múltiples veces sin duplicar datos.

Datos que se insertan
---------------------
1. Roles: Administrador, Operario, Consultor
2. ListTipo: Grupos de tipos (entrada, salida, alerta)
3. Tipo: Valores específicos por grupo (Compra, Consumo, Bajo stock, etc.)
4. UnidadMedida: kg, g, lb, L, ml, unidades, etc.
5. CategoriaProducto: Harinas, Azúcares, Grasas, Lácteos, etc.
6. Geografía: Provincias, cantones y distritos de Costa Rica (mínimo)
7. Admin user: admin@panaderiaduran.com / Admin123!

Orden de ejecución
------------------
El orden IMPORTA porque hay dependencias por FK:
    1. Roles (no depende de nadie)
    2. ListTipo (no depende de nadie)
    3. Tipo (depende de ListTipo)
    4. UnidadMedida (no depende de nadie)
    5. CategoriaProducto (no depende de nadie)
    6. Geografía: Provincia → Canton → Distrito
    7. Admin user (depende de Rol)

Cómo agregar más datos de seed
------------------------------
1. Crear una función `seed_xxx()` que retorne el número de registros insertados.
2. Usar `_seed_if_empty()` para inserts simples (un modelo, lista de dicts).
3. Para inserts con dependencias (como Tipo que necesita ListTipo.id),
   abrir sesión manualmente.
4. Agregar la llamada en `run_all_seeds()`.
"""

import logging
from typing import Type

import reflex as rx
from sqlmodel import select

from dev.models.models import (
    Canton,
    CategoriaProducto,
    Distrito,
    ListTipo,
    Provincia,
    Rol,
    Tipo,
    UnidadMedida,
)
from dev.core.security import hash_password

logger = logging.getLogger("dev.core.seed_data")


def _seed_if_empty(model: Type, data: list[dict]) -> int:
    """
    Utilidad genérica: inserta registros solo si la tabla está vacía.

    Args:
        model: Clase SQLModel destino.
        data: Lista de dicts con los campos del modelo.

    Returns:
        Número de registros insertados (0 si la tabla ya tenía datos).
    """
    with rx.session() as session:
        count = len(session.exec(select(model)).all())
        if count > 0:
            logger.debug(
                "%s ya tiene %s registros — saltando seed", model.__name__, count
            )
            return 0
        for item in data:
            session.add(model(**item))
        session.commit()
        logger.info("%s: %s registros insertados", model.__name__, len(data))
        return len(data)


def seed_roles() -> int:
    """Roles del sistema: Administrador (total), Operario (inventario), Consultor (lectura)."""
    return _seed_if_empty(
        Rol,
        [
            {"nombre": "Administrador", "descripcion": "Acceso total al sistema"},
            {"nombre": "Operario", "descripcion": "Gestión de inventario y producción"},
            {
                "nombre": "Consultor",
                "descripcion": "Solo lectura de reportes y estadísticas",
            },
        ],
    )


def seed_list_tipos() -> int:
    """Grupos de tipos: entrada (compras), salida (consumos), alerta (notificaciones)."""
    return _seed_if_empty(
        ListTipo,
        [
            {"nombre": "entrada", "descripcion": "Tipos de entrada de inventario"},
            {"nombre": "salida", "descripcion": "Tipos de salida de inventario"},
            {"nombre": "alerta", "descripcion": "Tipos de alertas del sistema"},
        ],
    )


def seed_tipos() -> int:
    """
    Valores de tipos por cada grupo.
    Necesita los IDs de ListTipo, por eso abre sesión manualmente.
    """
    with rx.session() as session:
        count = len(session.exec(select(Tipo)).all())
        if count > 0:
            return 0

        # Mapear nombres de ListTipo a sus IDs
        list_tipos = {lt.nombre: lt.id for lt in session.exec(select(ListTipo)).all()}

        tipos_data = [
            {
                "list_tipo_id": list_tipos["entrada"],
                "nombre": "Compra",
                "descripcion": "Compra a proveedor",
            },
            {
                "list_tipo_id": list_tipos["entrada"],
                "nombre": "Donación",
                "descripcion": "Producto donado",
            },
            {
                "list_tipo_id": list_tipos["entrada"],
                "nombre": "Ajuste positivo",
                "descripcion": "Ajuste manual de incremento",
            },
            {
                "list_tipo_id": list_tipos["salida"],
                "nombre": "Consumo",
                "descripcion": "Uso en producción",
            },
            {
                "list_tipo_id": list_tipos["salida"],
                "nombre": "Dañado",
                "descripcion": "Producto dañado o defectuoso",
            },
            {
                "list_tipo_id": list_tipos["salida"],
                "nombre": "Vencido",
                "descripcion": "Producto expirado",
            },
            {
                "list_tipo_id": list_tipos["salida"],
                "nombre": "Ajuste negativo",
                "descripcion": "Ajuste manual de decremento",
            },
            {
                "list_tipo_id": list_tipos["alerta"],
                "nombre": "Bajo stock",
                "descripcion": "Stock actual menor al mínimo",
            },
            {
                "list_tipo_id": list_tipos["alerta"],
                "nombre": "Próximo a vencer",
                "descripcion": "Producto próximo a fecha de vencimiento",
            },
        ]
        for item in tipos_data:
            session.add(Tipo(**item))
        session.commit()
        logger.info("Tipo: %s registros insertados", len(tipos_data))
        return len(tipos_data)


def seed_unidades_medida() -> int:
    """Unidades de medida usadas en panadería: kg, g, lb, L, ml, unidades, etc."""
    return _seed_if_empty(
        UnidadMedida,
        [
            {"nombre": "Kilogramo", "abreviatura": "kg"},
            {"nombre": "Gramo", "abreviatura": "g"},
            {"nombre": "Libra", "abreviatura": "lb"},
            {"nombre": "Litro", "abreviatura": "L"},
            {"nombre": "Mililitro", "abreviatura": "ml"},
            {"nombre": "Unidad", "abreviatura": "u"},
            {"nombre": "Docena", "abreviatura": "dz"},
            {"nombre": "Caja", "abreviatura": "cj"},
            {"nombre": "Bolsa", "abreviatura": "bolsa"},
            {"nombre": "Saco", "abreviatura": "saco"},
        ],
    )


def seed_categorias_producto() -> int:
    """Categorías de productos/insumos de una panadería."""
    return _seed_if_empty(
        CategoriaProducto,
        [
            {"nombre": "Harinas", "descripcion": "Harinas y derivados"},
            {"nombre": "Azúcares", "descripcion": "Azúcares y endulzantes"},
            {"nombre": "Grasas", "descripcion": "Mantequilla, margarina, aceites"},
            {"nombre": "Lácteos", "descripcion": "Leche, crema, queso"},
            {"nombre": "Huevos", "descripcion": "Huevos y derivados"},
            {"nombre": "Levaduras", "descripcion": "Levaduras y fermentos"},
            {"nombre": "Rellenos", "descripcion": "Rellenos y cremas"},
            {"nombre": "Frutas", "descripcion": "Frutas frescas y procesadas"},
            {"nombre": "Empaques", "descripcion": "Bolsas, cajas, etiquetas"},
            {"nombre": "Condimentos", "descripcion": "Especias, sal, vainilla, etc."},
            {"nombre": "Producción", "descripcion": "Productos finales elaborados por la panadería"},
        ],
    )


def seed_geografia() -> int:
    """
    Datos geográficos de Costa Rica: Provincia → Cantón → Distrito.
    Incluye solo San José y Alajuela como datos iniciales.
    Se puede extender con más provincias/cantones/distritos.

    Usa flush() para obtener IDs de provincia y cantón antes de crear distritos.
    """
    with rx.session() as session:
        count = len(session.exec(select(Provincia)).all())
        if count > 0:
            return 0

        # --- San José ---
        san_jose = Provincia(nombre="San José")
        session.add(san_jose)
        session.flush()

        canton_central = Canton(nombre="San José", provincia_id=san_jose.id)
        session.add(canton_central)
        session.flush()

        distritos_sj = [
            "Carmen",
            "Merced",
            "Hospital",
            "Catedral",
            "Zapote",
            "San Francisco de Dos Ríos",
            "Uruca",
            "Mata Redonda",
            "Pavas",
            "Hatillo",
            "San Sebastián",
        ]
        for nombre in distritos_sj:
            session.add(Distrito(nombre=nombre, canton_id=canton_central.id))

        # --- Alajuela ---
        alajuela = Provincia(nombre="Alajuela")
        session.add(alajuela)
        session.flush()

        canton_alajuela = Canton(nombre="Alajuela", provincia_id=alajuela.id)
        session.add(canton_alajuela)
        session.flush()

        distritos_alaj = [
            "Alajuela",
            "San José",
            "Carrizal",
            "San Antonio",
            "Guácima",
            "Tambor",
        ]
        for nombre in distritos_alaj:
            session.add(Distrito(nombre=nombre, canton_id=canton_alajuela.id))

        session.commit()
        logger.info("Geografía: provincias, cantones y distritos insertados")
        return 1


def seed_admin_user() -> int:
    """
    Crea el usuario administrador por defecto.
    Credenciales: admin@panaderiaduran.com / Admin123!
    Solo se crea si no existe ya un usuario con ese correo.
    """
    from dev.models.models import Usuario

    with rx.session() as session:
        stmt = select(Rol).where(Rol.nombre == "Administrador")
        rol = session.exec(stmt).first()
        if not rol:
            logger.warning("No se encontró rol Administrador — saltando seed de admin")
            return 0

        stmt = select(Usuario).where(Usuario.correo == "admin@panaderiaduran.com")
        if session.exec(stmt).first():
            logger.debug("Usuario admin ya existe — saltando")
            return 0

        admin = Usuario(
            nombre="Administrador",
            correo="admin@panaderiaduran.com",
            contrasena_hash=hash_password("Admin123!"),
            rol_id=rol.id,
            activo=True,
        )
        session.add(admin)
        session.commit()
        logger.info("Usuario admin creado — correo: admin@panaderiaduran.com")
        return 1


def run_all_seeds() -> dict[str, int]:
    """
    Ejecuta todas las funciones de seed en orden correcto.
    Llamado desde bootstrap.py al iniciar la aplicación.

    Returns:
        Dict con nombre de seed → registros insertados.
        Ej: {"roles": 3, "list_tipos": 3, "tipos": 9, "admin": 1}
    """
    logger.info("Iniciando seed de datos iniciales...")

    results = {}
    results["roles"] = seed_roles()
    results["list_tipos"] = seed_list_tipos()
    results["tipos"] = seed_tipos()
    results["unidades"] = seed_unidades_medida()
    results["categorias"] = seed_categorias_producto()
    results["geografia"] = seed_geografia()
    results["admin"] = seed_admin_user()

    logger.info("Seed completado — %s", results)
    return results
