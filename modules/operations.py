import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import math

from database.db import get_connection


class OperationsView:
    def __init__(self, parent, user_data):
        self.parent = parent
        self.user_data = user_data

        self.search_plate_entry = None
        self.search_code_entry = None
        self.tree = None

    def build(self):
        self.build_header()
        self.build_table()
        self.load_operations()

    def build_header(self):
        header_frame = tk.Frame(self.parent, bg="white")
        header_frame.pack(fill="x", padx=15, pady=15)

        tk.Label(
            header_frame,
            text="Buscar placa:",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#111827"
        ).grid(row=0, column=0, padx=(0, 8), pady=5, sticky="w")

        self.search_plate_entry = tk.Entry(header_frame, font=("Arial", 11), width=20)
        self.search_plate_entry.grid(row=0, column=1, padx=(0, 12), pady=5)
        self.search_plate_entry.bind("<KeyRelease>", lambda event: self.load_operations())

        tk.Label(
            header_frame,
            text="Código retiro:",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#111827"
        ).grid(row=0, column=2, padx=(0, 8), pady=5, sticky="w")

        self.search_code_entry = tk.Entry(header_frame, font=("Arial", 11), width=14)
        self.search_code_entry.grid(row=0, column=3, padx=(0, 12), pady=5)
        self.search_code_entry.bind("<KeyRelease>", lambda event: self.load_operations())

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
            command=self.load_operations
        ).grid(row=0, column=4, padx=(0, 10), pady=5)

        tk.Button(
            header_frame,
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
            command=self.open_new_operation_window
        ).grid(row=0, column=5, padx=(10, 0), pady=5)

    def build_table(self):
        table_frame = tk.Frame(self.parent, bg="white")
        table_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        columns = ("id", "codigo_retiro", "placa", "tipo", "ingreso", "servicios", "estado", "acciones")

        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18)
        self.tree.pack(fill="both", expand=True, side="left")

        self.tree.heading("id", text="ID")
        self.tree.heading("codigo_retiro", text="Código retiro")
        self.tree.heading("placa", text="Placa")
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("ingreso", text="Ingreso")
        self.tree.heading("servicios", text="Servicios")
        self.tree.heading("estado", text="Estado")
        self.tree.heading("acciones", text="Acciones")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("codigo_retiro", width=110, anchor="center")
        self.tree.column("placa", width=110, anchor="center")
        self.tree.column("tipo", width=90, anchor="center")
        self.tree.column("ingreso", width=150, anchor="center")
        self.tree.column("servicios", width=280, anchor="w")
        self.tree.column("estado", width=90, anchor="center")
        self.tree.column("acciones", width=110, anchor="center")

        scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar_y.pack(side="right", fill="y")

        scrollbar_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        scrollbar_x.pack(side="bottom", fill="x")

        self.tree.configure(
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )

        self.tree.bind("<Double-1>", self.on_double_click)

    def load_operations(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        placa_filter = self.search_plate_entry.get().strip().upper() if self.search_plate_entry else ""
        codigo_filter = self.search_code_entry.get().strip() if self.search_code_entry else ""

        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT 
                o.id,
                o.codigo_retiro,
                v.placa,
                v.tipo_vehiculo,
                o.fecha_ingreso,
                o.estado
            FROM operaciones o
            INNER JOIN vehiculos v ON o.vehiculo_id = v.id
            WHERE o.estado = 'activo'
        """
        params = []

        if placa_filter:
            query += " AND REPLACE(UPPER(v.placa), ' ', '') LIKE ?"
            params.append(f"%{placa_filter.replace(' ', '')}%")

        if codigo_filter:
            query += " AND o.codigo_retiro LIKE ?"
            params.append(f"%{codigo_filter}%")

        query += " ORDER BY o.fecha_ingreso DESC"

        cursor.execute(query, params)
        operations = cursor.fetchall()

        for operation in operations:
            operation_id = operation[0]
            codigo_retiro = operation[1]
            placa = operation[2]
            tipo_vehiculo = operation[3]
            fecha_ingreso = operation[4]
            estado = operation[5]

            servicios = self.get_operation_services(operation_id, cursor)

            self.tree.insert(
                "",
                "end",
                values=(
                    operation_id,
                    codigo_retiro,
                    placa,
                    tipo_vehiculo,
                    fecha_ingreso,
                    servicios,
                    estado,
                    "Doble clic"
                )
            )

        conn.close()

    def get_operation_services(self, operation_id, cursor):
        cursor.execute("""
            SELECT s.nombre
            FROM operacion_servicios os
            INNER JOIN servicios s ON os.servicio_id = s.id
            WHERE os.operacion_id = ? AND os.estado != 'cancelado'
            ORDER BY s.nombre ASC
        """, (operation_id,))
        rows = cursor.fetchall()

        service_names = [row[0] for row in rows]

        if not service_names:
            return "Parqueo"

        return "Parqueo, " + ", ".join(service_names)

    def on_double_click(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        item = self.tree.item(selected[0])
        values = item["values"]

        if not values:
            return

        operation_id = values[0]
        codigo_retiro = values[1]

        action_window = tk.Toplevel(self.parent)
        action_window.title("Acciones")
        action_window.geometry("340x280")
        action_window.resizable(False, False)
        action_window.configure(bg="white")
        action_window.grab_set()

        tk.Label(
            action_window,
            text=f"Operación #{operation_id}",
            font=("Arial", 14, "bold"),
            bg="white",
            fg="#111827"
        ).pack(pady=(20, 8))

        tk.Label(
            action_window,
            text=f"Código de retiro: {codigo_retiro}",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#2563eb"
        ).pack(pady=(0, 16))

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
            command=lambda: self.edit_operation(operation_id, action_window)
        ).pack(pady=6)

        tk.Button(
            action_window,
            text="Cobrar",
            font=("Arial", 11, "bold"),
            width=18,
            bg="#16a34a",
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            command=lambda: self.open_charge_window(operation_id, action_window)
        ).pack(pady=6)

        tk.Button(
            action_window,
            text="Cancelar operación",
            font=("Arial", 11, "bold"),
            width=18,
            bg="#dc2626",
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            command=lambda: self.cancel_operation(operation_id, action_window)
        ).pack(pady=6)

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
        ).pack(pady=6)

    def open_new_operation_window(self):
        OperationFormWindow(self, self.user_data, mode="create").run()

    def edit_operation(self, operation_id, action_window=None):
        if action_window:
            action_window.destroy()
        OperationFormWindow(self, self.user_data, mode="edit", operation_id=operation_id).run()

    def cancel_operation(self, operation_id, action_window=None):
        if action_window:
            action_window.destroy()
        CancelOperationWindow(self, self.user_data, operation_id).run()

    def open_charge_window(self, operation_id, action_window=None):
        if action_window:
            action_window.destroy()
        ChargeOperationWindow(self, self.user_data, operation_id).run()


class OperationFormWindow:
    def __init__(self, operations_view, user_data, mode="create", operation_id=None):
        self.operations_view = operations_view
        self.user_data = user_data
        self.mode = mode
        self.operation_id = operation_id

        self.window = tk.Toplevel()
        self.window.title("Nueva operación" if mode == "create" else "Editar operación")
        self.window.geometry("560x700")
        self.window.minsize(520, 620)
        self.window.resizable(True, True)
        self.window.configure(bg="white")
        self.window.grab_set()

        self.entry_placa_numero = None
        self.entry_placa_letras = None
        self.entry_cliente = None
        self.text_observaciones = None
        self.vehicle_type_var = tk.StringVar(value="auto")
        self.service_vars = {}
        self.services_data = []
        self.loaded_vehicle_id = None
        self.loaded_customer_id = None

        self.build_ui()

        if self.mode == "edit" and self.operation_id:
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

        title = "Nueva operación" if self.mode == "create" else "Editar operación"

        tk.Label(
            form,
            text=title,
            font=("Arial", 16, "bold"),
            bg="white",
            fg="#111827"
        ).pack(pady=(10, 10))

        now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        tk.Label(
            form,
            text=f"Hora actual: {now_str}",
            font=("Arial", 10),
            bg="white",
            fg="#374151"
        ).pack(pady=(0, 15))

        content = tk.Frame(form, bg="white")
        content.pack(fill="both", expand=True, padx=20)

        tk.Label(content, text="Placa *", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))

        plate_frame = tk.Frame(content, bg="white")
        plate_frame.pack(fill="x", pady=(0, 6))

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
            text="Formato referencial: 1023 ABC",
            font=("Arial", 9),
            bg="white",
            fg="#6b7280"
        ).pack(anchor="w", pady=(0, 12))

        tk.Label(content, text="Cliente (referencia opcional)", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.entry_cliente = tk.Entry(content, font=("Arial", 11))
        self.entry_cliente.pack(fill="x", pady=(0, 12))

        tk.Label(content, text="Tipo de vehículo *", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        vehicle_frame = tk.Frame(content, bg="white")
        vehicle_frame.pack(fill="x", pady=(0, 14))

        tk.Radiobutton(
            vehicle_frame,
            text="Auto",
            variable=self.vehicle_type_var,
            value="auto",
            bg="white",
            font=("Arial", 11)
        ).pack(side="left", padx=(0, 16))

        tk.Radiobutton(
            vehicle_frame,
            text="Moto",
            variable=self.vehicle_type_var,
            value="moto",
            bg="white",
            font=("Arial", 11)
        ).pack(side="left", padx=(0, 16))

        tk.Label(content, text="Servicios extra", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        services_frame = tk.Frame(content, bg="white")
        services_frame.pack(fill="x", pady=(0, 14))

        self.load_active_services()
        if not self.services_data:
            tk.Label(
                services_frame,
                text="No hay servicios activos registrados.",
                font=("Arial", 10),
                bg="white",
                fg="#6b7280"
            ).pack(anchor="w")
        else:
            for service in self.services_data:
                var = tk.BooleanVar(value=False)
                self.service_vars[service["id"]] = var
                tk.Checkbutton(
                    services_frame,
                    text=f"{service['nombre']} (Bs {service['precio']:.2f})",
                    variable=var,
                    bg="white",
                    font=("Arial", 11)
                ).pack(anchor="w", pady=3)

        tk.Label(content, text="Observaciones", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.text_observaciones = tk.Text(content, font=("Arial", 11), height=5)
        self.text_observaciones.pack(fill="x", pady=(0, 16))

        buttons_frame = tk.Frame(form, bg="white")
        buttons_frame.pack(pady=18)

        tk.Button(
            buttons_frame,
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
            command=self.save_operation
        ).grid(row=0, column=0, padx=10)

        tk.Button(
            buttons_frame,
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
            raise ValueError("Debe ingresar la placa completa.")

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

    def load_active_services(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, nombre, precio
            FROM servicios
            WHERE estado = 'activo'
            ORDER BY nombre ASC
        """)
        rows = cursor.fetchall()
        conn.close()

        self.services_data = [
            {"id": row[0], "nombre": row[1], "precio": float(row[2])}
            for row in rows
        ]

    def load_data(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                o.id,
                o.vehiculo_id,
                o.cliente_id,
                o.observaciones,
                v.placa,
                v.tipo_vehiculo,
                c.nombre
            FROM operaciones o
            INNER JOIN vehiculos v ON o.vehiculo_id = v.id
            LEFT JOIN clientes c ON o.cliente_id = c.id
            WHERE o.id = ? AND o.estado = 'activo'
        """, (self.operation_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            messagebox.showerror("Error", "No se encontró la operación activa.")
            self.window.destroy()
            return

        self.loaded_vehicle_id = row[1]
        self.loaded_customer_id = row[2]

        numero, letras = self.split_plate(row[4])
        self.entry_placa_numero.insert(0, numero)
        self.entry_placa_letras.insert(0, letras)
        self.vehicle_type_var.set(row[5] if row[5] else "auto")
        self.entry_cliente.insert(0, row[6] if row[6] else "")
        self.text_observaciones.insert("1.0", row[3] if row[3] else "")

        cursor.execute("""
            SELECT servicio_id
            FROM operacion_servicios
            WHERE operacion_id = ? AND estado != 'cancelado'
        """, (self.operation_id,))
        selected_ids = {r[0] for r in cursor.fetchall()}

        for service_id, var in self.service_vars.items():
            var.set(service_id in selected_ids)

        conn.close()

    def save_operation(self):
        try:
            placa = self.validate_plate()
        except ValueError as e:
            messagebox.showwarning("Dato inválido", str(e))
            return

        cliente_nombre = self.entry_cliente.get().strip()
        tipo_vehiculo = self.vehicle_type_var.get()
        observaciones = self.text_observaciones.get("1.0", "end").strip()

        conn = get_connection()
        cursor = conn.cursor()

        try:
            if self.mode == "create":
                vehiculo_id = self.get_or_create_vehicle(cursor, placa, tipo_vehiculo)
                cliente_id = self.get_or_create_customer_by_name(cursor, cliente_nombre)
                tarifa_id = self.get_active_rate(cursor, tipo_vehiculo)
                codigo_operacion = self.generate_operation_code(cursor)
                codigo_retiro = self.generate_pickup_code(cursor)
                fecha_ingreso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                cursor.execute("""
                    INSERT INTO operaciones (
                        codigo_operacion,
                        vehiculo_id,
                        cliente_id,
                        usuario_ingreso_id,
                        tarifa_id,
                        fecha_ingreso,
                        estado,
                        codigo_retiro,
                        observaciones
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    codigo_operacion,
                    vehiculo_id,
                    cliente_id,
                    self.user_data["id"],
                    tarifa_id,
                    fecha_ingreso,
                    "activo",
                    codigo_retiro,
                    observaciones if observaciones else None
                ))

                operacion_id = cursor.lastrowid
                self.replace_services(cursor, operacion_id)

                cursor.execute("""
                    INSERT INTO bitacora (
                        usuario_id, accion, tabla_afectada, registro_id, descripcion, fecha_evento
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.user_data["id"],
                    "CREAR_OPERACION",
                    "operaciones",
                    operacion_id,
                    f"Se creó la operación {operacion_id} para placa {placa} con código de retiro {codigo_retiro}",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

                conn.commit()

                messagebox.showinfo(
                    "Operación registrada",
                    f"Operación creada correctamente.\n\nCódigo de retiro: {codigo_retiro}"
                )

            else:
                cliente_id = self.get_or_create_customer_by_name(
                    cursor,
                    cliente_nombre,
                    existing_customer_id=self.loaded_customer_id
                )

                tarifa_id = self.get_active_rate(cursor, tipo_vehiculo)

                cursor.execute("""
                    UPDATE vehiculos
                    SET placa = ?, tipo_vehiculo = ?
                    WHERE id = ?
                """, (placa, tipo_vehiculo, self.loaded_vehicle_id))

                cursor.execute("""
                    UPDATE operaciones
                    SET cliente_id = ?, tarifa_id = ?, observaciones = ?
                    WHERE id = ?
                """, (
                    cliente_id,
                    tarifa_id,
                    observaciones if observaciones else None,
                    self.operation_id
                ))

                self.replace_services(cursor, self.operation_id)

                cursor.execute("""
                    INSERT INTO bitacora (
                        usuario_id, accion, tabla_afectada, registro_id, descripcion, fecha_evento
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.user_data["id"],
                    "EDITAR_OPERACION",
                    "operaciones",
                    self.operation_id,
                    f"Se editó la operación {self.operation_id} para placa {placa}",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

                conn.commit()
                messagebox.showinfo("Guardado", "Operación actualizada correctamente.")

            self.operations_view.load_operations()
            self.window.destroy()

        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"No se pudo guardar la operación.\n{str(e)}")

        finally:
            conn.close()

    def get_or_create_vehicle(self, cursor, placa, tipo_vehiculo):
        cursor.execute("SELECT id FROM vehiculos WHERE REPLACE(UPPER(placa), ' ', '') = ?", (placa.replace(" ", "").upper(),))
        row = cursor.fetchone()

        if row:
            cursor.execute("""
                UPDATE vehiculos
                SET tipo_vehiculo = ?, placa = ?
                WHERE id = ?
            """, (tipo_vehiculo, placa, row[0]))
            return row[0]

        fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO vehiculos (placa, tipo_vehiculo, fecha_creacion)
            VALUES (?, ?, ?)
        """, (placa, tipo_vehiculo, fecha_creacion))
        return cursor.lastrowid

    def get_or_create_customer_by_name(self, cursor, nombre, existing_customer_id=None):
        if not nombre:
            return None

        if existing_customer_id:
            cursor.execute("""
                UPDATE clientes
                SET nombre = ?
                WHERE id = ?
            """, (nombre, existing_customer_id))
            return existing_customer_id

        cursor.execute("""
            INSERT INTO clientes (nombre, fecha_creacion)
            VALUES (?, ?)
        """, (nombre, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        return cursor.lastrowid

    def get_active_rate(self, cursor, tipo_vehiculo):
        cursor.execute("""
            SELECT id
            FROM tarifas
            WHERE estado = 'activa' AND tipo_vehiculo = ? AND tipo_cobro = 'hora'
            ORDER BY id ASC
            LIMIT 1
        """, (tipo_vehiculo,))
        row = cursor.fetchone()

        if not row:
            raise Exception(f"No existe una tarifa activa para {tipo_vehiculo} por hora.")

        return row[0]

    def replace_services(self, cursor, operacion_id):
        cursor.execute("DELETE FROM operacion_servicios WHERE operacion_id = ?", (operacion_id,))

        selected_service_ids = [
            service_id for service_id, var in self.service_vars.items() if var.get()
        ]

        for service_id in selected_service_ids:
            cursor.execute("""
                SELECT precio
                FROM servicios
                WHERE id = ? AND estado = 'activo'
            """, (service_id,))
            row = cursor.fetchone()

            if not row:
                continue

            precio = float(row[0])

            cursor.execute("""
                INSERT INTO operacion_servicios (
                    operacion_id,
                    servicio_id,
                    cantidad,
                    precio_unitario,
                    subtotal,
                    estado
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                operacion_id,
                service_id,
                1,
                precio,
                precio,
                "pendiente"
            ))

    def generate_operation_code(self, cursor):
        while True:
            code = "OP-" + datetime.now().strftime("%Y%m%d%H%M%S")
            cursor.execute("SELECT 1 FROM operaciones WHERE codigo_operacion = ?", (code,))
            if not cursor.fetchone():
                return code

    def generate_pickup_code(self, cursor):
        while True:
            code = datetime.now().strftime("%H%M%S")
            cursor.execute("SELECT 1 FROM operaciones WHERE codigo_retiro = ? AND estado = 'activo'", (code,))
            if not cursor.fetchone():
                return code

    def run(self):
        pass


