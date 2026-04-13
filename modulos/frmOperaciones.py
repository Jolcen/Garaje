import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from database.db import getConnection
from modulos.frmCobros import FrmCobros
from utils.printer import imprimir_ticket


gnRolAdministrador = 1

gnEstadoGeneralActivo = 1
gnEstadoGeneralInactivo = 0

gnEstadoOperacionIngresado = 1
gnEstadoOperacionPagada = 3
gnEstadoOperacionCancelada = 4

gnTipoDetalleOperacion = 1


def getFechaHoraActualTexto():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def obtenerUsuarioActualId(txUsuarioData):
    if not txUsuarioData:
        return 0
    return txUsuarioData.get("Usuario", 0)


def esAdministrador(txUsuarioData):
    if not txUsuarioData:
        return False

    if txUsuarioData.get("RolId") == gnRolAdministrador:
        return True

    return str(txUsuarioData.get("Rol", "")).lower() == "admin"


def limpiarPlacaParaBusqueda(tcPlaca):
    return tcPlaca.replace(" ", "").replace("-", "").upper().strip()


def nombreEstadoOperacion(tnEstado):
    if tnEstado == gnEstadoOperacionIngresado:
        return "Ingresado"
    if tnEstado == gnEstadoOperacionPagada:
        return "Pagada"
    if tnEstado == gnEstadoOperacionCancelada:
        return "Cancelada"
    return "N/D"


def formatMinutes(tnMinutos):
    tnMinutos = int(tnMinutos or 0)
    tnHoras = tnMinutos // 60
    tnMinutosRestantes = tnMinutos % 60

    if tnHoras > 0 and tnMinutosRestantes > 0:
        return f"{tnHoras} h {tnMinutosRestantes} min"
    if tnHoras > 0:
        return f"{tnHoras} h"
    return f"{tnMinutosRestantes} min"


def obtenerTarifaParqueoPorTipoVehiculo(tcTipoVehiculo):
    loConn = getConnection()
    loCursor = loConn.cursor()

    loCursor.execute("""
        SELECT Tarifa, Nombre, TipoVehiculo
        FROM TARIFA
        WHERE Estado = ?
          AND TipoVehiculo = ?
          AND UPPER(Nombre) LIKE 'PARQUEO%'
        ORDER BY Tarifa ASC
        LIMIT 1
    """, (gnEstadoGeneralActivo, tcTipoVehiculo))
    toFila = loCursor.fetchone()

    loConn.close()
    return toFila


def obtenerServiciosActivos():
    loConn = getConnection()
    loCursor = loConn.cursor()

    loCursor.execute("""
        SELECT Servicio, Nombre, Precio
        FROM SERVICIO
        WHERE Estado = ?
        ORDER BY Nombre ASC
    """, (gnEstadoGeneralActivo,))
    laFilas = loCursor.fetchall()

    loConn.close()
    return laFilas


def tieneContratoActivoVehiculo(tnVehiculo):
    loConn = getConnection()
    loCursor = loConn.cursor()

    loCursor.execute("""
        SELECT Contrato
        FROM CONTRATO
        WHERE Vehiculo = ?
          AND Estado = 1
          AND date('now','localtime') BETWEEN FechaInicio AND FechaFin
        ORDER BY Contrato DESC
        LIMIT 1
    """, (tnVehiculo,))
    toFila = loCursor.fetchone()

    loConn.close()
    return toFila is not None


def obtenerVehiculoDeOperacion(tnOperacion):
    loConn = getConnection()
    loCursor = loConn.cursor()

    loCursor.execute("""
        SELECT Vehiculo
        FROM OPERACION
        WHERE Operacion = ?
        LIMIT 1
    """, (tnOperacion,))
    toFila = loCursor.fetchone()

    loConn.close()

    if not toFila:
        return None

    return toFila["Vehiculo"]


