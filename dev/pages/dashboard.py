
import reflex as rx
from rxconfig import config

from ..states.auth_state import AuthState

def index() -> rx.Component:

    return rx.cond(
        AuthState.is_authenticated, 
        rx.container(
            rx.color_mode.button(position="top-right"),
            rx.vstack(
                rx.heading("Welcome to Dashboard!", size="9"),
                rx.text(
                    "Get started by editing ",
                    rx.code(f"{config.app_name}/{config.app_name}.py"),
                    size="5",
                ),
                rx.link(
                    rx.button("Check out our docs!"),
                    href="https://reflex.dev/docs/getting-started/introduction/",
                    is_external=True,
                ),
                rx.button(
                    "Sign out",
                    size="3", 
                    width="100%",
                    on_click=AuthState.logout, # rx.toast("Login process"),  
                    #loading=AuthState.is_loading,
                ),
                spacing="5",
                justify="center",
                min_height="85vh",
            ),
        ), 
        rx.container(
            rx.color_mode.button(position="top-right"),
            rx.vstack(
                rx.heading("Not authenticated!", size="9"),
                rx.text(
                    "Get started by editing ",
                    rx.code(f"{config.app_name}/{config.app_name}.py"),
                    size="5",
                ),
                rx.link(
                    rx.button("Check out our docs!"),
                    href="https://reflex.dev/docs/getting-started/introduction/",
                    is_external=True,
                ),
                spacing="5",
                justify="center",
                min_height="85vh",
            ),
        )
    )

    