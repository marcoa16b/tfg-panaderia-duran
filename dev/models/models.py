from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel


class Provincia(SQLModel, table=True):
    __tablename__ = "provincia"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100, unique=True)
    activo: bool = Field(default=True)
    creado_en: Optional[datetime] = Field(default_factory=datetime.now)
    actualizado_en: Optional[datetime] = Field(default_factory=datetime.now)


class Canton(SQLModel, table=True):
    __tablename__ = "canton"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100)
    provincia_id: int = Field(foreign_key="provincia.id")
    activo: bool = Field(default=True)
    creado_en: Optional[datetime] = Field(default_factory=datetime.now)
    actualizado_en: Optional[datetime] = Field(default_factory=datetime.now)


class Distrito(SQLModel, table=True):
    __tablename__ = "distrito"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100)
    canton_id: int = Field(foreign_key="canton.id")
    activo: bool = Field(default=True)
    creado_en: Optional[datetime] = Field(default_factory=datetime.now)
    actualizado_en: Optional[datetime] = Field(default_factory=datetime.now)


class ListTipo(SQLModel, table=True):
    __tablename__ = "list_tipo"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=50, unique=True)
    descripcion: Optional[str] = Field(default=None)
    activo: bool = Field(default=True)
    creado_en: Optional[datetime] = Field(default_factory=datetime.now)
    actualizado_en: Optional[datetime] = Field(default_factory=datetime.now)


class Tipo(SQLModel, table=True):
    __tablename__ = "tipo"

    id: Optional[int] = Field(default=None, primary_key=True)
    list_tipo_id: int = Field(foreign_key="list_tipo.id")
    nombre: str = Field(max_length=50)
    descripcion: Optional[str] = Field(default=None)
    activo: bool = Field(default=True)
    creado_en: Optional[datetime] = Field(default_factory=datetime.now)
    actualizado_en: Optional[datetime] = Field(default_factory=datetime.now)


class Rol(SQLModel, table=True):
    __tablename__ = "rol"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=50, unique=True)
    descripcion: Optional[str] = Field(default=None)
    activo: bool = Field(default=True)
    creado_en: Optional[datetime] = Field(default_factory=datetime.now)
    actualizado_en: Optional[datetime] = Field(default_factory=datetime.now)


class Usuario(SQLModel, table=True):
    __tablename__ = "usuario"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100)
    correo: str = Field(max_length=150, unique=True, index=True)
    contrasena_hash: str = Field(max_length=255)
    rol_id: int = Field(foreign_key="rol.id")
    activo: bool = Field(default=True)
    creado_en: Optional[datetime] = Field(default_factory=datetime.now)
    actualizado_en: Optional[datetime] = Field(default_factory=datetime.now)


class CategoriaProducto(SQLModel, table=True):
    __tablename__ = "categoria_producto"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100, unique=True)
    descripcion: Optional[str] = Field(default=None)
    activo: bool = Field(default=True)
    creado_en: Optional[datetime] = Field(default_factory=datetime.now)
    actualizado_en: Optional[datetime] = Field(default_factory=datetime.now)


class UnidadMedida(SQLModel, table=True):
    __tablename__ = "unidad_medida"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=50, unique=True)
    abreviatura: str = Field(max_length=10, unique=True)
    activo: bool = Field(default=True)
    creado_en: Optional[datetime] = Field(default_factory=datetime.now)
    actualizado_en: Optional[datetime] = Field(default_factory=datetime.now)


class Proveedor(SQLModel, table=True):
    __tablename__ = "proveedor"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=150)
    telefono: Optional[str] = Field(default=None, max_length=20)
    correo: Optional[str] = Field(default=None, max_length=150)
    distrito_id: Optional[int] = Field(default=None, foreign_key="distrito.id")
    direccion_exacta: Optional[str] = Field(default=None)
    notas: Optional[str] = Field(default=None)
    activo: bool = Field(default=True)
    creado_en: Optional[datetime] = Field(default_factory=datetime.now)
    actualizado_en: Optional[datetime] = Field(default_factory=datetime.now)


class Producto(SQLModel, table=True):
    __tablename__ = "producto"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=150)
    descripcion: Optional[str] = Field(default=None)
    categoria_id: int = Field(foreign_key="categoria_producto.id")
    unidad_medida_id: int = Field(foreign_key="unidad_medida.id")
    stock_minimo: Decimal = Field(default=Decimal("0"), max_digits=12, decimal_places=3)
    stock_actual: Decimal = Field(default=Decimal("0"), max_digits=12, decimal_places=3)
    ubicacion: Optional[str] = Field(default=None, max_length=100)
    imagen_url: Optional[str] = Field(default=None, max_length=500)
    activo: bool = Field(default=True)
    creado_en: Optional[datetime] = Field(default_factory=datetime.now)
    actualizado_en: Optional[datetime] = Field(default_factory=datetime.now)


