import os
import json
import uuid
import requests
from datetime import datetime

from dotenv import load_dotenv

import database.db as db
from servicios.pagoService import (
    obtenerContextoDetalle,
    marcarOperacionPagada,
    insertarBitacora
)


# =========================================================
# CONFIGURACION QR MASTER
# =========================================================

load_dotenv()

gcUrlBase = os.getenv("PAGOFACIL_QR_BASE_URL", "https://masterqr.pagofacil.com.bo/api/services/v2").strip()
gcTokenService = os.getenv("PAGOFACIL_QR_TOKEN_SERVICE", "").strip()
gcTokenSecret = os.getenv("PAGOFACIL_QR_TOKEN_SECRET", "").strip()
gcCallbackUrl = os.getenv("PAGOFACIL_QR_CALLBACK_URL", "").strip()
gnCurrencyQr = int(os.getenv("PAGOFACIL_QR_CURRENCY", "2").strip())

gnTimeoutSegundos = 30


# =========================================================
# CONSTANTES DEL SISTEMA
# =========================================================
gnMetodoPagoQr = 3

gnTipoDetalleOperacion = 1
gnTipoDetalleContrato = 2

gnEstadoPagoRegistrado = 1
gnEstadoPagoAnulado = 2

gnEstadoTransaccionPreparado = 1
gnEstadoTransaccionPendiente = 2
gnEstadoTransaccionPagado = 3
gnEstadoTransaccionFallido = 4
gnEstadoTransaccionAnulado = 5
gnEstadoTransaccionExpirado = 6

gnMoneda = gnCurrencyQr


# =========================================================
# UTILIDADES GENERALES
# =========================================================
def limpiarTexto(tcValor):
    if tcValor is None:
        return ""
    return str(tcValor).strip()


def valorFloat(tnValor, tnDefault=0.0):
    try:
        return float(tnValor)
    except Exception:
        return float(tnDefault)


def valorInt(tnValor, tnDefault=0):
    try:
        return int(tnValor)
    except Exception:
        return int(tnDefault)


def ahoraFecha():
    return datetime.now().strftime("%Y-%m-%d")


def ahoraHora():
    return datetime.now().strftime("%H:%M:%S")


def ahoraFechaHora():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def jsonTexto(txValor):
    try:
        return json.dumps(txValor, ensure_ascii=False, indent=2)
    except Exception:
        return str(txValor)


def obtenerUsuarioId(txUsuarioData):
    if not isinstance(txUsuarioData, dict):
        return 0

    for lcClave in ("Usuario", "usuario", "IdUsuario", "idUsuario", "id"):
        if lcClave in txUsuarioData:
            return valorInt(txUsuarioData.get(lcClave), 0)

    return 0


def validarConfiguracionQr():
    
    if not gcTokenService:
        raise ValueError("Falta configurar PAGOFACIL_QR_TOKEN_SERVICE.")
    if not gcTokenSecret:
        raise ValueError("Falta configurar PAGOFACIL_QR_TOKEN_SECRET.")
    if gnCurrencyQr <= 0:
        raise ValueError("Moneda QR inválida.")


# =========================================================
# HTTP / API
# =========================================================
def postApi(tcEndpoint, txHeaders=None, txBody=None):
    lcUrl = f"{gcUrlBase}{tcEndpoint}"

    loHeaders = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Response-Language": "es",
    }
    if txHeaders:
        loHeaders.update(txHeaders)

    try:
        loResponse = requests.post(
            lcUrl,
            headers=loHeaders,
            json=txBody or {},
            timeout=gnTimeoutSegundos
        )
    except requests.RequestException as toError:
        raise ValueError(f"No se pudo conectar con QR Master: {str(toError)}")

    try:
        txRespuesta = loResponse.json()
    except Exception:
        raise ValueError(
            f"La API QR respondió con un contenido inválido. HTTP {loResponse.status_code}. "
            f"Respuesta: {loResponse.text}"
        )

    if loResponse.status_code >= 400:
        raise ValueError(
            f"Error HTTP {loResponse.status_code}: "
            f"{limpiarTexto(txRespuesta.get('message')) or loResponse.text}"
        )

    if valorInt(txRespuesta.get("error"), 1) != 0:
        raise ValueError(limpiarTexto(txRespuesta.get("message")) or "La API QR devolvió un error.")

    return txRespuesta


