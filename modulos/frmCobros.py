import json
import re
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from urllib import request, error

from database.db import getConnection


# =========================================================
# CONSTANTES
# =========================================================
gnMetodoPagoEfectivo = 1
gnMetodoPagoQr = 2

gnEstadoPagoRegistrado = 1
gnEstadoPagoAnulado = 2

gnTipoDetalleOperacion = 1
gnTipoDetalleContrato = 2

gnEstadoTransaccionPreparado = 1
gnEstadoTransaccionPendiente = 2
gnEstadoTransaccionPagado = 3
gnEstadoTransaccionFallido = 4
gnEstadoTransaccionAnulado = 5
gnEstadoTransaccionExpirado = 6

gnEstadoOperacionAbierta = 1
gnEstadoOperacionCerrada = 2
gnEstadoOperacionPagada = 3
gnEstadoOperacionCancelada = 4

gnMonedaDolares = 1
gnMonedaBolivianos = 2


# =========================================================
# CONFIGURACIÓN YAPE / PAGOFÁCIL
# Completa estos datos cuando te entreguen credenciales reales.
# =========================================================
gcPagoFacilBaseUrl = "https://serviciossolipago.pagofacil.com.bo"
gcPagoFacilTokenService = ""
gcPagoFacilTokenSecret = ""
gcPagoFacilCommerceId = ""
gcPagoFacilUrlCallback = ""
gcPagoFacilUrlReturn = ""

# Mientras no tengas credenciales reales, déjalo en False.
# Cuando ya tengas todo listo, cámbialo a True.
glQrIntegracionActiva = False


gxMetodoPagoTexto = {
    gnMetodoPagoEfectivo: "Efectivo",
    gnMetodoPagoQr: "QR",
}

gxMetodoPagoInv = {tcValor: tnClave for tnClave, tcValor in gxMetodoPagoTexto.items()}

gxTipoDetalleTexto = {
    gnTipoDetalleOperacion: "Operación",
    gnTipoDetalleContrato: "Contrato",
}


# =========================================================
# UTILIDADES
# =========================================================
def obtenerUsuarioActualId(txUsuarioData):
    if not txUsuarioData:
        return 0
    return txUsuarioData.get("Usuario", 0)


def getFechaHoraActualTexto():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def esTelefonoValido(tcTelefono):
    return bool(re.fullmatch(r"\d{7,8}", (tcTelefono or "").strip()))


def limpiarTexto(tcValor):
    if tcValor is None:
        return ""
    return str(tcValor).strip()


def ejecutarPostJson(tcUrl, txPayload, tcBearerToken=None, tnTimeout=30):
    laData = json.dumps(txPayload).encode("utf-8")

    laHeaders = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    if tcBearerToken:
        laHeaders["Authorization"] = f"Bearer {tcBearerToken}"

    loRequest = request.Request(
        tcUrl,
        data=laData,
        headers=laHeaders,
        method="POST"
    )

    try:
        with request.urlopen(loRequest, timeout=tnTimeout) as loResponse:
            lcBody = loResponse.read().decode("utf-8")
            if not lcBody:
                return {}
            return json.loads(lcBody)
    except error.HTTPError as toError:
        try:
            lcErrorBody = toError.read().decode("utf-8")
            if lcErrorBody:
                try:
                    txErrorJson = json.loads(lcErrorBody)
                    raise RuntimeError(txErrorJson.get("message") or txErrorJson.get("messageSistema") or lcErrorBody)
                except json.JSONDecodeError:
                    raise RuntimeError(lcErrorBody)
        except Exception:
            pass
        raise RuntimeError(f"Error HTTP {toError.code} al consumir el servicio.")
    except error.URLError as toError:
        raise RuntimeError(f"No se pudo conectar con PagoFácil/Yape. {toError.reason}")
    except json.JSONDecodeError:
        raise RuntimeError("La respuesta del servicio no tiene formato JSON válido.")


