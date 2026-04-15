import tkinter as tk
from tkinter import ttk, messagebox

from servicios.pagoService import obtenerContextoDetalle, cerrarOperacionSinPago
from modulos.frmPagoEfectivo import FrmPagoEfectivo
from modulos.frmPagoCodigoYape import FrmPagoCodigoYape
from modulos.frmPagoQr import FrmPagoQr
from modulos.frmPagoTigoMoney import FrmPagoTigoMoney


# =========================================================
# CONSTANTES
# =========================================================
gnMetodoPagoEfectivo = 1
gnMetodoPagoCodigoYape = 2
gnMetodoPagoQr = 3
gnMetodoPagoTigoMoney = 4

gnTipoDetalleOperacion = 1
gnTipoDetalleContrato = 2

gxMetodoPagoTexto = {
    gnMetodoPagoEfectivo: "Efectivo",
    gnMetodoPagoCodigoYape: "Código Yape",
    gnMetodoPagoQr: "QR",
    gnMetodoPagoTigoMoney: "Tigo Money",
}

gxMetodoPagoInv = {tcValor: tnClave for tnClave, tcValor in gxMetodoPagoTexto.items()}

gxTipoDetalleTexto = {
    gnTipoDetalleOperacion: "Operación",
    gnTipoDetalleContrato: "Contrato",
}


