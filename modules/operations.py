import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, time

from database.db import get_connection
from utils.printer import imprimir_ticket


# =========================================================
# CATÁLOGOS
# =========================================================
ESTADO_GENERAL_ACTIVO = 1
ESTADO_GENERAL_INACTIVO = 0

ROL_ADMIN = 1
ROL_EMPLEADO = 2

TIPO_TARIFA_ESCALONADA = 1
TIPO_TARIFA_NOCTURNA = 2

TIPO_DIA_LUNES_VIERNES = 1
TIPO_DIA_SABADO = 2
TIPO_DIA_NOCTURNA = 3

METODO_PAGO_EFECTIVO = 1
METODO_PAGO_QR = 2

ESTADO_CONTRATO_ACTIVO = 1

ESTADO_OPERACION_ACTIVO = 1
ESTADO_OPERACION_FINALIZADO = 2
ESTADO_OPERACION_CANCELADO = 3

TIPO_OPERACION_NORMAL = 1
TIPO_OPERACION_CONTRATO = 2

ESTADO_OPERACION_SERVICIO_PENDIENTE = 1
ESTADO_OPERACION_SERVICIO_EN_PROCESO = 2
ESTADO_OPERACION_SERVICIO_REALIZADO = 3
ESTADO_OPERACION_SERVICIO_CANCELADO = 4


# =========================================================
# UTILIDADES
# =========================================================
def ahora_texto():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def obtener_usuario_actual_id(user_data):
    if not user_data:
        return 0
    return user_data.get("Usuario") or user_data.get("id") or 0


def limpiar_placa_para_busqueda(placa):
    return placa.replace(" ", "").replace("-", "").upper().strip()


def es_sabado(fecha_dt):
    return fecha_dt.weekday() == 5


def franja_nocturna_aplica(fecha_ingreso_dt, fecha_salida_dt):
    """
    Aplica nocturna si la hora de salida cae entre 18:00 y 20:00.
    """
    hora_salida = fecha_salida_dt.time()
    return time(18, 0, 0) <= hora_salida <= time(20, 0, 0)


def nombre_tipo_operacion(tipo_operacion):
    if tipo_operacion == TIPO_OPERACION_CONTRATO:
        return "Contrato"
    return "Normal"


def nombre_estado_operacion(estado):
    if estado == ESTADO_OPERACION_ACTIVO:
        return "Activo"
    if estado == ESTADO_OPERACION_FINALIZADO:
        return "Finalizado"
    if estado == ESTADO_OPERACION_CANCELADO:
        return "Cancelado"
    return "N/D"


def nombre_metodo_pago(metodo):
    if metodo == METODO_PAGO_EFECTIVO:
        return "Efectivo"
    if metodo == METODO_PAGO_QR:
        return "QR"
    return "N/D"


