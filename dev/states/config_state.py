"""
config_state.py — Estado reactivo del módulo de configuración.

Gestiona tres secciones:
    - Categorías de producto (CRUD)
    - Unidades de medida (CRUD)
    - Perfil de usuario (editar nombre, correo, cambiar contraseña)
"""

import logging
from typing import Optional

import reflex as rx

from dev.core.exceptions import AppException
from dev.models.models import CategoriaProducto, UnidadMedida
from dev.repositories.base_repository import BaseRepository
from dev.services.auth_service import AuthService
from dev.states.auth_state import AuthState

logger = logging.getLogger("dev.states.config")


class CategoriaRepository(BaseRepository[CategoriaProducto]):
    model = CategoriaProducto


class UnidadMedidaRepository(BaseRepository[UnidadMedida]):
    model = UnidadMedida


class ConfigState(rx.State):
    tab_actual: str = "categorias"

    is_loading: bool = False
    error_message: str = ""
    success_message: str = ""

    # ── Categorías ────────────────────────────────────────────
    categorias: list[dict] = []
    cat_dialog_open: bool = False
    cat_modo_editar: bool = False
    cat_editando_id: Optional[int] = None
    cat_form_nombre: str = ""
    cat_form_descripcion: str = ""
    cat_confirm_open: bool = False
    cat_confirm_id: Optional[int] = None
    cat_confirm_nombre: str = ""

    # ── Unidades de medida ────────────────────────────────────
    unidades: list[dict] = []
    um_dialog_open: bool = False
    um_modo_editar: bool = False
    um_editando_id: Optional[int] = None
    um_form_nombre: str = ""
    um_form_abreviatura: str = ""

    um_confirm_open: bool = False
    um_confirm_id: Optional[int] = None
    um_confirm_nombre: str = ""

    # ── Perfil ────────────────────────────────────────────────
    perfil_nombre: str = ""
    perfil_correo: str = ""
    perfil_actual_pw: str = ""
    perfil_nueva_pw: str = ""
    perfil_confirm_pw: str = ""
    perfil_pw_dialog_open: bool = False

    def set_tab(self, tab: str):
        self.tab_actual = tab
        self.error_message = ""
        self.success_message = ""

    # ═══════════════════════════════════════════════════════════
    # CATEGORÍAS
    # ═══════════════════════════════════════════════════════════

    def load_categorias(self):
        try:
            cats = CategoriaRepository.get_all(only_active=False)
            self.categorias = [
                {
                    "id": c.id,
                    "nombre": c.nombre,
                    "descripcion": c.descripcion or "",
                    "activo": c.activo,
                }
                for c in cats
            ]
        except Exception as e:
            logger.error("Error cargando categorías: %s", str(e))
            self.error_message = "Error al cargar categorías."

    def cat_abrir_crear(self):
        self.cat_modo_editar = False
        self.cat_editando_id = None
        self.cat_form_nombre = ""
        self.cat_form_descripcion = ""
        self.error_message = ""
        self.cat_dialog_open = True

    def cat_abrir_editar(self, cat_id: int):
        try:
            c = CategoriaRepository.get_by_id(cat_id)
            self.cat_modo_editar = True
            self.cat_editando_id = cat_id
            self.cat_form_nombre = c.nombre
            self.cat_form_descripcion = c.descripcion or ""
            self.error_message = ""
            self.cat_dialog_open = True
        except Exception as e:
            logger.error("Error cargando categoría: %s", str(e))
            return rx.toast.error("Error al cargar categoría.")

    def cat_cerrar_dialog(self):
        self.cat_dialog_open = False
        self.error_message = ""

    def cat_guardar(self):
        self.error_message = ""
        if not self.cat_form_nombre.strip():
            self.error_message = "El nombre es obligatorio."
            return

        try:
            data = {
                "nombre": self.cat_form_nombre.strip(),
                "descripcion": self.cat_form_descripcion.strip() or None,
            }
            if self.cat_modo_editar and self.cat_editando_id:
                CategoriaRepository.update(self.cat_editando_id, **data)
                msg = "Categoría actualizada."
            else:
                CategoriaRepository.create(**data)
                msg = "Categoría creada."

            self.cat_dialog_open = False
            self.load_categorias()
            return rx.toast.success(msg)
        except AppException as e:
            self.error_message = e.message
        except Exception as e:
            logger.error("Error guardando categoría: %s", str(e))
            self.error_message = "Error inesperado al guardar."

    def cat_confirmar_desactivar(self, cat_id: int):
        try:
            c = CategoriaRepository.get_by_id(cat_id)
            self.cat_confirm_id = cat_id
            self.cat_confirm_nombre = c.nombre
            self.cat_confirm_open = True
        except Exception as e:
            logger.error("Error: %s", str(e))
            return rx.toast.error("Error al cargar categoría.")

    def cat_ejecutar_desactivar(self):
        if not self.cat_confirm_id:
            return
        try:
            CategoriaRepository.soft_delete(self.cat_confirm_id)
            self.cat_confirm_open = False
            self.cat_confirm_id = None
            self.cat_confirm_nombre = ""
            self.load_categorias()
            return rx.toast.success("Categoría desactivada.")
        except Exception as e:
            logger.error("Error desactivando categoría: %s", str(e))
            self.cat_confirm_open = False
            return rx.toast.error("Error al desactivar categoría.")

    def cat_cerrar_confirm(self):
        self.cat_confirm_open = False
        self.cat_confirm_id = None

    # ═══════════════════════════════════════════════════════════
    # UNIDADES DE MEDIDA
    # ═══════════════════════════════════════════════════════════

    def load_unidades(self):
        try:
            ums = UnidadMedidaRepository.get_all(only_active=False)
            self.unidades = [
                {
                    "id": u.id,
                    "nombre": u.nombre,
                    "abreviatura": u.abreviatura,
                    "activo": u.activo,
                }
                for u in ums
            ]
        except Exception as e:
            logger.error("Error cargando unidades: %s", str(e))
            self.error_message = "Error al cargar unidades de medida."

    def um_abrir_crear(self):
        self.um_modo_editar = False
        self.um_editando_id = None
        self.um_form_nombre = ""
        self.um_form_abreviatura = ""
        self.error_message = ""
        self.um_dialog_open = True

    def um_abrir_editar(self, um_id: int):
        try:
            u = UnidadMedidaRepository.get_by_id(um_id)
            self.um_modo_editar = True
            self.um_editando_id = um_id
            self.um_form_nombre = u.nombre
            self.um_form_abreviatura = u.abreviatura
            self.error_message = ""
            self.um_dialog_open = True
        except Exception as e:
            logger.error("Error cargando unidad: %s", str(e))
            return rx.toast.error("Error al cargar unidad de medida.")

    def um_cerrar_dialog(self):
        self.um_dialog_open = False
        self.error_message = ""

    def um_guardar(self):
        self.error_message = ""
        if not self.um_form_nombre.strip():
            self.error_message = "El nombre es obligatorio."
            return
        if not self.um_form_abreviatura.strip():
            self.error_message = "La abreviatura es obligatoria."
            return

        try:
            data = {
                "nombre": self.um_form_nombre.strip(),
                "abreviatura": self.um_form_abreviatura.strip(),
            }
            if self.um_modo_editar and self.um_editando_id:
                UnidadMedidaRepository.update(self.um_editando_id, **data)
                msg = "Unidad de medida actualizada."
            else:
                UnidadMedidaRepository.create(**data)
                msg = "Unidad de medida creada."

            self.um_dialog_open = False
            self.load_unidades()
            return rx.toast.success(msg)
        except AppException as e:
            self.error_message = e.message
        except Exception as e:
            logger.error("Error guardando unidad: %s", str(e))
            self.error_message = "Error inesperado al guardar."

    def um_confirmar_desactivar(self, um_id: int):
        try:
            u = UnidadMedidaRepository.get_by_id(um_id)
            self.um_confirm_id = um_id
            self.um_confirm_nombre = u.nombre
            self.um_confirm_open = True
        except Exception as e:
            logger.error("Error: %s", str(e))
            return rx.toast.error("Error al cargar unidad de medida.")

    def um_ejecutar_desactivar(self):
        if not self.um_confirm_id:
            return
        try:
            UnidadMedidaRepository.soft_delete(self.um_confirm_id)
            self.um_confirm_open = False
            self.um_confirm_id = None
            self.um_confirm_nombre = ""
            self.load_unidades()
            return rx.toast.success("Unidad de medida desactivada.")
        except Exception as e:
            logger.error("Error desactivando unidad: %s", str(e))
            self.um_confirm_open = False
            return rx.toast.error("Error al desactivar unidad de medida.")

    def um_cerrar_confirm(self):
        self.um_confirm_open = False
        self.um_confirm_id = None

    # ═══════════════════════════════════════════════════════════
    # PERFIL DE USUARIO
    # ═══════════════════════════════════════════════════════════

    def load_perfil(self):
        auth = self.get_state(AuthState)
        self.perfil_nombre = auth.user_nombre
        self.perfil_correo = auth.user_email
        self.error_message = ""
        self.success_message = ""

    def guardar_perfil(self):
        self.error_message = ""
        self.success_message = ""
        if not self.perfil_nombre.strip():
            self.error_message = "El nombre es obligatorio."
            return
        if not self.perfil_correo.strip():
            self.error_message = "El correo es obligatorio."
            return

        auth = self.get_state(AuthState)
        try:
            from dev.repositories.usuario_repo import UsuarioRepository

            data = {
                "nombre": self.perfil_nombre.strip(),
                "correo": self.perfil_correo.strip().lower(),
            }
            UsuarioRepository.update(auth.user_id, **data)
            auth.user_nombre = self.perfil_nombre.strip()
            auth.user_email = self.perfil_correo.strip().lower()
            self.success_message = "Perfil actualizado correctamente."
            return rx.toast.success("Perfil actualizado.")
        except AppException as e:
            self.error_message = e.message
        except Exception as e:
            logger.error("Error guardando perfil: %s", str(e))
            self.error_message = "Error inesperado al guardar perfil."

    def pw_abrir_dialog(self):
        self.perfil_actual_pw = ""
        self.perfil_nueva_pw = ""
        self.perfil_confirm_pw = ""
        self.error_message = ""
        self.perfil_pw_dialog_open = True

    def pw_cerrar_dialog(self):
        self.perfil_pw_dialog_open = False
        self.error_message = ""

    def cambiar_password(self):
        self.error_message = ""
        if not self.perfil_actual_pw:
            self.error_message = "Ingresa tu contraseña actual."
            return
        if not self.perfil_nueva_pw or len(self.perfil_nueva_pw) < 8:
            self.error_message = "La nueva contraseña debe tener al menos 8 caracteres."
            return
        if self.perfil_nueva_pw != self.perfil_confirm_pw:
            self.error_message = "Las contraseñas no coinciden."
            return

        auth = self.get_state(AuthState)
        try:
            AuthService.change_password(
                auth.user_id,
                self.perfil_actual_pw,
                self.perfil_nueva_pw,
            )
            self.perfil_pw_dialog_open = False
            self.perfil_actual_pw = ""
            self.perfil_nueva_pw = ""
            self.perfil_confirm_pw = ""
            return rx.toast.success("Contraseña cambiada correctamente.")
        except AppException as e:
            self.error_message = e.message
        except Exception as e:
            logger.error("Error cambiando contraseña: %s", str(e))
            self.error_message = "Error inesperado al cambiar contraseña."

    # ═══════════════════════════════════════════════════════════
    # LOAD GENERAL
    # ═══════════════════════════════════════════════════════════

    def on_load(self):
        self.is_loading = True
        self.error_message = ""
        try:
            self.load_categorias()
            self.load_unidades()
            self.load_perfil()
        except Exception as e:
            logger.error("Error cargando configuración: %s", str(e))
            self.error_message = "Error al cargar la configuración."
        finally:
            self.is_loading = False
