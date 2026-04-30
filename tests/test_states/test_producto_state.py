import pytest
from decimal import Decimal

from dev.states.producto_state import ProductoState


class TestProductoStateLoad:
    def test_load_productos(self, seed_producto):
        state = ProductoState()
        state.load_productos()
        assert state.is_loading is False
        assert len(state.productos) >= 1
        assert state.total_productos >= 1
        assert state.total_paginas >= 1

    def test_load_productos_carga_categorias(self, seed_producto):
        state = ProductoState()
        state.load_productos()
        assert len(state.categorias) >= 1
        assert len(state.unidades_medida) >= 1


class TestProductoStateFiltros:
    def test_buscar_productos(self, seed_producto):
        state = ProductoState()
        state.search_query = "harina"
        state.buscar_productos()
        assert len(state.productos) >= 1

    def test_filtrar_por_categoria(self, seed_producto):
        state = ProductoState()
        state.filtrar_por_categoria(str(seed_producto["cat_id"]))
        assert state.filtro_categoria_id == seed_producto["cat_id"]
        assert state.pagina_actual == 1

    def test_filtrar_por_categoria_cero(self, seed_producto):
        state = ProductoState()
        state.filtro_categoria_id = 5
        state.filtrar_por_categoria("0")
        assert state.filtro_categoria_id is None

    def test_limpiar_filtros(self, seed_producto):
        state = ProductoState()
        state.search_query = "harina"
        state.filtro_categoria_id = 1
        state.limpiar_filtros()
        assert state.search_query == ""
        assert state.filtro_categoria_id is None
        assert state.pagina_actual == 1


class TestProductoStatePaginacion:
    def test_pagina_siguiente(self, seed_producto):
        state = ProductoState()
        state.load_productos()
        total_antes = state.pagina_actual
        if state.total_paginas > 1:
            state.pagina_siguiente()
            assert state.pagina_actual == total_ante + 1
        else:
            state.pagina_siguiente()
            assert state.pagina_actual == total_antes

    def test_pagina_anterior(self, seed_producto):
        state = ProductoState()
        state.load_productos()
        state.pagina_actual = 1
        state.pagina_anterior()
        assert state.pagina_actual == 1


class TestProductoStateDialog:
    def test_abrir_crear(self, seed_producto):
        state = ProductoState()
        state.abrir_crear()
        assert state.dialog_open is True
        assert state.modo_editar is False
        assert state.form_nombre == ""

    def test_abrir_editar(self, seed_producto):
        state = ProductoState()
        state.abrir_editar(seed_producto["producto_id"])
        assert state.dialog_open is True
        assert state.modo_editar is True
        assert state.editando_id == seed_producto["producto_id"]
        assert state.form_nombre == "Harina de trigo"

    def test_cerrar_dialog(self, seed_producto):
        state = ProductoState()
        state.abrir_crear()
        state.cerrar_dialog()
        assert state.dialog_open is False

    def test_guardar_producto_crear(self, seed_producto):
        state = ProductoState()
        state.abrir_crear()
        state.form_nombre = "Nuevo Producto"
        state.form_categoria_id = str(seed_producto["cat_id"])
        state.form_unidad_medida_id = str(seed_producto["um_id"])
        state.guardar_producto()
        assert state.dialog_open is False

    def test_guardar_producto_sin_nombre(self, seed_producto):
        state = ProductoState()
        state.abrir_crear()
        state.form_nombre = ""
        state.guardar_producto()
        assert state.error_message != ""

    def test_guardar_producto_sin_categoria(self, seed_producto):
        state = ProductoState()
        state.abrir_crear()
        state.form_nombre = "Test"
        state.form_categoria_id = ""
        state.guardar_producto()
        assert "categoría" in state.error_message.lower() or "categor" in state.error_message.lower()


class TestProductoStateDesactivar:
    def test_confirmar_desactivar(self, seed_producto):
        state = ProductoState()
        state.confirmar_desactivar(seed_producto["producto_id"])
        assert state.confirm_open is True
        assert state.confirm_producto_id == seed_producto["producto_id"]

    def test_ejecutar_desactivar(self, seed_producto):
        state = ProductoState()
        state.confirmar_desactivar(seed_producto["producto_id"])
        state.ejecutar_desactivar()
        assert state.confirm_open is False

    def test_cerrar_confirm(self, seed_producto):
        state = ProductoState()
        state.confirmar_desactivar(seed_producto["producto_id"])
        state.cerrar_confirm()
        assert state.confirm_open is False
