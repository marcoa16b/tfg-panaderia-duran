"""
seed_demo.py — Datos de demostración para Panadería Durán.

Pobla la BD con datos realistas que permiten visualizar reportes,
estadísticas y funcionalidad completa del sistema.

Activación
----------
Variable de entorno ``SEED_DEMO=true``.  Ver ``bootstrap.py``.

Idempotente
-----------
Verifica la existencia de un proveedor marcador ``[Demo]`` antes
de insertar cualquier dato.  Seguro ejecutar múltiples veces.

Datos que se insertan
---------------------
1.  5  proveedores de demo
2.  23 productos (17 insumos + 6 productos finales)
3.  6  recetas con detalles de ingredientes
4.  ~10 entradas de inventario con lotes (Nov 2025 – Abr 2026)
5.  ~30 registros de producción con consumo FIFO de lotes
6.  4  salidas por daño / vencimiento
7.  Stock actual recalculado para cada producto
"""

import logging
from datetime import date
from decimal import Decimal

import reflex as rx
from sqlmodel import select

from dev.models.models import (
    CategoriaProducto,
    DetalleSalidaInventario,
    EntradaInventario,
    LoteInventario,
    ListTipo,
    Producto,
    ProduccionDiaria,
    ProduccionDetalle,
    Proveedor,
    Receta,
    RecetaDetalle,
    SalidaInventario,
    Tipo,
    UnidadMedida,
    Usuario,
)

logger = logging.getLogger("dev.core.seed_demo")

_DEMO_MARKER = "[Demo] Harinas del Valle"


def _first(session, model, **kw):
    stmt = select(model)
    for k, v in kw.items():
        stmt = stmt.where(getattr(model, k) == v)
    return session.exec(stmt).first()


def run_demo_seed() -> dict[str, int]:
    with rx.session() as session:
        if _first(session, Proveedor, nombre=_DEMO_MARKER):
            logger.info("Demo seed ya ejecutado — saltando")
            return {"demo": 0}

        cats = {c.nombre: c for c in session.exec(select(CategoriaProducto)).all()}
        ums = {u.nombre: u for u in session.exec(select(UnidadMedida)).all()}

        def _tipo(grupo: str, nombre: str) -> int | None:
            lt = _first(session, ListTipo, nombre=grupo)
            if not lt:
                return None
            t = _first(session, Tipo, list_tipo_id=lt.id, nombre=nombre)
            return t.id if t else None

        admin = _first(session, Usuario, correo="admin@panaderiaduran.com")
        admin_id = admin.id if admin else None

        tipo_compra = _tipo("entrada", "Compra")
        tipo_danado = _tipo("salida", "Dañado")
        tipo_vencido = _tipo("salida", "Vencido")

        results: dict[str, int] = {}
        provs: dict[str, Proveedor] = {}
        prods: dict[str, Producto] = {}
        recs: dict[str, Receta] = {}
        rec_dets: dict[str, list[tuple[str, Decimal]]] = {}
        lotes_by_prod: dict[str, list[LoteInventario]] = {}
        lote_used: dict[int, Decimal] = {}

        # ── 1. Proveedores ────────────────────────────────────────────────
        _create_proveedores(session, provs)
        results["proveedores"] = len(provs)

        # ── 2. Productos ──────────────────────────────────────────────────
        _create_productos(session, cats, ums, prods)
        prod_by_id: dict[int, str] = {p.id: n for n, p in prods.items()}
        results["productos"] = len(prods)

        # ── 3. Recetas ────────────────────────────────────────────────────
        _create_recetas(session, prods, recs, rec_dets)
        results["recetas"] = len(recs)

        # ── 4. Entradas + Lotes ───────────────────────────────────────────
        entradas_count = _create_entradas(
            session, provs, prods, tipo_compra, admin_id, lotes_by_prod
        )
        results["entradas"] = entradas_count
        results["lotes"] = sum(len(v) for v in lotes_by_prod.values())

        # ── 5. Producción + ProduccionDetalle (FIFO) ─────────────────────
        prod_count = _create_produccion(
            session, recs, rec_dets, prods, prod_by_id,
            lotes_by_prod, lote_used, admin_id,
        )
        results["produccion"] = prod_count

        # ── 6. Salidas (daño / vencimiento) ───────────────────────────────
        sal_count = _create_salidas(
            session, prods, lotes_by_prod, lote_used,
            tipo_danado, tipo_vencido, admin_id,
        )
        results["salidas"] = sal_count

        # ── 7. Recalcular stock_actual ────────────────────────────────────
        _recalc_stock(session, prods, lotes_by_prod, lote_used)

        session.commit()
        logger.info("Demo seed completado — %s", results)
        return results


