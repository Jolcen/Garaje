import tkinter as tk
from tkinter import messagebox
import base64
import io
import threading
import requests
import json

try:
    from PIL import Image, ImageTk
    PIL_DISPONIBLE = True
except Exception:
    PIL_DISPONIBLE = False

import servicios.pagoQr as pagoQr


# =========================================================
# CONSTANTES
# =========================================================
gnEstadoPreparado = 1
gnEstadoPendiente = 2
gnEstadoPagado = 3
gnEstadoFallido = 4
gnEstadoAnulado = 5
gnEstadoExpirado = 6

gxEstadoTexto = {
    gnEstadoPreparado: "Preparado",
    gnEstadoPendiente: "Pendiente",
    gnEstadoPagado: "Pagado",
    gnEstadoFallido: "Fallido",
    gnEstadoAnulado: "Anulado",
    gnEstadoExpirado: "Expirado",
}

gcBackendUrl = "http://127.0.0.1:8000"


# =========================================================
# UTILIDADES
# =========================================================
def limpiarTexto(tcValor):
    if tcValor is None:
        return ""
    return str(tcValor).strip()


def textoJson(txData):
    try:
        return json.dumps(txData, ensure_ascii=False, indent=2)
    except Exception:
        return str(txData)


# =========================================================
# FORMULARIO
# =========================================================
class FrmPagoQr(tk.Toplevel):
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

        self.toMaster = toMaster
        self.txUsuarioData = txUsuarioData or {}
        self.tnTipoDetalle = tnTipoDetalle
        self.tnDetalle = tnDetalle
        self.tcConcepto = limpiarTexto(tcConcepto)
        self.tnMonto = float(tnMonto)
        self.tfOnSave = tfOnSave

        self.tcNumeroPagoEmpresa = ""
        self.tcNumeroTransaccion = ""
        self.tcFechaExpiracion = ""
        self.tnEstadoTransaccion = 0
        self.toQrImageTk = None
        self.txUltimaRespuestaGeneracion = None
        self.tlQrGenerado = False
        self.toPollingId = None
        self.tlConsultando = False
        self.tlVentanaCerrada = False
        self.tlPagoProcesado = False

        self.title("Pago QR")
        self.geometry("560x760")
        self.resizable(False, False)
        self.configure(bg="#f4f6f8")
        self.transient(toMaster)
        self.grab_set()

        self.protocol("WM_DELETE_WINDOW", self.cerrarVentana)

        self.buildUi()
        self.centerWindow()

        self.after(100, self.generarQrAutomatico)

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
            text="Pago QR",
            font=("Arial", 18, "bold"),
            bg="#f4f6f8",
            fg="#111827"
        ).pack(anchor="center", pady=(0, 14))

        lofrmCard = tk.Frame(lofrmContainer, bg="white", bd=1, relief="solid")
        lofrmCard.pack(fill="both", expand=True)

        tk.Label(
            lofrmCard,
            text="Monto a pagar",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#374151"
        ).pack(pady=(18, 4))

        self.lblMonto = tk.Label(
            lofrmCard,
            text=f"Bs {self.tnMonto:.2f}",
            font=("Arial", 24, "bold"),
            bg="white",
            fg="#111827"
        )
        self.lblMonto.pack(pady=(0, 10))

        self.lblEstado = tk.Label(
            lofrmCard,
            text="Generando QR...",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#2563eb"
        )
        self.lblEstado.pack(pady=(0, 8))

        self.lblNumeroPagoEmpresaTitulo = tk.Label(
            lofrmCard,
            text="Número de pago empresa",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#374151"
        )
        self.lblNumeroPagoEmpresaTitulo.pack(pady=(4, 2))

        self.lblNumeroPagoEmpresa = tk.Label(
            lofrmCard,
            text="-",
            font=("Arial", 10),
            bg="white",
            fg="#111827",
            wraplength=480,
            justify="center"
        )
        self.lblNumeroPagoEmpresa.pack(pady=(0, 8))

        self.lblExpiracion = tk.Label(
            lofrmCard,
            text="",
            font=("Arial", 10),
            bg="white",
            fg="#6b7280"
        )
        self.lblExpiracion.pack(pady=(0, 12))

        self.lofrmQr = tk.Frame(
            lofrmCard,
            bg="#f9fafb",
            bd=1,
            relief="solid",
            width=430,
            height=430
        )
        self.lofrmQr.pack(pady=(0, 18))
        self.lofrmQr.pack_propagate(False)

        self.lblQr = tk.Label(
            self.lofrmQr,
            text="Generando QR...",
            font=("Arial", 12),
            bg="#f9fafb",
            fg="#6b7280"
        )
        self.lblQr.pack(expand=True)

        self.lblInfo = tk.Label(
            lofrmCard,
            text="Muestra este código al cliente para realizar el pago.",
            font=("Arial", 10),
            bg="white",
            fg="#6b7280"
        )
        self.lblInfo.pack(pady=(0, 16))

        lofrmBotones = tk.Frame(lofrmCard, bg="white")
        lofrmBotones.pack(fill="x", padx=18, pady=(0, 18))

        self.btnConsultar = tk.Button(
            lofrmBotones,
            text="Consultar estado",
            font=("Arial", 10, "bold"),
            bg="#059669",
            fg="white",
            bd=0,
            padx=12,
            pady=10,
            cursor="hand2",
            command=self.consultarEstadoManual
        )
        self.btnConsultar.pack(fill="x", pady=(0, 8))

        self.btnConfirmar = tk.Button(
            lofrmBotones,
            text="Confirmar pago",
            font=("Arial", 10, "bold"),
            bg="#7c3aed",
            fg="white",
            bd=0,
            padx=12,
            pady=10,
            cursor="hand2",
            command=self.confirmarPagoManual
        )
        self.btnConfirmar.pack(fill="x", pady=(0, 8))

        self.btnCerrar = tk.Button(
            lofrmBotones,
            text="Cerrar",
            font=("Arial", 10, "bold"),
            bg="#6b7280",
            fg="white",
            bd=0,
            padx=12,
            pady=10,
            cursor="hand2",
            command=self.cerrarVentana
        )
        self.btnCerrar.pack(fill="x")

    def imprimirDetalleTerminal(self):
        print("\n" + "=" * 70)
        print("PAGO QR - DETALLE DEL COBRO")
        print("=" * 70)
        print(f"TipoDetalle      : {self.tnTipoDetalle}")
        print(f"Detalle          : {self.tnDetalle}")
        print(f"Concepto         : {self.tcConcepto}")
        print(f"Monto            : Bs {self.tnMonto:.2f}")
        print(f"NumeroPagoEmpresa: {self.tcNumeroPagoEmpresa}")
        print(f"NumeroTransaccion: {self.tcNumeroTransaccion}")
        print(f"FechaExpiracion  : {self.tcFechaExpiracion}")
        print(f"Estado           : {gxEstadoTexto.get(self.tnEstadoTransaccion, self.tnEstadoTransaccion)}")
        print("=" * 70 + "\n")

    def imprimirCallbackTerminal(self, txRespuesta):
        print("\n" + "=" * 70)
        print("CALLBACK QR RECIBIDO DESDE BACKEND")
        print("=" * 70)
        print(textoJson(txRespuesta))
        print("=" * 70 + "\n")

    def setEstadoVisual(self, tnEstado):
        self.tnEstadoTransaccion = tnEstado
        self.lblEstado.config(
            text=f"Estado: {gxEstadoTexto.get(tnEstado, f'Desconocido ({tnEstado})')}"
        )

    def iniciarPolling(self):
        if self.toPollingId:
            self.after_cancel(self.toPollingId)
        self.toPollingId = self.after(5000, self.verificarPagoAutomatico)

    def detenerPolling(self):
        if self.toPollingId:
            self.after_cancel(self.toPollingId)
            self.toPollingId = None

    def deshabilitarBotones(self):
        self.btnConsultar.config(state="disabled")
        self.btnConfirmar.config(state="disabled")

    def generarQrAutomatico(self):
        try:
            if self.tlQrGenerado:
                return

            if self.tnMonto <= 0:
                raise ValueError("El monto debe ser mayor a 0 para generar el QR.")

            self.update_idletasks()

            txResultado = pagoQr.generarPagoQr(
                tnTipoDetalle=self.tnTipoDetalle,
                tnDetalle=self.tnDetalle,
                tcConcepto=self.tcConcepto,
                tnMonto=self.tnMonto,
                txUsuarioData=self.txUsuarioData
            )

            if not isinstance(txResultado, dict):
                raise ValueError("La respuesta de generar QR no es válida.")

            self.txUltimaRespuestaGeneracion = txResultado

            self.tcNumeroPagoEmpresa = limpiarTexto(txResultado.get("NumeroPagoEmpresa"))
            self.tcNumeroTransaccion = limpiarTexto(txResultado.get("NumeroTransaccion"))
            self.tcFechaExpiracion = limpiarTexto(txResultado.get("FechaHoraExpiracion"))
            self.setEstadoVisual(int(txResultado.get("EstadoTransaccion", gnEstadoPendiente)))

            self.lblNumeroPagoEmpresa.config(
                text=self.tcNumeroPagoEmpresa if self.tcNumeroPagoEmpresa else "-"
            )

            if self.tcFechaExpiracion:
                self.lblExpiracion.config(text=f"Expira en: {self.tcFechaExpiracion}")
            else:
                self.lblExpiracion.config(text="")

            lcQrBase64 = limpiarTexto(txResultado.get("QrBase64"))
            if lcQrBase64:
                self.mostrarQrBase64(lcQrBase64)
            else:
                self.lblQr.config(
                    text="No se recibió la imagen del QR.",
                    image=""
                )
                self.toQrImageTk = None

            self.tlQrGenerado = True
            self.iniciarPolling()

            self.imprimirDetalleTerminal()

        except Exception as toError:
            self.lblEstado.config(text="Error al generar QR")
            self.lblInfo.config(text=str(toError))
            self.lblQr.config(text="No se pudo generar el QR.", image="")
            messagebox.showerror("Error", str(toError), parent=self)

    def mostrarQrBase64(self, tcQrBase64):
        if not PIL_DISPONIBLE:
            self.lblQr.config(
                text="Pillow no está instalado.\nNo se puede renderizar el QR.",
                image=""
            )
            self.toQrImageTk = None
            return

        try:
            lbData = base64.b64decode(tcQrBase64)
            loImage = Image.open(io.BytesIO(lbData))
            loImage = loImage.resize((410, 410))
            self.toQrImageTk = ImageTk.PhotoImage(loImage)

            self.lblQr.config(
                image=self.toQrImageTk,
                text=""
            )
        except Exception as toError:
            self.lblQr.config(
                text=f"No se pudo mostrar el QR.\n{str(toError)}",
                image=""
            )
            self.toQrImageTk = None

    def consultarEstadoManual(self):
        if self.tlConsultando or self.tlPagoProcesado:
            return

        self.tlConsultando = True
        self.lblInfo.config(text="Consultando estado del pago...")

        th = threading.Thread(target=self._consultar_callback_worker, args=(False,), daemon=True)
        th.start()

    def verificarPagoAutomatico(self):
        if self.tlVentanaCerrada or self.tlPagoProcesado:
            return

        if self.tlConsultando:
            self.toPollingId = self.after(5000, self.verificarPagoAutomatico)
            return

        self.tlConsultando = True
        th = threading.Thread(target=self._consultar_callback_worker, args=(True,), daemon=True)
        th.start()

    def _consultar_callback_worker(self, tlAutomatico):
        try:
            if not self.tcNumeroPagoEmpresa:
                raise ValueError("No existe NumeroPagoEmpresa para consultar callback.")

            lcUrl = f"{gcBackendUrl}/pagos/{self.tcNumeroPagoEmpresa}"
            loResponse = requests.get(lcUrl, timeout=12)

            try:
                txRespuesta = loResponse.json()
            except Exception:
                raise ValueError(
                    f"El backend devolvió una respuesta inválida. HTTP {loResponse.status_code}. "
                    f"Respuesta: {loResponse.text}"
                )

            if loResponse.status_code >= 400:
                raise ValueError(
                    f"Error HTTP {loResponse.status_code}: "
                    f"{txRespuesta.get('message') or loResponse.text}"
                )

            self.after(
                0,
                lambda txResp=txRespuesta, tlAuto=tlAutomatico:
                    self._procesar_resultado_callback(txResp, tlAuto)
            )

        except Exception as e:
            lcError = str(e)
            self.after(
                0,
                lambda tcError=lcError, tlAuto=tlAutomatico:
                    self._procesar_error_callback(tcError, tlAuto)
            )

    def _procesar_resultado_callback(self, txRespuesta, tlAutomatico):
        self.tlConsultando = False

        if self.tlVentanaCerrada or self.tlPagoProcesado:
            return

        try:
            if not isinstance(txRespuesta, dict):
                raise ValueError("La respuesta del backend no es válida.")

            if not txRespuesta.get("ok"):
                if tlAutomatico and not self.tlVentanaCerrada:
                    self.lblInfo.config(text="Esperando confirmación del pago...")
                    self.toPollingId = self.after(5000, self.verificarPagoAutomatico)
                elif not tlAutomatico:
                    messagebox.showinfo(
                        "Sin confirmación",
                        "Aún no se recibió confirmación del pago.",
                        parent=self
                    )
                return

            self.imprimirCallbackTerminal(txRespuesta)

            txData = txRespuesta.get("data") or {}
            lcEstado = limpiarTexto(txData.get("Estado")).lower()
            lcFecha = limpiarTexto(txData.get("Fecha"))
            lcHora = limpiarTexto(txData.get("Hora"))

            if lcEstado in ("2", "3", "pagado", "paid", "success", "successful", "completado", "completed"):
                self.tlPagoProcesado = True
                self.setEstadoVisual(gnEstadoPagado)
                self.lblInfo.config(
                    text=f"Pago confirmado automáticamente: {lcFecha} {lcHora}".strip()
                )

                self.detenerPolling()
                self.deshabilitarBotones()

                messagebox.showinfo(
                    "Pago confirmado",
                    "El pago fue confirmado",
                    parent=self
                )

                if self.tfOnSave:
                    self.tfOnSave(None)

                self.tlVentanaCerrada = True
                self.destroy()
                return

            if tlAutomatico and not self.tlVentanaCerrada:
                self.lblInfo.config(text="Esperando confirmación del pago...")
                self.toPollingId = self.after(5000, self.verificarPagoAutomatico)
            elif not tlAutomatico:
                messagebox.showinfo(
                    "Aún pendiente",
                    "El callback ya existe, pero el estado aún no figura como pagado.",
                    parent=self
                )

        except Exception as e:
            if not tlAutomatico:
                messagebox.showerror("Error", str(e), parent=self)
            elif not self.tlVentanaCerrada:
                self.lblInfo.config(text="Esperando confirmación del pago...")
                self.toPollingId = self.after(5000, self.verificarPagoAutomatico)

    def _procesar_error_callback(self, tcError, tlAutomatico):
        self.tlConsultando = False

        if self.tlVentanaCerrada or self.tlPagoProcesado:
            return

        if not tlAutomatico:
            print("ERROR CALLBACK:", tcError)
            messagebox.showerror("Error", tcError, parent=self)
        else:
            self.lblInfo.config(text="Esperando confirmación del pago...")

        if tlAutomatico and not self.tlVentanaCerrada:
            self.toPollingId = self.after(5000, self.verificarPagoAutomatico)

    def confirmarPagoManual(self):
        try:
            if self.tlPagoProcesado:
                return

            if not self.tcNumeroPagoEmpresa and not self.tcNumeroTransaccion:
                raise ValueError("Primero debe generarse el QR.")

            llOk = messagebox.askyesno(
                "Confirmar pago",
                "Esta opción debe usarse solo si ya verificó que el pago fue realizado.\n\n¿Desea continuar?",
                parent=self
            )
            if not llOk:
                return

            self.registrarPagoConfirmado()

        except Exception as toError:
            messagebox.showerror("Error", str(toError), parent=self)

    def registrarPagoConfirmado(self):
        try:
            if self.tlPagoProcesado:
                return

            txResultado = pagoQr.confirmarPagoQr(
                tcNumeroPagoEmpresa=self.tcNumeroPagoEmpresa,
                tcNumeroTransaccion=self.tcNumeroTransaccion,
                tnTipoDetalle=self.tnTipoDetalle,
                tnDetalle=self.tnDetalle,
                tcConcepto=self.tcConcepto,
                tnMonto=self.tnMonto,
                txUsuarioData=self.txUsuarioData
            )

            if not isinstance(txResultado, dict):
                raise ValueError("La confirmación del pago no devolvió una respuesta válida.")

            tnPago = txResultado.get("Pago")

            self.tlPagoProcesado = True
            self.setEstadoVisual(gnEstadoPagado)
            self.lblInfo.config(text="El pago QR fue confirmado y registrado correctamente.")

            self.imprimirDetalleTerminal()

            self.detenerPolling()
            self.deshabilitarBotones()

            messagebox.showinfo("Éxito", "El pago QR fue registrado correctamente.", parent=self)

            if self.tfOnSave:
                self.tfOnSave(tnPago)

            self.tlVentanaCerrada = True
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def cerrarVentana(self):
        llSalir = messagebox.askyesno(
            "Cerrar",
            "Si cierra esta ventana y el QR no fue pagado, la operación seguirá pendiente.\n\n¿Desea cerrar?",
            parent=self
        )
        if llSalir:
            self.tlVentanaCerrada = True
            self.detenerPolling()
            self.destroy()