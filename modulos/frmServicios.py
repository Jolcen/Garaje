import tkinter as tk
from tkinter import ttk, messagebox

from database.db import getConnection


gnRolAdministrador = 1

gnEstadoInactivo = 0
gnEstadoActivo = 1

gxEstadoTexto = {
    gnEstadoActivo: "Activo",
    gnEstadoInactivo: "Inactivo"
}

gxTextoEstado = {
    "Activo": gnEstadoActivo,
    "Inactivo": gnEstadoInactivo
}


def obtenerUsuarioActualId(txUsuarioData):
    if not txUsuarioData:
        return 0
    return txUsuarioData.get("Usuario", 0)


class ServicesView:
    def __init__(self, toParent, txUsuarioData):
        self.toParent = toParent
        self.txUsuarioData = txUsuarioData

        self.lofrmMain = None
        self.logrdServicios = None
        self.lotxtBusqueda = None
        self.locmbFiltroEstado = None
        self.loEstadoFiltroVar = None

        self.lobtnEditar = None
        self.lobtnCambiarEstado = None

    def build(self):
        self.lofrmMain = tk.Frame(self.toParent, bg="white")
        self.lofrmMain.pack(fill="both", expand=True)

        if self.txUsuarioData.get("RolId") != gnRolAdministrador:
            self.buildAccessDenied()
            return

        self.buildHeader()
        self.buildTable()
        self.buildActions()
        self.loadServices()

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
            text="Solo el administrador puede gestionar servicios.",
            font=("Arial", 11),
            bg="white",
            fg="#4b5563"
        ).pack()

    def buildHeader(self):
        lofrmHeader = tk.Frame(self.lofrmMain, bg="white")
        lofrmHeader.pack(fill="x", padx=15, pady=15)

        tk.Label(
            lofrmHeader,
            text="Buscar servicio:",
            font=("Arial", 11, "bold"),
            bg="white"
        ).pack(side="left", padx=(0, 8))

        self.lotxtBusqueda = tk.Entry(lofrmHeader, font=("Arial", 11), width=28)
        self.lotxtBusqueda.pack(side="left", padx=(0, 12))
        self.lotxtBusqueda.bind("<KeyRelease>", lambda e: self.loadServices())

        tk.Label(
            lofrmHeader,
            text="Estado:",
            font=("Arial", 11, "bold"),
            bg="white"
        ).pack(side="left", padx=(0, 8))

        self.loEstadoFiltroVar = tk.StringVar(value="Activos")
        self.locmbFiltroEstado = ttk.Combobox(
            lofrmHeader,
            textvariable=self.loEstadoFiltroVar,
            state="readonly",
            width=12,
            values=["Activos", "Inactivos", "Todos"]
        )
        self.locmbFiltroEstado.pack(side="left", padx=(0, 12))
        self.locmbFiltroEstado.bind("<<ComboboxSelected>>", lambda e: self.loadServices())

        tk.Button(
            lofrmHeader,
            text="Nuevo servicio",
            bg="#16a34a",
            fg="white",
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.openNew
        ).pack(side="right")

    def buildTable(self):
        lofrmTabla = tk.Frame(self.lofrmMain, bg="white")
        lofrmTabla.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        columnas = ("Servicio", "Nombre", "Descripcion", "Precio", "Estado")

        self.logrdServicios = ttk.Treeview(
            lofrmTabla,
            columns=columnas,
            show="headings",
            selectmode="browse"
        )

        self.logrdServicios.heading("Servicio", text="Servicio")
        self.logrdServicios.heading("Nombre", text="Nombre")
        self.logrdServicios.heading("Descripcion", text="Descripción")
        self.logrdServicios.heading("Precio", text="Precio")
        self.logrdServicios.heading("Estado", text="Estado")

        self.logrdServicios.column("Servicio", width=70, anchor="center")
        self.logrdServicios.column("Nombre", width=220, anchor="w")
        self.logrdServicios.column("Descripcion", width=380, anchor="w")
        self.logrdServicios.column("Precio", width=120, anchor="e")
        self.logrdServicios.column("Estado", width=100, anchor="center")

        scrollbarY = ttk.Scrollbar(
            lofrmTabla,
            orient="vertical",
            command=self.logrdServicios.yview
        )
        self.logrdServicios.configure(yscrollcommand=scrollbarY.set)

        self.logrdServicios.pack(side="left", fill="both", expand=True)
        scrollbarY.pack(side="right", fill="y")

        self.logrdServicios.bind("<Double-1>", self.onDoubleClick)
        self.logrdServicios.bind("<<TreeviewSelect>>", lambda e: self.updateActionButtons())

    def buildActions(self):
        lofrmAcciones = tk.Frame(self.lofrmMain, bg="white")
        lofrmAcciones.pack(fill="x", padx=15, pady=(0, 15))

        self.lobtnEditar = tk.Button(
            lofrmAcciones,
            text="Editar",
            bg="#2563eb",
            fg="white",
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            state="disabled",
            command=self.openEditSelected
        )
        self.lobtnEditar.pack(side="left", padx=(0, 8))

        self.lobtnCambiarEstado = tk.Button(
            lofrmAcciones,
            text="Activar / Desactivar",
            bg="#d97706",
            fg="white",
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            state="disabled",
            command=self.toggleSelectedStatus
        )
        self.lobtnCambiarEstado.pack(side="left")

    def updateActionButtons(self):
        haySeleccion = bool(self.logrdServicios.selection())

        estadoBoton = "normal" if haySeleccion else "disabled"
        self.lobtnEditar.config(state=estadoBoton)
        self.lobtnCambiarEstado.config(state=estadoBoton)

    def getSelectedServiceData(self):
        seleccion = self.logrdServicios.selection()
        if not seleccion:
            return None

        valores = self.logrdServicios.item(seleccion[0])["values"]
        if not valores:
            return None

        return {
            "Servicio": valores[0],
            "Nombre": valores[1],
            "Descripcion": valores[2],
            "Precio": valores[3],
            "EstadoTexto": valores[4]
        }

    def loadServices(self):
        if not self.logrdServicios:
            return

        for item in self.logrdServicios.get_children():
            self.logrdServicios.delete(item)

        lcBusqueda = self.lotxtBusqueda.get().strip().upper() if self.lotxtBusqueda else ""
        lcFiltroEstado = self.loEstadoFiltroVar.get().strip() if self.loEstadoFiltroVar else "Activos"

        loConn = getConnection()
        loCursor = loConn.cursor()

        try:
            lcSql = """
                SELECT
                    Servicio,
                    Nombre,
                    Descripcion,
                    Precio,
                    Estado
                FROM SERVICIO
                WHERE 1 = 1
            """
            laParams = []

            if lcBusqueda:
                lcSql += """
                    AND (
                        UPPER(Nombre) LIKE ?
                        OR UPPER(COALESCE(Descripcion, '')) LIKE ?
                    )
                """
                laParams.extend([
                    f"%{lcBusqueda}%",
                    f"%{lcBusqueda}%"
                ])

            if lcFiltroEstado == "Activos":
                lcSql += " AND Estado = ? "
                laParams.append(gnEstadoActivo)
            elif lcFiltroEstado == "Inactivos":
                lcSql += " AND Estado = ? "
                laParams.append(gnEstadoInactivo)

            lcSql += " ORDER BY Nombre ASC"

            loCursor.execute(lcSql, laParams)
            laRows = loCursor.fetchall()

            for row in laRows:
                self.logrdServicios.insert("", "end", values=(
                    row["Servicio"],
                    row["Nombre"],
                    row["Descripcion"] or "",
                    f"Bs {float(row['Precio']):.2f}",
                    gxEstadoTexto.get(row["Estado"], "N/D")
                ))

            self.updateActionButtons()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los servicios.\n\n{str(e)}")
        finally:
            loConn.close()

    def openNew(self):
        ServiceForm(self, self.txUsuarioData)

    def openEditSelected(self):
        loServicio = self.getSelectedServiceData()
        if not loServicio:
            messagebox.showwarning("Aviso", "Debe seleccionar un servicio.")
            return

        ServiceForm(self, self.txUsuarioData, service_id=loServicio["Servicio"])

    def onDoubleClick(self, event):
        self.openEditSelected()

    def toggleSelectedStatus(self):
        loServicio = self.getSelectedServiceData()
        if not loServicio:
            messagebox.showwarning("Aviso", "Debe seleccionar un servicio.")
            return

        lnServicio = loServicio["Servicio"]
        lcNombre = loServicio["Nombre"]
        lcEstadoTexto = loServicio["EstadoTexto"]

        if lcEstadoTexto == "Activo":
            lnNuevoEstado = gnEstadoInactivo
            lcAccion = "desactivar"
            lcMensaje = f"¿Desea desactivar el servicio '{lcNombre}'?"
        else:
            lnNuevoEstado = gnEstadoActivo
            lcAccion = "activar"
            lcMensaje = f"¿Desea activar el servicio '{lcNombre}'?"

        if not messagebox.askyesno("Confirmar", lcMensaje):
            return

        loConn = getConnection()
        loCursor = loConn.cursor()

        try:
            loCursor.execute("""
                UPDATE SERVICIO
                SET
                    Estado = ?,
                    Usr = ?,
                    UsrFecha = date('now', 'localtime'),
                    UsrHora = time('now', 'localtime')
                WHERE Servicio = ?
            """, (
                lnNuevoEstado,
                obtenerUsuarioActualId(self.txUsuarioData),
                lnServicio
            ))

            loConn.commit()
            messagebox.showinfo("Éxito", f"Servicio {lcAccion}do correctamente.")
            self.loadServices()

        except Exception as e:
            loConn.rollback()
            messagebox.showerror("Error", f"No se pudo cambiar el estado.\n\n{str(e)}")
        finally:
            loConn.close()


