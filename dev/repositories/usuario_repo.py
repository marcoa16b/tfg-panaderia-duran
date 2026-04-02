from typing import Optional

import reflex as rx
from sqlmodel import select

from dev.models.models import Usuario


class UsuariosRepository:
    @staticmethod
    def get_by_correo(correo: str) -> Optional[Usuario]:
        with rx.session() as session:
            stmt = select(Usuario).where(Usuario.correo == correo)
            return session.exec(stmt).first()

    @staticmethod
    def create(
        nombre: str, correo: str, contrasena_hash: str, rol_id: int, activo: bool = True
    ) -> Usuario:
        with rx.session() as session:
            usuario = Usuario(
                nombre=nombre,
                correo=correo,
                contrasena_hash=contrasena_hash,
                rol_id=rol_id,
                activo=activo,
            )
            session.add(usuario)
            session.commit()
            session.refresh(usuario)
            return usuario

    @staticmethod
    def get_all() -> list[Usuario]:
        with rx.session() as session:
            stmt = select(Usuario)
            return session.exec(stmt).all()

    @staticmethod
    def update(usuario: Usuario) -> Usuario:
        with rx.session() as session:
            session.add(usuario)
            session.commit()
            session.refresh(usuario)
            return usuario

    @staticmethod
    def delete(usuario: Usuario) -> None:
        with rx.session() as session:
            session.delete(usuario)
            session.commit()
