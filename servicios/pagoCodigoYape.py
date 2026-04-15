import os
import json
from urllib import request, error

from dotenv import load_dotenv

from database.db import getConnection
from servicios.pagoService import (
    obtenerUsuarioActualId,
    insertarBitacora,
    marcarOperacionPagada,
    getFechaHoraActualTexto,
    limpiarTexto,
    esTelefonoValido,
)


# =========================================================
# CONSTANTES
# =========================================================
gnMetodoPagoCodigoYape = 2
gnEstadoPagoRegistrado = 1

gnTipoDetalleOperacion = 1
gnTipoDetalleContrato = 2

gnEstadoTransaccionPreparado = 1
gnEstadoTransaccionPendiente = 2
gnEstadoTransaccionPagado = 3
gnEstadoTransaccionFallido = 4
gnEstadoTransaccionAnulado = 5
gnEstadoTransaccionExpirado = 6

gnMonedaDolares = 1
gnMonedaBolivianos = 2


# =========================================================
# CONFIGURACIÓN PAGOFÁCIL / YAPE
# =========================================================

load_dotenv()

gcPagoFacilBaseUrl = os.getenv("PAGOFACIL_BASE_URL", "").strip()
gcPagoFacilTokenService = os.getenv("PAGOFACIL_TOKEN_SERVICE", "").strip()
gcPagoFacilTokenSecret = os.getenv("PAGOFACIL_TOKEN_SECRET", "").strip()
gcPagoFacilCommerceId = os.getenv("PAGOFACIL_COMMERCE_ID", "").strip()

gcBackendPagosBaseUrl = os.getenv("BACKEND_PAGOS_BASE_URL", "").strip()
gcPagoFacilUrlCallback = os.getenv("PAGOFACIL_URL_CALLBACK", "").strip()
gcPagoFacilUrlReturn = os.getenv("PAGOFACIL_URL_RETURN", "").strip()

glCodigoYapeIntegracionActiva = True


# =========================================================
# HTTP
# =========================================================
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
            lnStatusCode = getattr(loResponse, "status", None)
            lcBody = loResponse.read().decode("utf-8", errors="replace")

            if not lcBody:
                return {
                    "http_status": lnStatusCode,
                    "raw_body": "",
                    "json": {}
                }

            try:
                txRespuesta = json.loads(lcBody)
            except json.JSONDecodeError:
                raise RuntimeError(
                    "La respuesta del servicio no tiene formato JSON válido.\n\n"
                    f"Status HTTP: {lnStatusCode}\n"
                    f"Body recibido:\n{lcBody}"
                )

            if not isinstance(txRespuesta, dict):
                raise RuntimeError(
                    "La API devolvió una respuesta no válida.\n\n"
                    f"Status HTTP: {lnStatusCode}\n"
                    f"Body recibido:\n{lcBody}"
                )

            txRespuesta["_debug"] = {
                "url": tcUrl,
                "http_status": lnStatusCode,
                "headers_enviados": laHeaders,
                "payload_enviado": txPayload,
                "raw_body": lcBody,
            }

            return txRespuesta

    except error.HTTPError as toError:
        lnStatusCode = toError.code
        lcErrorBody = toError.read().decode("utf-8", errors="replace")

        try:
            txErrorJson = json.loads(lcErrorBody) if lcErrorBody else {}
        except json.JSONDecodeError:
            txErrorJson = None

        if isinstance(txErrorJson, dict):
            raise RuntimeError(
                "Error HTTP al consumir el servicio.\n\n"
                f"URL: {tcUrl}\n"
                f"Status HTTP: {lnStatusCode}\n"
                f"Payload enviado:\n{json.dumps(txPayload, indent=4, ensure_ascii=False)}\n\n"
                f"Respuesta completa:\n{json.dumps(txErrorJson, indent=4, ensure_ascii=False)}"
            )

        raise RuntimeError(
            "Error HTTP al consumir el servicio.\n\n"
            f"URL: {tcUrl}\n"
            f"Status HTTP: {lnStatusCode}\n"
            f"Payload enviado:\n{json.dumps(txPayload, indent=4, ensure_ascii=False)}\n\n"
            f"Body recibido:\n{lcErrorBody}"
        )

    except error.URLError as toError:
        raise RuntimeError(
            "No se pudo conectar con PagoFácil/Yape.\n\n"
            f"URL: {tcUrl}\n"
            f"Motivo: {toError.reason}\n"
            f"Payload enviado:\n{json.dumps(txPayload, indent=4, ensure_ascii=False)}"
        )


