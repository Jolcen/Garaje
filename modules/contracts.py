import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import calendar

from database.db import get_connection


# =========================================================
# CATÁLOGOS
# =========================================================
ESTADOS_CONTRATO = {
    0: "Inactivo",
    1: "Activo",
    2: "Vencido",
    3: "Suspendido",
    4: "Cancelado",
    5: "Finalizado",
}

ESTADOS_CONTRATO_INV = {v: k for k, v in ESTADOS_CONTRATO.items()}

MODALIDAD_PAGO = {
    1: "Efectivo",
    2: "QR",
}

MODALIDAD_PAGO_INV = {v: k for k, v in MODALIDAD_PAGO.items()}


# =========================================================
# UTILIDADES
# =========================================================
def fecha_actual_str():
    return datetime.now().strftime("%Y-%m-%d")


def sumar_meses(fecha_inicio_str, meses):
    """
    Suma meses a una fecha YYYY-MM-DD conservando el día en lo posible.
    """
    fecha = datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
    year = fecha.year + (fecha.month - 1 + meses) // 12
    month = (fecha.month - 1 + meses) % 12 + 1
    day = min(fecha.day, calendar.monthrange(year, month)[1])
    nueva = fecha.replace(year=year, month=month, day=day)
    return nueva.strftime("%Y-%m-%d")


def formatear_cliente(row):
    nombres = (row["Nombres"] or "").strip()
    apellidos = (row["Apellidos"] or "").strip()
    documento = (row["DocumentoIdentidad"] or "").strip()

    nombre_completo = f"{nombres} {apellidos}".strip()
    if documento:
        return f"{row['Cliente']} - {nombre_completo} | CI: {documento}"
    return f"{row['Cliente']} - {nombre_completo}"


def formatear_vehiculo(row):
    placa = (row["Placa"] or "").strip()
    tipo = (row["TipoVehiculo"] or "").strip()
    marca = (row["Marca"] or "").strip()
    modelo = (row["Modelo"] or "").strip()

    extra = " ".join(x for x in [marca, modelo] if x).strip()
    if extra:
        return f"{row['Vehiculo']} - {placa} | {tipo} | {extra}"
    return f"{row['Vehiculo']} - {placa} | {tipo}"


# =========================================================
# ACCESO A DATOS
# =========================================================
def obtener_clientes():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Cliente, Nombres, Apellidos, DocumentoIdentidad
        FROM CLIENTE
        WHERE Estado = 1
        ORDER BY Nombres, Apellidos
    """)
    filas = cursor.fetchall()
    conn.close()
    return filas


def obtener_vehiculos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Vehiculo, Placa, TipoVehiculo, Marca, Modelo
        FROM VEHICULO
        WHERE Estado = 1
        ORDER BY Placa
    """)
    filas = cursor.fetchall()
    conn.close()
    return filas


