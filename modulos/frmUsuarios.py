import tkinter as tk
from tkinter import ttk, messagebox

from database.db import getConnection


gnEstadoInactivo = 0
gnEstadoActivo = 1

gnRolAdmin = 1
gnRolEmpleado = 2

gxRolTexto = {
    gnRolAdmin: "admin",
    gnRolEmpleado: "empleado",
}

gxEstadoTexto = {
    gnEstadoActivo: "activo",
    gnEstadoInactivo: "inactivo",
}


def obtenerUsuarioActualId(txUsuarioData):
    if not txUsuarioData:
        return 0
    return txUsuarioData.get("Usuario", 0)


def getFechaHoraActualTexto():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class UsersView:
    def __init__(self, toParent, txUsuarioData):
        self.toParent = toParent
        self.txUsuarioData = txUsuarioData or {}

        self.logrdUsuarios = None
        self.lotxtBusqueda = None

    def build(self):
        if self.txUsuarioData.get("Rol") != "admin":
            self.buildAccessDenied()
            return

        self.buildHeader()
        self.buildTable()
        self.loadUsers()

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
            text="Solo el administrador puede gestionar usuarios.",
            font=("Arial", 11),
            bg="white",
            fg="#4b5563"
        )
        lolblMensaje.pack()

    def buildHeader(self):
        lofrmHeader = tk.Frame(self.toParent, bg="white")
        lofrmHeader.pack(fill="x", padx=15, pady=15)

        lolblBuscar = tk.Label(
            lofrmHeader,
            text="Buscar usuario:",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#111827"
        )
        lolblBuscar.pack(side="left", padx=(0, 8))

        self.lotxtBusqueda = tk.Entry(lofrmHeader, font=("Arial", 11), width=25)
        self.lotxtBusqueda.pack(side="left", padx=(0, 8))
        self.lotxtBusqueda.bind("<KeyRelease>", lambda toEvent: self.loadUsers())

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
            command=self.loadUsers
        )
        locmdBuscar.pack(side="left", padx=(0, 10))

        locmdNuevoUsuario = tk.Button(
            lofrmHeader,
            text="Nuevo usuario",
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
            command=self.openNewUserWindow
        )
        locmdNuevoUsuario.pack(side="right")

    def buildTable(self):
        lofrmTabla = tk.Frame(self.toParent, bg="white")
        lofrmTabla.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        taColumnas = (
            "Usuario",
            "Nombre",
            "NombreUsuario",
            "Rol",
            "Estado",
            "FechaCreacion",
            "Acciones"
        )

        self.logrdUsuarios = ttk.Treeview(
            lofrmTabla,
            columns=taColumnas,
            show="headings",
            height=18
        )

        self.logrdUsuarios.heading("Usuario", text="ID")
        self.logrdUsuarios.heading("Nombre", text="Nombre")
        self.logrdUsuarios.heading("NombreUsuario", text="Usuario")
        self.logrdUsuarios.heading("Rol", text="Rol")
        self.logrdUsuarios.heading("Estado", text="Estado")
        self.logrdUsuarios.heading("FechaCreacion", text="Fecha creación")
        self.logrdUsuarios.heading("Acciones", text="Acciones")

        self.logrdUsuarios.column("Usuario", width=60, anchor="center", stretch=False)
        self.logrdUsuarios.column("Nombre", width=240, anchor="w", stretch=False)
        self.logrdUsuarios.column("NombreUsuario", width=140, anchor="center", stretch=False)
        self.logrdUsuarios.column("Rol", width=100, anchor="center", stretch=False)
        self.logrdUsuarios.column("Estado", width=100, anchor="center", stretch=False)
        self.logrdUsuarios.column("FechaCreacion", width=160, anchor="center", stretch=False)
        self.logrdUsuarios.column("Acciones", width=120, anchor="center", stretch=False)

        loscrVertical = ttk.Scrollbar(lofrmTabla, orient="vertical", command=self.logrdUsuarios.yview)
        loscrHorizontal = ttk.Scrollbar(lofrmTabla, orient="horizontal", command=self.logrdUsuarios.xview)

        self.logrdUsuarios.configure(
            yscrollcommand=loscrVertical.set,
            xscrollcommand=loscrHorizontal.set
        )

        self.logrdUsuarios.grid(row=0, column=0, sticky="nsew")
        loscrVertical.grid(row=0, column=1, sticky="ns")
        loscrHorizontal.grid(row=1, column=0, sticky="ew")

        lofrmTabla.grid_rowconfigure(0, weight=1)
        lofrmTabla.grid_columnconfigure(0, weight=1)

        self.logrdUsuarios.bind("<Double-1>", self.onDoubleClick)

    def loadUsers(self):
        for toItem in self.logrdUsuarios.get_children():
            self.logrdUsuarios.delete(toItem)

        lcBusqueda = self.lotxtBusqueda.get().strip().upper() if self.lotxtBusqueda else ""

        loConn = getConnection()
        loCursor = loConn.cursor()

        lcQuery = """
            SELECT Usuario, Nombre, NombreUsuario, Rol, Estado, FechaCreacion
            FROM USUARIO
            WHERE 1 = 1
        """
        laParams = []

        if lcBusqueda:
            lcLikeValue = f"%{lcBusqueda}%"
            lcQuery += """
                AND (
                    UPPER(Nombre) LIKE ?
                    OR UPPER(NombreUsuario) LIKE ?
                )
            """
            laParams.extend([lcLikeValue, lcLikeValue])

        lcQuery += " ORDER BY Usuario ASC "

        loCursor.execute(lcQuery, laParams)
        laRows = loCursor.fetchall()
        loConn.close()

        for toRow in laRows:
            self.logrdUsuarios.insert(
                "",
                "end",
                values=(
                    toRow["Usuario"],
                    toRow["Nombre"],
                    toRow["NombreUsuario"],
                    gxRolTexto.get(toRow["Rol"], "N/D"),
                    gxEstadoTexto.get(toRow["Estado"], "N/D"),
                    toRow["FechaCreacion"],
                    "Doble clic"
                )
            )

    def onDoubleClick(self, toEvent):
        taSeleccionado = self.logrdUsuarios.selection()
        if not taSeleccionado:
            return

        taValores = self.logrdUsuarios.item(taSeleccionado[0], "values")
        if not taValores:
            return

        tnUsuario = int(taValores[0])
        lcNombreUsuario = taValores[2]
        lcEstado = taValores[4]

        loWindowAcciones = tk.Toplevel(self.toParent)
        loWindowAcciones.title("Acciones de usuario")
        loWindowAcciones.geometry("340x270")
        loWindowAcciones.resizable(False, False)
        loWindowAcciones.configure(bg="white")
        loWindowAcciones.grab_set()

        tk.Label(
            loWindowAcciones,
            text=f"Usuario: {lcNombreUsuario}",
            font=("Arial", 14, "bold"),
            bg="white",
            fg="#111827"
        ).pack(pady=(20, 10))

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
            command=lambda: self.confirmEdit(tnUsuario, loWindowAcciones)
        ).pack(pady=8)

        tnEstadoActual = gnEstadoActivo if lcEstado == "activo" else gnEstadoInactivo
        lcTextoToggle = "Inactivar" if tnEstadoActual == gnEstadoActivo else "Activar"
        lcColorToggle = "#dc2626" if tnEstadoActual == gnEstadoActivo else "#16a34a"

        tk.Button(
            loWindowAcciones,
            text=lcTextoToggle,
            font=("Arial", 11, "bold"),
            width=18,
            bg=lcColorToggle,
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            command=lambda: self.toggleUserStatus(tnUsuario, tnEstadoActual, loWindowAcciones)
        ).pack(pady=8)

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
        ).pack(pady=8)

    def confirmEdit(self, tnUsuario, loWindowAcciones=None):
        llConfirmado = messagebox.askyesno(
            "Confirmar edición",
            "¿Desea editar este usuario?"
        )
        if not llConfirmado:
            return

        self.editUser(tnUsuario, loWindowAcciones)

    def openNewUserWindow(self):
        UserFormWindow(self, self.txUsuarioData)

    def editUser(self, tnUsuario, loWindowAcciones=None):
        if loWindowAcciones:
            loWindowAcciones.destroy()
        UserFormWindow(self, self.txUsuarioData, tnUsuario=tnUsuario)

    def toggleUserStatus(self, tnUsuario, tnEstadoActual, loWindowAcciones=None):
        if loWindowAcciones:
            loWindowAcciones.destroy()

        tnNuevoEstado = gnEstadoInactivo if tnEstadoActual == gnEstadoActivo else gnEstadoActivo
        lcNuevoEstadoTexto = gxEstadoTexto[tnNuevoEstado]
        tnUsuarioActual = obtenerUsuarioActualId(self.txUsuarioData)

        if tnUsuario == tnUsuarioActual and tnNuevoEstado == gnEstadoInactivo:
            messagebox.showwarning("Acción no permitida", "No puede inactivar su propio usuario.")
            return

        llConfirmado = messagebox.askyesno(
            "Confirmar cambio",
            f"¿Desea cambiar el estado del usuario a '{lcNuevoEstadoTexto}'?"
        )
        if not llConfirmado:
            return

        loConn = getConnection()
        loCursor = loConn.cursor()

        try:
            if self.isLastActiveAdmin(loCursor, tnUsuario) and tnNuevoEstado == gnEstadoInactivo:
                messagebox.showwarning(
                    "Acción no permitida",
                    "No puede inactivar al único administrador activo."
                )
                return

            tnUsr = tnUsuarioActual

            loCursor.execute("""
                UPDATE USUARIO
                SET
                    Estado = ?,
                    Usr = ?,
                    UsrFecha = date('now','localtime'),
                    UsrHora = time('now','localtime'),
                    FechaModificacion = datetime('now','localtime')
                WHERE Usuario = ?
            """, (tnNuevoEstado, tnUsr, tnUsuario))

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
                "CAMBIAR_ESTADO_USUARIO",
                "USUARIO",
                tnUsuario,
                f"Se cambió el estado del usuario {tnUsuario} a {lcNuevoEstadoTexto}",
                getFechaHoraActualTexto(),
                tnUsr
            ))

            loConn.commit()
            messagebox.showinfo("Estado actualizado", "El estado del usuario fue actualizado.")
            self.loadUsers()

        except Exception as toError:
            loConn.rollback()
            messagebox.showerror("Error", f"No se pudo actualizar el estado.\n{str(toError)}")

        finally:
            loConn.close()

    def isLastActiveAdmin(self, loCursor, tnUsuario):
        loCursor.execute("""
            SELECT COUNT(*)
            FROM USUARIO
            WHERE Rol = ? AND Estado = ?
        """, (gnRolAdmin, gnEstadoActivo))
        lnAdminsActivos = loCursor.fetchone()[0]

        loCursor.execute("""
            SELECT Rol, Estado
            FROM USUARIO
            WHERE Usuario = ?
        """, (tnUsuario,))
        toRow = loCursor.fetchone()

        if not toRow:
            return False

        return (
            toRow["Rol"] == gnRolAdmin and
            toRow["Estado"] == gnEstadoActivo and
            lnAdminsActivos <= 1
        )


