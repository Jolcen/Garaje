import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import calendar

from database.db import getConnection
from modulos.frmCobros import FrmCobros


gnEstadoContratoPendiente = 0
gnEstadoContratoActivo = 1
gnEstadoContratoFinalizado = 2
gnEstadoContratoCancelado = 3

gnTipoDetalleContrato = 2

gxEstadosContrato = {
    gnEstadoContratoPendiente: "Pendiente",
    gnEstadoContratoActivo: "Activo",
    gnEstadoContratoFinalizado: "Finalizado",
    gnEstadoContratoCancelado: "Cancelado",
}

gxEstadosContratoInv = {tcValor: tnClave for tnClave, tcValor in gxEstadosContrato.items()}


def getFechaActualStr():
    return datetime.now().strftime("%Y-%m-%d")


def getFechaHoraActualStr():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def sumarMeses(tcFechaInicio, tnMeses):
    loFecha = datetime.strptime(tcFechaInicio, "%Y-%m-%d")
    lnAnio = loFecha.year + (loFecha.month - 1 + tnMeses) // 12
    lnMes = (loFecha.month - 1 + tnMeses) % 12 + 1
    lnDia = min(loFecha.day, calendar.monthrange(lnAnio, lnMes)[1])
    loNuevaFecha = loFecha.replace(year=lnAnio, month=lnMes, day=lnDia)
    return loNuevaFecha.strftime("%Y-%m-%d")


def formatearCliente(toRow):
    lcNombres = (toRow["Nombres"] or "").strip()
    lcApellidos = (toRow["Apellidos"] or "").strip()
    lcDocumento = (toRow["DocumentoIdentidad"] or "").strip()

    lcNombreCompleto = f"{lcNombres} {lcApellidos}".strip()

    if lcDocumento:
        return f"{lcNombreCompleto} | CI: {lcDocumento}"

    return lcNombreCompleto


def formatearVehiculo(toRow):
    lcNumeroPlaca = (toRow["NumeroPlaca"] or "").strip()
    lcLetraPlaca = (toRow["LetraPlaca"] or "").strip()
    lcTipoVehiculo = (toRow["TipoVehiculo"] or "").strip()
    lcMarca = (toRow["Marca"] or "").strip()
    lcColor = (toRow["Color"] or "").strip()

    lcPlaca = f"{lcNumeroPlaca} {lcLetraPlaca}".strip()
    lcExtra = " | ".join([tcValor for tcValor in [lcMarca, lcColor] if tcValor]).strip()

    if lcExtra:
        return f"{lcPlaca} | {lcTipoVehiculo} | {lcExtra}"

    return f"{lcPlaca} | {lcTipoVehiculo}"


def obtenerVehiculos():
    loConn = getConnection()
    loCursor = loConn.cursor()

    loCursor.execute("""
        SELECT
            V.Vehiculo,
            V.Cliente,
            V.NumeroPlaca,
            V.LetraPlaca,
            V.TipoVehiculo,
            V.Marca,
            V.Color,
            C.Nombres,
            C.Apellidos,
            C.DocumentoIdentidad
        FROM VEHICULO V
        LEFT JOIN CLIENTE C ON C.Cliente = V.Cliente
        WHERE V.Estado = 1
        ORDER BY V.NumeroPlaca, V.LetraPlaca
    """)

    laFilas = loCursor.fetchall()
    loConn.close()
    return laFilas


def obtenerTarifaMensualPorVehiculo(tnVehiculo):
    loConn = getConnection()
    loCursor = loConn.cursor()

    loCursor.execute("""
        SELECT T.Tarifa, T.Nombre, T.TipoVehiculo
        FROM VEHICULO V
        INNER JOIN TARIFA T
            ON T.TipoVehiculo = V.TipoVehiculo
           AND T.Estado = 1
        WHERE V.Vehiculo = ?
          AND V.Estado = 1
          AND UPPER(T.Nombre) LIKE 'MENSUAL%'
        ORDER BY T.Tarifa ASC
        LIMIT 1
    """, (tnVehiculo,))
    toFila = loCursor.fetchone()
    loConn.close()
    return toFila


def obtenerMontoMensualTarifa(tnTarifa):
    loConn = getConnection()
    loCursor = loConn.cursor()

    loCursor.execute("""
        SELECT Monto
        FROM TARIFADETALLE
        WHERE Tarifa = ?
          AND TipoCobro = 3
          AND Estado = 1
        ORDER BY TarifaDetalle ASC
        LIMIT 1
    """, (tnTarifa,))
    toFila = loCursor.fetchone()
    loConn.close()

    if not toFila:
        return None

    return float(toFila["Monto"])


