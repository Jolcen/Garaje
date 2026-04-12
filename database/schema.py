from database.db import get_connection


# =========================================================
# CATÁLOGOS / ESTADOS
# =========================================================
# USUARIO.Estado:
# 0 = Inactivo
# 1 = Activo
#
# USUARIO.Rol:
# 1 = Administrador
# 2 = Empleado
#
# CLIENTE.Estado:
# 0 = Inactivo
# 1 = Activo
#
# VEHICULO.Estado:
# 0 = Inactivo
# 1 = Activo
#
# SERVICIO.Estado:
# 0 = Inactivo
# 1 = Activo
#
# TARIFA.Estado:
# 0 = Inactiva
# 1 = Activa
#
# TARIFADETALLE.Estado:
# 0 = Inactivo
# 1 = Activo
#
# TARIFADETALLE.TipoCobro:
# 1 = Hora
# 2 = Dia
# 3 = Mes
# 4 = Nocturna
#
# CONTRATO.Estado:
# 1 = Activo
# 2 = Finalizado
# 3 = Cancelado
# 4 = Suspendido
#
# OPERACION.Estado:
# 1 = Abierta
# 2 = Cerrada
# 3 = Pagada
# 4 = Cancelada
#
# PAGO.Estado:
# 1 = Registrado
# 2 = Anulado
#
# PAGO.MetodoPago:
# 1 = Efectivo
# 2 = QR


def _fecha_actual_sql():
    return "date('now', 'localtime')"


def _hora_actual_sql():
    return "time('now', 'localtime')"


