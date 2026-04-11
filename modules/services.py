import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from database.db import get_connection


class ServicesView:
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
        self.load_services()

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
            text="Solo el administrador puede gestionar servicios.",
            font=("Arial", 11),
            bg="white",
            fg="#4b5563"
        ).pack()

    def build_header(self):
        header_frame = tk.Frame(self.parent, bg="white")
        header_frame.pack(fill="x", padx=15, pady=15)

        tk.Label(
            header_frame,
            text="Buscar servicio:",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#111827"
        ).pack(side="left", padx=(0, 8))

        self.search_entry = tk.Entry(header_frame, font=("Arial", 11), width=25)
        self.search_entry.pack(side="left", padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda event: self.load_services())

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
            command=self.load_services
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            header_frame,
            text="Nuevo servicio",
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
            command=self.open_new_service_window
        ).pack(side="right")

    def build_table(self):
        table_frame = tk.Frame(self.parent, bg="white")
        table_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        columns = (
            "id",
            "nombre",
            "descripcion",
            "precio",
            "duracion",
            "estado",
            "acciones"
        )

        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18)

        self.tree.heading("id", text="ID")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("descripcion", text="Descripción")
        self.tree.heading("precio", text="Precio")
        self.tree.heading("duracion", text="Duración estimada")
        self.tree.heading("estado", text="Estado")
        self.tree.heading("acciones", text="Acciones")

        self.tree.column("id", width=55, anchor="center", stretch=False)
        self.tree.column("nombre", width=170, anchor="w", stretch=False)
        self.tree.column("descripcion", width=320, anchor="w", stretch=False)
        self.tree.column("precio", width=100, anchor="center", stretch=False)
        self.tree.column("duracion", width=140, anchor="center", stretch=False)
        self.tree.column("estado", width=90, anchor="center", stretch=False)
        self.tree.column("acciones", width=110, anchor="center", stretch=False)

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

    def load_services(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        search_value = self.search_entry.get().strip().upper() if self.search_entry else ""

        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT id, nombre, descripcion, precio, duracion_estimada, estado
            FROM servicios
            WHERE 1=1
        """
        params = []

        if search_value:
            query += """
                AND (
                    UPPER(IFNULL(nombre, '')) LIKE ?
                    OR UPPER(IFNULL(descripcion, '')) LIKE ?
                    OR UPPER(IFNULL(estado, '')) LIKE ?
                )
            """
            like_value = f"%{search_value}%"
            params.extend([like_value, like_value, like_value])

        query += " ORDER BY id ASC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            duracion = f"{row[4]} min" if row[4] is not None else "-"
            self.tree.insert(
                "",
                "end",
                values=(
                    row[0],
                    row[1],
                    row[2] if row[2] else "",
                    f"Bs {float(row[3]):.2f}",
                    duracion,
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

        service_id = values[0]
        service_name = values[1]
        current_status = values[5]

        action_window = tk.Toplevel(self.parent)
        action_window.title("Acciones de servicio")
        action_window.geometry("340x270")
        action_window.resizable(False, False)
        action_window.configure(bg="white")
        action_window.grab_set()

        tk.Label(
            action_window,
            text=f"Servicio: {service_name}",
            font=("Arial", 14, "bold"),
            bg="white",
            fg="#111827",
            wraplength=260
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
            command=lambda: self.confirm_edit(service_id, action_window)
        ).pack(pady=8)

        toggle_text = "Inactivar" if current_status == "activo" else "Activar"
        toggle_color = "#dc2626" if current_status == "activo" else "#16a34a"

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
            command=lambda: self.toggle_service_status(service_id, current_status, action_window)
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

    def confirm_edit(self, service_id, action_window=None):
        confirmed = messagebox.askyesno(
            "Confirmar edición",
            "¿Desea editar este servicio?"
        )
        if not confirmed:
            return
        self.edit_service(service_id, action_window)

    def open_new_service_window(self):
        ServiceFormWindow(self, self.user_data, mode="create").run()

    def edit_service(self, service_id, action_window=None):
        if action_window:
            action_window.destroy()
        ServiceFormWindow(self, self.user_data, mode="edit", service_id=service_id).run()

    def toggle_service_status(self, service_id, current_status, action_window=None):
        if action_window:
            action_window.destroy()

        new_status = "inactivo" if current_status == "activo" else "activo"

        confirm = messagebox.askyesno(
            "Confirmar cambio",
            f"¿Desea cambiar el estado del servicio a '{new_status}'?"
        )
        if not confirm:
            return

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE servicios
                SET estado = ?
                WHERE id = ?
            """, (new_status, service_id))

            cursor.execute("""
                INSERT INTO bitacora (
                    usuario_id, accion, tabla_afectada, registro_id, descripcion, fecha_evento
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                self.user_data["id"],
                "CAMBIAR_ESTADO_SERVICIO",
                "servicios",
                service_id,
                f"Se cambió el estado del servicio {service_id} a {new_status}",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

            conn.commit()
            messagebox.showinfo("Estado actualizado", "El estado del servicio fue actualizado.")
            self.load_services()

        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"No se pudo actualizar el estado.\n{str(e)}")

        finally:
            conn.close()


class ServiceFormWindow:
    def __init__(self, services_view, current_user, mode="create", service_id=None):
        self.services_view = services_view
        self.current_user = current_user
        self.mode = mode
        self.service_id = service_id

        self.window = tk.Toplevel()
        self.window.title("Nuevo servicio" if mode == "create" else "Editar servicio")
        self.window.geometry("460x500")
        self.window.resizable(True, True)
        self.window.configure(bg="white")
        self.window.grab_set()

        self.entry_nombre = None
        self.text_descripcion = None
        self.entry_precio = None
        self.entry_duracion = None

        self.build_ui()

        if self.mode == "edit" and self.service_id:
            self.load_service_data()

    def build_ui(self):
        title = "Nuevo servicio" if self.mode == "create" else "Editar servicio"

        tk.Label(
            self.window,
            text=title,
            font=("Arial", 16, "bold"),
            bg="white",
            fg="#111827"
        ).pack(pady=(20, 20))

        form = tk.Frame(self.window, bg="white")
        form.pack(padx=30, fill="x")

        tk.Label(form, text="Nombre *", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.entry_nombre = tk.Entry(form, font=("Arial", 11))
        self.entry_nombre.pack(fill="x", pady=(0, 12))

        tk.Label(form, text="Descripción", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.text_descripcion = tk.Text(form, font=("Arial", 11), height=4)
        self.text_descripcion.pack(fill="x", pady=(0, 12))

        tk.Label(form, text="Precio (Bs) *", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.entry_precio = tk.Entry(form, font=("Arial", 11))
        self.entry_precio.pack(fill="x", pady=(0, 12))

        tk.Label(form, text="Duración estimada (minutos)", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.entry_duracion = tk.Entry(form, font=("Arial", 11))
        self.entry_duracion.pack(fill="x", pady=(0, 12))

        tk.Label(
            form,
            text="La duración es opcional. Puede dejarla vacía.",
            font=("Arial", 9),
            bg="white",
            fg="#6b7280"
        ).pack(anchor="w", pady=(0, 12))

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

    def load_service_data(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT nombre, descripcion, precio, duracion_estimada
            FROM servicios
            WHERE id = ?
        """, (self.service_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            messagebox.showerror("Error", "No se encontró el servicio.")
            self.window.destroy()
            return

        self.entry_nombre.insert(0, row[0])
        self.text_descripcion.insert("1.0", row[1] if row[1] else "")
        self.entry_precio.insert(0, str(row[2]))
        self.entry_duracion.insert(0, "" if row[3] is None else str(row[3]))

    def confirm_save(self):
        confirmed = messagebox.askyesno(
            "Confirmar guardado",
            "¿Desea guardar este servicio?"
        )
        if not confirmed:
            return

        self.save_service()

    def save_service(self):
        nombre = self.entry_nombre.get().strip()
        descripcion = self.text_descripcion.get("1.0", "end").strip()
        precio_str = self.entry_precio.get().strip()
        duracion_str = self.entry_duracion.get().strip()

        if not nombre or not precio_str:
            messagebox.showwarning("Datos requeridos", "Nombre y precio son obligatorios.")
            return

        try:
            precio = float(precio_str)
        except ValueError:
            messagebox.showwarning("Dato inválido", "El precio debe ser numérico.")
            return

        if precio < 0:
            messagebox.showwarning("Dato inválido", "El precio no puede ser negativo.")
            return

        duracion = None
        if duracion_str:
            try:
                duracion = int(duracion_str)
            except ValueError:
                messagebox.showwarning("Dato inválido", "La duración debe ser un número entero.")
                return

            if duracion < 0:
                messagebox.showwarning("Dato inválido", "La duración no puede ser negativa.")
                return

        conn = get_connection()
        cursor = conn.cursor()

        try:
            if self.mode == "create":
                cursor.execute("SELECT COUNT(*) FROM servicios WHERE UPPER(nombre) = ?", (nombre.upper(),))
                if cursor.fetchone()[0] > 0:
                    messagebox.showwarning("Servicio existente", "Ya existe un servicio con ese nombre.")
                    return

                cursor.execute("""
                    INSERT INTO servicios (
                        nombre, descripcion, precio, duracion_estimada, estado, fecha_creacion
                    )
                    VALUES (?, ?, ?, ?, 'activo', ?)
                """, (
                    nombre,
                    descripcion if descripcion else None,
                    precio,
                    duracion,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

                new_service_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO bitacora (
                        usuario_id, accion, tabla_afectada, registro_id, descripcion, fecha_evento
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.current_user["id"],
                    "CREAR_SERVICIO",
                    "servicios",
                    new_service_id,
                    f"Se creó el servicio '{nombre}'",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

            else:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM servicios
                    WHERE UPPER(nombre) = ? AND id != ?
                """, (nombre.upper(), self.service_id))
                if cursor.fetchone()[0] > 0:
                    messagebox.showwarning("Servicio existente", "Ya existe un servicio con ese nombre.")
                    return

                cursor.execute("""
                    UPDATE servicios
                    SET nombre = ?, descripcion = ?, precio = ?, duracion_estimada = ?
                    WHERE id = ?
                """, (
                    nombre,
                    descripcion if descripcion else None,
                    precio,
                    duracion,
                    self.service_id
                ))

                cursor.execute("""
                    INSERT INTO bitacora (
                        usuario_id, accion, tabla_afectada, registro_id, descripcion, fecha_evento
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.current_user["id"],
                    "EDITAR_SERVICIO",
                    "servicios",
                    self.service_id,
                    f"Se editó el servicio '{nombre}'",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

            conn.commit()
            messagebox.showinfo("Guardado", "Servicio guardado correctamente.")
            self.services_view.load_services()
            self.window.destroy()

        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"No se pudo guardar el servicio.\n{str(e)}")

        finally:
            conn.close()

    def run(self):
        pass