class EntradaInventario(SQLModel, table=True):
    __tablename__ = "entrada_inventario"

    id: Optional[int] = Field(default=None, primary_key=True)
    tipo_id: int = Field(foreign_key="tipo.id")
    proveedor_id: Optional[int] = Field(default=None, foreign_key="proveedor.id")
    fecha: date
    numero_factura: Optional[str] = Field(default=None, max_length=50)
    observaciones: Optional[str] = Field(default=None)
    usuario_id: Optional[int] = Field(default=None, foreign_key="usuario.id")
    activo: bool = Field(default=True)
    creado_en: Optional[datetime] = Field(default_factory=datetime.now)
    actualizado_en: Optional[datetime] = Field(default_factory=datetime.now)


class LoteInventario(SQLModel, table=True):
    __tablename__ = "lote_inventario"

    id: Optional[int] = Field(default=None, primary_key=True)
    entrada_id: int = Field(foreign_key="entrada_inventario.id")
    producto_id: int = Field(foreign_key="producto.id")
    codigo_lote: Optional[str] = Field(default=None, max_length=50)
    cantidad: Decimal = Field(max_digits=12, decimal_places=3)
    precio_unitario: Optional[Decimal] = Field(
        default=None, max_digits=12, decimal_places=2
    )
    fecha_vencimiento: Optional[date] = Field(default=None)
    activo: bool = Field(default=True)
    creado_en: Optional[datetime] = Field(default_factory=datetime.now)
    actualizado_en: Optional[datetime] = Field(default_factory=datetime.now)


class SalidaInventario(SQLModel, table=True):
    __tablename__ = "salida_inventario"

    id: Optional[int] = Field(default=None, primary_key=True)
    tipo_id: int = Field(foreign_key="tipo.id")
    fecha: date
    observaciones: Optional[str] = Field(default=None)
    usuario_id: Optional[int] = Field(default=None, foreign_key="usuario.id")
    activo: bool = Field(default=True)
    creado_en: Optional[datetime] = Field(default_factory=datetime.now)
    actualizado_en: Optional[datetime] = Field(default_factory=datetime.now)


class DetalleSalidaInventario(SQLModel, table=True):
    __tablename__ = "detalle_salida_inventario"

    id: Optional[int] = Field(default=None, primary_key=True)
    salida_id: int = Field(foreign_key="salida_inventario.id")
    lote_id: int = Field(foreign_key="lote_inventario.id")
    cantidad: Decimal = Field(max_digits=12, decimal_places=3)
    motivo: Optional[str] = Field(default=None)
    activo: bool = Field(default=True)
    creado_en: Optional[datetime] = Field(default_factory=datetime.now)
    actualizado_en: Optional[datetime] = Field(default_factory=datetime.now)


class Receta(SQLModel, table=True):
    __tablename__ = "receta"

    id: Optional[int] = Field(default=None, primary_key=True)
    producto_id: int = Field(foreign_key="producto.id")
    nombre: str = Field(max_length=150)
    descripcion: Optional[str] = Field(default=None)
    activo: bool = Field(default=True)
    creado_en: Optional[datetime] = Field(default_factory=datetime.now)
    actualizado_en: Optional[datetime] = Field(default_factory=datetime.now)


class RecetaDetalle(SQLModel, table=True):
    __tablename__ = "receta_detalle"

    id: Optional[int] = Field(default=None, primary_key=True)
    receta_id: int = Field(foreign_key="receta.id")
    producto_id: int = Field(foreign_key="producto.id")
    cantidad: Decimal = Field(max_digits=12, decimal_places=3)
    activo: bool = Field(default=True)
    creado_en: Optional[datetime] = Field(default_factory=datetime.now)
    actualizado_en: Optional[datetime] = Field(default_factory=datetime.now)


class ProduccionDiaria(SQLModel, table=True):
    __tablename__ = "produccion_diaria"

    id: Optional[int] = Field(default=None, primary_key=True)
    receta_id: int = Field(foreign_key="receta.id")
    fecha: date
    cantidad_producida: Decimal = Field(max_digits=12, decimal_places=3)
    usuario_id: Optional[int] = Field(default=None, foreign_key="usuario.id")
    observaciones: Optional[str] = Field(default=None)
    activo: bool = Field(default=True)
    creado_en: Optional[datetime] = Field(default_factory=datetime.now)
    actualizado_en: Optional[datetime] = Field(default_factory=datetime.now)


class ProduccionDetalle(SQLModel, table=True):
    __tablename__ = "produccion_detalle"

    id: Optional[int] = Field(default=None, primary_key=True)
    produccion_id: int = Field(foreign_key="produccion_diaria.id")
    lote_id: int = Field(foreign_key="lote_inventario.id")
    cantidad: Decimal = Field(max_digits=12, decimal_places=3)
    activo: bool = Field(default=True)
    creado_en: Optional[datetime] = Field(default_factory=datetime.now)
    actualizado_en: Optional[datetime] = Field(default_factory=datetime.now)


class AlertaInventario(SQLModel, table=True):
    __tablename__ = "alerta_inventario"

    id: Optional[int] = Field(default=None, primary_key=True)
    tipo_id: int = Field(foreign_key="tipo.id")
    producto_id: int = Field(foreign_key="producto.id")
    mensaje: str
    leida: bool = Field(default=False)
    fecha_leida: Optional[datetime] = Field(default=None)
    activo: bool = Field(default=True)
    creado_en: Optional[datetime] = Field(default_factory=datetime.now)
    actualizado_en: Optional[datetime] = Field(default_factory=datetime.now)