def autenticarQrMaster():
    validarConfiguracionQr()

    txHeaders = {
        "tcTokenService": gcTokenService,
        "tcTokenSecret": gcTokenSecret,
    }

    txRespuesta = postApi("/login", txHeaders=txHeaders, txBody={})
    txValores = txRespuesta.get("values") or {}

    lcToken = limpiarTexto(txValores.get("accessToken"))
    if not lcToken:
        raise ValueError("La API QR no devolvió accessToken.")

    return {
        "AccessToken": lcToken,
        "Respuesta": txRespuesta
    }


def listarMetodosHabilitados():
    txLogin = autenticarQrMaster()
    lcToken = txLogin["AccessToken"]

    txHeaders = {
        "Authorization": f"Bearer {lcToken}"
    }

    txRespuesta = postApi("/list-enabled-services", txHeaders=txHeaders, txBody={})
    laValores = txRespuesta.get("values") or []

    return {
        "AccessToken": lcToken,
        "Metodos": laValores,
        "Respuesta": txRespuesta
    }


def obtenerMetodoQrHabilitado():
    txResultado = listarMetodosHabilitados()
    laMetodos = txResultado["Metodos"]

    if not laMetodos:
        raise ValueError("No existen métodos QR habilitados para este comercio.")

    loSeleccionado = laMetodos[0]
    lnPaymentMethodId = valorInt(loSeleccionado.get("paymentMethodId"), 0)

    if lnPaymentMethodId <= 0:
        raise ValueError("No se pudo obtener el paymentMethodId del QR.")

    return {
        "AccessToken": txResultado["AccessToken"],
        "PaymentMethodId": lnPaymentMethodId,
        "Metodo": loSeleccionado,
        "Respuesta": txResultado["Respuesta"]
    }


def generarQrApi(tcNombreCliente, tcDocumento, tcTelefono, tcCorreo, tcNumeroPagoEmpresa,
                 tnMonto, tcCodigoClienteEmpresa, tcConcepto):
    txMetodo = obtenerMetodoQrHabilitado()
    lcToken = txMetodo["AccessToken"]
    lnPaymentMethodId = txMetodo["PaymentMethodId"]

    txHeaders = {
        "Authorization": f"Bearer {lcToken}"
    }

    txBody = {
        "paymentMethod": lnPaymentMethodId,
        "clientName": tcNombreCliente,
        "documentType": 1,
        "documentId": tcDocumento or "0",
        "phoneNumber": tcTelefono or "00000000",
        "email": tcCorreo or "cliente@correo.com",
        "paymentNumber": tcNumeroPagoEmpresa,
        "amount": round(valorFloat(tnMonto), 2),
        "currency": gnCurrencyQr,
        "clientCode": tcCodigoClienteEmpresa or "0",
        "callbackUrl": gcCallbackUrl or None,
        "orderDetail": [
            {
                "serial": 1,
                "product": tcConcepto or "Cobro",
                "quantity": 1,
                "price": round(valorFloat(tnMonto), 2),
                "discount": 0,
                "total": round(valorFloat(tnMonto), 2)
            }
        ]
    }

    if not gcCallbackUrl:
        txBody.pop("callbackUrl", None)

    txRespuesta = postApi("/generate-qr", txHeaders=txHeaders, txBody=txBody)
    txValores = txRespuesta.get("values") or {}

    return {
        "PaymentMethodId": lnPaymentMethodId,
        "Metodo": txMetodo["Metodo"],
        "RequestBody": txBody,
        "Respuesta": txRespuesta,
        "Valores": txValores
    }


