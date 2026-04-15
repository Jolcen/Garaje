import re
from datetime import datetime

from database.db import getConnection


# =========================================================
# CONSTANTES
# =========================================================
gnTipoDetalleOperacion = 1
gnTipoDetalleContrato = 2

gnEstadoOperacionAbierta = 1
gnEstadoOperacionCerrada = 2
gnEstadoOperacionPagada = 3
gnEstadoOperacionCancelada = 4


# =========================================================
# UTILIDADES
# =========================================================
def obtenerUsuarioActualId(txUsuarioData):
    if not txUsuarioData:
        return 0
    return txUsuarioData.get("Usuario", 0)


def getFechaHoraActualTexto():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def limpiarTexto(tcValor):
    if tcValor is None:
        return ""
    return str(tcValor).strip()


def esTelefonoValido(tcTelefono):
    return bool(re.fullmatch(r"\d{7,8}", limpiarTexto(tcTelefono)))


# =========================================================
# CONSULTAS DE APOYO
# =========================================================
def obtenerContextoDetalle(tnTipoDetalle, tnDetalle):
    loConn = getConnection()
    loCursor = loConn.cursor()

    try:
        if tnTipoDetalle == gnTipoDetalleOperacion:
            loCursor.execute("""
                SELECT
                    c.Cliente,
                    TRIM(COALESCE(c.Nombres, '') || ' ' || COALESCE(c.Apellidos, '')) AS NombreCliente,
                    COALESCE(c.Telefono, '') AS Telefono
                FROM OPERACION o
                INNER JOIN VEHICULO v ON v.Vehiculo = o.Vehiculo
                LEFT JOIN CLIENTE c ON c.Cliente = v.Cliente
                WHERE o.Operacion = ?
            """, (tnDetalle,))
            loFila = loCursor.fetchone()

            if loFila:
                return {
                    "Cliente": loFila[0],
                    "NombreCliente": limpiarTexto(loFila[1]) or f"Cliente {tnDetalle}",
                    "Telefono": limpiarTexto(loFila[2]),
                }

        elif tnTipoDetalle == gnTipoDetalleContrato:
            loCursor.execute("""
                SELECT
                    c.Cliente,
                    TRIM(COALESCE(c.Nombres, '') || ' ' || COALESCE(c.Apellidos, '')) AS NombreCliente,
                    COALESCE(c.Telefono, '') AS Telefono
                FROM CONTRATO ct
                INNER JOIN CLIENTE c ON c.Cliente = ct.Cliente
                WHERE ct.Contrato = ?
            """, (tnDetalle,))
            loFila = loCursor.fetchone()

            if loFila:
                return {
                    "Cliente": loFila[0],
                    "NombreCliente": limpiarTexto(loFila[1]) or f"Cliente {tnDetalle}",
                    "Telefono": limpiarTexto(loFila[2]),
                }

        return {
            "Cliente": None,
            "NombreCliente": f"Cliente {tnDetalle}",
            "Telefono": "",
        }

    finally:
        loConn.close()


# =========================================================
# BITÁCORA
# =========================================================
def insertarBitacora(loCursor, tnUsuario, tcAccion, tcTablaAfectada, tnRegistroAfectado, tcDescripcion):
    loCursor.execute("""
        INSERT INTO BITACORA (
            Usuario,
            Accion,
            TablaAfectada,
            RegistroAfectado,
            Descripcion,
            FechaEvento,
            Usr,
            UsrFecha,
            UsrHora,
            FechaCreacion,
            FechaModificacion
        )
        VALUES (
            ?, ?, ?, ?, ?, ?,
            ?,
            date('now','localtime'),
            time('now','localtime'),
            datetime('now','localtime'),
            datetime('now','localtime')
        )
    """, (
        tnUsuario,
        tcAccion,
        tcTablaAfectada,
        tnRegistroAfectado,
        tcDescripcion,
        getFechaHoraActualTexto(),
        tnUsuario
    ))


# =========================================================
# OPERACIONES
# =========================================================
def marcarOperacionPagada(loCursor, tnTipoDetalle, tnDetalle):
    if tnTipoDetalle != gnTipoDetalleOperacion:
        return

    loCursor.execute("""
        UPDATE OPERACION
        SET
            Estado = ?,
            FechaModificacion = datetime('now','localtime')
        WHERE Operacion = ?
    """, (
        gnEstadoOperacionPagada,
        tnDetalle
    ))


def cerrarOperacionSinPago(
    tnTipoDetalle,
    tnDetalle,
    tcConcepto,
    txUsuarioData=None
):
    loConn = getConnection()
    loCursor = loConn.cursor()
    tnUsr = obtenerUsuarioActualId(txUsuarioData)

    try:
        if tnTipoDetalle == gnTipoDetalleOperacion:
            loCursor.execute("""
                UPDATE OPERACION
                SET
                    Estado = ?,
                    FechaModificacion = datetime('now','localtime')
                WHERE Operacion = ?
            """, (
                gnEstadoOperacionCerrada,
                tnDetalle
            ))

        insertarBitacora(
            loCursor,
            tnUsr,
            "FINALIZAR_OPERACION_SIN_PAGO",
            "OPERACION" if tnTipoDetalle == gnTipoDetalleOperacion else "DETALLE",
            tnDetalle,
            f"Se finalizó el cobro sin pago. TipoDetalle={tnTipoDetalle}, Detalle={tnDetalle}, Concepto={tcConcepto}, Monto=Bs 0.00"
        )

        loConn.commit()

        return {
            "Detalle": tnDetalle
        }

    except Exception:
        loConn.rollback()
        raise
    finally:
        loConn.close()