# ═══════════════════════════════════════════════════════════════════════════
# PROVEEDORES
# ═══════════════════════════════════════════════════════════════════════════

_PROVEEDORES_DATA = [
    ("[Demo] Harinas del Valle", "2222-0001", "ventas@harinasvalle.cr", "Distribuidor principal de harinas"),
    ("[Demo] Azucarera Central", "2222-0002", "pedidos@azucareracentral.cr", "Azúcar y endulzantes"),
    ("[Demo] Lácteos La Fuente", "2222-0003", "info@lacteosfuente.cr", "Leche, crema, mantequilla"),
    ("[Demo] Empaques del Norte", "2222-0004", "ventas@empaquesnorte.cr", "Bolsas, cajas, etiquetas"),
    ("[Demo] Rellenos Tropicales", "2222-0005", "pedidos@rellenostropicales.cr", "Rellenos y cremas para repostería"),
]


def _create_proveedores(session, provs: dict):
    for nombre, tel, correo, notas in _PROVEEDORES_DATA:
        p = Proveedor(nombre=nombre, telefono=tel, correo=correo, notas=notas)
        session.add(p)
        session.flush()
        provs[nombre] = p


# ═══════════════════════════════════════════════════════════════════════════
# PRODUCTOS
# ═══════════════════════════════════════════════════════════════════════════

_PRODUCTOS_DATA = [
    # (nombre, descripcion, categoria, unidad_medida, stock_minimo, ubicacion)
    # ── Insumos ──
    ("Harina de trigo", "Harina de trigo blanqueada, uso panadero", "Harinas", "Kilogramo", 50, "Almacén A"),
    ("Harina integral", "Harina de trigo integral 100%", "Harinas", "Kilogramo", 20, "Almacén A"),
    ("Azúcar blanca", "Azúcar blanca refinada", "Azúcares", "Kilogramo", 30, "Almacén A"),
    ("Azúcar morena", "Azúcar morena sin refinar", "Azúcares", "Kilogramo", 15, "Almacén A"),
    ("Mantequilla", "Mantequilla sin sal premium", "Grasas", "Kilogramo", 10, "Refrigerador"),
    ("Margarina", "Margarina para pastelería", "Grasas", "Kilogramo", 8, "Refrigerador"),
    ("Aceite vegetal", "Aceite vegetal comestible", "Grasas", "Litro", 5, "Almacén B"),
    ("Leche entera", "Leche entera pasteurizada", "Lácteos", "Litro", 20, "Refrigerador"),
    ("Crema de leche", "Crema de leche para repostería", "Lácteos", "Litro", 5, "Refrigerador"),
    ("Huevos", "Huevos de gallina grado AA", "Huevos", "Unidad", 60, "Refrigerador"),
    ("Levadura seca", "Levadura seca instantánea", "Levaduras", "Kilogramo", 2, "Almacén B"),
    ("Sal", "Sal fina yodada", "Condimentos", "Kilogramo", 5, "Almacén B"),
    ("Vainilla líquida", "Extracto de vainilla natural", "Condimentos", "Litro", 1, "Almacén B"),
    ("Relleno de crema", "Crema pastelera para relleno", "Rellenos", "Kilogramo", 5, "Refrigerador"),
    ("Relleno de guayaba", "Relleno de guayaba tropical", "Rellenos", "Kilogramo", 5, "Refrigerador"),
    ("Bolsas para pan", "Bolsas plásticas para empanar", "Empaques", "Unidad", 200, "Almacén C"),
    ("Cajas para pastel", "Cajas de cartón para pastel", "Empaques", "Unidad", 50, "Almacén C"),
    # ── Productos finales ──
    ("Pan blanco", "Pan blanco de molde artesanal", "Producción", "Unidad", 30, "Exhibidor"),
    ("Pan integral", "Pan integral de molde", "Producción", "Unidad", 20, "Exhibidor"),
    ("Pan dulce", "Pan dulce tradicional", "Producción", "Unidad", 25, "Exhibidor"),
    ("Pastel de chocolate", "Pastel de chocolate con ganache", "Producción", "Unidad", 5, "Refrigerador exhibidor"),
    ("Rosquillas", "Rosquillas crujientes tradicionales", "Producción", "Unidad", 15, "Exhibidor"),
    ("Empanadas de guayaba", "Empanadas rellenas de guayaba", "Producción", "Unidad", 20, "Exhibidor"),
]