class OperationsView:
    def __init__(self, toParent, txUsuarioData):
        self.toParent = toParent
        self.txUsuarioData = txUsuarioData or {}

        self.lotxtBusquedaPlaca = None
        self.lotxtBusquedaCodigo = None
        self.locboEstado = None
        self.lovEstado = tk.StringVar(value="Todos")
        self.logrdOperaciones = None

    def build(self):
        self.buildHeader()
        self.buildTable()
        self.loadOperations()

    def buildHeader(self):
        lofrmHeader = tk.Frame(self.toParent, bg="white")
        lofrmHeader.pack(fill="x", padx=15, pady=15)

        tk.Label(
            lofrmHeader,
            text="Buscar placa:",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#111827"
        ).grid(row=0, column=0, padx=(0, 8), pady=5, sticky="w")

        self.lotxtBusquedaPlaca = tk.Entry(lofrmHeader, font=("Arial", 11), width=20)
        self.lotxtBusquedaPlaca.grid(row=0, column=1, padx=(0, 12), pady=5)
        self.lotxtBusquedaPlaca.bind("<KeyRelease>", lambda _e: self.loadOperations())

        tk.Label(
            lofrmHeader,
            text="Código operación:",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#111827"
        ).grid(row=0, column=2, padx=(0, 8), pady=5, sticky="w")

        self.lotxtBusquedaCodigo = tk.Entry(lofrmHeader, font=("Arial", 11), width=18)
        self.lotxtBusquedaCodigo.grid(row=0, column=3, padx=(0, 12), pady=5)
        self.lotxtBusquedaCodigo.bind("<KeyRelease>", lambda _e: self.loadOperations())

        lnColumna = 4

        if esAdministrador(self.txUsuarioData):
            tk.Label(
                lofrmHeader,
                text="Estado:",
                font=("Arial", 11, "bold"),
                bg="white",
                fg="#111827"
            ).grid(row=0, column=lnColumna, padx=(0, 8), pady=5, sticky="w")
            lnColumna += 1

            self.locboEstado = ttk.Combobox(
                lofrmHeader,
                textvariable=self.lovEstado,
                state="readonly",
                values=["Todos", "Ingresado", "Pagada", "Cancelada"],
                width=14
            )
            self.locboEstado.grid(row=0, column=lnColumna, padx=(0, 12), pady=5)
            self.locboEstado.bind("<<ComboboxSelected>>", lambda _e: self.loadOperations())
            lnColumna += 1

        tk.Button(
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
            command=self.loadOperations
        ).grid(row=0, column=lnColumna, padx=(0, 10), pady=5)
        lnColumna += 1

        tk.Button(
            lofrmHeader,
            text="Nuevo",
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
            command=self.openNewOperationWindow
        ).grid(row=0, column=lnColumna, padx=(10, 0), pady=5)

    def buildTable(self):
        lofrmTabla = tk.Frame(self.toParent, bg="white")
        lofrmTabla.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        taColumnas = (
            "Operacion",
            "CodigoOperacion",
            "Placa",
            "TipoVehiculo",
            "FechaIngreso",
            "Tiempo",
            "Servicios",
            "MontoParqueo",
            "MontoServicios",
            "Estado",
            "Acciones"
        )

        self.logrdOperaciones = ttk.Treeview(
            lofrmTabla,
            columns=taColumnas,
            show="headings",
            height=18
        )
        self.logrdOperaciones.pack(fill="both", expand=True, side="left")

        self.logrdOperaciones.heading("Operacion", text="ID")
        self.logrdOperaciones.heading("CodigoOperacion", text="Código")
        self.logrdOperaciones.heading("Placa", text="Placa")
        self.logrdOperaciones.heading("TipoVehiculo", text="Tipo")
        self.logrdOperaciones.heading("FechaIngreso", text="Ingreso")
        self.logrdOperaciones.heading("Tiempo", text="Tiempo")
        self.logrdOperaciones.heading("Servicios", text="Servicios")
        self.logrdOperaciones.heading("MontoParqueo", text="Parqueo")
        self.logrdOperaciones.heading("MontoServicios", text="Servicios Bs")
        self.logrdOperaciones.heading("Estado", text="Estado")
        self.logrdOperaciones.heading("Acciones", text="Acciones")

        self.logrdOperaciones.column("Operacion", width=60, anchor="center")
        self.logrdOperaciones.column("CodigoOperacion", width=110, anchor="center")
        self.logrdOperaciones.column("Placa", width=110, anchor="center")
        self.logrdOperaciones.column("TipoVehiculo", width=90, anchor="center")
        self.logrdOperaciones.column("FechaIngreso", width=150, anchor="center")
        self.logrdOperaciones.column("Tiempo", width=100, anchor="center")
        self.logrdOperaciones.column("Servicios", width=250, anchor="w")
        self.logrdOperaciones.column("MontoParqueo", width=100, anchor="center")
        self.logrdOperaciones.column("MontoServicios", width=110, anchor="center")
        self.logrdOperaciones.column("Estado", width=90, anchor="center")
        self.logrdOperaciones.column("Acciones", width=110, anchor="center")

        loscrVertical = ttk.Scrollbar(lofrmTabla, orient="vertical", command=self.logrdOperaciones.yview)
        loscrVertical.pack(side="right", fill="y")

        loscrHorizontal = ttk.Scrollbar(lofrmTabla, orient="horizontal", command=self.logrdOperaciones.xview)
        loscrHorizontal.pack(side="bottom", fill="x")

        self.logrdOperaciones.configure(
            yscrollcommand=loscrVertical.set,
            xscrollcommand=loscrHorizontal.set
        )

        self.logrdOperaciones.bind("<Double-1>", self.onDoubleClick)

    def obtenerEstadoFiltro(self):
        if not esAdministrador(self.txUsuarioData):
            return [gnEstadoOperacionIngresado]

        lcEstado = self.lovEstado.get().strip()

        if lcEstado == "Ingresado":
            return [gnEstadoOperacionIngresado]
        if lcEstado == "Pagada":
            return [gnEstadoOperacionPagada]
        if lcEstado == "Cancelada":
            return [gnEstadoOperacionCancelada]

        return [
            gnEstadoOperacionIngresado,
            gnEstadoOperacionPagada,
            gnEstadoOperacionCancelada
        ]

    def loadOperations(self):
        for toItem in self.logrdOperaciones.get_children():
            self.logrdOperaciones.delete(toItem)

        lcFiltroPlaca = self.lotxtBusquedaPlaca.get().strip().upper() if self.lotxtBusquedaPlaca else ""
        lcFiltroCodigo = self.lotxtBusquedaCodigo.get().strip().upper() if self.lotxtBusquedaCodigo else ""
        laEstados = self.obtenerEstadoFiltro()

        loConn = getConnection()
        loCursor = loConn.cursor()

        lcQuery = f"""
            SELECT
                O.Operacion,
                O.CodigoOperacion,
                O.FechaIngreso,
                O.FechaSalida,
                O.MontoParqueo,
                O.MontoServicios,
                O.Estado,
                V.NumeroPlaca,
                V.LetraPlaca,
                V.TipoVehiculo,
                O.Vehiculo
            FROM OPERACION O
            INNER JOIN VEHICULO V ON O.Vehiculo = V.Vehiculo
            WHERE O.Estado IN ({",".join(["?"] * len(laEstados))})
        """
        laParams = list(laEstados)

        if lcFiltroPlaca:
            lcQuery += """
                AND REPLACE(
                    REPLACE(
                        UPPER(IFNULL(V.NumeroPlaca, '') || IFNULL(V.LetraPlaca, '')),
                        ' ',
                        ''
                    ),
                    '-',
                    ''
                ) LIKE ?
            """
            laParams.append(f"%{limpiarPlacaParaBusqueda(lcFiltroPlaca)}%")

        if lcFiltroCodigo:
            lcQuery += " AND UPPER(IFNULL(O.CodigoOperacion, '')) LIKE ? "
            laParams.append(f"%{lcFiltroCodigo}%")

        lcQuery += " ORDER BY O.FechaIngreso DESC, O.Operacion DESC "

        loCursor.execute(lcQuery, laParams)
        laOperaciones = loCursor.fetchall()

        for toOperacion in laOperaciones:
            tnOperacion = toOperacion["Operacion"]
            lcCodigoOperacion = toOperacion["CodigoOperacion"] or ""
            lcPlaca = f"{toOperacion['NumeroPlaca'] or ''} {toOperacion['LetraPlaca'] or ''}".strip()
            lcTipoVehiculo = toOperacion["TipoVehiculo"] or ""
            lcFechaIngreso = toOperacion["FechaIngreso"] or ""
            lcTiempo = self.calculateOperationTime(
                toOperacion["FechaIngreso"],
                toOperacion["FechaSalida"]
            )
            lcServicios = self.getOperationServices(loCursor, tnOperacion)
            lnMontoParqueo = float(toOperacion["MontoParqueo"] or 0)
            lnMontoServicios = float(toOperacion["MontoServicios"] or 0)
            lcEstado = nombreEstadoOperacion(toOperacion["Estado"])

            if int(toOperacion["Estado"]) == gnEstadoOperacionIngresado:
                if tieneContratoActivoVehiculo(toOperacion["Vehiculo"]):
                    lcMontoParqueo = "Contrato activo"
                else:
                    lcMontoParqueo = "Bs 0.00"

                lcMontoServicios = "Bs 0.00"
            else:
                lcMontoParqueo = f"Bs {lnMontoParqueo:.2f}"
                lcMontoServicios = f"Bs {lnMontoServicios:.2f}"

            self.logrdOperaciones.insert(
                "",
                "end",
                values=(
                    tnOperacion,
                    lcCodigoOperacion,
                    lcPlaca,
                    lcTipoVehiculo,
                    lcFechaIngreso,
                    lcTiempo,
                    lcServicios,
                    lcMontoParqueo,
                    lcMontoServicios,
                    lcEstado,
                    "Doble clic"
                )
            )

        loConn.close()

    def calculateOperationTime(self, tcFechaIngreso, tcFechaSalida):
        if not tcFechaIngreso:
            return "N/D"

        try:
            loFechaIngreso = datetime.strptime(tcFechaIngreso, "%Y-%m-%d %H:%M:%S")

            if tcFechaSalida:
                loFechaSalida = datetime.strptime(tcFechaSalida, "%Y-%m-%d %H:%M:%S")
            else:
                loFechaSalida = datetime.now()

            tnMinutos = max(1, int((loFechaSalida - loFechaIngreso).total_seconds() / 60))
            return formatMinutes(tnMinutos)
        except Exception:
            return "N/D"

    def getOperationServices(self, loCursor, tnOperacion):
        loCursor.execute("""
            SELECT
                S.Nombre,
                OS.Cantidad
            FROM OPERACIONSERVICIO OS
            INNER JOIN SERVICIO S ON OS.Servicio = S.Servicio
            WHERE OS.Operacion = ?
            ORDER BY S.Nombre ASC
        """, (tnOperacion,))
        laRows = loCursor.fetchall()

        if not laRows:
            return "Solo parqueo"

        laServicios = []
        for toRow in laRows:
            lcNombre = toRow["Nombre"] or ""
            tnCantidad = int(toRow["Cantidad"] or 0)

            if tnCantidad > 1:
                laServicios.append(f"{lcNombre} x{tnCantidad}")
            else:
                laServicios.append(lcNombre)

        return ", ".join(laServicios)

    def onDoubleClick(self, toEvent):
        taSeleccionado = self.logrdOperaciones.selection()
        if not taSeleccionado:
            return

        taValores = self.logrdOperaciones.item(taSeleccionado[0], "values")
        if not taValores:
            return

        tnOperacion = int(taValores[0])
        lcCodigoOperacion = taValores[1]
        lcEstado = taValores[9]

        loWindowAcciones = tk.Toplevel(self.toParent)
        loWindowAcciones.title("Acciones")
        loWindowAcciones.geometry("360x320")
        loWindowAcciones.resizable(False, False)
        loWindowAcciones.configure(bg="white")
        loWindowAcciones.grab_set()

        tk.Label(
            loWindowAcciones,
            text=f"Operación #{tnOperacion}",
            font=("Arial", 14, "bold"),
            bg="white",
            fg="#111827"
        ).pack(pady=(20, 8))

        tk.Label(
            loWindowAcciones,
            text=f"Código: {lcCodigoOperacion}",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#2563eb"
        ).pack(pady=(0, 16))

        if lcEstado == "Ingresado":
            tk.Button(
                loWindowAcciones,
                text="Editar",
                font=("Arial", 11, "bold"),
                width=18,
                bg="#f59e0b",
                fg="white",
                bd=0,
                relief="flat",
                cursor="hand2",
                command=lambda: self.editOperation(tnOperacion, loWindowAcciones)
            ).pack(pady=6)

            tk.Button(
                loWindowAcciones,
                text="Cobrar",
                font=("Arial", 11, "bold"),
                width=18,
                bg="#16a34a",
                fg="white",
                bd=0,
                relief="flat",
                cursor="hand2",
                command=lambda: self.openChargeWindow(tnOperacion, loWindowAcciones)
            ).pack(pady=6)

            tk.Button(
                loWindowAcciones,
                text="Cancelar operación",
                font=("Arial", 11, "bold"),
                width=18,
                bg="#dc2626",
                fg="white",
                bd=0,
                relief="flat",
                cursor="hand2",
                command=lambda: self.cancelOperation(tnOperacion, loWindowAcciones)
            ).pack(pady=6)

        tk.Button(
            loWindowAcciones,
            text="Reimprimir ticket",
            font=("Arial", 11, "bold"),
            width=18,
            bg="#2563eb",
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            command=lambda: self.reprintTicket(tnOperacion)
        ).pack(pady=6)

        tk.Button(
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
        ).pack(pady=6)

    def openNewOperationWindow(self):
        OperationFormWindow(self, self.txUsuarioData)

    def editOperation(self, tnOperacion, loWindowAcciones=None):
        if loWindowAcciones:
            loWindowAcciones.destroy()
        OperationFormWindow(self, self.txUsuarioData, tnOperacion=tnOperacion)

    def cancelOperation(self, tnOperacion, loWindowAcciones=None):
        if loWindowAcciones:
            loWindowAcciones.destroy()
        CancelOperationWindow(self, self.txUsuarioData, tnOperacion)

    def openChargeWindow(self, tnOperacion, loWindowAcciones=None):
        if loWindowAcciones:
            loWindowAcciones.destroy()

        loConn = getConnection()
        loCursor = loConn.cursor()

        try:
            loCursor.execute("""
                SELECT
                    O.Operacion,
                    O.CodigoOperacion,
                    O.FechaIngreso,
                    O.Tarifa,
                    O.Estado,
                    O.Vehiculo,
                    V.NumeroPlaca,
                    V.LetraPlaca
                FROM OPERACION O
                INNER JOIN VEHICULO V ON O.Vehiculo = V.Vehiculo
                WHERE O.Operacion = ?
                  AND O.Estado = ?
            """, (tnOperacion, gnEstadoOperacionIngresado))
            toOperacion = loCursor.fetchone()

            if not toOperacion:
                messagebox.showwarning("Aviso", "La operación ya no está en estado ingresado.")
                return

            loCursor.execute("""
                SELECT COALESCE(SUM(Subtotal), 0) AS TotalServicios
                FROM OPERACIONSERVICIO
                WHERE Operacion = ?
            """, (tnOperacion,))
            lnMontoServicios = float(loCursor.fetchone()["TotalServicios"] or 0)

        finally:
            loConn.close()

        lcFechaSalida = getFechaHoraActualTexto()

        llTieneContratoActivo = tieneContratoActivoVehiculo(toOperacion["Vehiculo"])

        if llTieneContratoActivo:
            lnMontoParqueo = 0.0
            lcConcepto = f"Cobro servicios operación {toOperacion['CodigoOperacion']} (parqueo cubierto por contrato)"
        else:
            lnMontoParqueo = self.calculateParkingAmount(
                toOperacion["Tarifa"],
                toOperacion["FechaIngreso"],
                lcFechaSalida
            )
            lcConcepto = f"Cobro operación {toOperacion['CodigoOperacion']}"

        lnMontoTotal = round(lnMontoParqueo + lnMontoServicios, 2)

        def onPagoGuardado(_tnPago):
            self.finalizeChargedOperation(
                tnOperacion=tnOperacion,
                tcFechaSalida=lcFechaSalida,
                tnMontoParqueo=round(lnMontoParqueo, 2),
                tnMontoServicios=round(lnMontoServicios, 2)
            )

        FrmCobros(
            self.toParent,
            self.txUsuarioData,
            tnTipoDetalle=gnTipoDetalleOperacion,
            tnDetalle=tnOperacion,
            tcConcepto=lcConcepto,
            tnMonto=lnMontoTotal,
            tfOnSave=onPagoGuardado
        )

    def finalizeChargedOperation(self, tnOperacion, tcFechaSalida, tnMontoParqueo, tnMontoServicios):
        loConn = getConnection()
        loCursor = loConn.cursor()

        try:
            tnUsr = obtenerUsuarioActualId(self.txUsuarioData)

            loCursor.execute("""
                UPDATE OPERACION
                SET
                    FechaSalida = ?,
                    MontoParqueo = ?,
                    MontoServicios = ?,
                    Estado = ?,
                    Usr = ?,
                    UsrFecha = date('now','localtime'),
                    UsrHora = time('now','localtime'),
                    FechaModificacion = datetime('now','localtime')
                WHERE Operacion = ?
            """, (
                tcFechaSalida,
                tnMontoParqueo,
                tnMontoServicios,
                gnEstadoOperacionPagada,
                tnUsr,
                tnOperacion
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
                    ?, ?, ?, ?, ?, ?,
                    ?,
                    date('now','localtime'),
                    time('now','localtime'),
                    datetime('now','localtime'),
                    datetime('now','localtime')
                )
            """, (
                tnUsr,
                "COBRAR_OPERACION",
                "OPERACION",
                tnOperacion,
                f"Se cobró la operación {tnOperacion}",
                getFechaHoraActualTexto(),
                tnUsr
            ))

            loConn.commit()
            self.loadOperations()

        except Exception as toError:
            loConn.rollback()
            messagebox.showerror("Error", f"No se pudo cerrar la operación cobrada.\n{str(toError)}")
        finally:
            loConn.close()

    def reprintTicket(self, tnOperacion):
        loConn = getConnection()
        loCursor = loConn.cursor()

        try:
            loCursor.execute("""
                SELECT
                    O.CodigoOperacion,
                    O.FechaIngreso,
                    V.NumeroPlaca,
                    V.LetraPlaca
                FROM OPERACION O
                INNER JOIN VEHICULO V ON O.Vehiculo = V.Vehiculo
                WHERE O.Operacion = ?
                LIMIT 1
            """, (tnOperacion,))
            toDatos = loCursor.fetchone()

            if not toDatos:
                messagebox.showwarning("No encontrado", "No se encontró la operación para reimprimir.")
                return

            loFechaIngreso = datetime.strptime(toDatos["FechaIngreso"], "%Y-%m-%d %H:%M:%S")
            lcFechaTicket = loFechaIngreso.strftime("%d/%m/%Y")
            lcHoraTicket = loFechaIngreso.strftime("%H:%M")
            lcPlaca = f"{toDatos['NumeroPlaca'] or ''} {toDatos['LetraPlaca'] or ''}".strip()

            imprimir_ticket(
                codigo=toDatos["CodigoOperacion"],
                placa=lcPlaca,
                fecha=lcFechaTicket,
                hora_ingreso=lcHoraTicket
            )

            messagebox.showinfo(
                "Ticket reimpreso",
                f"Se reimprimió correctamente el ticket.\n\nCódigo: {toDatos['CodigoOperacion']}"
            )

        except Exception as toError:
            messagebox.showerror(
                "Error",
                f"No se pudo reimprimir el ticket.\n{str(toError)}"
            )

        finally:
            loConn.close()

    def calculateParkingAmount(self, tnTarifa, tcFechaIngreso, tcFechaSalida):
        if not tcFechaIngreso:
            return 0.0

        loFechaIngreso = datetime.strptime(tcFechaIngreso, "%Y-%m-%d %H:%M:%S")
        loFechaSalida = datetime.strptime(tcFechaSalida, "%Y-%m-%d %H:%M:%S")
        tnMinutos = max(1, int((loFechaSalida - loFechaIngreso).total_seconds() / 60))

        loConn = getConnection()
        loCursor = loConn.cursor()

        try:
            loCursor.execute("""
                SELECT Monto
                FROM TARIFADETALLE
                WHERE Tarifa = ?
                  AND Estado = ?
                  AND TipoCobro = 1
                  AND ? BETWEEN TiempoInicio AND TiempoFin
                ORDER BY TiempoInicio ASC
                LIMIT 1
            """, (tnTarifa, gnEstadoGeneralActivo, tnMinutos))
            toFila = loCursor.fetchone()

            if toFila:
                return float(toFila["Monto"] or 0)

            loCursor.execute("""
                SELECT Monto
                FROM TARIFADETALLE
                WHERE Tarifa = ?
                  AND Estado = ?
                  AND TipoCobro = 1
                ORDER BY TiempoFin DESC
                LIMIT 1
            """, (tnTarifa, gnEstadoGeneralActivo))
            toUltimaFila = loCursor.fetchone()

            if toUltimaFila:
                return float(toUltimaFila["Monto"] or 0)

            return 0.0

        finally:
            loConn.close()

    def run(self):
        pass


class OperationFormWindow:
    def __init__(self, toView, txUsuarioData, tnOperacion=None):
        self.toView = toView
        self.txUsuarioData = txUsuarioData or {}
        self.tnOperacion = tnOperacion

        self.loWindow = tk.Toplevel()
        self.loWindow.title("Nueva operación" if tnOperacion is None else "Editar operación")
        self.loWindow.geometry("620x620")
        self.loWindow.minsize(580, 580)
        self.loWindow.resizable(True, True)
        self.loWindow.configure(bg="white")
        self.loWindow.grab_set()

        self.lotxtPlacaNumero = None
        self.lotxtPlacaLetras = None
        self.lovTipoVehiculo = tk.StringVar(value="auto")
        self.lovTarifaTexto = tk.StringVar()
        self.lstServicios = None

        self.tnVehiculoCargado = None
        self.gnTarifaAutomatica = None
        self.laServicios = obtenerServiciosActivos()

        self.buildUi()

        if self.tnOperacion is not None:
            self.loadData()
        else:
            self.loadTarifaAutomatica()

    def buildUi(self):
        lofrmContainer = tk.Frame(self.loWindow, bg="white")
        lofrmContainer.pack(fill="both", expand=True, padx=20, pady=20)

        lcTitulo = "Nueva operación" if self.tnOperacion is None else "Editar operación"

        tk.Label(
            lofrmContainer,
            text=lcTitulo,
            font=("Arial", 16, "bold"),
            bg="white",
            fg="#111827"
        ).pack(pady=(0, 15))

        tk.Label(
            lofrmContainer,
            text="Vehículo / Placa *",
            font=("Arial", 11, "bold"),
            bg="white"
        ).pack(anchor="w", pady=(0, 5))

        lofrmPlaca = tk.Frame(lofrmContainer, bg="white")
        lofrmPlaca.pack(fill="x", pady=(0, 10))

        tk.Label(lofrmPlaca, text="Número", font=("Arial", 10), bg="white").pack(side="left", padx=(0, 6))
        self.lotxtPlacaNumero = tk.Entry(lofrmPlaca, font=("Arial", 11), width=10)
        self.lotxtPlacaNumero.pack(side="left", padx=(0, 16))
        self.lotxtPlacaNumero.bind("<KeyRelease>", self.onlyNumbersPlate)

        tk.Label(lofrmPlaca, text="Letras", font=("Arial", 10), bg="white").pack(side="left", padx=(0, 6))
        self.lotxtPlacaLetras = tk.Entry(lofrmPlaca, font=("Arial", 11), width=8)
        self.lotxtPlacaLetras.pack(side="left")
        self.lotxtPlacaLetras.bind("<KeyRelease>", self.onlyLettersPlate)

        tk.Label(
            lofrmContainer,
            text="Formato referencial: 1023 ABC",
            font=("Arial", 9),
            bg="white",
            fg="#6b7280"
        ).pack(anchor="w", pady=(0, 12))

        tk.Label(
            lofrmContainer,
            text="Tipo de vehículo *",
            font=("Arial", 11, "bold"),
            bg="white"
        ).pack(anchor="w", pady=(0, 5))

        lofrmTipoVehiculo = tk.Frame(lofrmContainer, bg="white")
        lofrmTipoVehiculo.pack(fill="x", pady=(0, 12))

        tk.Radiobutton(
            lofrmTipoVehiculo,
            text="Auto",
            variable=self.lovTipoVehiculo,
            value="auto",
            bg="white",
            font=("Arial", 11),
            command=self.loadTarifaAutomatica
        ).pack(side="left", padx=(0, 16))

        tk.Radiobutton(
            lofrmTipoVehiculo,
            text="Moto",
            variable=self.lovTipoVehiculo,
            value="moto",
            bg="white",
            font=("Arial", 11),
            command=self.loadTarifaAutomatica
        ).pack(side="left", padx=(0, 16))

        tk.Label(
            lofrmContainer,
            text="Tarifa asignada",
            font=("Arial", 11, "bold"),
            bg="white"
        ).pack(anchor="w", pady=(0, 5))

        tk.Entry(
            lofrmContainer,
            textvariable=self.lovTarifaTexto,
            font=("Arial", 11),
            state="readonly"
        ).pack(fill="x", pady=(0, 12))

        tk.Label(
            lofrmContainer,
            text="Servicios adicionales",
            font=("Arial", 11, "bold"),
            bg="white"
        ).pack(anchor="w", pady=(0, 5))

        lofrmServicios = tk.Frame(lofrmContainer, bg="white")
        lofrmServicios.pack(fill="both", expand=True, pady=(0, 16))

        self.lstServicios = tk.Listbox(
            lofrmServicios,
            selectmode="multiple",
            font=("Arial", 11),
            height=10,
            exportselection=False
        )
        self.lstServicios.pack(side="left", fill="both", expand=True)

        loscrServicios = ttk.Scrollbar(lofrmServicios, orient="vertical", command=self.lstServicios.yview)
        loscrServicios.pack(side="right", fill="y")
        self.lstServicios.configure(yscrollcommand=loscrServicios.set)

        for toServicio in self.laServicios:
            self.lstServicios.insert("end", f"{toServicio['Nombre']} - Bs {float(toServicio['Precio'] or 0):.2f}")

        tk.Label(
            lofrmContainer,
            text="Selecciona solo los servicios adicionales. El parqueo se cobra automáticamente.",
            font=("Arial", 9),
            bg="white",
            fg="#6b7280"
        ).pack(anchor="w", pady=(0, 12))

        lofrmBotones = tk.Frame(lofrmContainer, bg="white")
        lofrmBotones.pack(pady=10)

        tk.Button(
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
        ).grid(row=0, column=0, padx=10)

        tk.Button(
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
        ).grid(row=0, column=1, padx=10)

    def onlyNumbersPlate(self, _e=None):
        lcValor = self.lotxtPlacaNumero.get()
        lcFiltrado = "".join(tcCaracter for tcCaracter in lcValor if tcCaracter.isdigit())[:4]
        if lcValor != lcFiltrado:
            self.lotxtPlacaNumero.delete(0, "end")
            self.lotxtPlacaNumero.insert(0, lcFiltrado)

    def onlyLettersPlate(self, _e=None):
        lcValor = self.lotxtPlacaLetras.get()
        lcFiltrado = "".join(tcCaracter for tcCaracter in lcValor if tcCaracter.isalpha()).upper()[:3]
        if lcValor != lcFiltrado:
            self.lotxtPlacaLetras.delete(0, "end")
            self.lotxtPlacaLetras.insert(0, lcFiltrado)

    def validatePlate(self):
        lcNumero = self.lotxtPlacaNumero.get().strip()
        lcLetras = self.lotxtPlacaLetras.get().strip().upper()

        if not lcNumero or not lcLetras:
            raise ValueError("Debe ingresar la placa completa.")

        if not lcNumero.isdigit():
            raise ValueError("La parte numérica de la placa solo debe contener números.")

        if len(lcNumero) < 2 or len(lcNumero) > 4:
            raise ValueError("La parte numérica de la placa debe tener entre 2 y 4 dígitos.")

        if not lcLetras.isalpha():
            raise ValueError("La parte de letras de la placa solo debe contener letras.")

        if len(lcLetras) != 3:
            raise ValueError("La placa debe tener exactamente 3 letras.")

        return lcNumero, lcLetras

    def loadTarifaAutomatica(self):
        self.gnTarifaAutomatica = None
        self.lovTarifaTexto.set("")

        toTarifa = obtenerTarifaParqueoPorTipoVehiculo(self.lovTipoVehiculo.get())
        if not toTarifa:
            self.lovTarifaTexto.set("No existe tarifa de parqueo para este tipo")
            return

        self.gnTarifaAutomatica = toTarifa["Tarifa"]
        self.lovTarifaTexto.set(f"{toTarifa['Nombre']} | {toTarifa['TipoVehiculo']}")

    def loadData(self):
        loConn = getConnection()
        loCursor = loConn.cursor()

        loCursor.execute("""
            SELECT
                O.Vehiculo,
                O.Tarifa,
                O.CodigoOperacion,
                O.Estado,
                V.NumeroPlaca,
                V.LetraPlaca,
                V.TipoVehiculo
            FROM OPERACION O
            INNER JOIN VEHICULO V ON O.Vehiculo = V.Vehiculo
            WHERE O.Operacion = ?
        """, (self.tnOperacion,))
        toRow = loCursor.fetchone()

        if not toRow:
            loConn.close()
            messagebox.showerror("Error", "No se encontró la operación.")
            self.loWindow.destroy()
            return

        if int(toRow["Estado"]) != gnEstadoOperacionIngresado:
            loConn.close()
            messagebox.showwarning("Aviso", "Solo se puede editar una operación ingresada.")
            self.loWindow.destroy()
            return

        self.tnVehiculoCargado = toRow["Vehiculo"]

        self.lotxtPlacaNumero.insert(0, toRow["NumeroPlaca"] or "")
        self.lotxtPlacaLetras.insert(0, toRow["LetraPlaca"] or "")
        self.lovTipoVehiculo.set(toRow["TipoVehiculo"] or "auto")
        self.loadTarifaAutomatica()

        loCursor.execute("""
            SELECT Servicio
            FROM OPERACIONSERVICIO
            WHERE Operacion = ?
        """, (self.tnOperacion,))
        laServiciosOperacion = {toFila["Servicio"] for toFila in loCursor.fetchall()}

        loConn.close()

        for lnIndex, toServicio in enumerate(self.laServicios):
            if toServicio["Servicio"] in laServiciosOperacion:
                self.lstServicios.selection_set(lnIndex)

    def getSelectedServices(self):
        laSeleccion = self.lstServicios.curselection()
        laServiciosSeleccionados = []

        for lnIndex in laSeleccion:
            if 0 <= lnIndex < len(self.laServicios):
                laServiciosSeleccionados.append(self.laServicios[lnIndex])

        return laServiciosSeleccionados

    def confirmSave(self):
        llConfirmado = messagebox.askyesno(
            "Confirmar guardado",
            "¿Desea guardar esta operación?"
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
        laServiciosSeleccionados = self.getSelectedServices()

        if not self.gnTarifaAutomatica:
            messagebox.showwarning("Dato requerido", "No existe una tarifa automática válida.")
            return

        loConn = getConnection()
        loCursor = loConn.cursor()

        try:
            tnUsr = obtenerUsuarioActualId(self.txUsuarioData)

            if self.tnOperacion is None:
                tnVehiculo = self.getOrCreateVehicleForOperation(
                    loCursor,
                    lcNumeroPlaca,
                    lcLetraPlaca,
                    lcTipoVehiculo,
                    tnUsr
                )
                lcCodigoOperacion = self.generateOperationCode(loCursor)

                loCursor.execute("""
                    INSERT INTO OPERACION (
                        CodigoOperacion,
                        Vehiculo,
                        Tarifa,
                        FechaIngreso,
                        MontoParqueo,
                        MontoServicios,
                        Estado,
                        Usr,
                        UsrFecha,
                        UsrHora,
                        FechaCreacion,
                        FechaModificacion
                    )
                    VALUES (
                        ?, ?, ?,
                        datetime('now','localtime'),
                        0, 0, ?,
                        ?,
                        date('now','localtime'),
                        time('now','localtime'),
                        datetime('now','localtime'),
                        datetime('now','localtime')
                    )
                """, (
                    lcCodigoOperacion,
                    tnVehiculo,
                    self.gnTarifaAutomatica,
                    gnEstadoOperacionIngresado,
                    tnUsr
                ))

                tnOperacionGuardada = loCursor.lastrowid

                self.saveOperationServices(loCursor, tnOperacionGuardada, laServiciosSeleccionados)

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
                    "CREAR_OPERACION",
                    "OPERACION",
                    tnOperacionGuardada,
                    f"Se creó la operación '{lcCodigoOperacion}'",
                    getFechaHoraActualTexto(),
                    tnUsr
                ))

            else:
                tnVehiculo = self.getOrCreateVehicleForOperation(
                    loCursor,
                    lcNumeroPlaca,
                    lcLetraPlaca,
                    lcTipoVehiculo,
                    tnUsr
                )

                if int(tnVehiculo) != int(self.tnVehiculoCargado):
                    raise ValueError(
                        "No puedes cambiar el vehículo desde operaciones. Hazlo en Vehículos / Clientes."
                    )

                loCursor.execute("""
                    UPDATE OPERACION
                    SET
                        Tarifa = ?,
                        Usr = ?,
                        UsrFecha = date('now','localtime'),
                        UsrHora = time('now','localtime'),
                        FechaModificacion = datetime('now','localtime')
                    WHERE Operacion = ?
                """, (
                    self.gnTarifaAutomatica,
                    tnUsr,
                    self.tnOperacion
                ))

                loCursor.execute("DELETE FROM OPERACIONSERVICIO WHERE Operacion = ?", (self.tnOperacion,))
                self.saveOperationServices(loCursor, self.tnOperacion, laServiciosSeleccionados)

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
                    "EDITAR_OPERACION",
                    "OPERACION",
                    self.tnOperacion,
                    f"Se editó la operación '{self.tnOperacion}'",
                    getFechaHoraActualTexto(),
                    tnUsr
                ))

            loConn.commit()
            messagebox.showinfo("Guardado", "Operación guardada correctamente.")
            self.toView.loadOperations()
            self.loWindow.destroy()

        except Exception as toError:
            loConn.rollback()
            messagebox.showerror("Error", f"No se pudo guardar la operación.\n{str(toError)}")

        finally:
            loConn.close()

    def saveOperationServices(self, loCursor, tnOperacion, laServiciosSeleccionados):
        tnUsr = obtenerUsuarioActualId(self.txUsuarioData)

        for toServicio in laServiciosSeleccionados:
            lnPrecio = float(toServicio["Precio"] or 0)

            loCursor.execute("""
                INSERT INTO OPERACIONSERVICIO (
                    Operacion,
                    Servicio,
                    Cantidad,
                    PrecioUnitario,
                    Subtotal,
                    Usr,
                    UsrFecha,
                    UsrHora,
                    FechaCreacion,
                    FechaModificacion
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?,
                    date('now','localtime'),
                    time('now','localtime'),
                    datetime('now','localtime'),
                    datetime('now','localtime')
                )
            """, (
                tnOperacion,
                toServicio["Servicio"],
                1,
                lnPrecio,
                lnPrecio,
                tnUsr
            ))

    def getOrCreateVehicleForOperation(self, loCursor, tcNumeroPlaca, tcLetraPlaca, tcTipoVehiculo, tnUsr):
        loCursor.execute("""
            SELECT Vehiculo, TipoVehiculo, Estado
            FROM VEHICULO
            WHERE NumeroPlaca = ?
            AND LetraPlaca = ?
        """, (tcNumeroPlaca, tcLetraPlaca))
        toRow = loCursor.fetchone()

        if toRow:
            if int(toRow["Estado"]) != gnEstadoGeneralActivo:
                raise ValueError("El vehículo está inactivo.")

            lcTipoVehiculoRegistrado = (toRow["TipoVehiculo"] or "").strip().lower()
            lcTipoVehiculoFormulario = (tcTipoVehiculo or "").strip().lower()

            if lcTipoVehiculoRegistrado != lcTipoVehiculoFormulario:
                raise ValueError(
                    "La placa ya está registrada con otro tipo de vehículo."
                )

            return int(toRow["Vehiculo"])

        loCursor.execute("""
            INSERT INTO VEHICULO (
                NumeroPlaca,
                LetraPlaca,
                TipoVehiculo,
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
            tcNumeroPlaca,
            tcLetraPlaca,
            tcTipoVehiculo,
            gnEstadoGeneralActivo,
            tnUsr
        ))

        return int(loCursor.lastrowid)

    def generateOperationCode(self, loCursor):
        loCursor.execute("SELECT IFNULL(MAX(Operacion), 0) + 1 AS Siguiente FROM OPERACION")
        toFila = loCursor.fetchone()
        lnSiguiente = int(toFila["Siguiente"] or 1)
        return f"OP-{lnSiguiente:04d}"

    def run(self):
        pass