def obtener_contrato_por_id(contrato_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            C.Contrato,
            C.CodigoContrato,
            C.Cliente,
            C.Vehiculo,
            C.FechaInicio,
            C.FechaFin,
            C.DuracionMes,
            C.MontoContrato,
            C.ModalidadPago,
            C.EspacioAsignado,
            C.Observacion,
            C.Estado,
            CL.Nombres,
            CL.Apellidos,
            CL.DocumentoIdentidad,
            V.Placa,
            V.TipoVehiculo,
            V.Marca,
            V.Modelo
        FROM CONTRATO C
        INNER JOIN CLIENTE CL ON CL.Cliente = C.Cliente
        INNER JOIN VEHICULO V ON V.Vehiculo = C.Vehiculo
        WHERE C.Contrato = ?
    """, (contrato_id,))

    fila = cursor.fetchone()
    conn.close()
    return fila


def obtener_contratos(busqueda="", estado=None):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            C.Contrato,
            C.CodigoContrato,
            C.Cliente,
            C.Vehiculo,
            C.FechaInicio,
            C.FechaFin,
            C.DuracionMes,
            C.MontoContrato,
            C.ModalidadPago,
            C.EspacioAsignado,
            C.Observacion,
            C.Estado,

            CL.Nombres,
            CL.Apellidos,
            CL.DocumentoIdentidad,

            V.Placa,
            V.TipoVehiculo,
            V.Marca,
            V.Modelo
        FROM CONTRATO C
        INNER JOIN CLIENTE CL ON CL.Cliente = C.Cliente
        INNER JOIN VEHICULO V ON V.Vehiculo = C.Vehiculo
        WHERE 1 = 1
    """
    params = []

    if busqueda.strip():
        like = f"%{busqueda.strip()}%"
        query += """
            AND (
                C.CodigoContrato LIKE ?
                OR V.Placa LIKE ?
                OR CL.Nombres LIKE ?
                OR CL.Apellidos LIKE ?
                OR CL.DocumentoIdentidad LIKE ?
            )
        """
        params.extend([like, like, like, like, like])

    if estado is not None:
        query += " AND C.Estado = ? "
        params.append(estado)

    query += " ORDER BY C.Contrato DESC "

    cursor.execute(query, params)
    filas = cursor.fetchall()
    conn.close()
    return filas


def existe_contrato_activo_vehiculo(vehiculo, excluir_contrato=None):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT COUNT(*)
        FROM CONTRATO
        WHERE Vehiculo = ?
          AND Estado = 1
    """
    params = [vehiculo]

    if excluir_contrato is not None:
        query += " AND Contrato <> ? "
        params.append(excluir_contrato)

    cursor.execute(query, params)
    existe = cursor.fetchone()[0] > 0
    conn.close()
    return existe


def insertar_contrato(data, usr=0):
    if data["Estado"] == 1 and existe_contrato_activo_vehiculo(data["Vehiculo"]):
        raise ValueError("Ese vehículo ya tiene un contrato activo.")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO CONTRATO (
            Cliente,
            Vehiculo,
            CodigoContrato,
            FechaInicio,
            FechaFin,
            DuracionMes,
            MontoContrato,
            ModalidadPago,
            EspacioAsignado,
            Observacion,
            Estado,
            Usr,
            UsrFecha,
            UsrHora,
            FechaCreacion,
            FechaModificacion
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, date('now','localtime'), time('now','localtime'),
            datetime('now','localtime'), datetime('now','localtime')
        )
    """, (
        data["Cliente"],
        data["Vehiculo"],
        data["CodigoContrato"],
        data["FechaInicio"],
        data["FechaFin"],
        data["DuracionMes"],
        data["MontoContrato"],
        data["ModalidadPago"],
        data["EspacioAsignado"],
        data["Observacion"],
        data["Estado"],
        usr
    ))

    conn.commit()
    conn.close()


