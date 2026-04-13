import tkinter as tk
from tkinter import ttk, messagebox

from database.db import getConnection


gnRolAdministrador = 1

gnEstadoInactivo = 0
gnEstadoActivo = 1

gnTipoCobroHora = 1
gnTipoCobroDia = 2
gnTipoCobroMes = 3
gnTipoCobroNocturna = 4

gxEstadoTexto = {
    gnEstadoActivo: "Activa",
    gnEstadoInactivo: "Inactiva",
}

gxEstadoNumero = {
    "Activa": gnEstadoActivo,
    "Inactiva": gnEstadoInactivo,
}

gxTipoCobroTexto = {
    gnTipoCobroHora: "Hora",
    gnTipoCobroDia: "Día",
    gnTipoCobroMes: "Mes",
    gnTipoCobroNocturna: "Nocturna",
}

gxTipoCobroInv = {tcValor: tnClave for tnClave, tcValor in gxTipoCobroTexto.items()}


def obtenerUsuarioActualId(txUsuarioData):
    if not txUsuarioData:
        return 0
    return txUsuarioData.get("Usuario", 0)


def esHoraValida(tcHora):
    if not tcHora:
        return False

    partes = tcHora.split(":")
    if len(partes) != 2:
        return False

    try:
        horas = int(partes[0])
        minutos = int(partes[1])
    except ValueError:
        return False

    return 0 <= horas <= 23 and 0 <= minutos <= 59


