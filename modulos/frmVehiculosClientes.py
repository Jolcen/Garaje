import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from database.db import getConnection


gnEstadoGeneralInactivo = 0
gnEstadoGeneralActivo = 1

gnEstadoOperacionAbierta = 1
gnEstadoContratoActivo = 1


def obtenerUsuarioActualId(txUsuarioData):
    if not txUsuarioData:
        return 0
    return txUsuarioData.get("Usuario", 0)


def limpiarPlacaParaBusqueda(tcPlaca):
    return tcPlaca.replace(" ", "").replace("-", "").upper().strip()


def nombreClienteCompleto(tcNombres, tcApellidos):
    lcNombres = (tcNombres or "").strip()
    lcApellidos = (tcApellidos or "").strip()
    return f"{lcNombres} {lcApellidos}".strip()


def textoOVacio(txValor):
    return txValor if txValor else ""


def getFechaHoraActualTexto():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class VehiclesCustomersView:
    def __init__(self, toParent, txUsuarioData):
        self.toParent = toParent
        self.txUsuarioData = txUsuarioData

        self.logrdVehiculosClientes = None
        self.lotxtBusqueda = None

    def build(self):
        self.buildHeader()
        self.buildTable()
        self.loadRecords()

    def buildHeader(self):
        lofrmHeader = tk.Frame(self.toParent, bg="white")
        lofrmHeader.pack(fill="x", padx=15, pady=15)

        lolblBuscar = tk.Label(
            lofrmHeader,
            text="Buscar:",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#111827"
        )
        lolblBuscar.pack(side="left", padx=(0, 8))

        self.lotxtBusqueda = tk.Entry(lofrmHeader, font=("Arial", 11), width=30)
        self.lotxtBusqueda.pack(side="left", padx=(0, 8))
        self.lotxtBusqueda.bind("<KeyRelease>", lambda toEvent: self.loadRecords())

        locmdBuscar = tk.Button(
            lofrmHeader,
            text="Buscar",
            font=("Arial", 10, "bold"),
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            bd=0,
            relief="flat",
            padx=15,
            pady=6,
            cursor="hand2",
            command=self.loadRecords
        )
        locmdBuscar.pack(side="left", padx=(0, 10))

        locmdNuevoRegistro = tk.Button(
            lofrmHeader,
            text="Nuevo registro",
            font=("Arial", 10, "bold"),
            bg="#16a34a",
            fg="white",
            activebackground="#15803d",
            activeforeground="white",
            bd=0,
            relief="flat",
            padx=15,
            pady=6,
            cursor="hand2",
            command=self.openNewWindow
        )
        locmdNuevoRegistro.pack(side="right")

    def buildTable(self):
        lofrmTabla = tk.Frame(self.toParent, bg="white")
        lofrmTabla.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        taColumnas = (
            "Vehiculo",
            "Placa",
            "TipoVehiculo",
            "Marca",
            "Color",
            "Cliente",
            "Telefono",
            "Documento",
            "Acciones"
        )

        self.logrdVehiculosClientes = ttk.Treeview(
            lofrmTabla,
            columns=taColumnas,
            show="headings",
            height=18
        )

        self.logrdVehiculosClientes.heading("Vehiculo", text="ID")
        self.logrdVehiculosClientes.heading("Placa", text="Placa")
        self.logrdVehiculosClientes.heading("TipoVehiculo", text="Tipo")
        self.logrdVehiculosClientes.heading("Marca", text="Marca")
        self.logrdVehiculosClientes.heading("Color", text="Color")
        self.logrdVehiculosClientes.heading("Cliente", text="Cliente")
        self.logrdVehiculosClientes.heading("Telefono", text="Teléfono")
        self.logrdVehiculosClientes.heading("Documento", text="Documento")
        self.logrdVehiculosClientes.heading("Acciones", text="Acciones")

        self.logrdVehiculosClientes.column("Vehiculo", width=55, anchor="center", stretch=False)
        self.logrdVehiculosClientes.column("Placa", width=110, anchor="center", stretch=False)
        self.logrdVehiculosClientes.column("TipoVehiculo", width=90, anchor="center", stretch=False)
        self.logrdVehiculosClientes.column("Marca", width=100, anchor="center", stretch=False)
        self.logrdVehiculosClientes.column("Color", width=90, anchor="center", stretch=False)
        self.logrdVehiculosClientes.column("Cliente", width=180, anchor="w", stretch=False)
        self.logrdVehiculosClientes.column("Telefono", width=110, anchor="center", stretch=False)
        self.logrdVehiculosClientes.column("Documento", width=130, anchor="center", stretch=False)
        self.logrdVehiculosClientes.column("Acciones", width=100, anchor="center", stretch=False)

        loscrVertical = ttk.Scrollbar(
            lofrmTabla,
            orient="vertical",
            command=self.logrdVehiculosClientes.yview
        )
        loscrHorizontal = ttk.Scrollbar(
            lofrmTabla,
            orient="horizontal",
            command=self.logrdVehiculosClientes.xview
        )

        self.logrdVehiculosClientes.configure(
            yscrollcommand=loscrVertical.set,
            xscrollcommand=loscrHorizontal.set
        )

        self.logrdVehiculosClientes.grid(row=0, column=0, sticky="nsew")
        loscrVertical.grid(row=0, column=1, sticky="ns")
        loscrHorizontal.grid(row=1, column=0, sticky="ew")

        lofrmTabla.grid_rowconfigure(0, weight=1)
        lofrmTabla.grid_columnconfigure(0, weight=1)

        self.logrdVehiculosClientes.bind("<Double-1>", self.onDoubleClick)

    def loadRecords(self):
        for toItem in self.logrdVehiculosClientes.get_children():
            self.logrdVehiculosClientes.delete(toItem)

        lcBusqueda = self.lotxtBusqueda.get().strip().upper() if self.lotxtBusqueda else ""

        loConn = getConnection()
        loCursor = loConn.cursor()

        lcQuery = """
            SELECT
                V.Vehiculo,
                V.NumeroPlaca,
                V.LetraPlaca,
                V.TipoVehiculo,
                V.Marca,
                V.Color,
                C.Cliente,
                C.Nombres,
                C.Apellidos,
                C.Telefono,
                C.DocumentoIdentidad,
                C.ComplementoDocumento
            FROM VEHICULO V
            LEFT JOIN CLIENTE C ON V.Cliente = C.Cliente
            WHERE V.Estado = ?
        """
        laParams = [gnEstadoGeneralActivo]

        if lcBusqueda:
            lcLikeValue = f"%{lcBusqueda}%"
            lcLikePlaca = f"%{limpiarPlacaParaBusqueda(lcBusqueda)}%"

            lcQuery += """
                AND (
                    REPLACE(
                        REPLACE(
                            UPPER(IFNULL(V.NumeroPlaca, '') || IFNULL(V.LetraPlaca, '')),
                            ' ',
                            ''
                        ),
                        '-',
                        ''
                    ) LIKE ?
                    OR UPPER(IFNULL(V.TipoVehiculo, '')) LIKE ?
                    OR UPPER(IFNULL(V.Marca, '')) LIKE ?
                    OR UPPER(IFNULL(V.Color, '')) LIKE ?
                    OR UPPER(IFNULL(C.Nombres, '')) LIKE ?
                    OR UPPER(IFNULL(C.Apellidos, '')) LIKE ?
                    OR IFNULL(C.Telefono, '') LIKE ?
                    OR UPPER(IFNULL(C.DocumentoIdentidad, '')) LIKE ?
                )
            """
            laParams.extend([
                lcLikePlaca,
                lcLikeValue,
                lcLikeValue,
                lcLikeValue,
                lcLikeValue,
                lcLikeValue,
                f"%{lcBusqueda}%",
                lcLikeValue
            ])

        lcQuery += " ORDER BY V.Vehiculo ASC "

        loCursor.execute(lcQuery, laParams)
        laRows = loCursor.fetchall()
        loConn.close()

        for toRow in laRows:
            lcCliente = nombreClienteCompleto(toRow["Nombres"], toRow["Apellidos"])
            lcPlaca = f"{toRow['NumeroPlaca']} {toRow['LetraPlaca']}".strip()

            lcDocumento = textoOVacio(toRow["DocumentoIdentidad"])
            if toRow["ComplementoDocumento"]:
                lcDocumento = f"{lcDocumento} {toRow['ComplementoDocumento']}".strip()

            self.logrdVehiculosClientes.insert(
                "",
                "end",
                values=(
                    toRow["Vehiculo"],
                    lcPlaca,
                    toRow["TipoVehiculo"],
                    textoOVacio(toRow["Marca"]),
                    textoOVacio(toRow["Color"]),
                    lcCliente,
                    textoOVacio(toRow["Telefono"]),
                    lcDocumento,
                    "Doble clic"
                )
            )

    def onDoubleClick(self, toEvent):
        taSeleccionado = self.logrdVehiculosClientes.selection()
        if not taSeleccionado:
            return

        taValores = self.logrdVehiculosClientes.item(taSeleccionado[0], "values")
        if not taValores:
            return

        tnVehiculo = taValores[0]
        lcPlaca = taValores[1]

        loWindowAcciones = tk.Toplevel(self.toParent)
        loWindowAcciones.title("Acciones")
        loWindowAcciones.geometry("340x250")
        loWindowAcciones.resizable(False, False)
        loWindowAcciones.configure(bg="white")
        loWindowAcciones.grab_set()

        lolblTitulo = tk.Label(
            loWindowAcciones,
            text=f"Vehículo: {lcPlaca}",
            font=("Arial", 14, "bold"),
            bg="white",
            fg="#111827"
        )
        lolblTitulo.pack(pady=(20, 14))

        locmdEditar = tk.Button(
            loWindowAcciones,
            text="Editar",
            font=("Arial", 11, "bold"),
            width=18,
            bg="#f59e0b",
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            command=lambda: self.confirmEdit(tnVehiculo, loWindowAcciones)
        )
        locmdEditar.pack(pady=8)

        locmdEliminar = tk.Button(
            loWindowAcciones,
            text="Eliminar",
            font=("Arial", 11, "bold"),
            width=18,
            bg="#dc2626",
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            command=lambda: self.deleteRecord(tnVehiculo, loWindowAcciones)
        )
        locmdEliminar.pack(pady=8)

        locmdCerrar = tk.Button(
            loWindowAcciones,
            text="Cerrar",
            font=("Arial", 11, "bold"),
            width=18,
            bg="#6b7280",
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            command=loWindowAcciones.destroy
        )
        locmdCerrar.pack(pady=8)

    def confirmEdit(self, tnVehiculo, loWindowAcciones=None):
        llConfirmado = messagebox.askyesno(
            "Confirmar edición",
            "¿Desea editar este registro?"
        )
        if not llConfirmado:
            return

        self.editRecord(tnVehiculo, loWindowAcciones)

    def openNewWindow(self):
        VehicleCustomerFormWindow(self, self.txUsuarioData)

    def editRecord(self, tnVehiculo, loWindowAcciones=None):
        if loWindowAcciones:
            loWindowAcciones.destroy()
        VehicleCustomerFormWindow(self, self.txUsuarioData, tnVehiculo=tnVehiculo)

    def deleteRecord(self, tnVehiculo, loWindowAcciones=None):
        llConfirmado = messagebox.askyesno(
            "Confirmar eliminación",
            "¿Está seguro de eliminar este registro?\n\nEsta acción no se puede deshacer."
        )
        if not llConfirmado:
            return

        loConn = getConnection()
        loCursor = loConn.cursor()

        try:
            loCursor.execute("""
                SELECT NumeroPlaca, LetraPlaca, Cliente
                FROM VEHICULO
                WHERE Vehiculo = ? AND Estado = ?
            """, (tnVehiculo, gnEstadoGeneralActivo))
            toRow = loCursor.fetchone()

            if not toRow:
                messagebox.showerror("Error", "No se encontró el vehículo.")
                return

            lcPlaca = f"{toRow['NumeroPlaca']} {toRow['LetraPlaca']}".strip()
            tnCliente = toRow["Cliente"]

            loCursor.execute("""
                SELECT COUNT(*)
                FROM OPERACION
                WHERE Vehiculo = ? AND Estado = ?
            """, (tnVehiculo, gnEstadoOperacionAbierta))
            lnOperacionesActivas = loCursor.fetchone()[0]

            if lnOperacionesActivas > 0:
                messagebox.showwarning(
                    "No permitido",
                    "No se puede eliminar el vehículo porque tiene operaciones activas."
                )
                return

            loCursor.execute("""
                SELECT COUNT(*)
                FROM CONTRATO
                WHERE Vehiculo = ? AND Estado = ?
            """, (tnVehiculo, gnEstadoContratoActivo))
            lnContratosActivos = loCursor.fetchone()[0]

            if lnContratosActivos > 0:
                messagebox.showwarning(
                    "No permitido",
                    "No se puede eliminar el vehículo porque tiene contratos activos."
                )
                return

            tnUsr = obtenerUsuarioActualId(self.txUsuarioData)

            loCursor.execute("""
                UPDATE VEHICULO
                SET
                    Estado = ?,
                    Cliente = NULL,
                    Usr = ?,
                    UsrFecha = date('now','localtime'),
                    UsrHora = time('now','localtime'),
                    FechaModificacion = datetime('now','localtime')
                WHERE Vehiculo = ?
            """, (gnEstadoGeneralInactivo, tnUsr, tnVehiculo))

            if tnCliente:
                loCursor.execute("""
                    SELECT COUNT(*)
                    FROM VEHICULO
                    WHERE Cliente = ? AND Estado = ?
                """, (tnCliente, gnEstadoGeneralActivo))
                lnVehiculosActivosCliente = loCursor.fetchone()[0]

                loCursor.execute("""
                    SELECT COUNT(*)
                    FROM CONTRATO
                    WHERE Cliente = ? AND Estado = ?
                """, (tnCliente, gnEstadoContratoActivo))
                lnContratosActivosCliente = loCursor.fetchone()[0]

                if lnVehiculosActivosCliente == 0 and lnContratosActivosCliente == 0:
                    loCursor.execute("""
                        UPDATE CLIENTE
                        SET
                            Estado = ?,
                            Usr = ?,
                            UsrFecha = date('now','localtime'),
                            UsrHora = time('now','localtime'),
                            FechaModificacion = datetime('now','localtime')
                        WHERE Cliente = ?
                    """, (gnEstadoGeneralInactivo, tnUsr, tnCliente))

            loCursor.execute("""
                INSERT INTO BITACORA (
                    Usuario,
                    Accion,
                    TablaAfectada,
                    RegistroAfectado,
                    Descripcion,
                    FechaEvento,
                    Usr,
                    UsrFecha,
                    UsrHora,
                    FechaCreacion,
                    FechaModificacion
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?,
                    ?,
                    date('now','localtime'),
                    time('now','localtime'),
                    datetime('now','localtime'),
                    datetime('now','localtime')
                )
            """, (
                tnUsr,
                "ELIMINAR_VEHICULO_CLIENTE",
                "VEHICULO",
                tnVehiculo,
                f"Se inactivó el vehículo '{lcPlaca}'",
                getFechaHoraActualTexto(),
                tnUsr
            ))

            loConn.commit()

            if loWindowAcciones:
                loWindowAcciones.destroy()

            messagebox.showinfo("Eliminado", "Registro eliminado correctamente.")
            self.loadRecords()

        except Exception as toError:
            loConn.rollback()
            messagebox.showerror("Error", f"No se pudo eliminar el registro.\n{str(toError)}")

        finally:
            loConn.close()


