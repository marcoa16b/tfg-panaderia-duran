"""
Repositorio de autenticación
Autor: Eikling Antonio Davila Mercado

Capa: Repository / Data access

Descripción: este archivo es el encargado de realizar acciones en la base de datos.
"""

from typing import Optional
from reflex as rx
from sqlmodel import select
from ..models.usuario import Usuario


class UsuariosRepository:
    @staticmethod
    def get_by_email(email: str) -> Optional[Usuario]:
        with rx.session() as session:
            stmt = select (Usuario).where(Usuario.email == email)
            return session.exec(stmt).first()

    # Actualizar usuario
    @staticmethod
    def create(email: str, passwword_hash: str, activo: bool = True) -> Usuario:
        with rx.session() as session:
            usuario = Usuario(email=email, password_hash=passwword_hash, activo=activo)
            session.add(usuario)
            session.commit()
            session.refresh(usuario)
            return usuario
        
    # Obtener todos los usuarios
    @staticmethod
    def get_all() -> list[Usuario]:
        with rx.session() as session:
            stmt = select(Usuario)
            return session.exec(stmt).all()

    # Actualizar usuario
    @staticmethod
    def update(usuario: Usuario) -> Usuario:
        with rx.session() as session:
            session.add(usuario)
            session.commit()
            session.refresh(usuario)
            return usuario

    # Eliminar usuario
    @staticmethod
    def delete(usuario: Usuario) -> None:
        with rx.session() as session:
            session.delete(usuario)
            session.commit()
          