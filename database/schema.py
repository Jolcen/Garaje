from database.db import get_connection


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        usuario TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        rol TEXT NOT NULL CHECK(rol IN ('admin', 'empleado')),
        estado TEXT NOT NULL DEFAULT 'activo' CHECK(estado IN ('activo', 'inactivo')),
        fecha_creacion TEXT NOT NULL,
        ultimo_acceso TEXT
    );

    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        telefono TEXT,
        documento TEXT,
        observacion TEXT,
        fecha_creacion TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS vehiculos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        placa TEXT NOT NULL UNIQUE,
        tipo_vehiculo TEXT NOT NULL,
        marca TEXT,
        modelo TEXT,
        color TEXT,
        cliente_id INTEGER,
        fecha_creacion TEXT NOT NULL,
        FOREIGN KEY (cliente_id) REFERENCES clientes(id)
            ON UPDATE CASCADE
            ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS tarifas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        tipo_vehiculo TEXT NOT NULL,
        tipo_cobro TEXT NOT NULL CHECK(tipo_cobro IN ('hora', 'dia')),
        monto REAL NOT NULL CHECK(monto >= 0),
        fraccion_minima INTEGER NOT NULL DEFAULT 60 CHECK(fraccion_minima > 0),
        tolerancia_min INTEGER NOT NULL DEFAULT 0 CHECK(tolerancia_min >= 0),
        estado TEXT NOT NULL DEFAULT 'activa' CHECK(estado IN ('activa', 'inactiva')),
        fecha_creacion TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS servicios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE,
        descripcion TEXT,
        precio REAL NOT NULL CHECK(precio >= 0),
        duracion_estimada INTEGER,
        estado TEXT NOT NULL DEFAULT 'activo' CHECK(estado IN ('activo', 'inactivo')),
        fecha_creacion TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS operaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_operacion TEXT NOT NULL UNIQUE,
        vehiculo_id INTEGER NOT NULL,
        cliente_id INTEGER,
        usuario_ingreso_id INTEGER NOT NULL,
        usuario_salida_id INTEGER,
        tarifa_id INTEGER NOT NULL,

        fecha_ingreso TEXT NOT NULL,
        fecha_salida TEXT,

        minutos_estadia INTEGER NOT NULL DEFAULT 0 CHECK(minutos_estadia >= 0),
        monto_parqueo REAL NOT NULL DEFAULT 0 CHECK(monto_parqueo >= 0),
        monto_servicios REAL NOT NULL DEFAULT 0 CHECK(monto_servicios >= 0),
        monto_total REAL NOT NULL DEFAULT 0 CHECK(monto_total >= 0),

        estado TEXT NOT NULL DEFAULT 'activo' CHECK(estado IN ('activo', 'finalizado', 'cancelado')),
        codigo_retiro TEXT,
        observaciones TEXT,
        motivo_cancelacion TEXT,

        FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT,

        FOREIGN KEY (cliente_id) REFERENCES clientes(id)
            ON UPDATE CASCADE
            ON DELETE SET NULL,

        FOREIGN KEY (usuario_ingreso_id) REFERENCES usuarios(id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT,

        FOREIGN KEY (usuario_salida_id) REFERENCES usuarios(id)
            ON UPDATE CASCADE
            ON DELETE SET NULL,

        FOREIGN KEY (tarifa_id) REFERENCES tarifas(id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS operacion_servicios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        operacion_id INTEGER NOT NULL,
        servicio_id INTEGER NOT NULL,
        cantidad INTEGER NOT NULL DEFAULT 1 CHECK(cantidad > 0),
        precio_unitario REAL NOT NULL CHECK(precio_unitario >= 0),
        subtotal REAL NOT NULL CHECK(subtotal >= 0),
        estado TEXT NOT NULL DEFAULT 'pendiente' CHECK(estado IN ('pendiente', 'en_proceso', 'realizado', 'cancelado')),
        observacion TEXT,

        FOREIGN KEY (operacion_id) REFERENCES operaciones(id)
            ON UPDATE CASCADE
            ON DELETE CASCADE,

        FOREIGN KEY (servicio_id) REFERENCES servicios(id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS pagos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        operacion_id INTEGER NOT NULL,
        usuario_id INTEGER NOT NULL,
        fecha_pago TEXT NOT NULL,
        metodo_pago TEXT NOT NULL CHECK(metodo_pago IN ('efectivo', 'qr', 'transferencia')),
        monto REAL NOT NULL CHECK(monto >= 0),
        observacion TEXT,

        FOREIGN KEY (operacion_id) REFERENCES operaciones(id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT,

        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS bitacora (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        accion TEXT NOT NULL,
        tabla_afectada TEXT,
        registro_id INTEGER,
        descripcion TEXT,
        fecha_evento TEXT NOT NULL,

        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            ON UPDATE CASCADE
            ON DELETE SET NULL
    );

    CREATE INDEX IF NOT EXISTS idx_vehiculos_placa ON vehiculos(placa);
    CREATE INDEX IF NOT EXISTS idx_operaciones_estado ON operaciones(estado);
    CREATE INDEX IF NOT EXISTS idx_operaciones_fecha_ingreso ON operaciones(fecha_ingreso);
    CREATE INDEX IF NOT EXISTS idx_operaciones_fecha_salida ON operaciones(fecha_salida);
    CREATE INDEX IF NOT EXISTS idx_operaciones_codigo_retiro ON operaciones(codigo_retiro);
    CREATE INDEX IF NOT EXISTS idx_operacion_servicios_operacion_id ON operacion_servicios(operacion_id);
    CREATE INDEX IF NOT EXISTS idx_pagos_operacion_id ON pagos(operacion_id);
    CREATE INDEX IF NOT EXISTS idx_bitacora_usuario_id ON bitacora(usuario_id);
    """)

    conn.commit()
    conn.close()


def insert_initial_data():
    """
    Inserta datos iniciales solo si no existen todavía.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = ?", ("admin",))
    admin_exists = cursor.fetchone()[0]

    if admin_exists == 0:
        cursor.execute("""
            INSERT INTO usuarios (nombre, usuario, password, rol, estado, fecha_creacion)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, ("Administrador", "admin", "1234", "admin", "activo"))

    cursor.execute("SELECT COUNT(*) FROM tarifas")
    tarifas_count = cursor.fetchone()[0]

    if tarifas_count == 0:
        tarifas = [
            ("Auto por hora", "auto", "hora", 5.00, 60, 0, "activa"),
            ("Moto por hora", "moto", "hora", 3.00, 60, 0, "activa")
        ]
        cursor.executemany("""
            INSERT INTO tarifas (
                nombre, tipo_vehiculo, tipo_cobro, monto,
                fraccion_minima, tolerancia_min, estado, fecha_creacion
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, tarifas)

    cursor.execute("SELECT COUNT(*) FROM servicios")
    servicios_count = cursor.fetchone()[0]

    if servicios_count == 0:
        servicios = [
            ("Lavado", "Lavado básico del vehículo", 15.00, 30, "activo"),
            ("Pulido", "Pulido exterior", 25.00, 60, "activo"),
            ("Detailing", "Limpieza y detallado del vehículo", 40.00, 90, "activo"),
            ("Mantenimiento", "Servicio general de mantenimiento", 50.00, 120, "activo")
        ]
        cursor.executemany("""
            INSERT INTO servicios (
                nombre, descripcion, precio, duracion_estimada, estado, fecha_creacion
            )
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, servicios)

    conn.commit()
    conn.close()


def initialize_database():
    """
    Inicializa completamente la base de datos.
    """
    create_tables()
    insert_initial_data()