# =========================================================
# API YAPE / PAGOFÁCIL
# =========================================================
def autenticarPagoFacil():
    if not gcPagoFacilTokenService or not gcPagoFacilTokenSecret:
        raise RuntimeError("Faltan TokenService o TokenSecret en la configuración de PagoFácil.")

    txPayload = {
        "TokenService": gcPagoFacilTokenService,
        "TokenSecret": gcPagoFacilTokenSecret
    }

    txRespuesta = ejecutarPostJson(
        f"{gcPagoFacilBaseUrl}/api/auth/login",
        txPayload
    )

    if txRespuesta.get("error") != 0 or txRespuesta.get("status") != 1:
        raise RuntimeError(txRespuesta.get("message") or txRespuesta.get("messageSistema") or "No se pudo autenticar con PagoFácil.")

    tcAccessToken = (
        txRespuesta.get("values", {}).get("AccessToken")
        or txRespuesta.get("values", {}).get("accessToken")
    )

    if not tcAccessToken:
        raise RuntimeError("La autenticación no devolvió AccessToken.")

    return tcAccessToken, txRespuesta


def prepararPagoYape(tcAccessToken, txPagoQrData):
    if not gcPagoFacilCommerceId:
        raise RuntimeError("Falta tcCommerceID en la configuración de PagoFácil.")

    txPayload = {
        "tcCommerceID": gcPagoFacilCommerceId,
        "tcNombreCliente": txPagoQrData["NombreCliente"],
        "tcCodigoClienteEmpresa": txPagoQrData["CodigoClienteEmpresa"],
        "tnTelefonoEnvio": txPagoQrData["TelefonoEnvio"],
        "tnTelefonoBcp": txPagoQrData["TelefonoCuentaQr"],
        "tcCorreo": txPagoQrData["Correo"],
        "tcNroPago": txPagoQrData["NumeroPagoEmpresa"],
        "tnMontoTotal": f"{float(txPagoQrData['MontoTotalQr']):.2f}",
        "tnMoneda": txPagoQrData["Moneda"],
        "tcUrlCallBack": gcPagoFacilUrlCallback,
        "tcUrlReturn": gcPagoFacilUrlReturn,
        "taPedidoDetalle": txPagoQrData["PedidoDetalle"],
    }

    txRespuesta = ejecutarPostJson(
        f"{gcPagoFacilBaseUrl}/api/servicios/prepararPagoSoli",
        txPayload,
        tcBearerToken=tcAccessToken
    )

    if txRespuesta.get("error") != 0 or txRespuesta.get("status") != 1:
        raise RuntimeError(txRespuesta.get("message") or txRespuesta.get("messageSistema") or "No se pudo preparar el pago QR.")

    txValues = txRespuesta.get("values", {})

    return {
        "Respuesta": txRespuesta,
        "NumeroTransaccionQr": str(txValues.get("tnNroTransaccion", "")),
        "NumeroAutorizacionQr": str(
            txValues.get("TnNroAutorizacion", "")
            or txValues.get("tnNroAutorizacion", "")
        ),
        "Mensaje": txRespuesta.get("message", ""),
        "MensajeSistema": txRespuesta.get("messageSistema", ""),
        "PayloadEnviado": txPayload,
    }


def confirmarPagoYape(tcAccessToken, txConfirmacionData):
    txPayload = {
        "tnCliente": txConfirmacionData["ClienteEmpresa"],
        "tnNroTransaccion": txConfirmacionData["NumeroTransaccionQr"],
        "tnNroAutorizacion": txConfirmacionData["NumeroAutorizacionQr"],
        "tcCodigoPago": txConfirmacionData["CodigoPago"],
    }

    txRespuesta = ejecutarPostJson(
        f"{gcPagoFacilBaseUrl}/api/servicios/confirmarPagoSoli",
        txPayload,
        tcBearerToken=tcAccessToken
    )

    if txRespuesta.get("error") != 0 or txRespuesta.get("status") != 1:
        raise RuntimeError(txRespuesta.get("message") or txRespuesta.get("messageSistema") or "No se pudo confirmar el pago QR.")

    return {
        "Respuesta": txRespuesta,
        "Mensaje": txRespuesta.get("message", ""),
        "MensajeSistema": txRespuesta.get("messageSistema", ""),
    }


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
# ACTUALIZACIONES DE BD
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
        if float(tnMonto) <= 0:
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
            float(tnMonto),
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
            f"Se registró cobro en efectivo. TipoDetalle={tnTipoDetalle}, Detalle={tnDetalle}, Monto=Bs {float(tnMonto):.2f}"
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