class RatesView:
    def __init__(self, toParent, txUsuarioData):
        self.toParent = toParent
        self.txUsuarioData = txUsuarioData

        self.lofrmMain = None
        self.logrdTarifas = None
        self.lotxtBusqueda = None
        self.loFiltroEstado = None

        self.lobtnEditar = None
        self.lobtnDetalle = None
        self.lobtnEstado = None

    def build(self):
        self.lofrmMain = tk.Frame(self.toParent, bg="white")
        self.lofrmMain.pack(fill="both", expand=True)

        if self.txUsuarioData.get("RolId") != gnRolAdministrador:
            self.buildAccessDenied()
            return

        self.buildHeader()
        self.buildTable()
        self.buildActions()
        self.loadRates()

    def buildAccessDenied(self):
        lofrmContainer = tk.Frame(self.lofrmMain, bg="white")
        lofrmContainer.pack(fill="both", expand=True)

        tk.Label(
            lofrmContainer,
            text="Acceso restringido",
            font=("Arial", 18, "bold"),
            bg="white",
            fg="#b91c1c"
        ).pack(pady=(80, 10))

        tk.Label(
            lofrmContainer,
            text="Solo el administrador puede gestionar tarifas.",
            font=("Arial", 11),
            bg="white",
            fg="#4b5563"
        ).pack()

    def buildHeader(self):
        lofrmHeader = tk.Frame(self.lofrmMain, bg="white")
        lofrmHeader.pack(fill="x", padx=15, pady=15)

        tk.Label(
            lofrmHeader,
            text="Buscar tarifa:",
            font=("Arial", 11, "bold"),
            bg="white"
        ).pack(side="left", padx=(0, 8))

        self.lotxtBusqueda = tk.Entry(lofrmHeader, font=("Arial", 11), width=28)
        self.lotxtBusqueda.pack(side="left", padx=(0, 12))
        self.lotxtBusqueda.bind("<KeyRelease>", lambda e: self.loadRates())

        tk.Label(
            lofrmHeader,
            text="Estado:",
            font=("Arial", 11, "bold"),
            bg="white"
        ).pack(side="left", padx=(0, 8))

        self.loFiltroEstado = tk.StringVar(value="Activas")
        locmbEstado = ttk.Combobox(
            lofrmHeader,
            textvariable=self.loFiltroEstado,
            state="readonly",
            width=12,
            values=["Activas", "Inactivas", "Todas"]
        )
        locmbEstado.pack(side="left", padx=(0, 12))
        locmbEstado.bind("<<ComboboxSelected>>", lambda e: self.loadRates())

        tk.Button(
            lofrmHeader,
            text="Nueva tarifa",
            font=("Arial", 10, "bold"),
            bg="#16a34a",
            fg="white",
            bd=0,
            padx=15,
            pady=6,
            cursor="hand2",
            command=self.openNewRateWindow
        ).pack(side="right")

    def buildTable(self):
        lofrmTabla = tk.Frame(self.lofrmMain, bg="white")
        lofrmTabla.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        columnas = (
            "Tarifa",
            "Nombre",
            "TipoVehiculo",
            "Descripcion",
            "Estado",
        )

        self.logrdTarifas = ttk.Treeview(
            lofrmTabla,
            columns=columnas,
            show="headings",
            selectmode="browse"
        )

        self.logrdTarifas.heading("Tarifa", text="ID")
        self.logrdTarifas.heading("Nombre", text="Nombre")
        self.logrdTarifas.heading("TipoVehiculo", text="Tipo vehículo")
        self.logrdTarifas.heading("Descripcion", text="Descripción")
        self.logrdTarifas.heading("Estado", text="Estado")

        self.logrdTarifas.column("Tarifa", width=60, anchor="center")
        self.logrdTarifas.column("Nombre", width=220, anchor="w")
        self.logrdTarifas.column("TipoVehiculo", width=120, anchor="center")
        self.logrdTarifas.column("Descripcion", width=360, anchor="w")
        self.logrdTarifas.column("Estado", width=100, anchor="center")

        loscrVertical = ttk.Scrollbar(lofrmTabla, orient="vertical", command=self.logrdTarifas.yview)
        self.logrdTarifas.configure(yscrollcommand=loscrVertical.set)

        self.logrdTarifas.pack(fill="both", expand=True, side="left")
        loscrVertical.pack(side="right", fill="y")

        self.logrdTarifas.bind("<Double-1>", self.onDoubleClick)
        self.logrdTarifas.bind("<<TreeviewSelect>>", lambda e: self.updateActionButtons())

    def buildActions(self):
        lofrmAcciones = tk.Frame(self.lofrmMain, bg="white")
        lofrmAcciones.pack(fill="x", padx=15, pady=(0, 15))

        self.lobtnEditar = tk.Button(
            lofrmAcciones,
            text="Editar",
            font=("Arial", 10, "bold"),
            bg="#f59e0b",
            fg="white",
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
            state="disabled",
            command=self.openEditSelected
        )
        self.lobtnEditar.pack(side="left", padx=(0, 8))

        self.lobtnDetalle = tk.Button(
            lofrmAcciones,
            text="Ver / editar detalle",
            font=("Arial", 10, "bold"),
            bg="#2563eb",
            fg="white",
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
            state="disabled",
            command=self.openSelectedDetail
        )
        self.lobtnDetalle.pack(side="left", padx=(0, 8))

        self.lobtnEstado = tk.Button(
            lofrmAcciones,
            text="Activar / Inactivar",
            font=("Arial", 10, "bold"),
            bg="#6b7280",
            fg="white",
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
            state="disabled",
            command=self.toggleSelectedRateStatus
        )
        self.lobtnEstado.pack(side="left")

    def updateActionButtons(self):
        estado = "normal" if self.logrdTarifas.selection() else "disabled"
        self.lobtnEditar.config(state=estado)
        self.lobtnDetalle.config(state=estado)
        self.lobtnEstado.config(state=estado)

    def getSelectedRateData(self):
        seleccion = self.logrdTarifas.selection()
        if not seleccion:
            return None

        valores = self.logrdTarifas.item(seleccion[0], "values")
        if not valores:
            return None

        return {
            "Tarifa": valores[0],
            "Nombre": valores[1],
            "TipoVehiculo": valores[2],
            "Descripcion": valores[3],
            "EstadoTexto": valores[4]
        }

    def loadRates(self):
        for item in self.logrdTarifas.get_children():
            self.logrdTarifas.delete(item)

        lcBusqueda = self.lotxtBusqueda.get().strip().upper() if self.lotxtBusqueda else ""
        lcFiltroEstado = self.loFiltroEstado.get().strip() if self.loFiltroEstado else "Activas"

        loConn = getConnection()
        loCursor = loConn.cursor()

        try:
            lcQuery = """
                SELECT
                    Tarifa,
                    Nombre,
                    TipoVehiculo,
                    Descripcion,
                    Estado
                FROM TARIFA
                WHERE 1 = 1
            """
            laParams = []

            if lcBusqueda:
                lcLikeValue = f"%{lcBusqueda}%"
                lcQuery += """
                    AND (
                        UPPER(Nombre) LIKE ?
                        OR UPPER(TipoVehiculo) LIKE ?
                        OR UPPER(COALESCE(Descripcion, '')) LIKE ?
                    )
                """
                laParams.extend([lcLikeValue, lcLikeValue, lcLikeValue])

            if lcFiltroEstado == "Activas":
                lcQuery += " AND Estado = ? "
                laParams.append(gnEstadoActivo)
            elif lcFiltroEstado == "Inactivas":
                lcQuery += " AND Estado = ? "
                laParams.append(gnEstadoInactivo)

            lcQuery += " ORDER BY Nombre ASC "

            loCursor.execute(lcQuery, laParams)
            laRows = loCursor.fetchall()

            for toRow in laRows:
                self.logrdTarifas.insert(
                    "",
                    "end",
                    values=(
                        toRow["Tarifa"],
                        toRow["Nombre"],
                        toRow["TipoVehiculo"],
                        toRow["Descripcion"] if toRow["Descripcion"] else "",
                        gxEstadoTexto.get(toRow["Estado"], "N/D"),
                    )
                )

            self.updateActionButtons()

        except Exception as toError:
            messagebox.showerror("Error", f"No se pudieron cargar las tarifas.\n\n{str(toError)}")
        finally:
            loConn.close()

    def onDoubleClick(self, toEvent):
        self.openSelectedDetail()

    def openNewRateWindow(self):
        RateFormWindow(self, self.txUsuarioData)

    def openEditSelected(self):
        loTarifa = self.getSelectedRateData()
        if not loTarifa:
            messagebox.showwarning("Aviso", "Debe seleccionar una tarifa.")
            return

        RateFormWindow(self, self.txUsuarioData, tnTarifa=loTarifa["Tarifa"])

    def openSelectedDetail(self):
        loTarifa = self.getSelectedRateData()
        if not loTarifa:
            messagebox.showwarning("Aviso", "Debe seleccionar una tarifa.")
            return

        RateDetailWindow(self, self.txUsuarioData, loTarifa["Tarifa"])

    def toggleSelectedRateStatus(self):
        loTarifa = self.getSelectedRateData()
        if not loTarifa:
            messagebox.showwarning("Aviso", "Debe seleccionar una tarifa.")
            return

        tnTarifa = loTarifa["Tarifa"]
        lcEstadoActual = loTarifa["EstadoTexto"]

        tnEstadoActual = gxEstadoNumero.get(lcEstadoActual, gnEstadoActivo)
        tnNuevoEstado = gnEstadoInactivo if tnEstadoActual == gnEstadoActivo else gnEstadoActivo
        lcNuevoEstadoTexto = gxEstadoTexto[tnNuevoEstado]

        llConfirmar = messagebox.askyesno(
            "Confirmar cambio",
            f"¿Desea cambiar el estado de la tarifa a '{lcNuevoEstadoTexto}'?"
        )
        if not llConfirmar:
            return

        loConn = getConnection()
        loCursor = loConn.cursor()

        try:
            tnUsr = obtenerUsuarioActualId(self.txUsuarioData)

            loCursor.execute("""
                UPDATE TARIFA
                SET
                    Estado = ?,
                    Usr = ?,
                    UsrFecha = date('now','localtime'),
                    UsrHora = time('now','localtime')
                WHERE Tarifa = ?
            """, (tnNuevoEstado, tnUsr, tnTarifa))

            loConn.commit()
            messagebox.showinfo("Estado actualizado", "El estado de la tarifa fue actualizado.")
            self.loadRates()

        except Exception as toError:
            loConn.rollback()
            messagebox.showerror("Error", f"No se pudo actualizar el estado.\n{str(toError)}")
        finally:
            loConn.close()