def _fecha_hora_actual_sql():
    return "datetime('now', 'localtime')"


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript(f"""
    PRAGMA foreign_keys = ON;

    -- =====================================================
    -- TABLA: USUARIO
    -- =====================================================
    CREATE TABLE IF NOT EXISTS USUARIO (
        Usuario INTEGER PRIMARY KEY AUTOINCREMENT,
        Nombre TEXT NOT NULL,
        NombreUsuario TEXT NOT NULL UNIQUE,
        Contrasena TEXT NOT NULL,
        Rol INTEGER NOT NULL CHECK (Rol IN (1, 2)),
        Estado INTEGER NOT NULL DEFAULT 1 CHECK (Estado IN (0, 1)),

        Usr INTEGER NOT NULL DEFAULT 0,
        UsrFecha TEXT NOT NULL DEFAULT ({_fecha_actual_sql()}),
        UsrHora TEXT NOT NULL DEFAULT ({_hora_actual_sql()}),
        FechaCreacion TEXT NOT NULL DEFAULT ({_fecha_hora_actual_sql()}),
        FechaModificacion TEXT NOT NULL DEFAULT ({_fecha_hora_actual_sql()})
    );

    -- =====================================================
    -- TABLA: CLIENTE
    -- =====================================================
    CREATE TABLE IF NOT EXISTS CLIENTE (
        Cliente INTEGER PRIMARY KEY AUTOINCREMENT,
        Nombres TEXT NOT NULL,
        Apellidos TEXT,
        DocumentoIdentidad TEXT,
        ComplementoDocumento TEXT,
        Telefono TEXT,
        Estado INTEGER NOT NULL DEFAULT 1 CHECK (Estado IN (0, 1)),

        Usr INTEGER NOT NULL DEFAULT 0,
        UsrFecha TEXT NOT NULL DEFAULT ({_fecha_actual_sql()}),
        UsrHora TEXT NOT NULL DEFAULT ({_hora_actual_sql()}),
        FechaCreacion TEXT NOT NULL DEFAULT ({_fecha_hora_actual_sql()}),
        FechaModificacion TEXT NOT NULL DEFAULT ({_fecha_hora_actual_sql()})
    );

    -- =====================================================
    -- TABLA: VEHICULO
    -- =====================================================
    CREATE TABLE IF NOT EXISTS VEHICULO (
        Vehiculo INTEGER PRIMARY KEY AUTOINCREMENT,
        Cliente INTEGER,
        NumeroPlaca TEXT NOT NULL,
        LetraPlaca TEXT NOT NULL,
        TipoVehiculo TEXT NOT NULL,
        Marca TEXT,
        Color TEXT,
        Estado INTEGER NOT NULL DEFAULT 1 CHECK (Estado IN (0, 1)),

        Usr INTEGER NOT NULL DEFAULT 0,
        UsrFecha TEXT NOT NULL DEFAULT ({_fecha_actual_sql()}),
        UsrHora TEXT NOT NULL DEFAULT ({_hora_actual_sql()}),
        FechaCreacion TEXT NOT NULL DEFAULT ({_fecha_hora_actual_sql()}),
        FechaModificacion TEXT NOT NULL DEFAULT ({_fecha_hora_actual_sql()}),

        FOREIGN KEY (Cliente) REFERENCES CLIENTE(Cliente)
            ON UPDATE CASCADE
            ON DELETE SET NULL,

        UNIQUE (NumeroPlaca, LetraPlaca)
    );

    -- =====================================================
    -- TABLA: SERVICIO
    -- =====================================================
    CREATE TABLE IF NOT EXISTS SERVICIO (
        Servicio INTEGER PRIMARY KEY AUTOINCREMENT,
        Nombre TEXT NOT NULL UNIQUE,
        Descripcion TEXT,
        Precio REAL NOT NULL CHECK (Precio >= 0),
        Estado INTEGER NOT NULL DEFAULT 1 CHECK (Estado IN (0, 1)),

        Usr INTEGER NOT NULL DEFAULT 0,
        UsrFecha TEXT NOT NULL DEFAULT ({_fecha_actual_sql()}),
        UsrHora TEXT NOT NULL DEFAULT ({_hora_actual_sql()}),
        FechaCreacion TEXT NOT NULL DEFAULT ({_fecha_hora_actual_sql()}),
        FechaModificacion TEXT NOT NULL DEFAULT ({_fecha_hora_actual_sql()})
    );

    -- =====================================================
    -- TABLA: TARIFA
    -- =====================================================
    CREATE TABLE IF NOT EXISTS TARIFA (
        Tarifa INTEGER PRIMARY KEY AUTOINCREMENT,
        Nombre TEXT NOT NULL,
        TipoVehiculo TEXT NOT NULL,
        Descripcion TEXT,
        Estado INTEGER NOT NULL DEFAULT 1 CHECK (Estado IN (0, 1)),

        Usr INTEGER NOT NULL DEFAULT 0,
        UsrFecha TEXT NOT NULL DEFAULT ({_fecha_actual_sql()}),
        UsrHora TEXT NOT NULL DEFAULT ({_hora_actual_sql()}),
        FechaCreacion TEXT NOT NULL DEFAULT ({_fecha_hora_actual_sql()}),
        FechaModificacion TEXT NOT NULL DEFAULT ({_fecha_hora_actual_sql()})
    );

    -- =====================================================
    -- TABLA: TARIFADETALLE
    -- =====================================================
    CREATE TABLE IF NOT EXISTS TARIFADETALLE (
        TarifaDetalle INTEGER PRIMARY KEY AUTOINCREMENT,
        Tarifa INTEGER NOT NULL,
        TipoCobro INTEGER NOT NULL CHECK (TipoCobro IN (1, 2, 3, 4)),
        TiempoInicio INTEGER NOT NULL CHECK (TiempoInicio >= 0),
        TiempoFin INTEGER NOT NULL CHECK (TiempoFin >= TiempoInicio),
        Monto REAL NOT NULL CHECK (Monto >= 0),
        Estado INTEGER NOT NULL DEFAULT 1 CHECK (Estado IN (0, 1)),

        Usr INTEGER NOT NULL DEFAULT 0,
        UsrFecha TEXT NOT NULL DEFAULT ({_fecha_actual_sql()}),
        UsrHora TEXT NOT NULL DEFAULT ({_hora_actual_sql()}),
        FechaCreacion TEXT NOT NULL DEFAULT ({_fecha_hora_actual_sql()}),
        FechaModificacion TEXT NOT NULL DEFAULT ({_fecha_hora_actual_sql()}),

        FOREIGN KEY (Tarifa) REFERENCES TARIFA(Tarifa)
            ON UPDATE CASCADE
            ON DELETE CASCADE
    );

    -- =====================================================
    -- TABLA: CONTRATO
    -- =====================================================
    CREATE TABLE IF NOT EXISTS CONTRATO (
        Contrato INTEGER PRIMARY KEY AUTOINCREMENT,
        Cliente INTEGER NOT NULL,
        Vehiculo INTEGER NOT NULL,
        Tarifa INTEGER NOT NULL,
        CodigoContrato TEXT NOT NULL UNIQUE,
        FechaInicio TEXT NOT NULL,
        FechaFin TEXT NOT NULL,
        DuracionMeses INTEGER NOT NULL CHECK (DuracionMeses > 0),
        Estado INTEGER NOT NULL DEFAULT 1 CHECK (Estado IN (1, 2, 3, 4)),

        Usr INTEGER NOT NULL DEFAULT 0,
        UsrFecha TEXT NOT NULL DEFAULT ({_fecha_actual_sql()}),
        UsrHora TEXT NOT NULL DEFAULT ({_hora_actual_sql()}),
        FechaCreacion TEXT NOT NULL DEFAULT ({_fecha_hora_actual_sql()}),
        FechaModificacion TEXT NOT NULL DEFAULT ({_fecha_hora_actual_sql()}),

        FOREIGN KEY (Cliente) REFERENCES CLIENTE(Cliente)
            ON UPDATE CASCADE
            ON DELETE RESTRICT,

        FOREIGN KEY (Vehiculo) REFERENCES VEHICULO(Vehiculo)
            ON UPDATE CASCADE
            ON DELETE RESTRICT,

        FOREIGN KEY (Tarifa) REFERENCES TARIFA(Tarifa)
            ON UPDATE CASCADE
            ON DELETE RESTRICT
    );

    -- =====================================================
    -- TABLA: OPERACION
    -- =====================================================
    CREATE TABLE IF NOT EXISTS OPERACION (
        Operacion INTEGER PRIMARY KEY AUTOINCREMENT,
        CodigoOperacion TEXT NOT NULL UNIQUE,
        Vehiculo INTEGER NOT NULL,
        Tarifa INTEGER NOT NULL,
        FechaIngreso TEXT NOT NULL,
        FechaSalida TEXT,
        MontoParqueo REAL NOT NULL DEFAULT 0 CHECK (MontoParqueo >= 0),
        MontoServicios REAL NOT NULL DEFAULT 0 CHECK (MontoServicios >= 0),
        Estado INTEGER NOT NULL DEFAULT 1 CHECK (Estado IN (1, 2, 3, 4)),

        Usr INTEGER NOT NULL DEFAULT 0,
        UsrFecha TEXT NOT NULL DEFAULT ({_fecha_actual_sql()}),
        UsrHora TEXT NOT NULL DEFAULT ({_hora_actual_sql()}),
        FechaCreacion TEXT NOT NULL DEFAULT ({_fecha_hora_actual_sql()}),
        FechaModificacion TEXT NOT NULL DEFAULT ({_fecha_hora_actual_sql()}),

        FOREIGN KEY (Vehiculo) REFERENCES VEHICULO(Vehiculo)
            ON UPDATE CASCADE
            ON DELETE RESTRICT,

        FOREIGN KEY (Tarifa) REFERENCES TARIFA(Tarifa)
            ON UPDATE CASCADE
            ON DELETE RESTRICT
    );

    -- =====================================================
    -- TABLA: OPERACIONSERVICIO
    -- =====================================================
    CREATE TABLE IF NOT EXISTS OPERACIONSERVICIO (
        OperacionServicio INTEGER PRIMARY KEY AUTOINCREMENT,
        Operacion INTEGER NOT NULL,
        Servicio INTEGER NOT NULL,
        Cantidad INTEGER NOT NULL DEFAULT 1 CHECK (Cantidad > 0),
        PrecioUnitario REAL NOT NULL CHECK (PrecioUnitario >= 0),
        Subtotal REAL NOT NULL CHECK (Subtotal >= 0),

        Usr INTEGER NOT NULL DEFAULT 0,
        UsrFecha TEXT NOT NULL DEFAULT ({_fecha_actual_sql()}),
        UsrHora TEXT NOT NULL DEFAULT ({_hora_actual_sql()}),
        FechaCreacion TEXT NOT NULL DEFAULT ({_fecha_hora_actual_sql()}),
        FechaModificacion TEXT NOT NULL DEFAULT ({_fecha_hora_actual_sql()}),

        FOREIGN KEY (Operacion) REFERENCES OPERACION(Operacion)
            ON UPDATE CASCADE
            ON DELETE CASCADE,

        FOREIGN KEY (Servicio) REFERENCES SERVICIO(Servicio)
            ON UPDATE CASCADE
            ON DELETE RESTRICT
    );

    -- =====================================================
    -- TABLA: PAGO
    -- =====================================================
    CREATE TABLE IF NOT EXISTS PAGO (
        Pago INTEGER PRIMARY KEY AUTOINCREMENT,
        Operacion INTEGER NOT NULL,
        FechaPago TEXT NOT NULL,
        MetodoPago INTEGER NOT NULL CHECK (MetodoPago IN (1, 2)),
        Monto REAL NOT NULL CHECK (Monto >= 0),
        Estado INTEGER NOT NULL DEFAULT 1 CHECK (Estado IN (1, 2)),

        Usr INTEGER NOT NULL DEFAULT 0,
        UsrFecha TEXT NOT NULL DEFAULT ({_fecha_actual_sql()}),
        UsrHora TEXT NOT NULL DEFAULT ({_hora_actual_sql()}),
        FechaCreacion TEXT NOT NULL DEFAULT ({_fecha_hora_actual_sql()}),
        FechaModificacion TEXT NOT NULL DEFAULT ({_fecha_hora_actual_sql()}),

        FOREIGN KEY (Operacion) REFERENCES OPERACION(Operacion)
            ON UPDATE CASCADE
            ON DELETE RESTRICT
    );

    -- =====================================================
    -- TABLA: BITACORA
    -- =====================================================
    CREATE TABLE IF NOT EXISTS BITACORA (
        Bitacora INTEGER PRIMARY KEY AUTOINCREMENT,
        Usuario INTEGER,
        Accion TEXT NOT NULL,
        TablaAfectada TEXT,
        RegistroAfectado INTEGER,
        Descripcion TEXT,
        FechaEvento TEXT NOT NULL,

        Usr INTEGER NOT NULL DEFAULT 0,
        UsrFecha TEXT NOT NULL DEFAULT ({_fecha_actual_sql()}),
        UsrHora TEXT NOT NULL DEFAULT ({_hora_actual_sql()}),
        FechaCreacion TEXT NOT NULL DEFAULT ({_fecha_hora_actual_sql()}),
        FechaModificacion TEXT NOT NULL DEFAULT ({_fecha_hora_actual_sql()}),

        FOREIGN KEY (Usuario) REFERENCES USUARIO(Usuario)
            ON UPDATE CASCADE
            ON DELETE SET NULL
    );

    -- =====================================================
    -- ÍNDICES
    -- =====================================================
    CREATE INDEX IF NOT EXISTS IDX_USUARIO_NombreUsuario
        ON USUARIO(NombreUsuario);

    CREATE INDEX IF NOT EXISTS IDX_CLIENTE_DocumentoIdentidad
        ON CLIENTE(DocumentoIdentidad);

    CREATE INDEX IF NOT EXISTS IDX_VEHICULO_Cliente
        ON VEHICULO(Cliente);

    CREATE INDEX IF NOT EXISTS IDX_VEHICULO_Placa
        ON VEHICULO(NumeroPlaca, LetraPlaca);

    CREATE INDEX IF NOT EXISTS IDX_TARIFADETALLE_Tarifa
        ON TARIFADETALLE(Tarifa);

    CREATE INDEX IF NOT EXISTS IDX_TARIFADETALLE_TipoCobro
        ON TARIFADETALLE(TipoCobro);

    CREATE UNIQUE INDEX IF NOT EXISTS IDX_TARIFADETALLE_Rango
        ON TARIFADETALLE(Tarifa, TipoCobro, TiempoInicio, TiempoFin);

    CREATE INDEX IF NOT EXISTS IDX_CONTRATO_Cliente
        ON CONTRATO(Cliente);

    CREATE INDEX IF NOT EXISTS IDX_CONTRATO_Vehiculo
        ON CONTRATO(Vehiculo);

    CREATE INDEX IF NOT EXISTS IDX_CONTRATO_Tarifa
        ON CONTRATO(Tarifa);

    CREATE INDEX IF NOT EXISTS IDX_CONTRATO_FechaInicio
        ON CONTRATO(FechaInicio);

    CREATE INDEX IF NOT EXISTS IDX_CONTRATO_FechaFin
        ON CONTRATO(FechaFin);

    CREATE UNIQUE INDEX IF NOT EXISTS IDX_CONTRATO_Vehiculo_Activo
        ON CONTRATO(Vehiculo)
        WHERE Estado = 1;

    CREATE INDEX IF NOT EXISTS IDX_OPERACION_Estado
        ON OPERACION(Estado);

    CREATE INDEX IF NOT EXISTS IDX_OPERACION_FechaIngreso
        ON OPERACION(FechaIngreso);

    CREATE INDEX IF NOT EXISTS IDX_OPERACION_FechaSalida
        ON OPERACION(FechaSalida);

    CREATE INDEX IF NOT EXISTS IDX_OPERACION_Vehiculo
        ON OPERACION(Vehiculo);

    CREATE INDEX IF NOT EXISTS IDX_OPERACION_Tarifa
        ON OPERACION(Tarifa);

    CREATE INDEX IF NOT EXISTS IDX_OPERACIONSERVICIO_Operacion
        ON OPERACIONSERVICIO(Operacion);

    CREATE INDEX IF NOT EXISTS IDX_OPERACIONSERVICIO_Servicio
        ON OPERACIONSERVICIO(Servicio);

    CREATE INDEX IF NOT EXISTS IDX_PAGO_Operacion
        ON PAGO(Operacion);

    CREATE INDEX IF NOT EXISTS IDX_BITACORA_Usuario
        ON BITACORA(Usuario);

    CREATE INDEX IF NOT EXISTS IDX_BITACORA_FechaEvento
        ON BITACORA(FechaEvento);

    -- =====================================================
    -- TRIGGERS: FechaModificacion
    -- =====================================================
    CREATE TRIGGER IF NOT EXISTS TR_USUARIO_UPD
    AFTER UPDATE ON USUARIO
    FOR EACH ROW
    BEGIN
        UPDATE USUARIO
        SET FechaModificacion = {_fecha_hora_actual_sql()}
        WHERE Usuario = NEW.Usuario;
    END;

    CREATE TRIGGER IF NOT EXISTS TR_CLIENTE_UPD
    AFTER UPDATE ON CLIENTE
    FOR EACH ROW
    BEGIN
        UPDATE CLIENTE
        SET FechaModificacion = {_fecha_hora_actual_sql()}
        WHERE Cliente = NEW.Cliente;
    END;

    CREATE TRIGGER IF NOT EXISTS TR_VEHICULO_UPD
    AFTER UPDATE ON VEHICULO
    FOR EACH ROW
    BEGIN
        UPDATE VEHICULO
        SET FechaModificacion = {_fecha_hora_actual_sql()}
        WHERE Vehiculo = NEW.Vehiculo;
    END;

    CREATE TRIGGER IF NOT EXISTS TR_SERVICIO_UPD
    AFTER UPDATE ON SERVICIO
    FOR EACH ROW
    BEGIN
        UPDATE SERVICIO
        SET FechaModificacion = {_fecha_hora_actual_sql()}
        WHERE Servicio = NEW.Servicio;
    END;

    CREATE TRIGGER IF NOT EXISTS TR_TARIFA_UPD
    AFTER UPDATE ON TARIFA
    FOR EACH ROW
    BEGIN
        UPDATE TARIFA
        SET FechaModificacion = {_fecha_hora_actual_sql()}
        WHERE Tarifa = NEW.Tarifa;
    END;

    CREATE TRIGGER IF NOT EXISTS TR_TARIFADETALLE_UPD
    AFTER UPDATE ON TARIFADETALLE
    FOR EACH ROW
    BEGIN
        UPDATE TARIFADETALLE
        SET FechaModificacion = {_fecha_hora_actual_sql()}
        WHERE TarifaDetalle = NEW.TarifaDetalle;
    END;

    CREATE TRIGGER IF NOT EXISTS TR_CONTRATO_UPD
    AFTER UPDATE ON CONTRATO
    FOR EACH ROW
    BEGIN
        UPDATE CONTRATO
        SET FechaModificacion = {_fecha_hora_actual_sql()}
        WHERE Contrato = NEW.Contrato;
    END;

    CREATE TRIGGER IF NOT EXISTS TR_OPERACION_UPD
    AFTER UPDATE ON OPERACION
    FOR EACH ROW
    BEGIN
        UPDATE OPERACION
        SET FechaModificacion = {_fecha_hora_actual_sql()}
        WHERE Operacion = NEW.Operacion;
    END;

    CREATE TRIGGER IF NOT EXISTS TR_OPERACIONSERVICIO_UPD
    AFTER UPDATE ON OPERACIONSERVICIO
    FOR EACH ROW
    BEGIN
        UPDATE OPERACIONSERVICIO
        SET FechaModificacion = {_fecha_hora_actual_sql()}
        WHERE OperacionServicio = NEW.OperacionServicio;
    END;

    CREATE TRIGGER IF NOT EXISTS TR_PAGO_UPD
    AFTER UPDATE ON PAGO
    FOR EACH ROW
    BEGIN
        UPDATE PAGO
        SET FechaModificacion = {_fecha_hora_actual_sql()}
        WHERE Pago = NEW.Pago;
    END;

    CREATE TRIGGER IF NOT EXISTS TR_BITACORA_UPD
    AFTER UPDATE ON BITACORA
    FOR EACH ROW
    BEGIN
        UPDATE BITACORA
        SET FechaModificacion = {_fecha_hora_actual_sql()}
        WHERE Bitacora = NEW.Bitacora;
    END;
    """)

    conn.commit()
    conn.close()


