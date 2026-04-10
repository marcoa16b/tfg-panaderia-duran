"""
base_repository.py — Repositorio genérico base para CRUD.

Arquitectura
------------
Todos los repositorios del proyecto heredan de `BaseRepository[T]`, donde `T`
es un modelo SQLModel con `table=True`. Esto provee operaciones CRUD genéricas
(get, get_all, create, update, soft_delete, paginación) sin repetir código.

Patrón de diseño: Generic Repository
    - Cada subclase define `model = MiModelo` para acoplar el repo a su tabla.
    - Todos los métodos son `@classmethod` (sin estado) para compatibilidad
      con Reflex, que maneja sesiones de BD vía `rx.session()`.

Sesiones de BD
--------------
Cada método abre su propia sesión con `with rx.session() as session`.
Reflex se encarga del pool de conexiones y del commit/rollback automático
al salir del contexto. No es necesario pasar sesiones entre métodos.

Soft Delete
-----------
El borrado real está prohibido. `soft_delete()` pone `activo = False` y
actualiza `actualizado_en`. Todos los métodos de consulta aceptan
`only_active=True` para filtrar registros inactivos por defecto.

Uso
---
    from dev.repositories.base_repository import BaseRepository
    from dev.models.models import Producto

    class ProductoRepository(BaseRepository[Producto]):
        model = Producto

    # Hereda automáticamente: get_by_id, get_all, create, update, etc.

Relación con la arquitectura del proyecto
------------------------------------------
    [Page/UI] → [State (Reflex)] → [Service] → [Repository] → [PostgreSQL]

    Los repos NO contienen lógica de negocio. Solo acceso a datos puro.
    La lógica va en la capa `services/`.
"""

import logging
from datetime import datetime
from typing import Generic, Optional, Type, TypeVar

import reflex as rx
from sqlmodel import SQLModel, func, select

from dev.core.exceptions import NotFoundException

T = TypeVar("T", bound=SQLModel)

logger = logging.getLogger("dev.repositories.base")


class BaseRepository(Generic[T]):
    """
    Repositorio genérico CRUD para cualquier modelo SQLModel.

    Atributos de clase requeridos:
        model (Type[T]): El modelo SQLModel asociado. DEBE definirse en la subclase.

    Métodos heredados:
        - get_by_id(id) → instancia o None
        - get_by_id_or_fail(id) → instancia o lanza NotFoundException
        - get_all(only_active) → lista completa
        - get_paginated(offset, limit, only_active) → (lista, total)
        - create(**kwargs) → nueva instancia
        - update(id, **kwargs) → instancia actualizada
        - soft_delete(id) → True (pone activo=False)
        - count(only_active) → entero
        - exists(id) → bool
    """

    model: Type[T]

    @classmethod
    def get_by_id(cls, id: int) -> Optional[T]:
        """Obtiene un registro por su PK. Retorna None si no existe."""
        logger.debug("%s.get_by_id(%s)", cls.model.__name__, id)
        with rx.session() as session:
            return session.get(cls.model, id)

    @classmethod
    def get_by_id_or_fail(cls, id: int) -> T:
        """Obtiene un registro por PK. Lanza NotFoundException si no existe."""
        instance = cls.get_by_id(id)
        if not instance:
            raise NotFoundException(f"{cls.model.__name__} con id={id} no encontrado")
        return instance

    @classmethod
    def get_all(cls, only_active: bool = True) -> list[T]:
        """
        Retorna todos los registros de la tabla.
        Si only_active=True y el modelo tiene campo 'activo', filtra los inactivos.
        """
        logger.debug("%s.get_all(only_active=%s)", cls.model.__name__, only_active)
        with rx.session() as session:
            stmt = select(cls.model)
            if only_active and hasattr(cls.model, "activo"):
                stmt = stmt.where(cls.model.activo == True)  # noqa: E712
            return session.exec(stmt).all()

    @classmethod
    def get_paginated(
        cls,
        offset: int = 0,
        limit: int = 20,
        only_active: bool = True,
    ) -> tuple[list[T], int]:
        """
        Retorna una página de resultados junto con el total de registros.
        Útil para tablas con paginación en el frontend.

        Retorna:
            (lista_de_resultados, total_registros)
        """
        logger.debug(
            "%s.get_paginated(offset=%s, limit=%s)",
            cls.model.__name__,
            offset,
            limit,
        )
        with rx.session() as session:
            stmt = select(cls.model)
            count_stmt = select(func.count()).select_from(cls.model)
            if only_active and hasattr(cls.model, "activo"):
                stmt = stmt.where(cls.model.activo == True)  # noqa: E712
                count_stmt = count_stmt.where(cls.model.activo == True)  # noqa: E712
            total = session.exec(count_stmt).one()
            results = session.exec(stmt.offset(offset).limit(limit)).all()
            return results, total

    @classmethod
    def create(cls, **kwargs) -> T:
        """
        Crea un nuevo registro en la tabla.

        Args:
            **kwargs: Campos del modelo (ej: nombre="Harina", categoria_id=1).

        Returns:
            La instancia creada con su id generado por la BD.
        """
        logger.info("%s.create(%s)", cls.model.__name__, list(kwargs.keys()))
        with rx.session() as session:
            instance = cls.model(**kwargs)
            session.add(instance)
            session.commit()
            session.refresh(instance)  # Obtiene el id generado
            logger.info("%s creado — id=%s", cls.model.__name__, instance.id)
            return instance

    @classmethod
    def update(cls, id: int, **kwargs) -> T:
        """
        Actualiza campos específicos de un registro existente.
        Automáticamente actualiza el campo 'actualizado_en' si el modelo lo tiene.

        Args:
            id: PK del registro a actualizar.
            **kwargs: Campos a actualizar (solo se aplican si existen en el modelo).

        Raises:
            NotFoundException: Si el registro no existe.
        """
        logger.info("%s.update(%s, %s)", cls.model.__name__, id, list(kwargs.keys()))
        with rx.session() as session:
            instance = session.get(cls.model, id)
            if not instance:
                raise NotFoundException(
                    f"{cls.model.__name__} con id={id} no encontrado"
                )
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            if hasattr(instance, "actualizado_en"):
                instance.actualizado_en = datetime.now()
            session.add(instance)
            session.commit()
            session.refresh(instance)
            logger.info("%s actualizado — id=%s", cls.model.__name__, id)
            return instance

    @classmethod
    def soft_delete(cls, id: int) -> bool:
        """
        Borrado lógico: pone activo=False en lugar de eliminar el registro.
        El registro permanece en la BD para auditoría y trazabilidad.

        Raises:
            NotFoundException: Si el registro no existe.
        """
        logger.info("%s.soft_delete(%s)", cls.model.__name__, id)
        with rx.session() as session:
            instance = session.get(cls.model, id)
            if not instance:
                raise NotFoundException(
                    f"{cls.model.__name__} con id={id} no encontrado"
                )
            instance.activo = False
            instance.actualizado_en = datetime.now()
            session.add(instance)
            session.commit()
            logger.info("%s desactivado — id=%s", cls.model.__name__, id)
            return True

    @classmethod
    def count(cls, only_active: bool = True) -> int:
        """Cuenta el total de registros. Filtra inactivos por defecto."""
        with rx.session() as session:
            stmt = select(func.count()).select_from(cls.model)
            if only_active and hasattr(cls.model, "activo"):
                stmt = stmt.where(cls.model.activo == True)  # noqa: E712
            return session.exec(stmt).one()

    @classmethod
    def exists(cls, id: int) -> bool:
        """Verifica si un registro existe por su PK."""
        return cls.get_by_id(id) is not None