# =========================================================
# UTILIDADES
# =========================================================
def limpiarTexto(tcValor):
    if tcValor is None:
        return ""
    return str(tcValor).strip()


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

        self.toMaster = toMaster
        self.txUsuarioData = txUsuarioData or {}
        self.tnTipoDetalle = tnTipoDetalle
        self.tnDetalle = tnDetalle
        self.tcConcepto = limpiarTexto(tcConcepto)
        self.tnMonto = float(tnMonto)
        self.tfOnSave = tfOnSave

        self.txContexto = obtenerContextoDetalle(self.tnTipoDetalle, self.tnDetalle)

        self.lovMetodoPago = tk.StringVar(value="Efectivo")

        self.title("Cobros")
        self.geometry("560x460")
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
            text="Cobro",
            font=("Arial", 16, "bold"),
            bg="#f4f6f8",
            fg="#111827"
        ).pack(anchor="w", pady=(0, 12))

        lofrmCard = tk.Frame(lofrmContainer, bg="white", bd=1, relief="solid")
        lofrmCard.pack(fill="both", expand=True)

        lofrmCard.columnconfigure(1, weight=1)

        self.addInfoRow(lofrmCard, "Tipo:", gxTipoDetalleTexto.get(self.tnTipoDetalle, "N/D"), 0)
        self.addInfoRow(lofrmCard, "Referencia:", str(self.tnDetalle), 1)
        self.addInfoRow(lofrmCard, "Cliente:", limpiarTexto(self.txContexto.get("NombreCliente", "")) or "N/D", 2)
        self.addInfoRow(lofrmCard, "Concepto:", self.tcConcepto, 3)
        self.addInfoRow(lofrmCard, "Monto:", f"Bs {self.tnMonto:.2f}", 4)

        tk.Label(
            lofrmCard,
            text="Método de pago:",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#374151"
        ).grid(row=5, column=0, sticky="w", padx=14, pady=(14, 6))

        self.locboMetodo = ttk.Combobox(
            lofrmCard,
            textvariable=self.lovMetodoPago,
            values=list(gxMetodoPagoInv.keys()),
            state="readonly",
            width=24
        )
        self.locboMetodo.grid(row=5, column=1, sticky="w", padx=(0, 14), pady=(14, 6))

        self.lblInfo = tk.Label(
            lofrmCard,
            text="Selecciona el método de pago para continuar con el cobro.",
            font=("Arial", 9),
            bg="white",
            fg="#6b7280",
            wraplength=460,
            justify="left"
        )
        self.lblInfo.grid(row=6, column=0, columnspan=2, sticky="w", padx=14, pady=(6, 14))

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

        self.btnContinuar = tk.Button(
            lofrmBotones,
            text="Continuar",
            font=("Arial", 10, "bold"),
            bg="#059669",
            fg="white",
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            command=self.procesarCobro
        )
        self.btnContinuar.pack(side="right", padx=(0, 8))

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

    def procesarCobro(self):
        try:
            if self.tnMonto < 0:
                raise ValueError("El monto no puede ser negativo.")

            if self.tnMonto == 0:
                self.finalizarOperacionSinPago()
                return

            lcMetodoPago = self.lovMetodoPago.get().strip()

            if lcMetodoPago not in gxMetodoPagoInv:
                raise ValueError("Debes seleccionar un método de pago válido.")

            tnMetodoPago = gxMetodoPagoInv[lcMetodoPago]

            if tnMetodoPago == gnMetodoPagoEfectivo:
                self.abrirFormularioEfectivo()
                return

            if tnMetodoPago == gnMetodoPagoCodigoYape:
                self.abrirFormularioCodigoYape()
                return

            if tnMetodoPago == gnMetodoPagoQr:
                self.abrirFormularioQr()
                return

            if tnMetodoPago == gnMetodoPagoTigoMoney:
                self.abrirFormularioTigoMoney()
                return

            raise ValueError("El método de pago seleccionado no está soportado.")

        except Exception as toError:
            messagebox.showerror("Error", str(toError), parent=self)

    def finalizarOperacionSinPago(self):
        llOk = messagebox.askyesno(
            "Finalizar operación",
            "El monto total es Bs 0.00.\n\n¿Deseas finalizar la operación sin registrar pago?",
            parent=self
        )
        if not llOk:
            return

        txResultado = cerrarOperacionSinPago(
            tnTipoDetalle=self.tnTipoDetalle,
            tnDetalle=self.tnDetalle,
            tcConcepto=self.tcConcepto,
            txUsuarioData=self.txUsuarioData
        )

        if self.tfOnSave:
            self.tfOnSave(txResultado["Detalle"])

        messagebox.showinfo(
            "Éxito",
            "La operación fue finalizada correctamente sin pago.",
            parent=self
        )
        self.destroy()

    def abrirFormularioEfectivo(self):
        self.withdraw()

        def onSaveEfectivo(tnPago):
            if self.tfOnSave:
                self.tfOnSave(tnPago)
            self.destroy()

        loFrm = FrmPagoEfectivo(
            self.toMaster,
            self.txUsuarioData,
            self.tnTipoDetalle,
            self.tnDetalle,
            self.tcConcepto,
            self.tnMonto,
            tfOnSave=onSaveEfectivo
        )

        self.wait_window(loFrm)

        if self.winfo_exists():
            self.deiconify()
            self.grab_set()

    def abrirFormularioCodigoYape(self):
        self.withdraw()

        def onSaveCodigoYape(tnPago):
            if self.tfOnSave:
                self.tfOnSave(tnPago)
            self.destroy()

        loFrm = FrmPagoCodigoYape(
            self.toMaster,
            self.txUsuarioData,
            self.tnTipoDetalle,
            self.tnDetalle,
            self.tcConcepto,
            self.tnMonto,
            tfOnSave=onSaveCodigoYape
        )

        self.wait_window(loFrm)

        if self.winfo_exists():
            self.deiconify()
            self.grab_set()

    def abrirFormularioQr(self):
        self.withdraw()

        def onSaveQr(tnPago):
            if self.tfOnSave:
                self.tfOnSave(tnPago)
            self.destroy()

        loFrm = FrmPagoQr(
            self.toMaster,
            self.txUsuarioData,
            self.tnTipoDetalle,
            self.tnDetalle,
            self.tcConcepto,
            self.tnMonto,
            tfOnSave=onSaveQr
        )

        self.wait_window(loFrm)

        if self.winfo_exists():
            self.deiconify()
            self.grab_set()

    def abrirFormularioTigoMoney(self):
        self.withdraw()

        def onSaveTigoMoney(tnPago):
            if self.tfOnSave:
                self.tfOnSave(tnPago)
            self.destroy()

        loFrm = FrmPagoTigoMoney(
            self.toMaster,
            self.txUsuarioData,
            self.tnTipoDetalle,
            self.tnDetalle,
            self.tcConcepto,
            self.tnMonto,
            tfOnSave=onSaveTigoMoney
        )

        self.wait_window(loFrm)

        if self.winfo_exists():
            self.deiconify()
            self.grab_set()