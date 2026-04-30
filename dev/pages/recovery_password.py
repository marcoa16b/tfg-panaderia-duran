import reflex as rx

from dev.states.auth_state import AuthState


def recovery_password() -> rx.Component:
    return rx.flex(
        rx.card(
            rx.vstack(
                rx.center(
                    rx.image(
                        src="/Duran-logo.png",
                        width="3em",
                        height="auto",
                        border_radius="25%",
                    ),
                    rx.heading(
                        "Recuperar contraseña",
                        size="6",
                        as_="h2",
                        text_align="center",
                        width="100%",
                        weight="bold",
                    ),
                    rx.text(
                        "Ingresa tu correo electrónico y te enviaremos las instrucciones para restablecer tu contraseña.",
                        size="2",
                        color="gray",
                        text_align="center",
                        width="100%",
                    ),
                    direction="column",
                    spacing="3",
                    width="100%",
                ),
                rx.divider(margin_y="0.25em"),
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
                        AuthState.is_loading, "Enviando...", "Enviar instrucciones"
                    ),
                    size="3",
                    width="100%",
                    on_click=AuthState.send_recovery_email,
                    loading=AuthState.is_loading,
                ),
                rx.center(
                    rx.link(
                        rx.hstack(
                            rx.icon("arrow-left", size=14),
                            rx.text("Volver al inicio de sesión", size="2"),
                            spacing="1",
                            align="center",
                        ),
                        href="/login",
                    ),
                    width="100%",
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
        padding="1.5em",
    )