class CancelOperationWindow:
    def __init__(self, toView, txUsuarioData, tnOperacion):
        self.toView = toView
        self.txUsuarioData = txUsuarioData or {}
        self.tnOperacion = tnOperacion

        self.loWindow = tk.Toplevel()
        self.loWindow.title("Cancelar operación")
        self.loWindow.geometry("420x260")
        self.loWindow.resizable(False, False)
        self.loWindow.configure(bg="white")
        self.loWindow.grab_set()

        self.lotxtMotivo = None
        self.buildUi()

    def buildUi(self):
        tk.Label(
            self.loWindow,
            text="Cancelar operación",
            font=("Arial", 16, "bold"),
            bg="white",
            fg="#111827"
        ).pack(pady=(20, 12))

        tk.Label(
            self.loWindow,
            text="Motivo de cancelación *",
            font=("Arial", 11, "bold"),
            bg="white"
        ).pack(anchor="w", padx=30)

        self.lotxtMotivo = tk.Text(self.loWindow, font=("Arial", 11), height=6)
        self.lotxtMotivo.pack(fill="x", padx=30, pady=(8, 16))

        lofrmBotones = tk.Frame(self.loWindow, bg="white")
        lofrmBotones.pack(pady=10)

        tk.Button(
            lofrmBotones,
            text="Confirmar cancelación",
            font=("Arial", 11, "bold"),
            bg="#dc2626",
            fg="white",
            bd=0,
            relief="flat",
            padx=16,
            pady=8,
            cursor="hand2",
            command=self.confirmCancel
        ).grid(row=0, column=0, padx=8)

        tk.Button(
            lofrmBotones,
            text="Cerrar",
            font=("Arial", 11, "bold"),
            bg="#6b7280",
            fg="white",
            bd=0,
            relief="flat",
            padx=16,
            pady=8,
            cursor="hand2",
            command=self.loWindow.destroy
        ).grid(row=0, column=1, padx=8)

    def confirmCancel(self):
        lcMotivo = self.lotxtMotivo.get("1.0", "end").strip()

        if not lcMotivo:
            messagebox.showwarning("Dato requerido", "Debe ingresar el motivo de cancelación.")
            return

        loConn = getConnection()
        loCursor = loConn.cursor()

        try:
            tnUsr = obtenerUsuarioActualId(self.txUsuarioData)

            loCursor.execute("""
                UPDATE OPERACION
                SET
                    Estado = ?,
                    FechaSalida = datetime('now','localtime'),
                    Usr = ?,
                    UsrFecha = date('now','localtime'),
                    UsrHora = time('now','localtime'),
                    FechaModificacion = datetime('now','localtime')
                WHERE Operacion = ? AND Estado = ?
            """, (
                gnEstadoOperacionCancelada,
                tnUsr,
                self.tnOperacion,
                gnEstadoOperacionIngresado
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
                    ?, ?, ?, ?, ?, ?,
                    ?,
                    date('now','localtime'),
                    time('now','localtime'),
                    datetime('now','localtime'),
                    datetime('now','localtime')
                )
            """, (
                tnUsr,
                "CANCELAR_OPERACION",
                "OPERACION",
                self.tnOperacion,
                f"Se canceló la operación {self.tnOperacion}. Motivo: {lcMotivo}",
                getFechaHoraActualTexto(),
                tnUsr
            ))

            loConn.commit()
            messagebox.showinfo("Operación cancelada", "La operación fue cancelada correctamente.")
            self.loWindow.destroy()
            self.toView.loadOperations()

        except Exception as toError:
            loConn.rollback()
            messagebox.showerror("Error", f"No se pudo cancelar la operación.\n{str(toError)}")

        finally:
            loConn.close()

    def run(self):
        pass