def consultarTransaccionApi(tcNumeroPagoEmpresa="", tcNumeroTransaccion=""):
    if not tcNumeroPagoEmpresa and not tcNumeroTransaccion:
        raise ValueError("Debes enviar NumeroPagoEmpresa o NumeroTransaccion.")

    txLogin = autenticarQrMaster()
    lcToken = txLogin["AccessToken"]

    txHeaders = {
        "Authorization": f"Bearer {lcToken}"
    }

    txBody = {}
    if tcNumeroTransaccion:
        txBody["pagofacilTransactionId"] = tcNumeroTransaccion
    if tcNumeroPagoEmpresa:
        txBody["companyTransactionId"] = tcNumeroPagoEmpresa

    txRespuesta = postApi("/query-transaction", txHeaders=txHeaders, txBody=txBody)
    txValores = txRespuesta.get("values") or {}

    return {
        "RequestBody": txBody,
        "Respuesta": txRespuesta,
        "Valores": txValores
    }


# =========================================================
# MAPEOS
# =========================================================
def mapearEstadoGeneracionApi(tnEstadoApi):
    lnEstadoApi = valorInt(tnEstadoApi, 0)

    if lnEstadoApi == 1:
        return gnEstadoTransaccionPendiente

    return gnEstadoTransaccionPreparado


def mapearEstadoConsultaApi(tnEstadoApi):
    lcEstado = limpiarTexto(tnEstadoApi).lower()

    if lcEstado in ("3", "paid", "pagado", "success", "successful", "completed", "completado"):
        return gnEstadoTransaccionPagado

    if lcEstado in ("4", "failed", "fallido", "rechazado", "error"):
        return gnEstadoTransaccionFallido

    if lcEstado in ("5", "annulled", "anulado", "cancelado", "cancelled"):
        return gnEstadoTransaccionAnulado

    if lcEstado in ("6", "expired", "expirado"):
        return gnEstadoTransaccionExpirado

    if lcEstado in ("1", "2", "pending", "pendiente", "prepared", "preparado", ""):
        return gnEstadoTransaccionPendiente

    return gnEstadoTransaccionPendiente


# =========================================================
# DATOS DEL CLIENTE / CONTEXTO
# =========================================================
def obtenerDatosClienteQr(tnTipoDetalle, tnDetalle):
    txContexto = obtenerContextoDetalle(tnTipoDetalle, tnDetalle) or {}

    lcNombreCliente = (
        limpiarTexto(txContexto.get("NombreCliente")) or
        limpiarTexto(txContexto.get("ClienteNombre")) or
        limpiarTexto(txContexto.get("Nombres")) or
        "Cliente"
    )

    lnCliente = valorInt(
        txContexto.get("Cliente")
        or txContexto.get("IdCliente")
        or txContexto.get("ClienteId"),
        0
    )

    lcDocumento = (
        limpiarTexto(txContexto.get("DocumentoIdentidad")) or
        limpiarTexto(txContexto.get("Ci")) or
        "0"
    )

    lcTelefono = (
        limpiarTexto(txContexto.get("Telefono")) or
        limpiarTexto(txContexto.get("Celular")) or
        "00000000"
    )

    lcCorreo = (
        limpiarTexto(txContexto.get("Correo")) or
        limpiarTexto(txContexto.get("Email")) or
        "cliente@correo.com"
    )

    return {
        "Contexto": txContexto,
        "Cliente": lnCliente if lnCliente > 0 else None,
        "NombreCliente": lcNombreCliente,
        "Documento": lcDocumento,
        "Telefono": lcTelefono,
        "Correo": lcCorreo,
        "CodigoClienteEmpresa": str(lnCliente or tnDetalle or 0)
    }