def generarCodigoContrato():
    loConn = getConnection()
    loCursor = loConn.cursor()

    loCursor.execute("""
        SELECT IFNULL(MAX(Contrato), 0) + 1 AS Siguiente
        FROM CONTRATO
    """)
    toFila = loCursor.fetchone()
    loConn.close()

    lnSiguiente = int(toFila["Siguiente"]) if toFila else 1
    return f"CTR-{lnSiguiente:04d}"


def obtenerContratoPorId(tnContrato):
    loConn = getConnection()
    loCursor = loConn.cursor()

    loCursor.execute("""
        SELECT
            C.Contrato,
            C.Cliente,
            C.Vehiculo,
            C.Tarifa,
            C.CodigoContrato,
            C.FechaInicio,
            C.FechaFin,
            C.DuracionMeses,
            C.Observacion,
            C.Estado,
            CL.Nombres,
            CL.Apellidos,
            CL.DocumentoIdentidad,
            V.NumeroPlaca,
            V.LetraPlaca,
            V.TipoVehiculo,
            V.Marca,
            V.Color,
            T.Nombre AS NombreTarifa
        FROM CONTRATO C
        INNER JOIN CLIENTE CL ON CL.Cliente = C.Cliente
        INNER JOIN VEHICULO V ON V.Vehiculo = C.Vehiculo
        INNER JOIN TARIFA T ON T.Tarifa = C.Tarifa
        WHERE C.Contrato = ?
    """, (tnContrato,))

    toFila = loCursor.fetchone()
    loConn.close()
    return toFila


def obtenerContratos(tcBusqueda="", tnEstado=None):
    loConn = getConnection()
    loCursor = loConn.cursor()

    lcQuery = """
        SELECT
            C.Contrato,
            C.Cliente,
            C.Vehiculo,
            C.Tarifa,
            C.CodigoContrato,
            C.FechaInicio,
            C.FechaFin,
            C.DuracionMeses,
            C.Observacion,
            C.Estado,
            CL.Nombres,
            CL.Apellidos,
            CL.DocumentoIdentidad,
            V.NumeroPlaca,
            V.LetraPlaca,
            V.TipoVehiculo,
            T.Nombre AS NombreTarifa
        FROM CONTRATO C
        INNER JOIN CLIENTE CL ON CL.Cliente = C.Cliente
        INNER JOIN VEHICULO V ON V.Vehiculo = C.Vehiculo
        INNER JOIN TARIFA T ON T.Tarifa = C.Tarifa
        WHERE 1 = 1
    """
    laParams = []

    if tcBusqueda.strip():
        lcLike = f"%{tcBusqueda.strip()}%"
        lcQuery += """
            AND (
                C.CodigoContrato LIKE ?
                OR V.NumeroPlaca LIKE ?
                OR V.LetraPlaca LIKE ?
                OR CL.Nombres LIKE ?
                OR CL.Apellidos LIKE ?
                OR CL.DocumentoIdentidad LIKE ?
                OR T.Nombre LIKE ?
            )
        """
        laParams.extend([lcLike, lcLike, lcLike, lcLike, lcLike, lcLike, lcLike])

    if tnEstado is not None:
        lcQuery += " AND C.Estado = ? "
        laParams.append(tnEstado)

    lcQuery += " ORDER BY C.Contrato DESC "

    loCursor.execute(lcQuery, laParams)
    laFilas = loCursor.fetchall()
    loConn.close()
    return laFilas


def existeContratoActivoVehiculo(tnVehiculo, tnExcluirContrato=None):
    loConn = getConnection()
    loCursor = loConn.cursor()

    lcQuery = """
        SELECT COUNT(*)
        FROM CONTRATO
        WHERE Vehiculo = ?
          AND Estado = ?
    """
    laParams = [tnVehiculo, gnEstadoContratoActivo]

    if tnExcluirContrato is not None:
        lcQuery += " AND Contrato <> ? "
        laParams.append(tnExcluirContrato)

    loCursor.execute(lcQuery, laParams)
    llExiste = loCursor.fetchone()[0] > 0
    loConn.close()
    return llExiste


def insertarContrato(txData, tnUsr=0):
    if txData["Estado"] == gnEstadoContratoActivo and existeContratoActivoVehiculo(txData["Vehiculo"]):
        raise ValueError("Ese vehículo ya tiene un contrato activo.")

    loConn = getConnection()
    loCursor = loConn.cursor()

    loCursor.execute("""
        INSERT INTO CONTRATO (
            Cliente,
            Vehiculo,
            Tarifa,
            CodigoContrato,
            FechaInicio,
            FechaFin,
            DuracionMeses,
            Observacion,
            Estado,
            Usr,
            UsrFecha,
            UsrHora,
            FechaCreacion,
            FechaModificacion
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, date('now','localtime'), time('now','localtime'),
            datetime('now','localtime'), datetime('now','localtime')
        )
    """, (
        txData["Cliente"],
        txData["Vehiculo"],
        txData["Tarifa"],
        txData["CodigoContrato"],
        txData["FechaInicio"],
        txData["FechaFin"],
        txData["DuracionMeses"],
        txData["Observacion"],
        txData["Estado"],
        tnUsr
    ))

    loConn.commit()
    loConn.close()