class RateFormWindow:
    def __init__(self, toRatesView, txUsuarioData, tnTarifa=None):
        self.toRatesView = toRatesView
        self.txUsuarioData = txUsuarioData
        self.tnTarifa = tnTarifa

        self.loWindow = tk.Toplevel()
        self.loWindow.title("Nueva tarifa" if tnTarifa is None else "Editar tarifa")
        self.loWindow.geometry("480x320")
        self.loWindow.resizable(False, False)
        self.loWindow.configure(bg="white")
        self.loWindow.transient(self.toRatesView.toParent.winfo_toplevel())
        self.loWindow.grab_set()

        self.lotxtNombre = None
        self.lovTipoVehiculo = tk.StringVar(value="auto")
        self.lotxtDescripcion = None

        self.buildUi()
        self.centerWindow()

        if self.tnTarifa is not None:
            self.loadRateData()

        self.updateNameSuggestion()

    def centerWindow(self):
        self.loWindow.update_idletasks()
        ancho = self.loWindow.winfo_width()
        alto = self.loWindow.winfo_height()
        x = (self.loWindow.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.loWindow.winfo_screenheight() // 2) - (alto // 2)
        self.loWindow.geometry(f"{ancho}x{alto}+{x}+{y}")

    def buildUi(self):
        lcTitulo = "Nueva tarifa" if self.tnTarifa is None else "Editar tarifa"

        tk.Label(
            self.loWindow,
            text=lcTitulo,
            font=("Arial", 16, "bold"),
            bg="white",
            fg="#111827"
        ).pack(pady=(20, 16))

        lofrmFormulario = tk.Frame(self.loWindow, bg="white")
        lofrmFormulario.pack(padx=30, fill="x")

        tk.Label(
            lofrmFormulario,
            text="Tipo de vehículo *",
            font=("Arial", 11, "bold"),
            bg="white"
        ).pack(anchor="w", pady=(0, 5))

        lofrmVehiculo = tk.Frame(lofrmFormulario, bg="white")
        lofrmVehiculo.pack(fill="x", pady=(0, 12))

        tk.Radiobutton(
            lofrmVehiculo,
            text="Auto",
            variable=self.lovTipoVehiculo,
            value="auto",
            bg="white",
            font=("Arial", 11),
            command=self.updateNameSuggestion
        ).pack(side="left", padx=(0, 20))

        tk.Radiobutton(
            lofrmVehiculo,
            text="Moto",
            variable=self.lovTipoVehiculo,
            value="moto",
            bg="white",
            font=("Arial", 11),
            command=self.updateNameSuggestion
        ).pack(side="left", padx=(0, 20))

        tk.Label(
            lofrmFormulario,
            text="Nombre *",
            font=("Arial", 11, "bold"),
            bg="white"
        ).pack(anchor="w", pady=(0, 5))

        self.lotxtNombre = tk.Entry(lofrmFormulario, font=("Arial", 11))
        self.lotxtNombre.pack(fill="x", pady=(0, 12))

        tk.Label(
            lofrmFormulario,
            text="Descripción",
            font=("Arial", 11, "bold"),
            bg="white"
        ).pack(anchor="w", pady=(0, 5))

        self.lotxtDescripcion = tk.Entry(lofrmFormulario, font=("Arial", 11))
        self.lotxtDescripcion.pack(fill="x", pady=(0, 12))

        tk.Label(
            lofrmFormulario,
            text="Ejemplo: Parqueo Auto, Mensual Auto.",
            font=("Arial", 9),
            bg="white",
            fg="#6b7280"
        ).pack(anchor="w", pady=(0, 12))

        lofrmBotones = tk.Frame(self.loWindow, bg="white")
        lofrmBotones.pack(pady=18)

        tk.Button(
            lofrmBotones,
            text="Guardar",
            font=("Arial", 11, "bold"),
            bg="#2563eb",
            fg="white",
            bd=0,
            padx=18,
            pady=8,
            cursor="hand2",
            command=self.confirmSave
        ).grid(row=0, column=0, padx=10)

        tk.Button(
            lofrmBotones,
            text="Cancelar",
            font=("Arial", 11, "bold"),
            bg="#dc2626",
            fg="white",
            bd=0,
            padx=18,
            pady=8,
            cursor="hand2",
            command=self.loWindow.destroy
        ).grid(row=0, column=1, padx=10)

    def updateNameSuggestion(self):
        if not self.lotxtNombre:
            return

        lcVehicleText = "Auto" if self.lovTipoVehiculo.get() == "auto" else "Moto"
        lcNombreActual = self.lotxtNombre.get().strip()

        sugerencias = {
            "",
            "Parqueo Auto",
            "Parqueo Moto",
            "Mensual Auto",
            "Mensual Moto",
            "Tarifa General Auto",
            "Tarifa General Moto",
        }

        if lcNombreActual in sugerencias:
            self.lotxtNombre.delete(0, "end")
            self.lotxtNombre.insert(0, f"Parqueo {lcVehicleText}")

    def loadRateData(self):
        loConn = getConnection()
        loCursor = loConn.cursor()

        try:
            loCursor.execute("""
                SELECT Nombre, TipoVehiculo, Descripcion
                FROM TARIFA
                WHERE Tarifa = ?
            """, (self.tnTarifa,))
            toRow = loCursor.fetchone()

            if not toRow:
                messagebox.showerror("Error", "No se encontró la tarifa.")
                self.loWindow.destroy()
                return

            self.lotxtNombre.delete(0, "end")
            self.lotxtNombre.insert(0, toRow["Nombre"])
            self.lovTipoVehiculo.set(toRow["TipoVehiculo"])
            self.lotxtDescripcion.delete(0, "end")
            self.lotxtDescripcion.insert(0, toRow["Descripcion"] if toRow["Descripcion"] else "")
        finally:
            loConn.close()

    def existeNombreDuplicado(self, tcNombre, tcTipoVehiculo):
        loConn = getConnection()
        loCursor = loConn.cursor()

        try:
            if self.tnTarifa is None:
                loCursor.execute("""
                    SELECT COUNT(*) AS Cantidad
                    FROM TARIFA
                    WHERE UPPER(Nombre) = UPPER(?)
                      AND UPPER(TipoVehiculo) = UPPER(?)
                """, (tcNombre, tcTipoVehiculo))
            else:
                loCursor.execute("""
                    SELECT COUNT(*) AS Cantidad
                    FROM TARIFA
                    WHERE UPPER(Nombre) = UPPER(?)
                      AND UPPER(TipoVehiculo) = UPPER(?)
                      AND Tarifa <> ?
                """, (tcNombre, tcTipoVehiculo, self.tnTarifa))

            fila = loCursor.fetchone()
            return fila["Cantidad"] > 0
        finally:
            loConn.close()

    def confirmSave(self):
        llConfirmado = messagebox.askyesno(
            "Confirmar guardado",
            "¿Desea guardar esta tarifa?"
        )
        if not llConfirmado:
            return

        self.saveRate()

    def saveRate(self):
        lcNombre = self.lotxtNombre.get().strip()
        lcTipoVehiculo = self.lovTipoVehiculo.get().strip()
        lcDescripcion = self.lotxtDescripcion.get().strip()

        if not lcNombre:
            messagebox.showwarning("Datos requeridos", "El nombre es obligatorio.")
            self.lotxtNombre.focus()
            return

        if self.existeNombreDuplicado(lcNombre, lcTipoVehiculo):
            messagebox.showwarning("Validación", "Ya existe una tarifa con ese nombre para ese tipo de vehículo.")
            self.lotxtNombre.focus()
            return

        loConn = getConnection()
        loCursor = loConn.cursor()

        try:
            tnUsr = obtenerUsuarioActualId(self.txUsuarioData)

            if self.tnTarifa is None:
                loCursor.execute("""
                    INSERT INTO TARIFA (
                        Nombre,
                        TipoVehiculo,
                        Descripcion,
                        Estado,
                        Usr,
                        UsrFecha,
                        UsrHora,
                        FechaCreacion,
                        FechaModificacion
                    )
                    VALUES (
                        ?, ?, ?, ?, ?,
                        date('now','localtime'),
                        time('now','localtime'),
                        datetime('now','localtime'),
                        datetime('now','localtime')
                    )
                """, (
                    lcNombre,
                    lcTipoVehiculo,
                    lcDescripcion if lcDescripcion else None,
                    gnEstadoActivo,
                    tnUsr
                ))
            else:
                loCursor.execute("""
                    UPDATE TARIFA
                    SET
                        Nombre = ?,
                        TipoVehiculo = ?,
                        Descripcion = ?,
                        Usr = ?,
                        UsrFecha = date('now','localtime'),
                        UsrHora = time('now','localtime')
                    WHERE Tarifa = ?
                """, (
                    lcNombre,
                    lcTipoVehiculo,
                    lcDescripcion if lcDescripcion else None,
                    tnUsr,
                    self.tnTarifa
                ))

            loConn.commit()
            messagebox.showinfo("Guardado", "Tarifa guardada correctamente.")
            self.toRatesView.loadRates()
            self.loWindow.destroy()

        except Exception as toError:
            loConn.rollback()
            messagebox.showerror("Error", f"No se pudo guardar la tarifa.\n{str(toError)}")
        finally:
            loConn.close()

    def run(self):
        pass


class RateDetailWindow:
    def __init__(self, toRatesView, txUsuarioData, tnTarifa):
        self.toRatesView = toRatesView
        self.txUsuarioData = txUsuarioData
        self.tnTarifa = tnTarifa

        self.loWindow = tk.Toplevel()
        self.loWindow.title("Detalle de tarifa")
        self.loWindow.geometry("980x540")
        self.loWindow.resizable(True, True)
        self.loWindow.configure(bg="white")
        self.loWindow.transient(self.toRatesView.toParent.winfo_toplevel())
        self.loWindow.grab_set()

        self.logrdDetalle = None
        self.toTarifaInfo = None

        self.lobtnEditar = None
        self.lobtnEstado = None

        self.loadRateInfo()
        self.buildUi()
        self.loadDetails()

    def loadRateInfo(self):
        loConn = getConnection()
        loCursor = loConn.cursor()

        try:
            loCursor.execute("""
                SELECT Tarifa, Nombre, TipoVehiculo, Descripcion
                FROM TARIFA
                WHERE Tarifa = ?
            """, (self.tnTarifa,))
            self.toTarifaInfo = loCursor.fetchone()

            if not self.toTarifaInfo:
                raise Exception("No se encontró la tarifa.")
        finally:
            loConn.close()

    def buildUi(self):
        lofrmHeader = tk.Frame(self.loWindow, bg="white")
        lofrmHeader.pack(fill="x", padx=15, pady=15)

        tk.Label(
            lofrmHeader,
            text=f"Detalle: {self.toTarifaInfo['Nombre']}",
            font=("Arial", 15, "bold"),
            bg="white",
            fg="#111827"
        ).pack(anchor="w")

        tk.Label(
            lofrmHeader,
            text=f"Vehículo: {self.toTarifaInfo['TipoVehiculo']}",
            font=("Arial", 10),
            bg="white",
            fg="#4b5563"
        ).pack(anchor="w", pady=(4, 0))

        lofrmAcciones = tk.Frame(self.loWindow, bg="white")
        lofrmAcciones.pack(fill="x", padx=15, pady=(0, 10))

        tk.Button(
            lofrmAcciones,
            text="Nuevo detalle",
            font=("Arial", 10, "bold"),
            bg="#16a34a",
            fg="white",
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
            command=self.openNewDetail
        ).pack(side="right")

        self.lobtnEditar = tk.Button(
            lofrmAcciones,
            text="Editar detalle",
            font=("Arial", 10, "bold"),
            bg="#f59e0b",
            fg="white",
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
            state="disabled",
            command=self.editSelectedDetail
        )
        self.lobtnEditar.pack(side="left", padx=(0, 8))

        self.lobtnEstado = tk.Button(
            lofrmAcciones,
            text="Activar / Inactivar",
            font=("Arial", 10, "bold"),
            bg="#2563eb",
            fg="white",
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
            state="disabled",
            command=self.toggleSelectedDetailStatus
        )
        self.lobtnEstado.pack(side="left")

        lofrmTabla = tk.Frame(self.loWindow, bg="white")
        lofrmTabla.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        columnas = (
            "TarifaDetalle",
            "TipoCobro",
            "TiempoInicio",
            "TiempoFin",
            "HoraInicio",
            "HoraFin",
            "Monto",
            "Estado",
        )

        self.logrdDetalle = ttk.Treeview(
            lofrmTabla,
            columns=columnas,
            show="headings",
            selectmode="browse"
        )

        self.logrdDetalle.heading("TarifaDetalle", text="ID")
        self.logrdDetalle.heading("TipoCobro", text="Tipo cobro")
        self.logrdDetalle.heading("TiempoInicio", text="Tiempo inicio")
        self.logrdDetalle.heading("TiempoFin", text="Tiempo fin")
        self.logrdDetalle.heading("HoraInicio", text="Hora inicio")
        self.logrdDetalle.heading("HoraFin", text="Hora fin")
        self.logrdDetalle.heading("Monto", text="Monto")
        self.logrdDetalle.heading("Estado", text="Estado")

        self.logrdDetalle.column("TarifaDetalle", width=55, anchor="center")
        self.logrdDetalle.column("TipoCobro", width=110, anchor="center")
        self.logrdDetalle.column("TiempoInicio", width=100, anchor="center")
        self.logrdDetalle.column("TiempoFin", width=100, anchor="center")
        self.logrdDetalle.column("HoraInicio", width=100, anchor="center")
        self.logrdDetalle.column("HoraFin", width=100, anchor="center")
        self.logrdDetalle.column("Monto", width=100, anchor="e")
        self.logrdDetalle.column("Estado", width=90, anchor="center")

        loscrVertical = ttk.Scrollbar(lofrmTabla, orient="vertical", command=self.logrdDetalle.yview)
        self.logrdDetalle.configure(yscrollcommand=loscrVertical.set)

        self.logrdDetalle.pack(fill="both", expand=True, side="left")
        loscrVertical.pack(side="right", fill="y")

        self.logrdDetalle.bind("<Double-1>", lambda e: self.editSelectedDetail())
        self.logrdDetalle.bind("<<TreeviewSelect>>", lambda e: self.updateActionButtons())

    def updateActionButtons(self):
        estado = "normal" if self.logrdDetalle.selection() else "disabled"
        self.lobtnEditar.config(state=estado)
        self.lobtnEstado.config(state=estado)

    def loadDetails(self):
        for toItem in self.logrdDetalle.get_children():
            self.logrdDetalle.delete(toItem)

        loConn = getConnection()
        loCursor = loConn.cursor()

        try:
            loCursor.execute("""
                SELECT
                    TarifaDetalle,
                    TipoCobro,
                    TiempoInicio,
                    TiempoFin,
                    HoraInicio,
                    HoraFin,
                    Monto,
                    Estado
                FROM TARIFADETALLE
                WHERE Tarifa = ?
                ORDER BY TipoCobro ASC, TiempoInicio ASC, TarifaDetalle ASC
            """, (self.tnTarifa,))
            laRows = loCursor.fetchall()

            for toRow in laRows:
                self.logrdDetalle.insert(
                    "",
                    "end",
                    values=(
                        toRow["TarifaDetalle"],
                        gxTipoCobroTexto.get(toRow["TipoCobro"], "N/D"),
                        toRow["TiempoInicio"],
                        toRow["TiempoFin"],
                        toRow["HoraInicio"] or "",
                        toRow["HoraFin"] or "",
                        f"Bs {float(toRow['Monto']):.2f}",
                        gxEstadoTexto.get(toRow["Estado"], "N/D")
                    )
                )

            self.updateActionButtons()

        finally:
            loConn.close()

    def getSelectedDetailData(self):
        seleccion = self.logrdDetalle.selection()
        if not seleccion:
            return None

        valores = self.logrdDetalle.item(seleccion[0], "values")
        if not valores:
            return None

        return {
            "TarifaDetalle": valores[0],
            "TipoCobroTexto": valores[1],
            "EstadoTexto": valores[7]
        }

    def openNewDetail(self):
        RateDetailFormWindow(self, self.txUsuarioData, self.tnTarifa)

    def editSelectedDetail(self):
        loDetalle = self.getSelectedDetailData()
        if not loDetalle:
            messagebox.showwarning("Aviso", "Debe seleccionar un detalle.")
            return

        RateDetailFormWindow(
            self,
            self.txUsuarioData,
            self.tnTarifa,
            tnTarifaDetalle=loDetalle["TarifaDetalle"]
        )

    def toggleSelectedDetailStatus(self):
        loDetalle = self.getSelectedDetailData()
        if not loDetalle:
            messagebox.showwarning("Aviso", "Debe seleccionar un detalle.")
            return

        tnTarifaDetalle = loDetalle["TarifaDetalle"]

        loConn = getConnection()
        loCursor = loConn.cursor()

        try:
            loCursor.execute("""
                SELECT Estado
                FROM TARIFADETALLE
                WHERE TarifaDetalle = ?
            """, (tnTarifaDetalle,))
            toRow = loCursor.fetchone()

            if not toRow:
                messagebox.showerror("Error", "No se encontró el detalle.")
                return

            tnEstadoActual = toRow["Estado"]
            tnNuevoEstado = gnEstadoInactivo if tnEstadoActual == gnEstadoActivo else gnEstadoActivo
            tnUsr = obtenerUsuarioActualId(self.txUsuarioData)

            loCursor.execute("""
                UPDATE TARIFADETALLE
                SET
                    Estado = ?,
                    Usr = ?,
                    UsrFecha = date('now','localtime'),
                    UsrHora = time('now','localtime')
                WHERE TarifaDetalle = ?
            """, (tnNuevoEstado, tnUsr, tnTarifaDetalle))

            loConn.commit()
            self.loadDetails()
            messagebox.showinfo("Actualizado", "Estado del detalle actualizado.")

        except Exception as toError:
            loConn.rollback()
            messagebox.showerror("Error", f"No se pudo actualizar el detalle.\n{str(toError)}")
        finally:
            loConn.close()

    def run(self):
        pass


class RateDetailFormWindow:
    def __init__(self, toDetailView, txUsuarioData, tnTarifa, tnTarifaDetalle=None):
        self.toDetailView = toDetailView
        self.txUsuarioData = txUsuarioData
        self.tnTarifa = tnTarifa
        self.tnTarifaDetalle = tnTarifaDetalle

        self.loWindow = tk.Toplevel()
        self.loWindow.title("Nuevo detalle" if tnTarifaDetalle is None else "Editar detalle")
        self.loWindow.geometry("460x520")
        self.loWindow.resizable(False, False)
        self.loWindow.configure(bg="white")
        self.loWindow.transient(self.toDetailView.loWindow)
        self.loWindow.grab_set()

        self.lovTipoCobro = tk.StringVar(value="Hora")
        self.lotxtTiempoInicio = None
        self.lotxtTiempoFin = None
        self.lotxtHoraInicio = None
        self.lotxtHoraFin = None
        self.lotxtMonto = None

        self.lofrmTiempo = None
        self.lofrmHorario = None
        self.lolblAyuda = None

        self.buildUi()
        self.centerWindow()

        if self.tnTarifaDetalle is not None:
            self.loadDetailData()

        self.actualizarFormularioSegunTipo()

    def centerWindow(self):
        self.loWindow.update_idletasks()
        ancho = self.loWindow.winfo_width()
        alto = self.loWindow.winfo_height()
        x = (self.loWindow.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.loWindow.winfo_screenheight() // 2) - (alto // 2)
        self.loWindow.geometry(f"{ancho}x{alto}+{x}+{y}")

    def buildUi(self):
        lcTitulo = "Nuevo detalle" if self.tnTarifaDetalle is None else "Editar detalle"

        tk.Label(
            self.loWindow,
            text=lcTitulo,
            font=("Arial", 16, "bold"),
            bg="white",
            fg="#111827"
        ).pack(pady=(20, 16))

        lofrmFormulario = tk.Frame(self.loWindow, bg="white")
        lofrmFormulario.pack(padx=30, fill="x")

        tk.Label(
            lofrmFormulario,
            text="Tipo cobro *",
            font=("Arial", 11, "bold"),
            bg="white"
        ).pack(anchor="w", pady=(0, 5))

        locboTipoCobro = ttk.Combobox(
            lofrmFormulario,
            textvariable=self.lovTipoCobro,
            values=list(gxTipoCobroInv.keys()),
            state="readonly"
        )
        locboTipoCobro.pack(fill="x", pady=(0, 12))
        locboTipoCobro.bind("<<ComboboxSelected>>", lambda e: self.actualizarFormularioSegunTipo())

        self.lofrmTiempo = tk.Frame(lofrmFormulario, bg="white")
        self.lofrmTiempo.pack(fill="x", pady=(0, 10))

        tk.Label(
            self.lofrmTiempo,
            text="Tiempo inicio *",
            font=("Arial", 11, "bold"),
            bg="white"
        ).pack(anchor="w", pady=(0, 5))

        self.lotxtTiempoInicio = tk.Entry(self.lofrmTiempo, font=("Arial", 11))
        self.lotxtTiempoInicio.pack(fill="x", pady=(0, 12))

        tk.Label(
            self.lofrmTiempo,
            text="Tiempo fin *",
            font=("Arial", 11, "bold"),
            bg="white"
        ).pack(anchor="w", pady=(0, 5))

        self.lotxtTiempoFin = tk.Entry(self.lofrmTiempo, font=("Arial", 11))
        self.lotxtTiempoFin.pack(fill="x", pady=(0, 12))

        self.lofrmHorario = tk.Frame(lofrmFormulario, bg="white")
        self.lofrmHorario.pack(fill="x", pady=(0, 10))

        tk.Label(
            self.lofrmHorario,
            text="Hora inicio *",
            font=("Arial", 11, "bold"),
            bg="white"
        ).pack(anchor="w", pady=(0, 5))

        self.lotxtHoraInicio = tk.Entry(self.lofrmHorario, font=("Arial", 11))
        self.lotxtHoraInicio.pack(fill="x", pady=(0, 12))

        tk.Label(
            self.lofrmHorario,
            text="Hora fin *",
            font=("Arial", 11, "bold"),
            bg="white"
        ).pack(anchor="w", pady=(0, 5))

        self.lotxtHoraFin = tk.Entry(self.lofrmHorario, font=("Arial", 11))
        self.lotxtHoraFin.pack(fill="x", pady=(0, 12))

        tk.Label(
            lofrmFormulario,
            text="Monto (Bs) *",
            font=("Arial", 11, "bold"),
            bg="white"
        ).pack(anchor="w", pady=(0, 5))

        self.lotxtMonto = tk.Entry(lofrmFormulario, font=("Arial", 11))
        self.lotxtMonto.pack(fill="x", pady=(0, 12))

        self.lolblAyuda = tk.Label(
            lofrmFormulario,
            text="",
            font=("Arial", 9),
            bg="white",
            fg="#6b7280",
            justify="left"
        )
        self.lolblAyuda.pack(anchor="w", pady=(0, 12))

        lofrmBotones = tk.Frame(self.loWindow, bg="white")
        lofrmBotones.pack(pady=18)

        tk.Button(
            lofrmBotones,
            text="Guardar",
            font=("Arial", 11, "bold"),
            bg="#2563eb",
            fg="white",
            bd=0,
            padx=18,
            pady=8,
            cursor="hand2",
            command=self.confirmSave
        ).grid(row=0, column=0, padx=10)

        tk.Button(
            lofrmBotones,
            text="Cancelar",
            font=("Arial", 11, "bold"),
            bg="#dc2626",
            fg="white",
            bd=0,
            padx=18,
            pady=8,
            cursor="hand2",
            command=self.loWindow.destroy
        ).grid(row=0, column=1, padx=10)

    def actualizarFormularioSegunTipo(self):
        lcTipo = self.lovTipoCobro.get().strip()

        self.lofrmTiempo.pack_forget()
        self.lofrmHorario.pack_forget()

        if lcTipo == "Nocturna":
            self.lofrmHorario.pack(fill="x", pady=(0, 10))
            self.lolblAyuda.config(
                text="Para tarifa nocturna ingresa el horario en formato HH:MM.\nEjemplo: 18:00 a 20:00."
            )
        elif lcTipo == "Mes":
            self.lofrmTiempo.pack(fill="x", pady=(0, 10))
            self.lolblAyuda.config(
                text="Para tarifa mensual usa normalmente Tiempo inicio = 1 y Tiempo fin = 1."
            )
        elif lcTipo == "Día":
            self.lofrmTiempo.pack(fill="x", pady=(0, 10))
            self.lolblAyuda.config(
                text="Para tarifa por día usa normalmente Tiempo inicio = 1 y Tiempo fin = 1."
            )
        else:
            self.lofrmTiempo.pack(fill="x", pady=(0, 10))
            self.lolblAyuda.config(
                text="Para tarifa por hora usa minutos.\nEjemplo: 1 a 30, 31 a 60, 61 a 120."
            )

    def loadDetailData(self):
        loConn = getConnection()
        loCursor = loConn.cursor()

        try:
            loCursor.execute("""
                SELECT
                    TipoCobro,
                    TiempoInicio,
                    TiempoFin,
                    HoraInicio,
                    HoraFin,
                    Monto
                FROM TARIFADETALLE
                WHERE TarifaDetalle = ?
            """, (self.tnTarifaDetalle,))
            toRow = loCursor.fetchone()

            if not toRow:
                messagebox.showerror("Error", "No se encontró el detalle.")
                self.loWindow.destroy()
                return

            self.lovTipoCobro.set(gxTipoCobroTexto.get(toRow["TipoCobro"], "Hora"))

            self.lotxtTiempoInicio.delete(0, "end")
            self.lotxtTiempoInicio.insert(0, str(toRow["TiempoInicio"]))

            self.lotxtTiempoFin.delete(0, "end")
            self.lotxtTiempoFin.insert(0, str(toRow["TiempoFin"]))

            self.lotxtHoraInicio.delete(0, "end")
            self.lotxtHoraInicio.insert(0, toRow["HoraInicio"] or "")

            self.lotxtHoraFin.delete(0, "end")
            self.lotxtHoraFin.insert(0, toRow["HoraFin"] or "")

            self.lotxtMonto.delete(0, "end")
            self.lotxtMonto.insert(0, str(toRow["Monto"]))

            self.actualizarFormularioSegunTipo()

        finally:
            loConn.close()

    def existeDetalleDuplicado(self, tnTipoCobro, tnTiempoInicio, tnTiempoFin, tcHoraInicio, tcHoraFin):
        loConn = getConnection()
        loCursor = loConn.cursor()

        try:
            if self.tnTarifaDetalle is None:
                loCursor.execute("""
                    SELECT COUNT(*) AS Cantidad
                    FROM TARIFADETALLE
                    WHERE Tarifa = ?
                      AND TipoCobro = ?
                      AND TiempoInicio = ?
                      AND TiempoFin = ?
                      AND COALESCE(HoraInicio, '') = COALESCE(?, '')
                      AND COALESCE(HoraFin, '') = COALESCE(?, '')
                """, (
                    self.tnTarifa,
                    tnTipoCobro,
                    tnTiempoInicio,
                    tnTiempoFin,
                    tcHoraInicio,
                    tcHoraFin
                ))
            else:
                loCursor.execute("""
                    SELECT COUNT(*) AS Cantidad
                    FROM TARIFADETALLE
                    WHERE Tarifa = ?
                      AND TipoCobro = ?
                      AND TiempoInicio = ?
                      AND TiempoFin = ?
                      AND COALESCE(HoraInicio, '') = COALESCE(?, '')
                      AND COALESCE(HoraFin, '') = COALESCE(?, '')
                      AND TarifaDetalle <> ?
                """, (
                    self.tnTarifa,
                    tnTipoCobro,
                    tnTiempoInicio,
                    tnTiempoFin,
                    tcHoraInicio,
                    tcHoraFin,
                    self.tnTarifaDetalle
                ))

            fila = loCursor.fetchone()
            return fila["Cantidad"] > 0
        finally:
            loConn.close()

    def confirmSave(self):
        llConfirmado = messagebox.askyesno(
            "Confirmar guardado",
            "¿Desea guardar este detalle?"
        )
        if not llConfirmado:
            return

        self.saveDetail()

    def saveDetail(self):
        tnTipoCobro = gxTipoCobroInv[self.lovTipoCobro.get()]
        lcTiempoInicio = self.lotxtTiempoInicio.get().strip()
        lcTiempoFin = self.lotxtTiempoFin.get().strip()
        lcHoraInicio = self.lotxtHoraInicio.get().strip()
        lcHoraFin = self.lotxtHoraFin.get().strip()
        lcMonto = self.lotxtMonto.get().strip()

        tnTiempoInicio = 0
        tnTiempoFin = 0
        tcHoraInicio = None
        tcHoraFin = None

        if not lcMonto:
            messagebox.showwarning("Datos requeridos", "El monto es obligatorio.")
            self.lotxtMonto.focus()
            return

        try:
            tnMonto = float(lcMonto)
        except ValueError:
            messagebox.showwarning("Datos inválidos", "El monto debe ser numérico.")
            self.lotxtMonto.focus()
            return

        if tnMonto < 0:
            messagebox.showwarning("Datos inválidos", "El monto no puede ser negativo.")
            self.lotxtMonto.focus()
            return

        if tnTipoCobro == gnTipoCobroNocturna:
            if not lcHoraInicio or not lcHoraFin:
                messagebox.showwarning(
                    "Datos requeridos",
                    "Para la tarifa nocturna debe ingresar hora inicio y hora fin."
                )
                return

            if not esHoraValida(lcHoraInicio) or not esHoraValida(lcHoraFin):
                messagebox.showwarning(
                    "Datos inválidos",
                    "Las horas deben tener formato HH:MM."
                )
                return

            tcHoraInicio = lcHoraInicio
            tcHoraFin = lcHoraFin
            tnTiempoInicio = 0
            tnTiempoFin = 0

        else:
            if not lcTiempoInicio or not lcTiempoFin:
                messagebox.showwarning(
                    "Datos requeridos",
                    "Tiempo inicio y tiempo fin son obligatorios."
                )
                return

            try:
                tnTiempoInicio = int(lcTiempoInicio)
                tnTiempoFin = int(lcTiempoFin)
            except ValueError:
                messagebox.showwarning(
                    "Datos inválidos",
                    "Tiempo inicio y tiempo fin deben ser enteros."
                )
                return

            if tnTiempoInicio < 0 or tnTiempoFin < tnTiempoInicio:
                messagebox.showwarning("Datos inválidos", "Verifica el rango de tiempos.")
                return

            tcHoraInicio = None
            tcHoraFin = None

        if self.existeDetalleDuplicado(
            tnTipoCobro,
            tnTiempoInicio,
            tnTiempoFin,
            tcHoraInicio,
            tcHoraFin
        ):
            messagebox.showwarning(
                "Validación",
                "Ya existe un detalle con esos mismos valores."
            )
            return

        tnUsr = obtenerUsuarioActualId(self.txUsuarioData)

        loConn = getConnection()
        loCursor = loConn.cursor()

        try:
            if self.tnTarifaDetalle is None:
                loCursor.execute("""
                    INSERT INTO TARIFADETALLE (
                        Tarifa,
                        TipoCobro,
                        TiempoInicio,
                        TiempoFin,
                        HoraInicio,
                        HoraFin,
                        Monto,
                        Estado,
                        Usr,
                        UsrFecha,
                        UsrHora,
                        FechaCreacion,
                        FechaModificacion
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        date('now','localtime'),
                        time('now','localtime'),
                        datetime('now','localtime'),
                        datetime('now','localtime')
                    )
                """, (
                    self.tnTarifa,
                    tnTipoCobro,
                    tnTiempoInicio,
                    tnTiempoFin,
                    tcHoraInicio,
                    tcHoraFin,
                    tnMonto,
                    gnEstadoActivo,
                    tnUsr
                ))
            else:
                loCursor.execute("""
                    UPDATE TARIFADETALLE
                    SET
                        TipoCobro = ?,
                        TiempoInicio = ?,
                        TiempoFin = ?,
                        HoraInicio = ?,
                        HoraFin = ?,
                        Monto = ?,
                        Usr = ?,
                        UsrFecha = date('now','localtime'),
                        UsrHora = time('now','localtime')
                    WHERE TarifaDetalle = ?
                """, (
                    tnTipoCobro,
                    tnTiempoInicio,
                    tnTiempoFin,
                    tcHoraInicio,
                    tcHoraFin,
                    tnMonto,
                    tnUsr,
                    self.tnTarifaDetalle
                ))

            loConn.commit()
            messagebox.showinfo("Guardado", "Detalle guardado correctamente.")
            self.toDetailView.loadDetails()
            self.loWindow.destroy()

        except Exception as toError:
            loConn.rollback()
            messagebox.showerror("Error", f"No se pudo guardar el detalle.\n{str(toError)}")
        finally:
            loConn.close()

    def run(self):
        pass