def construirNumeroPagoEmpresa(tnTipoDetalle, tnDetalle):
    lcPrefijo = "OP" if tnTipoDetalle == gnTipoDetalleOperacion else "CT"
    lcFechaHora = datetime.now().strftime("%Y%m%d%H%M%S")
    lcRandom = uuid.uuid4().hex[:6].upper()
    return f"QR-{lcPrefijo}-{tnDetalle}-{lcFechaHora}-{lcRandom}"


# =========================================================
# BASE DE DATOS
# =========================================================
def insertarPagoQrPendiente(
    tnTipoDetalle,
    tnDetalle,
    tcConcepto,
    tnMonto,
    txUsuarioData,
    txDatosCliente,
    txApiGeneracion
):
    loConn = db.getConnection()
    loCursor = loConn.cursor()

    lnUsuario = obtenerUsuarioId(txUsuarioData)
    lcFecha = ahoraFecha()
    lcHora = ahoraHora()
    lcFechaHora = ahoraFechaHora()

    txValores = txApiGeneracion["Valores"]
    txRespuesta = txApiGeneracion["Respuesta"]
    txBody = txApiGeneracion["RequestBody"]

    lcNumeroPagoEmpresa = limpiarTexto(txBody.get("paymentNumber"))
    lcNumeroTransaccion = limpiarTexto(txValores.get("transactionId"))
    lcFechaExpiracion = limpiarTexto(txValores.get("expirationDate"))
    lcQrBase64 = limpiarTexto(txValores.get("qrBase64"))
    lnEstadoTransaccion = mapearEstadoGeneracionApi(txValores.get("status"))

    lnOperacion = tnDetalle if tnTipoDetalle == gnTipoDetalleOperacion else None

    try:
        loCursor.execute(
            """
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lnOperacion,
                tnTipoDetalle,
                tnDetalle,
                tcConcepto,
                lcFecha,
                gnMetodoPagoQr,
                round(valorFloat(tnMonto), 2),
                gnEstadoPagoRegistrado,
                lnUsuario,
                lcFecha,
                lcHora,
                lcFechaHora,
                lcFechaHora
            )
        )
        lnPago = loCursor.lastrowid

        loCursor.execute(
            """
            INSERT INTO PAGODIGITAL (
                Pago,
                Cliente,
                NumeroPagoEmpresa,
                MontoTotal,
                NumeroTransaccion,
                CodigoClienteEmpresa,
                TelefonoEnvio,
                TelefonoCuenta,
                Correo,
                Moneda,
                EstadoTransaccion,
                Mensaje,
                MensajeSistema,
                ReciboBase64,
                UrlCallback,
                DetallePedidoJson,
                JsonRespuestaPreparacion,
                FechaHoraPreparacion,
                FechaHoraExpiracion,
                Usr,
                UsrFecha,
                UsrHora,
                FechaCreacion,
                FechaModificacion
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lnPago,
                txDatosCliente.get("Cliente"),
                lcNumeroPagoEmpresa,
                round(valorFloat(tnMonto), 2),
                lcNumeroTransaccion,
                limpiarTexto(txBody.get("clientCode")),
                limpiarTexto(txBody.get("phoneNumber")),
                limpiarTexto(txBody.get("phoneNumber")),
                limpiarTexto(txBody.get("email")),
                gnMoneda,
                lnEstadoTransaccion,
                limpiarTexto(txRespuesta.get("message")),
                "",
                lcQrBase64,
                limpiarTexto(txBody.get("callbackUrl")),
                jsonTexto(txBody.get("orderDetail")),
                jsonTexto(txRespuesta),
                lcFechaHora,
                lcFechaExpiracion,
                lnUsuario,
                lcFecha,
                lcHora,
                lcFechaHora,
                lcFechaHora
            )
        )

        loConn.commit()
        return lnPago

    except Exception:
        loConn.rollback()
        raise
    finally:
        loConn.close()