def actualizarContrato(tnContrato, txData, tnUsr=0):
    if txData["Estado"] == gnEstadoContratoActivo and existeContratoActivoVehiculo(
        txData["Vehiculo"], tnExcluirContrato=tnContrato
    ):
        raise ValueError("Ese vehículo ya tiene otro contrato activo.")

    loConn = getConnection()
    loCursor = loConn.cursor()

    loCursor.execute("""
        UPDATE CONTRATO
        SET
            Cliente = ?,
            Vehiculo = ?,
            Tarifa = ?,
            CodigoContrato = ?,
            FechaInicio = ?,
            FechaFin = ?,
            DuracionMeses = ?,
            Observacion = ?,
            Estado = ?,
            Usr = ?,
            UsrFecha = date('now','localtime'),
            UsrHora = time('now','localtime'),
            FechaModificacion = datetime('now','localtime')
        WHERE Contrato = ?
    """, (
        txData["Cliente"],
        txData["Vehiculo"],
        txData["Tarifa"],
        txData["CodigoContrato"],
        txData["FechaInicio"],
        txData["FechaFin"],
        txData["DuracionMeses"],
        txData["Observacion"],
        txData["Estado"],
        tnUsr,
        tnContrato
    ))

    loConn.commit()
    loConn.close()


def cambiarEstadoContrato(tnContrato, tnNuevoEstado, tcObservacion="", tnUsr=0):
    loConn = getConnection()
    loCursor = loConn.cursor()

    if tnNuevoEstado == gnEstadoContratoActivo:
        loCursor.execute("SELECT Vehiculo FROM CONTRATO WHERE Contrato = ?", (tnContrato,))
        toFila = loCursor.fetchone()

        if not toFila:
            loConn.close()
            raise ValueError("Contrato no encontrado.")

        tnVehiculo = toFila["Vehiculo"]

        if existeContratoActivoVehiculo(tnVehiculo, tnExcluirContrato=tnContrato):
            loConn.close()
            raise ValueError("Ese vehículo ya tiene otro contrato activo.")

    loCursor.execute("""
        UPDATE CONTRATO
        SET
            Estado = ?,
            Observacion = CASE
                WHEN ? <> '' THEN ?
                ELSE Observacion
            END,
            Usr = ?,
            UsrFecha = date('now','localtime'),
            UsrHora = time('now','localtime'),
            FechaModificacion = datetime('now','localtime')
        WHERE Contrato = ?
    """, (
        tnNuevoEstado,
        tcObservacion,
        tcObservacion,
        tnUsr,
        tnContrato
    ))

    loConn.commit()
    loConn.close()


def activarContratoPorPago(tnContrato, tnUsr=0):
    cambiarEstadoContrato(tnContrato, gnEstadoContratoActivo, tnUsr=tnUsr)


def finalizarContratosVencidos(tnUsr=0):
    loConn = getConnection()
    loCursor = loConn.cursor()

    loCursor.execute("""
        UPDATE CONTRATO
        SET
            Estado = ?,
            Usr = ?,
            UsrFecha = date('now','localtime'),
            UsrHora = time('now','localtime'),
            FechaModificacion = datetime('now','localtime')
        WHERE Estado = ?
          AND FechaFin < date('now','localtime')
    """, (
        gnEstadoContratoFinalizado,
        tnUsr,
        gnEstadoContratoActivo
    ))

    loConn.commit()
    loConn.close()


