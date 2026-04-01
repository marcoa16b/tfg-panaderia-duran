import reflex as rx
from dev.states.auth_state import AuthState


def recovery_password() -> rx.Component:
    return rx.flex(
        rx.card(
            rx.vstack(
                rx.vstack(
                    rx.center(
                        rx.image(
                            src="/logo.png",
                            width="2.5em",
                            height="auto",
                            border_radius="25%",
                        ),
                        width="100%",
                    ),
                    rx.heading(
                        "Recupera tu contraseña",
                        size="6",
                        as_="h2",
                        text_align="center",
                        width="100%",
                    ),
                    rx.text(
                        "Ingresa tu email para enviarte las instrucciones.",
                        size="3",
                        color="gray",
                        text_align="center",
                        width="100%",
                    ),
                    direction="column",
                    spacing="4",
                    width="100%",
                ),
                rx.vstack(
                    rx.text(
                        "Correo electrónico",
                        size="3",
                        weight="medium",
                        text_align="left",
                        width="100%",
                    ),
                    rx.input(
                        placeholder="user@mail.com",
                        type="email",
                        size="3",
                        width="100%",
                        value=AuthState.email,
                        on_change=AuthState.set_email,
                    ),
                    spacing="2",
                    width="100%",
                ),
                rx.cond(
                    AuthState.error_message != "",
                    rx.text(AuthState.error_message, color="red", size="2"),
                ),
                rx.button(
                    rx.cond(AuthState.is_loading, "Enviando...", "Enviar email de recuperación"),
                    size="3",
                    width="100%",
                    on_click=AuthState.send_recovery_email,
                    loading=AuthState.is_loading,
                ),
                rx.center(
                    rx.link("Volver al inicio de sesión", href="/login", size="3"),
                    width="100%",
                ),
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
        padding="1.5em",
    )