def obtenerPagoDigitalPorReferencia(tcNumeroPagoEmpresa="", tcNumeroTransaccion=""):
    if not tcNumeroPagoEmpresa and not tcNumeroTransaccion:
        raise ValueError("Debes enviar NumeroPagoEmpresa o NumeroTransaccion.")

    loConn = db.getConnection()
    loCursor = loConn.cursor()

    try:
        lcSql = """
            SELECT
                p.Pago,
                p.Operacion,
                p.TipoDetalle,
                p.Detalle,
                p.Concepto,
                p.Monto,
                p.Estado AS EstadoPago,
                pd.PagoDigital,
                pd.Cliente,
                pd.NumeroPagoEmpresa,
                pd.MontoTotal,
                pd.NumeroTransaccion,
                pd.Moneda,
                pd.EstadoTransaccion,
                pd.Mensaje,
                pd.MensajeSistema,
                pd.ReciboBase64,
                pd.UrlCallback,
                pd.JsonRespuestaPreparacion,
                pd.JsonRespuestaConfirmacion,
                pd.JsonRespuestaConsulta,
                pd.FechaHoraPreparacion,
                pd.FechaHoraConfirmacion,
                pd.FechaHoraFinalizacion,
                pd.FechaHoraExpiracion
            FROM PAGO p
            INNER JOIN PAGODIGITAL pd ON pd.Pago = p.Pago
            WHERE 1 = 1
        """
        laParams = []

        if tcNumeroPagoEmpresa:
            lcSql += " AND pd.NumeroPagoEmpresa = ?"
            laParams.append(tcNumeroPagoEmpresa)

        if tcNumeroTransaccion:
            lcSql += " AND pd.NumeroTransaccion = ?"
            laParams.append(tcNumeroTransaccion)

        lcSql += " ORDER BY pd.PagoDigital DESC LIMIT 1"

        loCursor.execute(lcSql, laParams)
        loFila = loCursor.fetchone()

        if not loFila:
            raise ValueError("No se encontró el pago digital solicitado.")

        if hasattr(loFila, "keys"):
            return {lcKey: loFila[lcKey] for lcKey in loFila.keys()}

        return {
            "Pago": loFila[0],
            "Operacion": loFila[1],
            "TipoDetalle": loFila[2],
            "Detalle": loFila[3],
            "Concepto": loFila[4],
            "Monto": loFila[5],
            "EstadoPago": loFila[6],
            "PagoDigital": loFila[7],
            "Cliente": loFila[8],
            "NumeroPagoEmpresa": loFila[9],
            "MontoTotal": loFila[10],
            "NumeroTransaccion": loFila[11],
            "Moneda": loFila[12],
            "EstadoTransaccion": loFila[13],
            "Mensaje": loFila[14],
            "MensajeSistema": loFila[15],
            "ReciboBase64": loFila[16],
            "UrlCallback": loFila[17],
            "JsonRespuestaPreparacion": loFila[18],
            "JsonRespuestaConfirmacion": loFila[19],
            "JsonRespuestaConsulta": loFila[20],
            "FechaHoraPreparacion": loFila[21],
            "FechaHoraConfirmacion": loFila[22],
            "FechaHoraFinalizacion": loFila[23],
            "FechaHoraExpiracion": loFila[24],
        }

    finally:
        loConn.close()


def actualizarEstadoConsultaPagoDigital(
    tnPagoDigital,
    tnEstadoTransaccion,
    txRespuestaConsulta,
    tcFechaHoraPago="",
    tcMensaje=""
):
    loConn = db.getConnection()
    loCursor = loConn.cursor()

    lcFecha = ahoraFecha()
    lcHora = ahoraHora()
    lcFechaHora = ahoraFechaHora()

    try:
        loCursor.execute(
            """
            UPDATE PAGODIGITAL
            SET
                EstadoTransaccion = ?,
                Mensaje = ?,
                JsonRespuestaConsulta = ?,
                FechaHoraConfirmacion = CASE
                    WHEN ? = ? THEN ?
                    ELSE FechaHoraConfirmacion
                END,
                FechaHoraFinalizacion = CASE
                    WHEN ? = ? THEN ?
                    ELSE FechaHoraFinalizacion
                END,
                FechaModificacion = ?
            WHERE PagoDigital = ?
            """,
            (
                tnEstadoTransaccion,
                tcMensaje,
                jsonTexto(txRespuestaConsulta),
                tnEstadoTransaccion,
                gnEstadoTransaccionPagado,
                tcFechaHoraPago or lcFechaHora,
                tnEstadoTransaccion,
                gnEstadoTransaccionPagado,
                tcFechaHoraPago or lcFechaHora,
                lcFechaHora,
                tnPagoDigital
            )
        )
        loConn.commit()

    except Exception:
        loConn.rollback()
        raise
    finally:
        loConn.close()


