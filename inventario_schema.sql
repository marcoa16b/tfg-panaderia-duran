-- =====================================================
-- Autor: Noemy Alvarado Quesada - Eikling Davila Mercado
-- Proyecto: Sistema de Gestión de Inventario
-- =====================================================


-- =====================================================
-- TABLAS DE UBICACIÓN GEOGRÁFICA
-- =====================================================

-- Tabla de provincias
CREATE TABLE provincia (
  id SERIAL PRIMARY KEY,
  nombre VARCHAR(100) UNIQUE NOT NULL,
  activo BOOLEAN DEFAULT TRUE,
  creado_en TIMESTAMP DEFAULT now(),
  actualizado_en TIMESTAMP DEFAULT now()
);

-- Tabla de cantones
CREATE TABLE canton (
  id SERIAL PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  provincia_id INTEGER NOT NULL,
  activo BOOLEAN DEFAULT TRUE,
  creado_en TIMESTAMP DEFAULT now(),
  actualizado_en TIMESTAMP DEFAULT now(),

  CONSTRAINT fk_canton_provincia
  FOREIGN KEY (provincia_id) REFERENCES provincia(id)
);

-- Tabla de distritos
CREATE TABLE distrito (
  id SERIAL PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  canton_id INTEGER NOT NULL,
  activo BOOLEAN DEFAULT TRUE,
  creado_en TIMESTAMP DEFAULT now(),
  actualizado_en TIMESTAMP DEFAULT now(),

  CONSTRAINT fk_distrito_canton
  FOREIGN KEY (canton_id) REFERENCES canton(id)
);


-- =====================================================
-- TABLA GENERAL DE LISTAS DE TIPOS
-- =====================================================

-- Lista de grupos de tipos (alertas, entradas, salidas)
CREATE TABLE list_tipo (
  id SERIAL PRIMARY KEY,
  nombre VARCHAR(50) UNIQUE NOT NULL,
  descripcion TEXT,
  activo BOOLEAN DEFAULT TRUE,
  creado_en TIMESTAMP DEFAULT now(),
  actualizado_en TIMESTAMP DEFAULT now()
);

-- Tipos pertenecientes a cada lista de grupos de tipos
CREATE TABLE tipo (
  id SERIAL PRIMARY KEY,
  list_tipo_id INTEGER NOT NULL,
  nombre VARCHAR(50) NOT NULL,
  descripcion TEXT,
  activo BOOLEAN DEFAULT TRUE,
  creado_en TIMESTAMP DEFAULT now(),
  actualizado_en TIMESTAMP DEFAULT now(),

  CONSTRAINT fk_tipo_lista
  FOREIGN KEY (list_tipo_id) REFERENCES list_tipo(id)
);


-- =====================================================
-- TABLAS DE USUARIO Y ROLES
-- =====================================================

-- Roles del sistema
CREATE TABLE rol (
  id SERIAL PRIMARY KEY,
  nombre VARCHAR(50) UNIQUE NOT NULL,
  descripcion TEXT,
  activo BOOLEAN DEFAULT TRUE,
  creado_en TIMESTAMP DEFAULT now(),
  actualizado_en TIMESTAMP DEFAULT now()
);

-- Usuarios del sistema
CREATE TABLE usuario (
  id SERIAL PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  correo VARCHAR(150) UNIQUE NOT NULL,
  contrasena_hash VARCHAR(255) NOT NULL,
  rol_id INTEGER NOT NULL,
  activo BOOLEAN DEFAULT TRUE,
  creado_en TIMESTAMP DEFAULT now(),
  actualizado_en TIMESTAMP DEFAULT now(),

  CONSTRAINT fk_usuario_rol
  FOREIGN KEY (rol_id) REFERENCES rol(id)
);


-- =====================================================
-- CLASIFICACIÓN DE PRODUCTOS
-- =====================================================

-- Categorías de productos
CREATE TABLE categoria_producto (
  id SERIAL PRIMARY KEY,
  nombre VARCHAR(100) UNIQUE NOT NULL,
  descripcion TEXT,
  activo BOOLEAN DEFAULT TRUE,
  creado_en TIMESTAMP DEFAULT now(),
  actualizado_en TIMESTAMP DEFAULT now()
);

-- Unidades de medida de productos
CREATE TABLE unidad_medida (
  id SERIAL PRIMARY KEY,
  nombre VARCHAR(50) UNIQUE NOT NULL,
  abreviatura VARCHAR(10) UNIQUE NOT NULL,
  activo BOOLEAN DEFAULT TRUE,
  creado_en TIMESTAMP DEFAULT now(),
  actualizado_en TIMESTAMP DEFAULT now()
);


-- =====================================================
-- TABLA DE PROVEEDORES
-- =====================================================

