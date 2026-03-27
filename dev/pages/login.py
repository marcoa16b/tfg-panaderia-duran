""" 
Interfaz de la página /login
Autor: Noemy Alejandra Alvarado Quesada

Capa: UI / Presentation

Descripcion: Esta es la pagina de autenticación, genera un pequeño formulario de email y contraseña
para el inicio de sesión de los usuarios

UI -> State -> Service -> Repository
"""

import reflex as rx

# Importamos el estado desde el archivo de servicio de autenticación.
from ..states.auth_state import AuthState 


def login() -> rx.Component:
    return rx.flex(
        rx.card(
            rx.vstack(
                rx.center(
                    rx.image(
                        # La imagen "logo.png" se agrego a la carpeta "assets"
                        src="/logo.png", width="2.5em", height="auto", border_radius="25%"
                    ),
                rx.heading(
                    "Sign in to your account",
                    size="6",
                    as_="h2",
                    text_align="center",
                    width="100%",
                ),
                direction="column",
                spacing="5",
                width="100%",
                ),
                rx.vstack(
                    rx.text(
                        "Email address",
                        size="3",
                        weight="medium",
                        text_align="left",
                        width="100%",
                    ),
                    rx.input(
                        placeholder="user@reflex.dev", 
                        type="email", 
                        size="3", 
                        width="100%",
                        value=AuthState.email,
                        on_change=AuthState.set_email
                    ),
                    justify="start",
                    spacing="2",
                    width="100%",
                ),
                rx.vstack(
                    rx.hstack(
                        rx.text("Contraseña", size="3", weight="medium"),
                        rx.link("¿Olvidaste tu contraseña?", href="/recovery-password", size="3"),
                        justify="between",
                        width="100%",
                    ),
                    rx.input(
                        placeholder="Ingresa tu contraseña",
                        type="password",
                        size="3",
                        width="100%",
                        value=AuthState.password,
                        on_change=AuthState.set_password
                    ),
                    spacing="2",
                    width="100%",
                ),
                rx.cond(  
                    AuthState.error_message != "",  
                    rx.text(AuthState.error_message, color="red", size="2"),  
                ),
                rx.button(
                    rx.cond(AuthState.is_loading, "Iniciando sesión...", "Iniciar sesión"),
                    size="3", 
                    width="100%",
                    on_click=AuthState.login, # rx.toast("Login process"),  
                    loading=AuthState.is_loading, 
                ),
                # rx.center(
                #     rx.text("New here?", size="3"),
                #     rx.link("Sign up", href="/register", size="3"),
                #     opacity="0.8",
                #     spacing="2",
                #     direction="row",
                # ),
                spacing="6",
                width="100%",
                align_items="center",
            ),
            size="4",
            max_width="28em",
            width="100%",
            align_items="center",
            justify="center",
        ),
        min_height="100vh",
        width="100%",
        align_items="center",   
        display="flex",
        justify_content="center",
    )
 