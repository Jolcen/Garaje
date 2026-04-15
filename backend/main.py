from fastapi import FastAPI, Request, BackgroundTasks
import sqlite3
import os
import json
import sys
from datetime import datetime

app = FastAPI()

DB_PATH = os.path.join(os.path.dirname(__file__), "pagos.db")


# =========================================================
# UTILIDADES
# =========================================================
def get_connection():
    return sqlite3.connect(DB_PATH)


def get_fecha_hora_actual():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def limpiar_texto(tcValor):
    if tcValor is None:
        return ""
    return str(tcValor).strip()


def valor_int(tnValor, tnDefault=0):
    try:
        return int(tnValor)
    except Exception:
        return int(tnDefault)


def leer_request_body(lbRaw: bytes):
    lcRaw = lbRaw.decode("utf-8", errors="replace")
    if not lcRaw:
        return {}

    try:
        return json.loads(lcRaw)
    except Exception:
        return {}


# =========================================================
# BD AUXILIAR DE CALLBACKS
# =========================================================
def init_db():
    loConn = get_connection()
    loCursor = loConn.cursor()

    loCursor.execute("""
        CREATE TABLE IF NOT EXISTS PAGOWEB (
            PagoWeb INTEGER PRIMARY KEY AUTOINCREMENT,
            NumeroPagoEmpresa TEXT NOT NULL UNIQUE,
            PedidoID TEXT,
            Fecha TEXT,
            Hora TEXT,
            MetodoPago TEXT,
            Estado TEXT,
            JsonCallback TEXT,
            FechaRegistro TEXT NOT NULL,
            FechaModificacion TEXT NOT NULL
        )
    """)

    loConn.commit()
    loConn.close()


