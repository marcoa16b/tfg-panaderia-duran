import logging
from typing import Optional

import reflex as rx

from dev.core.exceptions import AppException
from dev.repositories.proveedor_repo import ProveedorRepository

logger = logging.getLogger("dev.states.proveedor")

PAGE_SIZE = 20


class ProveedorState(rx.State):
    proveedores: list[dict] = []
    total_proveedores: int = 0
    pagina_actual: int = 1
    total_paginas: int = 1

    search_query: str = ""
    is_loading: bool = False
    error_message: str = ""
    success_message: str = ""

    dialog_open: bool = False
    modo_editar: bool = False
    editando_id: Optional[int] = None

    form_nombre: str = ""
    form_telefono: str = ""
    form_correo: str = ""
    form_direccion: str = ""
    form_notas: str = ""

    confirm_open: bool = False
    confirm_proveedor_id: Optional[int] = None
    confirm_proveedor_nombre: str = ""

    def load_proveedores(self):
        self.is_loading = True
        self.error_message = ""
        try:
            offset = (self.pagina_actual - 1) * PAGE_SIZE
            resultados, total = ProveedorRepository.search_with_filters(
                query=self.search_query if self.search_query.strip() else None,
                offset=offset,
                limit=PAGE_SIZE,
            )
            self.proveedores = [self._proveedor_to_dict(p) for p in resultados]
            self.total_proveedores = total
            self.total_paginas = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        except Exception as e:
            logger.error("Error cargando proveedores: %s", str(e))
            self.error_message = "Error al cargar proveedores."
        finally:
            self.is_loading = False

    def buscar_proveedores(self):
        self.pagina_actual = 1
        self.load_proveedores()

    def limpiar_filtros(self):
        self.search_query = ""
        self.pagina_actual = 1
        self.load_proveedores()

    def pagina_siguiente(self):
        if self.pagina_actual < self.total_paginas:
            self.pagina_actual += 1
            self.load_proveedores()

    def pagina_anterior(self):
        if self.pagina_actual > 1:
            self.pagina_actual -= 1
            self.load_proveedores()

    def abrir_crear(self):
        self.modo_editar = False
        self.editando_id = None
        self.form_nombre = ""
        self.form_telefono = ""
        self.form_correo = ""
        self.form_direccion = ""
        self.form_notas = ""
        self.error_message = ""
        self.dialog_open = True

    def abrir_editar(self, proveedor_id: int):
        try:
            p = ProveedorRepository.get_by_id(proveedor_id)
            self.modo_editar = True
            self.editando_id = proveedor_id
            self.form_nombre = p.nombre
            self.form_telefono = p.telefono or ""
            self.form_correo = p.correo or ""
            self.form_direccion = p.direccion_exacta or ""
            self.form_notas = p.notas or ""
            self.error_message = ""
            self.dialog_open = True
        except Exception as e:
            logger.error("Error cargando proveedor: %s", str(e))
            return rx.toast.error("Error al cargar proveedor.")

    def cerrar_dialog(self):
        self.dialog_open = False
        self.error_message = ""

    def guardar_proveedor(self):
        self.error_message = ""
        if not self.form_nombre.strip():
            self.error_message = "El nombre es obligatorio."
            return

        try:
            data = {
                "nombre": self.form_nombre.strip(),
                "telefono": self.form_telefono.strip() or None,
                "correo": self.form_correo.strip() or None,
                "direccion_exacta": self.form_direccion.strip() or None,
                "notas": self.form_notas.strip() or None,
            }
            if self.modo_editar and self.editando_id:
                ProveedorRepository.update(self.editando_id, **data)
                msg = "Proveedor actualizado correctamente."
            else:
                ProveedorRepository.create(**data)
                msg = "Proveedor creado correctamente."

            self.dialog_open = False
            self.load_proveedores()
            return rx.toast.success(msg)
        except AppException as e:
            self.error_message = e.message
        except Exception as e:
            logger.error("Error guardando proveedor: %s", str(e))
            self.error_message = "Error inesperado al guardar."

    def confirmar_desactivar(self, proveedor_id: int):
        try:
            p = ProveedorRepository.get_by_id(proveedor_id)
            self.confirm_proveedor_id = proveedor_id
            self.confirm_proveedor_nombre = p.nombre
            self.confirm_open = True
        except Exception as e:
            logger.error("Error: %s", str(e))
            return rx.toast.error("Error al cargar proveedor.")

    def ejecutar_desactivar(self):
        if not self.confirm_proveedor_id:
            return
        try:
            ProveedorRepository.soft_delete(self.confirm_proveedor_id)
            self.confirm_open = False
            self.confirm_proveedor_id = None
            self.confirm_proveedor_nombre = ""
            self.load_proveedores()
            return rx.toast.success("Proveedor desactivado.")
        except Exception as e:
            logger.error("Error desactivando: %s", str(e))
            self.confirm_open = False
            return rx.toast.error("Error al desactivar proveedor.")

    def cerrar_confirm(self):
        self.confirm_open = False
        self.confirm_proveedor_id = None

    @staticmethod
    def _proveedor_to_dict(p) -> dict:
        return {
            "id": p.id,
            "nombre": p.nombre,
            "telefono": p.telefono or "",
            "correo": p.correo or "",
            "direccion": p.direccion_exacta or "",
            "notas": p.notas or "",
            "activo": p.activo,
        }
