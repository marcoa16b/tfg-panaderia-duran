"""
auth_state.py — Estado reactivo de autenticación.

Arquitectura
------------
Capa State (Application Layer) para autenticación. Es el puente entre
la UI (login, recuperación de contraseña) y AuthService (lógica de negocio).

Patrón de diseño: Reflex State
    - Variables reactivas sincronizadas al frontend via WebSocket.
    - Event handlers llamados desde componentes UI (botones, formularios).
    - Delega toda la lógica al Service, nunca accede a la BD directamente.

Relación con otras capas
------------------------
    [Login Page] → AuthState.login() → AuthService.authenticate() → UsuarioRepository → [BD]
    [Layout]     → AuthState.check_auth() → redirect a /login si no autenticado
    [Header]     → AuthState.logout() → limpia estado + redirect

Variables de estado
-------------------
    Públicas (sincronizadas al frontend):
        - email, password: Campos del formulario de login.
        - error_message: Mensaje de error para mostrar en la UI.
        - is_loading: Estado de carga del formulario.
        - is_authenticated: Indicador de sesión activa.
        - user_id, user_email, user_nombre: Datos del usuario autenticado.
        - token: JWT generado al autenticar.

Flujo de autenticación
----------------------
1. El usuario ingresa correo + contraseña en el login.
2. AuthState.login() llama a AuthService.authenticate().
3. Si es exitoso: se almacenan los datos del usuario + token en el estado.
4. Se redirige al dashboard ("/").
5. Si falla: se muestra mensaje de error genérico.

Protección de rutas
-------------------
AuthState.check_auth() se llama desde el layout para verificar que
el usuario esté autenticado. Si no lo está, redirige a /login.

Uso desde la capa UI:
    from dev.states.auth_state import AuthState

    rx.button("Login", on_click=AuthState.login)
    rx.text(AuthState.user_email)
    rx.cond(AuthState.is_authenticated, DashboardContent, rx.redirect("/login"))
"""

import logging
from typing import Optional

import reflex as rx

from dev.services.auth_service import AuthService

logger = logging.getLogger("dev.states.auth")


class AuthState(rx.State):
    """
    Estado reactivo de autenticación.

    Gestiona el ciclo completo de autenticación del usuario:
    login, logout, protección de rutas y recuperación de contraseña.

    Métodos principales:
        - login: Autentica al usuario contra AuthService.
        - logout: Cierra la sesión y redirige al login.
        - check_auth: Verifica sesión activa (protección de rutas).
        - send_recovery_email: Inicia flujo de recuperación de contraseña.

    Variables reactivas:
        - is_authenticated: True si el usuario tiene sesión activa.
        - user_email, user_nombre: Datos del usuario para mostrar en UI.
        - token: JWT para validación posterior.
        - error_message: Mensaje de error para mostrar en formularios.
    """

    email: str = ""
    password: str = ""
    error_message: str = ""
    is_loading: bool = False

    is_authenticated: bool = False
    user_id: Optional[int] = None
    user_email: str = ""
    user_nombre: str = ""
    token: str = ""

    def clear_error(self):
        """Limpia el mensaje de error del formulario."""
        self.error_message = ""

    def login(self):
        """
        Autentica al usuario con correo y contraseña.

        Flujo:
            1. Valida que los campos no estén vacíos.
            2. Llama a AuthService.authenticate() con las credenciales.
            3. Si es exitoso: almacena datos del usuario + token en estado.
            4. Redirige al dashboard ("/").
            5. Si falla: muestra mensaje de error genérico.

        Returns:
            rx.redirect("/") si el login es exitoso.
            None si falla (error se muestra en error_message).

        Nota de seguridad:
            No revela si el usuario existe o no — mismo mensaje genérico
            para "usuario no encontrado" y "contraseña incorrecta".
        """
        self.clear_error()
        self.is_loading = True

        if not self.email.strip() or not self.password:
            self.error_message = "Correo y contraseña son obligatorios."
            self.is_loading = False
            return

        logger.info("Intento de login para: %s", self.email)
        result = AuthService.authenticate(self.email, self.password)

        if not result:
            self.error_message = "Credenciales inválidas."
            self.is_loading = False
            return

        usuario = result["usuario"]
        self.is_authenticated = True
        self.user_id = usuario.id
        self.user_email = usuario.correo
        self.user_nombre = usuario.nombre
        self.token = result["token"]
        self.password = ""
        self.is_loading = False
        logger.info("Login exitoso — usuario_id=%s", usuario.id)

        return rx.redirect("/")

    def logout(self):
        """
        Cierra la sesión del usuario.

        Limpia todas las variables de estado (credenciales, datos de usuario,
        token) y redirige a la página de login.

        Returns:
            rx.redirect("/login")
        """
        logger.info("Cierre de sesión para usuario: %s", self.user_email)
        self.email = ""
        self.password = ""
        self.error_message = ""
        self.is_loading = False
        self.is_authenticated = False
        self.user_id = None
        self.user_email = ""
        self.user_nombre = ""
        self.token = ""
        return rx.redirect("/login")

    def check_auth(self):
        """
        Verifica que el usuario esté autenticado (protección de rutas).

        Se llama desde el layout o páginas protegidas para redirigir
        a /login si no hay sesión activa.

        Returns:
            rx.redirect("/login") si no autenticado.
            None si la sesión es válida.
        """
        if not self.is_authenticated:
            return rx.redirect("/login")

    def send_recovery_email(self):
        """
        Inicia el flujo de recuperación de contraseña.

        Valida que se haya ingresado un correo y muestra un mensaje
        neutral por seguridad (no revela si el correo existe o no).

        Returns:
            rx.toast.info con mensaje neutral de confirmación.
        """
        self.clear_error()
        self.is_loading = True
        try:
            email = self.email.strip().lower()
            if not email:
                self.error_message = "Debes ingresar un correo electrónico."
                return

            logger.info("Solicitud de recuperación para: %s", email)
            return rx.toast.info(
                "Si el correo existe, recibirás instrucciones para recuperar tu contraseña.",
                position="top-right",
            )
        finally:
            self.is_loading = False