def ejecutarGetJson(tcUrl, tnTimeout=15):
    loRequest = request.Request(
        tcUrl,
        headers={"Accept": "application/json"},
        method="GET"
    )

    try:
        with request.urlopen(loRequest, timeout=tnTimeout) as loResponse:
            lcBody = loResponse.read().decode("utf-8", errors="replace")
            if not lcBody:
                return {}
            return json.loads(lcBody)

    except error.HTTPError as toError:
        lcErrorBody = toError.read().decode("utf-8", errors="replace")

        if lcErrorBody:
            try:
                txErrorJson = json.loads(lcErrorBody)
                raise RuntimeError(
                    txErrorJson.get("message")
                    or txErrorJson.get("messageSistema")
                    or lcErrorBody
                )
            except json.JSONDecodeError:
                raise RuntimeError(lcErrorBody)

        raise RuntimeError(f"Error HTTP {toError.code} al consultar el backend de Código Yape.")

    except error.URLError as toError:
        raise RuntimeError(f"No se pudo conectar con el backend de Código Yape. {toError.reason}")

    except json.JSONDecodeError:
        raise RuntimeError("La respuesta del backend no tiene formato JSON válido.")


# =========================================================
# API PAGOFÁCIL / YAPE
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

    if not isinstance(txRespuesta, dict):
        raise RuntimeError(f"Respuesta inválida en autenticación: {txRespuesta}")

    if txRespuesta.get("error") != 0 or txRespuesta.get("status") != 1:
        raise RuntimeError(
            txRespuesta.get("message")
            or txRespuesta.get("messageSistema")
            or "No se pudo autenticar con PagoFácil."
        )

    txValues = txRespuesta.get("values")

    if isinstance(txValues, str):
        tcAccessToken = txValues.strip()
    elif isinstance(txValues, dict):
        tcAccessToken = (
            txValues.get("AccessToken")
            or txValues.get("accessToken")
            or ""
        ).strip()
    else:
        raise RuntimeError(f"Respuesta inválida en values de autenticación: {txValues}")

    if not tcAccessToken:
        raise RuntimeError("La autenticación no devolvió AccessToken.")

    return tcAccessToken


