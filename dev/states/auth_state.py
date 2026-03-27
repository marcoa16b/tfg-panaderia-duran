""" 
Estado de autenticación
Autor: Noemy Alejandra Alvarado Quesada & Eikling Davila Mercado

Capa: State / Application layer

Descripcion: Este es un archivo para gestionar el estado de autenticación de los usuarios,
comunica el frontend con el backend (AuthService).
"""

from typing import Optional
import reflex as rx
from dev.services.auth_service import AuthService


class AuthState(rx.State):
    email: str = ""
    password: str = ""

    error_message: str = ""
    is_loading: bool = False

    is_authenticated: bool = False
    user_id: Optional[int] = None
    user_email: str = ""

    # GETTERS & SETTERS -> por cada variable de la clase, debe haber un get y un set
    def get_email(self):
        return self.email
    
    def set_email(self, email: str):
        self.email = email

    def get_password(self):
        return self.password
    
    def set_password(self, password: str):
        self.password = password

    # METHODS
    def clear_error(self):
        self.error_message = ""

    def login(self):
        self.clear_error()
        self.is_loading = True

        if not self.email.strip() or not self.password:
            self.error_message = "Email y contraseña son obligatorios."
            self.is_loading = False
            return

        usuario = AuthService.authenticate(self.email, self.password)

        if not usuario:
            self.error_message = "Credenciales inválidas."
            self.is_loading = False
            return

        self.is_authenticated = True
        self.user_id = usuario.id
        self.user_email = usuario.email
        self.password = ""
        self.is_loading = False

        return rx.redirect("/")

    def logout(self):
        print("sign out process")
        self.email = ""
        self.password = ""
        self.error_message = ""
        self.is_loading = False
        self.is_authenticated = False
        self.user_id = None
        self.user_email = ""
        return rx.redirect("/login")
    
    # Este metodo es para la pagina de recuperación de contraseña
    def send_recovery_email(self):  
        self.clear_error()  
        self.is_loading = True  
        try:  
            email = self.email.strip().lower()  
            if not email:  
                self.error_message = "Debes ingresar un correo electrónico."  
                return  
    
            # TODO: Aquí llamas al service real de recuperación:  
            # AuthService.request_password_recovery(email)  
    
            # Mensaje neutro por seguridad (no revelar si existe o no)  
            return rx.toast("Si el correo existe, recibirás instrucciones para recuperar tu contraseña.", position="top-right",)  
        finally:  
            self.is_loading = False