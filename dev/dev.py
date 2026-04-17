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
from dev.pages.demo_components import demo_components

from dev.core.bootstrap import bootstrap_app

setup_logging()
logger = logging.getLogger("dev")


class State(rx.State):
    """The app state."""


bootstrap_app()

app = rx.App()
app.add_page(index)
app.add_page(login)
app.add_page(recovery_password, "/recovery-password")
app.add_page(productos, "/productos")
app.add_page(entradas, "/entradas")
app.add_page(salidas, "/salidas")
app.add_page(recetas, "/recetas")
app.add_page(produccion_diaria, "/produccion-diaria")
app.add_page(alertas, "/alertas")
app.add_page(estadisticas, "/estadisticas")
app.add_page(reportes, "/reportes")
app.add_page(demo_components, "/demo-components")