def _create_productos(session, cats, ums, prods: dict):
    for nombre, desc, cat, um, stock_min, ubic in _PRODUCTOS_DATA:
        p = Producto(
            nombre=nombre,
            descripcion=desc,
            categoria_id=cats[cat].id,
            unidad_medida_id=ums[um].id,
            stock_minimo=Decimal(str(stock_min)),
            stock_actual=Decimal("0"),
            ubicacion=ubic,
        )
        session.add(p)
        session.flush()
        prods[nombre] = p


# ═══════════════════════════════════════════════════════════════════════════
# RECETAS
# ═══════════════════════════════════════════════════════════════════════════

_RECETAS_DATA = [
    # (producto_final, nombre_receta, descripcion, [(insumo, cant_por_unidad)])
    (
        "Pan blanco",
        "Receta Pan Blanco Artesanal",
        "Pan blanco clásico de la panadería",
        [
            ("Harina de trigo", "0.500"),
            ("Azúcar blanca", "0.020"),
            ("Mantequilla", "0.030"),
            ("Levadura seca", "0.005"),
            ("Sal", "0.005"),
            ("Huevos", "0.500"),
            ("Leche entera", "0.100"),
        ],
    ),
    (
        "Pan integral",
        "Receta Pan Integral",
        "Pan integral nutritivo",
        [
            ("Harina integral", "0.500"),
            ("Azúcar blanca", "0.020"),
            ("Mantequilla", "0.030"),
            ("Levadura seca", "0.005"),
            ("Sal", "0.005"),
            ("Huevos", "0.500"),
            ("Leche entera", "0.100"),
        ],
    ),
    (
        "Pan dulce",
        "Receta Pan Dulce Tradicional",
        "Pan dulce esponjoso con vainilla",
        [
            ("Harina de trigo", "0.400"),
            ("Azúcar blanca", "0.080"),
            ("Mantequilla", "0.050"),
            ("Huevos", "1.000"),
            ("Levadura seca", "0.005"),
            ("Vainilla líquida", "0.005"),
            ("Leche entera", "0.100"),
        ],
    ),
    (
        "Pastel de chocolate",
        "Receta Pastel de Chocolate",
        "Pastel三层de chocolate con crema",
        [
            ("Harina de trigo", "0.300"),
            ("Azúcar blanca", "0.150"),
            ("Huevos", "3.000"),
            ("Mantequilla", "0.100"),
            ("Crema de leche", "0.200"),
            ("Relleno de crema", "0.150"),
        ],
    ),
    (
        "Rosquillas",
        "Receta Rosquillas Crujientes",
        "Rosquillas tradicionales crujientes",
        [
            ("Harina de trigo", "0.300"),
            ("Azúcar blanca", "0.050"),
            ("Mantequilla", "0.030"),
            ("Huevos", "1.000"),
            ("Levadura seca", "0.003"),
        ],
    ),
    (
        "Empanadas de guayaba",
        "Receta Empanadas de Guayaba",
        "Empanadas dulces rellenas de guayaba",
        [
            ("Harina de trigo", "0.250"),
            ("Mantequilla", "0.020"),
            ("Sal", "0.003"),
            ("Huevos", "0.500"),
            ("Relleno de guayaba", "0.100"),
        ],
    ),
]