def prepararRegistroPagoQr(
    tnTipoDetalle,
    tnDetalle,
    tcConcepto,
    tnMonto,
    txQrData,
    txUsuarioData=None
):
    loConn = getConnection()
    loCursor = loConn.cursor()
    tnUsr = obtenerUsuarioActualId(txUsuarioData)

    try:
        if float(tnMonto) <= 0:
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
            gnMetodoPagoQr,
            float(tnMonto),
            gnEstadoPagoRegistrado,
            tnUsr
        ))

        tnPago = loCursor.lastrowid
        lcNumeroPagoEmpresa = f"PAGO-{tnPago}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        lcNumeroTransaccionQr = ""
        lcNumeroAutorizacionQr = ""
        lcMensaje = "Cobro QR preparado localmente."
        lcMensajeSistema = ""
        lcJsonPreparacion = ""
        lcDetallePedidoJson = json.dumps(txQrData["PedidoDetalle"], ensure_ascii=False)

        if glQrIntegracionActiva:
            tcAccessToken, _ = autenticarPagoFacil()

            txPreparacion = prepararPagoYape(
                tcAccessToken,
                {
                    "NombreCliente": txQrData["NombreCliente"],
                    "CodigoClienteEmpresa": txQrData["CodigoClienteEmpresa"],
                    "TelefonoEnvio": txQrData["TelefonoEnvio"],
                    "TelefonoCuentaQr": txQrData["TelefonoCuentaQr"],
                    "Correo": txQrData["Correo"],
                    "NumeroPagoEmpresa": lcNumeroPagoEmpresa,
                    "MontoTotalQr": float(tnMonto),
                    "Moneda": gnMonedaBolivianos,
                    "PedidoDetalle": txQrData["PedidoDetalle"],
                }
            )

            lcNumeroTransaccionQr = txPreparacion["NumeroTransaccionQr"]
            lcNumeroAutorizacionQr = txPreparacion["NumeroAutorizacionQr"]
            lcMensaje = txPreparacion["Mensaje"]
            lcMensajeSistema = txPreparacion["MensajeSistema"]
            lcJsonPreparacion = json.dumps(txPreparacion["Respuesta"], ensure_ascii=False)

        loCursor.execute("""
            INSERT INTO PAGOQR (
                Pago,
                Cliente,
                NumeroPagoEmpresa,
                MontoTotalQr,
                NumeroTransaccionQr,
                NumeroAutorizacionQr,
                CodigoClienteEmpresa,
                TelefonoEnvio,
                TelefonoCuentaQr,
                Correo,
                Moneda,
                EstadoTransaccion,
                Mensaje,
                MensajeSistema,
                UrlCallback,
                UrlRetorno,
                DetallePedidoJson,
                JsonRespuestaPreparacion,
                FechaHoraPreparacion,
                Usr,
                UsrFecha,
                UsrHora,
                FechaCreacion,
                FechaModificacion
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                date('now','localtime'),
                time('now','localtime'),
                datetime('now','localtime'),
                datetime('now','localtime')
            )
        """, (
            tnPago,
            txQrData["Cliente"],
            lcNumeroPagoEmpresa,
            float(tnMonto),
            lcNumeroTransaccionQr,
            lcNumeroAutorizacionQr,
            txQrData["CodigoClienteEmpresa"],
            txQrData["TelefonoEnvio"],
            txQrData["TelefonoCuentaQr"],
            txQrData["Correo"],
            gnMonedaBolivianos,
            gnEstadoTransaccionPreparado,
            lcMensaje,
            lcMensajeSistema,
            gcPagoFacilUrlCallback,
            gcPagoFacilUrlReturn,
            lcDetallePedidoJson,
            lcJsonPreparacion,
            getFechaHoraActualTexto(),
            tnUsr
        ))

        tnPagoQr = loCursor.lastrowid

        insertarBitacora(
            loCursor,
            tnUsr,
            "PREPARAR_COBRO_QR",
            "PAGOQR",
            tnPagoQr,
            f"Se preparó cobro QR. Pago={tnPago}, Monto=Bs {float(tnMonto):.2f}, NumeroPagoEmpresa={lcNumeroPagoEmpresa}"
        )

        loConn.commit()

        return {
            "Pago": tnPago,
            "PagoQr": tnPagoQr,
            "Cliente": txQrData["Cliente"],
            "CodigoClienteEmpresa": txQrData["CodigoClienteEmpresa"],
            "NumeroPagoEmpresa": lcNumeroPagoEmpresa,
            "NumeroTransaccionQr": lcNumeroTransaccionQr,
            "NumeroAutorizacionQr": lcNumeroAutorizacionQr,
            "Mensaje": lcMensaje,
            "MensajeSistema": lcMensajeSistema,
        }

    except Exception:
        loConn.rollback()
        raise
    finally:
        loConn.close()


