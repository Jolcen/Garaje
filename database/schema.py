from database.db import getConnection


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
# 0 = Pendiente
# 1 = Activo
# 2 = Finalizado
# 3 = Cancelado
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
# 2 = Codigo Yape
# 3 = QR
# 4 = Tigo Money
#
# PAGODIGITAL.EstadoTransaccion:
# 1 = Preparado
# 2 = Pendiente
# 3 = Pagado
# 4 = Fallido
# 5 = Anulado
# 6 = Expirado
#
# PAGODIGITAL.Moneda:
# 1 = Dolares
# 2 = Bolivianos


def getFechaActualSql():
    return "date('now', 'localtime')"


def getHoraActualSql():
    return "time('now', 'localtime')"


def getFechaHoraActualSql():
    return "datetime('now', 'localtime')"


def createTables():
    loConn = getConnection()
    loCursor = loConn.cursor()

    loCursor.executescript(f"""
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
        UsrFecha TEXT NOT NULL DEFAULT ({getFechaActualSql()}),
        UsrHora TEXT NOT NULL DEFAULT ({getHoraActualSql()}),
        FechaCreacion TEXT NOT NULL DEFAULT ({getFechaHoraActualSql()}),
        FechaModificacion TEXT NOT NULL DEFAULT ({getFechaHoraActualSql()})
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
        UsrFecha TEXT NOT NULL DEFAULT ({getFechaActualSql()}),
        UsrHora TEXT NOT NULL DEFAULT ({getHoraActualSql()}),
        FechaCreacion TEXT NOT NULL DEFAULT ({getFechaHoraActualSql()}),
        FechaModificacion TEXT NOT NULL DEFAULT ({getFechaHoraActualSql()})
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
        UsrFecha TEXT NOT NULL DEFAULT ({getFechaActualSql()}),
        UsrHora TEXT NOT NULL DEFAULT ({getHoraActualSql()}),
        FechaCreacion TEXT NOT NULL DEFAULT ({getFechaHoraActualSql()}),
        FechaModificacion TEXT NOT NULL DEFAULT ({getFechaHoraActualSql()}),

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
        UsrFecha TEXT NOT NULL DEFAULT ({getFechaActualSql()}),
        UsrHora TEXT NOT NULL DEFAULT ({getHoraActualSql()}),
        FechaCreacion TEXT NOT NULL DEFAULT ({getFechaHoraActualSql()}),
        FechaModificacion TEXT NOT NULL DEFAULT ({getFechaHoraActualSql()})
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
        UsrFecha TEXT NOT NULL DEFAULT ({getFechaActualSql()}),
        UsrHora TEXT NOT NULL DEFAULT ({getHoraActualSql()}),
        FechaCreacion TEXT NOT NULL DEFAULT ({getFechaHoraActualSql()}),
        FechaModificacion TEXT NOT NULL DEFAULT ({getFechaHoraActualSql()})
    );

    -- =====================================================
    -- TABLA: TARIFADETALLE
    -- =====================================================
    CREATE TABLE IF NOT EXISTS TARIFADETALLE (
        TarifaDetalle INTEGER PRIMARY KEY AUTOINCREMENT,
        Tarifa INTEGER NOT NULL,
        TipoCobro INTEGER NOT NULL CHECK (TipoCobro IN (1, 2, 3, 4)),
        TiempoInicio INTEGER NOT NULL DEFAULT 0 CHECK (TiempoInicio >= 0),
        TiempoFin INTEGER NOT NULL DEFAULT 0 CHECK (TiempoFin >= TiempoInicio),
        HoraInicio TEXT,
        HoraFin TEXT,
        Monto REAL NOT NULL CHECK (Monto >= 0),
        Estado INTEGER NOT NULL DEFAULT 1 CHECK (Estado IN (0, 1)),

        Usr INTEGER NOT NULL DEFAULT 0,
        UsrFecha TEXT NOT NULL DEFAULT ({getFechaActualSql()}),
        UsrHora TEXT NOT NULL DEFAULT ({getHoraActualSql()}),
        FechaCreacion TEXT NOT NULL DEFAULT ({getFechaHoraActualSql()}),
        FechaModificacion TEXT NOT NULL DEFAULT ({getFechaHoraActualSql()}),

        FOREIGN KEY (Tarifa) REFERENCES TARIFA(Tarifa)
            ON UPDATE CASCADE
            ON DELETE CASCADE,

        CHECK (
            (TipoCobro = 4 AND HoraInicio IS NOT NULL AND HoraFin IS NOT NULL)
            OR
            (TipoCobro IN (1, 2, 3))
        )
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
        Observacion TEXT,
        Estado INTEGER NOT NULL DEFAULT 0 CHECK (Estado IN (0, 1, 2, 3)),

        Usr INTEGER NOT NULL DEFAULT 0,
        UsrFecha TEXT NOT NULL DEFAULT ({getFechaActualSql()}),
        UsrHora TEXT NOT NULL DEFAULT ({getHoraActualSql()}),
        FechaCreacion TEXT NOT NULL DEFAULT ({getFechaHoraActualSql()}),
        FechaModificacion TEXT NOT NULL DEFAULT ({getFechaHoraActualSql()}),

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
        UsrFecha TEXT NOT NULL DEFAULT ({getFechaActualSql()}),
        UsrHora TEXT NOT NULL DEFAULT ({getHoraActualSql()}),
        FechaCreacion TEXT NOT NULL DEFAULT ({getFechaHoraActualSql()}),
        FechaModificacion TEXT NOT NULL DEFAULT ({getFechaHoraActualSql()}),

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
        UsrFecha TEXT NOT NULL DEFAULT ({getFechaActualSql()}),
        UsrHora TEXT NOT NULL DEFAULT ({getHoraActualSql()}),
        FechaCreacion TEXT NOT NULL DEFAULT ({getFechaHoraActualSql()}),
        FechaModificacion TEXT NOT NULL DEFAULT ({getFechaHoraActualSql()}),

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
        Operacion INTEGER,
        TipoDetalle INTEGER NOT NULL CHECK (TipoDetalle IN (1, 2)),
        Detalle INTEGER NOT NULL,
        Concepto TEXT NOT NULL,
        FechaPago TEXT NOT NULL,
        MetodoPago INTEGER NOT NULL CHECK (MetodoPago IN (1, 2, 3, 4)),
        Monto REAL NOT NULL CHECK (Monto >= 0),
        Estado INTEGER NOT NULL DEFAULT 1 CHECK (Estado IN (1, 2)),

        Usr INTEGER NOT NULL DEFAULT 0,
        UsrFecha TEXT NOT NULL DEFAULT ({getFechaActualSql()}),
        UsrHora TEXT NOT NULL DEFAULT ({getHoraActualSql()}),
        FechaCreacion TEXT NOT NULL DEFAULT ({getFechaHoraActualSql()}),
        FechaModificacion TEXT NOT NULL DEFAULT ({getFechaHoraActualSql()}),

        FOREIGN KEY (Operacion) REFERENCES OPERACION(Operacion)
            ON UPDATE CASCADE
            ON DELETE RESTRICT
    );

    -- =====================================================
    -- TABLA: PAGODIGITAL
    -- =====================================================
    CREATE TABLE IF NOT EXISTS PAGODIGITAL (
        PagoDigital INTEGER PRIMARY KEY AUTOINCREMENT,
        Pago INTEGER NOT NULL UNIQUE,
        Cliente INTEGER,
        NumeroPagoEmpresa TEXT NOT NULL,
        MontoTotal REAL NOT NULL DEFAULT 0 CHECK (MontoTotal >= 0),
        NumeroTransaccion TEXT,
        NumeroAutorizacion TEXT,
        CodigoClienteEmpresa TEXT,
        TelefonoEnvio TEXT,
        TelefonoCuenta TEXT,
        Correo TEXT,
        Moneda INTEGER NOT NULL DEFAULT 2 CHECK (Moneda IN (1, 2)),
        EstadoTransaccion INTEGER NOT NULL DEFAULT 1 CHECK (EstadoTransaccion IN (1, 2, 3, 4, 5, 6)),
        Mensaje TEXT,
        MensajeSistema TEXT,
        CodigoPago TEXT,
        NombreArchivoRecibo TEXT,
        RutaRecibo TEXT,
        ReciboBase64 TEXT,
        UrlCallback TEXT,
        UrlRetorno TEXT,
        DetallePedidoJson TEXT,
        JsonRespuestaPreparacion TEXT,
        JsonRespuestaConfirmacion TEXT,
        JsonRespuestaConsulta TEXT,
        FechaHoraPreparacion TEXT,
        FechaHoraConfirmacion TEXT,
        FechaHoraFinalizacion TEXT,
        FechaHoraExpiracion TEXT,

        Usr INTEGER NOT NULL DEFAULT 0,
        UsrFecha TEXT NOT NULL DEFAULT ({getFechaActualSql()}),
        UsrHora TEXT NOT NULL DEFAULT ({getHoraActualSql()}),
        FechaCreacion TEXT NOT NULL DEFAULT ({getFechaHoraActualSql()}),
        FechaModificacion TEXT NOT NULL DEFAULT ({getFechaHoraActualSql()}),

        FOREIGN KEY (Pago) REFERENCES PAGO(Pago)
            ON UPDATE CASCADE
            ON DELETE CASCADE,

        FOREIGN KEY (Cliente) REFERENCES CLIENTE(Cliente)
            ON UPDATE CASCADE
            ON DELETE SET NULL
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
        UsrFecha TEXT NOT NULL DEFAULT ({getFechaActualSql()}),
        UsrHora TEXT NOT NULL DEFAULT ({getHoraActualSql()}),
        FechaCreacion TEXT NOT NULL DEFAULT ({getFechaHoraActualSql()}),
        FechaModificacion TEXT NOT NULL DEFAULT ({getFechaHoraActualSql()}),

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

    CREATE INDEX IF NOT EXISTS IDX_CLIENTE_Telefono
        ON CLIENTE(Telefono);

    CREATE INDEX IF NOT EXISTS IDX_VEHICULO_Cliente
        ON VEHICULO(Cliente);

    CREATE INDEX IF NOT EXISTS IDX_VEHICULO_Placa
        ON VEHICULO(NumeroPlaca, LetraPlaca);

    CREATE INDEX IF NOT EXISTS IDX_TARIFADETALLE_Tarifa
        ON TARIFADETALLE(Tarifa);

    CREATE INDEX IF NOT EXISTS IDX_TARIFADETALLE_TipoCobro
        ON TARIFADETALLE(TipoCobro);

    CREATE INDEX IF NOT EXISTS IDX_TARIFADETALLE_Horario
        ON TARIFADETALLE(HoraInicio, HoraFin);

    CREATE UNIQUE INDEX IF NOT EXISTS IDX_TARIFADETALLE_Rango
        ON TARIFADETALLE(
            Tarifa,
            TipoCobro,
            TiempoInicio,
            TiempoFin,
            IFNULL(HoraInicio, ''),
            IFNULL(HoraFin, '')
        );

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

    CREATE INDEX IF NOT EXISTS IDX_PAGO_TipoDetalle
        ON PAGO(TipoDetalle);

    CREATE INDEX IF NOT EXISTS IDX_PAGO_Detalle
        ON PAGO(Detalle);

    CREATE INDEX IF NOT EXISTS IDX_PAGO_MetodoPago
        ON PAGO(MetodoPago);

    CREATE INDEX IF NOT EXISTS IDX_PAGO_FechaPago
        ON PAGO(FechaPago);

    CREATE INDEX IF NOT EXISTS IDX_PAGO_Estado
        ON PAGO(Estado);

    CREATE INDEX IF NOT EXISTS IDX_PAGODIGITAL_Pago
        ON PAGODIGITAL(Pago);

    CREATE UNIQUE INDEX IF NOT EXISTS IDX_PAGODIGITAL_NumeroPagoEmpresa
        ON PAGODIGITAL(NumeroPagoEmpresa);

    CREATE INDEX IF NOT EXISTS IDX_PAGODIGITAL_NumeroTransaccion
        ON PAGODIGITAL(NumeroTransaccion);

    CREATE INDEX IF NOT EXISTS IDX_PAGODIGITAL_NumeroAutorizacion
        ON PAGODIGITAL(NumeroAutorizacion);

    CREATE INDEX IF NOT EXISTS IDX_PAGODIGITAL_EstadoTransaccion
        ON PAGODIGITAL(EstadoTransaccion);

    CREATE INDEX IF NOT EXISTS IDX_PAGODIGITAL_Cliente
        ON PAGODIGITAL(Cliente);

    CREATE INDEX IF NOT EXISTS IDX_PAGODIGITAL_FechaHoraPreparacion
        ON PAGODIGITAL(FechaHoraPreparacion);

    CREATE INDEX IF NOT EXISTS IDX_PAGODIGITAL_FechaHoraConfirmacion
        ON PAGODIGITAL(FechaHoraConfirmacion);

    CREATE INDEX IF NOT EXISTS IDX_PAGODIGITAL_FechaHoraFinalizacion
        ON PAGODIGITAL(FechaHoraFinalizacion);

    CREATE INDEX IF NOT EXISTS IDX_PAGODIGITAL_FechaHoraExpiracion
        ON PAGODIGITAL(FechaHoraExpiracion);

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
        SET FechaModificacion = {getFechaHoraActualSql()}
        WHERE Usuario = NEW.Usuario;
    END;

    CREATE TRIGGER IF NOT EXISTS TR_CLIENTE_UPD
    AFTER UPDATE ON CLIENTE
    FOR EACH ROW
    BEGIN
        UPDATE CLIENTE
        SET FechaModificacion = {getFechaHoraActualSql()}
        WHERE Cliente = NEW.Cliente;
    END;

    CREATE TRIGGER IF NOT EXISTS TR_VEHICULO_UPD
    AFTER UPDATE ON VEHICULO
    FOR EACH ROW
    BEGIN
        UPDATE VEHICULO
        SET FechaModificacion = {getFechaHoraActualSql()}
        WHERE Vehiculo = NEW.Vehiculo;
    END;

    CREATE TRIGGER IF NOT EXISTS TR_SERVICIO_UPD
    AFTER UPDATE ON SERVICIO
    FOR EACH ROW
    BEGIN
        UPDATE SERVICIO
        SET FechaModificacion = {getFechaHoraActualSql()}
        WHERE Servicio = NEW.Servicio;
    END;

    CREATE TRIGGER IF NOT EXISTS TR_TARIFA_UPD
    AFTER UPDATE ON TARIFA
    FOR EACH ROW
    BEGIN
        UPDATE TARIFA
        SET FechaModificacion = {getFechaHoraActualSql()}
        WHERE Tarifa = NEW.Tarifa;
    END;

    CREATE TRIGGER IF NOT EXISTS TR_TARIFADETALLE_UPD
    AFTER UPDATE ON TARIFADETALLE
    FOR EACH ROW
    BEGIN
        UPDATE TARIFADETALLE
        SET FechaModificacion = {getFechaHoraActualSql()}
        WHERE TarifaDetalle = NEW.TarifaDetalle;
    END;

    CREATE TRIGGER IF NOT EXISTS TR_CONTRATO_UPD
    AFTER UPDATE ON CONTRATO
    FOR EACH ROW
    BEGIN
        UPDATE CONTRATO
        SET FechaModificacion = {getFechaHoraActualSql()}
        WHERE Contrato = NEW.Contrato;
    END;

    CREATE TRIGGER IF NOT EXISTS TR_OPERACION_UPD
    AFTER UPDATE ON OPERACION
    FOR EACH ROW
    BEGIN
        UPDATE OPERACION
        SET FechaModificacion = {getFechaHoraActualSql()}
        WHERE Operacion = NEW.Operacion;
    END;

    CREATE TRIGGER IF NOT EXISTS TR_OPERACIONSERVICIO_UPD
    AFTER UPDATE ON OPERACIONSERVICIO
    FOR EACH ROW
    BEGIN
        UPDATE OPERACIONSERVICIO
        SET FechaModificacion = {getFechaHoraActualSql()}
        WHERE OperacionServicio = NEW.OperacionServicio;
    END;

    CREATE TRIGGER IF NOT EXISTS TR_PAGO_UPD
    AFTER UPDATE ON PAGO
    FOR EACH ROW
    BEGIN
        UPDATE PAGO
        SET FechaModificacion = {getFechaHoraActualSql()}
        WHERE Pago = NEW.Pago;
    END;

    CREATE TRIGGER IF NOT EXISTS TR_PAGODIGITAL_UPD
    AFTER UPDATE ON PAGODIGITAL
    FOR EACH ROW
    BEGIN
        UPDATE PAGODIGITAL
        SET FechaModificacion = {getFechaHoraActualSql()}
        WHERE PagoDigital = NEW.PagoDigital;
    END;

    CREATE TRIGGER IF NOT EXISTS TR_BITACORA_UPD
    AFTER UPDATE ON BITACORA
    FOR EACH ROW
    BEGIN
        UPDATE BITACORA
        SET FechaModificacion = {getFechaHoraActualSql()}
        WHERE Bitacora = NEW.Bitacora;
    END;
    """)

    loConn.commit()
    loConn.close()