-- Información de proveedores
CREATE TABLE proveedor (
  id SERIAL PRIMARY KEY,
  nombre VARCHAR(150) NOT NULL,
  telefono VARCHAR(20),
  correo VARCHAR(150),
  distrito_id INTEGER,
  direccion_exacta TEXT,
  notas TEXT,
  activo BOOLEAN DEFAULT TRUE,
  creado_en TIMESTAMP DEFAULT now(),
  actualizado_en TIMESTAMP DEFAULT now(),

  CONSTRAINT fk_proveedor_distrito
  FOREIGN KEY (distrito_id) REFERENCES distrito(id)
);


-- =====================================================
-- TABLA DE PRODUCTOS
-- =====================================================

-- Catálogo general de productos del inventario
CREATE TABLE producto (
  id SERIAL PRIMARY KEY,
  nombre VARCHAR(150) NOT NULL,
  descripcion TEXT,
  categoria_id INTEGER NOT NULL,
  unidad_medida_id INTEGER NOT NULL,
  stock_minimo DECIMAL(12,3) DEFAULT 0,
  stock_actual DECIMAL(12,3) DEFAULT 0,
  ubicacion VARCHAR(100),
  imagen_url VARCHAR(500),
  activo BOOLEAN DEFAULT TRUE,
  creado_en TIMESTAMP DEFAULT now(),
  actualizado_en TIMESTAMP DEFAULT now(),

  CONSTRAINT fk_producto_categoria
  FOREIGN KEY (categoria_id) REFERENCES categoria_producto(id),

  CONSTRAINT fk_producto_unidad
  FOREIGN KEY (unidad_medida_id) REFERENCES unidad_medida(id)
);


-- =====================================================
-- TABLA DE ENTRADAS DE INVENTARIO
-- =====================================================

-- Registro general de entradas al inventario
CREATE TABLE entrada_inventario (
  id SERIAL PRIMARY KEY,
  tipo_id INTEGER NOT NULL,
  proveedor_id INTEGER,
  fecha DATE NOT NULL,
  numero_factura VARCHAR(50),
  observaciones TEXT,
  usuario_id INTEGER,
  activo BOOLEAN DEFAULT TRUE,
  creado_en TIMESTAMP DEFAULT now(),
  actualizado_en TIMESTAMP DEFAULT now(),

  CONSTRAINT fk_entrada_tipo
  FOREIGN KEY (tipo_id) REFERENCES tipo(id),

  CONSTRAINT fk_entrada_proveedor
  FOREIGN KEY (proveedor_id) REFERENCES proveedor(id),

  CONSTRAINT fk_entrada_usuario
  FOREIGN KEY (usuario_id) REFERENCES usuario(id)
);


-- =====================================================
-- TABLA DE LOTES DE INVENTARIO
-- =====================================================

-- Cada lote representa un ingreso específico de producto (detalle de entrada)
CREATE TABLE lote_inventario (
  id SERIAL PRIMARY KEY,
  entrada_id INTEGER NOT NULL,
  producto_id INTEGER NOT NULL,
  codigo_lote VARCHAR(50),
  cantidad DECIMAL(12,3) NOT NULL,
  precio_unitario DECIMAL(12,2),
  fecha_vencimiento DATE,
  activo BOOLEAN DEFAULT TRUE,
  creado_en TIMESTAMP DEFAULT now(),
  actualizado_en TIMESTAMP DEFAULT now(),

  CONSTRAINT fk_lote_entrada
  FOREIGN KEY (entrada_id) REFERENCES entrada_inventario(id),

  CONSTRAINT fk_lote_producto
  FOREIGN KEY (producto_id) REFERENCES producto(id)
);


-- =====================================================
-- TABLA DE SALIDAS DE INVENTARIO
-- =====================================================

-- Registro general de salidas de inventario
CREATE TABLE salida_inventario (
  id SERIAL PRIMARY KEY,
  tipo_id INTEGER NOT NULL,
  fecha DATE NOT NULL,
  observaciones TEXT,
  usuario_id INTEGER,
  activo BOOLEAN DEFAULT TRUE,
  creado_en TIMESTAMP DEFAULT now(),
  actualizado_en TIMESTAMP DEFAULT now(),

  CONSTRAINT fk_salida_tipo
  FOREIGN KEY (tipo_id) REFERENCES tipo(id),

  CONSTRAINT fk_salida_usuario
  FOREIGN KEY (usuario_id) REFERENCES usuario(id)
);


-- =====================================================
-- DETALLE DE SALIDA
-- =====================================================

-- Productos que salen del inventario
CREATE TABLE detalle_salida_inventario (
  id SERIAL PRIMARY KEY,
  salida_id INTEGER NOT NULL,
  lote_id INTEGER NOT NULL,
  cantidad DECIMAL(12,3) NOT NULL,
  motivo TEXT,
  activo BOOLEAN DEFAULT TRUE,
  creado_en TIMESTAMP DEFAULT now(),
  actualizado_en TIMESTAMP DEFAULT now(),

  CONSTRAINT fk_detalle_salida
  FOREIGN KEY (salida_id) REFERENCES salida_inventario(id),

  CONSTRAINT fk_detalle_salida_lote
  FOREIGN KEY (lote_id) REFERENCES lote_inventario(id)
);