def confirmarRegistroPagoQr(
    tnPagoQr,
    tnTipoDetalle,
    tnDetalle,
    tcCodigoPago,
    txUsuarioData=None
):
    loConn = getConnection()
    loCursor = loConn.cursor()
    tnUsr = obtenerUsuarioActualId(txUsuarioData)

    try:
        tcCodigoPago = limpiarTexto(tcCodigoPago)
        if not tcCodigoPago:
            raise ValueError("Debes ingresar el código de pago.")

        loCursor.execute("""
            SELECT
                pq.PagoQr,
                pq.Pago,
                pq.CodigoClienteEmpresa,
                pq.NumeroTransaccionQr,
                pq.NumeroAutorizacionQr,
                pq.EstadoTransaccion
            FROM PAGOQR pq
            WHERE pq.PagoQr = ?
        """, (tnPagoQr,))
        loFila = loCursor.fetchone()

        if not loFila:
            raise ValueError("No se encontró el registro PAGOQR.")

        if int(loFila[5]) == gnEstadoTransaccionPagado:
            raise ValueError("Este cobro QR ya fue confirmado anteriormente.")

        lcCodigoClienteEmpresa = limpiarTexto(loFila[2])
        lcNumeroTransaccionQr = limpiarTexto(loFila[3])
        lcNumeroAutorizacionQr = limpiarTexto(loFila[4])

        lcMensaje = "Pago QR confirmado localmente."
        lcMensajeSistema = ""
        lcJsonConfirmacion = ""

        if glQrIntegracionActiva:
            if not lcCodigoClienteEmpresa:
                raise ValueError("Falta CodigoClienteEmpresa para confirmar el pago.")

            if not lcNumeroTransaccionQr or not lcNumeroAutorizacionQr:
                raise ValueError("Faltan NumeroTransaccionQr o NumeroAutorizacionQr para confirmar el pago.")

            tcAccessToken, _ = autenticarPagoFacil()

            txConfirmacion = confirmarPagoYape(
                tcAccessToken,
                {
                    "ClienteEmpresa": lcCodigoClienteEmpresa,
                    "NumeroTransaccionQr": lcNumeroTransaccionQr,
                    "NumeroAutorizacionQr": lcNumeroAutorizacionQr,
                    "CodigoPago": tcCodigoPago,
                }
            )

            lcMensaje = txConfirmacion["Mensaje"]
            lcMensajeSistema = txConfirmacion["MensajeSistema"]
            lcJsonConfirmacion = json.dumps(txConfirmacion["Respuesta"], ensure_ascii=False)

        loCursor.execute("""
            UPDATE PAGOQR
            SET
                EstadoTransaccion = ?,
                CodigoPago = ?,
                Mensaje = ?,
                MensajeSistema = ?,
                JsonRespuestaConfirmacion = ?,
                FechaHoraConfirmacion = ?,
                FechaHoraFinalizacion = ?,
                FechaModificacion = datetime('now','localtime')
            WHERE PagoQr = ?
        """, (
            gnEstadoTransaccionPagado,
            tcCodigoPago,
            lcMensaje,
            lcMensajeSistema,
            lcJsonConfirmacion,
            getFechaHoraActualTexto(),
            getFechaHoraActualTexto(),
            tnPagoQr
        ))

        marcarOperacionPagada(loCursor, tnTipoDetalle, tnDetalle)

        insertarBitacora(
            loCursor,
            tnUsr,
            "CONFIRMAR_COBRO_QR",
            "PAGOQR",
            tnPagoQr,
            f"Se confirmó cobro QR. PagoQr={tnPagoQr}, Detalle={tnDetalle}"
        )

        loConn.commit()

        return {
            "PagoQr": tnPagoQr,
            "Mensaje": lcMensaje,
            "MensajeSistema": lcMensajeSistema,
        }

    except Exception:
        loConn.rollback()
        raise
    finally:
        loConn.close()