class UserFormWindow:
    def __init__(self, toUsersView, txUsuarioData, tnUsuario=None):
        self.toUsersView = toUsersView
        self.txUsuarioData = txUsuarioData
        self.tnUsuario = tnUsuario

        self.loWindow = tk.Toplevel()
        self.loWindow.title("Nuevo usuario" if tnUsuario is None else "Editar usuario")
        self.loWindow.geometry("440x450")
        self.loWindow.resizable(True, True)
        self.loWindow.configure(bg="white")
        self.loWindow.grab_set()

        self.lotxtNombre = None
        self.lotxtNombreUsuario = None
        self.lotxtContrasena = None
        self.lovRol = tk.StringVar(value="empleado")

        self.buildUi()

        if self.tnUsuario is not None:
            self.loadUserData()

    def buildUi(self):
        lcTitulo = "Nuevo usuario" if self.tnUsuario is None else "Editar usuario"

        tk.Label(
            self.loWindow,
            text=lcTitulo,
            font=("Arial", 16, "bold"),
            bg="white",
            fg="#111827"
        ).pack(pady=(20, 20))

        lofrmFormulario = tk.Frame(self.loWindow, bg="white")
        lofrmFormulario.pack(padx=30, fill="x")

        tk.Label(lofrmFormulario, text="Nombre completo *", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.lotxtNombre = tk.Entry(lofrmFormulario, font=("Arial", 11))
        self.lotxtNombre.pack(fill="x", pady=(0, 12))

        tk.Label(lofrmFormulario, text="Usuario *", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.lotxtNombreUsuario = tk.Entry(lofrmFormulario, font=("Arial", 11))
        self.lotxtNombreUsuario.pack(fill="x", pady=(0, 12))

        tk.Label(
            lofrmFormulario,
            text="Contraseña" + (" *" if self.tnUsuario is None else " (opcional)"),
            font=("Arial", 11, "bold"),
            bg="white"
        ).pack(anchor="w", pady=(0, 5))
        self.lotxtContrasena = tk.Entry(lofrmFormulario, font=("Arial", 11), show="*")
        self.lotxtContrasena.pack(fill="x", pady=(0, 12))

        tk.Label(lofrmFormulario, text="Rol *", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))

        lofrmRoles = tk.Frame(lofrmFormulario, bg="white")
        lofrmRoles.pack(fill="x", pady=(0, 12))

        tk.Radiobutton(
            lofrmRoles,
            text="Administrador",
            variable=self.lovRol,
            value="admin",
            bg="white",
            font=("Arial", 11)
        ).pack(side="left", padx=(0, 20))

        tk.Radiobutton(
            lofrmRoles,
            text="Empleado",
            variable=self.lovRol,
            value="empleado",
            bg="white",
            font=("Arial", 11)
        ).pack(side="left")

        tk.Label(
            lofrmFormulario,
            text="En edición, deje la contraseña vacía si no desea cambiarla.",
            font=("Arial", 9),
            bg="white",
            fg="#6b7280"
        ).pack(anchor="w", pady=(0, 10))

        lofrmBotones = tk.Frame(self.loWindow, bg="white")
        lofrmBotones.pack(pady=20)

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

    def loadUserData(self):
        loConn = getConnection()
        loCursor = loConn.cursor()

        loCursor.execute("""
            SELECT Nombre, NombreUsuario, Rol
            FROM USUARIO
            WHERE Usuario = ?
        """, (self.tnUsuario,))
        toRow = loCursor.fetchone()
        loConn.close()

        if not toRow:
            messagebox.showerror("Error", "No se encontró el usuario.")
            self.loWindow.destroy()
            return

        self.lotxtNombre.insert(0, toRow["Nombre"])
        self.lotxtNombreUsuario.insert(0, toRow["NombreUsuario"])
        self.lovRol.set("admin" if toRow["Rol"] == gnRolAdmin else "empleado")

    def confirmSave(self):
        llConfirmado = messagebox.askyesno(
            "Confirmar guardado",
            "¿Desea guardar este usuario?"
        )
        if not llConfirmado:
            return

        self.saveUser()

    def isLastActiveAdmin(self, loCursor, tnUsuario):
        loCursor.execute("""
            SELECT COUNT(*)
            FROM USUARIO
            WHERE Rol = ? AND Estado = ?
        """, (gnRolAdmin, gnEstadoActivo))
        lnAdminsActivos = loCursor.fetchone()[0]

        loCursor.execute("""
            SELECT Rol, Estado
            FROM USUARIO
            WHERE Usuario = ?
        """, (tnUsuario,))
        toRow = loCursor.fetchone()

        if not toRow:
            return False

        return (
            toRow["Rol"] == gnRolAdmin and
            toRow["Estado"] == gnEstadoActivo and
            lnAdminsActivos <= 1
        )

    def saveUser(self):
        lcNombre = self.lotxtNombre.get().strip()
        lcNombreUsuario = self.lotxtNombreUsuario.get().strip()
        lcContrasena = self.lotxtContrasena.get().strip()
        tnRol = gnRolAdmin if self.lovRol.get() == "admin" else gnRolEmpleado

        if not lcNombre or not lcNombreUsuario:
            messagebox.showwarning("Datos requeridos", "Nombre y usuario son obligatorios.")
            return

        if self.tnUsuario is None and not lcContrasena:
            messagebox.showwarning("Datos requeridos", "La contraseña es obligatoria.")
            return

        loConn = getConnection()
        loCursor = loConn.cursor()

        try:
            tnUsr = obtenerUsuarioActualId(self.txUsuarioData)
            tnUsuarioActual = tnUsr

            if self.tnUsuario is None:
                loCursor.execute("SELECT COUNT(*) FROM USUARIO WHERE NombreUsuario = ?", (lcNombreUsuario,))
                if loCursor.fetchone()[0] > 0:
                    messagebox.showwarning("Usuario existente", "Ese nombre de usuario ya existe.")
                    return

                loCursor.execute("""
                    INSERT INTO USUARIO (
                        Nombre,
                        NombreUsuario,
                        Contrasena,
                        Rol,
                        Estado,
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
                    lcNombre,
                    lcNombreUsuario,
                    lcContrasena,
                    tnRol,
                    gnEstadoActivo,
                    tnUsr
                ))

                tnUsuarioNuevo = loCursor.lastrowid

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
                    "CREAR_USUARIO",
                    "USUARIO",
                    tnUsuarioNuevo,
                    f"Se creó el usuario '{lcNombreUsuario}' con rol '{gxRolTexto.get(tnRol, 'N/D')}'",
                    getFechaHoraActualTexto(),
                    tnUsr
                ))

            else:
                loCursor.execute("""
                    SELECT COUNT(*)
                    FROM USUARIO
                    WHERE NombreUsuario = ? AND Usuario != ?
                """, (lcNombreUsuario, self.tnUsuario))
                if loCursor.fetchone()[0] > 0:
                    messagebox.showwarning("Usuario existente", "Ese nombre de usuario ya existe.")
                    return

                if self.tnUsuario == tnUsuarioActual:
                    if self.isLastActiveAdmin(loCursor, self.tnUsuario) and tnRol != gnRolAdmin:
                        messagebox.showwarning(
                            "Acción no permitida",
                            "No puede quitar el rol de administrador al único administrador activo."
                        )
                        return

                if lcContrasena:
                    loCursor.execute("""
                        UPDATE USUARIO
                        SET
                            Nombre = ?,
                            NombreUsuario = ?,
                            Contrasena = ?,
                            Rol = ?,
                            Usr = ?,
                            UsrFecha = date('now','localtime'),
                            UsrHora = time('now','localtime'),
                            FechaModificacion = datetime('now','localtime')
                        WHERE Usuario = ?
                    """, (
                        lcNombre,
                        lcNombreUsuario,
                        lcContrasena,
                        tnRol,
                        tnUsr,
                        self.tnUsuario
                    ))
                else:
                    loCursor.execute("""
                        UPDATE USUARIO
                        SET
                            Nombre = ?,
                            NombreUsuario = ?,
                            Rol = ?,
                            Usr = ?,
                            UsrFecha = date('now','localtime'),
                            UsrHora = time('now','localtime'),
                            FechaModificacion = datetime('now','localtime')
                        WHERE Usuario = ?
                    """, (
                        lcNombre,
                        lcNombreUsuario,
                        tnRol,
                        tnUsr,
                        self.tnUsuario
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
                    "EDITAR_USUARIO",
                    "USUARIO",
                    self.tnUsuario,
                    f"Se editó el usuario '{lcNombreUsuario}'",
                    getFechaHoraActualTexto(),
                    tnUsr
                ))

            loConn.commit()
            messagebox.showinfo("Guardado", "Usuario guardado correctamente.")
            self.toUsersView.loadUsers()
            self.loWindow.destroy()

        except Exception as toError:
            loConn.rollback()
            messagebox.showerror("Error", f"No se pudo guardar el usuario.\n{str(toError)}")

        finally:
            loConn.close()

    def run(self):
        pass