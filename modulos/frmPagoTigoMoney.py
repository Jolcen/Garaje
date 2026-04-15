import tkinter as tk
from tkinter import messagebox
import threading
import requests
import json
import os

from dotenv import load_dotenv

import servicios.pagoTigoMoney as pagoTigoMoney


# =========================================================
# CONFIGURACION
# =========================================================
load_dotenv()

gcBackendUrl = os.getenv("BACKEND_PAGOS_BASE_URL", "http://127.0.0.1:8000").strip()


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


def esTelefonoValido(tcTelefono):
    lcTelefono = limpiarTexto(tcTelefono)
    return lcTelefono.isdigit() and len(lcTelefono) in (7, 8)


# =========================================================
# FORMULARIO
# =========================================================
class FrmPagoTigoMoney(tk.Toplevel):
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
        self.txUltimaRespuestaGeneracion = None
        self.tlTransaccionGenerada = False
        self.toPollingId = None
        self.tlConsultando = False
        self.tlVentanaCerrada = False
        self.tlPagoProcesado = False

        self.txDatosCliente = pagoTigoMoney.obtenerDatosClienteTigoMoney(
            self.tnTipoDetalle,
            self.tnDetalle
        )

        self.lovNombreCliente = tk.StringVar(
            value=limpiarTexto(self.txDatosCliente.get("NombreCliente", ""))
        )
        self.lovDocumento = tk.StringVar(
            value=limpiarTexto(self.txDatosCliente.get("Documento", ""))
        )
        self.lovTelefono = tk.StringVar(
            value=limpiarTexto(self.txDatosCliente.get("Telefono", ""))
        )
        self.lovCorreo = tk.StringVar(
            value=limpiarTexto(self.txDatosCliente.get("Correo", ""))
        )

        self.title("Pago Tigo Money")
        self.geometry("620x900")
        self.minsize(620, 900)
        self.resizable(False, False)
        self.configure(bg="#f4f6f8")
        self.transient(toMaster)
        self.grab_set()

        self.protocol("WM_DELETE_WINDOW", self.cerrarVentana)

        self.buildUi()
        self.centerWindow()

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
            text="Pago Tigo Money",
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
            text="Completa los datos y genera la transacción.",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#2563eb"
        )
        self.lblEstado.pack(pady=(0, 12))

        lofrmDatos = tk.Frame(lofrmCard, bg="white")
        lofrmDatos.pack(fill="x", padx=18, pady=(0, 12))

        self.crearCampo(lofrmDatos, "Cliente:", self.lovNombreCliente, 0)
        self.crearCampo(lofrmDatos, "Documento / CI / NIT:", self.lovDocumento, 1)
        self.crearCampo(lofrmDatos, "Teléfono:", self.lovTelefono, 2)
        self.crearCampo(lofrmDatos, "Correo:", self.lovCorreo, 3)

        self.lblNumeroPagoEmpresaTitulo = tk.Label(
            lofrmCard,
            text="Número de pago empresa",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#374151"
        )
        self.lblNumeroPagoEmpresaTitulo.pack(pady=(6, 2))

        self.lblNumeroPagoEmpresa = tk.Label(
            lofrmCard,
            text="-",
            font=("Arial", 10),
            bg="white",
            fg="#111827",
            wraplength=540,
            justify="center"
        )
        self.lblNumeroPagoEmpresa.pack(pady=(0, 8))

        self.lblNumeroTransaccionTitulo = tk.Label(
            lofrmCard,
            text="Número de transacción",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#374151"
        )
        self.lblNumeroTransaccionTitulo.pack(pady=(4, 2))

        self.lblNumeroTransaccion = tk.Label(
            lofrmCard,
            text="-",
            font=("Arial", 10),
            bg="white",
            fg="#111827",
            wraplength=540,
            justify="center"
        )
        self.lblNumeroTransaccion.pack(pady=(0, 8))

        self.lblExpiracion = tk.Label(
            lofrmCard,
            text="",
            font=("Arial", 10),
            bg="white",
            fg="#6b7280"
        )
        self.lblExpiracion.pack(pady=(0, 10))

        self.lblInfo = tk.Label(
            lofrmCard,
            text="Genera la transacción para iniciar el cobro con Tigo Money.",
            font=("Arial", 10),
            bg="white",
            fg="#6b7280",
            wraplength=540,
            justify="center"
        )
        self.lblInfo.pack(pady=(0, 16))

        self.txtDetalle = tk.Text(
            lofrmCard,
            height=8,
            font=("Courier New", 9),
            bg="#f9fafb",
            fg="#111827",
            bd=1,
            relief="solid"
        )
        self.txtDetalle.pack(fill="x", padx=18, pady=(0, 18))
        self.txtDetalle.insert("1.0", "Aquí se mostrará el detalle de la transacción.")
        self.txtDetalle.config(state="disabled")

        lofrmBotones = tk.Frame(lofrmCard, bg="white")
        lofrmBotones.pack(fill="x", padx=18, pady=(0, 18))

        self.btnGenerar = tk.Button(
            lofrmBotones,
            text="Generar transacción",
            font=("Arial", 10, "bold"),
            bg="#2563eb",
            fg="white",
            bd=0,
            padx=12,
            pady=10,
            cursor="hand2",
            command=self.generarTransaccion
        )
        self.btnGenerar.pack(fill="x", pady=(0, 8))

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

    def crearCampo(self, toParent, tcLabel, toVariable, tnRow):
        tk.Label(
            toParent,
            text=tcLabel,
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#374151"
        ).grid(row=tnRow, column=0, sticky="w", pady=(0, 10), padx=(0, 10))

        lotxt = tk.Entry(
            toParent,
            textvariable=toVariable,
            font=("Arial", 10),
            bg="white",
            fg="#111827",
            relief="solid",
            bd=1
        )
        lotxt.grid(row=tnRow, column=1, sticky="ew", pady=(0, 10))

        toParent.columnconfigure(1, weight=1)

    def actualizarDetalleTexto(self, tcTexto):
        self.txtDetalle.config(state="normal")
        self.txtDetalle.delete("1.0", "end")
        self.txtDetalle.insert("1.0", limpiarTexto(tcTexto) or "-")
        self.txtDetalle.config(state="disabled")

    def imprimirDetalleTerminal(self):
        print("\n" + "=" * 70)
        print("PAGO TIGO MONEY - DETALLE DEL COBRO")
        print("=" * 70)
        print(f"TipoDetalle      : {self.tnTipoDetalle}")
        print(f"Detalle          : {self.tnDetalle}")
        print(f"Concepto         : {self.tcConcepto}")
        print(f"Monto            : Bs {self.tnMonto:.2f}")
        print(f"NombreCliente    : {self.lovNombreCliente.get()}")
        print(f"Documento        : {self.lovDocumento.get()}")
        print(f"Telefono         : {self.lovTelefono.get()}")
        print(f"Correo           : {self.lovCorreo.get()}")
        print(f"NumeroPagoEmpresa: {self.tcNumeroPagoEmpresa}")
        print(f"NumeroTransaccion: {self.tcNumeroTransaccion}")
        print(f"FechaExpiracion  : {self.tcFechaExpiracion}")
        print(f"Estado           : {gxEstadoTexto.get(self.tnEstadoTransaccion, self.tnEstadoTransaccion)}")
        print("=" * 70 + "\n")

    def imprimirCallbackTerminal(self, txRespuesta):
        print("\n" + "=" * 70)
        print("CALLBACK TIGO MONEY RECIBIDO DESDE BACKEND")
        print("=" * 70)
        print(textoJson(txRespuesta))
        print("=" * 70 + "\n")

    def setEstadoVisual(self, tnEstado):
        self.tnEstadoTransaccion = tnEstado
        self.lblEstado.config(
            text=f"Estado: {gxEstadoTexto.get(tnEstado, f'Desconocido ({tnEstado})')}"
        )

    def validarDatos(self):
        lcNombreCliente = limpiarTexto(self.lovNombreCliente.get())
        lcDocumento = limpiarTexto(self.lovDocumento.get())
        lcTelefono = limpiarTexto(self.lovTelefono.get())
        lcCorreo = limpiarTexto(self.lovCorreo.get())

        if not lcNombreCliente:
            raise ValueError("Debes ingresar el nombre del cliente.")

        if not lcDocumento:
            raise ValueError("Debes ingresar el documento o CI/NIT.")

        if not lcTelefono:
            raise ValueError("Debes ingresar el teléfono.")
        if not esTelefonoValido(lcTelefono):
            raise ValueError("El teléfono debe tener 7 u 8 dígitos.")

        if not lcCorreo:
            raise ValueError("Debes ingresar el correo.")

        return {
            "NombreCliente": lcNombreCliente,
            "Documento": lcDocumento,
            "Telefono": lcTelefono,
            "Correo": lcCorreo
        }

    def iniciarPolling(self):
        if self.toPollingId:
            self.after_cancel(self.toPollingId)
        self.toPollingId = self.after(5000, self.verificarPagoAutomatico)

    def detenerPolling(self):
        if self.toPollingId:
            self.after_cancel(self.toPollingId)
            self.toPollingId = None

    def deshabilitarBotones(self):
        self.btnGenerar.config(state="disabled")
        self.btnConsultar.config(state="disabled")
        self.btnConfirmar.config(state="disabled")

    def generarTransaccion(self):
        try:
            if self.tlTransaccionGenerada:
                llNueva = messagebox.askyesno(
                    "Regenerar",
                    "Ya existe una transacción generada.\n\n¿Deseas generar una nueva transacción?",
                    parent=self
                )
                if not llNueva:
                    return

            if self.tnMonto <= 0:
                raise ValueError("El monto debe ser mayor a 0 para generar Tigo Money.")

            txDatosFormulario = self.validarDatos()

            txResultado = pagoTigoMoney.generarPagoTigoMoney(
                tnTipoDetalle=self.tnTipoDetalle,
                tnDetalle=self.tnDetalle,
                tcConcepto=self.tcConcepto,
                tnMonto=self.tnMonto,
                txUsuarioData=self.txUsuarioData,
                tcNombreCliente=txDatosFormulario["NombreCliente"],
                tcDocumento=txDatosFormulario["Documento"],
                tcTelefono=txDatosFormulario["Telefono"],
                tcCorreo=txDatosFormulario["Correo"]
            )

            if not isinstance(txResultado, dict):
                raise ValueError("La respuesta de Tigo Money no es válida.")

            self.txUltimaRespuestaGeneracion = txResultado
            self.tcNumeroPagoEmpresa = limpiarTexto(txResultado.get("NumeroPagoEmpresa"))
            self.tcNumeroTransaccion = limpiarTexto(txResultado.get("NumeroTransaccion"))
            self.tcFechaExpiracion = limpiarTexto(txResultado.get("FechaHoraExpiracion"))
            self.setEstadoVisual(int(txResultado.get("EstadoTransaccion", gnEstadoPendiente)))

            self.lblNumeroPagoEmpresa.config(
                text=self.tcNumeroPagoEmpresa if self.tcNumeroPagoEmpresa else "-"
            )
            self.lblNumeroTransaccion.config(
                text=self.tcNumeroTransaccion if self.tcNumeroTransaccion else "-"
            )

            if self.tcFechaExpiracion:
                self.lblExpiracion.config(text=f"Expira en: {self.tcFechaExpiracion}")
            else:
                self.lblExpiracion.config(text="")

            self.lblInfo.config(
                text="Transacción generada. Ahora puedes consultar el estado o confirmar el pago."
            )

            self.actualizarDetalleTexto(
                txResultado.get("RespuestaTexto") or "Transacción generada."
            )

            self.tlTransaccionGenerada = True
            self.iniciarPolling()

            self.imprimirDetalleTerminal()

            messagebox.showinfo(
                "Éxito",
                "La transacción Tigo Money fue generada correctamente.",
                parent=self
            )

        except Exception as toError:
            self.lblEstado.config(text="Error al generar Tigo Money")
            self.lblInfo.config(text=str(toError))
            self.actualizarDetalleTexto(str(toError))
            messagebox.showerror("Error", str(toError), parent=self)

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
                    "El pago fue confirmado.",
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
            print("ERROR CALLBACK TIGO MONEY:", tcError)
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
                raise ValueError("Primero debe generarse la transacción Tigo Money.")

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

            txResultado = pagoTigoMoney.confirmarPagoTigoMoney(
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
            self.lblInfo.config(text="El pago Tigo Money fue confirmado y registrado correctamente.")
            self.actualizarDetalleTexto(
                txResultado.get("RespuestaTexto") or "Pago confirmado."
            )

            self.imprimirDetalleTerminal()

            self.detenerPolling()
            self.deshabilitarBotones()

            messagebox.showinfo(
                "Éxito",
                "El pago Tigo Money fue registrado correctamente.",
                parent=self
            )

            if self.tfOnSave:
                self.tfOnSave(tnPago)

            self.tlVentanaCerrada = True
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def cerrarVentana(self):
        llSalir = messagebox.askyesno(
            "Cerrar",
            "Si cierra esta ventana y la transacción no fue pagada, la operación seguirá pendiente.\n\n¿Desea cerrar?",
            parent=self
        )
        if llSalir:
            self.tlVentanaCerrada = True
            self.detenerPolling()
            self.destroy()