def upsert_pago_callback(txData: dict):
    loConn = get_connection()
    loCursor = loConn.cursor()

    lcNumeroPagoEmpresa = limpiar_texto(txData.get("PedidoID"))
    lcFecha = limpiar_texto(txData.get("Fecha"))
    lcHora = limpiar_texto(txData.get("Hora"))
    lcMetodoPago = limpiar_texto(txData.get("MetodoPago"))
    lcEstado = limpiar_texto(txData.get("Estado"))
    lcJsonCallback = json.dumps(txData, ensure_ascii=False)
    lcAhora = get_fecha_hora_actual()

    if not lcNumeroPagoEmpresa:
        raise ValueError("No se recibió PedidoID en el callback.")

    loCursor.execute("""
        SELECT PagoWeb
        FROM PAGOWEB
        WHERE NumeroPagoEmpresa = ?
    """, (lcNumeroPagoEmpresa,))
    loFila = loCursor.fetchone()

    if loFila:
        loCursor.execute("""
            UPDATE PAGOWEB
            SET
                PedidoID = ?,
                Fecha = ?,
                Hora = ?,
                MetodoPago = ?,
                Estado = ?,
                JsonCallback = ?,
                FechaModificacion = ?
            WHERE NumeroPagoEmpresa = ?
        """, (
            lcNumeroPagoEmpresa,
            lcFecha,
            lcHora,
            lcMetodoPago,
            lcEstado,
            lcJsonCallback,
            lcAhora,
            lcNumeroPagoEmpresa
        ))
    else:
        loCursor.execute("""
            INSERT INTO PAGOWEB (
                NumeroPagoEmpresa,
                PedidoID,
                Fecha,
                Hora,
                MetodoPago,
                Estado,
                JsonCallback,
                FechaRegistro,
                FechaModificacion
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lcNumeroPagoEmpresa,
            lcNumeroPagoEmpresa,
            lcFecha,
            lcHora,
            lcMetodoPago,
            lcEstado,
            lcJsonCallback,
            lcAhora,
            lcAhora
        ))

    loConn.commit()
    loConn.close()


# =========================================================
# INTEGRACION CON EL SISTEMA PRINCIPAL
# =========================================================
def agregar_ruta_proyecto():
    lcBackendDir = os.path.dirname(__file__)
    lcProyectoDir = os.path.dirname(lcBackendDir)

    if lcProyectoDir not in sys.path:
        sys.path.insert(0, lcProyectoDir)


def estado_indica_pagado(tcEstado: str):
    lcEstado = limpiar_texto(tcEstado).lower()

    return lcEstado in (
        "2",
        "3",
        "pagado",
        "paid",
        "success",
        "successful",
        "completado",
        "completed"
    )


def es_metodo_qr(tcMetodoPago: str):
    lcMetodoPago = limpiar_texto(tcMetodoPago).lower()

    return lcMetodoPago in (
        "4",
        "qr",
        "masterqr",
        "qr master"
    )


def es_metodo_tigomoney(tcMetodoPago: str):
    lcMetodoPago = limpiar_texto(tcMetodoPago).lower()

    return lcMetodoPago in (
        "3",
        "5",
        "6",
        "tigomoney",
        "tigo money",
        "tigo"
    )


def detectar_metodo_por_numero_pago(tcNumeroPagoEmpresa: str):
    """
    Método de respaldo según el prefijo que genera el sistema.
    QR -> QR-
    Tigo Money -> TM-
    """
    lcNumeroPagoEmpresa = limpiar_texto(tcNumeroPagoEmpresa).upper()

    if lcNumeroPagoEmpresa.startswith("QR-"):
        return "QR"

    if lcNumeroPagoEmpresa.startswith("TM-"):
        return "TIGOMONEY"

    return ""


def confirmar_pago_en_sistema(tcNumeroPagoEmpresa: str, tcMetodoPago: str = ""):
    agregar_ruta_proyecto()

    txUsuarioData = {
        "Usuario": 1
    }

    lcMetodoPago = limpiar_texto(tcMetodoPago)
    lcMetodoDetectado = detectar_metodo_por_numero_pago(tcNumeroPagoEmpresa)

    if es_metodo_qr(lcMetodoPago) or lcMetodoDetectado == "QR":
        from servicios.pagoQr import confirmarPagoQr

        return confirmarPagoQr(
            tcNumeroPagoEmpresa=tcNumeroPagoEmpresa,
            tcNumeroTransaccion="",
            tnTipoDetalle=0,
            tnDetalle=0,
            tcConcepto="",
            tnMonto=0,
            txUsuarioData=txUsuarioData
        )

    if es_metodo_tigomoney(lcMetodoPago) or lcMetodoDetectado == "TIGOMONEY":
        from servicios.pagoTigoMoney import confirmarPagoTigoMoney

        return confirmarPagoTigoMoney(
            tcNumeroPagoEmpresa=tcNumeroPagoEmpresa,
            tcNumeroTransaccion="",
            tnTipoDetalle=0,
            tnDetalle=0,
            tcConcepto="",
            tnMonto=0,
            txUsuarioData=txUsuarioData
        )

    raise ValueError(
        f"No se pudo determinar el método de pago para confirmar automáticamente. "
        f"MetodoPago='{tcMetodoPago}', NumeroPagoEmpresa='{tcNumeroPagoEmpresa}'"
    )


def confirmar_pago_background(tcNumeroPagoEmpresa: str, tcMetodoPago: str = ""):
    """
    Confirmación en segundo plano.
    Así el callback responde rápido a PagoFácil y no genera 502 por lentitud.
    """
    try:
        print(f"[CALLBACK] Iniciando confirmación automática: {tcNumeroPagoEmpresa}")
        print(f"[CALLBACK] Método detectado/recibido: {tcMetodoPago}")

        txResultado = confirmar_pago_en_sistema(tcNumeroPagoEmpresa, tcMetodoPago)

        print(f"[CALLBACK] Confirmación automática OK: {tcNumeroPagoEmpresa}")
        print(json.dumps(txResultado, ensure_ascii=False, indent=2))

    except Exception as toError:
        print(f"[CALLBACK] Error en confirmación automática de {tcNumeroPagoEmpresa}: {str(toError)}")


def procesar_callback_pagofacil(txData: dict):
    lcNumeroPagoEmpresa = limpiar_texto(txData.get("PedidoID"))
    lcEstado = limpiar_texto(txData.get("Estado"))
    lcMetodoPago = limpiar_texto(txData.get("MetodoPago"))

    upsert_pago_callback(txData)

    if not lcNumeroPagoEmpresa:
        raise ValueError("No se recibió PedidoID en el callback.")

    print("\n" + "=" * 70)
    print("CALLBACK RECIBIDO")
    print("=" * 70)
    print(json.dumps(txData, ensure_ascii=False, indent=2))
    print("=" * 70 + "\n")

    return {
        "Procesado": True,
        "NumeroPagoEmpresa": lcNumeroPagoEmpresa,
        "Estado": lcEstado,
        "MetodoPago": lcMetodoPago
    }


# =========================================================
# EVENTOS
# =========================================================
@app.on_event("startup")
def startup_event():
    init_db()


# =========================================================
# ENDPOINTS
# =========================================================
@app.get("/")
def home():
    return {
        "ok": True,
        "message": "Backend de pagos activo"
    }


@app.post("/pagofacil/callback")
async def pagofacil_callback(request: Request, background_tasks: BackgroundTasks):
    try:
        lcContentType = limpiar_texto(request.headers.get("content-type")).lower()
        txBody = {}

        if "application/json" in lcContentType:
            txBody = await request.json()

        elif (
            "application/x-www-form-urlencoded" in lcContentType
            or "multipart/form-data" in lcContentType
        ):
            toForm = await request.form()
            txBody = dict(toForm)

        else:
            lbRaw = await request.body()
            txBody = leer_request_body(lbRaw)

        txResultadoProceso = procesar_callback_pagofacil(txBody)

        lcNumeroPagoEmpresa = limpiar_texto(txResultadoProceso.get("NumeroPagoEmpresa"))
        lcEstado = limpiar_texto(txResultadoProceso.get("Estado"))
        lcMetodoPago = limpiar_texto(txResultadoProceso.get("MetodoPago"))

        if lcNumeroPagoEmpresa and estado_indica_pagado(lcEstado):
            background_tasks.add_task(
                confirmar_pago_background,
                lcNumeroPagoEmpresa,
                lcMetodoPago
            )

        return {
            "error": 0,
            "status": 1,
            "message": "Callback recibido correctamente",
            "values": True
        }

    except Exception as toError:
        print(f"[CALLBACK] Error procesando callback: {str(toError)}")

        return {
            "error": 1,
            "status": 0,
            "message": f"Error procesando callback: {str(toError)}",
            "values": False
        }


@app.get("/pagos/{numero_pago_empresa}")
def obtener_pago(numero_pago_empresa: str):
    print(f"[BACKEND] Consultando pago: {numero_pago_empresa}")

    loConn = get_connection()
    loCursor = loConn.cursor()

    loCursor.execute("""
        SELECT
            NumeroPagoEmpresa,
            Fecha,
            Hora,
            MetodoPago,
            Estado,
            JsonCallback,
            FechaRegistro,
            FechaModificacion
        FROM PAGOWEB
        WHERE NumeroPagoEmpresa = ?
    """, (numero_pago_empresa,))
    loFila = loCursor.fetchone()
    loConn.close()

    if not loFila:
        return {
            "ok": False,
            "message": "Pago no encontrado"
        }

    return {
        "ok": True,
        "data": {
            "NumeroPagoEmpresa": loFila[0],
            "Fecha": loFila[1],
            "Hora": loFila[2],
            "MetodoPago": loFila[3],
            "Estado": loFila[4],
            "JsonCallback": loFila[5],
            "FechaRegistro": loFila[6],
            "FechaModificacion": loFila[7]
        }
    }


@app.get("/pagofacil/return")
def pagofacil_return():
    return {
        "ok": True,
        "message": "Retorno recibido"
    }