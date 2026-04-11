import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from database.db import get_connection


class AuditLogView:
    def __init__(self, parent, user_data):
        self.parent = parent
        self.user_data = user_data

        self.search_entry = None
        self.entry_from = None
        self.entry_to = None
        self.tree = None

    def build(self):
        if self.user_data["rol"] != "admin":
            self.build_access_denied()
            return

        self.build_filters()
        self.build_table()
        self.load_logs()

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
            text="Solo el administrador puede ver la bitácora.",
            font=("Arial", 11),
            bg="white",
            fg="#4b5563"
        ).pack()

    def build_filters(self):
        filters_frame = tk.Frame(self.parent, bg="white")
        filters_frame.pack(fill="x", padx=15, pady=15)

        tk.Label(
            filters_frame,
            text="Buscar:",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#111827"
        ).grid(row=0, column=0, padx=(5, 5), pady=5, sticky="w")

        self.search_entry = tk.Entry(filters_frame, font=("Arial", 10), width=24)
        self.search_entry.grid(row=0, column=1, padx=(0, 12), pady=5, sticky="w")
        self.search_entry.bind("<KeyRelease>", lambda event: self.load_logs())

        tk.Label(
            filters_frame,
            text="Desde (YYYY-MM-DD):",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#111827"
        ).grid(row=0, column=2, padx=(5, 5), pady=5, sticky="w")

        self.entry_from = tk.Entry(filters_frame, font=("Arial", 10), width=14)
        self.entry_from.grid(row=0, column=3, padx=(0, 12), pady=5, sticky="w")

        tk.Label(
            filters_frame,
            text="Hasta (YYYY-MM-DD):",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#111827"
        ).grid(row=0, column=4, padx=(5, 5), pady=5, sticky="w")

        self.entry_to = tk.Entry(filters_frame, font=("Arial", 10), width=14)
        self.entry_to.grid(row=0, column=5, padx=(0, 12), pady=5, sticky="w")

        tk.Button(
            filters_frame,
            text="Buscar",
            font=("Arial", 10, "bold"),
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            bd=0,
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=self.load_logs
        ).grid(row=0, column=6, padx=8, pady=5)

        tk.Button(
            filters_frame,
            text="Limpiar",
            font=("Arial", 10, "bold"),
            bg="#6b7280",
            fg="white",
            activebackground="#4b5563",
            activeforeground="white",
            bd=0,
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=self.clear_filters
        ).grid(row=0, column=7, padx=8, pady=5)

    def build_table(self):
        table_frame = tk.Frame(self.parent, bg="white")
        table_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        columns = (
            "id",
            "usuario",
            "accion",
            "tabla_afectada",
            "registro_id",
            "descripcion",
            "fecha_evento"
        )

        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18)

        self.tree.heading("id", text="ID")
        self.tree.heading("usuario", text="Usuario")
        self.tree.heading("accion", text="Acción")
        self.tree.heading("tabla_afectada", text="Tabla")
        self.tree.heading("registro_id", text="Registro")
        self.tree.heading("descripcion", text="Descripción")
        self.tree.heading("fecha_evento", text="Fecha")

        self.tree.column("id", width=55, anchor="center", stretch=False)
        self.tree.column("usuario", width=150, anchor="w", stretch=False)
        self.tree.column("accion", width=180, anchor="center", stretch=False)
        self.tree.column("tabla_afectada", width=110, anchor="center", stretch=False)
        self.tree.column("registro_id", width=80, anchor="center", stretch=False)
        self.tree.column("descripcion", width=420, anchor="w", stretch=False)
        self.tree.column("fecha_evento", width=160, anchor="center", stretch=False)

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

    def clear_filters(self):
        self.search_entry.delete(0, tk.END)
        self.entry_from.delete(0, tk.END)
        self.entry_to.delete(0, tk.END)
        self.load_logs()

    def validate_date(self, value):
        if not value:
            return True
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def load_logs(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        search_value = self.search_entry.get().strip().upper() if self.search_entry else ""
        date_from = self.entry_from.get().strip() if self.entry_from else ""
        date_to = self.entry_to.get().strip() if self.entry_to else ""

        if not self.validate_date(date_from):
            messagebox.showwarning("Fecha inválida", "La fecha 'Desde' debe estar en formato YYYY-MM-DD.")
            return

        if not self.validate_date(date_to):
            messagebox.showwarning("Fecha inválida", "La fecha 'Hasta' debe estar en formato YYYY-MM-DD.")
            return

        if date_from and date_to and date_from > date_to:
            messagebox.showwarning("Rango inválido", "La fecha 'Desde' no puede ser mayor que la fecha 'Hasta'.")
            return

        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                b.id,
                u.nombre,
                b.accion,
                b.tabla_afectada,
                b.registro_id,
                b.descripcion,
                b.fecha_evento
            FROM bitacora b
            LEFT JOIN usuarios u ON b.usuario_id = u.id
            WHERE 1=1
        """
        params = []

        if search_value:
            query += """
                AND (
                    UPPER(IFNULL(u.nombre, '')) LIKE ?
                    OR UPPER(IFNULL(b.accion, '')) LIKE ?
                    OR UPPER(IFNULL(b.tabla_afectada, '')) LIKE ?
                    OR UPPER(IFNULL(b.descripcion, '')) LIKE ?
                )
            """
            like_value = f"%{search_value}%"
            params.extend([like_value, like_value, like_value, like_value])

        if date_from:
            query += " AND date(b.fecha_evento) >= date(?)"
            params.append(date_from)

        if date_to:
            query += " AND date(b.fecha_evento) <= date(?)"
            params.append(date_to)

        query += " ORDER BY b.fecha_evento DESC, b.id DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    row[0],
                    row[1] if row[1] else "-",
                    row[2] if row[2] else "",
                    row[3] if row[3] else "",
                    row[4] if row[4] is not None else "",
                    row[5] if row[5] else "",
                    row[6] if row[6] else ""
                )
            )