class CancelOperationWindow:
    def __init__(self, operations_view, user_data, operation_id):
        self.operations_view = operations_view
        self.user_data = user_data
        self.operation_id = operation_id

        self.window = tk.Toplevel()
        self.window.title("Cancelar operación")
        self.window.geometry("420x290")
        self.window.resizable(False, False)
        self.window.configure(bg="white")
        self.window.grab_set()

        self.text_reason = None

        self.build_ui()

    def build_ui(self):
        tk.Label(
            self.window,
            text="Cancelar operación",
            font=("Arial", 16, "bold"),
            bg="white",
            fg="#111827"
        ).pack(pady=(20, 12))

        tk.Label(
            self.window,
            text="Motivo de cancelación *",
            font=("Arial", 11, "bold"),
            bg="white"
        ).pack(anchor="w", padx=30)

        self.text_reason = tk.Text(self.window, font=("Arial", 11), height=6)
        self.text_reason.pack(fill="x", padx=30, pady=(8, 16))

        buttons = tk.Frame(self.window, bg="white")
        buttons.pack(pady=10)

        tk.Button(
            buttons,
            text="Confirmar cancelación",
            font=("Arial", 11, "bold"),
            bg="#dc2626",
            fg="white",
            bd=0,
            relief="flat",
            padx=16,
            pady=8,
            cursor="hand2",
            command=self.confirm_cancel
        ).grid(row=0, column=0, padx=8)

        tk.Button(
            buttons,
            text="Cerrar",
            font=("Arial", 11, "bold"),
            bg="#6b7280",
            fg="white",
            bd=0,
            relief="flat",
            padx=16,
            pady=8,
            cursor="hand2",
            command=self.window.destroy
        ).grid(row=0, column=1, padx=8)

    def confirm_cancel(self):
        reason = self.text_reason.get("1.0", "end").strip()

        if not reason:
            messagebox.showwarning("Dato requerido", "Debe ingresar el motivo de cancelación.")
            return

        conn = get_connection()
        cursor = conn.cursor()

        try:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
                UPDATE operaciones
                SET
                    estado = 'cancelado',
                    motivo_cancelacion = ?,
                    fecha_salida = ?
                WHERE id = ? AND estado = 'activo'
            """, (reason, now_str, self.operation_id))

            cursor.execute("""
                INSERT INTO bitacora (
                    usuario_id, accion, tabla_afectada, registro_id, descripcion, fecha_evento
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                self.user_data["id"],
                "CANCELAR_OPERACION",
                "operaciones",
                self.operation_id,
                f"Se canceló la operación {self.operation_id}. Motivo: {reason}",
                now_str
            ))

            conn.commit()
            messagebox.showinfo("Operación cancelada", "La operación fue cancelada correctamente.")
            self.window.destroy()
            self.operations_view.load_operations()

        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"No se pudo cancelar la operación.\n{str(e)}")

        finally:
            conn.close()

    def run(self):
        pass