# =========================================================
# FORMULARIO
# =========================================================
class FrmCobros(tk.Toplevel):
    def __init__(
        self,
        toMaster,
        txUsuarioData,
        tnTipoDetalle,
        tnDetalle,
        tcConcepto,
        tnMonto,
        tfOnSave=None
    ):
        super().__init__(toMaster)

        self.txUsuarioData = txUsuarioData or {}
        self.tnTipoDetalle = tnTipoDetalle
        self.tnDetalle = tnDetalle
        self.tcConcepto = tcConcepto
        self.tnMonto = float(tnMonto)
        self.tfOnSave = tfOnSave

        self.txContexto = obtenerContextoDetalle(self.tnTipoDetalle, self.tnDetalle)
        self.txQrActual = None

        self.title("Registrar cobro")
        self.geometry("640x650")
        self.resizable(False, True)
        self.configure(bg="#f4f6f8")
        self.transient(toMaster)
        self.grab_set()

        self.lovMetodoPago = tk.StringVar(value="Efectivo")
        self.lovNombreCliente = tk.StringVar(value=limpiarTexto(self.txContexto.get("NombreCliente", "")))
        self.lovCodigoClienteEmpresa = tk.StringVar(
            value=str(self.txContexto.get("Cliente", "") or self.tnDetalle)
        )
        self.lovTelefonoEnvio = tk.StringVar(value=limpiarTexto(self.txContexto.get("Telefono", "")))
        self.lovTelefonoCuentaQr = tk.StringVar(value=limpiarTexto(self.txContexto.get("Telefono", "")))
        self.lovCorreo = tk.StringVar(value="")
        self.lovCodigoPago = tk.StringVar(value="")

        self.buildUi()
        self.centerWindow()
        self.toggleQrSection()

    def centerWindow(self):
        self.update_idletasks()
        lnWidth = self.winfo_width()
        lnHeight = self.winfo_height()
        lnPosX = int((self.winfo_screenwidth() / 2) - (lnWidth / 2))
        lnPosY = int((self.winfo_screenheight() / 2) - (lnHeight / 2))
        self.geometry(f"{lnWidth}x{lnHeight}+{lnPosX}+{lnPosY}")

    def buildUi(self):
        lofrmContainer = tk.Frame(self, bg="#f4f6f8")
        lofrmContainer.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(
            lofrmContainer,
            text="Registrar cobro",
            font=("Arial", 16, "bold"),
            bg="#f4f6f8",
            fg="#111827"
        ).pack(anchor="w", pady=(0, 12))

        lofrmCard = tk.Frame(lofrmContainer, bg="white", bd=1, relief="solid")
        lofrmCard.pack(fill="both", expand=True)

        lofrmCard.columnconfigure(1, weight=1)

        self.addInfoRow(lofrmCard, "Tipo:", gxTipoDetalleTexto.get(self.tnTipoDetalle, "N/D"), 0)
        self.addInfoRow(lofrmCard, "Referencia:", str(self.tnDetalle), 1)
        self.addInfoRow(lofrmCard, "Concepto:", self.tcConcepto, 2)
        self.addInfoRow(lofrmCard, "Monto:", f"Bs {self.tnMonto:.2f}", 3)

        tk.Label(
            lofrmCard,
            text="Método de pago:",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#374151"
        ).grid(row=4, column=0, sticky="w", padx=14, pady=(14, 6))

        self.locboMetodo = ttk.Combobox(
            lofrmCard,
            textvariable=self.lovMetodoPago,
            values=list(gxMetodoPagoInv.keys()),
            state="readonly",
            width=20
        )
        self.locboMetodo.grid(row=4, column=1, sticky="w", padx=(0, 14), pady=(14, 6))
        self.locboMetodo.bind("<<ComboboxSelected>>", lambda event: self.toggleQrSection())

        self.lblInfoQr = tk.Label(
            lofrmCard,
            text="Si eliges QR, primero se prepara el cobro y luego se confirma con el código de pago.",
            font=("Arial", 9),
            bg="white",
            fg="#6b7280",
            wraplength=500,
            justify="left"
        )
        self.lblInfoQr.grid(row=5, column=0, columnspan=2, sticky="w", padx=14, pady=(6, 10))

        self.lofrmQr = tk.Frame(lofrmCard, bg="white")
        self.lofrmQr.grid(row=6, column=0, columnspan=2, sticky="nsew", padx=14, pady=(0, 10))
        self.lofrmQr.columnconfigure(1, weight=1)

        self.addEntryRow(self.lofrmQr, "Nombre cliente:", self.lovNombreCliente, 0)
        self.addEntryRow(self.lofrmQr, "Código cliente empresa:", self.lovCodigoClienteEmpresa, 1)
        self.addEntryRow(self.lofrmQr, "Teléfono envío:", self.lovTelefonoEnvio, 2)
        self.addEntryRow(self.lofrmQr, "Teléfono cuenta QR:", self.lovTelefonoCuentaQr, 3)
        self.addEntryRow(self.lofrmQr, "Correo:", self.lovCorreo, 4)
        self.addEntryRow(self.lofrmQr, "Código pago:", self.lovCodigoPago, 5, state="disabled")

        self.lblEstadoQr = tk.Label(
            self.lofrmQr,
            text="",
            font=("Arial", 9),
            bg="white",
            fg="#1f2937",
            wraplength=500,
            justify="left"
        )
        self.lblEstadoQr.grid(row=6, column=0, columnspan=2, sticky="w", pady=(8, 0))

        lofrmBotones = tk.Frame(lofrmContainer, bg="#f4f6f8")
        lofrmBotones.pack(fill="x", pady=(12, 0))

        self.btnConfirmarQr = tk.Button(
            lofrmBotones,
            text="Confirmar QR",
            font=("Arial", 10, "bold"),
            bg="#2563eb",
            fg="white",
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            state="disabled",
            command=self.confirmQrPayment
        )
        self.btnConfirmarQr.pack(side="right", padx=(8, 0))

        self.btnGuardar = tk.Button(
            lofrmBotones,
            text="Guardar cobro",
            font=("Arial", 10, "bold"),
            bg="#059669",
            fg="white",
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            command=self.savePayment
        )
        self.btnGuardar.pack(side="right", padx=(8, 0))

        tk.Button(
            lofrmBotones,
            text="Cancelar",
            font=("Arial", 10, "bold"),
            bg="#6b7280",
            fg="white",
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            command=self.destroy
        ).pack(side="right")

    def addInfoRow(self, toParent, tcLabel, tcValue, tnRow):
        tk.Label(
            toParent,
            text=tcLabel,
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#374151"
        ).grid(row=tnRow, column=0, sticky="w", padx=14, pady=(14, 6))

        tk.Label(
            toParent,
            text=tcValue,
            font=("Arial", 10),
            bg="white",
            fg="#111827",
            anchor="w",
            justify="left"
        ).grid(row=tnRow, column=1, sticky="w", padx=(0, 14), pady=(14, 6))

    def addEntryRow(self, toParent, tcLabel, tvVariable, tnRow, state="normal"):
        tk.Label(
            toParent,
            text=tcLabel,
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#374151"
        ).grid(row=tnRow, column=0, sticky="w", pady=(8, 4))

        loEntry = tk.Entry(
            toParent,
            textvariable=tvVariable,
            font=("Arial", 10),
            width=36,
            state=state
        )
        loEntry.grid(row=tnRow, column=1, sticky="we", padx=(10, 0), pady=(8, 4))

        if tcLabel == "Código pago:":
            self.txtCodigoPago = loEntry

        return loEntry

    def toggleQrSection(self):
        lcMetodoPago = self.lovMetodoPago.get().strip()
        llEsQr = lcMetodoPago == "QR"

        if llEsQr:
            self.lofrmQr.grid()
            self.lblInfoQr.configure(
                text="Para QR/Yape se preparará el cobro. Si la integración aún está desactivada, se hará una preparación local de prueba."
            )
            self.geometry("640x650")
        else:
            self.lofrmQr.grid_remove()
            self.lblInfoQr.configure(
                text="Cobro en efectivo: registra el pago y marca la operación como pagada."
            )
            self.btnConfirmarQr.config(state="disabled")
            self.txtCodigoPago.config(state="disabled")
            self.lblEstadoQr.config(text="")
            self.geometry("640x430")

        self.centerWindow()

    def construirDatosQr(self):
        lcNombreCliente = limpiarTexto(self.lovNombreCliente.get())
        lcCodigoClienteEmpresa = limpiarTexto(self.lovCodigoClienteEmpresa.get())
        lcTelefonoEnvio = limpiarTexto(self.lovTelefonoEnvio.get())
        lcTelefonoCuentaQr = limpiarTexto(self.lovTelefonoCuentaQr.get())
        lcCorreo = limpiarTexto(self.lovCorreo.get())

        if not lcNombreCliente:
            raise ValueError("Debes ingresar el nombre del cliente.")

        if not lcCodigoClienteEmpresa:
            raise ValueError("Debes ingresar el código cliente empresa.")

        if not esTelefonoValido(lcTelefonoEnvio):
            raise ValueError("El teléfono de envío debe tener 7 u 8 dígitos.")

        if not esTelefonoValido(lcTelefonoCuentaQr):
            raise ValueError("El teléfono de la cuenta QR debe tener 7 u 8 dígitos.")

        txPedidoDetalle = [
            {
                "Serial": 1,
                "Producto": self.tcConcepto,
                "Cantidad": 1,
                "Precio": f"{self.tnMonto:.2f}",
                "Descuento": "0",
                "Total": f"{self.tnMonto:.2f}"
            }
        ]

        return {
            "Cliente": self.txContexto.get("Cliente"),
            "NombreCliente": lcNombreCliente,
            "CodigoClienteEmpresa": lcCodigoClienteEmpresa,
            "TelefonoEnvio": lcTelefonoEnvio,
            "TelefonoCuentaQr": lcTelefonoCuentaQr,
            "Correo": lcCorreo,
            "PedidoDetalle": txPedidoDetalle
        }

    def savePayment(self):
        try:
            if self.tnMonto <= 0:
                raise ValueError("El monto debe ser mayor a 0.")

            lcMetodoPago = self.lovMetodoPago.get().strip()

            if lcMetodoPago not in gxMetodoPagoInv:
                raise ValueError("Debes seleccionar un método de pago válido.")

            tnMetodoPago = gxMetodoPagoInv[lcMetodoPago]

            if tnMetodoPago == gnMetodoPagoEfectivo:
                llOk = messagebox.askyesno(
                    "Confirmar cobro",
                    f"¿Deseas registrar el cobro en efectivo por Bs {self.tnMonto:.2f}?"
                )
                if not llOk:
                    return

                txResultado = registrarPagoEfectivo(
                    tnTipoDetalle=self.tnTipoDetalle,
                    tnDetalle=self.tnDetalle,
                    tcConcepto=self.tcConcepto,
                    tnMonto=self.tnMonto,
                    txUsuarioData=self.txUsuarioData
                )

                if self.tfOnSave:
                    self.tfOnSave(txResultado["Pago"])

                messagebox.showinfo(
                    "Éxito",
                    f"Cobro registrado correctamente.\nNro. Pago: {txResultado['Pago']}"
                )
                self.destroy()
                return

            txQrData = self.construirDatosQr()

            llOk = messagebox.askyesno(
                "Preparar cobro QR",
                f"¿Deseas preparar el cobro QR por Bs {self.tnMonto:.2f}?"
            )
            if not llOk:
                return

            txResultadoQr = prepararRegistroPagoQr(
                tnTipoDetalle=self.tnTipoDetalle,
                tnDetalle=self.tnDetalle,
                tcConcepto=self.tcConcepto,
                tnMonto=self.tnMonto,
                txQrData=txQrData,
                txUsuarioData=self.txUsuarioData
            )

            self.txQrActual = txResultadoQr
            self.txtCodigoPago.config(state="normal")
            self.btnConfirmarQr.config(state="normal")
            self.btnGuardar.config(state="disabled")

            lcEstado = (
                f"QR preparado.\n"
                f"Nro. Pago: {txResultadoQr['Pago']}\n"
                f"Nro. Pago Empresa: {txResultadoQr['NumeroPagoEmpresa']}\n"
            )

            if txResultadoQr["NumeroTransaccionQr"]:
                lcEstado += f"Nro. Transacción: {txResultadoQr['NumeroTransaccionQr']}\n"

            if txResultadoQr["NumeroAutorizacionQr"]:
                lcEstado += f"Nro. Autorización: {txResultadoQr['NumeroAutorizacionQr']}\n"

            if txResultadoQr["Mensaje"]:
                lcEstado += f"Mensaje: {txResultadoQr['Mensaje']}"

            self.lblEstadoQr.config(text=lcEstado)

            messagebox.showinfo(
                "QR preparado",
                "El cobro QR fue preparado correctamente.\nAhora ingresa el código de pago y presiona 'Confirmar QR'."
            )

        except Exception as toError:
            messagebox.showerror(
                "Error",
                f"No se pudo procesar el cobro.\n{str(toError)}"
            )

    def confirmQrPayment(self):
        try:
            if not self.txQrActual:
                raise ValueError("Primero debes preparar el cobro QR.")

            lcCodigoPago = limpiarTexto(self.lovCodigoPago.get())
            if not lcCodigoPago:
                raise ValueError("Debes ingresar el código de pago.")

            llOk = messagebox.askyesno(
                "Confirmar pago QR",
                "¿Deseas confirmar el pago QR con el código ingresado?"
            )
            if not llOk:
                return

            txConfirmacion = confirmarRegistroPagoQr(
                tnPagoQr=self.txQrActual["PagoQr"],
                tnTipoDetalle=self.tnTipoDetalle,
                tnDetalle=self.tnDetalle,
                tcCodigoPago=lcCodigoPago,
                txUsuarioData=self.txUsuarioData
            )

            if self.tfOnSave:
                self.tfOnSave(self.txQrActual["Pago"])

            messagebox.showinfo(
                "Éxito",
                "Pago QR confirmado correctamente."
            )

            self.destroy()

        except Exception as toError:
            messagebox.showerror(
                "Error",
                f"No se pudo confirmar el pago QR.\n{str(toError)}"
            )