def actualizar_contrato(contrato_id, data, usr=0):
    if data["Estado"] == 1 and existe_contrato_activo_vehiculo(
        data["Vehiculo"], excluir_contrato=contrato_id
    ):
        raise ValueError("Ese vehículo ya tiene otro contrato activo.")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE CONTRATO
        SET
            Cliente = ?,
            Vehiculo = ?,
            CodigoContrato = ?,
            FechaInicio = ?,
            FechaFin = ?,
            DuracionMes = ?,
            MontoContrato = ?,
            ModalidadPago = ?,
            EspacioAsignado = ?,
            Observacion = ?,
            Estado = ?,
            Usr = ?,
            UsrFecha = date('now','localtime'),
            UsrHora = time('now','localtime'),
            FechaModificacion = datetime('now','localtime')
        WHERE Contrato = ?
    """, (
        data["Cliente"],
        data["Vehiculo"],
        data["CodigoContrato"],
        data["FechaInicio"],
        data["FechaFin"],
        data["DuracionMes"],
        data["MontoContrato"],
        data["ModalidadPago"],
        data["EspacioAsignado"],
        data["Observacion"],
        data["Estado"],
        usr,
        contrato_id
    ))

    conn.commit()
    conn.close()


def cambiar_estado_contrato(contrato_id, nuevo_estado, usr=0):
    conn = get_connection()
    cursor = conn.cursor()

    if nuevo_estado == 1:
        cursor.execute("SELECT Vehiculo FROM CONTRATO WHERE Contrato = ?", (contrato_id,))
        fila = cursor.fetchone()
        if not fila:
            conn.close()
            raise ValueError("Contrato no encontrado.")

        vehiculo = fila["Vehiculo"]
        if existe_contrato_activo_vehiculo(vehiculo, excluir_contrato=contrato_id):
            conn.close()
            raise ValueError("Ese vehículo ya tiene otro contrato activo.")

    cursor.execute("""
        UPDATE CONTRATO
        SET
            Estado = ?,
            Usr = ?,
            UsrFecha = date('now','localtime'),
            UsrHora = time('now','localtime'),
            FechaModificacion = datetime('now','localtime')
        WHERE Contrato = ?
    """, (nuevo_estado, usr, contrato_id))

    conn.commit()
    conn.close()


# =========================================================
# FORMULARIO
# =========================================================
class ContractForm(tk.Toplevel):
    def __init__(self, master, user_data, on_save, contrato=None):
        super().__init__(master)

        self.user_data = user_data or {}
        self.on_save = on_save
        self.contrato = contrato

        self.title("Contrato")
        self.geometry("760x650")
        self.minsize(760, 650)
        self.configure(bg="#f4f6f8")
        self.transient(master)
        self.grab_set()

        self.clientes = obtener_clientes()
        self.vehiculos = obtener_vehiculos()

        self.mapa_clientes = {formatear_cliente(c): c["Cliente"] for c in self.clientes}
        self.mapa_vehiculos = {formatear_vehiculo(v): v["Vehiculo"] for v in self.vehiculos}

        self._build_ui()
        self._cargar_datos_si_edicion()
        self._recalcular_fin_silencioso()

    def _build_ui(self):
        container = tk.Frame(self, bg="#f4f6f8")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        titulo = "Editar contrato" if self.contrato else "Nuevo contrato"
        tk.Label(
            container,
            text=titulo,
            font=("Arial", 16, "bold"),
            bg="#f4f6f8",
            fg="#1f2937"
        ).pack(anchor="w", pady=(0, 12))

        form = tk.Frame(container, bg="#ffffff", bd=1, relief="solid")
        form.pack(fill="both", expand=True)

        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        self.var_codigo = tk.StringVar()
        self.var_cliente = tk.StringVar()
        self.var_vehiculo = tk.StringVar()
        self.var_fecha_inicio = tk.StringVar(value=fecha_actual_str())
        self.var_duracion = tk.StringVar(value="1")
        self.var_fecha_fin = tk.StringVar()
        self.var_monto = tk.StringVar(value="0")
        self.var_modalidad = tk.StringVar(value="Efectivo")
        self.var_estado = tk.StringVar(value="Activo")
        self.var_espacio = tk.StringVar()

        fila = 0
        self._add_label_entry(form, "Código contrato:", self.var_codigo, fila, 0)
        self._add_label_combo(
            form, "Estado:", self.var_estado, list(ESTADOS_CONTRATO_INV.keys()), fila, 2
        )
        fila += 1

        self._add_label_combo(
            form, "Cliente:", self.var_cliente, list(self.mapa_clientes.keys()), fila, 0, width=42
        )
        self._add_label_combo(
            form, "Vehículo:", self.var_vehiculo, list(self.mapa_vehiculos.keys()), fila, 2, width=42
        )
        fila += 1

        self._add_label_entry(form, "Fecha inicio (YYYY-MM-DD):", self.var_fecha_inicio, fila, 0)
        self._add_label_entry(form, "Duración (meses):", self.var_duracion, fila, 2)
        fila += 1

        self._add_label_entry(form, "Fecha fin:", self.var_fecha_fin, fila, 0, state="readonly")
        self._add_label_entry(form, "Monto contrato:", self.var_monto, fila, 2)
        fila += 1

        self._add_label_combo(
            form, "Modalidad pago:", self.var_modalidad, list(MODALIDAD_PAGO_INV.keys()), fila, 0
        )
        self._add_label_entry(form, "Espacio asignado:", self.var_espacio, fila, 2)
        fila += 1

        tk.Label(
            form,
            text="Observación:",
            font=("Arial", 10, "bold"),
            bg="#ffffff",
            fg="#374151"
        ).grid(row=fila, column=0, sticky="w", padx=14, pady=(12, 6))

        self.txt_observacion = tk.Text(
            form,
            width=70,
            height=8,
            font=("Arial", 10),
            wrap="word",
            bd=1,
            relief="solid"
        )
        self.txt_observacion.grid(
            row=fila + 1, column=0, columnspan=4,
            sticky="nsew", padx=14, pady=(0, 12)
        )

        btns = tk.Frame(container, bg="#f4f6f8")
        btns.pack(fill="x", pady=(12, 0))

        tk.Button(
            btns,
            text="Calcular fecha fin",
            font=("Arial", 10, "bold"),
            bg="#2563eb",
            fg="white",
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            command=self.calcular_fecha_fin
        ).pack(side="left")

        tk.Button(
            btns,
            text="Guardar",
            font=("Arial", 10, "bold"),
            bg="#059669",
            fg="white",
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            command=self.guardar
        ).pack(side="right", padx=(8, 0))

        tk.Button(
            btns,
            text="Cancelar",
            font=("Arial", 10, "bold"),
            bg="#6b7280",
            fg="white",
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            command=self.destroy
        ).pack(side="right")

        self.var_fecha_inicio.trace_add("write", lambda *_: self._recalcular_fin_silencioso())
        self.var_duracion.trace_add("write", lambda *_: self._recalcular_fin_silencioso())

    def _add_label_entry(self, parent, text, variable, row, col, state="normal"):
        tk.Label(
            parent,
            text=text,
            font=("Arial", 10, "bold"),
            bg="#ffffff",
            fg="#374151"
        ).grid(row=row, column=col, sticky="w", padx=14, pady=(12, 6))

        entry = tk.Entry(
            parent,
            textvariable=variable,
            font=("Arial", 10),
            relief="solid",
            bd=1,
            state=state
        )
        entry.grid(row=row, column=col + 1, sticky="ew", padx=(0, 14), pady=(12, 6))

    def _add_label_combo(self, parent, text, variable, values, row, col, width=28):
        tk.Label(
            parent,
            text=text,
            font=("Arial", 10, "bold"),
            bg="#ffffff",
            fg="#374151"
        ).grid(row=row, column=col, sticky="w", padx=14, pady=(12, 6))

        combo = ttk.Combobox(
            parent,
            textvariable=variable,
            values=values,
            state="readonly",
            width=width
        )
        combo.grid(row=row, column=col + 1, sticky="ew", padx=(0, 14), pady=(12, 6))

    def _cargar_datos_si_edicion(self):
        if not self.contrato:
            return

        self.var_codigo.set(self.contrato["CodigoContrato"])
        self.var_fecha_inicio.set(self.contrato["FechaInicio"])
        self.var_duracion.set(str(self.contrato["DuracionMes"]))
        self.var_fecha_fin.set(self.contrato["FechaFin"])
        self.var_monto.set(str(self.contrato["MontoContrato"]))
        self.var_modalidad.set(MODALIDAD_PAGO.get(self.contrato["ModalidadPago"], "Efectivo"))
        self.var_estado.set(ESTADOS_CONTRATO.get(self.contrato["Estado"], "Activo"))
        self.var_espacio.set(self.contrato["EspacioAsignado"] or "")
        self.txt_observacion.insert("1.0", self.contrato["Observacion"] or "")

        for texto, cliente_id in self.mapa_clientes.items():
            if cliente_id == self.contrato["Cliente"]:
                self.var_cliente.set(texto)
                break

        for texto, vehiculo_id in self.mapa_vehiculos.items():
            if vehiculo_id == self.contrato["Vehiculo"]:
                self.var_vehiculo.set(texto)
                break

    def _recalcular_fin_silencioso(self):
        try:
            fecha_inicio = self.var_fecha_inicio.get().strip()
            duracion = int(self.var_duracion.get().strip())
            if fecha_inicio and duracion > 0:
                self.var_fecha_fin.set(sumar_meses(fecha_inicio, duracion))
        except Exception:
            self.var_fecha_fin.set("")

    def calcular_fecha_fin(self):
        try:
            fecha_inicio = self.var_fecha_inicio.get().strip()
            duracion = int(self.var_duracion.get().strip())

            datetime.strptime(fecha_inicio, "%Y-%m-%d")
            if duracion <= 0:
                raise ValueError

            self.var_fecha_fin.set(sumar_meses(fecha_inicio, duracion))
        except Exception:
            messagebox.showerror(
                "Error",
                "Verifica la fecha de inicio y la duración en meses."
            )

    def guardar(self):
        try:
            codigo = self.var_codigo.get().strip()
            cliente_txt = self.var_cliente.get().strip()
            vehiculo_txt = self.var_vehiculo.get().strip()
            fecha_inicio = self.var_fecha_inicio.get().strip()
            fecha_fin = self.var_fecha_fin.get().strip()
            duracion = int(self.var_duracion.get().strip())
            monto = float(self.var_monto.get().strip())
            modalidad = MODALIDAD_PAGO_INV[self.var_modalidad.get().strip()]
            estado = ESTADOS_CONTRATO_INV[self.var_estado.get().strip()]
            espacio = self.var_espacio.get().strip()
            observacion = self.txt_observacion.get("1.0", "end").strip()

            if not codigo:
                raise ValueError("Debes ingresar el código del contrato.")
            if not cliente_txt or cliente_txt not in self.mapa_clientes:
                raise ValueError("Debes seleccionar un cliente válido.")
            if not vehiculo_txt or vehiculo_txt not in self.mapa_vehiculos:
                raise ValueError("Debes seleccionar un vehículo válido.")

            datetime.strptime(fecha_inicio, "%Y-%m-%d")
            datetime.strptime(fecha_fin, "%Y-%m-%d")

            if duracion <= 0:
                raise ValueError("La duración debe ser mayor a 0.")
            if monto < 0:
                raise ValueError("El monto no puede ser negativo.")

            data = {
                "Cliente": self.mapa_clientes[cliente_txt],
                "Vehiculo": self.mapa_vehiculos[vehiculo_txt],
                "CodigoContrato": codigo,
                "FechaInicio": fecha_inicio,
                "FechaFin": fecha_fin,
                "DuracionMes": duracion,
                "MontoContrato": monto,
                "ModalidadPago": modalidad,
                "EspacioAsignado": espacio,
                "Observacion": observacion,
                "Estado": estado,
            }

            usr = self.user_data.get("id", 0)

            if self.contrato:
                actualizar_contrato(self.contrato["Contrato"], data, usr=usr)
            else:
                insertar_contrato(data, usr=usr)

            self.on_save()
            self.destroy()

        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el contrato.\n{e}")


# =========================================================
# VISTA PRINCIPAL
# =========================================================
class ContractsView(tk.Frame):
    def __init__(self, parent, user_data, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.user_data = user_data or {}
        self.configure(bg="#f4f6f8")

        self.var_busqueda = tk.StringVar()
        self.var_estado = tk.StringVar(value="Todos")
        self.tree = None

    def build(self):
        self._build_ui()
        self.cargar_contratos()
        self.pack(fill="both", expand=True)

    def _build_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

        container = tk.Frame(self, bg="#f4f6f8")
        container.pack(fill="both", expand=True, padx=16, pady=16)

        header = tk.Frame(container, bg="#f4f6f8")
        header.pack(fill="x", pady=(0, 10))

        tk.Label(
            header,
            text="Gestión de Contratos",
            font=("Arial", 18, "bold"),
            bg="#f4f6f8",
            fg="#111827"
        ).pack(side="left")

        actions = tk.Frame(container, bg="#f4f6f8")
        actions.pack(fill="x", pady=(0, 10))

        tk.Label(
            actions,
            text="Buscar:",
            font=("Arial", 10, "bold"),
            bg="#f4f6f8"
        ).pack(side="left", padx=(0, 6))

        entry_busqueda = tk.Entry(
            actions,
            textvariable=self.var_busqueda,
            font=("Arial", 10),
            relief="solid",
            bd=1,
            width=28
        )
        entry_busqueda.pack(side="left", padx=(0, 8))
        entry_busqueda.bind("<Return>", lambda e: self.cargar_contratos())

        tk.Label(
            actions,
            text="Estado:",
            font=("Arial", 10, "bold"),
            bg="#f4f6f8"
        ).pack(side="left", padx=(4, 6))

        cbo_estado = ttk.Combobox(
            actions,
            textvariable=self.var_estado,
            state="readonly",
            values=["Todos"] + list(ESTADOS_CONTRATO_INV.keys()),
            width=16
        )
        cbo_estado.pack(side="left", padx=(0, 8))

        tk.Button(
            actions,
            text="Buscar",
            font=("Arial", 10, "bold"),
            bg="#2563eb",
            fg="white",
            bd=0,
            padx=12,
            pady=7,
            cursor="hand2",
            command=self.cargar_contratos
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            actions,
            text="Limpiar",
            font=("Arial", 10, "bold"),
            bg="#6b7280",
            fg="white",
            bd=0,
            padx=12,
            pady=7,
            cursor="hand2",
            command=self.limpiar_filtros
        ).pack(side="left", padx=(0, 12))

        tk.Button(
            actions,
            text="Nuevo contrato",
            font=("Arial", 10, "bold"),
            bg="#059669",
            fg="white",
            bd=0,
            padx=12,
            pady=7,
            cursor="hand2",
            command=self.abrir_nuevo
        ).pack(side="right")

        tabla_frame = tk.Frame(container, bg="#ffffff", bd=1, relief="solid")
        tabla_frame.pack(fill="both", expand=True)

        columnas = (
            "Contrato",
            "CodigoContrato",
            "Cliente",
            "Placa",
            "FechaInicio",
            "FechaFin",
            "DuracionMes",
            "MontoContrato",
            "ModalidadPago",
            "Estado",
        )

        self.tree = ttk.Treeview(
            tabla_frame,
            columns=columnas,
            show="headings",
            height=16
        )

        encabezados = {
            "Contrato": "ID",
            "CodigoContrato": "Código",
            "Cliente": "Cliente",
            "Placa": "Placa",
            "FechaInicio": "Inicio",
            "FechaFin": "Fin",
            "DuracionMes": "Meses",
            "MontoContrato": "Monto",
            "ModalidadPago": "Pago",
            "Estado": "Estado",
        }

        anchos = {
            "Contrato": 60,
            "CodigoContrato": 120,
            "Cliente": 220,
            "Placa": 100,
            "FechaInicio": 100,
            "FechaFin": 100,
            "DuracionMes": 70,
            "MontoContrato": 90,
            "ModalidadPago": 90,
            "Estado": 100,
        }

        for col in columnas:
            self.tree.heading(col, text=encabezados[col])
            self.tree.column(col, width=anchos[col], anchor="center")

        scrollbar_y = ttk.Scrollbar(tabla_frame, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(tabla_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")

        self.tree.bind("<Double-1>", lambda e: self.editar_seleccionado())

        footer = tk.Frame(container, bg="#f4f6f8")
        footer.pack(fill="x", pady=(10, 0))

        tk.Button(
            footer,
            text="Editar",
            font=("Arial", 10, "bold"),
            bg="#f59e0b",
            fg="white",
            bd=0,
            padx=12,
            pady=7,
            cursor="hand2",
            command=self.editar_seleccionado
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            footer,
            text="Activar",
            font=("Arial", 10, "bold"),
            bg="#10b981",
            fg="white",
            bd=0,
            padx=12,
            pady=7,
            cursor="hand2",
            command=lambda: self.cambiar_estado_seleccionado(1)
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            footer,
            text="Suspender",
            font=("Arial", 10, "bold"),
            bg="#f97316",
            fg="white",
            bd=0,
            padx=12,
            pady=7,
            cursor="hand2",
            command=lambda: self.cambiar_estado_seleccionado(3)
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            footer,
            text="Finalizar",
            font=("Arial", 10, "bold"),
            bg="#6b7280",
            fg="white",
            bd=0,
            padx=12,
            pady=7,
            cursor="hand2",
            command=lambda: self.cambiar_estado_seleccionado(5)
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            footer,
            text="Cancelar",
            font=("Arial", 10, "bold"),
            bg="#dc2626",
            fg="white",
            bd=0,
            padx=12,
            pady=7,
            cursor="hand2",
            command=lambda: self.cambiar_estado_seleccionado(4)
        ).pack(side="left")

    def limpiar_filtros(self):
        self.var_busqueda.set("")
        self.var_estado.set("Todos")
        self.cargar_contratos()

    def cargar_contratos(self):
        if self.tree is None:
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        estado_txt = self.var_estado.get().strip()
        estado_valor = None if estado_txt == "Todos" else ESTADOS_CONTRATO_INV.get(estado_txt)

        filas = obtener_contratos(
            busqueda=self.var_busqueda.get().strip(),
            estado=estado_valor
        )

        for fila in filas:
            cliente = f"{fila['Nombres']} {fila['Apellidos'] or ''}".strip()
            self.tree.insert(
                "",
                "end",
                values=(
                    fila["Contrato"],
                    fila["CodigoContrato"],
                    cliente,
                    fila["Placa"],
                    fila["FechaInicio"],
                    fila["FechaFin"],
                    fila["DuracionMes"],
                    f"{float(fila['MontoContrato']):.2f}",
                    MODALIDAD_PAGO.get(fila["ModalidadPago"], "N/D"),
                    ESTADOS_CONTRATO.get(fila["Estado"], "N/D"),
                )
            )

    def abrir_nuevo(self):
        ContractForm(self, self.user_data, self.cargar_contratos)

    def _obtener_id_seleccionado(self):
        seleccionado = self.tree.selection()
        if not seleccionado:
            messagebox.showwarning("Aviso", "Selecciona un contrato.")
            return None

        valores = self.tree.item(seleccionado[0], "values")
        return int(valores[0])

    def editar_seleccionado(self):
        contrato_id = self._obtener_id_seleccionado()
        if contrato_id is None:
            return

        contrato = obtener_contrato_por_id(contrato_id)
        if not contrato:
            messagebox.showerror("Error", "No se encontró el contrato.")
            return

        ContractForm(self, self.user_data, self.cargar_contratos, contrato=contrato)

    def cambiar_estado_seleccionado(self, nuevo_estado):
        contrato_id = self._obtener_id_seleccionado()
        if contrato_id is None:
            return

        nombre_estado = ESTADOS_CONTRATO.get(nuevo_estado, "desconocido")
        ok = messagebox.askyesno(
            "Confirmar",
            f"¿Deseas cambiar el estado del contrato a '{nombre_estado}'?"
        )
        if not ok:
            return

        try:
            usr = self.user_data.get("id", 0)
            cambiar_estado_contrato(contrato_id, nuevo_estado, usr=usr)
            self.cargar_contratos()
            messagebox.showinfo("Éxito", "Estado actualizado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", str(e))