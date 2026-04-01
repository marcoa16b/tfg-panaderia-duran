"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx

from rxconfig import config

from dev.pages.login import login
from dev.pages.dashboard import index
from dev.pages.recovery_password import recovery_password

from dev.core.bootstrap import bootstrap_app

class State(rx.State):
    """The app state."""

# bootstrap_app()
  
app = rx.App()
app.add_page(index)
app.add_page(login)
app.add_page(recovery_password, "/recovery-password")