# =========================================================
# VISTA PRINCIPAL
# =========================================================
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

        columns = (
            "Operacion",
            "CodigoRetiro",
            "Placa",
            "TipoVehiculo",
            "FechaIngreso",
            "TipoOperacion",
            "Servicios",
            "Estado",
            "Acciones",
        )

        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18)
        self.tree.pack(fill="both", expand=True, side="left")

        self.tree.heading("Operacion", text="ID")
        self.tree.heading("CodigoRetiro", text="Código retiro")
        self.tree.heading("Placa", text="Placa")
        self.tree.heading("TipoVehiculo", text="Tipo")
        self.tree.heading("FechaIngreso", text="Ingreso")
        self.tree.heading("TipoOperacion", text="Modalidad")
        self.tree.heading("Servicios", text="Servicios")
        self.tree.heading("Estado", text="Estado")
        self.tree.heading("Acciones", text="Acciones")

        self.tree.column("Operacion", width=60, anchor="center")
        self.tree.column("CodigoRetiro", width=110, anchor="center")
        self.tree.column("Placa", width=110, anchor="center")
        self.tree.column("TipoVehiculo", width=90, anchor="center")
        self.tree.column("FechaIngreso", width=150, anchor="center")
        self.tree.column("TipoOperacion", width=100, anchor="center")
        self.tree.column("Servicios", width=250, anchor="w")
        self.tree.column("Estado", width=90, anchor="center")
        self.tree.column("Acciones", width=110, anchor="center")

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
                O.Operacion,
                O.CodigoRetiro,
                V.Placa,
                V.TipoVehiculo,
                O.FechaIngreso,
                O.TipoOperacion,
                O.Estado
            FROM OPERACION O
            INNER JOIN VEHICULO V ON O.Vehiculo = V.Vehiculo
            WHERE O.Estado = ?
        """
        params = [ESTADO_OPERACION_ACTIVO]

        if placa_filter:
            query += " AND REPLACE(REPLACE(UPPER(V.Placa), ' ', ''), '-', '') LIKE ? "
            params.append(f"%{limpiar_placa_para_busqueda(placa_filter)}%")

        if codigo_filter:
            query += " AND O.CodigoRetiro LIKE ? "
            params.append(f"%{codigo_filter}%")

        query += " ORDER BY O.FechaIngreso DESC "

        cursor.execute(query, params)
        operations = cursor.fetchall()

        for operation in operations:
            operacion_id = operation["Operacion"]
            codigo_retiro = operation["CodigoRetiro"]
            placa = operation["Placa"]
            tipo_vehiculo = operation["TipoVehiculo"]
            fecha_ingreso = operation["FechaIngreso"]
            tipo_operacion = operation["TipoOperacion"]
            estado = operation["Estado"]

            servicios = self.get_operation_services(operacion_id, cursor)

            self.tree.insert(
                "",
                "end",
                values=(
                    operacion_id,
                    codigo_retiro,
                    placa,
                    tipo_vehiculo,
                    fecha_ingreso,
                    nombre_tipo_operacion(tipo_operacion),
                    servicios,
                    nombre_estado_operacion(estado),
                    "Doble clic"
                )
            )

        conn.close()

    def get_operation_services(self, operation_id, cursor):
        cursor.execute("""
            SELECT S.Nombre
            FROM OPERACIONSERVICIO OS
            INNER JOIN SERVICIO S ON OS.Servicio = S.Servicio
            WHERE OS.Operacion = ?
              AND OS.Estado != ?
            ORDER BY S.Nombre ASC
        """, (operation_id, ESTADO_OPERACION_SERVICIO_CANCELADO))
        rows = cursor.fetchall()

        service_names = [row["Nombre"] for row in rows]

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
        action_window.geometry("340x360")
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
            text="Reimprimir ticket",
            font=("Arial", 11, "bold"),
            width=18,
            bg="#2563eb",
            fg="white",
            bd=0,
            relief="flat",
            cursor="hand2",
            command=lambda: self.reprint_ticket(operation_id)
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

    def reprint_ticket(self, operation_id):
        conn = get_connection()
        cursor = conn.cursor()

        try:
            datos = self.get_operation_ticket_data(cursor, operation_id)

            if not datos:
                messagebox.showwarning("No encontrado", "No se encontró la operación para reimprimir.")
                return

            fecha_dt = datetime.strptime(datos["FechaIngreso"], "%Y-%m-%d %H:%M:%S")
            fecha_ticket = fecha_dt.strftime("%d/%m/%Y")
            hora_ticket = fecha_dt.strftime("%H:%M")

            imprimir_ticket(
                codigo=datos["CodigoRetiro"],
                placa=datos["Placa"],
                fecha=fecha_ticket,
                hora_ingreso=hora_ticket
            )

            messagebox.showinfo(
                "Ticket reimpreso",
                f"Se reimprimió correctamente el ticket.\n\nCódigo: {datos['CodigoRetiro']}"
            )

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo reimprimir el ticket.\n{str(e)}"
            )

        finally:
            conn.close()

    def get_operation_ticket_data(self, cursor, operation_id):
        cursor.execute("""
            SELECT
                O.Operacion,
                O.CodigoRetiro,
                O.FechaIngreso,
                V.Placa
            FROM OPERACION O
            INNER JOIN VEHICULO V ON O.Vehiculo = V.Vehiculo
            WHERE O.Operacion = ?
            LIMIT 1
        """, (operation_id,))

        return cursor.fetchone()


# =========================================================
# FORMULARIO DE OPERACIÓN
# =========================================================
class OperationFormWindow:
    def __init__(self, operations_view, user_data, mode="create", operation_id=None):
        self.operations_view = operations_view
        self.user_data = user_data
        self.mode = mode
        self.operation_id = operation_id

        self.window = tk.Toplevel()
        self.window.title("Nueva operación" if mode == "create" else "Editar operación")
        self.window.geometry("560x720")
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
        self.loaded_contract_id = None

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
                self.service_vars[service["Servicio"]] = var
                tk.Checkbutton(
                    services_frame,
                    text=f"{service['Nombre']} (Bs {float(service['Precio']):.2f})",
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
            SELECT Servicio, Nombre, Precio
            FROM SERVICIO
            WHERE Estado = ?
            ORDER BY Nombre ASC
        """, (ESTADO_GENERAL_ACTIVO,))
        rows = cursor.fetchall()
        conn.close()

        self.services_data = rows

    def load_data(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                O.Operacion,
                O.Vehiculo,
                O.Cliente,
                O.Contrato,
                O.Observacion,
                V.Placa,
                V.TipoVehiculo,
                CL.Nombres
            FROM OPERACION O
            INNER JOIN VEHICULO V ON O.Vehiculo = V.Vehiculo
            LEFT JOIN CLIENTE CL ON O.Cliente = CL.Cliente
            WHERE O.Operacion = ? AND O.Estado = ?
        """, (self.operation_id, ESTADO_OPERACION_ACTIVO))
        row = cursor.fetchone()

        if not row:
            conn.close()
            messagebox.showerror("Error", "No se encontró la operación activa.")
            self.window.destroy()
            return

        self.loaded_vehicle_id = row["Vehiculo"]
        self.loaded_customer_id = row["Cliente"]
        self.loaded_contract_id = row["Contrato"]

        numero, letras = self.split_plate(row["Placa"])
        self.entry_placa_numero.insert(0, numero)
        self.entry_placa_letras.insert(0, letras)
        self.vehicle_type_var.set(row["TipoVehiculo"] if row["TipoVehiculo"] else "auto")
        self.entry_cliente.insert(0, row["Nombres"] if row["Nombres"] else "")
        self.text_observaciones.insert("1.0", row["Observacion"] if row["Observacion"] else "")

        cursor.execute("""
            SELECT Servicio
            FROM OPERACIONSERVICIO
            WHERE Operacion = ? AND Estado != ?
        """, (self.operation_id, ESTADO_OPERACION_SERVICIO_CANCELADO))
        selected_ids = {r["Servicio"] for r in cursor.fetchall()}

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
            usr = obtener_usuario_actual_id(self.user_data)

            if self.mode == "create":
                vehiculo_id = self.get_or_create_vehicle(cursor, placa, tipo_vehiculo)
                cliente_id = self.get_or_create_customer_by_name(cursor, cliente_nombre)
                contrato_id = self.get_active_contract_for_vehicle(cursor, vehiculo_id)

                tipo_operacion = TIPO_OPERACION_CONTRATO if contrato_id else TIPO_OPERACION_NORMAL
                tarifa_id = self.get_main_tariff_for_vehicle(cursor, tipo_vehiculo)

                codigo_operacion = self.generate_operation_code(cursor)
                codigo_retiro = self.generate_pickup_code(cursor)
                fecha_ingreso = ahora_texto()

                cursor.execute("""
                    INSERT INTO OPERACION (
                        CodigoOperacion,
                        Vehiculo,
                        Cliente,
                        Tarifa,
                        Contrato,
                        UsuarioIngreso,
                        FechaIngreso,
                        TipoOperacion,
                        Estado,
                        CodigoRetiro,
                        Observacion,
                        Usr,
                        UsrFecha,
                        UsrHora,
                        FechaCreacion,
                        FechaModificacion
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        date('now','localtime'),
                        time('now','localtime'),
                        datetime('now','localtime'),
                        datetime('now','localtime')
                    )
                """, (
                    codigo_operacion,
                    vehiculo_id,
                    cliente_id,
                    tarifa_id,
                    contrato_id,
                    usr,
                    fecha_ingreso,
                    tipo_operacion,
                    ESTADO_OPERACION_ACTIVO,
                    codigo_retiro,
                    observaciones if observaciones else None,
                    usr
                ))

                operacion_id = cursor.lastrowid
                self.replace_services(cursor, operacion_id)

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
                    "CREAR_OPERACION",
                    "OPERACION",
                    operacion_id,
                    f"Se creó la operación {operacion_id} para placa {placa} con código de retiro {codigo_retiro}",
                    fecha_ingreso,
                    ESTADO_GENERAL_ACTIVO,
                    usr
                ))

                conn.commit()

                if contrato_id:
                    messagebox.showinfo(
                        "Operación registrada",
                        f"Operación creada correctamente.\n\nCódigo de retiro: {codigo_retiro}\nVehículo con contrato activo."
                    )
                else:
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

                contrato_id = self.get_active_contract_for_vehicle(cursor, self.loaded_vehicle_id)
                tipo_operacion = TIPO_OPERACION_CONTRATO if contrato_id else TIPO_OPERACION_NORMAL
                tarifa_id = self.get_main_tariff_for_vehicle(cursor, tipo_vehiculo)

                cursor.execute("""
                    UPDATE VEHICULO
                    SET
                        Placa = ?,
                        TipoVehiculo = ?,
                        Usr = ?,
                        UsrFecha = date('now','localtime'),
                        UsrHora = time('now','localtime'),
                        FechaModificacion = datetime('now','localtime')
                    WHERE Vehiculo = ?
                """, (placa, tipo_vehiculo, usr, self.loaded_vehicle_id))

                cursor.execute("""
                    UPDATE OPERACION
                    SET
                        Cliente = ?,
                        Tarifa = ?,
                        Contrato = ?,
                        TipoOperacion = ?,
                        Observacion = ?,
                        Usr = ?,
                        UsrFecha = date('now','localtime'),
                        UsrHora = time('now','localtime'),
                        FechaModificacion = datetime('now','localtime')
                    WHERE Operacion = ?
                """, (
                    cliente_id,
                    tarifa_id,
                    contrato_id,
                    tipo_operacion,
                    observaciones if observaciones else None,
                    usr,
                    self.operation_id
                ))

                self.replace_services(cursor, self.operation_id)

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
                    "EDITAR_OPERACION",
                    "OPERACION",
                    self.operation_id,
                    f"Se editó la operación {self.operation_id} para placa {placa}",
                    ahora_texto(),
                    ESTADO_GENERAL_ACTIVO,
                    usr
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
        cursor.execute("""
            SELECT Vehiculo
            FROM VEHICULO
            WHERE REPLACE(REPLACE(UPPER(Placa), ' ', ''), '-', '') = ?
        """, (limpiar_placa_para_busqueda(placa),))
        row = cursor.fetchone()

        usr = obtener_usuario_actual_id(self.user_data)

        if row:
            cursor.execute("""
                UPDATE VEHICULO
                SET
                    TipoVehiculo = ?,
                    Placa = ?,
                    Usr = ?,
                    UsrFecha = date('now','localtime'),
                    UsrHora = time('now','localtime'),
                    FechaModificacion = datetime('now','localtime')
                WHERE Vehiculo = ?
            """, (tipo_vehiculo, placa, usr, row["Vehiculo"]))
            return row["Vehiculo"]

        cursor.execute("""
            INSERT INTO VEHICULO (
                Placa,
                TipoVehiculo,
                Estado,
                Usr,
                UsrFecha,
                UsrHora,
                FechaCreacion,
                FechaModificacion
            )
            VALUES (
                ?, ?, ?, ?,
                date('now','localtime'),
                time('now','localtime'),
                datetime('now','localtime'),
                datetime('now','localtime')
            )
        """, (
            placa,
            tipo_vehiculo,
            ESTADO_GENERAL_ACTIVO,
            usr
        ))
        return cursor.lastrowid

    def get_or_create_customer_by_name(self, cursor, nombre, existing_customer_id=None):
        if not nombre:
            return None

        usr = obtener_usuario_actual_id(self.user_data)

        if existing_customer_id:
            cursor.execute("""
                UPDATE CLIENTE
                SET
                    Nombres = ?,
                    Usr = ?,
                    UsrFecha = date('now','localtime'),
                    UsrHora = time('now','localtime'),
                    FechaModificacion = datetime('now','localtime')
                WHERE Cliente = ?
            """, (nombre, usr, existing_customer_id))
            return existing_customer_id

        cursor.execute("""
            INSERT INTO CLIENTE (
                Nombres,
                Estado,
                Usr,
                UsrFecha,
                UsrHora,
                FechaCreacion,
                FechaModificacion
            )
            VALUES (
                ?, ?, ?,
                date('now','localtime'),
                time('now','localtime'),
                datetime('now','localtime'),
                datetime('now','localtime')
            )
        """, (
            nombre,
            ESTADO_GENERAL_ACTIVO,
            usr
        ))
        return cursor.lastrowid

    def get_main_tariff_for_vehicle(self, cursor, tipo_vehiculo):
        cursor.execute("""
            SELECT Tarifa
            FROM TARIFA
            WHERE Estado = ?
              AND TipoVehiculo = ?
              AND TipoTarifa = ?
            ORDER BY Tarifa ASC
            LIMIT 1
        """, (
            ESTADO_GENERAL_ACTIVO,
            tipo_vehiculo,
            TIPO_TARIFA_ESCALONADA
        ))
        row = cursor.fetchone()

        if not row:
            raise Exception(f"No existe una tarifa escalonada activa para {tipo_vehiculo}.")

        return row["Tarifa"]

    def get_active_contract_for_vehicle(self, cursor, vehiculo_id):
        hoy = datetime.now().strftime("%Y-%m-%d")

        cursor.execute("""
            SELECT Contrato
            FROM CONTRATO
            WHERE Vehiculo = ?
              AND Estado = ?
              AND FechaInicio <= ?
              AND FechaFin >= ?
            ORDER BY Contrato DESC
            LIMIT 1
        """, (
            vehiculo_id,
            ESTADO_CONTRATO_ACTIVO,
            hoy,
            hoy
        ))
        row = cursor.fetchone()

        if not row:
            return None

        return row["Contrato"]

    def replace_services(self, cursor, operacion_id):
        cursor.execute("DELETE FROM OPERACIONSERVICIO WHERE Operacion = ?", (operacion_id,))

        selected_service_ids = [
            service_id for service_id, var in self.service_vars.items() if var.get()
        ]

        usr = obtener_usuario_actual_id(self.user_data)

        for service_id in selected_service_ids:
            cursor.execute("""
                SELECT Precio
                FROM SERVICIO
                WHERE Servicio = ? AND Estado = ?
            """, (service_id, ESTADO_GENERAL_ACTIVO))
            row = cursor.fetchone()

            if not row:
                continue

            precio = float(row["Precio"])

            cursor.execute("""
                INSERT INTO OPERACIONSERVICIO (
                    Operacion,
                    Servicio,
                    Cantidad,
                    PrecioUnitario,
                    Subtotal,
                    Estado,
                    Usr,
                    UsrFecha,
                    UsrHora,
                    FechaCreacion,
                    FechaModificacion
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?,
                    date('now','localtime'),
                    time('now','localtime'),
                    datetime('now','localtime'),
                    datetime('now','localtime')
                )
            """, (
                operacion_id,
                service_id,
                1,
                precio,
                precio,
                ESTADO_OPERACION_SERVICIO_PENDIENTE,
                usr
            ))

    def generate_operation_code(self, cursor):
        while True:
            code = "OP-" + datetime.now().strftime("%Y%m%d%H%M%S")
            cursor.execute("SELECT 1 FROM OPERACION WHERE CodigoOperacion = ?", (code,))
            if not cursor.fetchone():
                return code

    def generate_pickup_code(self, cursor):
        while True:
            code = datetime.now().strftime("%H%M%S")
            cursor.execute("""
                SELECT 1
                FROM OPERACION
                WHERE CodigoRetiro = ? AND Estado = ?
            """, (code, ESTADO_OPERACION_ACTIVO))
            if not cursor.fetchone():
                return code

    def run(self):
        pass


# =========================================================
# CANCELAR OPERACIÓN
# =========================================================
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
            now_str = ahora_texto()
            usr = obtener_usuario_actual_id(self.user_data)

            cursor.execute("""
                UPDATE OPERACION
                SET
                    Estado = ?,
                    MotivoCancelacion = ?,
                    FechaSalida = ?,
                    Usr = ?,
                    UsrFecha = date('now','localtime'),
                    UsrHora = time('now','localtime'),
                    FechaModificacion = datetime('now','localtime')
                WHERE Operacion = ? AND Estado = ?
            """, (
                ESTADO_OPERACION_CANCELADO,
                reason,
                now_str,
                usr,
                self.operation_id,
                ESTADO_OPERACION_ACTIVO
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
                "CANCELAR_OPERACION",
                "OPERACION",
                self.operation_id,
                f"Se canceló la operación {self.operation_id}. Motivo: {reason}",
                now_str,
                ESTADO_GENERAL_ACTIVO,
                usr
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


# =========================================================
# COBRAR OPERACIÓN
# =========================================================
class ChargeOperationWindow:
    def __init__(self, operations_view, user_data, operation_id):
        self.operations_view = operations_view
        self.user_data = user_data
        self.operation_id = operation_id

        self.window = tk.Toplevel()
        self.window.title("Cobrar operación")
        self.window.geometry("540x600")
        self.window.minsize(520, 560)
        self.window.resizable(False, False)
        self.window.configure(bg="white")
        self.window.grab_set()

        self.operation_data = None
        self.calculation = None
        self.method_var = tk.IntVar(value=METODO_PAGO_EFECTIVO)

        self.load_operation_data()
        self.build_ui()

    def load_operation_data(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                O.Operacion,
                O.CodigoRetiro,
                O.FechaIngreso,
                O.Tarifa,
                O.Contrato,
                O.TipoOperacion,
                V.Placa,
                V.TipoVehiculo
            FROM OPERACION O
            INNER JOIN VEHICULO V ON O.Vehiculo = V.Vehiculo
            WHERE O.Operacion = ? AND O.Estado = ?
        """, (self.operation_id, ESTADO_OPERACION_ACTIVO))
        row = cursor.fetchone()

        if not row:
            conn.close()
            raise Exception("La operación no existe o ya no está activa.")

        self.operation_data = {
            "Operacion": row["Operacion"],
            "CodigoRetiro": row["CodigoRetiro"],
            "FechaIngreso": row["FechaIngreso"],
            "Tarifa": row["Tarifa"],
            "Contrato": row["Contrato"],
            "TipoOperacion": row["TipoOperacion"],
            "Placa": row["Placa"],
            "TipoVehiculo": row["TipoVehiculo"],
        }

        cursor.execute("""
            SELECT COALESCE(SUM(Subtotal), 0) AS TotalServicios
            FROM OPERACIONSERVICIO
            WHERE Operacion = ? AND Estado != ?
        """, (self.operation_id, ESTADO_OPERACION_SERVICIO_CANCELADO))
        monto_servicios = float(cursor.fetchone()["TotalServicios"] or 0)

        conn.close()

        fecha_ingreso_dt = datetime.strptime(self.operation_data["FechaIngreso"], "%Y-%m-%d %H:%M:%S")
        fecha_salida_dt = datetime.now()
        total_minutes = max(1, int((fecha_salida_dt - fecha_ingreso_dt).total_seconds() / 60))

        monto_parqueo = self.calcular_monto_parqueo(
            tipo_operacion=self.operation_data["TipoOperacion"],
            tipo_vehiculo=self.operation_data["TipoVehiculo"],
            minutos_estadia=total_minutes,
            fecha_ingreso_dt=fecha_ingreso_dt,
            fecha_salida_dt=fecha_salida_dt
        )

        monto_total = monto_parqueo + monto_servicios

        self.calculation = {
            "FechaSalida": fecha_salida_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "MinutosEstadia": total_minutes,
            "MontoParqueo": round(monto_parqueo, 2),
            "MontoServicios": round(monto_servicios, 2),
            "MontoTotal": round(monto_total, 2)
        }

    def calcular_monto_parqueo(self, tipo_operacion, tipo_vehiculo, minutos_estadia, fecha_ingreso_dt, fecha_salida_dt):
        if tipo_operacion == TIPO_OPERACION_CONTRATO:
            return 0.0

        conn = get_connection()
        cursor = conn.cursor()

        try:
            tipo_dia = TIPO_DIA_SABADO if es_sabado(fecha_ingreso_dt) else TIPO_DIA_LUNES_VIERNES

            if franja_nocturna_aplica(fecha_ingreso_dt, fecha_salida_dt):
                cursor.execute("""
                    SELECT TD.Monto
                    FROM TARIFA T
                    INNER JOIN TARIFADETALLE TD ON T.Tarifa = TD.Tarifa
                    WHERE T.Estado = ?
                      AND T.TipoVehiculo = ?
                      AND T.TipoTarifa = ?
                      AND TD.Estado = ?
                      AND TD.TipoDia = ?
                    ORDER BY TD.TarifaDetalle ASC
                    LIMIT 1
                """, (
                    ESTADO_GENERAL_ACTIVO,
                    tipo_vehiculo,
                    TIPO_TARIFA_NOCTURNA,
                    ESTADO_GENERAL_ACTIVO,
                    TIPO_DIA_NOCTURNA
                ))
                row_nocturna = cursor.fetchone()
                if row_nocturna:
                    return float(row_nocturna["Monto"])

            cursor.execute("""
                SELECT TD.Monto
                FROM TARIFA T
                INNER JOIN TARIFADETALLE TD ON T.Tarifa = TD.Tarifa
                WHERE T.Estado = ?
                  AND T.TipoVehiculo = ?
                  AND T.TipoTarifa = ?
                  AND TD.Estado = ?
                  AND TD.TipoDia = ?
                  AND ? BETWEEN TD.MinutoInicio AND TD.MinutoFin
                ORDER BY TD.TarifaDetalle ASC
                LIMIT 1
            """, (
                ESTADO_GENERAL_ACTIVO,
                tipo_vehiculo,
                TIPO_TARIFA_ESCALONADA,
                ESTADO_GENERAL_ACTIVO,
                tipo_dia,
                minutos_estadia
            ))
            row = cursor.fetchone()

            if row:
                return float(row["Monto"])

            cursor.execute("""
                SELECT TD.Monto
                FROM TARIFA T
                INNER JOIN TARIFADETALLE TD ON T.Tarifa = TD.Tarifa
                WHERE T.Estado = ?
                  AND T.TipoVehiculo = ?
                  AND T.TipoTarifa = ?
                  AND TD.Estado = ?
                  AND TD.TipoDia = ?
                ORDER BY TD.MinutoFin DESC
                LIMIT 1
            """, (
                ESTADO_GENERAL_ACTIVO,
                tipo_vehiculo,
                TIPO_TARIFA_ESCALONADA,
                ESTADO_GENERAL_ACTIVO,
                tipo_dia
            ))
            row_ultimo = cursor.fetchone()

            if row_ultimo:
                return float(row_ultimo["Monto"])

            raise Exception(f"No existe detalle de tarifa configurado para {tipo_vehiculo}.")

        finally:
            conn.close()

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
            ("Código retiro:", self.operation_data["CodigoRetiro"]),
            ("Placa:", self.operation_data["Placa"]),
            ("Ingreso:", self.operation_data["FechaIngreso"]),
            ("Salida:", self.calculation["FechaSalida"]),
            ("Tiempo:", f"{self.calculation['MinutosEstadia']} min"),
            ("Modalidad:", nombre_tipo_operacion(self.operation_data["TipoOperacion"])),
            ("Monto parqueo:", f"Bs {self.calculation['MontoParqueo']:.2f}"),
            ("Monto servicios:", f"Bs {self.calculation['MontoServicios']:.2f}"),
            ("Total:", f"Bs {self.calculation['MontoTotal']:.2f}")
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

        methods = [("Efectivo", METODO_PAGO_EFECTIVO), ("QR", METODO_PAGO_QR)]
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
            usr = obtener_usuario_actual_id(self.user_data)

            cursor.execute("""
                UPDATE OPERACION
                SET
                    UsuarioSalida = ?,
                    FechaSalida = ?,
                    MinutosEstadia = ?,
                    MontoParqueo = ?,
                    MontoServicios = ?,
                    MontoTotal = ?,
                    Estado = ?,
                    Usr = ?,
                    UsrFecha = date('now','localtime'),
                    UsrHora = time('now','localtime'),
                    FechaModificacion = datetime('now','localtime')
                WHERE Operacion = ?
            """, (
                usr,
                self.calculation["FechaSalida"],
                self.calculation["MinutosEstadia"],
                self.calculation["MontoParqueo"],
                self.calculation["MontoServicios"],
                self.calculation["MontoTotal"],
                ESTADO_OPERACION_FINALIZADO,
                usr,
                self.operation_id
            ))

            cursor.execute("""
                INSERT INTO PAGO (
                    Operacion,
                    Usuario,
                    FechaPago,
                    MetodoPago,
                    Monto,
                    Observacion,
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
                self.operation_id,
                usr,
                self.calculation["FechaSalida"],
                self.method_var.get(),
                self.calculation["MontoTotal"],
                f"Cobro registrado desde módulo Operaciones. Código de retiro: {self.operation_data['CodigoRetiro']}",
                ESTADO_GENERAL_ACTIVO,
                usr
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
                "COBRAR_OPERACION",
                "OPERACION",
                self.operation_id,
                f"Se cobró la operación {self.operation_id} con código de retiro {self.operation_data['CodigoRetiro']} por Bs {self.calculation['MontoTotal']:.2f}",
                self.calculation["FechaSalida"],
                ESTADO_GENERAL_ACTIVO,
                usr
            ))

            conn.commit()

            messagebox.showinfo(
                "Cobro realizado",
                f"Operación finalizada correctamente.\n"
                f"Código de retiro: {self.operation_data['CodigoRetiro']}\n"
                f"Total cobrado: Bs {self.calculation['MontoTotal']:.2f}"
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