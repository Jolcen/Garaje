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
# CONFIGURACION TIGO MONEY
# =========================================================
load_dotenv()

gcUrlBase = os.getenv(
    "PAGOFACIL_TIGOMONEY_BASE_URL",
    os.getenv("PAGOFACIL_BASE_URL", "https://serviciostigomoney.pagofacil.com.bo")
).strip()

gcTokenService = os.getenv(
    "PAGOFACIL_TIGOMONEY_TOKEN_SERVICE",
    os.getenv("PAGOFACIL_TOKEN_SERVICE", "")
).strip()

gcTokenSecret = os.getenv(
    "PAGOFACIL_TIGOMONEY_TOKEN_SECRET",
    os.getenv("PAGOFACIL_TOKEN_SECRET", "")
).strip()

gcCommerceId = os.getenv(
    "PAGOFACIL_TIGOMONEY_COMMERCE_ID",
    os.getenv("PAGOFACIL_COMMERCE_ID", "")
).strip()

gcCallbackUrl = os.getenv(
    "PAGOFACIL_TIGOMONEY_URL_CALLBACK",
    os.getenv("PAGOFACIL_URL_CALLBACK", "")
).strip()

gcReturnUrl = os.getenv(
    "PAGOFACIL_TIGOMONEY_URL_RETURN",
    os.getenv("PAGOFACIL_URL_RETURN", "")
).strip()

gnCurrencyTigoMoney = int(
    os.getenv(
        "PAGOFACIL_TIGOMONEY_CURRENCY",
        "2"
    ).strip()
)

gnTimeoutSegundos = 30


# =========================================================
# CONSTANTES DEL SISTEMA
# =========================================================
gnMetodoPagoTigoMoney = 4

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

gnMoneda = gnCurrencyTigoMoney


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


def validarConfiguracionTigoMoney():
    if not gcUrlBase:
        raise ValueError("Falta configurar PAGOFACIL_TIGOMONEY_BASE_URL o PAGOFACIL_BASE_URL.")
    if not gcTokenService:
        raise ValueError("Falta configurar PAGOFACIL_TIGOMONEY_TOKEN_SERVICE o PAGOFACIL_TOKEN_SERVICE.")
    if not gcTokenSecret:
        raise ValueError("Falta configurar PAGOFACIL_TIGOMONEY_TOKEN_SECRET o PAGOFACIL_TOKEN_SECRET.")
    if not gcCommerceId:
        raise ValueError("Falta configurar PAGOFACIL_TIGOMONEY_COMMERCE_ID o PAGOFACIL_COMMERCE_ID.")
    if gnCurrencyTigoMoney <= 0:
        raise ValueError("Moneda Tigo Money inválida.")


