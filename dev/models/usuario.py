"""
Modelo de usuario en la Base de Datos
Autor: Eikling Antonio Davila Mercado

Capal: Model

Descripcion: Este archivo contiene el modelo del usuario que ira dentro de la BD.

NOTA: Si se actualiza este modelo debe ejecutar el comando 'uv run reflex db migrate'
"""

from sqlmodel import SQLModel, Field, select
from typing import Optional


# =======================
# Modelo de Base de Datos
# =======================

class Usuario(SQLModel, table=True):
    __tablename__ = "usuarios"

    id: Optional[int] = Field (default=None, primary_key=True, nullable=False)
    email: str = Field(index=True, unique=True)
    password_hash: str = Field(nullable=False)
    activo: bool = Field(default=True)
