import tkinter as tk
from tkinter import messagebox

from modulos.frmOperaciones import OperationsView
from modulos.frmVehiculosClientes import VehiclesCustomersView
from modulos.frmTarifas import RatesView
from modulos.frmServicios import ServicesView
from modulos.frmReportes import ReportsView
from modulos.frmUsuarios import UsersView
from modulos.frmBitacora import AuditLogView
from modulos.frmContratos import ContractsView


class DashboardWindow:
    def __init__(self, txUsuarioData):
        self.txUsuarioData = txUsuarioData or {}

        self.loRoot = tk.Tk()
        self.loRoot.title("Sistema de Garaje")
        self.loRoot.geometry("1366x768")
        self.loRoot.minsize(1200, 700)
        self.loRoot.configure(bg="#facc15")

        try:
            self.loRoot.state("zoomed")
        except Exception:
            pass

        self.lofrmContenido = None
        self.lolblTituloModulo = None
        self.lxBotonesSidebar = {}

        self.buildUi()
        self.showModule("Operaciones")

        self.loRoot.protocol("WM_DELETE_WINDOW", self.confirmExit)

    def buildUi(self):
        self.loRoot.grid_rowconfigure(1, weight=1)
        self.loRoot.grid_columnconfigure(1, weight=1)

        self.buildTopbar()
        self.buildSidebar()
        self.buildContentArea()

    def buildTopbar(self):
        lofrmTopbar = tk.Frame(self.loRoot, bg="#1e3a8a", height=55)
        lofrmTopbar.grid(row=0, column=0, columnspan=2, sticky="nsew")
        lofrmTopbar.grid_propagate(False)

        lcNombreUsuario = self.txUsuarioData.get("Nombre", "Usuario")
        lcRolUsuario = self.txUsuarioData.get("Rol", "empleado")

        lolblTituloSistema = tk.Label(
            lofrmTopbar,
            text="Sistema de Garaje",
            bg="#1e3a8a",
            fg="white",
            font=("Arial", 16, "bold")
        )
        lolblTituloSistema.pack(side="left", padx=20)

        lolblUsuarioInfo = tk.Label(
            lofrmTopbar,
            text=f"{lcNombreUsuario} | Rol: {lcRolUsuario}",
            bg="#1e3a8a",
            fg="white",
            font=("Arial", 11)
        )
        lolblUsuarioInfo.pack(side="right", padx=20)

    def buildSidebar(self):
        lofrmSidebar = tk.Frame(self.loRoot, bg="#facc15", width=230)
        lofrmSidebar.grid(row=1, column=0, sticky="nsew")
        lofrmSidebar.grid_propagate(False)

        lolblMenuTitulo = tk.Label(
            lofrmSidebar,
            text="MENÚ",
            bg="#facc15",
            fg="#1e3a8a",
            font=("Arial", 13, "bold")
        )
        lolblMenuTitulo.pack(pady=(20, 15))

        lcRolUsuario = self.txUsuarioData.get("Rol", "empleado")

        laBotones = [
            ("Operaciones", lambda: self.showModule("Operaciones")),
            ("Vehículos / Clientes", lambda: self.showModule("Vehículos / Clientes")),
            ("Contratos", lambda: self.showModule("Contratos")),
            ("Reportes", lambda: self.showModule("Reportes")),
        ]

        if lcRolUsuario == "admin":
            laBotones.extend([
                ("Tarifas", lambda: self.showModule("Tarifas")),
                ("Servicios", lambda: self.showModule("Servicios")),
                ("Usuarios", lambda: self.showModule("Usuarios")),
                ("Bitácora", lambda: self.showModule("Bitácora")),
            ])

        for tcTexto, tfComando in laBotones:
            locmdModulo = tk.Button(
                lofrmSidebar,
                text=tcTexto,
                command=tfComando,
                bg="#1e3a8a",
                fg="white",
                activebackground="#2563eb",
                activeforeground="white",
                font=("Arial", 11, "bold"),
                bd=0,
                relief="flat",
                width=22,
                height=2,
                cursor="hand2"
            )
            locmdModulo.pack(pady=5)
            self.lxBotonesSidebar[tcTexto] = locmdModulo

        locmdCerrarSesion = tk.Button(
            lofrmSidebar,
            text="Cerrar sesión",
            command=self.logout,
            bg="#dc2626",
            fg="white",
            activebackground="#b91c1c",
            activeforeground="white",
            font=("Arial", 11, "bold"),
            bd=0,
            relief="flat",
            width=22,
            height=2,
            cursor="hand2"
        )
        locmdCerrarSesion.pack(side="bottom", pady=20)

    def buildContentArea(self):
        lofrmContainer = tk.Frame(self.loRoot, bg="#fde68a")
        lofrmContainer.grid(row=1, column=1, sticky="nsew")
        lofrmContainer.grid_rowconfigure(1, weight=1)
        lofrmContainer.grid_columnconfigure(0, weight=1)

        lofrmHeader = tk.Frame(lofrmContainer, bg="#fbbf24", height=50)
        lofrmHeader.grid(row=0, column=0, sticky="nsew")
        lofrmHeader.grid_propagate(False)

        self.lolblTituloModulo = tk.Label(
            lofrmHeader,
            text="",
            bg="#fbbf24",
            fg="#1e3a8a",
            font=("Arial", 14, "bold")
        )
        self.lolblTituloModulo.pack(side="left", padx=20, pady=10)

        self.lofrmContenido = tk.Frame(
            lofrmContainer,
            bg="white",
            bd=1,
            relief="solid"
        )
        self.lofrmContenido.grid(row=1, column=0, sticky="nsew", padx=15, pady=15)

        self.lofrmContenido.grid_rowconfigure(0, weight=1)
        self.lofrmContenido.grid_columnconfigure(0, weight=1)

    def clearContent(self):
        for loWidget in self.lofrmContenido.winfo_children():
            loWidget.destroy()

    def updateActiveButton(self, tcNombreModulo):
        for tcNombreBoton, loBoton in self.lxBotonesSidebar.items():
            if tcNombreBoton == tcNombreModulo:
                loBoton.configure(bg="#2563eb")
            else:
                loBoton.configure(bg="#1e3a8a")

    def showModule(self, tcNombreModulo):
        self.clearContent()
        self.lolblTituloModulo.config(text=tcNombreModulo)
        self.updateActiveButton(tcNombreModulo)

        loVista = None

        if tcNombreModulo == "Operaciones":
            loVista = OperationsView(self.lofrmContenido, self.txUsuarioData)
        elif tcNombreModulo == "Vehículos / Clientes":
            loVista = VehiclesCustomersView(self.lofrmContenido, self.txUsuarioData)
        elif tcNombreModulo == "Contratos":
            loVista = ContractsView(self.lofrmContenido, self.txUsuarioData)
        elif tcNombreModulo == "Tarifas":
            loVista = RatesView(self.lofrmContenido, self.txUsuarioData)
        elif tcNombreModulo == "Servicios":
            loVista = ServicesView(self.lofrmContenido, self.txUsuarioData)
        elif tcNombreModulo == "Reportes":
            loVista = ReportsView(self.lofrmContenido)
        elif tcNombreModulo == "Usuarios":
            loVista = UsersView(self.lofrmContenido, self.txUsuarioData)
        elif tcNombreModulo == "Bitácora":
            loVista = AuditLogView(self.lofrmContenido, self.txUsuarioData)

        if loVista is None:
            return

        if hasattr(loVista, "build"):
            loVista.build()
        else:
            loVista.pack(fill="both", expand=True)

    def logout(self):
        llConfirmar = messagebox.askyesno(
            "Cerrar sesión",
            "¿Desea cerrar sesión?"
        )
        if not llConfirmar:
            return

        self.loRoot.destroy()

        from modulos.frmLogin import LoginWindow
        loLogin = LoginWindow()
        loLogin.run()

    def confirmExit(self):
        llConfirmar = messagebox.askyesno(
            "Salir",
            "¿Desea cerrar el sistema?"
        )
        if llConfirmar:
            self.loRoot.destroy()

    def run(self):
        self.loRoot.mainloop()