class ContractForm(tk.Toplevel):
    def __init__(self, toMaster, txUsuarioData, tfOnSave, toContrato=None):
        super().__init__(toMaster)

        self.txUsuarioData = txUsuarioData or {}
        self.tfOnSave = tfOnSave
        self.toContrato = toContrato

        self.title("Contrato")
        self.geometry("760x500")
        self.minsize(760, 500)
        self.configure(bg="#f4f6f8")
        self.transient(toMaster)
        self.grab_set()

        self.laVehiculos = obtenerVehiculos()
        self.laVehiculosFiltrados = list(self.laVehiculos)

        self.gxMapaVehiculos = {}
        self.buildMapaVehiculos()

        self.buildUi()
        self.loadEditDataIfNeeded()
        self.recalculateEndDateSilent()
        self.updateDatosAutomaticos()

    def buildMapaVehiculos(self):
        self.gxMapaVehiculos = {
            formatearVehiculo(toVehiculo): toVehiculo["Vehiculo"]
            for toVehiculo in self.laVehiculosFiltrados
        }

    def buildUi(self):
        lofrmContainer = tk.Frame(self, bg="#f4f6f8")
        lofrmContainer.pack(fill="both", expand=True, padx=20, pady=20)

        lcTitulo = "Editar contrato" if self.toContrato else "Nuevo contrato"

        tk.Label(
            lofrmContainer,
            text=lcTitulo,
            font=("Arial", 16, "bold"),
            bg="#f4f6f8",
            fg="#1f2937"
        ).pack(anchor="w", pady=(0, 12))

        lofrmFormulario = tk.Frame(lofrmContainer, bg="#ffffff", bd=1, relief="solid")
        lofrmFormulario.pack(fill="both", expand=True)

        lofrmFormulario.columnconfigure(1, weight=1)
        lofrmFormulario.columnconfigure(3, weight=1)

        self.lovCodigoContrato = tk.StringVar(value=generarCodigoContrato() if not self.toContrato else "")
        self.lovBuscarVehiculo = tk.StringVar()
        self.lovVehiculo = tk.StringVar()
        self.lovClienteTexto = tk.StringVar()
        self.lovTarifaTexto = tk.StringVar()
        self.lovFechaInicio = tk.StringVar(value=getFechaActualStr())
        self.lovDuracionMeses = tk.StringVar(value="1")
        self.lovFechaFin = tk.StringVar()
        self.lovObservacion = tk.StringVar()

        lnFila = 0
        self.addLabelEntry(lofrmFormulario, "Código contrato:", self.lovCodigoContrato, lnFila, 0, tcState="readonly")
        self.addLabelEntry(lofrmFormulario, "Buscar vehículo:", self.lovBuscarVehiculo, lnFila, 2)
        lnFila += 1

        self.locboVehiculo = self.addLabelCombo(
            lofrmFormulario,
            "Vehículo:",
            self.lovVehiculo,
            list(self.gxMapaVehiculos.keys()),
            lnFila,
            0,
            width=42
        )
        self.locboVehiculo.bind("<<ComboboxSelected>>", lambda _e: self.updateDatosAutomaticos())
        lnFila += 1

        self.addLabelEntry(lofrmFormulario, "Cliente asignado:", self.lovClienteTexto, lnFila, 0, tcState="readonly")
        self.addLabelEntry(lofrmFormulario, "Tarifa mensual:", self.lovTarifaTexto, lnFila, 2, tcState="readonly")
        lnFila += 1

        self.addLabelEntry(lofrmFormulario, "Fecha inicio (YYYY-MM-DD):", self.lovFechaInicio, lnFila, 0)
        self.addLabelEntry(lofrmFormulario, "Duración (meses):", self.lovDuracionMeses, lnFila, 2)
        lnFila += 1

        self.addLabelEntry(lofrmFormulario, "Fecha fin:", self.lovFechaFin, lnFila, 0, tcState="readonly")
        self.addLabelEntry(lofrmFormulario, "Observación:", self.lovObservacion, lnFila, 2)
        lnFila += 1

        tk.Label(
            lofrmFormulario,
            text="El cliente y la tarifa se asignan automáticamente según el vehículo.",
            font=("Arial", 9),
            bg="#ffffff",
            fg="#6b7280"
        ).grid(row=lnFila, column=0, columnspan=4, sticky="w", padx=14, pady=(6, 4))

        lofrmBotones = tk.Frame(lofrmContainer, bg="#f4f6f8")
        lofrmBotones.pack(fill="x", pady=(12, 0))

        tk.Button(
            lofrmBotones,
            text="Guardar",
            font=("Arial", 10, "bold"),
            bg="#059669",
            fg="white",
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            command=self.saveContract
        ).pack(side="right", padx=(8, 0))

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

        self.lovFechaInicio.trace_add("write", lambda *_: self.recalculateEndDateSilent())
        self.lovDuracionMeses.trace_add("write", lambda *_: self.recalculateEndDateSilent())
        self.lovBuscarVehiculo.trace_add("write", lambda *_: self.filtrarVehiculos())

    def addLabelEntry(self, toParent, tcTexto, toVariable, tnRow, tnCol, tcState="normal"):
        tk.Label(
            toParent,
            text=tcTexto,
            font=("Arial", 10, "bold"),
            bg="#ffffff",
            fg="#374151"
        ).grid(row=tnRow, column=tnCol, sticky="w", padx=14, pady=(12, 6))

        lotxtCampo = tk.Entry(
            toParent,
            textvariable=toVariable,
            font=("Arial", 10),
            relief="solid",
            bd=1,
            state=tcState
        )
        lotxtCampo.grid(row=tnRow, column=tnCol + 1, sticky="ew", padx=(0, 14), pady=(12, 6))
        return lotxtCampo

    def addLabelCombo(self, toParent, tcTexto, toVariable, taValores, tnRow, tnCol, tnWidth=28, width=None):
        lnWidth = width if width is not None else tnWidth

        tk.Label(
            toParent,
            text=tcTexto,
            font=("Arial", 10, "bold"),
            bg="#ffffff",
            fg="#374151"
        ).grid(row=tnRow, column=tnCol, sticky="w", padx=14, pady=(12, 6))

        locboCampo = ttk.Combobox(
            toParent,
            textvariable=toVariable,
            values=taValores,
            state="readonly",
            width=lnWidth
        )
        locboCampo.grid(row=tnRow, column=tnCol + 1, sticky="ew", padx=(0, 14), pady=(12, 6))
        return locboCampo

    def filtrarVehiculos(self):
        lcBusqueda = self.lovBuscarVehiculo.get().strip().upper()

        if not lcBusqueda:
            self.laVehiculosFiltrados = list(self.laVehiculos)
        else:
            self.laVehiculosFiltrados = []
            for toVehiculo in self.laVehiculos:
                lcTexto = formatearVehiculo(toVehiculo).upper()
                if lcBusqueda in lcTexto:
                    self.laVehiculosFiltrados.append(toVehiculo)

        lcSeleccionActual = self.lovVehiculo.get().strip()

        self.buildMapaVehiculos()
        self.locboVehiculo["values"] = list(self.gxMapaVehiculos.keys())

        if lcSeleccionActual not in self.gxMapaVehiculos:
            self.lovVehiculo.set("")
            self.updateDatosAutomaticos()

    def getVehiculoSeleccionadoId(self):
        lcVehiculoTexto = self.lovVehiculo.get().strip()
        if not lcVehiculoTexto or lcVehiculoTexto not in self.gxMapaVehiculos:
            return None
        return self.gxMapaVehiculos[lcVehiculoTexto]

    def getVehiculoSeleccionadoRow(self):
        tnVehiculo = self.getVehiculoSeleccionadoId()
        if tnVehiculo is None:
            return None

        for toVehiculo in self.laVehiculos:
            if toVehiculo["Vehiculo"] == tnVehiculo:
                return toVehiculo

        return None

    def updateDatosAutomaticos(self):
        toVehiculo = self.getVehiculoSeleccionadoRow()

        if not toVehiculo:
            self.lovClienteTexto.set("")
            self.lovTarifaTexto.set("")
            return

        self.lovClienteTexto.set(formatearCliente(toVehiculo))

        toTarifa = obtenerTarifaMensualPorVehiculo(toVehiculo["Vehiculo"])

        if not toTarifa:
            self.lovTarifaTexto.set("No existe tarifa mensual para este vehículo")
            return

        self.lovTarifaTexto.set(f"{toTarifa['Nombre']} | {toTarifa['TipoVehiculo']}")

    def obtenerTarifaAutomaticaId(self):
        tnVehiculo = self.getVehiculoSeleccionadoId()

        if not tnVehiculo:
            return None

        toTarifa = obtenerTarifaMensualPorVehiculo(tnVehiculo)
        if not toTarifa:
            return None

        return toTarifa["Tarifa"]

    def loadEditDataIfNeeded(self):
        if not self.toContrato:
            return

        self.lovCodigoContrato.set(self.toContrato["CodigoContrato"])
        self.lovFechaInicio.set(self.toContrato["FechaInicio"])
        self.lovDuracionMeses.set(str(self.toContrato["DuracionMeses"]))
        self.lovFechaFin.set(self.toContrato["FechaFin"])
        self.lovObservacion.set(self.toContrato["Observacion"] or "")

        for toVehiculo in self.laVehiculos:
            if toVehiculo["Vehiculo"] == self.toContrato["Vehiculo"]:
                lcTextoVehiculo = formatearVehiculo(toVehiculo)
                self.lovVehiculo.set(lcTextoVehiculo)
                break

        self.updateDatosAutomaticos()

    def recalculateEndDateSilent(self):
        try:
            lcFechaInicio = self.lovFechaInicio.get().strip()
            lnDuracionMeses = int(self.lovDuracionMeses.get().strip())

            if lcFechaInicio and lnDuracionMeses > 0:
                self.lovFechaFin.set(sumarMeses(lcFechaInicio, lnDuracionMeses))
        except Exception:
            self.lovFechaFin.set("")

    def saveContract(self):
        try:
            lcCodigoContrato = self.lovCodigoContrato.get().strip()
            lcVehiculoTexto = self.lovVehiculo.get().strip()
            lcFechaInicio = self.lovFechaInicio.get().strip()
            lcFechaFin = self.lovFechaFin.get().strip()
            lcObservacion = self.lovObservacion.get().strip()
            lnDuracionMeses = int(self.lovDuracionMeses.get().strip())

            if not lcCodigoContrato:
                raise ValueError("No se pudo generar el código del contrato.")
            if not lcVehiculoTexto or lcVehiculoTexto not in self.gxMapaVehiculos:
                raise ValueError("Debes seleccionar un vehículo válido.")

            datetime.strptime(lcFechaInicio, "%Y-%m-%d")
            datetime.strptime(lcFechaFin, "%Y-%m-%d")

            if lnDuracionMeses <= 0:
                raise ValueError("La duración debe ser mayor a 0.")

            tnVehiculo = self.gxMapaVehiculos[lcVehiculoTexto]
            toVehiculo = self.getVehiculoSeleccionadoRow()

            if not toVehiculo or not toVehiculo["Cliente"]:
                raise ValueError("El vehículo seleccionado no tiene un cliente asignado.")

            tnTarifa = self.obtenerTarifaAutomaticaId()

            if not tnTarifa:
                raise ValueError("No existe una tarifa mensual activa para el vehículo seleccionado.")

            txData = {
                "Cliente": toVehiculo["Cliente"],
                "Vehiculo": tnVehiculo,
                "Tarifa": tnTarifa,
                "CodigoContrato": lcCodigoContrato,
                "FechaInicio": lcFechaInicio,
                "FechaFin": lcFechaFin,
                "DuracionMeses": lnDuracionMeses,
                "Observacion": lcObservacion if lcObservacion else None,
                "Estado": self.toContrato["Estado"] if self.toContrato else gnEstadoContratoPendiente,
            }

            tnUsr = self.txUsuarioData.get("Usuario", 0)

            if self.toContrato:
                actualizarContrato(self.toContrato["Contrato"], txData, tnUsr=tnUsr)
            else:
                insertarContrato(txData, tnUsr=tnUsr)

            self.tfOnSave()
            self.destroy()

        except ValueError as toError:
            messagebox.showerror("Error", str(toError))
        except Exception as toError:
            messagebox.showerror("Error", f"No se pudo guardar el contrato.\n{toError}")


