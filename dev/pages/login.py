import reflex as rx

from ..states.auth_state import AuthState


def login() -> rx.Component:
    return rx.flex(
        rx.card(
            rx.vstack(
                rx.center(
                    rx.image(
                        src="/logo.png",
                        width="3em",
                        height="auto",
                        border_radius="25%",
                    ),
                    rx.heading(
                        "Panadería Durán",
                        size="7",
                        as_="h1",
                        text_align="center",
                        width="100%",
                        weight="bold",
                    ),
                    rx.text(
                        "Sistema de Inventario",
                        size="3",
                        color="gray",
                        text_align="center",
                    ),
                    direction="column",
                    spacing="3",
                    width="100%",
                ),
                rx.divider(margin_y="0.5em"),
                rx.vstack(
                    rx.text(
                        "Correo electrónico",
                        size="3",
                        weight="medium",
                        text_align="left",
                        width="100%",
                    ),
                    rx.input(
                        placeholder="usuario@panaderiaduran.com",
                        type="email",
                        size="3",
                        width="100%",
                        value=AuthState.email,
                        on_change=AuthState.set_email,
                    ),
                    justify="start",
                    spacing="2",
                    width="100%",
                ),
                rx.vstack(
                    rx.hstack(
                        rx.text("Contraseña", size="3", weight="medium"),
                        rx.spacer(),
                        rx.link(
                            "¿Olvidaste tu contraseña?",
                            href="/recovery-password",
                            size="2",
                        ),
                        justify="between",
                        width="100%",
                        align="center",
                    ),
                    rx.input(
                        placeholder="Ingresa tu contraseña",
                        type="password",
                        size="3",
                        width="100%",
                        value=AuthState.password,
                        on_change=AuthState.set_password,
                    ),
                    spacing="2",
                    width="100%",
                ),
                rx.cond(
                    AuthState.error_message != "",
                    rx.callout(
                        AuthState.error_message,
                        icon="circle-alert",
                        color_scheme="red",
                        size="1",
                    ),
                ),
                rx.button(
                    rx.cond(
                        AuthState.is_loading, "Iniciando sesión...", "Iniciar sesión"
                    ),
                    size="3",
                    width="100%",
                    on_click=AuthState.login,
                    loading=AuthState.is_loading,
                ),
                spacing="5",
                width="100%",
                align_items="center",
            ),
            size="4",
            max_width="28em",
            width="100%",
        ),
        min_height="100vh",
        width="100%",
        align_items="center",
        display="flex",
        justify_content="center",
        background=rx.color_mode_cond(
            light="linear-gradient(135deg, var(--gray-2) 0%, var(--gray-4) 100%)",
            dark="linear-gradient(135deg, var(--gray-1) 0%, var(--gray-3) 100%)",
        ),
    )