def insertInitialData():
    """
    Inserta datos iniciales solo si no existen todavía.
    """
    loConn = getConnection()
    loCursor = loConn.cursor()

    # -----------------------------------------------------
    # Usuario admin inicial
    # -----------------------------------------------------
    loCursor.execute(
        "SELECT COUNT(*) FROM USUARIO WHERE NombreUsuario = ?",
        ("admin",)
    )
    lnAdminExists = loCursor.fetchone()[0]

    if lnAdminExists == 0:
        loCursor.execute(f"""
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
                ?, {getFechaActualSql()}, {getHoraActualSql()},
                {getFechaHoraActualSql()}, {getFechaHoraActualSql()}
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
    # Tarifas cabecera simplificadas
    # -----------------------------------------------------
    loCursor.execute("SELECT COUNT(*) FROM TARIFA")
    lnTarifasCount = loCursor.fetchone()[0]

    if lnTarifasCount == 0:
        laTarifas = [
            (
                "Parqueo Auto",
                "auto",
                "Tarifa general de parqueo por tramos y tarifa nocturna",
                1,
                0
            ),
            (
                "Mensual Auto",
                "auto",
                "Tarifa mensual para contratos",
                1,
                0
            ),
            (
                "Parqueo Moto",
                "moto",
                "Tarifa general de parqueo por tramos y tarifa nocturna",
                1,
                0
            ),
            (
                "Mensual Moto",
                "moto",
                "Tarifa mensual para contratos",
                1,
                0
            )
        ]

        loCursor.executemany(f"""
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
                {getFechaActualSql()}, {getHoraActualSql()},
                {getFechaHoraActualSql()}, {getFechaHoraActualSql()}
            )
        """, laTarifas)

    loCursor.execute("SELECT Tarifa FROM TARIFA WHERE Nombre = ?", ("Parqueo Auto",))
    loFilaParqueoAuto = loCursor.fetchone()
    lnTarifaParqueoAuto = loFilaParqueoAuto[0] if loFilaParqueoAuto else None

    loCursor.execute("SELECT Tarifa FROM TARIFA WHERE Nombre = ?", ("Mensual Auto",))
    loFilaMensualAuto = loCursor.fetchone()
    lnTarifaMensualAuto = loFilaMensualAuto[0] if loFilaMensualAuto else None

    loCursor.execute("SELECT Tarifa FROM TARIFA WHERE Nombre = ?", ("Parqueo Moto",))
    loFilaParqueoMoto = loCursor.fetchone()
    lnTarifaParqueoMoto = loFilaParqueoMoto[0] if loFilaParqueoMoto else None

    loCursor.execute("SELECT Tarifa FROM TARIFA WHERE Nombre = ?", ("Mensual Moto",))
    loFilaMensualMoto = loCursor.fetchone()
    lnTarifaMensualMoto = loFilaMensualMoto[0] if loFilaMensualMoto else None

    # -----------------------------------------------------
    # Tarifas detalle simplificadas
    # -----------------------------------------------------
    loCursor.execute("SELECT COUNT(*) FROM TARIFADETALLE")
    lnDetallesCount = loCursor.fetchone()[0]

    if lnDetallesCount == 0:
        laDetalles = []

        if lnTarifaParqueoAuto:
            laDetalles.extend([
                (lnTarifaParqueoAuto, 1, 1, 30, None, None, 4.0, 1, 0),
                (lnTarifaParqueoAuto, 1, 31, 60, None, None, 6.0, 1, 0),
                (lnTarifaParqueoAuto, 1, 61, 120, None, None, 10.0, 1, 0),
                (lnTarifaParqueoAuto, 1, 121, 180, None, None, 14.0, 1, 0),
                (lnTarifaParqueoAuto, 1, 181, 240, None, None, 18.0, 1, 0),
                (lnTarifaParqueoAuto, 1, 241, 300, None, None, 22.0, 1, 0),
                (lnTarifaParqueoAuto, 1, 301, 360, None, None, 26.0, 1, 0),
                (lnTarifaParqueoAuto, 1, 361, 420, None, None, 30.0, 1, 0),
                (lnTarifaParqueoAuto, 1, 421, 480, None, None, 35.0, 1, 0),
                (lnTarifaParqueoAuto, 4, 0, 0, "18:00", "20:00", 25.0, 1, 0),
            ])

        if lnTarifaMensualAuto:
            laDetalles.append(
                (lnTarifaMensualAuto, 3, 1, 1, None, None, 300.0, 1, 0)
            )

        if lnTarifaParqueoMoto:
            laDetalles.extend([
                (lnTarifaParqueoMoto, 1, 1, 30, None, None, 4.0, 1, 0),
                (lnTarifaParqueoMoto, 1, 31, 60, None, None, 6.0, 1, 0),
                (lnTarifaParqueoMoto, 1, 61, 120, None, None, 10.0, 1, 0),
                (lnTarifaParqueoMoto, 1, 121, 180, None, None, 14.0, 1, 0),
                (lnTarifaParqueoMoto, 1, 181, 240, None, None, 18.0, 1, 0),
                (lnTarifaParqueoMoto, 1, 241, 300, None, None, 22.0, 1, 0),
                (lnTarifaParqueoMoto, 1, 301, 360, None, None, 26.0, 1, 0),
                (lnTarifaParqueoMoto, 1, 361, 420, None, None, 30.0, 1, 0),
                (lnTarifaParqueoMoto, 1, 421, 480, None, None, 35.0, 1, 0),
                (lnTarifaParqueoMoto, 4, 0, 0, "18:00", "20:00", 25.0, 1, 0),
            ])

        if lnTarifaMensualMoto:
            laDetalles.append(
                (lnTarifaMensualMoto, 3, 1, 1, None, None, 300.0, 1, 0)
            )

        if laDetalles:
            loCursor.executemany(f"""
                INSERT INTO TARIFADETALLE (
                    Tarifa,
                    TipoCobro,
                    TiempoInicio,
                    TiempoFin,
                    HoraInicio,
                    HoraFin,
                    Monto,
                    Estado,
                    Usr,
                    UsrFecha,
                    UsrHora,
                    FechaCreacion,
                    FechaModificacion
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    {getFechaActualSql()}, {getHoraActualSql()},
                    {getFechaHoraActualSql()}, {getFechaHoraActualSql()}
                )
            """, laDetalles)

    # -----------------------------------------------------
    # Servicios iniciales
    # -----------------------------------------------------
    loCursor.execute("SELECT COUNT(*) FROM SERVICIO")
    lnServiciosCount = loCursor.fetchone()[0]

    if lnServiciosCount == 0:
        laServicios = [
            ("Lavado", "Lavado basico del vehiculo", 15.00, 1, 0),
            ("Pulido", "Pulido exterior", 25.00, 1, 0),
            ("Detailing", "Limpieza y detallado del vehiculo", 40.00, 1, 0),
            ("Mantenimiento", "Servicio general de mantenimiento", 50.00, 1, 0)
        ]

        loCursor.executemany(f"""
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
                {getFechaActualSql()}, {getHoraActualSql()},
                {getFechaHoraActualSql()}, {getFechaHoraActualSql()}
            )
        """, laServicios)

    loConn.commit()
    loConn.close()


def initializeDatabase():
    """
    Inicializa completamente la base de datos.
    """
    createTables()
    insertInitialData()