class ChargeOperationWindow:
    def __init__(self, operations_view, user_data, operation_id):
        self.operations_view = operations_view
        self.user_data = user_data
        self.operation_id = operation_id

        self.window = tk.Toplevel()
        self.window.title("Cobrar operación")
        self.window.geometry("520x560")
        self.window.minsize(520, 560)
        self.window.resizable(False, False)
        self.window.configure(bg="white")
        self.window.grab_set()

        self.operation_data = None
        self.calculation = None
        self.method_var = tk.StringVar(value="efectivo")

        self.load_operation_data()
        self.build_ui()

    def load_operation_data(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                o.id,
                o.codigo_retiro,
                v.placa,
                o.fecha_ingreso,
                o.tarifa_id,
                t.monto,
                t.fraccion_minima,
                t.tolerancia_min
            FROM operaciones o
            INNER JOIN vehiculos v ON o.vehiculo_id = v.id
            INNER JOIN tarifas t ON o.tarifa_id = t.id
            WHERE o.id = ? AND o.estado = 'activo'
        """, (self.operation_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            raise Exception("La operación no existe o ya no está activa.")

        self.operation_data = {
            "id": row[0],
            "codigo_retiro": row[1],
            "placa": row[2],
            "fecha_ingreso": row[3],
            "tarifa_id": row[4],
            "monto_tarifa": float(row[5]),
            "fraccion_minima": int(row[6]),
            "tolerancia_min": int(row[7])
        }

        cursor.execute("""
            SELECT COALESCE(SUM(subtotal), 0)
            FROM operacion_servicios
            WHERE operacion_id = ? AND estado != 'cancelado'
        """, (self.operation_id,))
        monto_servicios = float(cursor.fetchone()[0] or 0)

        conn.close()

        fecha_ingreso_dt = datetime.strptime(self.operation_data["fecha_ingreso"], "%Y-%m-%d %H:%M:%S")
        fecha_salida_dt = datetime.now()
        total_minutes = int((fecha_salida_dt - fecha_ingreso_dt).total_seconds() / 60)

        tolerancia = self.operation_data["tolerancia_min"]
        fraccion = self.operation_data["fraccion_minima"]
        monto_tarifa = self.operation_data["monto_tarifa"]

        if total_minutes <= tolerancia:
            bloques = 1
        else:
            bloques = max(1, math.ceil(total_minutes / fraccion))

        monto_parqueo = bloques * monto_tarifa
        monto_total = monto_parqueo + monto_servicios

        self.calculation = {
            "fecha_salida": fecha_salida_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "minutos_estadia": total_minutes,
            "bloques": bloques,
            "monto_parqueo": round(monto_parqueo, 2),
            "monto_servicios": round(monto_servicios, 2),
            "monto_total": round(monto_total, 2)
        }

    def build_ui(self):
        tk.Label(
            self.window,
            text="Cobro de operación",
            font=("Arial", 16, "bold"),
            bg="white",
            fg="#111827"
        ).pack(pady=(20, 15))

        content_frame = tk.Frame(self.window, bg="white")
        content_frame.pack(fill="both", expand=True, padx=30)

        rows = [
            ("Código retiro:", self.operation_data["codigo_retiro"]),
            ("Placa:", self.operation_data["placa"]),
            ("Ingreso:", self.operation_data["fecha_ingreso"]),
            ("Salida:", self.calculation["fecha_salida"]),
            ("Tiempo:", f"{self.calculation['minutos_estadia']} min"),
            ("Monto parqueo:", f"Bs {self.calculation['monto_parqueo']:.2f}"),
            ("Monto servicios:", f"Bs {self.calculation['monto_servicios']:.2f}"),
            ("Total:", f"Bs {self.calculation['monto_total']:.2f}")
        ]

        for label_text, value_text in rows:
            row = tk.Frame(content_frame, bg="white")
            row.pack(fill="x", pady=4)

            tk.Label(
                row,
                text=label_text,
                font=("Arial", 11, "bold"),
                bg="white",
                fg="#111827",
                width=16,
                anchor="w"
            ).pack(side="left")

            tk.Label(
                row,
                text=value_text,
                font=("Arial", 11),
                bg="white",
                fg="#374151",
                anchor="w"
            ).pack(side="left")

        method_frame = tk.Frame(content_frame, bg="white")
        method_frame.pack(fill="x", pady=(18, 10))

        tk.Label(
            method_frame,
            text="Método de pago:",
            font=("Arial", 11, "bold"),
            bg="white"
        ).pack(anchor="w", pady=(0, 8))

        methods = [("Efectivo", "efectivo"), ("QR", "qr")]
        for text, value in methods:
            tk.Radiobutton(
                method_frame,
                text=text,
                variable=self.method_var,
                value=value,
                bg="white",
                font=("Arial", 11)
            ).pack(anchor="w", pady=2)

        buttons_frame = tk.Frame(self.window, bg="white")
        buttons_frame.pack(fill="x", pady=(10, 20))

        tk.Button(
            buttons_frame,
            text="Confirmar cobro",
            font=("Arial", 11, "bold"),
            bg="#16a34a",
            fg="white",
            activebackground="#15803d",
            activeforeground="white",
            bd=0,
            relief="flat",
            padx=18,
            pady=8,
            cursor="hand2",
            command=self.confirm_charge
        ).pack(side="left", padx=(90, 10))

        tk.Button(
            buttons_frame,
            text="Cerrar",
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
        ).pack(side="left", padx=10)

    def confirm_charge(self):
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE operaciones
                SET
                    usuario_salida_id = ?,
                    fecha_salida = ?,
                    minutos_estadia = ?,
                    monto_parqueo = ?,
                    monto_servicios = ?,
                    monto_total = ?,
                    estado = 'finalizado'
                WHERE id = ?
            """, (
                self.user_data["id"],
                self.calculation["fecha_salida"],
                self.calculation["minutos_estadia"],
                self.calculation["monto_parqueo"],
                self.calculation["monto_servicios"],
                self.calculation["monto_total"],
                self.operation_id
            ))

            cursor.execute("""
                INSERT INTO pagos (
                    operacion_id,
                    usuario_id,
                    fecha_pago,
                    metodo_pago,
                    monto,
                    observacion
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                self.operation_id,
                self.user_data["id"],
                self.calculation["fecha_salida"],
                self.method_var.get(),
                self.calculation["monto_total"],
                f"Cobro registrado desde módulo Operaciones. Código de retiro: {self.operation_data['codigo_retiro']}"
            ))

            cursor.execute("""
                INSERT INTO bitacora (
                    usuario_id,
                    accion,
                    tabla_afectada,
                    registro_id,
                    descripcion,
                    fecha_evento
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                self.user_data["id"],
                "COBRAR",
                "operaciones",
                self.operation_id,
                f"Se cobró la operación {self.operation_id} con código de retiro {self.operation_data['codigo_retiro']} por Bs {self.calculation['monto_total']:.2f}",
                self.calculation["fecha_salida"]
            ))

            conn.commit()

            messagebox.showinfo(
                "Cobro realizado",
                f"Operación finalizada correctamente.\n"
                f"Código de retiro: {self.operation_data['codigo_retiro']}\n"
                f"Total cobrado: Bs {self.calculation['monto_total']:.2f}"
            )

            self.window.destroy()
            self.operations_view.load_operations()

        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"No se pudo registrar el cobro.\n{str(e)}")

        finally:
            conn.close()

    def run(self):
        pass