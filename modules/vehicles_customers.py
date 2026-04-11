import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from database.db import get_connection


class VehiclesCustomersView:
    def __init__(self, parent, user_data):
        self.parent = parent
        self.user_data = user_data

        self.tree = None
        self.search_entry = None

    def build(self):
        self.build_header()
        self.build_table()
        self.load_records()

    def build_header(self):
        header_frame = tk.Frame(self.parent, bg="white")
        header_frame.pack(fill="x", padx=15, pady=15)

        tk.Label(
            header_frame,
            text="Buscar:",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#111827"
        ).pack(side="left", padx=(0, 8))

        self.search_entry = tk.Entry(header_frame, font=("Arial", 11), width=30)
        self.search_entry.pack(side="left", padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda event: self.load_records())

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
            command=self.load_records
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            header_frame,
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
            command=self.open_new_window
        ).pack(side="right")

    def build_table(self):
        table_frame = tk.Frame(self.parent, bg="white")
        table_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        columns = (
            "id",
            "placa",
            "tipo_vehiculo",
            "marca",
            "modelo",
            "color",
            "cliente",
            "telefono",
            "acciones"
        )

        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18)

        self.tree.heading("id", text="ID")
        self.tree.heading("placa", text="Placa")
        self.tree.heading("tipo_vehiculo", text="Tipo")
        self.tree.heading("marca", text="Marca")
        self.tree.heading("modelo", text="Modelo")
        self.tree.heading("color", text="Color")
        self.tree.heading("cliente", text="Cliente")
        self.tree.heading("telefono", text="Teléfono")
        self.tree.heading("acciones", text="Acciones")

        self.tree.column("id", width=55, anchor="center", stretch=False)
        self.tree.column("placa", width=100, anchor="center", stretch=False)
        self.tree.column("tipo_vehiculo", width=90, anchor="center", stretch=False)
        self.tree.column("marca", width=100, anchor="center", stretch=False)
        self.tree.column("modelo", width=100, anchor="center", stretch=False)
        self.tree.column("color", width=90, anchor="center", stretch=False)
        self.tree.column("cliente", width=180, anchor="w", stretch=False)
        self.tree.column("telefono", width=110, anchor="center", stretch=False)
        self.tree.column("acciones", width=100, anchor="center", stretch=False)

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

    def load_records(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        search_value = self.search_entry.get().strip().upper() if self.search_entry else ""

        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                v.id,
                v.placa,
                v.tipo_vehiculo,
                v.marca,
                v.modelo,
                v.color,
                c.nombre,
                c.telefono
            FROM vehiculos v
            LEFT JOIN clientes c ON v.cliente_id = c.id
            WHERE 1=1
        """
        params = []

        if search_value:
            like_value = f"%{search_value}%"
            like_plate_value = f"%{search_value.replace(' ', '')}%"

            query += """
                AND (
                    REPLACE(UPPER(v.placa), ' ', '') LIKE ?
                    OR UPPER(v.tipo_vehiculo) LIKE ?
                    OR UPPER(IFNULL(v.marca, '')) LIKE ?
                    OR UPPER(IFNULL(v.modelo, '')) LIKE ?
                    OR UPPER(IFNULL(v.color, '')) LIKE ?
                    OR UPPER(IFNULL(c.nombre, '')) LIKE ?
                    OR IFNULL(c.telefono, '') LIKE ?
                )
            """
            params.extend([
                like_plate_value,
                like_value,
                like_value,
                like_value,
                like_value,
                like_value,
                f"%{search_value}%"
            ])

        query += " ORDER BY v.id ASC"

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
                    row[3] if row[3] else "",
                    row[4] if row[4] else "",
                    row[5] if row[5] else "",
                    row[6] if row[6] else "",
                    row[7] if row[7] else "",
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

        vehicle_id = values[0]
        plate = values[1]

        action_window = tk.Toplevel(self.parent)
        action_window.title("Acciones")
        action_window.geometry("340x250")
        action_window.resizable(False, False)
        action_window.configure(bg="white")
        action_window.grab_set()

        tk.Label(
            action_window,
            text=f"Vehículo: {plate}",
            font=("Arial", 14, "bold"),
            bg="white",
            fg="#111827"
        ).pack(pady=(20, 14))

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
            command=lambda: self.confirm_edit(vehicle_id, action_window)
        ).pack(pady=8)

        tk.Button(
            action_window,
            text="Eliminar",
            font=("Arial", 11, "bold"),
            width=18,
            bg="#dc2626",
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            command=lambda: self.delete_record(vehicle_id, action_window)
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

    def confirm_edit(self, vehicle_id, action_window=None):
        confirmed = messagebox.askyesno(
            "Confirmar edición",
            "¿Desea editar este registro?"
        )
        if not confirmed:
            return

        self.edit_record(vehicle_id, action_window)

    def open_new_window(self):
        VehicleCustomerFormWindow(self, self.user_data, mode="create").run()

    def edit_record(self, vehicle_id, action_window=None):
        if action_window:
            action_window.destroy()
        VehicleCustomerFormWindow(self, self.user_data, mode="edit", vehicle_id=vehicle_id).run()

    def delete_record(self, vehicle_id, action_window=None):
        confirmed = messagebox.askyesno(
            "Confirmar eliminación",
            "¿Está seguro de eliminar este registro?\n\nEsta acción no se puede deshacer."
        )
        if not confirmed:
            return

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT placa, cliente_id
                FROM vehiculos
                WHERE id = ?
            """, (vehicle_id,))
            row = cursor.fetchone()

            if not row:
                messagebox.showerror("Error", "No se encontró el vehículo.")
                return

            placa = row[0]
            cliente_id = row[1]

            cursor.execute("""
                SELECT COUNT(*)
                FROM operaciones
                WHERE vehiculo_id = ? AND estado = 'activo'
            """, (vehicle_id,))
            active_operations = cursor.fetchone()[0]

            if active_operations > 0:
                messagebox.showwarning(
                    "No permitido",
                    "No se puede eliminar el vehículo porque tiene operaciones activas."
                )
                return

            cursor.execute("""
                DELETE FROM vehiculos
                WHERE id = ?
            """, (vehicle_id,))

            if cliente_id:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM vehiculos
                    WHERE cliente_id = ?
                """, (cliente_id,))
                used_by_other_vehicles = cursor.fetchone()[0]

                if used_by_other_vehicles == 0:
                    cursor.execute("""
                        DELETE FROM clientes
                        WHERE id = ?
                    """, (cliente_id,))

            cursor.execute("""
                INSERT INTO bitacora (
                    usuario_id, accion, tabla_afectada, registro_id, descripcion, fecha_evento
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                self.user_data["id"],
                "ELIMINAR_VEHICULO_CLIENTE",
                "vehiculos",
                vehicle_id,
                f"Se eliminó el vehículo '{placa}'",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

            conn.commit()

            if action_window:
                action_window.destroy()

            messagebox.showinfo("Eliminado", "Registro eliminado correctamente.")
            self.load_records()

        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"No se pudo eliminar el registro.\n{str(e)}")

        finally:
            conn.close()