-- =====================================================
-- TABLAS DE RECETAS
-- =====================================================

-- Recetas de productos elaborados
CREATE TABLE receta (
  id SERIAL PRIMARY KEY,
  producto_id INTEGER NOT NULL,
  nombre VARCHAR(150) NOT NULL,
  descripcion TEXT,
  activo BOOLEAN DEFAULT TRUE,
  creado_en TIMESTAMP DEFAULT now(),
  actualizado_en TIMESTAMP DEFAULT now(),

  CONSTRAINT fk_receta_producto
  FOREIGN KEY (producto_id) REFERENCES producto(id)
);

-- Ingredientes que componen cada receta
CREATE TABLE receta_detalle (
  id SERIAL PRIMARY KEY,
  receta_id INTEGER NOT NULL,
  producto_id INTEGER NOT NULL,
  cantidad DECIMAL(12,3) NOT NULL,
  activo BOOLEAN DEFAULT TRUE,
  creado_en TIMESTAMP DEFAULT now(),
  actualizado_en TIMESTAMP DEFAULT now(),

  CONSTRAINT fk_receta_detalle_receta
  FOREIGN KEY (receta_id) REFERENCES receta(id),

  CONSTRAINT fk_receta_detalle_producto
  FOREIGN KEY (producto_id) REFERENCES producto(id),

  CONSTRAINT uq_receta_producto
  UNIQUE (receta_id, producto_id)
);


-- =====================================================
-- TABLAS DE PRODUCCIÓN
-- =====================================================

-- Registro de procesos de producción diaria
CREATE TABLE produccion_diaria (
  id SERIAL PRIMARY KEY,
  receta_id INTEGER NOT NULL,
  fecha DATE NOT NULL,
  cantidad_producida DECIMAL(12,3) NOT NULL,
  usuario_id INTEGER,
  observaciones TEXT,
  activo BOOLEAN DEFAULT TRUE,
  creado_en TIMESTAMP DEFAULT now(),
  actualizado_en TIMESTAMP DEFAULT now(),

  CONSTRAINT fk_produccion_receta
  FOREIGN KEY (receta_id) REFERENCES receta(id),

  CONSTRAINT fk_produccion_usuario
  FOREIGN KEY (usuario_id) REFERENCES usuario(id)
);

-- Ingredientes consumidos en cada producción (trazabilidad por lote)
CREATE TABLE produccion_detalle (
  id SERIAL PRIMARY KEY,
  produccion_id INTEGER NOT NULL,
  lote_id INTEGER NOT NULL,
  cantidad DECIMAL(12,3) NOT NULL,
  activo BOOLEAN DEFAULT TRUE,
  creado_en TIMESTAMP DEFAULT now(),
  actualizado_en TIMESTAMP DEFAULT now(),

  CONSTRAINT fk_produccion_detalle_produccion
  FOREIGN KEY (produccion_id) REFERENCES produccion_diaria(id),

  CONSTRAINT fk_produccion_detalle_lote
  FOREIGN KEY (lote_id) REFERENCES lote_inventario(id)
);


-- =====================================================
-- TABLA DE ALERTAS DE INVENTARIO
-- =====================================================

-- Alertas generadas por el sistema
CREATE TABLE alerta_inventario (
  id SERIAL PRIMARY KEY,
  tipo_id INTEGER NOT NULL,
  producto_id INTEGER NOT NULL,
  mensaje TEXT NOT NULL,
  leida BOOLEAN DEFAULT FALSE,
  fecha_leida TIMESTAMP,
  activo BOOLEAN DEFAULT TRUE,
  creado_en TIMESTAMP DEFAULT now(),
  actualizado_en TIMESTAMP DEFAULT now(),

  CONSTRAINT fk_alerta_tipo
  FOREIGN KEY (tipo_id) REFERENCES tipo(id),

  CONSTRAINT fk_alerta_producto
  FOREIGN KEY (producto_id) REFERENCES producto(id)
);


-- =====================================================
-- VISTA: CONSUMO ANUAL POR PRODUCTO
-- =====================================================

CREATE VIEW v_consumo_anual AS
SELECT
    p.id AS producto_id,
    p.nombre AS producto_nombre,
    COALESCE(SUM(ds.cantidad), 0) AS total_consumido
FROM producto p
LEFT JOIN lote_inventario li ON li.producto_id = p.id
LEFT JOIN detalle_salida_inventario ds ON ds.lote_id = li.id
    AND ds.activo = TRUE
LEFT JOIN salida_inventario si ON si.id = ds.salida_id
    AND si.fecha >= DATE_TRUNC('year', CURRENT_DATE)
    AND si.fecha < DATE_TRUNC('year', CURRENT_DATE) + INTERVAL '1 year'
WHERE p.activo = TRUE
GROUP BY p.id, p.nombre;
