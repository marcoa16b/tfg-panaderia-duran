"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import logging

import reflex as rx

from rxconfig import config

from dev.core.logging_config import setup_logging
from dev.pages.login import login
from dev.pages.dashboard import index
from dev.pages.recovery_password import recovery_password
from dev.pages.productos import productos
from dev.pages.entradas import entradas
from dev.pages.salidas import salidas
from dev.pages.recetas import recetas
from dev.pages.produccion_diaria import produccion_diaria
from dev.pages.alertas import alertas
from dev.pages.estadisticas import estadisticas
from dev.pages.reportes import reportes
from dev.pages.proveedores import proveedores
from dev.pages.demo_components import demo_components

from dev.core.bootstrap import bootstrap_app

from dev.states.dashboard_state import DashboardState
from dev.states.producto_state import ProductoState
from dev.states.entrada_salida_state import EntradaSalidaState
from dev.states.receta_state import RecetaState
from dev.states.produccion_state import ProduccionState
from dev.states.reporte_state import ReporteState
from dev.states.proveedor_state import ProveedorState
from dev.states.auth_state import AuthState

setup_logging()
logger = logging.getLogger("dev")


class State(rx.State):
    """The app state."""


bootstrap_app()

app = rx.App()
app.add_page(index, on_load=[AuthState.check_auth, DashboardState.load_dashboard])
app.add_page(login)
app.add_page(recovery_password, "/recovery-password")
app.add_page(productos, "/productos", on_load=[AuthState.check_auth, ProductoState.load_productos])
app.add_page(entradas, "/entradas", on_load=[AuthState.check_auth, EntradaSalidaState.on_load])
app.add_page(salidas, "/salidas", on_load=[AuthState.check_auth, EntradaSalidaState.on_load])
app.add_page(recetas, "/recetas", on_load=[AuthState.check_auth, RecetaState.on_load])
app.add_page(produccion_diaria, "/produccion-diaria", on_load=[AuthState.check_auth, ProduccionState.on_load])
app.add_page(alertas, "/alertas", on_load=[AuthState.check_auth, DashboardState.load_dashboard])
app.add_page(estadisticas, "/estadisticas", on_load=[AuthState.check_auth, ReporteState.on_load])
app.add_page(reportes, "/reportes", on_load=[AuthState.check_auth, ReporteState.on_load])
app.add_page(proveedores, "/proveedores", on_load=[AuthState.check_auth, ProveedorState.load_proveedores])
app.add_page(demo_components, "/demo-components")