class VehicleCustomerFormWindow:
    def __init__(self, toView, txUsuarioData, tnVehiculo=None):
        self.toView = toView
        self.txUsuarioData = txUsuarioData
        self.tnVehiculo = tnVehiculo

        self.loWindow = tk.Toplevel()
        self.loWindow.title("Nuevo vehículo / cliente" if tnVehiculo is None else "Editar vehículo / cliente")
        self.loWindow.geometry("620x590")
        self.loWindow.minsize(560, 540)
        self.loWindow.resizable(True, True)
        self.loWindow.configure(bg="white")
        self.loWindow.grab_set()

        self.lotxtPlacaNumero = None
        self.lotxtPlacaLetras = None
        self.lovTipoVehiculo = tk.StringVar(value="auto")
        self.lotxtMarca = None
        self.lotxtColor = None

        self.lotxtNombres = None
        self.lotxtApellidos = None
        self.lotxtTelefono = None
        self.lotxtDocumento = None
        self.lotxtComplementoDocumento = None

        self.tnClienteCargado = None

        self.buildUi()

        if self.tnVehiculo is not None:
            self.loadData()

    def buildScrollableForm(self):
        lofrmOuter = tk.Frame(self.loWindow, bg="white")
        lofrmOuter.pack(fill="both", expand=True, padx=10, pady=10)

        loCanvas = tk.Canvas(lofrmOuter, bg="white", highlightthickness=0)
        loscrVertical = ttk.Scrollbar(lofrmOuter, orient="vertical", command=loCanvas.yview)

        lofrmScrollable = tk.Frame(loCanvas, bg="white")

        lofrmScrollable.bind(
            "<Configure>",
            lambda toEvent: loCanvas.configure(scrollregion=loCanvas.bbox("all"))
        )

        toCanvasWindow = loCanvas.create_window((0, 0), window=lofrmScrollable, anchor="nw")

        def onCanvasConfigure(toEvent):
            loCanvas.itemconfig(toCanvasWindow, width=toEvent.width)

        loCanvas.bind("<Configure>", onCanvasConfigure)
        loCanvas.configure(yscrollcommand=loscrVertical.set)

        loCanvas.pack(side="left", fill="both", expand=True)
        loscrVertical.pack(side="right", fill="y")

        def onMouseWheel(toEvent):
            if loCanvas.winfo_exists():
                loCanvas.yview_scroll(int(-1 * (toEvent.delta / 120)), "units")

        def bindMouseWheel(toEvent=None):
            self.loWindow.bind_all("<MouseWheel>", onMouseWheel)

        def unbindMouseWheel(toEvent=None):
            self.loWindow.unbind_all("<MouseWheel>")

        loCanvas.bind("<Enter>", bindMouseWheel)
        loCanvas.bind("<Leave>", unbindMouseWheel)
        lofrmScrollable.bind("<Enter>", bindMouseWheel)
        lofrmScrollable.bind("<Leave>", unbindMouseWheel)

        def onDestroy(toEvent=None):
            try:
                self.loWindow.unbind_all("<MouseWheel>")
            except Exception:
                pass

        self.loWindow.bind("<Destroy>", onDestroy)

        return lofrmScrollable

    def buildUi(self):
        lofrmFormulario = self.buildScrollableForm()

        lcTitulo = "Nuevo vehículo / cliente" if self.tnVehiculo is None else "Editar vehículo / cliente"

        lolblTitulo = tk.Label(
            lofrmFormulario,
            text=lcTitulo,
            font=("Arial", 16, "bold"),
            bg="white",
            fg="#111827"
        )
        lolblTitulo.pack(pady=(10, 15))

        lofrmContenido = tk.Frame(lofrmFormulario, bg="white")
        lofrmContenido.pack(fill="both", expand=True, padx=20)

        lolblTituloVehiculo = tk.Label(
            lofrmContenido,
            text="Datos del vehículo",
            font=("Arial", 12, "bold"),
            bg="white",
            fg="#111827"
        )
        lolblTituloVehiculo.pack(anchor="w", pady=(5, 10))

        lolblPlaca = tk.Label(
            lofrmContenido,
            text="Placa *",
            font=("Arial", 11, "bold"),
            bg="white"
        )
        lolblPlaca.pack(anchor="w", pady=(0, 5))

        lofrmPlaca = tk.Frame(lofrmContenido, bg="white")
        lofrmPlaca.pack(fill="x", pady=(0, 4))

        tk.Label(lofrmPlaca, text="Número", font=("Arial", 10), bg="white").pack(side="left", padx=(0, 6))
        self.lotxtPlacaNumero = tk.Entry(lofrmPlaca, font=("Arial", 11), width=10)
        self.lotxtPlacaNumero.pack(side="left", padx=(0, 16))
        self.lotxtPlacaNumero.bind("<KeyRelease>", self.onlyNumbersPlate)

        tk.Label(lofrmPlaca, text="Letras", font=("Arial", 10), bg="white").pack(side="left", padx=(0, 6))
        self.lotxtPlacaLetras = tk.Entry(lofrmPlaca, font=("Arial", 11), width=8)
        self.lotxtPlacaLetras.pack(side="left")
        self.lotxtPlacaLetras.bind("<KeyRelease>", self.onlyLettersPlate)

        tk.Label(
            lofrmContenido,
            text="Formato referencial: 1023 ADV",
            font=("Arial", 9),
            bg="white",
            fg="#6b7280"
        ).pack(anchor="w", pady=(0, 12))

        lolblTipoVehiculo = tk.Label(
            lofrmContenido,
            text="Tipo de vehículo *",
            font=("Arial", 11, "bold"),
            bg="white"
        )
        lolblTipoVehiculo.pack(anchor="w", pady=(0, 5))

        lofrmTipoVehiculo = tk.Frame(lofrmContenido, bg="white")
        lofrmTipoVehiculo.pack(fill="x", pady=(0, 12))

        tkrdbAuto = tk.Radiobutton(
            lofrmTipoVehiculo,
            text="Auto",
            variable=self.lovTipoVehiculo,
            value="auto",
            bg="white",
            font=("Arial", 11)
        )
        tkrdbAuto.pack(side="left", padx=(0, 16))

        tkrdbMoto = tk.Radiobutton(
            lofrmTipoVehiculo,
            text="Moto",
            variable=self.lovTipoVehiculo,
            value="moto",
            bg="white",
            font=("Arial", 11)
        )
        tkrdbMoto.pack(side="left", padx=(0, 16))

        tk.Label(lofrmContenido, text="Marca", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.lotxtMarca = tk.Entry(lofrmContenido, font=("Arial", 11))
        self.lotxtMarca.pack(fill="x", pady=(0, 12))

        tk.Label(lofrmContenido, text="Color", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.lotxtColor = tk.Entry(lofrmContenido, font=("Arial", 11))
        self.lotxtColor.pack(fill="x", pady=(0, 18))

        lolblTituloCliente = tk.Label(
            lofrmContenido,
            text="Datos del cliente (opcionales)",
            font=("Arial", 12, "bold"),
            bg="white",
            fg="#111827"
        )
        lolblTituloCliente.pack(anchor="w", pady=(5, 10))

        tk.Label(lofrmContenido, text="Nombres", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.lotxtNombres = tk.Entry(lofrmContenido, font=("Arial", 11))
        self.lotxtNombres.pack(fill="x", pady=(0, 12))

        tk.Label(lofrmContenido, text="Apellidos", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.lotxtApellidos = tk.Entry(lofrmContenido, font=("Arial", 11))
        self.lotxtApellidos.pack(fill="x", pady=(0, 12))

        tk.Label(lofrmContenido, text="Teléfono", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.lotxtTelefono = tk.Entry(lofrmContenido, font=("Arial", 11))
        self.lotxtTelefono.pack(fill="x", pady=(0, 12))

        tk.Label(lofrmContenido, text="Documento identidad", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.lotxtDocumento = tk.Entry(lofrmContenido, font=("Arial", 11))
        self.lotxtDocumento.pack(fill="x", pady=(0, 12))

        tk.Label(lofrmContenido, text="Complemento documento", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.lotxtComplementoDocumento = tk.Entry(lofrmContenido, font=("Arial", 11))
        self.lotxtComplementoDocumento.pack(fill="x", pady=(0, 16))

        lofrmBotones = tk.Frame(lofrmFormulario, bg="white")
        lofrmBotones.pack(pady=15)

        locmdGuardar = tk.Button(
            lofrmBotones,
            text="Guardar",
            font=("Arial", 11, "bold"),
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            bd=0,
            relief="flat",
            padx=18,
            pady=8,
            cursor="hand2",
            command=self.confirmSave
        )
        locmdGuardar.grid(row=0, column=0, padx=10)

        locmdCancelar = tk.Button(
            lofrmBotones,
            text="Cancelar",
            font=("Arial", 11, "bold"),
            bg="#dc2626",
            fg="white",
            activebackground="#b91c1c",
            activeforeground="white",
            bd=0,
            relief="flat",
            padx=18,
            pady=8,
            cursor="hand2",
            command=self.loWindow.destroy
        )
        locmdCancelar.grid(row=0, column=1, padx=10)

    def onlyNumbersPlate(self, toEvent=None):
        lcValor = self.lotxtPlacaNumero.get()
        lcFiltrado = "".join(tcCaracter for tcCaracter in lcValor if tcCaracter.isdigit())[:4]
        if lcValor != lcFiltrado:
            self.lotxtPlacaNumero.delete(0, "end")
            self.lotxtPlacaNumero.insert(0, lcFiltrado)

    def onlyLettersPlate(self, toEvent=None):
        lcValor = self.lotxtPlacaLetras.get()
        lcFiltrado = "".join(tcCaracter for tcCaracter in lcValor if tcCaracter.isalpha()).upper()[:3]
        if lcValor != lcFiltrado:
            self.lotxtPlacaLetras.delete(0, "end")
            self.lotxtPlacaLetras.insert(0, lcFiltrado)

    def validatePlate(self):
        lcNumero = self.lotxtPlacaNumero.get().strip()
        lcLetras = self.lotxtPlacaLetras.get().strip().upper()

        if not lcNumero or not lcLetras:
            raise ValueError("La placa es obligatoria.")

        if not lcNumero.isdigit():
            raise ValueError("La parte numérica de la placa solo debe contener números.")

        if len(lcNumero) < 2 or len(lcNumero) > 4:
            raise ValueError("La parte numérica de la placa debe tener entre 2 y 4 dígitos.")

        if not lcLetras.isalpha():
            raise ValueError("La parte de letras de la placa solo debe contener letras.")

        if len(lcLetras) != 3:
            raise ValueError("La placa debe tener exactamente 3 letras.")

        return lcNumero, lcLetras

    def splitPlate(self, tcNumeroPlaca, tcLetraPlaca):
        return tcNumeroPlaca or "", tcLetraPlaca or ""

    def loadData(self):
        loConn = getConnection()
        loCursor = loConn.cursor()

        loCursor.execute("""
            SELECT
                V.NumeroPlaca,
                V.LetraPlaca,
                V.TipoVehiculo,
                V.Marca,
                V.Color,
                V.Cliente,
                C.Nombres,
                C.Apellidos,
                C.Telefono,
                C.DocumentoIdentidad,
                C.ComplementoDocumento
            FROM VEHICULO V
            LEFT JOIN CLIENTE C ON V.Cliente = C.Cliente
            WHERE V.Vehiculo = ? AND V.Estado = ?
        """, (self.tnVehiculo, gnEstadoGeneralActivo))
        toRow = loCursor.fetchone()
        loConn.close()

        if not toRow:
            messagebox.showerror("Error", "No se encontró el vehículo.")
            self.loWindow.destroy()
            return

        lcNumero, lcLetras = self.splitPlate(toRow["NumeroPlaca"], toRow["LetraPlaca"])
        self.lotxtPlacaNumero.insert(0, lcNumero)
        self.lotxtPlacaLetras.insert(0, lcLetras)

        self.lovTipoVehiculo.set(toRow["TipoVehiculo"] if toRow["TipoVehiculo"] else "auto")
        self.lotxtMarca.insert(0, toRow["Marca"] if toRow["Marca"] else "")
        self.lotxtColor.insert(0, toRow["Color"] if toRow["Color"] else "")

        self.tnClienteCargado = toRow["Cliente"]

        self.lotxtNombres.insert(0, toRow["Nombres"] if toRow["Nombres"] else "")
        self.lotxtApellidos.insert(0, toRow["Apellidos"] if toRow["Apellidos"] else "")
        self.lotxtTelefono.insert(0, toRow["Telefono"] if toRow["Telefono"] else "")
        self.lotxtDocumento.insert(0, toRow["DocumentoIdentidad"] if toRow["DocumentoIdentidad"] else "")
        self.lotxtComplementoDocumento.insert(0, toRow["ComplementoDocumento"] if toRow["ComplementoDocumento"] else "")

    def confirmSave(self):
        llConfirmado = messagebox.askyesno(
            "Confirmar guardado",
            "¿Desea guardar este registro?"
        )
        if not llConfirmado:
            return

        self.saveData()

    def saveData(self):
        try:
            lcNumeroPlaca, lcLetraPlaca = self.validatePlate()
        except ValueError as toError:
            messagebox.showwarning("Dato inválido", str(toError))
            return

        lcTipoVehiculo = self.lovTipoVehiculo.get()
        lcMarca = self.lotxtMarca.get().strip()
        lcColor = self.lotxtColor.get().strip()

        lcNombres = self.lotxtNombres.get().strip()
        lcApellidos = self.lotxtApellidos.get().strip()
        lcTelefono = self.lotxtTelefono.get().strip()
        lcDocumento = self.lotxtDocumento.get().strip()
        lcComplementoDocumento = self.lotxtComplementoDocumento.get().strip()

        loConn = getConnection()
        loCursor = loConn.cursor()

        try:
            lcPlacaNormalizada = limpiarPlacaParaBusqueda(f"{lcNumeroPlaca}{lcLetraPlaca}")
            tnUsr = obtenerUsuarioActualId(self.txUsuarioData)

            if self.tnVehiculo is None:
                loCursor.execute("""
                    SELECT COUNT(*)
                    FROM VEHICULO
                    WHERE REPLACE(
                        REPLACE(
                            UPPER(IFNULL(NumeroPlaca, '') || IFNULL(LetraPlaca, '')),
                            ' ',
                            ''
                        ),
                        '-',
                        ''
                    ) = ?
                    AND Estado = ?
                """, (lcPlacaNormalizada, gnEstadoGeneralActivo))
                if loCursor.fetchone()[0] > 0:
                    messagebox.showwarning("Placa existente", "Ya existe un vehículo con esa placa.")
                    return

                tnCliente = self.resolveCustomer(
                    loCursor,
                    lcNombres,
                    lcApellidos,
                    lcTelefono,
                    lcDocumento,
                    lcComplementoDocumento
                )

                loCursor.execute("""
                    INSERT INTO VEHICULO (
                        Cliente,
                        NumeroPlaca,
                        LetraPlaca,
                        TipoVehiculo,
                        Marca,
                        Color,
                        Estado,
                        Usr,
                        UsrFecha,
                        UsrHora,
                        FechaCreacion,
                        FechaModificacion
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?,
                        date('now','localtime'),
                        time('now','localtime'),
                        datetime('now','localtime'),
                        datetime('now','localtime')
                    )
                """, (
                    tnCliente,
                    lcNumeroPlaca,
                    lcLetraPlaca,
                    lcTipoVehiculo,
                    lcMarca if lcMarca else None,
                    lcColor if lcColor else None,
                    gnEstadoGeneralActivo,
                    tnUsr
                ))

                tnVehiculoNuevo = loCursor.lastrowid

                loCursor.execute("""
                    INSERT INTO BITACORA (
                        Usuario,
                        Accion,
                        TablaAfectada,
                        RegistroAfectado,
                        Descripcion,
                        FechaEvento,
                        Usr,
                        UsrFecha,
                        UsrHora,
                        FechaCreacion,
                        FechaModificacion
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?, ?,
                        date('now','localtime'),
                        time('now','localtime'),
                        datetime('now','localtime'),
                        datetime('now','localtime')
                    )
                """, (
                    tnUsr,
                    "CREAR_VEHICULO_CLIENTE",
                    "VEHICULO",
                    tnVehiculoNuevo,
                    f"Se creó el vehículo '{lcNumeroPlaca} {lcLetraPlaca}'",
                    getFechaHoraActualTexto(),
                    tnUsr
                ))
            else:
                loCursor.execute("""
                    SELECT COUNT(*)
                    FROM VEHICULO
                    WHERE REPLACE(
                        REPLACE(
                            UPPER(IFNULL(NumeroPlaca, '') || IFNULL(LetraPlaca, '')),
                            ' ',
                            ''
                        ),
                        '-',
                        ''
                    ) = ?
                    AND Vehiculo != ?
                    AND Estado = ?
                """, (lcPlacaNormalizada, self.tnVehiculo, gnEstadoGeneralActivo))
                if loCursor.fetchone()[0] > 0:
                    messagebox.showwarning("Placa existente", "Ya existe un vehículo con esa placa.")
                    return

                tnCliente = self.resolveCustomer(
                    loCursor,
                    lcNombres,
                    lcApellidos,
                    lcTelefono,
                    lcDocumento,
                    lcComplementoDocumento,
                    tnClienteExistente=self.tnClienteCargado
                )

                loCursor.execute("""
                    UPDATE VEHICULO
                    SET
                        Cliente = ?,
                        NumeroPlaca = ?,
                        LetraPlaca = ?,
                        TipoVehiculo = ?,
                        Marca = ?,
                        Color = ?,
                        Usr = ?,
                        UsrFecha = date('now','localtime'),
                        UsrHora = time('now','localtime'),
                        FechaModificacion = datetime('now','localtime')
                    WHERE Vehiculo = ?
                """, (
                    tnCliente,
                    lcNumeroPlaca,
                    lcLetraPlaca,
                    lcTipoVehiculo,
                    lcMarca if lcMarca else None,
                    lcColor if lcColor else None,
                    tnUsr,
                    self.tnVehiculo
                ))

                loCursor.execute("""
                    INSERT INTO BITACORA (
                        Usuario,
                        Accion,
                        TablaAfectada,
                        RegistroAfectado,
                        Descripcion,
                        FechaEvento,
                        Usr,
                        UsrFecha,
                        UsrHora,
                        FechaCreacion,
                        FechaModificacion
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?, ?,
                        date('now','localtime'),
                        time('now','localtime'),
                        datetime('now','localtime'),
                        datetime('now','localtime')
                    )
                """, (
                    tnUsr,
                    "EDITAR_VEHICULO_CLIENTE",
                    "VEHICULO",
                    self.tnVehiculo,
                    f"Se editó el vehículo '{lcNumeroPlaca} {lcLetraPlaca}'",
                    getFechaHoraActualTexto(),
                    tnUsr
                ))

            loConn.commit()
            messagebox.showinfo("Guardado", "Registro guardado correctamente.")
            self.toView.loadRecords()
            self.loWindow.destroy()

        except Exception as toError:
            loConn.rollback()
            messagebox.showerror("Error", f"No se pudo guardar el registro.\n{str(toError)}")

        finally:
            loConn.close()

    def resolveCustomer(
        self,
        loCursor,
        tcNombres,
        tcApellidos,
        tcTelefono,
        tcDocumento,
        tcComplementoDocumento,
        tnClienteExistente=None
    ):
        llTieneDatosCliente = any([
            tcNombres,
            tcApellidos,
            tcTelefono,
            tcDocumento,
            tcComplementoDocumento
        ])

        if not llTieneDatosCliente:
            return None

        tnUsr = obtenerUsuarioActualId(self.txUsuarioData)

        if tnClienteExistente:
            loCursor.execute("""
                UPDATE CLIENTE
                SET
                    Nombres = ?,
                    Apellidos = ?,
                    Telefono = ?,
                    DocumentoIdentidad = ?,
                    ComplementoDocumento = ?,
                    Estado = ?,
                    Usr = ?,
                    UsrFecha = date('now','localtime'),
                    UsrHora = time('now','localtime'),
                    FechaModificacion = datetime('now','localtime')
                WHERE Cliente = ?
            """, (
                tcNombres if tcNombres else None,
                tcApellidos if tcApellidos else None,
                tcTelefono if tcTelefono else None,
                tcDocumento if tcDocumento else None,
                tcComplementoDocumento if tcComplementoDocumento else None,
                gnEstadoGeneralActivo,
                tnUsr,
                tnClienteExistente
            ))
            return tnClienteExistente

        loCursor.execute("""
            INSERT INTO CLIENTE (
                Nombres,
                Apellidos,
                Telefono,
                DocumentoIdentidad,
                ComplementoDocumento,
                Estado,
                Usr,
                UsrFecha,
                UsrHora,
                FechaCreacion,
                FechaModificacion
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?,
                date('now','localtime'),
                time('now','localtime'),
                datetime('now','localtime'),
                datetime('now','localtime')
            )
        """, (
            tcNombres if tcNombres else None,
            tcApellidos if tcApellidos else None,
            tcTelefono if tcTelefono else None,
            tcDocumento if tcDocumento else None,
            tcComplementoDocumento if tcComplementoDocumento else None,
            gnEstadoGeneralActivo,
            tnUsr
        ))
        return loCursor.lastrowid

    def run(self):
        pass