def prepararPagoCodigoYapeApi(tcAccessToken, txPagoData):
    if not gcPagoFacilCommerceId:
        raise RuntimeError("Falta tcCommerceID en la configuración de PagoFácil.")

    txPayload = {
        "tcCommerceID": gcPagoFacilCommerceId,
        "tcNombreCliente": txPagoData["NombreCliente"],
        "tcCodigoClienteEmpresa": txPagoData["CodigoClienteEmpresa"],
        "tnTelefonoEnvio": txPagoData["TelefonoEnvio"],
        "tnTelefonoBcp": txPagoData["TelefonoYape"],
        "tcCorreo": txPagoData["Correo"],
        "tcNroPago": txPagoData["NumeroPagoEmpresa"],
        "tnMontoTotal": f"{float(txPagoData['MontoTotal']):.2f}",
        "tnMoneda": txPagoData["Moneda"],
        "tcUrlCallBack": gcPagoFacilUrlCallback,
        "tcUrlReturn": gcPagoFacilUrlReturn,
        "taPedidoDetalle": txPagoData["PedidoDetalle"],
    }

    txRespuesta = ejecutarPostJson(
        f"{gcPagoFacilBaseUrl}/api/servicios/prepararPagoSoli",
        txPayload,
        tcBearerToken=tcAccessToken
    )

    if not isinstance(txRespuesta, dict):
        raise RuntimeError(f"Respuesta inválida al preparar pago por Código Yape: {txRespuesta}")

    if txRespuesta.get("error") != 0 or txRespuesta.get("status") != 1:
        raise RuntimeError(
            txRespuesta.get("message")
            or txRespuesta.get("messageSistema")
            or "No se pudo preparar el pago por Código Yape."
        )

    txValues = txRespuesta.get("values", {})
    if not isinstance(txValues, dict):
        raise RuntimeError(f"Respuesta inválida en values al preparar el pago: {txValues}")

    return {
        "Respuesta": txRespuesta,
        "NumeroTransaccion": str(txValues.get("tnNroTransaccion", "")),
        "NumeroAutorizacion": str(
            txValues.get("TnNroAutorizacion", "")
            or txValues.get("tnNroAutorizacion", "")
        ),
        "Mensaje": txRespuesta.get("message", ""),
        "MensajeSistema": txRespuesta.get("messageSistema", ""),
        "PayloadEnviado": txPayload,
    }


def confirmarPagoCodigoYapeApi(tcAccessToken, txConfirmacionData):
    txPayload = {
        "tnCliente": txConfirmacionData["CodigoClienteEmpresa"],
        "tnNroTransaccion": txConfirmacionData["NumeroTransaccion"],
        "tnNroAutorizacion": txConfirmacionData["NumeroAutorizacion"],
        "tcCodigoPago": txConfirmacionData["CodigoPago"],
    }

    txRespuesta = ejecutarPostJson(
        f"{gcPagoFacilBaseUrl}/api/servicios/confirmarPagoSoli",
        txPayload,
        tcBearerToken=tcAccessToken
    )

    if txRespuesta.get("error") != 0 or txRespuesta.get("status") != 1:
        raise RuntimeError(
            txRespuesta.get("message")
            or txRespuesta.get("messageSistema")
            or "No se pudo confirmar el pago por Código Yape."
        )

    return {
        "Respuesta": txRespuesta,
        "Mensaje": txRespuesta.get("message", ""),
        "MensajeSistema": txRespuesta.get("messageSistema", ""),
    }


def consultarEstadoPagoCodigoYapeWeb(tcNumeroPagoEmpresa):
    tcNumeroPagoEmpresa = limpiarTexto(tcNumeroPagoEmpresa)
    if not tcNumeroPagoEmpresa:
        raise ValueError("Falta NumeroPagoEmpresa para consultar el estado del pago.")

    return ejecutarGetJson(f"{gcBackendPagosBaseUrl}/pagos/{tcNumeroPagoEmpresa}")


# =========================================================
# VALIDACIONES
# =========================================================
def validarDatosPagoCodigoYape(txPagoData):
    lcNombreCliente = limpiarTexto(txPagoData.get("NombreCliente"))
    lcCodigoClienteEmpresa = limpiarTexto(txPagoData.get("CodigoClienteEmpresa"))
    lcTelefonoEnvio = limpiarTexto(txPagoData.get("TelefonoEnvio"))
    lcTelefonoYape = limpiarTexto(txPagoData.get("TelefonoYape"))
    lcCorreo = limpiarTexto(txPagoData.get("Correo"))

    if not lcNombreCliente:
        raise ValueError("Debes ingresar el nombre del cliente.")

    if not lcCodigoClienteEmpresa:
        raise ValueError("Debes ingresar el código cliente empresa.")

    if not esTelefonoValido(lcTelefonoEnvio):
        raise ValueError("El teléfono de envío debe tener 7 u 8 dígitos.")

    if not esTelefonoValido(lcTelefonoYape):
        raise ValueError("El teléfono Yape debe tener 7 u 8 dígitos.")

    return {
        "NombreCliente": lcNombreCliente,
        "CodigoClienteEmpresa": lcCodigoClienteEmpresa,
        "TelefonoEnvio": lcTelefonoEnvio,
        "TelefonoYape": lcTelefonoYape,
        "Correo": lcCorreo,
        "PedidoDetalle": txPagoData.get("PedidoDetalle", []),
        "Cliente": txPagoData.get("Cliente"),
    }


