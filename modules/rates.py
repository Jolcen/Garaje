import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from database.db import get_connection


class RatesView:
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
        self.load_rates()

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
            text="Solo el administrador puede gestionar tarifas.",
            font=("Arial", 11),
            bg="white",
            fg="#4b5563"
        ).pack()

    def build_header(self):
        header_frame = tk.Frame(self.parent, bg="white")
        header_frame.pack(fill="x", padx=15, pady=15)

        tk.Label(
            header_frame,
            text="Buscar tarifa:",
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#111827"
        ).pack(side="left", padx=(0, 8))

        self.search_entry = tk.Entry(header_frame, font=("Arial", 11), width=25)
        self.search_entry.pack(side="left", padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda event: self.load_rates())

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
            command=self.load_rates
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            header_frame,
            text="Nueva tarifa",
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
            command=self.open_new_rate_window
        ).pack(side="right")

    def build_table(self):
        table_frame = tk.Frame(self.parent, bg="white")
        table_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        columns = (
            "id",
            "nombre",
            "tipo_vehiculo",
            "tipo_cobro",
            "monto",
            "fraccion_minima",
            "tolerancia_min",
            "estado",
            "acciones"
        )

        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18)
        self.tree.pack(fill="both", expand=True, side="left")

        self.tree.heading("id", text="ID")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("tipo_vehiculo", text="Tipo vehículo")
        self.tree.heading("tipo_cobro", text="Tipo cobro")
        self.tree.heading("monto", text="Monto")
        self.tree.heading("fraccion_minima", text="Fracción (min)")
        self.tree.heading("tolerancia_min", text="Tolerancia")
        self.tree.heading("estado", text="Estado")
        self.tree.heading("acciones", text="Acciones")

        self.tree.column("id", width=55, anchor="center")
        self.tree.column("nombre", width=180, anchor="w")
        self.tree.column("tipo_vehiculo", width=110, anchor="center")
        self.tree.column("tipo_cobro", width=100, anchor="center")
        self.tree.column("monto", width=90, anchor="center")
        self.tree.column("fraccion_minima", width=100, anchor="center")
        self.tree.column("tolerancia_min", width=90, anchor="center")
        self.tree.column("estado", width=90, anchor="center")
        self.tree.column("acciones", width=110, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind("<Double-1>", self.on_double_click)

    def load_rates(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        search_value = self.search_entry.get().strip().upper() if self.search_entry else ""

        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT id, nombre, tipo_vehiculo, tipo_cobro, monto,
                   fraccion_minima, tolerancia_min, estado
            FROM tarifas
            WHERE 1=1
        """
        params = []

        if search_value:
            query += """
                AND (
                    UPPER(nombre) LIKE ?
                    OR UPPER(tipo_vehiculo) LIKE ?
                    OR UPPER(tipo_cobro) LIKE ?
                    OR UPPER(estado) LIKE ?
                )
            """
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
                    f"Bs {float(row[4]):.2f}",
                    row[5],
                    row[6],
                    row[7],
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

        rate_id = values[0]
        rate_name = values[1]
        current_status = values[7]

        action_window = tk.Toplevel(self.parent)
        action_window.title("Acciones de tarifa")
        action_window.geometry("320x260")
        action_window.resizable(False, False)
        action_window.configure(bg="white")
        action_window.grab_set()

        tk.Label(
            action_window,
            text=f"Tarifa: {rate_name}",
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
            command=lambda: self.edit_rate(rate_id, action_window)
        ).pack(pady=8)

        toggle_text = "Inactivar" if current_status == "activa" else "Activar"
        toggle_color = "#dc2626" if current_status == "activa" else "#16a34a"

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
            command=lambda: self.toggle_rate_status(rate_id, current_status, action_window)
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

    def open_new_rate_window(self):
        RateFormWindow(self, self.user_data, mode="create").run()

    def edit_rate(self, rate_id, action_window=None):
        if action_window:
            action_window.destroy()
        RateFormWindow(self, self.user_data, mode="edit", rate_id=rate_id).run()

    def toggle_rate_status(self, rate_id, current_status, action_window=None):
        if action_window:
            action_window.destroy()

        new_status = "inactiva" if current_status == "activa" else "activa"

        confirm = messagebox.askyesno(
            "Confirmar cambio",
            f"¿Desea cambiar el estado de la tarifa a '{new_status}'?"
        )
        if not confirm:
            return

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE tarifas
                SET estado = ?
                WHERE id = ?
            """, (new_status, rate_id))

            cursor.execute("""
                INSERT INTO bitacora (
                    usuario_id, accion, tabla_afectada, registro_id, descripcion, fecha_evento
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                self.user_data["id"],
                "CAMBIAR_ESTADO_TARIFA",
                "tarifas",
                rate_id,
                f"Se cambió el estado de la tarifa {rate_id} a {new_status}",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

            conn.commit()
            messagebox.showinfo("Estado actualizado", "El estado de la tarifa fue actualizado.")
            self.load_rates()

        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"No se pudo actualizar el estado.\n{str(e)}")

        finally:
            conn.close()


class RateFormWindow:
    def __init__(self, rates_view, current_user, mode="create", rate_id=None):
        self.rates_view = rates_view
        self.current_user = current_user
        self.mode = mode
        self.rate_id = rate_id

        self.window = tk.Toplevel()
        self.window.title("Nueva tarifa" if mode == "create" else "Editar tarifa")
        self.window.geometry("430x580")
        self.window.resizable(True, True)
        self.window.configure(bg="white")
        self.window.grab_set()

        self.entry_nombre = None
        self.vehicle_var = tk.StringVar(value="auto")
        self.charge_var = tk.StringVar(value="hora")
        self.entry_monto = None
        self.entry_fraccion = None
        self.entry_tolerancia = None

        self.build_ui()

        if self.mode == "edit" and self.rate_id:
            self.load_rate_data()

        self.update_name_suggestion()
        self.update_fields_by_charge_type()

    def build_ui(self):
        title = "Nueva tarifa" if self.mode == "create" else "Editar tarifa"

        tk.Label(
            self.window,
            text=title,
            font=("Arial", 16, "bold"),
            bg="white",
            fg="#111827"
        ).pack(pady=(20, 16))

        form = tk.Frame(self.window, bg="white")
        form.pack(padx=30, fill="x")

        tk.Label(form, text="Tipo de vehículo *", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        vehicle_frame = tk.Frame(form, bg="white")
        vehicle_frame.pack(fill="x", pady=(0, 12))

        tk.Radiobutton(
            vehicle_frame,
            text="Auto",
            variable=self.vehicle_var,
            value="auto",
            bg="white",
            font=("Arial", 11),
            command=self.update_name_suggestion
        ).pack(side="left", padx=(0, 20))

        tk.Radiobutton(
            vehicle_frame,
            text="Moto",
            variable=self.vehicle_var,
            value="moto",
            bg="white",
            font=("Arial", 11),
            command=self.update_name_suggestion
        ).pack(side="left", padx=(0, 20))

        tk.Label(form, text="Tipo de cobro *", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        charge_frame = tk.Frame(form, bg="white")
        charge_frame.pack(fill="x", pady=(0, 12))

        tk.Radiobutton(
            charge_frame,
            text="Por hora",
            variable=self.charge_var,
            value="hora",
            bg="white",
            font=("Arial", 11),
            command=self.on_charge_type_change
        ).pack(side="left", padx=(0, 20))

        tk.Radiobutton(
            charge_frame,
            text="Por día",
            variable=self.charge_var,
            value="dia",
            bg="white",
            font=("Arial", 11),
            command=self.on_charge_type_change
        ).pack(side="left")

        tk.Label(form, text="Nombre *", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.entry_nombre = tk.Entry(form, font=("Arial", 11))
        self.entry_nombre.pack(fill="x", pady=(0, 12))

        tk.Label(form, text="Monto (Bs) *", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.entry_monto = tk.Entry(form, font=("Arial", 11))
        self.entry_monto.pack(fill="x", pady=(0, 12))

        tk.Label(form, text="Fracción mínima (minutos) *", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.entry_fraccion = tk.Entry(form, font=("Arial", 11))
        self.entry_fraccion.pack(fill="x", pady=(0, 12))

        tk.Label(form, text="Tolerancia (minutos) *", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.entry_tolerancia = tk.Entry(form, font=("Arial", 11))
        self.entry_tolerancia.pack(fill="x", pady=(0, 12))

        tk.Label(
            form,
            text="Sugerencia: para cobro por día se usará 1440 minutos.",
            font=("Arial", 9),
            bg="white",
            fg="#6b7280"
        ).pack(anchor="w", pady=(0, 12))

        buttons = tk.Frame(self.window, bg="white")
        buttons.pack(pady=18)

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

    def update_name_suggestion(self):
        if not self.entry_nombre:
            return

        vehicle_text = "Auto" if self.vehicle_var.get() == "auto" else "Moto"
        charge_text = "por hora" if self.charge_var.get() == "hora" else "por día"
        suggested_name = f"{vehicle_text} {charge_text}"

        current_name = self.entry_nombre.get().strip()
        auto_names = ["Auto por hora", "Auto por día", "Moto por hora", "Moto por día", ""]

        if current_name in auto_names:
            self.entry_nombre.delete(0, "end")
            self.entry_nombre.insert(0, suggested_name)

    def on_charge_type_change(self):
        self.update_name_suggestion()
        self.update_fields_by_charge_type()

    def update_fields_by_charge_type(self):
        if not self.entry_fraccion or not self.entry_tolerancia:
            return

        if self.charge_var.get() == "dia":
            self.entry_fraccion.delete(0, "end")
            self.entry_fraccion.insert(0, "1440")
            self.entry_tolerancia.delete(0, "end")
            self.entry_tolerancia.insert(0, "0")

    def load_rate_data(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT nombre, tipo_vehiculo, tipo_cobro, monto, fraccion_minima, tolerancia_min
            FROM tarifas
            WHERE id = ?
        """, (self.rate_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            messagebox.showerror("Error", "No se encontró la tarifa.")
            self.window.destroy()
            return

        self.entry_nombre.delete(0, "end")
        self.entry_nombre.insert(0, row[0])
        self.vehicle_var.set(row[1])
        self.charge_var.set(row[2])
        self.entry_monto.insert(0, str(row[3]))
        self.entry_fraccion.insert(0, str(row[4]))
        self.entry_tolerancia.insert(0, str(row[5]))

    def confirm_save(self):
        confirmed = messagebox.askyesno(
            "Confirmar guardado",
            "¿Desea guardar esta tarifa?"
        )
        if not confirmed:
            return

        self.save_rate()

    def save_rate(self):
        nombre = self.entry_nombre.get().strip()
        tipo_vehiculo = self.vehicle_var.get()
        tipo_cobro = self.charge_var.get()
        monto_str = self.entry_monto.get().strip()
        fraccion_str = self.entry_fraccion.get().strip()
        tolerancia_str = self.entry_tolerancia.get().strip()

        if tipo_cobro == "dia" and not fraccion_str:
            fraccion_str = "1440"
        if tipo_cobro == "dia" and not tolerancia_str:
            tolerancia_str = "0"

        if not nombre or not monto_str or not fraccion_str or not tolerancia_str:
            messagebox.showwarning("Datos requeridos", "Todos los campos son obligatorios.")
            return

        try:
            monto = float(monto_str)
            fraccion_minima = int(fraccion_str)
            tolerancia_min = int(tolerancia_str)
        except ValueError:
            messagebox.showwarning("Datos inválidos", "Monto debe ser numérico y fracción/tolerancia deben ser enteros.")
            return

        if monto <= 0:
            messagebox.showwarning("Datos inválidos", "El monto debe ser mayor a 0.")
            return

        if fraccion_minima <= 0:
            messagebox.showwarning("Datos inválidos", "La fracción mínima debe ser mayor a 0.")
            return

        if tolerancia_min < 0:
            messagebox.showwarning("Datos inválidos", "La tolerancia no puede ser negativa.")
            return

        conn = get_connection()
        cursor = conn.cursor()

        try:
            if self.mode == "create":
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM tarifas
                    WHERE tipo_vehiculo = ? AND tipo_cobro = ? AND estado = 'activa'
                """, (tipo_vehiculo, tipo_cobro))
                if cursor.fetchone()[0] > 0:
                    messagebox.showwarning(
                        "Tarifa duplicada",
                        "Ya existe una tarifa activa para ese tipo de vehículo y tipo de cobro."
                    )
                    return

                cursor.execute("""
                    INSERT INTO tarifas (
                        nombre, tipo_vehiculo, tipo_cobro, monto,
                        fraccion_minima, tolerancia_min, estado, fecha_creacion
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 'activa', ?)
                """, (
                    nombre,
                    tipo_vehiculo,
                    tipo_cobro,
                    monto,
                    fraccion_minima,
                    tolerancia_min,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

                new_rate_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO bitacora (
                        usuario_id, accion, tabla_afectada, registro_id, descripcion, fecha_evento
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.current_user["id"],
                    "CREAR_TARIFA",
                    "tarifas",
                    new_rate_id,
                    f"Se creó la tarifa '{nombre}'",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

            else:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM tarifas
                    WHERE tipo_vehiculo = ? AND tipo_cobro = ? AND estado = 'activa' AND id != ?
                """, (tipo_vehiculo, tipo_cobro, self.rate_id))
                if cursor.fetchone()[0] > 0:
                    messagebox.showwarning(
                        "Tarifa duplicada",
                        "Ya existe otra tarifa activa para ese tipo de vehículo y tipo de cobro."
                    )
                    return

                cursor.execute("""
                    UPDATE tarifas
                    SET nombre = ?, tipo_vehiculo = ?, tipo_cobro = ?, monto = ?,
                        fraccion_minima = ?, tolerancia_min = ?
                    WHERE id = ?
                """, (
                    nombre,
                    tipo_vehiculo,
                    tipo_cobro,
                    monto,
                    fraccion_minima,
                    tolerancia_min,
                    self.rate_id
                ))

                cursor.execute("""
                    INSERT INTO bitacora (
                        usuario_id, accion, tabla_afectada, registro_id, descripcion, fecha_evento
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.current_user["id"],
                    "EDITAR_TARIFA",
                    "tarifas",
                    self.rate_id,
                    f"Se editó la tarifa '{nombre}'",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

            conn.commit()
            messagebox.showinfo("Guardado", "Tarifa guardada correctamente.")
            self.rates_view.load_rates()
            self.window.destroy()

        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"No se pudo guardar la tarifa.\n{str(e)}")

        finally:
            conn.close()

    def run(self):
        pass