def _create_recetas(session, prods, recs: dict, rec_dets: dict):
    for prod_final, nombre, desc, ingredientes in _RECETAS_DATA:
        r = Receta(
            producto_id=prods[prod_final].id,
            nombre=nombre,
            descripcion=desc,
        )
        session.add(r)
        session.flush()
        recs[prod_final] = r
        rec_dets[prod_final] = ingredientes
        for insumo_nombre, cantidad_str in ingredientes:
            rd = RecetaDetalle(
                receta_id=r.id,
                producto_id=prods[insumo_nombre].id,
                cantidad=Decimal(cantidad_str),
            )
            session.add(rd)
        session.flush()


# ═══════════════════════════════════════════════════════════════════════════
# ENTRADAS + LOTES
# ═══════════════════════════════════════════════════════════════════════════

_ENTRADAS_DATA = [
    # (fecha, proveedor_key, factura, obs, [(producto, cantidad, precio, vencimiento)])
    (
        date(2025, 11, 1), "[Demo] Harinas del Valle", "FAC-2025-001",
        "Pedido mensual noviembre",
        [
            ("Harina de trigo", "150", "1200", date(2026, 5, 15)),
            ("Harina integral", "40", "1800", date(2026, 4, 20)),
        ],
    ),
    (
        date(2025, 11, 3), "[Demo] Azucarera Central", "FAC-2025-002",
        "Azúcar noviembre",
        [
            ("Azúcar blanca", "60", "800", date(2026, 11, 1)),
            ("Azúcar morena", "20", "750", date(2026, 11, 1)),
        ],
    ),
    (
        date(2025, 11, 5), "[Demo] Lácteos La Fuente", "FAC-2025-003",
        "Lácteos y huevos noviembre",
        [
            ("Mantequilla", "20", "3500", date(2026, 2, 1)),
            ("Leche entera", "40", "900", date(2025, 12, 20)),
            ("Crema de leche", "6", "2500", date(2025, 12, 15)),
            ("Huevos", "360", "280", date(2025, 12, 30)),
        ],
    ),
    (
        date(2025, 12, 1), "[Demo] Harinas del Valle", "FAC-2025-004",
        "Pedido mensual diciembre",
        [
            ("Harina de trigo", "120", "1200", date(2026, 6, 1)),
            ("Harina integral", "30", "1800", date(2026, 5, 10)),
            ("Levadura seca", "3", "5000", date(2026, 6, 15)),
        ],
    ),
    (
        date(2025, 12, 5), "[Demo] Lácteos La Fuente", "FAC-2025-005",
        "Lácteos diciembre",
        [
            ("Mantequilla", "15", "3500", date(2026, 3, 1)),
            ("Leche entera", "35", "900", date(2026, 1, 20)),
            ("Huevos", "300", "280", date(2026, 1, 25)),
        ],
    ),
    (
        date(2026, 1, 6), "[Demo] Harinas del Valle", "FAC-2026-001",
        "Pedido mensual enero",
        [
            ("Harina de trigo", "100", "1250", date(2026, 7, 1)),
            ("Levadura seca", "2", "5000", date(2026, 7, 15)),
            ("Sal", "8", "500", date(2027, 1, 1)),
        ],
    ),
    (
        date(2026, 1, 10), "[Demo] Azucarera Central", "FAC-2026-002",
        "Azúcar enero",
        [
            ("Azúcar blanca", "40", "800", date(2027, 1, 1)),
        ],
    ),
    (
        date(2026, 2, 1), "[Demo] Harinas del Valle", "FAC-2026-003",
        "Pedido mensual febrero",
        [
            ("Harina de trigo", "130", "1250", date(2026, 8, 1)),
            ("Harina integral", "45", "1800", date(2026, 7, 1)),
            ("Vainilla líquida", "1.5", "8000", date(2027, 6, 1)),
        ],
    ),
    (
        date(2026, 2, 5), "[Demo] Lácteos La Fuente", "FAC-2026-004",
        "Lácteos febrero",
        [
            ("Mantequilla", "20", "3500", date(2026, 5, 1)),
            ("Leche entera", "30", "900", date(2026, 3, 15)),
            ("Huevos", "300", "280", date(2026, 3, 10)),
            ("Crema de leche", "4", "2500", date(2026, 3, 20)),
        ],
    ),
    (
        date(2026, 3, 1), "[Demo] Rellenos Tropicales", "FAC-2026-005",
        "Rellenos marzo",
        [
            ("Relleno de crema", "8", "3000", date(2026, 9, 1)),
            ("Relleno de guayaba", "20", "2500", date(2026, 9, 1)),
        ],
    ),
    (
        date(2026, 3, 5), "[Demo] Harinas del Valle", "FAC-2026-006",
        "Pedido mensual marzo",
        [
            ("Harina de trigo", "130", "1250", date(2026, 9, 1)),
            ("Levadura seca", "4", "5000", date(2026, 9, 15)),
        ],
    ),
    (
        date(2026, 3, 8), "[Demo] Lácteos La Fuente", "FAC-2026-007",
        "Lácteos marzo",
        [
            ("Mantequilla", "18", "3500", date(2026, 6, 1)),
            ("Leche entera", "35", "900", date(2026, 5, 3)),
            ("Huevos", "300", "280", date(2026, 4, 20)),
        ],
    ),
    (
        date(2026, 4, 1), "[Demo] Harinas del Valle", "FAC-2026-008",
        "Pedido mensual abril",
        [
            ("Harina de trigo", "100", "1250", date(2026, 10, 1)),
            ("Harina integral", "30", "1800", date(2026, 9, 15)),
            ("Sal", "6", "500", date(2027, 4, 1)),
        ],
    ),
    (
        date(2026, 4, 5), "[Demo] Lácteos La Fuente", "FAC-2026-009",
        "Lácteos abril",
        [
            ("Mantequilla", "15", "3500", date(2026, 7, 1)),
            ("Leche entera", "25", "900", date(2026, 5, 5)),
            ("Huevos", "240", "280", date(2026, 5, 15)),
            ("Crema de leche", "5", "2500", date(2026, 5, 10)),
        ],
    ),
    (
        date(2026, 4, 8), "[Demo] Empaques del Norte", "FAC-2026-010",
        "Empaques abril",
        [
            ("Bolsas para pan", "500", "25", date(2027, 4, 1)),
            ("Cajas para pastel", "120", "350", date(2027, 4, 1)),
        ],
    ),
    (
        date(2026, 4, 10), "[Demo] Rellenos Tropicales", "FAC-2026-011",
        "Rellenos abril",
        [
            ("Relleno de crema", "6", "3000", date(2026, 10, 1)),
            ("Relleno de guayaba", "15", "2500", date(2026, 10, 1)),
        ],
    ),
    (
        date(2026, 4, 12), "[Demo] Azucarera Central", "FAC-2026-012",
        "Azúcar abril",
        [
            ("Azúcar blanca", "35", "800", date(2027, 4, 1)),
        ],
    ),
]