# =========================================================
# BD
# =========================================================
def prepararRegistroPagoCodigoYape(
    tnTipoDetalle,
    tnDetalle,
    tcConcepto,
    tnMonto,
    txPagoData,
    txUsuarioData=None
):
    loConn = getConnection()
    loCursor = loConn.cursor()
    tnUsr = obtenerUsuarioActualId(txUsuarioData)

    try:
        tnMonto = float(tnMonto)

        if tnMonto <= 0:
            raise ValueError("El monto debe ser mayor a 0.")

        txPagoData = validarDatosPagoCodigoYape(txPagoData)

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
            gnMetodoPagoCodigoYape,
            tnMonto,
            gnEstadoPagoRegistrado,
            tnUsr
        ))

        tnPago = loCursor.lastrowid
        lcNumeroPagoEmpresa = f"YAPE-{tnPago}"

        lcNumeroTransaccion = ""
        lcNumeroAutorizacion = ""
        lcMensaje = "Pago por Código Yape preparado localmente."
        lcMensajeSistema = ""
        lcJsonPreparacion = ""
        lcDetallePedidoJson = json.dumps(txPagoData["PedidoDetalle"], ensure_ascii=False)

        if glCodigoYapeIntegracionActiva:
            tcAccessToken = autenticarPagoFacil()

            txPreparacion = prepararPagoCodigoYapeApi(
                tcAccessToken,
                {
                    "NombreCliente": txPagoData["NombreCliente"],
                    "CodigoClienteEmpresa": txPagoData["CodigoClienteEmpresa"],
                    "TelefonoEnvio": txPagoData["TelefonoEnvio"],
                    "TelefonoYape": txPagoData["TelefonoYape"],
                    "Correo": txPagoData["Correo"],
                    "NumeroPagoEmpresa": lcNumeroPagoEmpresa,
                    "MontoTotal": tnMonto,
                    "Moneda": gnMonedaBolivianos,
                    "PedidoDetalle": txPagoData["PedidoDetalle"],
                }
            )

            lcNumeroTransaccion = txPreparacion["NumeroTransaccion"]
            lcNumeroAutorizacion = txPreparacion["NumeroAutorizacion"]
            lcMensaje = txPreparacion["Mensaje"]
            lcMensajeSistema = txPreparacion["MensajeSistema"]
            lcJsonPreparacion = json.dumps(txPreparacion["Respuesta"], ensure_ascii=False)

        loCursor.execute("""
            INSERT INTO PAGODIGITAL (
                Pago,
                Cliente,
                NumeroPagoEmpresa,
                MontoTotal,
                NumeroTransaccion,
                NumeroAutorizacion,
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
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                date('now','localtime'),
                time('now','localtime'),
                datetime('now','localtime'),
                datetime('now','localtime')
            )
        """, (
            tnPago,
            txPagoData["Cliente"],
            lcNumeroPagoEmpresa,
            tnMonto,
            lcNumeroTransaccion,
            lcNumeroAutorizacion,
            txPagoData["CodigoClienteEmpresa"],
            txPagoData["TelefonoEnvio"],
            txPagoData["TelefonoYape"],
            txPagoData["Correo"],
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

        tnPagoDigital = loCursor.lastrowid

        insertarBitacora(
            loCursor,
            tnUsr,
            "PREPARAR_PAGO_CODIGO_YAPE",
            "PAGODIGITAL",
            tnPagoDigital,
            f"Se preparó pago por Código Yape. Pago={tnPago}, Monto=Bs {tnMonto:.2f}, NumeroPagoEmpresa={lcNumeroPagoEmpresa}"
        )

        loConn.commit()

        return {
            "Pago": tnPago,
            "PagoDigital": tnPagoDigital,
            "NumeroPagoEmpresa": lcNumeroPagoEmpresa,
            "NumeroTransaccion": lcNumeroTransaccion,
            "NumeroAutorizacion": lcNumeroAutorizacion,
            "Mensaje": lcMensaje,
            "MensajeSistema": lcMensajeSistema,
        }

    except Exception:
        loConn.rollback()
        raise
    finally:
        loConn.close()

def consultarEstadoPagoCodigoYape(
    tnPagoDigital,
    txUsuarioData=None
):
    loConn = getConnection()
    loCursor = loConn.cursor()
    tnUsr = obtenerUsuarioActualId(txUsuarioData)

    try:
        loCursor.execute("""
            SELECT
                pd.PagoDigital,
                pd.Pago,
                pd.NumeroPagoEmpresa,
                pd.EstadoTransaccion,
                p.TipoDetalle,
                p.Detalle
            FROM PAGODIGITAL pd
            INNER JOIN PAGO p ON p.Pago = pd.Pago
            WHERE pd.PagoDigital = ?
        """, (tnPagoDigital,))
        loFila = loCursor.fetchone()

        if not loFila:
            raise ValueError("No se encontró el pago de Código Yape.")

        tnPago = loFila[1]
        lcNumeroPagoEmpresa = limpiarTexto(loFila[2])
        tnEstadoActual = int(loFila[3])
        tnTipoDetalle = loFila[4]
        tnDetalle = loFila[5]

        if tnEstadoActual == gnEstadoTransaccionPagado:
            return {
                "Pago": tnPago,
                "PagoDigital": tnPagoDigital,
                "Estado": "PAGADO",
                "Mensaje": "El pago ya fue confirmado anteriormente."
            }

        txRespuestaWeb = consultarEstadoPagoCodigoYapeWeb(lcNumeroPagoEmpresa)

        if not txRespuestaWeb.get("ok"):
            return {
                "Pago": tnPago,
                "PagoDigital": tnPagoDigital,
                "Estado": "PENDIENTE",
                "Mensaje": "Esperando confirmación del pago..."
            }

        txData = txRespuestaWeb.get("data", {})
        lcEstadoWeb = limpiarTexto(txData.get("Estado", "")).upper()
        lcMetodoPagoWeb = limpiarTexto(txData.get("MetodoPago", ""))
        lcFechaWeb = limpiarTexto(txData.get("Fecha", ""))
        lcHoraWeb = limpiarTexto(txData.get("Hora", ""))
        lcJsonConsulta = json.dumps(txData, ensure_ascii=False)

        llPagoExitoso = lcEstadoWeb in ["PAGADO", "2"]

        if llPagoExitoso:
            loCursor.execute("""
                UPDATE PAGODIGITAL
                SET
                    EstadoTransaccion = ?,
                    Mensaje = ?,
                    MensajeSistema = ?,
                    JsonRespuestaConsulta = ?,
                    FechaHoraConfirmacion = COALESCE(FechaHoraConfirmacion, ?),
                    FechaHoraFinalizacion = ?,
                    FechaModificacion = datetime('now','localtime')
                WHERE PagoDigital = ?
            """, (
                gnEstadoTransaccionPagado,
                f"Pago confirmado automáticamente. Método={lcMetodoPagoWeb}",
                f"Fecha={lcFechaWeb} Hora={lcHoraWeb}",
                lcJsonConsulta,
                getFechaHoraActualTexto(),
                getFechaHoraActualTexto(),
                tnPagoDigital
            ))

            marcarOperacionPagada(loCursor, tnTipoDetalle, tnDetalle)

            insertarBitacora(
                loCursor,
                tnUsr,
                "CONFIRMAR_PAGO_CODIGO_YAPE",
                "PAGODIGITAL",
                tnPagoDigital,
                f"Se confirmó el pago por Código Yape. PagoDigital={tnPagoDigital}, Detalle={tnDetalle}, EstadoWeb={lcEstadoWeb}"
            )

            loConn.commit()

            return {
                "Pago": tnPago,
                "PagoDigital": tnPagoDigital,
                "Estado": "PAGADO",
                "Mensaje": "El pago por Código Yape fue confirmado correctamente."
            }

        loCursor.execute("""
            UPDATE PAGODIGITAL
            SET
                JsonRespuestaConsulta = ?,
                FechaModificacion = datetime('now','localtime')
            WHERE PagoDigital = ?
        """, (
            lcJsonConsulta,
            tnPagoDigital
        ))

        loConn.commit()

        return {
            "Pago": tnPago,
            "PagoDigital": tnPagoDigital,
            "Estado": lcEstadoWeb or "PENDIENTE",
            "Mensaje": "Esperando confirmación del pago..."
        }

    except Exception:
        loConn.rollback()
        raise
    finally:
        loConn.close()

def confirmarPagoCodigoYapeManual(
    tnPagoDigital,
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
                pd.PagoDigital,
                pd.CodigoClienteEmpresa,
                pd.NumeroTransaccion,
                pd.NumeroAutorizacion,
                pd.NumeroPagoEmpresa,
                pd.EstadoTransaccion
            FROM PAGODIGITAL pd
            WHERE pd.PagoDigital = ?
        """, (tnPagoDigital,))
        loFila = loCursor.fetchone()

        if not loFila:
            raise ValueError("No se encontró el pago de Código Yape.")

        if int(loFila[5]) == gnEstadoTransaccionPagado:
            return {
                "PagoDigital": tnPagoDigital,
                "Mensaje": "El pago ya estaba confirmado."
            }

        tcAccessToken = autenticarPagoFacil()

        txConfirmacion = confirmarPagoCodigoYapeApi(
            tcAccessToken,
            {
                "CodigoClienteEmpresa": limpiarTexto(loFila[1]),
                "NumeroTransaccion": limpiarTexto(loFila[2]),
                "NumeroAutorizacion": limpiarTexto(loFila[3]),
                "CodigoPago": tcCodigoPago,
            }
        )

        loCursor.execute("""
            UPDATE PAGODIGITAL
            SET
                CodigoPago = ?,
                EstadoTransaccion = ?,
                Mensaje = ?,
                MensajeSistema = ?,
                JsonRespuestaConfirmacion = ?,
                FechaHoraConfirmacion = ?,
                FechaModificacion = datetime('now','localtime')
            WHERE PagoDigital = ?
        """, (
            tcCodigoPago,
            gnEstadoTransaccionPendiente,
            txConfirmacion.get("Mensaje", "Código enviado correctamente."),
            txConfirmacion.get("MensajeSistema", ""),
            json.dumps(txConfirmacion.get("Respuesta", {}), ensure_ascii=False),
            getFechaHoraActualTexto(),
            tnPagoDigital
        ))

        insertarBitacora(
            loCursor,
            tnUsr,
            "CONFIRMAR_CODIGO_YAPE_MANUAL",
            "PAGODIGITAL",
            tnPagoDigital,
            f"Se envió manualmente el código de confirmación para Código Yape. NumeroPagoEmpresa={limpiarTexto(loFila[4])}"
        )

        loConn.commit()

        return {
            "PagoDigital": tnPagoDigital,
            "Mensaje": txConfirmacion.get("Mensaje", "Código enviado correctamente. Esperando confirmación."),
        }

    except Exception:
        loConn.rollback()
        raise
    finally:
        loConn.close()