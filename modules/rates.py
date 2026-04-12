import tkinter as tk
from tkinter import ttk, messagebox

from database.db import get_connection


# =========================================================
# CATÁLOGOS
# =========================================================
ESTADO_INACTIVO = 0
ESTADO_ACTIVO = 1

TIPO_TARIFA_ESCALONADA = 1
TIPO_TARIFA_NOCTURNA = 2

TIPO_DIA_LUNES_VIERNES = 1
TIPO_DIA_SABADO = 2
TIPO_DIA_NOCTURNA = 3

TIPO_TARIFA_TEXTO = {
    TIPO_TARIFA_ESCALONADA: "Escalonada",
    TIPO_TARIFA_NOCTURNA: "Nocturna",
}
TIPO_TARIFA_INV = {v: k for k, v in TIPO_TARIFA_TEXTO.items()}

TIPO_DIA_TEXTO = {
    TIPO_DIA_LUNES_VIERNES: "Lunes a viernes",
    TIPO_DIA_SABADO: "Sábado",
    TIPO_DIA_NOCTURNA: "Nocturna",
}
TIPO_DIA_INV = {v: k for k, v in TIPO_DIA_TEXTO.items()}

ESTADO_TEXTO = {
    ESTADO_ACTIVO: "Activa",
    ESTADO_INACTIVO: "Inactiva",
}


# =========================================================
# UTILIDADES
# =========================================================
def obtener_usuario_actual_id(user_data):
    if not user_data:
        return 0
    return user_data.get("Usuario") or user_data.get("id") or 0


