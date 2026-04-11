import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

from database.db import get_connection


class ReportsView:
    def __init__(self, parent):
        self.parent = parent

        self.entry_from = None
        self.entry_to = None
        self.entry_plate = None
        self.tree = None
        self.total_label = None

        self.current_rows = []

    def build(self):
        self.build_filters()
        self.build_table()
        self.build_footer()
        self.load_reports()

    def build_filters(self):
        filters_frame = tk.Frame(self.parent, bg="white")
        filters_frame.pack(fill="x", padx=15, pady=15)

        tk.Label(
            filters_frame,
            text="Desde (YYYY-MM-DD):",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#111827"
        ).grid(row=0, column=0, padx=(5, 5), pady=5, sticky="w")

        self.entry_from = tk.Entry(filters_frame, font=("Arial", 10), width=14)
        self.entry_from.grid(row=0, column=1, padx=(0, 12), pady=5, sticky="w")

        tk.Label(
            filters_frame,
            text="Hasta (YYYY-MM-DD):",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#111827"
        ).grid(row=0, column=2, padx=(5, 5), pady=5, sticky="w")

        self.entry_to = tk.Entry(filters_frame, font=("Arial", 10), width=14)
        self.entry_to.grid(row=0, column=3, padx=(0, 12), pady=5, sticky="w")

        tk.Label(
            filters_frame,
            text="Placa:",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#111827"
        ).grid(row=0, column=4, padx=(5, 5), pady=5, sticky="w")

        self.entry_plate = tk.Entry(filters_frame, font=("Arial", 10), width=14)
        self.entry_plate.grid(row=0, column=5, padx=(0, 12), pady=5, sticky="w")
        self.entry_plate.bind("<KeyRelease>", lambda event: self.load_reports())

        search_button = tk.Button(
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
            command=self.load_reports
        )
        search_button.grid(row=0, column=6, padx=8, pady=5)

        clear_button = tk.Button(
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
        )
        clear_button.grid(row=0, column=7, padx=8, pady=5)

        export_button = tk.Button(
            filters_frame,
            text="Exportar Excel",
            font=("Arial", 10, "bold"),
            bg="#16a34a",
            fg="white",
            activebackground="#15803d",
            activeforeground="white",
            bd=0,
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=self.export_excel
        )
        export_button.grid(row=0, column=8, padx=8, pady=5)

    def build_table(self):
        table_frame = tk.Frame(self.parent, bg="white")
        table_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        columns = (
            "id",
            "placa",
            "empleado",
            "servicios",
            "tiempo",
            "fecha_ingreso",
            "fecha_salida",
            "monto_total"
        )

        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18)

        self.tree.heading("id", text="ID")
        self.tree.heading("placa", text="Placa")
        self.tree.heading("empleado", text="Empleado")
        self.tree.heading("servicios", text="Servicios")
        self.tree.heading("tiempo", text="Tiempo")
        self.tree.heading("fecha_ingreso", text="Fecha ingreso")
        self.tree.heading("fecha_salida", text="Fecha salida")
        self.tree.heading("monto_total", text="Monto cobrado")

        self.tree.column("id", width=60, anchor="center", stretch=False)
        self.tree.column("placa", width=110, anchor="center", stretch=False)
        self.tree.column("empleado", width=180, anchor="w", stretch=False)
        self.tree.column("servicios", width=260, anchor="w", stretch=False)
        self.tree.column("tiempo", width=100, anchor="center", stretch=False)
        self.tree.column("fecha_ingreso", width=150, anchor="center", stretch=False)
        self.tree.column("fecha_salida", width=150, anchor="center", stretch=False)
        self.tree.column("monto_total", width=120, anchor="center", stretch=False)

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

    def build_footer(self):
        footer = tk.Frame(self.parent, bg="white")
        footer.pack(fill="x", padx=15, pady=(0, 15))

        self.total_label = tk.Label(
            footer,
            text="Total generado: Bs 0.00",
            font=("Arial", 12, "bold"),
            bg="white",
            fg="#111827"
        )
        self.total_label.pack(side="right")

    def clear_filters(self):
        self.entry_from.delete(0, tk.END)
        self.entry_to.delete(0, tk.END)
        self.entry_plate.delete(0, tk.END)
        self.load_reports()

    def validate_date(self, value):
        if not value:
            return True
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def format_duration(self, minutes):
        minutes = int(minutes or 0)
        horas = minutes // 60
        mins = minutes % 60

        if horas > 0 and mins > 0:
            return f"{horas} h {mins} min"
        if horas > 0:
            return f"{horas} h"
        return f"{mins} min"

    def load_reports(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        date_from = self.entry_from.get().strip()
        date_to = self.entry_to.get().strip()
        plate = self.entry_plate.get().strip().upper()

        if not self.validate_date(date_from):
            messagebox.showwarning("Fecha inválida", "La fecha 'Desde' debe estar en formato YYYY-MM-DD.")
            return

        if not self.validate_date(date_to):
            messagebox.showwarning("Fecha inválida", "La fecha 'Hasta' debe estar en formato YYYY-MM-DD.")
            return

        if date_from and date_to:
            if date_from > date_to:
                messagebox.showwarning("Rango inválido", "La fecha 'Desde' no puede ser mayor que la fecha 'Hasta'.")
                return

        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                o.id,
                v.placa,
                u.nombre,
                o.minutos_estadia,
                o.fecha_ingreso,
                o.fecha_salida,
                o.monto_total
            FROM operaciones o
            INNER JOIN vehiculos v ON o.vehiculo_id = v.id
            LEFT JOIN usuarios u ON o.usuario_salida_id = u.id
            WHERE o.estado = 'finalizado'
        """
        params = []

        if date_from:
            query += " AND date(o.fecha_salida) >= date(?)"
            params.append(date_from)

        if date_to:
            query += " AND date(o.fecha_salida) <= date(?)"
            params.append(date_to)

        if plate:
            query += " AND REPLACE(UPPER(v.placa), ' ', '') LIKE ?"
            params.append(f"%{plate.replace(' ', '')}%")

        query += " ORDER BY o.fecha_salida DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        self.current_rows = []
        total_generated = 0.0

        for row in rows:
            operation_id = row[0]
            placa = row[1] or ""
            empleado = row[2] if row[2] else "-"
            minutos = int(row[3] or 0)
            fecha_ingreso = row[4] or ""
            fecha_salida = row[5] or ""
            monto_total = float(row[6] or 0)

            tiempo = self.format_duration(minutos)
            servicios = self.get_operation_services(cursor, operation_id)

            view_row = (
                operation_id,
                placa,
                empleado,
                servicios,
                tiempo,
                fecha_ingreso,
                fecha_salida,
                f"Bs {monto_total:.2f}"
            )

            self.current_rows.append({
                "id": operation_id,
                "placa": placa,
                "empleado": empleado,
                "servicios": servicios,
                "tiempo": tiempo,
                "minutos": minutos,
                "fecha_ingreso": fecha_ingreso,
                "fecha_salida": fecha_salida,
                "monto_total": monto_total
            })

            self.tree.insert("", "end", values=view_row)
            total_generated += monto_total

        conn.close()

        self.total_label.config(text=f"Total generado: Bs {total_generated:.2f}")

    def get_operation_services(self, cursor, operation_id):
        cursor.execute("""
            SELECT s.nombre
            FROM operacion_servicios os
            INNER JOIN servicios s ON os.servicio_id = s.id
            WHERE os.operacion_id = ? AND os.estado != 'cancelado'
            ORDER BY s.nombre ASC
        """, (operation_id,))
        rows = cursor.fetchall()

        names = [r[0] for r in rows]
        if not names:
            return "Parqueo"
        return "Parqueo, " + ", ".join(names)

    def export_excel(self):
        if not self.current_rows:
            messagebox.showwarning("Sin datos", "No hay datos para exportar.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Guardar reporte",
            defaultextension=".xlsx",
            filetypes=[("Archivos Excel", "*.xlsx")],
            initialfile=f"reporte_garaje_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

        if not file_path:
            return

        try:
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Reportes"

            headers = [
                "ID",
                "Placa",
                "Empleado",
                "Servicios",
                "Tiempo",
                "Fecha ingreso",
                "Fecha salida",
                "Monto cobrado"
            ]
            sheet.append(headers)

            for col in range(1, len(headers) + 1):
                cell = sheet.cell(row=1, column=col)
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center")

            for row in self.current_rows:
                sheet.append([
                    row["id"],
                    row["placa"],
                    row["empleado"],
                    row["servicios"],
                    row["tiempo"],
                    row["fecha_ingreso"],
                    row["fecha_salida"],
                    row["monto_total"]
                ])

            total = sum(row["monto_total"] for row in self.current_rows)
            last_row = sheet.max_row + 2
            sheet.cell(row=last_row, column=7, value="Total generado")
            sheet.cell(row=last_row, column=7).font = Font(bold=True)
            sheet.cell(row=last_row, column=8, value=total)
            sheet.cell(row=last_row, column=8).font = Font(bold=True)

            widths = {
                "A": 10,
                "B": 14,
                "C": 22,
                "D": 35,
                "E": 14,
                "F": 22,
                "G": 22,
                "H": 16
            }

            for col_letter, width in widths.items():
                sheet.column_dimensions[col_letter].width = width

            workbook.save(file_path)

            messagebox.showinfo("Exportación exitosa", "El reporte se exportó correctamente a Excel.")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar el archivo.\n{str(e)}")