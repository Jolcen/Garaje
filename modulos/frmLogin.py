import os
import tkinter as tk
from tkinter import messagebox

from database.db import getConnection
from modulos.frmPanelPrincipal import DashboardWindow


gxRolesUsuario = {
    1: "admin",
    2: "empleado",
}


class LoginWindow:
    def __init__(self):
        self.loRoot = tk.Tk()
        self.loRoot.title("Inicio de Sesión")
        self.loRoot.geometry("460x500")
        self.loRoot.resizable(False, False)
        self.loRoot.configure(bg="#facc15")

        self.lotxtUsuario = None
        self.lotxtContrasena = None
        self.lolMostrarContrasena = tk.BooleanVar(value=False)
        self.loimgLogo = None

        self.buildUi()
        self.centerWindow()

    def getLogoPath(self):
        lcBaseDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(lcBaseDir, "static", "logo.png")

    def centerWindow(self):
        self.loRoot.update_idletasks()

        lnWidth = 460
        lnHeight = 500
        lnScreenWidth = self.loRoot.winfo_screenwidth()
        lnScreenHeight = self.loRoot.winfo_screenheight()

        lnPosX = int((lnScreenWidth / 2) - (lnWidth / 2))
        lnPosY = int((lnScreenHeight / 2) - (lnHeight / 2))

        self.loRoot.geometry(f"{lnWidth}x{lnHeight}+{lnPosX}+{lnPosY}")

    def buildUi(self):
        lofrmTop = tk.Frame(self.loRoot, bg="#facc15")
        lofrmTop.pack(pady=(0, 0))

        lcLogoPath = self.getLogoPath()
        if os.path.exists(lcLogoPath):
            try:
                self.loimgLogo = tk.PhotoImage(file=lcLogoPath)
                self.loimgLogo = self.loimgLogo.subsample(6, 6)

                loimgLogo = tk.Label(
                    lofrmTop,
                    image=self.loimgLogo,
                    bg="#facc15"
                )
                loimgLogo.pack(pady=(0, 2))
            except Exception:
                lolblLogoAlterno = tk.Label(
                    lofrmTop,
                    text="CAR PARK",
                    font=("Arial", 20, "bold"),
                    bg="#facc15",
                    fg="#1e3a8a"
                )
                lolblLogoAlterno.pack(pady=(0, 2))
        else:
            lolblLogoAlterno = tk.Label(
                lofrmTop,
                text="CAR PARK",
                font=("Arial", 20, "bold"),
                bg="#facc15",
                fg="#1e3a8a"
            )
            lolblLogoAlterno.pack(pady=(0, 2))

        lolblTitulo = tk.Label(
            self.loRoot,
            text="Sistema Carpark",
            font=("Arial", 18, "bold"),
            bg="#facc15",
            fg="#111827"
        )
        lolblTitulo.pack(pady=(0, 2))

        lolblSubtitulo = tk.Label(
            self.loRoot,
            text="Iniciar sesión",
            font=("Arial", 11),
            bg="#facc15",
            fg="#374151"
        )
        lolblSubtitulo.pack(pady=(0, 6))

        lofrmCard = tk.Frame(
            self.loRoot,
            bg="white",
            bd=1,
            relief="solid",
            padx=20,
            pady=20
        )
        lofrmCard.pack(padx=25, fill="x")

        lolblUsuario = tk.Label(
            lofrmCard,
            text="Usuario *",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#111827"
        )
        lolblUsuario.pack(anchor="w", pady=(0, 5))

        self.lotxtUsuario = tk.Entry(lofrmCard, font=("Arial", 11))
        self.lotxtUsuario.pack(fill="x", pady=(0, 12))
        self.lotxtUsuario.focus_set()

        lolblContrasena = tk.Label(
            lofrmCard,
            text="Contraseña *",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#111827"
        )
        lolblContrasena.pack(anchor="w", pady=(0, 5))

        lofrmContrasena = tk.Frame(lofrmCard, bg="white")
        lofrmContrasena.pack(fill="x", pady=(0, 10))

        self.lotxtContrasena = tk.Entry(
            lofrmContrasena,
            font=("Arial", 11),
            show="*"
        )
        self.lotxtContrasena.pack(side="left", fill="x", expand=True)

        lochkMostrar = tk.Checkbutton(
            lofrmContrasena,
            text="Mostrar",
            variable=self.lolMostrarContrasena,
            onvalue=True,
            offvalue=False,
            command=self.togglePasswordVisibility,
            bg="white",
            activebackground="white",
            font=("Arial", 10)
        )
        lochkMostrar.pack(side="left", padx=(10, 0))

        lolblAyuda = tk.Label(
            lofrmCard,
            text="Ingrese sus credenciales para acceder al sistema.",
            font=("Arial", 9),
            bg="white",
            fg="#6b7280"
        )
        lolblAyuda.pack(anchor="w", pady=(2, 0))

        lofrmBotones = tk.Frame(self.loRoot, bg="#facc15")
        lofrmBotones.pack(pady=18)

        locmdIngresar = tk.Button(
            lofrmBotones,
            text="Ingresar",
            font=("Arial", 11, "bold"),
            width=15,
            bg="#1e3a8a",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            command=self.validateLogin
        )
        locmdIngresar.grid(row=0, column=0, padx=8)

        locmdSalir = tk.Button(
            lofrmBotones,
            text="Salir",
            font=("Arial", 11, "bold"),
            width=15,
            bg="#dc2626",
            fg="white",
            activebackground="#b91c1c",
            activeforeground="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            command=self.confirmExit
        )
        locmdSalir.grid(row=0, column=1, padx=8)

        self.lotxtUsuario.bind("<Return>", lambda loEvent: self.validateLogin())
        self.lotxtContrasena.bind("<Return>", lambda loEvent: self.validateLogin())

        self.loRoot.protocol("WM_DELETE_WINDOW", self.confirmExit)

    def togglePasswordVisibility(self):
        if self.lolMostrarContrasena.get():
            self.lotxtContrasena.config(show="")
        else:
            self.lotxtContrasena.config(show="*")

    def authenticateUser(self, tcNombreUsuario, tcContrasena):
        loConn = None

        try:
            loConn = getConnection()
            loCursor = loConn.cursor()

            loCursor.execute("""
                SELECT
                    Usuario,
                    Nombre,
                    NombreUsuario,
                    Contrasena,
                    Rol,
                    Estado
                FROM USUARIO
                WHERE NombreUsuario = ?
            """, (tcNombreUsuario,))

            loUsuario = loCursor.fetchone()

            if not loUsuario:
                return None

            if loUsuario["Contrasena"] != tcContrasena:
                return None

            if loUsuario["Estado"] != 1:
                return "inactive"

            lcRolTexto = gxRolesUsuario.get(loUsuario["Rol"], "empleado")

            loCursor.execute("""
                UPDATE USUARIO
                SET
                    Usr = ?,
                    UsrFecha = date('now', 'localtime'),
                    UsrHora = time('now', 'localtime'),
                    FechaModificacion = datetime('now', 'localtime')
                WHERE Usuario = ?
            """, (loUsuario["Usuario"], loUsuario["Usuario"]))

            loConn.commit()

            return {
                "Usuario": loUsuario["Usuario"],
                "Nombre": loUsuario["Nombre"],
                "NombreUsuario": loUsuario["NombreUsuario"],
                "Rol": lcRolTexto,
                "RolId": int(loUsuario["Rol"]),
                "Estado": loUsuario["Estado"],
            }

        except Exception as loError:
            messagebox.showerror(
                "Error",
                f"No se pudo validar el acceso.\n{str(loError)}"
            )
            return "db_error"

        finally:
            if loConn:
                loConn.close()

    def validateLogin(self):
        lcNombreUsuario = self.lotxtUsuario.get().strip()
        lcContrasena = self.lotxtContrasena.get().strip()

        if not lcNombreUsuario or not lcContrasena:
            messagebox.showwarning(
                "Campos requeridos",
                "Ingrese usuario y contraseña."
            )
            return

        lxResultado = self.authenticateUser(lcNombreUsuario, lcContrasena)

        if lxResultado == "db_error":
            return

        if lxResultado is None:
            self.lotxtContrasena.delete(0, tk.END)
            messagebox.showerror(
                "Acceso denegado",
                "Usuario o contraseña incorrectos."
            )
            return

        if lxResultado == "inactive":
            self.lotxtContrasena.delete(0, tk.END)
            messagebox.showwarning(
                "Usuario inactivo",
                "Este usuario está inactivo."
            )
            return

        messagebox.showinfo(
            "Acceso correcto",
            f"Bienvenido, {lxResultado['Nombre']}."
        )

        self.loRoot.destroy()

        loDashboard = DashboardWindow(lxResultado)
        loDashboard.run()

    def confirmExit(self):
        llConfirmado = messagebox.askyesno(
            "Confirmar salida",
            "¿Desea cerrar el sistema?"
        )

        if llConfirmado:
            self.loRoot.destroy()

    def run(self):
        self.loRoot.mainloop()