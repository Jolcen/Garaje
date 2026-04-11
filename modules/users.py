import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from database.db import get_connection


class UsersView:
    def __init__(self, parent, user_data):
        self.parent = parent
        self.user_data = user_data

        self.tree = None
        self.search_entry = None

    def build(self):
        if self.user_data["rol"] != "admin":
            self.build_access_denied()
            return

        self.build_header()
        self.build_table()
        self.load_users()

    def build_access_denied(self):
        container = tk.Frame(self.parent, bg="white")
        container.pack(fill="both", expand=True)

        tk.Label(
            container,
            text="Acceso restringido",
            font=("Arial", 18, "bold"),
            bg="white",
            fg="#b91c1c"
        ).pack(pady=(80, 10))

        tk.Label(
            container,
            text="Solo el administrador puede gestionar usuarios.",
            font=("Arial", 11),
            bg="white",
            fg="#4b5563"
        ).pack()

    def build_header(self):
        header_frame = tk.Frame(self.parent, bg="white")
        header_frame.pack(fill="x", padx=15, pady=15)

        tk.Label(
            header_frame,
            text="Buscar usuario:",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#111827"
        ).pack(side="left", padx=(0, 8))

        self.search_entry = tk.Entry(header_frame, font=("Arial", 11), width=25)
        self.search_entry.pack(side="left", padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda event: self.load_users())

        tk.Button(
            header_frame,
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
            command=self.load_users
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            header_frame,
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
            command=self.open_new_user_window
        ).pack(side="right")

    def build_table(self):
        table_frame = tk.Frame(self.parent, bg="white")
        table_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        columns = ("id", "nombre", "usuario", "rol", "estado", "fecha_creacion", "acciones")

        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18)

        self.tree.heading("id", text="ID")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("usuario", text="Usuario")
        self.tree.heading("rol", text="Rol")
        self.tree.heading("estado", text="Estado")
        self.tree.heading("fecha_creacion", text="Fecha creación")
        self.tree.heading("acciones", text="Acciones")

        self.tree.column("id", width=60, anchor="center", stretch=False)
        self.tree.column("nombre", width=240, anchor="w", stretch=False)
        self.tree.column("usuario", width=140, anchor="center", stretch=False)
        self.tree.column("rol", width=100, anchor="center", stretch=False)
        self.tree.column("estado", width=100, anchor="center", stretch=False)
        self.tree.column("fecha_creacion", width=160, anchor="center", stretch=False)
        self.tree.column("acciones", width=120, anchor="center", stretch=False)

        scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)

        self.tree.configure(
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>", self.on_double_click)

    def load_users(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        search_value = self.search_entry.get().strip().upper() if self.search_entry else ""

        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT id, nombre, usuario, rol, estado, fecha_creacion
            FROM usuarios
            WHERE 1=1
        """
        params = []

        if search_value:
            query += " AND (UPPER(nombre) LIKE ? OR UPPER(usuario) LIKE ? OR UPPER(rol) LIKE ? OR UPPER(estado) LIKE ?)"
            like_value = f"%{search_value}%"
            params.extend([like_value, like_value, like_value, like_value])

        query += " ORDER BY id ASC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    row[4],
                    row[5],
                    "Doble clic"
                )
            )

    def on_double_click(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        item = self.tree.item(selected[0])
        values = item["values"]
        if not values:
            return

        user_id = values[0]
        username = values[2]
        estado = values[4]

        action_window = tk.Toplevel(self.parent)
        action_window.title("Acciones de usuario")
        action_window.geometry("340x270")
        action_window.resizable(False, False)
        action_window.configure(bg="white")
        action_window.grab_set()

        tk.Label(
            action_window,
            text=f"Usuario: {username}",
            font=("Arial", 14, "bold"),
            bg="white",
            fg="#111827"
        ).pack(pady=(20, 10))

        tk.Button(
            action_window,
            text="Editar",
            font=("Arial", 11, "bold"),
            width=18,
            bg="#f59e0b",
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            command=lambda: self.confirm_edit(user_id, action_window)
        ).pack(pady=8)

        toggle_text = "Inactivar" if estado == "activo" else "Activar"
        toggle_color = "#dc2626" if estado == "activo" else "#16a34a"

        tk.Button(
            action_window,
            text=toggle_text,
            font=("Arial", 11, "bold"),
            width=18,
            bg=toggle_color,
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            command=lambda: self.toggle_user_status(user_id, estado, action_window)
        ).pack(pady=8)

        tk.Button(
            action_window,
            text="Cerrar",
            font=("Arial", 11, "bold"),
            width=18,
            bg="#6b7280",
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            command=action_window.destroy
        ).pack(pady=8)

    def confirm_edit(self, user_id, action_window=None):
        confirmed = messagebox.askyesno(
            "Confirmar edición",
            "¿Desea editar este usuario?"
        )
        if not confirmed:
            return
        self.edit_user(user_id, action_window)

    def open_new_user_window(self):
        UserFormWindow(self, self.user_data, mode="create").run()

    def edit_user(self, user_id, action_window=None):
        if action_window:
            action_window.destroy()
        UserFormWindow(self, self.user_data, mode="edit", user_id=user_id).run()

    def toggle_user_status(self, user_id, current_status, action_window=None):
        if action_window:
            action_window.destroy()

        new_status = "inactivo" if current_status == "activo" else "activo"

        if user_id == self.user_data["id"] and new_status == "inactivo":
            messagebox.showwarning("Acción no permitida", "No puede inactivar su propio usuario.")
            return

        confirm = messagebox.askyesno(
            "Confirmar cambio",
            f"¿Desea cambiar el estado del usuario a '{new_status}'?"
        )
        if not confirm:
            return

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE usuarios
                SET estado = ?
                WHERE id = ?
            """, (new_status, user_id))

            cursor.execute("""
                INSERT INTO bitacora (
                    usuario_id, accion, tabla_afectada, registro_id, descripcion, fecha_evento
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                self.user_data["id"],
                "CAMBIAR_ESTADO_USUARIO",
                "usuarios",
                user_id,
                f"Se cambió el estado del usuario {user_id} a {new_status}",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

            conn.commit()
            messagebox.showinfo("Estado actualizado", "El estado del usuario fue actualizado.")
            self.load_users()

        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"No se pudo actualizar el estado.\n{str(e)}")

        finally:
            conn.close()


class UserFormWindow:
    def __init__(self, users_view, current_user, mode="create", user_id=None):
        self.users_view = users_view
        self.current_user = current_user
        self.mode = mode
        self.user_id = user_id

        self.window = tk.Toplevel()
        self.window.title("Nuevo usuario" if mode == "create" else "Editar usuario")
        self.window.geometry("440x450")
        self.window.resizable(True, True)
        self.window.configure(bg="white")
        self.window.grab_set()

        self.entry_nombre = None
        self.entry_usuario = None
        self.entry_password = None
        self.role_var = tk.StringVar(value="empleado")

        self.build_ui()

        if self.mode == "edit" and self.user_id:
            self.load_user_data()

    def build_ui(self):
        title = "Nuevo usuario" if self.mode == "create" else "Editar usuario"

        tk.Label(
            self.window,
            text=title,
            font=("Arial", 16, "bold"),
            bg="white",
            fg="#111827"
        ).pack(pady=(20, 20))

        form = tk.Frame(self.window, bg="white")
        form.pack(padx=30, fill="x")

        tk.Label(form, text="Nombre completo *", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.entry_nombre = tk.Entry(form, font=("Arial", 11))
        self.entry_nombre.pack(fill="x", pady=(0, 12))

        tk.Label(form, text="Usuario *", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.entry_usuario = tk.Entry(form, font=("Arial", 11))
        self.entry_usuario.pack(fill="x", pady=(0, 12))

        tk.Label(form, text="Contraseña" + (" *" if self.mode == "create" else " (opcional)"), font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.entry_password = tk.Entry(form, font=("Arial", 11), show="*")
        self.entry_password.pack(fill="x", pady=(0, 12))

        tk.Label(form, text="Rol *", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))

        roles_frame = tk.Frame(form, bg="white")
        roles_frame.pack(fill="x", pady=(0, 12))

        tk.Radiobutton(
            roles_frame,
            text="Administrador",
            variable=self.role_var,
            value="admin",
            bg="white",
            font=("Arial", 11)
        ).pack(side="left", padx=(0, 20))

        tk.Radiobutton(
            roles_frame,
            text="Empleado",
            variable=self.role_var,
            value="empleado",
            bg="white",
            font=("Arial", 11)
        ).pack(side="left")

        info_text = "En edición, deje la contraseña vacía si no desea cambiarla."
        tk.Label(
            form,
            text=info_text,
            font=("Arial", 9),
            bg="white",
            fg="#6b7280"
        ).pack(anchor="w", pady=(0, 10))

        buttons = tk.Frame(self.window, bg="white")
        buttons.pack(pady=20)

        tk.Button(
            buttons,
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
            command=self.confirm_save
        ).grid(row=0, column=0, padx=10)

        tk.Button(
            buttons,
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
            command=self.window.destroy
        ).grid(row=0, column=1, padx=10)

    def load_user_data(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT nombre, usuario, rol
            FROM usuarios
            WHERE id = ?
        """, (self.user_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            messagebox.showerror("Error", "No se encontró el usuario.")
            self.window.destroy()
            return

        self.entry_nombre.insert(0, row[0])
        self.entry_usuario.insert(0, row[1])
        self.role_var.set(row[2])

    def confirm_save(self):
        confirmed = messagebox.askyesno(
            "Confirmar guardado",
            "¿Desea guardar este usuario?"
        )
        if not confirmed:
            return

        self.save_user()

    def is_last_active_admin(self, cursor, user_id):
        cursor.execute("""
            SELECT COUNT(*)
            FROM usuarios
            WHERE rol = 'admin' AND estado = 'activo'
        """)
        active_admins = cursor.fetchone()[0]

        cursor.execute("""
            SELECT rol, estado
            FROM usuarios
            WHERE id = ?
        """, (user_id,))
        row = cursor.fetchone()

        if not row:
            return False

        current_role, current_status = row[0], row[1]

        return current_role == "admin" and current_status == "activo" and active_admins <= 1

    def save_user(self):
        nombre = self.entry_nombre.get().strip()
        usuario = self.entry_usuario.get().strip()
        password = self.entry_password.get().strip()
        rol = self.role_var.get()

        if not nombre or not usuario:
            messagebox.showwarning("Datos requeridos", "Nombre y usuario son obligatorios.")
            return

        if self.mode == "create" and not password:
            messagebox.showwarning("Datos requeridos", "La contraseña es obligatoria.")
            return

        conn = get_connection()
        cursor = conn.cursor()

        try:
            if self.mode == "create":
                cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = ?", (usuario,))
                if cursor.fetchone()[0] > 0:
                    messagebox.showwarning("Usuario existente", "Ese nombre de usuario ya existe.")
                    return

                cursor.execute("""
                    INSERT INTO usuarios (nombre, usuario, password, rol, estado, fecha_creacion)
                    VALUES (?, ?, ?, ?, 'activo', ?)
                """, (
                    nombre,
                    usuario,
                    password,
                    rol,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

                new_user_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO bitacora (
                        usuario_id, accion, tabla_afectada, registro_id, descripcion, fecha_evento
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.current_user["id"],
                    "CREAR_USUARIO",
                    "usuarios",
                    new_user_id,
                    f"Se creó el usuario '{usuario}' con rol '{rol}'",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

            else:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM usuarios
                    WHERE usuario = ? AND id != ?
                """, (usuario, self.user_id))
                if cursor.fetchone()[0] > 0:
                    messagebox.showwarning("Usuario existente", "Ese nombre de usuario ya existe.")
                    return

                if self.user_id == self.current_user["id"]:
                    if self.is_last_active_admin(cursor, self.user_id) and rol != "admin":
                        messagebox.showwarning(
                            "Acción no permitida",
                            "No puede quitar el rol de administrador al único administrador activo."
                        )
                        return

                if password:
                    cursor.execute("""
                        UPDATE usuarios
                        SET nombre = ?, usuario = ?, password = ?, rol = ?
                        WHERE id = ?
                    """, (nombre, usuario, password, rol, self.user_id))
                else:
                    cursor.execute("""
                        UPDATE usuarios
                        SET nombre = ?, usuario = ?, rol = ?
                        WHERE id = ?
                    """, (nombre, usuario, rol, self.user_id))

                cursor.execute("""
                    INSERT INTO bitacora (
                        usuario_id, accion, tabla_afectada, registro_id, descripcion, fecha_evento
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.current_user["id"],
                    "EDITAR_USUARIO",
                    "usuarios",
                    self.user_id,
                    f"Se editó el usuario '{usuario}'",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

            conn.commit()
            messagebox.showinfo("Guardado", "Usuario guardado correctamente.")
            self.users_view.load_users()
            self.window.destroy()

        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"No se pudo guardar el usuario.\n{str(e)}")

        finally:
            conn.close()

    def run(self):
        pass