def _create_entradas(session, provs, prods, tipo_compra_id, admin_id, lotes_by_prod):
    count = 0
    for fecha, prov_key, factura, obs, lotes_data in _ENTRADAS_DATA:
        e = EntradaInventario(
            tipo_id=tipo_compra_id,
            proveedor_id=provs[prov_key].id if prov_key in provs else None,
            fecha=fecha,
            numero_factura=factura,
            observaciones=obs,
            usuario_id=admin_id,
        )
        session.add(e)
        session.flush()
        count += 1

        for prod_nombre, cant_str, precio_str, venc in lotes_data:
            l = LoteInventario(
                entrada_id=e.id,
                producto_id=prods[prod_nombre].id,
                codigo_lote=f"L{e.id:04d}-{prods[prod_nombre].id:03d}",
                cantidad=Decimal(cant_str),
                precio_unitario=Decimal(precio_str),
                fecha_vencimiento=venc,
            )
            session.add(l)
            session.flush()
            lotes_by_prod.setdefault(prod_nombre, []).append(l)
    session.flush()
    return count


# ═══════════════════════════════════════════════════════════════════════════
# PRODUCCIÓN (con consumo FIFO de lotes)
# ═══════════════════════════════════════════════════════════════════════════

_PRODUCCIONES_DATA = [
    # (receta_key, fecha, cantidad_producida)
    ("Pan blanco", date(2025, 11, 4), 60),
    ("Pan dulce", date(2025, 11, 6), 50),
    ("Rosquillas", date(2025, 11, 8), 35),
    ("Empanadas de guayaba", date(2025, 11, 11), 45),
    ("Pan integral", date(2025, 11, 13), 40),
    ("Pastel de chocolate", date(2025, 11, 15), 4),

    ("Pan blanco", date(2025, 12, 2), 70),
    ("Pan dulce", date(2025, 12, 4), 55),
    ("Empanadas de guayaba", date(2025, 12, 7), 50),
    ("Rosquillas", date(2025, 12, 9), 40),
    ("Pan integral", date(2025, 12, 11), 35),
    ("Pastel de chocolate", date(2025, 12, 14), 6),

    ("Pan blanco", date(2026, 1, 7), 65),
    ("Pan dulce", date(2026, 1, 9), 45),
    ("Pan integral", date(2026, 1, 12), 45),
    ("Pastel de chocolate", date(2026, 1, 15), 5),
    ("Pan blanco", date(2026, 1, 17), 55),
    ("Empanadas de guayaba", date(2026, 1, 20), 40),

    ("Pan blanco", date(2026, 2, 3), 75),
    ("Pan dulce", date(2026, 2, 6), 60),
    ("Rosquillas", date(2026, 2, 10), 30),
    ("Empanadas de guayaba", date(2026, 2, 13), 55),
    ("Pan integral", date(2026, 2, 17), 45),
    ("Pastel de chocolate", date(2026, 2, 20), 7),

    ("Pan blanco", date(2026, 3, 3), 80),
    ("Pan dulce", date(2026, 3, 6), 55),
    ("Empanadas de guayaba", date(2026, 3, 10), 50),
    ("Rosquillas", date(2026, 3, 13), 35),
    ("Pastel de chocolate", date(2026, 3, 16), 8),
    ("Pan integral", date(2026, 3, 18), 35),

    ("Pan blanco", date(2026, 4, 2), 70),
    ("Pan integral", date(2026, 4, 4), 40),
    ("Pan dulce", date(2026, 4, 7), 50),
    ("Pastel de chocolate", date(2026, 4, 9), 6),
    ("Empanadas de guayaba", date(2026, 4, 11), 45),
    ("Pan blanco", date(2026, 4, 15), 60),
    ("Rosquillas", date(2026, 4, 17), 30),
]