def finalizarDetallePagado(tnTipoDetalle, tnDetalle, txUsuarioData):
    loConn = db.getConnection()
    loCursor = loConn.cursor()

    tnUsr = obtenerUsuarioId(txUsuarioData)

    try:
        marcarOperacionPagada(loCursor, tnTipoDetalle, tnDetalle)

        insertarBitacora(
            loCursor,
            tnUsr,
            "PAGO_QR_CONFIRMADO",
            "OPERACION" if tnTipoDetalle == gnTipoDetalleOperacion else "DETALLE",
            tnDetalle,
            f"Pago QR confirmado. TipoDetalle={tnTipoDetalle}, Detalle={tnDetalle}"
        )

        loConn.commit()

    except Exception:
        loConn.rollback()
        raise
    finally:
        loConn.close()


# =========================================================
# FUNCIONES PRINCIPALES PARA EL FORMULARIO
# =========================================================
def generarPagoQr(tnTipoDetalle, tnDetalle, tcConcepto, tnMonto, txUsuarioData):
    tnMonto = valorFloat(tnMonto)

    if tnMonto <= 0:
        raise ValueError("El monto debe ser mayor a 0 para generar QR.")

    txDatosCliente = obtenerDatosClienteQr(tnTipoDetalle, tnDetalle)
    lcNumeroPagoEmpresa = construirNumeroPagoEmpresa(tnTipoDetalle, tnDetalle)

    txApiGeneracion = generarQrApi(
        tcNombreCliente=txDatosCliente["NombreCliente"],
        tcDocumento=txDatosCliente["Documento"],
        tcTelefono=txDatosCliente["Telefono"],
        tcCorreo=txDatosCliente["Correo"],
        tcNumeroPagoEmpresa=lcNumeroPagoEmpresa,
        tnMonto=tnMonto,
        tcCodigoClienteEmpresa=txDatosCliente["CodigoClienteEmpresa"],
        tcConcepto=tcConcepto
    )

    lnPago = insertarPagoQrPendiente(
        tnTipoDetalle=tnTipoDetalle,
        tnDetalle=tnDetalle,
        tcConcepto=tcConcepto,
        tnMonto=tnMonto,
        txUsuarioData=txUsuarioData,
        txDatosCliente=txDatosCliente,
        txApiGeneracion=txApiGeneracion
    )

    txValores = txApiGeneracion["Valores"]
    txRespuesta = txApiGeneracion["Respuesta"]

    return {
        "Pago": lnPago,
        "NumeroPagoEmpresa": lcNumeroPagoEmpresa,
        "NumeroTransaccion": limpiarTexto(txValores.get("transactionId")),
        "FechaHoraExpiracion": limpiarTexto(txValores.get("expirationDate")),
        "EstadoTransaccion": mapearEstadoGeneracionApi(txValores.get("status")),
        "Mensaje": limpiarTexto(txRespuesta.get("message")) or "QR generado correctamente.",
        "QrBase64": limpiarTexto(txValores.get("qrBase64")),
        "CheckoutUrl": limpiarTexto(txValores.get("checkoutUrl")),
        "DeepLink": limpiarTexto(txValores.get("deepLink")),
        "QrContentUrl": limpiarTexto(txValores.get("qrContentUrl")),
        "UniversalUrl": limpiarTexto(txValores.get("universalUrl")),
        "RespuestaTexto": jsonTexto(txRespuesta)
    }


