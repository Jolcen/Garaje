from datetime import datetime

from database.db import getConnection
from servicios.pagoService import (
    obtenerUsuarioActualId,
    insertarBitacora,
    marcarOperacionPagada,
    getFechaHoraActualTexto,
)


# =========================================================
# CONSTANTES
# =========================================================
gnMetodoPagoEfectivo = 1

gnEstadoPagoRegistrado = 1

gnTipoDetalleOperacion = 1
gnTipoDetalleContrato = 2


# =========================================================
# SERVICIO DE PAGO EN EFECTIVO
# =========================================================
def registrarPagoEfectivo(
    tnTipoDetalle,
    tnDetalle,
    tcConcepto,
    tnMonto,
    txUsuarioData=None
):
    loConn = getConnection()
    loCursor = loConn.cursor()
    tnUsr = obtenerUsuarioActualId(txUsuarioData)

    try:
        tnMonto = float(tnMonto)

        if tnMonto <= 0:
            raise ValueError("El monto debe ser mayor a 0.")

        tnOperacion = tnDetalle if tnTipoDetalle == gnTipoDetalleOperacion else None

        loCursor.execute("""
            INSERT INTO PAGO (
                Operacion,
                TipoDetalle,
                Detalle,
                Concepto,
                FechaPago,
                MetodoPago,
                Monto,
                Estado,
                Usr,
                UsrFecha,
                UsrHora,
                FechaCreacion,
                FechaModificacion
            )
            VALUES (
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                date('now','localtime'),
                time('now','localtime'),
                datetime('now','localtime'),
                datetime('now','localtime')
            )
        """, (
            tnOperacion,
            tnTipoDetalle,
            tnDetalle,
            tcConcepto,
            getFechaHoraActualTexto(),
            gnMetodoPagoEfectivo,
            tnMonto,
            gnEstadoPagoRegistrado,
            tnUsr
        ))

        tnPago = loCursor.lastrowid

        marcarOperacionPagada(loCursor, tnTipoDetalle, tnDetalle)

        insertarBitacora(
            loCursor,
            tnUsr,
            "REGISTRAR_COBRO_EFECTIVO",
            "PAGO",
            tnPago,
            f"Se registró cobro en efectivo. TipoDetalle={tnTipoDetalle}, Detalle={tnDetalle}, Monto=Bs {tnMonto:.2f}"
        )

        loConn.commit()

        return {
            "Pago": tnPago
        }

    except Exception:
        loConn.rollback()
        raise
    finally:
        loConn.close()