def _create_produccion(
    session, recs, rec_dets, prods, prod_by_id,
    lotes_by_prod, lote_used, admin_id,
):
    count = 0
    for receta_key, fecha, cantidad in _PRODUCCIONES_DATA:
        if receta_key not in recs:
            continue
        receta = recs[receta_key]
        pd = ProduccionDiaria(
            receta_id=receta.id,
            fecha=fecha,
            cantidad_producida=Decimal(str(cantidad)),
            usuario_id=admin_id,
        )
        session.add(pd)
        session.flush()
        count += 1

        ingredientes = rec_dets.get(receta_key, [])
        for insumo_nombre, qty_str in ingredientes:
            total_needed = Decimal(qty_str) * cantidad
            lotes = lotes_by_prod.get(insumo_nombre, [])
            remaining = total_needed
            for lote in lotes:
                if remaining <= 0:
                    break
                used = lote_used.get(lote.id, Decimal("0"))
                available = lote.cantidad - used
                if available <= 0:
                    continue
                take = min(available, remaining)
                det = ProduccionDetalle(
                    produccion_id=pd.id,
                    lote_id=lote.id,
                    cantidad=take,
                )
                session.add(det)
                lote_used[lote.id] = used + take
                remaining -= take
    session.flush()
    return count


# ═══════════════════════════════════════════════════════════════════════════
# SALIDAS (daño / vencimiento)
# ═══════════════════════════════════════════════════════════════════════════

