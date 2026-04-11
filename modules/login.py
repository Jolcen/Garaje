import tkinter as tk
from tkinter import messagebox

from database.db import get_connection
from modules.dashboard import DashboardWindow


class LoginWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Inicio de Sesión")
        self.root.geometry("460x430")
        self.root.resizable(False, False)
        self.root.configure(bg="#f3f4f6")

        self.entry_usuario = None
        self.entry_password = None
        self.show_password_var = tk.BooleanVar(value=False)

        self.build_ui()
        self.center_window()

    def center_window(self):
        self.root.update_idletasks()
        width = 460
        height = 430
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))

        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def build_ui(self):
        title_label = tk.Label(
            self.root,
            text="Sistema Carpark",
            font=("Arial", 18, "bold"),
            bg="#f3f4f6",
            fg="#111827"
        )
        title_label.pack(pady=(28, 8))

        subtitle_label = tk.Label(
            self.root,
            text="Iniciar sesión",
            font=("Arial", 11),
            bg="#f3f4f6",
            fg="#4b5563"
        )
        subtitle_label.pack(pady=(0, 18))

        card = tk.Frame(
            self.root,
            bg="white",
            bd=1,
            relief="solid",
            padx=20,
            pady=20
        )
        card.pack(padx=25, fill="x")

        usuario_label = tk.Label(
            card,
            text="Usuario *",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#111827"
        )
        usuario_label.pack(anchor="w", pady=(0, 5))

        self.entry_usuario = tk.Entry(card, font=("Arial", 11))
        self.entry_usuario.pack(fill="x", pady=(0, 12))
        self.entry_usuario.focus_set()

        password_label = tk.Label(
            card,
            text="Contraseña *",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#111827"
        )
        password_label.pack(anchor="w", pady=(0, 5))

        password_frame = tk.Frame(card, bg="white")
        password_frame.pack(fill="x", pady=(0, 8))

        self.entry_password = tk.Entry(password_frame, font=("Arial", 11), show="*")
        self.entry_password.pack(side="left", fill="x", expand=True)

        toggle_button = tk.Checkbutton(
            password_frame,
            text="Mostrar",
            variable=self.show_password_var,
            onvalue=True,
            offvalue=False,
            command=self.toggle_password_visibility,
            bg="white",
            font=("Arial", 10),
            activebackground="white"
        )
        toggle_button.pack(side="left", padx=(10, 0))

        helper_label = tk.Label(
            card,
            text="Ingrese sus credenciales para acceder al sistema.",
            font=("Arial", 9),
            bg="white",
            fg="#6b7280"
        )
        helper_label.pack(anchor="w", pady=(0, 4))

        buttons_frame = tk.Frame(self.root, bg="#f3f4f6")
        buttons_frame.pack(pady=20)

        login_button = tk.Button(
            buttons_frame,
            text="Ingresar",
            font=("Arial", 11, "bold"),
            width=16,
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            command=self.login
        )
        login_button.grid(row=0, column=0, padx=8)

        exit_button = tk.Button(
            buttons_frame,
            text="Salir",
            font=("Arial", 11, "bold"),
            width=16,
            bg="#dc2626",
            fg="white",
            activebackground="#b91c1c",
            activeforeground="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            command=self.confirm_exit
        )
        exit_button.grid(row=0, column=1, padx=8)

        self.entry_usuario.bind("<Return>", lambda event: self.login())
        self.entry_password.bind("<Return>", lambda event: self.login())

        self.root.protocol("WM_DELETE_WINDOW", self.confirm_exit)

    def toggle_password_visibility(self):
        if self.show_password_var.get():
            self.entry_password.config(show="")
        else:
            self.entry_password.config(show="*")

    def authenticate_user(self, usuario, password):
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, nombre, usuario, rol, estado
                FROM usuarios
                WHERE usuario = ? AND password = ?
            """, (usuario, password))

            user = cursor.fetchone()

            if not user:
                return None

            if user[4] != "activo":
                return "inactive"

            return {
                "id": user[0],
                "nombre": user[1],
                "usuario": user[2],
                "rol": user[3],
                "estado": user[4]
            }

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo validar el acceso.\n{str(e)}")
            return "db_error"

        finally:
            if conn:
                conn.close()

    def login(self):
        usuario = self.entry_usuario.get().strip()
        password = self.entry_password.get().strip()

        if not usuario or not password:
            messagebox.showwarning("Campos requeridos", "Ingrese usuario y contraseña.")
            return

        result = self.authenticate_user(usuario, password)

        if result == "db_error":
            return

        if result is None:
            self.entry_password.delete(0, tk.END)
            messagebox.showerror("Acceso denegado", "Usuario o contraseña incorrectos.")
            return

        if result == "inactive":
            self.entry_password.delete(0, tk.END)
            messagebox.showwarning("Usuario inactivo", "Este usuario está inactivo.")
            return

        messagebox.showinfo("Acceso correcto", f"Bienvenido, {result['nombre']}.")
        self.root.destroy()

        dashboard = DashboardWindow(result)
        dashboard.run()

    def confirm_exit(self):
        confirmed = messagebox.askyesno(
            "Confirmar salida",
            "¿Desea cerrar el sistema?"
        )
        if confirmed:
            self.root.destroy()

    def run(self):
        self.root.mainloop()