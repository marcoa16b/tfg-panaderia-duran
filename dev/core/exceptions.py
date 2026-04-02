class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(AppException):
    def __init__(self, message: str = "Recurso no encontrado"):
        super().__init__(message, status_code=404)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "No autorizado"):
        super().__init__(message, status_code=401)


class ForbiddenException(AppException):
    def __init__(self, message: str = "Acceso denegado"):
        super().__init__(message, status_code=403)


class ValidationException(AppException):
    def __init__(self, message: str = "Datos inválidos"):
        super().__init__(message, status_code=422)


class DuplicateException(AppException):
    def __init__(self, message: str = "El recurso ya existe"):
        super().__init__(message, status_code=409)