class ServiceForm(tk.Toplevel):
    def __init__(self, toView, txUsuarioData, service_id=None):
        super().__init__()

        self.toView = toView
        self.txUsuarioData = txUsuarioData
        self.service_id = service_id

        self.title("Servicio")
        self.geometry("460x360")
        self.resizable(False, False)
        self.configure(bg="white")
        self.transient(self.toView.toParent.winfo_toplevel())
        self.grab_set()

        self.lotxtNombre = None
        self.lotxtDescripcion = None
        self.lotxtPrecio = None
        self.loEstadoVar = None
        self.locmbEstado = None

        self.buildUi()
        self.centerWindow()

        if self.service_id:
            self.loadData()

    def centerWindow(self):
        self.update_idletasks()

        ancho = self.winfo_width()
        alto = self.winfo_height()

        x = (self.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.winfo_screenheight() // 2) - (alto // 2)

        self.geometry(f"{ancho}x{alto}+{x}+{y}")

    def buildUi(self):
        lofrmMain = tk.Frame(self, bg="white", padx=20, pady=20)
        lofrmMain.pack(fill="both", expand=True)

        tk.Label(
            lofrmMain,
            text="Nombre",
            font=("Arial", 10, "bold"),
            bg="white",
            anchor="w"
        ).pack(fill="x", pady=(0, 4))

        self.lotxtNombre = tk.Entry(lofrmMain, font=("Arial", 10))
        self.lotxtNombre.pack(fill="x", pady=(0, 10))

        tk.Label(
            lofrmMain,
            text="Descripción",
            font=("Arial", 10, "bold"),
            bg="white",
            anchor="w"
        ).pack(fill="x", pady=(0, 4))

        self.lotxtDescripcion = tk.Text(lofrmMain, font=("Arial", 10), height=5)
        self.lotxtDescripcion.pack(fill="x", pady=(0, 10))

        tk.Label(
            lofrmMain,
            text="Precio",
            font=("Arial", 10, "bold"),
            bg="white",
            anchor="w"
        ).pack(fill="x", pady=(0, 4))

        self.lotxtPrecio = tk.Entry(lofrmMain, font=("Arial", 10))
        self.lotxtPrecio.pack(fill="x", pady=(0, 10))

        tk.Label(
            lofrmMain,
            text="Estado",
            font=("Arial", 10, "bold"),
            bg="white",
            anchor="w"
        ).pack(fill="x", pady=(0, 4))

        self.loEstadoVar = tk.StringVar(value="Activo")
        self.locmbEstado = ttk.Combobox(
            lofrmMain,
            textvariable=self.loEstadoVar,
            state="readonly",
            values=["Activo", "Inactivo"]
        )
        self.locmbEstado.pack(fill="x", pady=(0, 15))

        lofrmBotones = tk.Frame(lofrmMain, bg="white")
        lofrmBotones.pack(fill="x", pady=(10, 0))

        tk.Button(
            lofrmBotones,
            text="Guardar",
            bg="#16a34a",
            fg="white",
            bd=0,
            padx=16,
            pady=8,
            cursor="hand2",
            command=self.save
        ).pack(side="right", padx=(8, 0))

        tk.Button(
            lofrmBotones,
            text="Cancelar",
            bg="#6b7280",
            fg="white",
            bd=0,
            padx=16,
            pady=8,
            cursor="hand2",
            command=self.destroy
        ).pack(side="right")

    def loadData(self):
        loConn = getConnection()
        loCursor = loConn.cursor()

        try:
            loCursor.execute("""
                SELECT
                    Servicio,
                    Nombre,
                    Descripcion,
                    Precio,
                    Estado
                FROM SERVICIO
                WHERE Servicio = ?
            """, (self.service_id,))
            row = loCursor.fetchone()

            if not row:
                messagebox.showwarning("Aviso", "No se encontró el servicio.")
                self.destroy()
                return

            self.lotxtNombre.insert(0, row["Nombre"])
            self.lotxtDescripcion.insert("1.0", row["Descripcion"] or "")
            self.lotxtPrecio.insert(0, str(row["Precio"]))
            self.loEstadoVar.set(gxEstadoTexto.get(row["Estado"], "Activo"))

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el servicio.\n\n{str(e)}")
            self.destroy()
        finally:
            loConn.close()

    def validarDatos(self):
        lcNombre = self.lotxtNombre.get().strip()
        lcDescripcion = self.lotxtDescripcion.get("1.0", "end").strip()
        lcPrecio = self.lotxtPrecio.get().strip()
        lcEstadoTexto = self.loEstadoVar.get().strip()

        if not lcNombre:
            messagebox.showwarning("Validación", "Debe ingresar el nombre del servicio.")
            self.lotxtNombre.focus()
            return None

        if len(lcNombre) > 100:
            messagebox.showwarning("Validación", "El nombre del servicio es demasiado largo.")
            self.lotxtNombre.focus()
            return None

        if not lcPrecio:
            messagebox.showwarning("Validación", "Debe ingresar el precio del servicio.")
            self.lotxtPrecio.focus()
            return None

        try:
            lnPrecio = float(lcPrecio)
        except ValueError:
            messagebox.showwarning("Validación", "El precio debe ser numérico.")
            self.lotxtPrecio.focus()
            return None

        if lnPrecio < 0:
            messagebox.showwarning("Validación", "El precio no puede ser negativo.")
            self.lotxtPrecio.focus()
            return None

        lnEstado = gxTextoEstado.get(lcEstadoTexto, gnEstadoActivo)

        return {
            "Nombre": lcNombre,
            "Descripcion": lcDescripcion,
            "Precio": lnPrecio,
            "Estado": lnEstado
        }

    def existeNombreDuplicado(self, tcNombre):
        loConn = getConnection()
        loCursor = loConn.cursor()

        try:
            if self.service_id:
                loCursor.execute("""
                    SELECT COUNT(*) AS Cantidad
                    FROM SERVICIO
                    WHERE UPPER(Nombre) = UPPER(?)
                      AND Servicio <> ?
                """, (tcNombre, self.service_id))
            else:
                loCursor.execute("""
                    SELECT COUNT(*) AS Cantidad
                    FROM SERVICIO
                    WHERE UPPER(Nombre) = UPPER(?)
                """, (tcNombre,))

            loFila = loCursor.fetchone()
            return loFila["Cantidad"] > 0
        finally:
            loConn.close()

    def save(self):
        loData = self.validarDatos()
        if not loData:
            return

        if self.existeNombreDuplicado(loData["Nombre"]):
            messagebox.showwarning("Validación", "Ya existe un servicio con ese nombre.")
            self.lotxtNombre.focus()
            return

        lnUsuarioActual = obtenerUsuarioActualId(self.txUsuarioData)

        loConn = getConnection()
        loCursor = loConn.cursor()

        try:
            if self.service_id:
                loCursor.execute("""
                    UPDATE SERVICIO
                    SET
                        Nombre = ?,
                        Descripcion = ?,
                        Precio = ?,
                        Estado = ?,
                        Usr = ?,
                        UsrFecha = date('now', 'localtime'),
                        UsrHora = time('now', 'localtime')
                    WHERE Servicio = ?
                """, (
                    loData["Nombre"],
                    loData["Descripcion"],
                    loData["Precio"],
                    loData["Estado"],
                    lnUsuarioActual,
                    self.service_id
                ))
            else:
                loCursor.execute("""
                    INSERT INTO SERVICIO (
                        Nombre,
                        Descripcion,
                        Precio,
                        Estado,
                        Usr,
                        UsrFecha,
                        UsrHora,
                        FechaCreacion,
                        FechaModificacion
                    )
                    VALUES (
                        ?, ?, ?, ?, ?,
                        date('now', 'localtime'),
                        time('now', 'localtime'),
                        datetime('now', 'localtime'),
                        datetime('now', 'localtime')
                    )
                """, (
                    loData["Nombre"],
                    loData["Descripcion"],
                    loData["Precio"],
                    loData["Estado"],
                    lnUsuarioActual
                ))

            loConn.commit()

            if self.service_id:
                messagebox.showinfo("Éxito", "Servicio actualizado correctamente.")
            else:
                messagebox.showinfo("Éxito", "Servicio registrado correctamente.")

            self.toView.loadServices()
            self.destroy()

        except Exception as e:
            loConn.rollback()
            messagebox.showerror("Error", f"No se pudo guardar el servicio.\n\n{str(e)}")
        finally:
            loConn.close()