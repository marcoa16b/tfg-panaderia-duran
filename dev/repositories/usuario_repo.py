"""
usuario_repo.py — Repositorio de acceso a datos para la tabla `usuario`.

Hereda de BaseRepository[Usuario], lo que provee automáticamente:
    get_by_id, get_all, get_paginated, create, update, soft_delete, count, exists

Métodos específicos de dominio:
    - get_by_correo: Búsqueda por email (para login/autenticación).
    - get_active_by_correo: Igual pero filtra solo usuarios activos.
    - search: Búsqueda textual por nombre o correo (usa ilike = case-insensitive).
    - exists_by_correo: Verifica si un correo ya está registrado.

Uso desde la capa Service:
    from dev.repositories.usuario_repo import UsuarioRepository

    usuario = UsuarioRepository.get_by_correo("admin@panaderiaduran.com")
    todos = UsuarioRepository.get_all()
    nuevos = UsuarioRepository.create(nombre="Ana", correo="ana@mail.com", ...)
"""

import logging
from typing import Optional

import reflex as rx
from sqlmodel import select

from dev.models.models import Usuario
from dev.repositories.base_repository import BaseRepository

logger = logging.getLogger("dev.repositories.usuario")


class UsuarioRepository(BaseRepository[Usuario]):
    model = Usuario

    @classmethod
    def get_by_correo(cls, correo: str) -> Optional[Usuario]:
        """Busca un usuario por su correo electrónico. Incluye inactivos."""
        logger.debug("Buscando usuario por correo: %s", correo)
        with rx.session() as session:
            stmt = select(Usuario).where(Usuario.correo == correo)
            return session.exec(stmt).first()

    @classmethod
    def get_active_by_correo(cls, correo: str) -> Optional[Usuario]:
        """Busca un usuario activo por correo. Ignora usuarios con activo=False."""
        logger.debug("Buscando usuario activo por correo: %s", correo)
        with rx.session() as session:
            stmt = select(Usuario).where(
                Usuario.correo == correo,
                Usuario.activo == True,  # noqa: E712
            )
            return session.exec(stmt).first()

    @classmethod
    def search(cls, query: str, only_active: bool = True) -> list[Usuario]:
        """
        Búsqueda textual por nombre o correo (parcial, case-insensitive).
        Usa ilike que es compatible con SQLite y PostgreSQL.
        """
        logger.debug("Buscando usuarios: %s", query)
        with rx.session() as session:
            stmt = select(Usuario).where(
                Usuario.nombre.ilike(f"%{query}%") | Usuario.correo.ilike(f"%{query}%")
            )
            if only_active:
                stmt = stmt.where(Usuario.activo == True)  # noqa: E712
            return list(session.exec(stmt).all())

    @classmethod
    def exists_by_correo(cls, correo: str) -> bool:
        """Verifica si ya existe un usuario con ese correo."""
        return cls.get_by_correo(correo) is not None