# =========================================================
# HTTP / API
# =========================================================
def postApi(tcEndpoint, txHeaders=None, txBody=None):
    lcBase = gcUrlBase.rstrip("/")
    lcUrl = f"{lcBase}{tcEndpoint}"

    loHeaders = {
        "Content-Type": "application/json",
        "Accept": "application/json",
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
        raise ValueError(f"No se pudo conectar con Tigo Money: {str(toError)}")

    try:
        txRespuesta = loResponse.json()
    except Exception:
        raise ValueError(
            f"La API Tigo Money respondió con un contenido inválido. HTTP {loResponse.status_code}. "
            f"Respuesta: {loResponse.text}"
        )

    if loResponse.status_code >= 400:
        raise ValueError(
            f"Error HTTP {loResponse.status_code}: "
            f"{limpiarTexto(txRespuesta.get('message')) or loResponse.text}"
        )

    if valorInt(txRespuesta.get("error"), 1) != 0:
        raise ValueError(
            limpiarTexto(txRespuesta.get("message"))
            or "La API Tigo Money devolvió un error."
        )

    return txRespuesta


def autenticarTigoMoney():
    validarConfiguracionTigoMoney()

    txBody = {
        "TokenService": gcTokenService,
        "TokenSecret": gcTokenSecret
    }

    try:
        txRespuesta = postApi("/api/servicio/login", txBody=txBody)
    except Exception:
        # compatibilidad por si el servidor expone /api/auth/login
        txRespuesta = postApi("/api/auth/login", txBody=txBody)

    lcToken = limpiarTexto(txRespuesta.get("values"))
    if not lcToken:
        txValores = txRespuesta.get("values") or {}
        lcToken = limpiarTexto(txValores.get("accessToken"))

    if not lcToken:
        raise ValueError("La API Tigo Money no devolvió AccessToken.")

    return {
        "AccessToken": lcToken,
        "Respuesta": txRespuesta
    }


def generarTransaccionApi(tcNombreCliente, tcDocumento, tcTelefono, tcCorreo,
                         tcNumeroPagoEmpresa, tnMonto, tcCodigoClienteEmpresa,
                         tcConcepto):
    txLogin = autenticarTigoMoney()
    lcToken = txLogin["AccessToken"]

    txHeaders = {
        "Authorization": f"Bearer {lcToken}"
    }

    txBody = {
        "tcCommerceID": gcCommerceId,
        "tcNroPago": tcNumeroPagoEmpresa,
        "tcNombreUsuario": tcNombreCliente,
        "tnCiNit": tcDocumento or "0",
        "tnTelefono": tcTelefono or "00000000",
        "tcCorreo": tcCorreo or "cliente@correo.com",
        "tcCodigoClienteEmpresa": tcCodigoClienteEmpresa or "0",
        "tnMontoClienteEmpresa": f"{round(valorFloat(tnMonto), 2):.2f}",
        "tnMoneda": gnCurrencyTigoMoney,
        "tcUrlCallBack": gcCallbackUrl,
        "tcUrlReturn": gcReturnUrl,
        "taPedidoDetalle": [
            {
                "Serial": 1,
                "Producto": tcConcepto or "Cobro",
                "Cantidad": 1,
                "Precio": f"{round(valorFloat(tnMonto), 2):.2f}",
                "Descuento": 0,
                "Total": f"{round(valorFloat(tnMonto), 2):.2f}"
            }
        ]
    }

    if not gcCallbackUrl:
        txBody.pop("tcUrlCallBack", None)

    if not gcReturnUrl:
        txBody.pop("tcUrlReturn", None)

    txRespuesta = postApi(
        "/api/servicio/pagotigomoney",
        txHeaders=txHeaders,
        txBody=txBody
    )

    return {
        "RequestBody": txBody,
        "Respuesta": txRespuesta,
        "Valores": txRespuesta.get("values")
    }


def consultarTransaccionApi(tcNumeroTransaccion=""):
    if not tcNumeroTransaccion:
        raise ValueError("Debes enviar NumeroTransaccion para consultar Tigo Money.")

    txBody = {
        "TransaccionDePago": tcNumeroTransaccion
    }

    txRespuesta = postApi(
        "/api/servicio/consultartransaccion",
        txBody=txBody
    )

    return {
        "RequestBody": txBody,
        "Respuesta": txRespuesta,
        "Valores": txRespuesta.get("values") or {}
    }


def obtenerReciboApi(tcNumeroTransaccion, tcNumeroPagoEmpresa):
    txLogin = autenticarTigoMoney()
    lcToken = txLogin["AccessToken"]

    txHeaders = {
        "Authorization": f"Bearer {lcToken}"
    }

    txBody = {
        "tnTransaccionDePago": valorInt(tcNumeroTransaccion, 0),
        "tnNroPago": tcNumeroPagoEmpresa
    }

    txRespuesta = postApi(
        "/api/servicio/obtenerrecibo",
        txHeaders=txHeaders,
        txBody=txBody
    )

    return {
        "RequestBody": txBody,
        "Respuesta": txRespuesta,
        "Valores": txRespuesta.get("values") or {}
    }


# =========================================================
# MAPEOS
# =========================================================
def mapearEstadoGeneracionApi(txRespuesta):
    lcMensaje = limpiarTexto(txRespuesta.get("message")).lower()
    if "proces" in lcMensaje:
        return gnEstadoTransaccionPendiente
    return gnEstadoTransaccionPreparado


def mapearEstadoConsultaApi(tnEstadoApi, tcMensajeEstado=""):
    lcEstado = limpiarTexto(tnEstadoApi).lower()
    lcMensajeEstado = limpiarTexto(tcMensajeEstado).lower()

    if lcEstado in ("1", "2", "3", "paid", "pagado", "success", "successful", "completed", "completado"):
        if lcEstado in ("2", "3", "paid", "pagado", "success", "successful", "completed", "completado"):
            return gnEstadoTransaccionPagado

    if "completado" in lcMensajeEstado or "pagado" in lcMensajeEstado:
        return gnEstadoTransaccionPagado

    if "vencido" in lcMensajeEstado or "expir" in lcMensajeEstado:
        return gnEstadoTransaccionExpirado

    if "anulado" in lcMensajeEstado or "cancel" in lcMensajeEstado:
        return gnEstadoTransaccionAnulado

    if "fall" in lcMensajeEstado or "rechaz" in lcMensajeEstado or "error" in lcMensajeEstado:
        return gnEstadoTransaccionFallido

    return gnEstadoTransaccionPendiente


# =========================================================
# DATOS DEL CLIENTE / CONTEXTO
# =========================================================
def obtenerDatosClienteTigoMoney(tnTipoDetalle, tnDetalle):
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
    return f"TM-{lcPrefijo}-{tnDetalle}-{lcFechaHora}-{lcRandom}"


# =========================================================
# BASE DE DATOS
# =========================================================
def insertarPagoTigoMoneyPendiente(
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

    txRespuesta = txApiGeneracion["Respuesta"]
    txBody = txApiGeneracion["RequestBody"]

    lcNumeroPagoEmpresa = limpiarTexto(txBody.get("tcNroPago"))
    lcNumeroTransaccion = limpiarTexto(txRespuesta.get("values"))
    lnEstadoTransaccion = mapearEstadoGeneracionApi(txRespuesta)

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
                gnMetodoPagoTigoMoney,
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lnPago,
                txDatosCliente.get("Cliente"),
                lcNumeroPagoEmpresa,
                round(valorFloat(tnMonto), 2),
                lcNumeroTransaccion,
                limpiarTexto(txBody.get("tcCodigoClienteEmpresa")),
                limpiarTexto(txBody.get("tnTelefono")),
                limpiarTexto(txBody.get("tnTelefono")),
                limpiarTexto(txBody.get("tcCorreo")),
                gnMoneda,
                lnEstadoTransaccion,
                limpiarTexto(txRespuesta.get("message")),
                limpiarTexto(txRespuesta.get("messageSistema")),
                limpiarTexto(txBody.get("tcUrlCallBack")),
                limpiarTexto(txBody.get("tcUrlReturn")),
                jsonTexto(txBody.get("taPedidoDetalle")),
                jsonTexto(txRespuesta),
                lcFechaHora,
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
                pd.NombreArchivoRecibo,
                pd.ReciboBase64,
                pd.UrlCallback,
                pd.UrlRetorno,
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

        return dict(loFila)

    finally:
        loConn.close()


def actualizarEstadoConsultaPagoDigital(
    tnPagoDigital,
    tnEstadoTransaccion,
    txRespuestaConsulta,
    tcFechaHoraPago="",
    tcMensaje="",
    tcMensajeSistema=""
):
    loConn = db.getConnection()
    loCursor = loConn.cursor()

    lcFechaHora = ahoraFechaHora()

    try:
        loCursor.execute(
            """
            UPDATE PAGODIGITAL
            SET
                EstadoTransaccion = ?,
                Mensaje = ?,
                MensajeSistema = ?,
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
                tcMensajeSistema,
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


def guardarReciboPagoDigital(tnPagoDigital, txRespuestaRecibo):
    loConn = db.getConnection()
    loCursor = loConn.cursor()

    lcFechaHora = ahoraFechaHora()
    txValores = txRespuestaRecibo.get("values") or {}

    try:
        loCursor.execute(
            """
            UPDATE PAGODIGITAL
            SET
                NombreArchivoRecibo = ?,
                ReciboBase64 = ?,
                JsonRespuestaConfirmacion = ?,
                FechaModificacion = ?
            WHERE PagoDigital = ?
            """,
            (
                limpiarTexto(txValores.get("tcNombreArchivo")),
                limpiarTexto(txValores.get("tcFacturaPDF")),
                jsonTexto(txRespuestaRecibo),
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
            "PAGO_TIGOMONEY_CONFIRMADO",
            "OPERACION" if tnTipoDetalle == gnTipoDetalleOperacion else "DETALLE",
            tnDetalle,
            f"Pago Tigo Money confirmado. TipoDetalle={tnTipoDetalle}, Detalle={tnDetalle}"
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
def generarPagoTigoMoney(tnTipoDetalle, tnDetalle, tcConcepto, tnMonto, txUsuarioData,
                         tcNombreCliente="", tcDocumento="", tcTelefono="", tcCorreo=""):
    tnMonto = valorFloat(tnMonto)

    if tnMonto <= 0:
        raise ValueError("El monto debe ser mayor a 0 para generar Tigo Money.")

    txDatosClienteBase = obtenerDatosClienteTigoMoney(tnTipoDetalle, tnDetalle)
    lcNumeroPagoEmpresa = construirNumeroPagoEmpresa(tnTipoDetalle, tnDetalle)

    txDatosCliente = {
        **txDatosClienteBase,
        "NombreCliente": limpiarTexto(tcNombreCliente) or txDatosClienteBase["NombreCliente"],
        "Documento": limpiarTexto(tcDocumento) or txDatosClienteBase["Documento"],
        "Telefono": limpiarTexto(tcTelefono) or txDatosClienteBase["Telefono"],
        "Correo": limpiarTexto(tcCorreo) or txDatosClienteBase["Correo"],
    }

    txApiGeneracion = generarTransaccionApi(
        tcNombreCliente=txDatosCliente["NombreCliente"],
        tcDocumento=txDatosCliente["Documento"],
        tcTelefono=txDatosCliente["Telefono"],
        tcCorreo=txDatosCliente["Correo"],
        tcNumeroPagoEmpresa=lcNumeroPagoEmpresa,
        tnMonto=tnMonto,
        tcCodigoClienteEmpresa=txDatosCliente["CodigoClienteEmpresa"],
        tcConcepto=tcConcepto
    )

    lnPago = insertarPagoTigoMoneyPendiente(
        tnTipoDetalle=tnTipoDetalle,
        tnDetalle=tnDetalle,
        tcConcepto=tcConcepto,
        tnMonto=tnMonto,
        txUsuarioData=txUsuarioData,
        txDatosCliente=txDatosCliente,
        txApiGeneracion=txApiGeneracion
    )

    txRespuesta = txApiGeneracion["Respuesta"]

    return {
        "Pago": lnPago,
        "NumeroPagoEmpresa": lcNumeroPagoEmpresa,
        "NumeroTransaccion": limpiarTexto(txRespuesta.get("values")),
        "FechaHoraExpiracion": "",
        "EstadoTransaccion": mapearEstadoGeneracionApi(txRespuesta),
        "Mensaje": limpiarTexto(txRespuesta.get("message")) or "Transacción Tigo Money generada correctamente.",
        "RespuestaTexto": jsonTexto(txRespuesta)
    }


def consultarPagoTigoMoney(tcNumeroPagoEmpresa, tcNumeroTransaccion, txUsuarioData):
    txPagoBd = obtenerPagoDigitalPorReferencia(
        tcNumeroPagoEmpresa=tcNumeroPagoEmpresa,
        tcNumeroTransaccion=tcNumeroTransaccion
    )

    lcNumeroTransaccion = (
        limpiarTexto(tcNumeroTransaccion)
        or limpiarTexto(txPagoBd.get("NumeroTransaccion"))
    )

    if not lcNumeroTransaccion:
        raise ValueError("No existe NumeroTransaccion para consultar Tigo Money.")

    txApiConsulta = consultarTransaccionApi(
        tcNumeroTransaccion=lcNumeroTransaccion
    )

    txValores = txApiConsulta["Valores"]
    txRespuesta = txApiConsulta["Respuesta"]

    tnEstadoTransaccion = mapearEstadoConsultaApi(
        txValores.get("estadoPago"),
        txValores.get("messageEstado")
    )

    actualizarEstadoConsultaPagoDigital(
        tnPagoDigital=valorInt(txPagoBd["PagoDigital"]),
        tnEstadoTransaccion=tnEstadoTransaccion,
        txRespuestaConsulta=txRespuesta,
        tcFechaHoraPago=ahoraFechaHora() if tnEstadoTransaccion == gnEstadoTransaccionPagado else "",
        tcMensaje=limpiarTexto(txRespuesta.get("message")),
        tcMensajeSistema=limpiarTexto(txValores.get("messageEstado"))
    )

    return {
        "Pago": txPagoBd["Pago"],
        "PagoDigital": txPagoBd["PagoDigital"],
        "NumeroPagoEmpresa": limpiarTexto(txPagoBd["NumeroPagoEmpresa"]),
        "NumeroTransaccion": lcNumeroTransaccion,
        "EstadoTransaccion": tnEstadoTransaccion,
        "FechaHoraPago": ahoraFechaHora() if tnEstadoTransaccion == gnEstadoTransaccionPagado else "",
        "RespuestaTexto": jsonTexto(txRespuesta)
    }


def confirmarPagoTigoMoney(tcNumeroPagoEmpresa, tcNumeroTransaccion, tnTipoDetalle,
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
            "RespuestaTexto": "El pago Tigo Money ya estaba confirmado previamente."
        }

    txConsulta = consultarPagoTigoMoney(
        tcNumeroPagoEmpresa=tcNumeroPagoEmpresa,
        tcNumeroTransaccion=tcNumeroTransaccion,
        txUsuarioData=txUsuarioData
    )

    if valorInt(txConsulta.get("EstadoTransaccion")) != gnEstadoTransaccionPagado:
        raise ValueError("La transacción Tigo Money aún no figura como pagada.")

    try:
        txRecibo = obtenerReciboApi(
            tcNumeroTransaccion=limpiarTexto(txConsulta.get("NumeroTransaccion")),
            tcNumeroPagoEmpresa=limpiarTexto(txConsulta.get("NumeroPagoEmpresa"))
        )
        guardarReciboPagoDigital(
            valorInt(txPagoBd.get("PagoDigital")),
            txRecibo["Respuesta"]
        )
    except Exception:
        # El recibo es deseable, pero no debe bloquear la confirmación del pago
        pass

    finalizarDetallePagado(
        tnTipoDetalle=valorInt(txPagoBd.get("TipoDetalle")),
        tnDetalle=valorInt(txPagoBd.get("Detalle")),
        txUsuarioData=txUsuarioData
    )

    return {
        "Pago": txPagoBd["Pago"],
        "RespuestaTexto": "Pago Tigo Money confirmado y registrado correctamente."
    }