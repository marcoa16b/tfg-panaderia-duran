"""
Servicio de login
Autor: E

Capa: Service / Domain logic

Descripción: este archivo incluye funciones relevantes como encriptación y verificación de contraseñas,
ademas de llamar a los metodos de repositorio (Base de datos).

Notas:
- Se utilizo Argon2 para cifrar las contraseñas, añadiendo una capa extra de seguridad en el sistema 
al utilizar uno de los metodos de cifrado mas seguros.
"""

from passlib.context import CryptContext
import reflex as rx
from ..repositories.usuario_repo import UsuariosRepository

# =========================  
# Password hashing  
# =========================  
pwd_context = CryptContext(  
    schemes=["argon2"],  
    deprecated="auto",  
)

# =========================  
# Auth Service  
# ========================= 
class AuthService:
    @staticmethod  
    def hash_password(password: str) -> str:  
        return pwd_context.hash(password) 
    
    @staticmethod  
    def verify_password(plain_password: str, password_hash: str) -> bool:  
        return pwd_context.verify(plain_password, password_hash)

    @classmethod  
    def authenticate(cls, email: str, password: str):  
        email_normalized = email.strip().lower()  
        usuario = UsuariosRepository.get_by_email(email_normalized)   
        if not usuario:  
            return None  
        if not usuario.activo:  
            return None  
        if not cls.verify_password(password, usuario.password_hash):  
            return None  
        return usuario