def consultarPagoQr(tcNumeroPagoEmpresa, tcNumeroTransaccion, txUsuarioData):
    txPagoBd = obtenerPagoDigitalPorReferencia(
        tcNumeroPagoEmpresa=tcNumeroPagoEmpresa,
        tcNumeroTransaccion=tcNumeroTransaccion
    )

    txApiConsulta = consultarTransaccionApi(
        tcNumeroPagoEmpresa=tcNumeroPagoEmpresa,
        tcNumeroTransaccion=tcNumeroTransaccion
    )

    txValores = txApiConsulta["Valores"]
    txRespuesta = txApiConsulta["Respuesta"]

    tnEstadoTransaccion = mapearEstadoConsultaApi(txValores.get("paymentStatus"))

    lcFechaPago = limpiarTexto(txValores.get("paymentDate"))
    lcHoraPago = limpiarTexto(txValores.get("paymentTime"))
    lcFechaHoraPago = ""

    if lcFechaPago and lcHoraPago:
        lcFechaHoraPago = f"{lcFechaPago} {lcHoraPago}"
    elif lcFechaPago:
        lcFechaHoraPago = lcFechaPago

    actualizarEstadoConsultaPagoDigital(
        tnPagoDigital=valorInt(txPagoBd["PagoDigital"]),
        tnEstadoTransaccion=tnEstadoTransaccion,
        txRespuestaConsulta=txRespuesta,
        tcFechaHoraPago=lcFechaHoraPago,
        tcMensaje=limpiarTexto(txRespuesta.get("message"))
    )

    return {
        "Pago": txPagoBd["Pago"],
        "PagoDigital": txPagoBd["PagoDigital"],
        "NumeroPagoEmpresa": limpiarTexto(txPagoBd["NumeroPagoEmpresa"]),
        "NumeroTransaccion": limpiarTexto(txPagoBd["NumeroTransaccion"]),
        "EstadoTransaccion": tnEstadoTransaccion,
        "FechaHoraPago": lcFechaHoraPago,
        "RespuestaTexto": jsonTexto(txRespuesta)
    }


def confirmarPagoQr(tcNumeroPagoEmpresa, tcNumeroTransaccion, tnTipoDetalle,
                    tnDetalle, tcConcepto, tnMonto, txUsuarioData):
    txPagoBd = obtenerPagoDigitalPorReferencia(
        tcNumeroPagoEmpresa=tcNumeroPagoEmpresa,
        tcNumeroTransaccion=tcNumeroTransaccion
    )

    if valorInt(txPagoBd.get("EstadoTransaccion")) == gnEstadoTransaccionPagado:
        finalizarDetallePagado(
            tnTipoDetalle=valorInt(txPagoBd.get("TipoDetalle")),
            tnDetalle=valorInt(txPagoBd.get("Detalle")),
            txUsuarioData=txUsuarioData
        )
        return {
            "Pago": txPagoBd["Pago"],
            "RespuestaTexto": "El pago ya estaba confirmado previamente."
        }

    txConsulta = consultarPagoQr(
        tcNumeroPagoEmpresa=tcNumeroPagoEmpresa,
        tcNumeroTransaccion=tcNumeroTransaccion,
        txUsuarioData=txUsuarioData
    )

    if valorInt(txConsulta.get("EstadoTransaccion")) != gnEstadoTransaccionPagado:
        raise ValueError("La transacción QR aún no figura como pagada.")

    finalizarDetallePagado(
        tnTipoDetalle=valorInt(txPagoBd.get("TipoDetalle")),
        tnDetalle=valorInt(txPagoBd.get("Detalle")),
        txUsuarioData=txUsuarioData
    )

    return {
        "Pago": txPagoBd["Pago"],
        "RespuestaTexto": "Pago QR confirmado y registrado correctamente."
    }