class ContractsView(tk.Frame):
    def __init__(self, toParent, txUsuarioData, *args, **kwargs):
        super().__init__(toParent, *args, **kwargs)

        self.txUsuarioData = txUsuarioData or {}
        self.configure(bg="#f4f6f8")

        self.lovBusqueda = tk.StringVar()
        self.lovEstado = tk.StringVar(value="Todos")
        self.logrdContratos = None

    def build(self):
        finalizarContratosVencidos(self.txUsuarioData.get("Usuario", 0))
        self.buildUi()
        self.loadContracts()
        self.pack(fill="both", expand=True)

    def buildUi(self):
        for toWidget in self.winfo_children():
            toWidget.destroy()

        lofrmContainer = tk.Frame(self, bg="#f4f6f8")
        lofrmContainer.pack(fill="both", expand=True, padx=16, pady=16)

        lofrmHeader = tk.Frame(lofrmContainer, bg="#f4f6f8")
        lofrmHeader.pack(fill="x", pady=(0, 10))

        tk.Label(
            lofrmHeader,
            text="Gestión de Contratos",
            font=("Arial", 18, "bold"),
            bg="#f4f6f8",
            fg="#111827"
        ).pack(side="left")

        lofrmAcciones = tk.Frame(lofrmContainer, bg="#f4f6f8")
        lofrmAcciones.pack(fill="x", pady=(0, 10))

        tk.Label(
            lofrmAcciones,
            text="Buscar:",
            font=("Arial", 10, "bold"),
            bg="#f4f6f8"
        ).pack(side="left", padx=(0, 6))

        lotxtBusqueda = tk.Entry(
            lofrmAcciones,
            textvariable=self.lovBusqueda,
            font=("Arial", 10),
            relief="solid",
            bd=1,
            width=28
        )
        lotxtBusqueda.pack(side="left", padx=(0, 8))
        lotxtBusqueda.bind("<Return>", lambda _e: self.loadContracts())

        tk.Label(
            lofrmAcciones,
            text="Estado:",
            font=("Arial", 10, "bold"),
            bg="#f4f6f8"
        ).pack(side="left", padx=(4, 6))

        locboEstado = ttk.Combobox(
            lofrmAcciones,
            textvariable=self.lovEstado,
            state="readonly",
            values=["Todos"] + list(gxEstadosContratoInv.keys()),
            width=16
        )
        locboEstado.pack(side="left", padx=(0, 8))

        tk.Button(
            lofrmAcciones,
            text="Buscar",
            font=("Arial", 10, "bold"),
            bg="#2563eb",
            fg="white",
            bd=0,
            padx=12,
            pady=7,
            cursor="hand2",
            command=self.loadContracts
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            lofrmAcciones,
            text="Limpiar",
            font=("Arial", 10, "bold"),
            bg="#6b7280",
            fg="white",
            bd=0,
            padx=12,
            pady=7,
            cursor="hand2",
            command=self.clearFilters
        ).pack(side="left", padx=(0, 12))

        tk.Button(
            lofrmAcciones,
            text="Nuevo contrato",
            font=("Arial", 10, "bold"),
            bg="#059669",
            fg="white",
            bd=0,
            padx=12,
            pady=7,
            cursor="hand2",
            command=self.openNew
        ).pack(side="right")

        lofrmTabla = tk.Frame(lofrmContainer, bg="#ffffff", bd=1, relief="solid")
        lofrmTabla.pack(fill="both", expand=True)

        taColumnas = (
            "Contrato",
            "CodigoContrato",
            "Cliente",
            "Placa",
            "Tarifa",
            "FechaInicio",
            "FechaFin",
            "DuracionMeses",
            "Estado",
        )

        self.logrdContratos = ttk.Treeview(
            lofrmTabla,
            columns=taColumnas,
            show="headings",
            height=16
        )

        gxEncabezados = {
            "Contrato": "ID",
            "CodigoContrato": "Código",
            "Cliente": "Cliente",
            "Placa": "Placa",
            "Tarifa": "Tarifa",
            "FechaInicio": "Inicio",
            "FechaFin": "Fin",
            "DuracionMeses": "Meses",
            "Estado": "Estado",
        }

        gxAnchos = {
            "Contrato": 60,
            "CodigoContrato": 120,
            "Cliente": 220,
            "Placa": 120,
            "Tarifa": 170,
            "FechaInicio": 100,
            "FechaFin": 100,
            "DuracionMeses": 70,
            "Estado": 100,
        }

        for tcColumna in taColumnas:
            self.logrdContratos.heading(tcColumna, text=gxEncabezados[tcColumna])
            self.logrdContratos.column(tcColumna, width=gxAnchos[tcColumna], anchor="center")

        loscrVertical = ttk.Scrollbar(lofrmTabla, orient="vertical", command=self.logrdContratos.yview)
        loscrHorizontal = ttk.Scrollbar(lofrmTabla, orient="horizontal", command=self.logrdContratos.xview)

        self.logrdContratos.configure(
            yscrollcommand=loscrVertical.set,
            xscrollcommand=loscrHorizontal.set
        )

        self.logrdContratos.pack(side="left", fill="both", expand=True)
        loscrVertical.pack(side="right", fill="y")
        loscrHorizontal.pack(side="bottom", fill="x")

        self.logrdContratos.bind("<Double-1>", lambda _e: self.editSelected())

        lofrmFooter = tk.Frame(lofrmContainer, bg="#f4f6f8")
        lofrmFooter.pack(fill="x", pady=(10, 0))

        tk.Button(
            lofrmFooter,
            text="Editar",
            font=("Arial", 10, "bold"),
            bg="#f59e0b",
            fg="white",
            bd=0,
            padx=12,
            pady=7,
            cursor="hand2",
            command=self.editSelected
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            lofrmFooter,
            text="Cobrar",
            font=("Arial", 10, "bold"),
            bg="#2563eb",
            fg="white",
            bd=0,
            padx=12,
            pady=7,
            cursor="hand2",
            command=self.chargeSelected
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            lofrmFooter,
            text="Cancelar contrato",
            font=("Arial", 10, "bold"),
            bg="#dc2626",
            fg="white",
            bd=0,
            padx=12,
            pady=7,
            cursor="hand2",
            command=self.cancelSelected
        ).pack(side="left", padx=(0, 6))

    def clearFilters(self):
        self.lovBusqueda.set("")
        self.lovEstado.set("Todos")
        self.loadContracts()

    def loadContracts(self):
        if self.logrdContratos is None:
            return

        finalizarContratosVencidos(self.txUsuarioData.get("Usuario", 0))

        for toItem in self.logrdContratos.get_children():
            self.logrdContratos.delete(toItem)

        lcEstadoTexto = self.lovEstado.get().strip()
        tnEstadoValor = None if lcEstadoTexto == "Todos" else gxEstadosContratoInv.get(lcEstadoTexto)

        laFilas = obtenerContratos(
            tcBusqueda=self.lovBusqueda.get().strip(),
            tnEstado=tnEstadoValor
        )

        for toFila in laFilas:
            lcCliente = f"{toFila['Nombres']} {toFila['Apellidos'] or ''}".strip()
            lcPlaca = f"{toFila['NumeroPlaca']} {toFila['LetraPlaca']}".strip()

            self.logrdContratos.insert(
                "",
                "end",
                values=(
                    toFila["Contrato"],
                    toFila["CodigoContrato"],
                    lcCliente,
                    lcPlaca,
                    toFila["NombreTarifa"],
                    toFila["FechaInicio"],
                    toFila["FechaFin"],
                    toFila["DuracionMeses"],
                    gxEstadosContrato.get(toFila["Estado"], "N/D"),
                )
            )

    def openNew(self):
        ContractForm(self, self.txUsuarioData, self.loadContracts)

    def getSelectedId(self):
        taSeleccionado = self.logrdContratos.selection()

        if not taSeleccionado:
            messagebox.showwarning("Aviso", "Selecciona un contrato.")
            return None

        taValores = self.logrdContratos.item(taSeleccionado[0], "values")
        return int(taValores[0])

    def editSelected(self):
        tnContrato = self.getSelectedId()

        if tnContrato is None:
            return

        toContrato = obtenerContratoPorId(tnContrato)

        if not toContrato:
            messagebox.showerror("Error", "No se encontró el contrato.")
            return

        if toContrato["Estado"] == gnEstadoContratoFinalizado:
            messagebox.showwarning("Aviso", "No se puede editar un contrato finalizado.")
            return

        ContractForm(self, self.txUsuarioData, self.loadContracts, toContrato=toContrato)

    def chargeSelected(self):
        tnContrato = self.getSelectedId()

        if tnContrato is None:
            return

        toContrato = obtenerContratoPorId(tnContrato)

        if not toContrato:
            messagebox.showerror("Error", "No se encontró el contrato.")
            return

        if toContrato["Estado"] == gnEstadoContratoActivo:
            messagebox.showwarning("Aviso", "Este contrato ya fue cobrado y está activo.")
            return

        if toContrato["Estado"] == gnEstadoContratoCancelado:
            messagebox.showwarning("Aviso", "No se puede cobrar un contrato cancelado.")
            return

        if toContrato["Estado"] == gnEstadoContratoFinalizado:
            messagebox.showwarning("Aviso", "No se puede cobrar un contrato finalizado.")
            return

        lnMontoMensual = obtenerMontoMensualTarifa(toContrato["Tarifa"])
        if lnMontoMensual is None:
            messagebox.showerror("Error", "No se encontró el monto mensual de la tarifa del contrato.")
            return

        lnMontoTotal = float(lnMontoMensual) * int(toContrato["DuracionMeses"])
        lcConcepto = f"Cobro contrato {toContrato['CodigoContrato']}"

        def onPagoGuardado(_tnPago):
            tnUsr = self.txUsuarioData.get("Usuario", 0)
            activarContratoPorPago(toContrato["Contrato"], tnUsr=tnUsr)
            self.loadContracts()

        FrmCobros(
            self,
            self.txUsuarioData,
            tnTipoDetalle=gnTipoDetalleContrato,
            tnDetalle=toContrato["Contrato"],
            tcConcepto=lcConcepto,
            tnMonto=lnMontoTotal,
            tfOnSave=onPagoGuardado
        )

    def cancelSelected(self):
        tnContrato = self.getSelectedId()

        if tnContrato is None:
            return

        toContrato = obtenerContratoPorId(tnContrato)

        if not toContrato:
            messagebox.showerror("Error", "No se encontró el contrato.")
            return

        if toContrato["Estado"] == gnEstadoContratoFinalizado:
            messagebox.showwarning("Aviso", "El contrato ya está finalizado.")
            return

        if toContrato["Estado"] == gnEstadoContratoCancelado:
            messagebox.showwarning("Aviso", "El contrato ya está cancelado.")
            return

        lcObservacion = simpledialog.askstring(
            "Cancelar contrato",
            "Ingrese el motivo de cancelación:"
        )

        if lcObservacion is None:
            return

        lcObservacion = lcObservacion.strip()
        if not lcObservacion:
            messagebox.showwarning("Aviso", "Debes ingresar una observación para cancelar.")
            return

        llOk = messagebox.askyesno(
            "Confirmar",
            "¿Deseas cancelar este contrato?"
        )

        if not llOk:
            return

        try:
            tnUsr = self.txUsuarioData.get("Usuario", 0)
            cambiarEstadoContrato(
                tnContrato,
                gnEstadoContratoCancelado,
                tcObservacion=lcObservacion,
                tnUsr=tnUsr
            )
            self.loadContracts()
            messagebox.showinfo("Éxito", "Contrato cancelado correctamente.")
        except Exception as toError:
            messagebox.showerror("Error", str(toError))