class VehicleCustomerFormWindow:
    def __init__(self, view, current_user, mode="create", vehicle_id=None):
        self.view = view
        self.current_user = current_user
        self.mode = mode
        self.vehicle_id = vehicle_id

        self.window = tk.Toplevel()
        self.window.title("Nuevo vehículo / cliente" if mode == "create" else "Editar vehículo / cliente")
        self.window.geometry("560x700")
        self.window.minsize(520, 620)
        self.window.resizable(True, True)
        self.window.configure(bg="white")
        self.window.grab_set()

        self.entry_placa_numero = None
        self.entry_placa_letras = None
        self.vehicle_type_var = tk.StringVar(value="auto")
        self.entry_marca = None
        self.entry_modelo = None
        self.entry_color = None

        self.entry_cliente = None
        self.entry_telefono = None
        self.entry_documento = None
        self.text_observacion = None

        self.loaded_customer_id = None

        self.build_ui()

        if self.mode == "edit" and self.vehicle_id:
            self.load_data()

    def build_scrollable_form(self):
        outer = tk.Frame(self.window, bg="white")
        outer.pack(fill="both", expand=True, padx=10, pady=10)

        canvas = tk.Canvas(outer, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)

        scrollable_frame = tk.Frame(canvas, bg="white")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        return scrollable_frame

    def build_ui(self):
        form = self.build_scrollable_form()

        title = "Nuevo vehículo / cliente" if self.mode == "create" else "Editar vehículo / cliente"

        tk.Label(
            form,
            text=title,
            font=("Arial", 16, "bold"),
            bg="white",
            fg="#111827"
        ).pack(pady=(10, 15))

        content = tk.Frame(form, bg="white")
        content.pack(fill="both", expand=True, padx=20)

        tk.Label(
            content,
            text="Datos del vehículo",
            font=("Arial", 12, "bold"),
            bg="white",
            fg="#111827"
        ).pack(anchor="w", pady=(5, 10))

        tk.Label(content, text="Placa *", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))

        plate_frame = tk.Frame(content, bg="white")
        plate_frame.pack(fill="x", pady=(0, 4))

        tk.Label(plate_frame, text="Número", font=("Arial", 10), bg="white").pack(side="left", padx=(0, 6))
        self.entry_placa_numero = tk.Entry(plate_frame, font=("Arial", 11), width=10)
        self.entry_placa_numero.pack(side="left", padx=(0, 16))
        self.entry_placa_numero.bind("<KeyRelease>", self.only_numbers_plate)

        tk.Label(plate_frame, text="Letras", font=("Arial", 10), bg="white").pack(side="left", padx=(0, 6))
        self.entry_placa_letras = tk.Entry(plate_frame, font=("Arial", 11), width=8)
        self.entry_placa_letras.pack(side="left")
        self.entry_placa_letras.bind("<KeyRelease>", self.only_letters_plate)

        tk.Label(
            content,
            text="Formato referencial: 1023 ADV",
            font=("Arial", 9),
            bg="white",
            fg="#6b7280"
        ).pack(anchor="w", pady=(0, 12))

        tk.Label(content, text="Tipo de vehículo *", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        type_frame = tk.Frame(content, bg="white")
        type_frame.pack(fill="x", pady=(0, 12))

        tk.Radiobutton(
            type_frame,
            text="Auto",
            variable=self.vehicle_type_var,
            value="auto",
            bg="white",
            font=("Arial", 11)
        ).pack(side="left", padx=(0, 16))

        tk.Radiobutton(
            type_frame,
            text="Moto",
            variable=self.vehicle_type_var,
            value="moto",
            bg="white",
            font=("Arial", 11)
        ).pack(side="left", padx=(0, 16))

        tk.Label(content, text="Marca", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.entry_marca = tk.Entry(content, font=("Arial", 11))
        self.entry_marca.pack(fill="x", pady=(0, 12))

        tk.Label(content, text="Modelo", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.entry_modelo = tk.Entry(content, font=("Arial", 11))
        self.entry_modelo.pack(fill="x", pady=(0, 12))

        tk.Label(content, text="Color", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 18))
        self.entry_color = tk.Entry(content, font=("Arial", 11))
        self.entry_color.pack(fill="x", pady=(0, 18))

        tk.Label(
            content,
            text="Datos del cliente (opcionales)",
            font=("Arial", 12, "bold"),
            bg="white",
            fg="#111827"
        ).pack(anchor="w", pady=(5, 10))

        tk.Label(content, text="Nombre", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.entry_cliente = tk.Entry(content, font=("Arial", 11))
        self.entry_cliente.pack(fill="x", pady=(0, 12))

        tk.Label(content, text="Teléfono", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.entry_telefono = tk.Entry(content, font=("Arial", 11))
        self.entry_telefono.pack(fill="x", pady=(0, 12))

        tk.Label(content, text="Documento", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.entry_documento = tk.Entry(content, font=("Arial", 11))
        self.entry_documento.pack(fill="x", pady=(0, 12))

        tk.Label(content, text="Observación", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.text_observacion = tk.Text(content, font=("Arial", 11), height=4)
        self.text_observacion.pack(fill="x", pady=(0, 16))

        buttons = tk.Frame(form, bg="white")
        buttons.pack(pady=15)

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

    def only_numbers_plate(self, event=None):
        value = self.entry_placa_numero.get()
        filtered = "".join(ch for ch in value if ch.isdigit())[:4]
        if value != filtered:
            self.entry_placa_numero.delete(0, "end")
            self.entry_placa_numero.insert(0, filtered)

    def only_letters_plate(self, event=None):
        value = self.entry_placa_letras.get()
        filtered = "".join(ch for ch in value if ch.isalpha()).upper()[:3]
        if value != filtered:
            self.entry_placa_letras.delete(0, "end")
            self.entry_placa_letras.insert(0, filtered)

    def validate_plate(self):
        numero = self.entry_placa_numero.get().strip()
        letras = self.entry_placa_letras.get().strip().upper()

        if not numero or not letras:
            raise ValueError("La placa es obligatoria.")

        if not numero.isdigit():
            raise ValueError("La parte numérica de la placa solo debe contener números.")

        if len(numero) < 2 or len(numero) > 4:
            raise ValueError("La parte numérica de la placa debe tener entre 2 y 4 dígitos.")

        if not letras.isalpha():
            raise ValueError("La parte de letras de la placa solo debe contener letras.")

        if len(letras) != 3:
            raise ValueError("La placa debe tener exactamente 3 letras.")

        return f"{numero} {letras}"

    def split_plate(self, placa):
        if not placa:
            return "", ""

        cleaned = placa.strip().upper().replace("-", " ")
        parts = cleaned.split()

        if len(parts) >= 2:
            return parts[0], parts[1]

        compact = cleaned.replace(" ", "")
        numero = "".join(ch for ch in compact if ch.isdigit())
        letras = "".join(ch for ch in compact if ch.isalpha())

        return numero[:4], letras[:3]

    def load_data(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                v.placa,
                v.tipo_vehiculo,
                v.marca,
                v.modelo,
                v.color,
                v.cliente_id,
                c.nombre,
                c.telefono,
                c.documento,
                c.observacion
            FROM vehiculos v
            LEFT JOIN clientes c ON v.cliente_id = c.id
            WHERE v.id = ?
        """, (self.vehicle_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            messagebox.showerror("Error", "No se encontró el vehículo.")
            self.window.destroy()
            return

        numero, letras = self.split_plate(row[0])
        self.entry_placa_numero.insert(0, numero)
        self.entry_placa_letras.insert(0, letras)

        self.vehicle_type_var.set(row[1] if row[1] else "auto")
        self.entry_marca.insert(0, row[2] if row[2] else "")
        self.entry_modelo.insert(0, row[3] if row[3] else "")
        self.entry_color.insert(0, row[4] if row[4] else "")
        self.loaded_customer_id = row[5]

        self.entry_cliente.insert(0, row[6] if row[6] else "")
        self.entry_telefono.insert(0, row[7] if row[7] else "")
        self.entry_documento.insert(0, row[8] if row[8] else "")
        self.text_observacion.insert("1.0", row[9] if row[9] else "")

    def confirm_save(self):
        confirmed = messagebox.askyesno(
            "Confirmar guardado",
            "¿Desea guardar este registro?"
        )
        if not confirmed:
            return

        self.save_data()

    def save_data(self):
        try:
            placa = self.validate_plate()
        except ValueError as e:
            messagebox.showwarning("Dato inválido", str(e))
            return

        tipo_vehiculo = self.vehicle_type_var.get()
        marca = self.entry_marca.get().strip()
        modelo = self.entry_modelo.get().strip()
        color = self.entry_color.get().strip()

        nombre_cliente = self.entry_cliente.get().strip()
        telefono = self.entry_telefono.get().strip()
        documento = self.entry_documento.get().strip()
        observacion = self.text_observacion.get("1.0", "end").strip()

        conn = get_connection()
        cursor = conn.cursor()

        try:
            if self.mode == "create":
                cursor.execute(
                    "SELECT COUNT(*) FROM vehiculos WHERE REPLACE(UPPER(placa), ' ', '') = ?",
                    (placa.replace(" ", "").upper(),)
                )
                if cursor.fetchone()[0] > 0:
                    messagebox.showwarning("Placa existente", "Ya existe un vehículo con esa placa.")
                    return

                cliente_id = self.resolve_customer(cursor, nombre_cliente, telefono, documento, observacion)

                cursor.execute("""
                    INSERT INTO vehiculos (
                        placa, tipo_vehiculo, marca, modelo, color, cliente_id, fecha_creacion
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    placa,
                    tipo_vehiculo,
                    marca if marca else None,
                    modelo if modelo else None,
                    color if color else None,
                    cliente_id,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

                vehicle_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO bitacora (
                        usuario_id, accion, tabla_afectada, registro_id, descripcion, fecha_evento
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.current_user["id"],
                    "CREAR_VEHICULO_CLIENTE",
                    "vehiculos",
                    vehicle_id,
                    f"Se creó el vehículo '{placa}'",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

            else:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM vehiculos
                    WHERE REPLACE(UPPER(placa), ' ', '') = ?
                    AND id != ?
                """, (placa.replace(" ", "").upper(), self.vehicle_id))
                if cursor.fetchone()[0] > 0:
                    messagebox.showwarning("Placa existente", "Ya existe un vehículo con esa placa.")
                    return

                cliente_id = self.resolve_customer(
                    cursor,
                    nombre_cliente,
                    telefono,
                    documento,
                    observacion,
                    existing_customer_id=self.loaded_customer_id
                )

                cursor.execute("""
                    UPDATE vehiculos
                    SET placa = ?, tipo_vehiculo = ?, marca = ?, modelo = ?, color = ?, cliente_id = ?
                    WHERE id = ?
                """, (
                    placa,
                    tipo_vehiculo,
                    marca if marca else None,
                    modelo if modelo else None,
                    color if color else None,
                    cliente_id,
                    self.vehicle_id
                ))

                cursor.execute("""
                    INSERT INTO bitacora (
                        usuario_id, accion, tabla_afectada, registro_id, descripcion, fecha_evento
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.current_user["id"],
                    "EDITAR_VEHICULO_CLIENTE",
                    "vehiculos",
                    self.vehicle_id,
                    f"Se editó el vehículo '{placa}'",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

            conn.commit()
            messagebox.showinfo("Guardado", "Registro guardado correctamente.")
            self.view.load_records()
            self.window.destroy()

        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"No se pudo guardar el registro.\n{str(e)}")

        finally:
            conn.close()

    def resolve_customer(self, cursor, nombre, telefono, documento, observacion, existing_customer_id=None):
        has_customer_data = any([nombre, telefono, documento, observacion])

        if not has_customer_data:
            return None

        if existing_customer_id:
            cursor.execute("""
                UPDATE clientes
                SET nombre = ?, telefono = ?, documento = ?, observacion = ?
                WHERE id = ?
            """, (
                nombre if nombre else None,
                telefono if telefono else None,
                documento if documento else None,
                observacion if observacion else None,
                existing_customer_id
            ))
            return existing_customer_id

        cursor.execute("""
            INSERT INTO clientes (nombre, telefono, documento, observacion, fecha_creacion)
            VALUES (?, ?, ?, ?, ?)
        """, (
            nombre if nombre else None,
            telefono if telefono else None,
            documento if documento else None,
            observacion if observacion else None,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        return cursor.lastrowid

    def run(self):
        pass