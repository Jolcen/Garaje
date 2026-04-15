import tkinter as tk
from tkinter import messagebox

from servicios.pagoService import obtenerContextoDetalle, limpiarTexto
from servicios.pagoCodigoYape import (
    prepararRegistroPagoCodigoYape,
    confirmarPagoCodigoYapeManual,
    consultarEstadoPagoCodigoYape,
)


# =========================================================
# CONSTANTES
# =========================================================
gnTipoDetalleOperacion = 1
gnTipoDetalleContrato = 2

gxTipoDetalleTexto = {
    gnTipoDetalleOperacion: "Operación",
    gnTipoDetalleContrato: "Contrato",
}

gnIntervaloConsultaCodigoYapeMs = 5000


# =========================================================
# FORMULARIO
# =========================================================
class FrmPagoCodigoYape(tk.Toplevel):
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

        self.txContexto = obtenerContextoDetalle(self.tnTipoDetalle, self.tnDetalle)

        self.txPagoCodigoYapeActual = None
        self.tnAfterConsultaCodigoYape = None
        self.llPagoConfirmado = False

        self.lovNombreCliente = tk.StringVar(
            value=limpiarTexto(self.txContexto.get("NombreCliente", ""))
        )
        self.lovCodigoClienteEmpresa = tk.StringVar(
            value=str(self.txContexto.get("Cliente", "") or self.tnDetalle)
        )
        self.lovTelefonoEnvio = tk.StringVar(
            value=limpiarTexto(self.txContexto.get("Telefono", ""))
        )
        self.lovTelefonoYape = tk.StringVar(
            value=limpiarTexto(self.txContexto.get("Telefono", ""))
        )
        self.lovCorreo = tk.StringVar(value="")
        self.lovCodigoPago = tk.StringVar(value="")

        self.title("Pago por código Yape")
        self.geometry("620x610")
        self.resizable(False, True)
        self.configure(bg="#f4f6f8")
        self.transient(toMaster)
        self.grab_set()

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
            text="Pago por código Yape",
            font=("Arial", 16, "bold"),
            bg="#f4f6f8",
            fg="#111827"
        ).pack(anchor="w", pady=(0, 12))

        lofrmCard = tk.Frame(lofrmContainer, bg="white", bd=1, relief="solid")
        lofrmCard.pack(fill="both", expand=True)

        lofrmCard.columnconfigure(1, weight=1)

        self.addInfoRow(lofrmCard, "Tipo:", gxTipoDetalleTexto.get(self.tnTipoDetalle, "N/D"), 0)
        self.addInfoRow(lofrmCard, "Referencia:", str(self.tnDetalle), 1)
        self.addInfoRow(
            lofrmCard,
            "Cliente:",
            limpiarTexto(self.txContexto.get("NombreCliente", "")) or "N/D",
            2
        )
        self.addInfoRow(lofrmCard, "Concepto:", self.tcConcepto, 3)
        self.addInfoRow(lofrmCard, "Monto:", f"Bs {self.tnMonto:.2f}", 4)

        self.lblInfo = tk.Label(
            lofrmCard,
            text=(
                "Primero se preparará el pago por código Yape. "
                "Luego debes ingresar el código recibido para confirmar el pago."
            ),
            font=("Arial", 9),
            bg="white",
            fg="#6b7280",
            wraplength=520,
            justify="left"
        )
        self.lblInfo.grid(row=5, column=0, columnspan=2, sticky="w", padx=14, pady=(10, 10))

        self.addEntryRow(lofrmCard, "Nombre cliente:", self.lovNombreCliente, 6)
        self.addEntryRow(lofrmCard, "Código cliente empresa:", self.lovCodigoClienteEmpresa, 7)
        self.addEntryRow(lofrmCard, "Teléfono envío:", self.lovTelefonoEnvio, 8)
        self.addEntryRow(lofrmCard, "Teléfono Yape:", self.lovTelefonoYape, 9)
        self.addEntryRow(lofrmCard, "Correo:", self.lovCorreo, 10)
        self.addEntryRow(lofrmCard, "Código de pago:", self.lovCodigoPago, 11, state="disabled")

        self.lblEstado = tk.Label(
            lofrmCard,
            text="",
            font=("Arial", 9),
            bg="white",
            fg="#1f2937",
            wraplength=520,
            justify="left"
        )
        self.lblEstado.grid(row=12, column=0, columnspan=2, sticky="w", padx=14, pady=(10, 14))

        lofrmBotones = tk.Frame(lofrmContainer, bg="#f4f6f8")
        lofrmBotones.pack(fill="x", pady=(12, 0))

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

        self.btnConfirmarCodigo = tk.Button(
            lofrmBotones,
            text="Confirmar código",
            font=("Arial", 10, "bold"),
            bg="#2563eb",
            fg="white",
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            state="disabled",
            command=self.confirmarCodigoPago
        )
        self.btnConfirmarCodigo.pack(side="right", padx=(8, 0))

        self.btnPreparar = tk.Button(
            lofrmBotones,
            text="Preparar pago",
            font=("Arial", 10, "bold"),
            bg="#059669",
            fg="white",
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            command=self.prepararPago
        )
        self.btnPreparar.pack(side="right", padx=(8, 0))

    def addInfoRow(self, toParent, tcLabel, tcValue, tnRow):
        tk.Label(
            toParent,
            text=tcLabel,
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#374151"
        ).grid(row=tnRow, column=0, sticky="w", padx=14, pady=(12, 6))

        tk.Label(
            toParent,
            text=tcValue,
            font=("Arial", 10),
            bg="white",
            fg="#111827",
            anchor="w",
            justify="left"
        ).grid(row=tnRow, column=1, sticky="w", padx=(0, 14), pady=(12, 6))

    def addEntryRow(self, toParent, tcLabel, tvVariable, tnRow, state="normal"):
        tk.Label(
            toParent,
            text=tcLabel,
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#374151"
        ).grid(row=tnRow, column=0, sticky="w", padx=14, pady=(8, 4))

        loEntry = tk.Entry(
            toParent,
            textvariable=tvVariable,
            font=("Arial", 10),
            width=36,
            state=state
        )
        loEntry.grid(row=tnRow, column=1, sticky="we", padx=(0, 14), pady=(8, 4))

        if tcLabel == "Código de pago:":
            self.txtCodigoPago = loEntry

        return loEntry

    def construirDatosPagoCodigoYape(self):
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
            "NombreCliente": limpiarTexto(self.lovNombreCliente.get()),
            "CodigoClienteEmpresa": limpiarTexto(self.lovCodigoClienteEmpresa.get()),
            "TelefonoEnvio": limpiarTexto(self.lovTelefonoEnvio.get()),
            "TelefonoYape": limpiarTexto(self.lovTelefonoYape.get()),
            "Correo": limpiarTexto(self.lovCorreo.get()),
            "PedidoDetalle": txPedidoDetalle,
        }

    def iniciarConsultaAutomatica(self):
        self.detenerConsultaAutomatica()
        self.tnAfterConsultaCodigoYape = self.after(
            gnIntervaloConsultaCodigoYapeMs,
            self.verificarEstadoPago
        )

    def detenerConsultaAutomatica(self):
        if self.tnAfterConsultaCodigoYape:
            try:
                self.after_cancel(self.tnAfterConsultaCodigoYape)
            except Exception:
                pass
            self.tnAfterConsultaCodigoYape = None

    def prepararPago(self):
        try:
            if self.tnMonto <= 0:
                raise ValueError("El monto para código Yape debe ser mayor a 0.")

            if not limpiarTexto(self.lovNombreCliente.get()):
                raise ValueError("Debes ingresar el nombre del cliente.")

            if not limpiarTexto(self.lovCodigoClienteEmpresa.get()):
                raise ValueError("Debes ingresar el código cliente empresa.")

            if not limpiarTexto(self.lovTelefonoEnvio.get()):
                raise ValueError("Debes ingresar el teléfono de envío.")

            if not limpiarTexto(self.lovTelefonoYape.get()):
                raise ValueError("Debes ingresar el teléfono Yape.")

            txDatosPago = self.construirDatosPagoCodigoYape()

            llOk = messagebox.askyesno(
                "Preparar pago",
                f"¿Deseas preparar el pago por código Yape por Bs {self.tnMonto:.2f}?",
                parent=self
            )
            if not llOk:
                return

            self.btnPreparar.config(state="disabled")

            txResultado = prepararRegistroPagoCodigoYape(
                tnTipoDetalle=self.tnTipoDetalle,
                tnDetalle=self.tnDetalle,
                tcConcepto=self.tcConcepto,
                tnMonto=self.tnMonto,
                txPagoData=txDatosPago,
                txUsuarioData=self.txUsuarioData
            )

            self.txPagoCodigoYapeActual = txResultado
            self.llPagoConfirmado = False

            self.txtCodigoPago.config(state="normal")
            self.btnConfirmarCodigo.config(state="normal")
            self.lovCodigoPago.set("")
            self.txtCodigoPago.focus_set()

            self.lblEstado.config(
                text="Pago preparado correctamente. Ahora ingresa el código recibido para confirmar."
            )

            messagebox.showinfo(
                "Pago preparado",
                "El pago por código Yape fue preparado correctamente.",
                parent=self
            )

            self.iniciarConsultaAutomatica()

        except Exception as toError:
            self.btnPreparar.config(state="normal")
            messagebox.showerror(
                "Error",
                f"No se pudo preparar el pago por código Yape.\n{str(toError)}",
                parent=self
            )

    def confirmarCodigoPago(self):
        try:
            if not self.txPagoCodigoYapeActual:
                raise ValueError("Primero debes preparar el pago por código Yape.")

            lcCodigoPago = limpiarTexto(self.lovCodigoPago.get())
            if not lcCodigoPago:
                raise ValueError("Debes ingresar el código de pago.")

            self.btnConfirmarCodigo.config(state="disabled")

            txResultado = confirmarPagoCodigoYapeManual(
                tnPagoDigital=self.txPagoCodigoYapeActual["PagoDigital"],
                tcCodigoPago=lcCodigoPago,
                txUsuarioData=self.txUsuarioData
            )

            self.lblEstado.config(
                text=txResultado.get(
                    "Mensaje",
                    "Código enviado correctamente. Esperando confirmación del pago."
                )
            )

            messagebox.showinfo(
                "Código enviado",
                "El código fue enviado correctamente. Ahora el sistema esperará la confirmación.",
                parent=self
            )

            self.verificarEstadoPago()

        except Exception as toError:
            self.btnConfirmarCodigo.config(state="normal")
            messagebox.showerror(
                "Error",
                f"No se pudo confirmar el código Yape.\n{str(toError)}",
                parent=self
            )

    def verificarEstadoPago(self):
        try:
            if not self.txPagoCodigoYapeActual:
                return

            txEstado = consultarEstadoPagoCodigoYape(
                tnPagoDigital=self.txPagoCodigoYapeActual["PagoDigital"],
                txUsuarioData=self.txUsuarioData
            )

            lcEstado = limpiarTexto(txEstado.get("Estado", "")).upper()
            lcMensaje = limpiarTexto(txEstado.get("Mensaje", ""))

            if lcMensaje:
                self.lblEstado.config(text=lcMensaje)
            else:
                self.lblEstado.config(text="Esperando confirmación del pago...")

            if lcEstado == "PAGADO" and not self.llPagoConfirmado:
                self.llPagoConfirmado = True
                self.detenerConsultaAutomatica()

                if self.tfOnSave:
                    self.tfOnSave(self.txPagoCodigoYapeActual["Pago"])

                messagebox.showinfo(
                    "Pago confirmado",
                    "El pago por código Yape fue confirmado correctamente.",
                    parent=self
                )
                self.destroy()
                return

            self.iniciarConsultaAutomatica()

        except Exception:
            self.lblEstado.config(text="Esperando confirmación del pago...")
            self.iniciarConsultaAutomatica()

    def destroy(self):
        self.detenerConsultaAutomatica()
        super().destroy()