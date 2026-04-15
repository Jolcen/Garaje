import tkinter as tk
from tkinter import messagebox

from servicios.pagoService import obtenerContextoDetalle
from servicios.pagoEfectivo import registrarPagoEfectivo


# =========================================================
# CONSTANTES
# =========================================================
gnTipoDetalleOperacion = 1
gnTipoDetalleContrato = 2

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
class FrmPagoEfectivo(tk.Toplevel):
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

        self.title("Pago en efectivo")
        self.geometry("560x390")
        self.resizable(False, False)
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
            text="Cobro en efectivo",
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
            text="Este formulario registrará el cobro en efectivo y marcará la operación como pagada.",
            font=("Arial", 9),
            bg="white",
            fg="#6b7280",
            wraplength=460,
            justify="left"
        )
        self.lblInfo.grid(row=5, column=0, columnspan=2, sticky="w", padx=14, pady=(10, 14))

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

        self.btnGuardar = tk.Button(
            lofrmBotones,
            text="Registrar pago",
            font=("Arial", 10, "bold"),
            bg="#059669",
            fg="white",
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            command=self.savePayment
        )
        self.btnGuardar.pack(side="right", padx=(0, 8))

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

    def savePayment(self):
        try:
            if self.tnMonto <= 0:
                raise ValueError("El monto para pago en efectivo debe ser mayor a 0.")

            llOk = messagebox.askyesno(
                "Confirmar cobro",
                f"¿Deseas registrar el cobro en efectivo por Bs {self.tnMonto:.2f}?",
                parent=self
            )
            if not llOk:
                return

            self.btnGuardar.config(state="disabled")

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
                f"Cobro registrado correctamente.\nNro. Pago: {txResultado['Pago']}",
                parent=self
            )
            self.destroy()

        except Exception as toError:
            self.btnGuardar.config(state="normal")
            messagebox.showerror(
                "Error",
                f"No se pudo registrar el cobro en efectivo.\n{str(toError)}",
                parent=self
            )