def ahora_texto():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# =========================================================
# VISTA PRINCIPAL
# =========================================================
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
            "Tarifa",
            "Nombre",
            "TipoVehiculo",
            "TipoTarifa",
            "Descripcion",
            "Estado",
            "Acciones"
        )

        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18)
        self.tree.pack(fill="both", expand=True, side="left")

        self.tree.heading("Tarifa", text="ID")
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("TipoVehiculo", text="Tipo vehículo")
        self.tree.heading("TipoTarifa", text="Tipo tarifa")
        self.tree.heading("Descripcion", text="Descripción")
        self.tree.heading("Estado", text="Estado")
        self.tree.heading("Acciones", text="Acciones")

        self.tree.column("Tarifa", width=55, anchor="center")
        self.tree.column("Nombre", width=180, anchor="w")
        self.tree.column("TipoVehiculo", width=110, anchor="center")
        self.tree.column("TipoTarifa", width=110, anchor="center")
        self.tree.column("Descripcion", width=260, anchor="w")
        self.tree.column("Estado", width=90, anchor="center")
        self.tree.column("Acciones", width=110, anchor="center")

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
            SELECT
                Tarifa,
                Nombre,
                TipoVehiculo,
                TipoTarifa,
                Descripcion,
                Estado
            FROM TARIFA
            WHERE 1 = 1
        """
        params = []

        if search_value:
            like_value = f"%{search_value}%"
            query += """
                AND (
                    UPPER(Nombre) LIKE ?
                    OR UPPER(TipoVehiculo) LIKE ?
                    OR UPPER(IFNULL(Descripcion, '')) LIKE ?
                )
            """
            params.extend([like_value, like_value, like_value])

        query += " ORDER BY Tarifa ASC "

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    row["Tarifa"],
                    row["Nombre"],
                    row["TipoVehiculo"],
                    TIPO_TARIFA_TEXTO.get(row["TipoTarifa"], "N/D"),
                    row["Descripcion"] if row["Descripcion"] else "",
                    ESTADO_TEXTO.get(row["Estado"], "N/D"),
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
        current_status = values[5]

        action_window = tk.Toplevel(self.parent)
        action_window.title("Acciones de tarifa")
        action_window.geometry("340x310")
        action_window.resizable(False, False)
        action_window.configure(bg="white")
        action_window.grab_set()

        tk.Label(
            action_window,
            text=f"Tarifa: {rate_name}",
            font=("Arial", 14, "bold"),
            bg="white",
            fg="#111827",
            wraplength=280
        ).pack(pady=(20, 10))

        tk.Button(
            action_window,
            text="Editar",
            font=("Arial", 11, "bold"),
            width=20,
            bg="#f59e0b",
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            command=lambda: self.edit_rate(rate_id, action_window)
        ).pack(pady=8)

        tk.Button(
            action_window,
            text="Ver / editar detalle",
            font=("Arial", 11, "bold"),
            width=20,
            bg="#2563eb",
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            command=lambda: self.open_detail_window(rate_id, action_window)
        ).pack(pady=8)

        estado_actual = ESTADO_ACTIVO if current_status == "Activa" else ESTADO_INACTIVO
        toggle_text = "Inactivar" if estado_actual == ESTADO_ACTIVO else "Activar"
        toggle_color = "#dc2626" if estado_actual == ESTADO_ACTIVO else "#16a34a"

        tk.Button(
            action_window,
            text=toggle_text,
            font=("Arial", 11, "bold"),
            width=20,
            bg=toggle_color,
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            command=lambda: self.toggle_rate_status(rate_id, estado_actual, action_window)
        ).pack(pady=8)

        tk.Button(
            action_window,
            text="Cerrar",
            font=("Arial", 11, "bold"),
            width=20,
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

    def open_detail_window(self, rate_id, action_window=None):
        if action_window:
            action_window.destroy()
        RateDetailWindow(self, self.user_data, rate_id).run()

    def toggle_rate_status(self, rate_id, current_status, action_window=None):
        if action_window:
            action_window.destroy()

        new_status = ESTADO_INACTIVO if current_status == ESTADO_ACTIVO else ESTADO_ACTIVO
        new_status_text = ESTADO_TEXTO[new_status]

        confirm = messagebox.askyesno(
            "Confirmar cambio",
            f"¿Desea cambiar el estado de la tarifa a '{new_status_text}'?"
        )
        if not confirm:
            return

        conn = get_connection()
        cursor = conn.cursor()

        try:
            usr = obtener_usuario_actual_id(self.user_data)

            cursor.execute("""
                UPDATE TARIFA
                SET
                    Estado = ?,
                    Usr = ?,
                    UsrFecha = date('now','localtime'),
                    UsrHora = time('now','localtime'),
                    FechaModificacion = datetime('now','localtime')
                WHERE Tarifa = ?
            """, (new_status, usr, rate_id))

            cursor.execute("""
                INSERT INTO BITACORA (
                    Usuario,
                    Accion,
                    TablaAfectada,
                    RegistroAfectado,
                    Descripcion,
                    FechaEvento,
                    Estado,
                    Usr,
                    UsrFecha,
                    UsrHora,
                    FechaCreacion,
                    FechaModificacion
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?,
                    date('now','localtime'),
                    time('now','localtime'),
                    datetime('now','localtime'),
                    datetime('now','localtime')
                )
            """, (
                usr,
                "CAMBIAR_ESTADO_TARIFA",
                "TARIFA",
                rate_id,
                f"Se cambió el estado de la tarifa {rate_id} a {new_status_text}",
                ahora_texto(),
                ESTADO_ACTIVO,
                usr
            ))

            conn.commit()
            messagebox.showinfo("Estado actualizado", "El estado de la tarifa fue actualizado.")
            self.load_rates()

        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"No se pudo actualizar el estado.\n{str(e)}")

        finally:
            conn.close()


# =========================================================
# FORMULARIO CABECERA TARIFA
# =========================================================
class RateFormWindow:
    def __init__(self, rates_view, current_user, mode="create", rate_id=None):
        self.rates_view = rates_view
        self.current_user = current_user
        self.mode = mode
        self.rate_id = rate_id

        self.window = tk.Toplevel()
        self.window.title("Nueva tarifa" if mode == "create" else "Editar tarifa")
        self.window.geometry("460x420")
        self.window.resizable(False, False)
        self.window.configure(bg="white")
        self.window.grab_set()

        self.entry_nombre = None
        self.vehicle_var = tk.StringVar(value="auto")
        self.tipo_tarifa_var = tk.StringVar(value="Escalonada")
        self.entry_descripcion = None

        self.build_ui()

        if self.mode == "edit" and self.rate_id:
            self.load_rate_data()

        self.update_name_suggestion()

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

        tk.Label(form, text="Tipo de tarifa *", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        tipo_frame = tk.Frame(form, bg="white")
        tipo_frame.pack(fill="x", pady=(0, 12))

        tk.Radiobutton(
            tipo_frame,
            text="Escalonada",
            variable=self.tipo_tarifa_var,
            value="Escalonada",
            bg="white",
            font=("Arial", 11),
            command=self.update_name_suggestion
        ).pack(side="left", padx=(0, 20))

        tk.Radiobutton(
            tipo_frame,
            text="Nocturna",
            variable=self.tipo_tarifa_var,
            value="Nocturna",
            bg="white",
            font=("Arial", 11),
            command=self.update_name_suggestion
        ).pack(side="left")

        tk.Label(form, text="Nombre *", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.entry_nombre = tk.Entry(form, font=("Arial", 11))
        self.entry_nombre.pack(fill="x", pady=(0, 12))

        tk.Label(form, text="Descripción", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.entry_descripcion = tk.Entry(form, font=("Arial", 11))
        self.entry_descripcion.pack(fill="x", pady=(0, 12))

        tk.Label(
            form,
            text="Luego podrás editar los tramos o detalle de la tarifa.",
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
        tipo_text = self.tipo_tarifa_var.get()
        suggested_name = f"Tarifa {tipo_text} {vehicle_text}"

        current_name = self.entry_nombre.get().strip()
        auto_names = [
            "",
            "Tarifa Escalonada Auto",
            "Tarifa Escalonada Moto",
            "Tarifa Nocturna Auto",
            "Tarifa Nocturna Moto",
        ]

        if current_name in auto_names:
            self.entry_nombre.delete(0, "end")
            self.entry_nombre.insert(0, suggested_name)

    def load_rate_data(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT Nombre, TipoVehiculo, TipoTarifa, Descripcion
            FROM TARIFA
            WHERE Tarifa = ?
        """, (self.rate_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            messagebox.showerror("Error", "No se encontró la tarifa.")
            self.window.destroy()
            return

        self.entry_nombre.delete(0, "end")
        self.entry_nombre.insert(0, row["Nombre"])
        self.vehicle_var.set(row["TipoVehiculo"])
        self.tipo_tarifa_var.set(TIPO_TARIFA_TEXTO.get(row["TipoTarifa"], "Escalonada"))
        self.entry_descripcion.delete(0, "end")
        self.entry_descripcion.insert(0, row["Descripcion"] if row["Descripcion"] else "")

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
        tipo_tarifa = TIPO_TARIFA_INV[self.tipo_tarifa_var.get()]
        descripcion = self.entry_descripcion.get().strip()

        if not nombre:
            messagebox.showwarning("Datos requeridos", "El nombre es obligatorio.")
            return

        conn = get_connection()
        cursor = conn.cursor()

        try:
            usr = obtener_usuario_actual_id(self.current_user)

            if self.mode == "create":
                cursor.execute("""
                    INSERT INTO TARIFA (
                        Nombre,
                        TipoVehiculo,
                        TipoTarifa,
                        Descripcion,
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
                    nombre,
                    tipo_vehiculo,
                    tipo_tarifa,
                    descripcion if descripcion else None,
                    ESTADO_ACTIVO,
                    usr
                ))

                new_rate_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO BITACORA (
                        Usuario,
                        Accion,
                        TablaAfectada,
                        RegistroAfectado,
                        Descripcion,
                        FechaEvento,
                        Estado,
                        Usr,
                        UsrFecha,
                        UsrHora,
                        FechaCreacion,
                        FechaModificacion
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?,
                        date('now','localtime'),
                        time('now','localtime'),
                        datetime('now','localtime'),
                        datetime('now','localtime')
                    )
                """, (
                    usr,
                    "CREAR_TARIFA",
                    "TARIFA",
                    new_rate_id,
                    f"Se creó la tarifa '{nombre}'",
                    ahora_texto(),
                    ESTADO_ACTIVO,
                    usr
                ))

            else:
                cursor.execute("""
                    UPDATE TARIFA
                    SET
                        Nombre = ?,
                        TipoVehiculo = ?,
                        TipoTarifa = ?,
                        Descripcion = ?,
                        Usr = ?,
                        UsrFecha = date('now','localtime'),
                        UsrHora = time('now','localtime'),
                        FechaModificacion = datetime('now','localtime')
                    WHERE Tarifa = ?
                """, (
                    nombre,
                    tipo_vehiculo,
                    tipo_tarifa,
                    descripcion if descripcion else None,
                    usr,
                    self.rate_id
                ))

                cursor.execute("""
                    INSERT INTO BITACORA (
                        Usuario,
                        Accion,
                        TablaAfectada,
                        RegistroAfectado,
                        Descripcion,
                        FechaEvento,
                        Estado,
                        Usr,
                        UsrFecha,
                        UsrHora,
                        FechaCreacion,
                        FechaModificacion
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?,
                        date('now','localtime'),
                        time('now','localtime'),
                        datetime('now','localtime'),
                        datetime('now','localtime')
                    )
                """, (
                    usr,
                    "EDITAR_TARIFA",
                    "TARIFA",
                    self.rate_id,
                    f"Se editó la tarifa '{nombre}'",
                    ahora_texto(),
                    ESTADO_ACTIVO,
                    usr
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


# =========================================================
# DETALLE DE TARIFA
# =========================================================
class RateDetailWindow:
    def __init__(self, rates_view, current_user, rate_id):
        self.rates_view = rates_view
        self.current_user = current_user
        self.rate_id = rate_id

        self.window = tk.Toplevel()
        self.window.title("Detalle de tarifa")
        self.window.geometry("850x520")
        self.window.resizable(True, True)
        self.window.configure(bg="white")
        self.window.grab_set()

        self.tree = None
        self.rate_info = None

        self.load_rate_info()
        self.build_ui()
        self.load_details()

    def load_rate_info(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT Tarifa, Nombre, TipoVehiculo, TipoTarifa, Descripcion
            FROM TARIFA
            WHERE Tarifa = ?
        """, (self.rate_id,))
        self.rate_info = cursor.fetchone()
        conn.close()

        if not self.rate_info:
            raise Exception("No se encontró la tarifa.")

    def build_ui(self):
        header = tk.Frame(self.window, bg="white")
        header.pack(fill="x", padx=15, pady=15)

        tk.Label(
            header,
            text=f"Detalle: {self.rate_info['Nombre']}",
            font=("Arial", 15, "bold"),
            bg="white",
            fg="#111827"
        ).pack(anchor="w")

        tk.Label(
            header,
            text=f"Vehículo: {self.rate_info['TipoVehiculo']} | Tipo: {TIPO_TARIFA_TEXTO.get(self.rate_info['TipoTarifa'], 'N/D')}",
            font=("Arial", 10),
            bg="white",
            fg="#4b5563"
        ).pack(anchor="w", pady=(4, 0))

        actions = tk.Frame(self.window, bg="white")
        actions.pack(fill="x", padx=15, pady=(0, 10))

        tk.Button(
            actions,
            text="Nuevo detalle",
            font=("Arial", 10, "bold"),
            bg="#16a34a",
            fg="white",
            bd=0,
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=self.open_new_detail
        ).pack(side="right")

        table_frame = tk.Frame(self.window, bg="white")
        table_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        columns = (
            "TarifaDetalle",
            "TipoDia",
            "MinutoInicio",
            "MinutoFin",
            "Monto",
            "HoraInicio",
            "HoraFin",
            "Estado",
        )

        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=14)
        self.tree.pack(fill="both", expand=True, side="left")

        self.tree.heading("TarifaDetalle", text="ID")
        self.tree.heading("TipoDia", text="Tipo día")
        self.tree.heading("MinutoInicio", text="Min inicio")
        self.tree.heading("MinutoFin", text="Min fin")
        self.tree.heading("Monto", text="Monto")
        self.tree.heading("HoraInicio", text="Hora inicio")
        self.tree.heading("HoraFin", text="Hora fin")
        self.tree.heading("Estado", text="Estado")

        self.tree.column("TarifaDetalle", width=55, anchor="center")
        self.tree.column("TipoDia", width=130, anchor="center")
        self.tree.column("MinutoInicio", width=90, anchor="center")
        self.tree.column("MinutoFin", width=90, anchor="center")
        self.tree.column("Monto", width=90, anchor="center")
        self.tree.column("HoraInicio", width=90, anchor="center")
        self.tree.column("HoraFin", width=90, anchor="center")
        self.tree.column("Estado", width=90, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind("<Double-1>", self.on_double_click)

    def load_details(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                TarifaDetalle,
                TipoDia,
                MinutoInicio,
                MinutoFin,
                Monto,
                HoraInicio,
                HoraFin,
                Estado
            FROM TARIFADETALLE
            WHERE Tarifa = ?
            ORDER BY TipoDia ASC, MinutoInicio ASC, TarifaDetalle ASC
        """, (self.rate_id,))
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    row["TarifaDetalle"],
                    TIPO_DIA_TEXTO.get(row["TipoDia"], "N/D"),
                    row["MinutoInicio"],
                    row["MinutoFin"],
                    f"Bs {float(row['Monto']):.2f}",
                    row["HoraInicio"] if row["HoraInicio"] else "",
                    row["HoraFin"] if row["HoraFin"] else "",
                    ESTADO_TEXTO.get(row["Estado"], "N/D")
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

        detail_id = values[0]

        action_window = tk.Toplevel(self.window)
        action_window.title("Acciones detalle")
        action_window.geometry("320x230")
        action_window.resizable(False, False)
        action_window.configure(bg="white")
        action_window.grab_set()

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
            command=lambda: self.edit_detail(detail_id, action_window)
        ).pack(pady=(28, 10))

        tk.Button(
            action_window,
            text="Inactivar / Activar",
            font=("Arial", 11, "bold"),
            width=18,
            bg="#2563eb",
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            command=lambda: self.toggle_detail_status(detail_id, action_window)
        ).pack(pady=10)

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
        ).pack(pady=10)

    def open_new_detail(self):
        RateDetailFormWindow(self, self.current_user, self.rate_id, mode="create").run()

    def edit_detail(self, detail_id, action_window=None):
        if action_window:
            action_window.destroy()
        RateDetailFormWindow(self, self.current_user, self.rate_id, mode="edit", detail_id=detail_id).run()

    def toggle_detail_status(self, detail_id, action_window=None):
        if action_window:
            action_window.destroy()

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT Estado
                FROM TARIFADETALLE
                WHERE TarifaDetalle = ?
            """, (detail_id,))
            row = cursor.fetchone()

            if not row:
                messagebox.showerror("Error", "No se encontró el detalle.")
                return

            estado_actual = row["Estado"]
            nuevo_estado = ESTADO_INACTIVO if estado_actual == ESTADO_ACTIVO else ESTADO_ACTIVO
            usr = obtener_usuario_actual_id(self.current_user)

            cursor.execute("""
                UPDATE TARIFADETALLE
                SET
                    Estado = ?,
                    Usr = ?,
                    UsrFecha = date('now','localtime'),
                    UsrHora = time('now','localtime'),
                    FechaModificacion = datetime('now','localtime')
                WHERE TarifaDetalle = ?
            """, (nuevo_estado, usr, detail_id))

            conn.commit()
            self.load_details()
            messagebox.showinfo("Actualizado", "Estado del detalle actualizado.")

        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"No se pudo actualizar el detalle.\n{e}")

        finally:
            conn.close()

    def run(self):
        pass


# =========================================================
# FORMULARIO DETALLE TARIFA
# =========================================================
class RateDetailFormWindow:
    def __init__(self, detail_view, current_user, rate_id, mode="create", detail_id=None):
        self.detail_view = detail_view
        self.current_user = current_user
        self.rate_id = rate_id
        self.mode = mode
        self.detail_id = detail_id

        self.window = tk.Toplevel()
        self.window.title("Nuevo detalle" if mode == "create" else "Editar detalle")
        self.window.geometry("430x520")
        self.window.resizable(False, False)
        self.window.configure(bg="white")
        self.window.grab_set()

        self.tipo_dia_var = tk.StringVar(value="Lunes a viernes")
        self.entry_min_inicio = None
        self.entry_min_fin = None
        self.entry_monto = None
        self.entry_hora_inicio = None
        self.entry_hora_fin = None

        self.build_ui()

        if self.mode == "edit" and self.detail_id:
            self.load_detail_data()

        self.on_tipo_dia_change()

    def build_ui(self):
        title = "Nuevo detalle" if self.mode == "create" else "Editar detalle"

        tk.Label(
            self.window,
            text=title,
            font=("Arial", 16, "bold"),
            bg="white",
            fg="#111827"
        ).pack(pady=(20, 16))

        form = tk.Frame(self.window, bg="white")
        form.pack(padx=30, fill="x")

        tk.Label(form, text="Tipo día *", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        cbo_tipo = ttk.Combobox(
            form,
            textvariable=self.tipo_dia_var,
            values=list(TIPO_DIA_INV.keys()),
            state="readonly"
        )
        cbo_tipo.pack(fill="x", pady=(0, 12))
        cbo_tipo.bind("<<ComboboxSelected>>", lambda e: self.on_tipo_dia_change())

        tk.Label(form, text="Minuto inicio *", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.entry_min_inicio = tk.Entry(form, font=("Arial", 11))
        self.entry_min_inicio.pack(fill="x", pady=(0, 12))

        tk.Label(form, text="Minuto fin *", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.entry_min_fin = tk.Entry(form, font=("Arial", 11))
        self.entry_min_fin.pack(fill="x", pady=(0, 12))

        tk.Label(form, text="Monto (Bs) *", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.entry_monto = tk.Entry(form, font=("Arial", 11))
        self.entry_monto.pack(fill="x", pady=(0, 12))

        tk.Label(form, text="Hora inicio", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.entry_hora_inicio = tk.Entry(form, font=("Arial", 11))
        self.entry_hora_inicio.pack(fill="x", pady=(0, 12))

        tk.Label(form, text="Hora fin", font=("Arial", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 5))
        self.entry_hora_fin = tk.Entry(form, font=("Arial", 11))
        self.entry_hora_fin.pack(fill="x", pady=(0, 12))

        tk.Label(
            form,
            text="Formato hora: HH:MM. Para nocturna puedes usar 18:00 y 20:00.",
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
            bd=0,
            relief="flat",
            padx=18,
            pady=8,
            cursor="hand2",
            command=self.window.destroy
        ).grid(row=0, column=1, padx=10)

    def on_tipo_dia_change(self):
        tipo = self.tipo_dia_var.get()

        if tipo == "Nocturna":
            self.entry_hora_inicio.config(state="normal")
            self.entry_hora_fin.config(state="normal")
        else:
            self.entry_hora_inicio.config(state="normal")
            self.entry_hora_fin.config(state="normal")

    def load_detail_data(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT TipoDia, MinutoInicio, MinutoFin, Monto, HoraInicio, HoraFin
            FROM TARIFADETALLE
            WHERE TarifaDetalle = ?
        """, (self.detail_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            messagebox.showerror("Error", "No se encontró el detalle.")
            self.window.destroy()
            return

        self.tipo_dia_var.set(TIPO_DIA_TEXTO.get(row["TipoDia"], "Lunes a viernes"))
        self.entry_min_inicio.insert(0, str(row["MinutoInicio"]))
        self.entry_min_fin.insert(0, str(row["MinutoFin"]))
        self.entry_monto.insert(0, str(row["Monto"]))
        self.entry_hora_inicio.insert(0, row["HoraInicio"] if row["HoraInicio"] else "")
        self.entry_hora_fin.insert(0, row["HoraFin"] if row["HoraFin"] else "")

    def confirm_save(self):
        confirmed = messagebox.askyesno(
            "Confirmar guardado",
            "¿Desea guardar este detalle?"
        )
        if not confirmed:
            return

        self.save_detail()

    def save_detail(self):
        tipo_dia = TIPO_DIA_INV[self.tipo_dia_var.get()]
        min_inicio_str = self.entry_min_inicio.get().strip()
        min_fin_str = self.entry_min_fin.get().strip()
        monto_str = self.entry_monto.get().strip()
        hora_inicio = self.entry_hora_inicio.get().strip()
        hora_fin = self.entry_hora_fin.get().strip()

        if not min_inicio_str or not min_fin_str or not monto_str:
            messagebox.showwarning("Datos requeridos", "Minuto inicio, minuto fin y monto son obligatorios.")
            return

        try:
            min_inicio = int(min_inicio_str)
            min_fin = int(min_fin_str)
            monto = float(monto_str)
        except ValueError:
            messagebox.showwarning("Datos inválidos", "Minutos deben ser enteros y monto numérico.")
            return

        if min_inicio < 0 or min_fin < min_inicio:
            messagebox.showwarning("Datos inválidos", "Verifica el rango de minutos.")
            return

        if monto < 0:
            messagebox.showwarning("Datos inválidos", "El monto no puede ser negativo.")
            return

        usr = obtener_usuario_actual_id(self.current_user)

        conn = get_connection()
        cursor = conn.cursor()

        try:
            if self.mode == "create":
                cursor.execute("""
                    INSERT INTO TARIFADETALLE (
                        Tarifa,
                        TipoDia,
                        MinutoInicio,
                        MinutoFin,
                        Monto,
                        HoraInicio,
                        HoraFin,
                        Estado,
                        Usr,
                        UsrFecha,
                        UsrHora,
                        FechaCreacion,
                        FechaModificacion
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        date('now','localtime'),
                        time('now','localtime'),
                        datetime('now','localtime'),
                        datetime('now','localtime')
                    )
                """, (
                    self.rate_id,
                    tipo_dia,
                    min_inicio,
                    min_fin,
                    monto,
                    hora_inicio if hora_inicio else None,
                    hora_fin if hora_fin else None,
                    ESTADO_ACTIVO,
                    usr
                ))

            else:
                cursor.execute("""
                    UPDATE TARIFADETALLE
                    SET
                        TipoDia = ?,
                        MinutoInicio = ?,
                        MinutoFin = ?,
                        Monto = ?,
                        HoraInicio = ?,
                        HoraFin = ?,
                        Usr = ?,
                        UsrFecha = date('now','localtime'),
                        UsrHora = time('now','localtime'),
                        FechaModificacion = datetime('now','localtime')
                    WHERE TarifaDetalle = ?
                """, (
                    tipo_dia,
                    min_inicio,
                    min_fin,
                    monto,
                    hora_inicio if hora_inicio else None,
                    hora_fin if hora_fin else None,
                    usr,
                    self.detail_id
                ))

            conn.commit()
            messagebox.showinfo("Guardado", "Detalle guardado correctamente.")
            self.detail_view.load_details()
            self.window.destroy()

        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"No se pudo guardar el detalle.\n{str(e)}")

        finally:
            conn.close()

    def run(self):
        pass