def insert_initial_data():
    """
    Inserta datos iniciales solo si no existen todavía.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # -----------------------------------------------------
    # Usuario admin inicial
    # -----------------------------------------------------
    cursor.execute(
        "SELECT COUNT(*) FROM USUARIO WHERE NombreUsuario = ?",
        ("admin",)
    )
    admin_exists = cursor.fetchone()[0]

    if admin_exists == 0:
        cursor.execute(f"""
            INSERT INTO USUARIO (
                Nombre,
                NombreUsuario,
                Contrasena,
                Rol,
                Estado,
                Usr,
                UsrFecha,
                UsrHora,
                FechaCreacion,
                FechaModificacion
            )
            VALUES (
                ?, ?, ?, ?, ?,
                ?, {_fecha_actual_sql()}, {_hora_actual_sql()},
                {_fecha_hora_actual_sql()}, {_fecha_hora_actual_sql()}
            )
        """, (
            "Administrador",
            "admin",
            "1234",
            1,
            1,
            0
        ))

    # -----------------------------------------------------
    # Tarifas cabecera
    # -----------------------------------------------------
    cursor.execute("SELECT COUNT(*) FROM TARIFA")
    tarifas_count = cursor.fetchone()[0]

    if tarifas_count == 0:
        tarifas = [
            (
                "Tarifa General Auto",
                "auto",
                "Tarifa general por horas para auto",
                1,
                0
            ),
            (
                "Tarifa Diaria Auto",
                "auto",
                "Tarifa por dia para auto",
                1,
                0
            ),
            (
                "Tarifa Mensual Auto",
                "auto",
                "Tarifa por mes para auto",
                1,
                0
            ),
            (
                "Tarifa Nocturna Auto",
                "auto",
                "Tarifa nocturna para auto",
                1,
                0
            )
        ]

        cursor.executemany(f"""
            INSERT INTO TARIFA (
                Nombre,
                TipoVehiculo,
                Descripcion,
                Estado,
                Usr,
                UsrFecha,
                UsrHora,
                FechaCreacion,
                FechaModificacion
            )
            VALUES (
                ?, ?, ?, ?, ?,
                {_fecha_actual_sql()}, {_hora_actual_sql()},
                {_fecha_hora_actual_sql()}, {_fecha_hora_actual_sql()}
            )
        """, tarifas)

    cursor.execute("SELECT Tarifa FROM TARIFA WHERE Nombre = ?", ("Tarifa General Auto",))
    fila_general = cursor.fetchone()
    tarifa_general = fila_general[0] if fila_general else None

    cursor.execute("SELECT Tarifa FROM TARIFA WHERE Nombre = ?", ("Tarifa Diaria Auto",))
    fila_dia = cursor.fetchone()
    tarifa_dia = fila_dia[0] if fila_dia else None

    cursor.execute("SELECT Tarifa FROM TARIFA WHERE Nombre = ?", ("Tarifa Mensual Auto",))
    fila_mes = cursor.fetchone()
    tarifa_mes = fila_mes[0] if fila_mes else None

    cursor.execute("SELECT Tarifa FROM TARIFA WHERE Nombre = ?", ("Tarifa Nocturna Auto",))
    fila_nocturna = cursor.fetchone()
    tarifa_nocturna = fila_nocturna[0] if fila_nocturna else None

    # -----------------------------------------------------
    # Tarifas detalle
    # -----------------------------------------------------
    cursor.execute("SELECT COUNT(*) FROM TARIFADETALLE")
    detalles_count = cursor.fetchone()[0]

    if detalles_count == 0:
        detalles = []

        if tarifa_general:
            detalles.extend([
                (tarifa_general, 1, 1, 30, 4.0, 1, 0),
                (tarifa_general, 1, 31, 60, 6.0, 1, 0),
                (tarifa_general, 1, 61, 120, 10.0, 1, 0),
                (tarifa_general, 1, 121, 180, 14.0, 1, 0),
                (tarifa_general, 1, 181, 240, 18.0, 1, 0),
                (tarifa_general, 1, 241, 300, 22.0, 1, 0),
                (tarifa_general, 1, 301, 360, 26.0, 1, 0),
                (tarifa_general, 1, 361, 420, 30.0, 1, 0),
                (tarifa_general, 1, 421, 480, 35.0, 1, 0),
            ])

        if tarifa_dia:
            detalles.append((tarifa_dia, 2, 1, 1, 35.0, 1, 0))

        if tarifa_mes:
            detalles.append((tarifa_mes, 3, 1, 1, 300.0, 1, 0))

        if tarifa_nocturna:
            detalles.append((tarifa_nocturna, 4, 1, 1, 25.0, 1, 0))

        if detalles:
            cursor.executemany(f"""
                INSERT INTO TARIFADETALLE (
                    Tarifa,
                    TipoCobro,
                    TiempoInicio,
                    TiempoFin,
                    Monto,
                    Estado,
                    Usr,
                    UsrFecha,
                    UsrHora,
                    FechaCreacion,
                    FechaModificacion
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?,
                    {_fecha_actual_sql()}, {_hora_actual_sql()},
                    {_fecha_hora_actual_sql()}, {_fecha_hora_actual_sql()}
                )
            """, detalles)

    # -----------------------------------------------------
    # Servicios iniciales
    # -----------------------------------------------------
    cursor.execute("SELECT COUNT(*) FROM SERVICIO")
    servicios_count = cursor.fetchone()[0]

    if servicios_count == 0:
        servicios = [
            ("Lavado", "Lavado basico del vehiculo", 15.00, 1, 0),
            ("Pulido", "Pulido exterior", 25.00, 1, 0),
            ("Detailing", "Limpieza y detallado del vehiculo", 40.00, 1, 0),
            ("Mantenimiento", "Servicio general de mantenimiento", 50.00, 1, 0)
        ]

        cursor.executemany(f"""
            INSERT INTO SERVICIO (
                Nombre,
                Descripcion,
                Precio,
                Estado,
                Usr,
                UsrFecha,
                UsrHora,
                FechaCreacion,
                FechaModificacion
            )
            VALUES (
                ?, ?, ?, ?, ?,
                {_fecha_actual_sql()}, {_hora_actual_sql()},
                {_fecha_hora_actual_sql()}, {_fecha_hora_actual_sql()}
            )
        """, servicios)

    conn.commit()
    conn.close()


def initialize_database():
    """
    Inicializa completamente la base de datos.
    """
    create_tables()
    insert_initial_data()