_SALIDAS_DATA = [
    # (fecha, tipo_nombre, obs, [(producto, cantidad, motivo)])
    (date(2026, 1, 20), "Vencido", "Leche vencida encontrada en inventario", [
        ("Leche entera", "5", "Cinco litros vencidos — lote DIC"),
    ]),
    (date(2026, 2, 15), "Dañado", "Huevos rotos durante transporte interno", [
        ("Huevos", "12", "Caja caída — doce huevos rotos"),
    ]),
    (date(2026, 3, 20), "Vencido", "Harina vencida en almacén", [
        ("Harina de trigo", "8", "Lote de noviembre sin rotación"),
    ]),
    (date(2026, 4, 12), "Dañado", "Mantequilla con temperatura fuera de rango", [
        ("Mantequilla", "3", "Falla eléctrica en refrigerador"),
    ]),
]


def _create_salidas(
    session, prods, lotes_by_prod, lote_used,
    tipo_danado_id, tipo_vencido_id, admin_id,
):
    count = 0
    for fecha, tipo_nombre, obs, detalles in _SALIDAS_DATA:
        tipo_id = tipo_vencido_id if tipo_nombre == "Vencido" else tipo_danado_id
        if not tipo_id:
            continue

        s = SalidaInventario(
            tipo_id=tipo_id,
            fecha=fecha,
            observaciones=obs,
            usuario_id=admin_id,
        )
        session.add(s)
        session.flush()
        count += 1

        for prod_nombre, cant_str, motivo in detalles:
            lotes = lotes_by_prod.get(prod_nombre, [])
            remaining = Decimal(cant_str)
            for lote in lotes:
                if remaining <= 0:
                    break
                used = lote_used.get(lote.id, Decimal("0"))
                available = lote.cantidad - used
                if available <= 0:
                    continue
                take = min(available, remaining)
                ds = DetalleSalidaInventario(
                    salida_id=s.id,
                    lote_id=lote.id,
                    cantidad=take,
                    motivo=motivo,
                )
                session.add(ds)
                lote_used[lote.id] = used + take
                remaining -= take
    session.flush()
    return count


# ═══════════════════════════════════════════════════════════════════════════
# RECALCULAR STOCK
# ═══════════════════════════════════════════════════════════════════════════

def _recalc_stock(session, prods, lotes_by_prod, lote_used):
    insumo_names = {
        n for n, _, _, _, _, _ in _PRODUCTOS_DATA
        if n in {
            "Harina de trigo", "Harina integral", "Azúcar blanca", "Azúcar morena",
            "Mantequilla", "Margarina", "Aceite vegetal", "Leche entera",
            "Crema de leche", "Huevos", "Levadura seca", "Sal", "Vainilla líquida",
            "Relleno de crema", "Relleno de guayaba", "Bolsas para pan",
            "Cajas para pastel",
        }
    }

    for nombre, prod in prods.items():
        lotes = lotes_by_prod.get(nombre, [])
        if not lotes:
            continue

        if nombre in insumo_names:
            total = Decimal("0")
            for lote in lotes:
                used = lote_used.get(lote.id, Decimal("0"))
                remaining = max(lote.cantidad - used, Decimal("0"))
                total += remaining
            prod.stock_actual = total
        else:
            prod.stock_actual = Decimal("0")

        session.add(prod)

    produced_counts: dict[str, Decimal] = {}
    for receta_key, _, cantidad in _PRODUCCIONES_DATA:
        produced_counts[receta_key] = produced_counts.get(receta_key, Decimal("0")) + cantidad

    for receta_key, total in produced_counts.items():
        if receta_key in prods:
            remaining_ratio = Decimal("0.15")
            prods[receta_key].stock_actual = (total * remaining_ratio).quantize(Decimal("1"))
            session.add(prods[receta_key])

    session.flush()
