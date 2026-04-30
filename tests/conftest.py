import pytest
import reflex as rx
from contextlib import contextmanager
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlmodel import SQLModel, Session, create_engine, select

from dev.models import models as _  # noqa: F401 — ensure all models registered
from dev.models.models import (
    Rol, ListTipo, Tipo, UnidadMedida, CategoriaProducto,
    Provincia, Canton, Distrito, Usuario, Producto,
    EntradaInventario, LoteInventario, SalidaInventario,
    DetalleSalidaInventario, Receta, RecetaDetalle,
    ProduccionDiaria, ProduccionDetalle, AlertaInventario,
)
from dev.core.security import hash_password

_test_engine = create_engine("sqlite:///:memory:", echo=False)


@contextmanager
def _test_session():
    with Session(_test_engine) as s:
        yield s


@pytest.fixture(autouse=True)
def _patch_rx_session():
    original = rx.session
    rx.session = _test_session
    yield
    rx.session = original


@pytest.fixture(autouse=True)
def _setup_test_db():
    SQLModel.metadata.create_all(_test_engine)
    yield
    SQLModel.metadata.drop_all(_test_engine)


@pytest.fixture
def seed_basic():
    with rx.session() as s:
        rol = Rol(nombre="Administrador", descripcion="Admin")
        s.add(rol)
        s.flush()

        lt_entrada = ListTipo(nombre="entrada", descripcion="Entradas")
        lt_salida = ListTipo(nombre="salida", descripcion="Salidas")
        lt_alerta = ListTipo(nombre="alerta", descripcion="Alertas")
        s.add(lt_entrada)
        s.add(lt_salida)
        s.add(lt_alerta)
        s.flush()

        tipos = [
            Tipo(list_tipo_id=lt_entrada.id, nombre="Compra"),
            Tipo(list_tipo_id=lt_entrada.id, nombre="Donación"),
            Tipo(list_tipo_id=lt_entrada.id, nombre="Ajuste positivo"),
            Tipo(list_tipo_id=lt_salida.id, nombre="Consumo"),
            Tipo(list_tipo_id=lt_salida.id, nombre="Dañado"),
            Tipo(list_tipo_id=lt_salida.id, nombre="Vencido"),
            Tipo(list_tipo_id=lt_salida.id, nombre="Ajuste negativo"),
            Tipo(list_tipo_id=lt_alerta.id, nombre="Bajo stock"),
            Tipo(list_tipo_id=lt_alerta.id, nombre="Próximo a vencer"),
        ]
        for t in tipos:
            s.add(t)
        s.flush()

        um = UnidadMedida(nombre="Kilogramo", abreviatura="kg")
        s.add(um)
        s.flush()

        cat = CategoriaProducto(nombre="Harinas", descripcion="Harinas")
        s.add(cat)
        s.flush()

        admin = Usuario(
            nombre="Admin Test",
            correo="admin@test.com",
            contrasena_hash=hash_password("Admin123!"),
            rol_id=rol.id,
        )
        s.add(admin)
        s.commit()

        return {
            "rol_id": rol.id,
            "lt_entrada_id": lt_entrada.id,
            "lt_salida_id": lt_salida.id,
            "lt_alerta_id": lt_alerta.id,
            "tipo_compra_id": tipos[0].id,
            "tipo_consumo_id": tipos[3].id,
            "tipo_daniado_id": tipos[4].id,
            "tipo_vencido_id": tipos[5].id,
            "tipo_bajo_stock_id": tipos[7].id,
            "tipo_proximo_vencer_id": tipos[8].id,
            "um_id": um.id,
            "cat_id": cat.id,
            "admin_id": admin.id,
        }


@pytest.fixture
def seed_producto(seed_basic):
    from dev.repositories.producto_repo import ProductoRepository

    producto = ProductoRepository.create(
        nombre="Harina de trigo",
        descripcion="Harina blanca",
        categoria_id=seed_basic["cat_id"],
        unidad_medida_id=seed_basic["um_id"],
        stock_minimo=Decimal("10"),
        stock_actual=Decimal("0"),
    )
    seed_basic["producto_id"] = producto.id
    return seed_basic


@pytest.fixture
def seed_entrada(seed_producto):
    from dev.repositories.entrada_repo import EntradaRepository

    result = EntradaRepository.create_with_lotes(
        entrada_data={
            "tipo_id": seed_producto["tipo_compra_id"],
            "fecha": date.today(),
        },
        lotes_data=[
            {
                "producto_id": seed_producto["producto_id"],
                "codigo_lote": "L001",
                "cantidad": Decimal("100"),
                "precio_unitario": Decimal("1.50"),
                "fecha_vencimiento": date.today() + __import__("datetime").timedelta(days=30),
            }
        ],
    )
    seed_producto["entrada_id"] = result["entrada"].id
    seed_producto["lote_id"] = result["lotes"][0].id

    from dev.repositories.producto_repo import ProductoRepository
    for lote in result["lotes"]:
        ProductoRepository.update_stock(lote.producto_id, lote.cantidad)

    return seed_producto
