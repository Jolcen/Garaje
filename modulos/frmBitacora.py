import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from database.db import getConnection


class AuditLogView:
    def __init__(self, toParent, txUsuarioData):
        self.toParent = toParent
        self.txUsuarioData = txUsuarioData

        self.lotxtBusqueda = None
        self.lotxtFechaDesde = None
        self.lotxtFechaHasta = None
        self.logrdBitacora = None

    def build(self):
        if self.txUsuarioData["Rol"] != "admin":
            self.buildAccessDenied()
            return

        self.buildFilters()
        self.buildTable()
        self.loadLogs()

    def buildAccessDenied(self):
        lofrmContainer = tk.Frame(self.toParent, bg="white")
        lofrmContainer.pack(fill="both", expand=True)

        lolblTitulo = tk.Label(
            lofrmContainer,
            text="Acceso restringido",
            font=("Arial", 18, "bold"),
            bg="white",
            fg="#b91c1c"
        )
        lolblTitulo.pack(pady=(80, 10))

        lolblMensaje = tk.Label(
            lofrmContainer,
            text="Solo el administrador puede ver la bitácora.",
            font=("Arial", 11),
            bg="white",
            fg="#4b5563"
        )
        lolblMensaje.pack()

    def buildFilters(self):
        lofrmFiltros = tk.Frame(self.toParent, bg="white")
        lofrmFiltros.pack(fill="x", padx=15, pady=15)

        lolblBuscar = tk.Label(
            lofrmFiltros,
            text="Buscar:",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#111827"
        )
        lolblBuscar.grid(row=0, column=0, padx=(5, 5), pady=5, sticky="w")

        self.lotxtBusqueda = tk.Entry(lofrmFiltros, font=("Arial", 10), width=24)
        self.lotxtBusqueda.grid(row=0, column=1, padx=(0, 12), pady=5, sticky="w")
        self.lotxtBusqueda.bind("<KeyRelease>", lambda loEvent: self.loadLogs())

        lolblFechaDesde = tk.Label(
            lofrmFiltros,
            text="Desde (YYYY-MM-DD):",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#111827"
        )
        lolblFechaDesde.grid(row=0, column=2, padx=(5, 5), pady=5, sticky="w")

        self.lotxtFechaDesde = tk.Entry(lofrmFiltros, font=("Arial", 10), width=14)
        self.lotxtFechaDesde.grid(row=0, column=3, padx=(0, 12), pady=5, sticky="w")

        lolblFechaHasta = tk.Label(
            lofrmFiltros,
            text="Hasta (YYYY-MM-DD):",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#111827"
        )
        lolblFechaHasta.grid(row=0, column=4, padx=(5, 5), pady=5, sticky="w")

        self.lotxtFechaHasta = tk.Entry(lofrmFiltros, font=("Arial", 10), width=14)
        self.lotxtFechaHasta.grid(row=0, column=5, padx=(0, 12), pady=5, sticky="w")

        locmdBuscar = tk.Button(
            lofrmFiltros,
            text="Buscar",
            font=("Arial", 10, "bold"),
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            bd=0,
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=self.loadLogs
        )
        locmdBuscar.grid(row=0, column=6, padx=8, pady=5)

        locmdLimpiar = tk.Button(
            lofrmFiltros,
            text="Limpiar",
            font=("Arial", 10, "bold"),
            bg="#6b7280",
            fg="white",
            activebackground="#4b5563",
            activeforeground="white",
            bd=0,
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=self.clearFilters
        )
        locmdLimpiar.grid(row=0, column=7, padx=8, pady=5)

    def buildTable(self):
        lofrmTabla = tk.Frame(self.toParent, bg="white")
        lofrmTabla.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        taColumnas = (
            "Bitacora",
            "UsuarioNombre",
            "Accion",
            "TablaAfectada",
            "RegistroAfectado",
            "Descripcion",
            "FechaEvento"
        )

        self.logrdBitacora = ttk.Treeview(
            lofrmTabla,
            columns=taColumnas,
            show="headings",
            height=18
        )

        self.logrdBitacora.heading("Bitacora", text="ID")
        self.logrdBitacora.heading("UsuarioNombre", text="Usuario")
        self.logrdBitacora.heading("Accion", text="Acción")
        self.logrdBitacora.heading("TablaAfectada", text="Tabla")
        self.logrdBitacora.heading("RegistroAfectado", text="Registro")
        self.logrdBitacora.heading("Descripcion", text="Descripción")
        self.logrdBitacora.heading("FechaEvento", text="Fecha")

        self.logrdBitacora.column("Bitacora", width=55, anchor="center", stretch=False)
        self.logrdBitacora.column("UsuarioNombre", width=150, anchor="w", stretch=False)
        self.logrdBitacora.column("Accion", width=180, anchor="center", stretch=False)
        self.logrdBitacora.column("TablaAfectada", width=110, anchor="center", stretch=False)
        self.logrdBitacora.column("RegistroAfectado", width=80, anchor="center", stretch=False)
        self.logrdBitacora.column("Descripcion", width=420, anchor="w", stretch=False)
        self.logrdBitacora.column("FechaEvento", width=160, anchor="center", stretch=False)

        loscrVertical = ttk.Scrollbar(
            lofrmTabla,
            orient="vertical",
            command=self.logrdBitacora.yview
        )
        loscrHorizontal = ttk.Scrollbar(
            lofrmTabla,
            orient="horizontal",
            command=self.logrdBitacora.xview
        )

        self.logrdBitacora.configure(
            yscrollcommand=loscrVertical.set,
            xscrollcommand=loscrHorizontal.set
        )

        self.logrdBitacora.grid(row=0, column=0, sticky="nsew")
        loscrVertical.grid(row=0, column=1, sticky="ns")
        loscrHorizontal.grid(row=1, column=0, sticky="ew")

        lofrmTabla.grid_rowconfigure(0, weight=1)
        lofrmTabla.grid_columnconfigure(0, weight=1)

    def clearFilters(self):
        self.lotxtBusqueda.delete(0, tk.END)
        self.lotxtFechaDesde.delete(0, tk.END)
        self.lotxtFechaHasta.delete(0, tk.END)
        self.loadLogs()

    def validateDate(self, tcValor):
        if not tcValor:
            return True

        try:
            datetime.strptime(tcValor, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def loadLogs(self):
        for toItem in self.logrdBitacora.get_children():
            self.logrdBitacora.delete(toItem)

        lcBusqueda = self.lotxtBusqueda.get().strip().upper() if self.lotxtBusqueda else ""
        lcFechaDesde = self.lotxtFechaDesde.get().strip() if self.lotxtFechaDesde else ""
        lcFechaHasta = self.lotxtFechaHasta.get().strip() if self.lotxtFechaHasta else ""

        if not self.validateDate(lcFechaDesde):
            messagebox.showwarning(
                "Fecha inválida",
                "La fecha 'Desde' debe estar en formato YYYY-MM-DD."
            )
            return

        if not self.validateDate(lcFechaHasta):
            messagebox.showwarning(
                "Fecha inválida",
                "La fecha 'Hasta' debe estar en formato YYYY-MM-DD."
            )
            return

        if lcFechaDesde and lcFechaHasta and lcFechaDesde > lcFechaHasta:
            messagebox.showwarning(
                "Rango inválido",
                "La fecha 'Desde' no puede ser mayor que la fecha 'Hasta'."
            )
            return

        loConn = getConnection()
        loCursor = loConn.cursor()

        lcQuery = """
            SELECT
                B.Bitacora,
                U.Nombre AS UsuarioNombre,
                B.Accion,
                B.TablaAfectada,
                B.RegistroAfectado,
                B.Descripcion,
                B.FechaEvento
            FROM BITACORA B
            LEFT JOIN USUARIO U ON B.Usuario = U.Usuario
            WHERE 1 = 1
        """
        laParams = []

        if lcBusqueda:
            lcLikeValue = f"%{lcBusqueda}%"
            lcQuery += """
                AND (
                    UPPER(IFNULL(U.Nombre, '')) LIKE ?
                    OR UPPER(IFNULL(B.Accion, '')) LIKE ?
                    OR UPPER(IFNULL(B.TablaAfectada, '')) LIKE ?
                    OR UPPER(IFNULL(B.Descripcion, '')) LIKE ?
                )
            """
            laParams.extend([lcLikeValue, lcLikeValue, lcLikeValue, lcLikeValue])

        if lcFechaDesde:
            lcQuery += " AND date(B.FechaEvento) >= date(?) "
            laParams.append(lcFechaDesde)

        if lcFechaHasta:
            lcQuery += " AND date(B.FechaEvento) <= date(?) "
            laParams.append(lcFechaHasta)

        lcQuery += " ORDER BY B.FechaEvento DESC, B.Bitacora DESC "

        loCursor.execute(lcQuery, laParams)
        laRows = loCursor.fetchall()
        loConn.close()

        for taRow in laRows:
            self.logrdBitacora.insert(
                "",
                "end",
                values=(
                    taRow["Bitacora"],
                    taRow["UsuarioNombre"] if taRow["UsuarioNombre"] else "-",
                    taRow["Accion"] if taRow["Accion"] else "",
                    taRow["TablaAfectada"] if taRow["TablaAfectada"] else "",
                    taRow["RegistroAfectado"] if taRow["RegistroAfectado"] is not None else "",
                    taRow["Descripcion"] if taRow["Descripcion"] else "",
                    taRow["FechaEvento"] if taRow["FechaEvento"] else ""
                )
            )