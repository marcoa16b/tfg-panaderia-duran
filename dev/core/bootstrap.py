from dev.services.auth_service import AuthService
  
  
def bootstrap_app() -> None:  
    # Garantiza usuario fijo al iniciar  
    AuthService.ensure_default_user_exists()
    