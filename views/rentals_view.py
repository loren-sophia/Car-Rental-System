import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from database.rental_queries import (
    get_all_rentals, start_rental, complete_rental, calculate_rental_cost
)
from database.customer_queries import get_all_customers
from database.vehicle_queries import get_available_vehicles, get_vehicle_by_id
from utils.date_picker import DatePickerButton

COLUMNS = ("ID", "Cliente", "Vehiculo", "Inicio", "Fin", "Costo Total", "Estado")
STATUSES = ["All", "active", "completed", "late"]

STATUS_LABELS = {
    "All": "Todos", "active": "Activo",
    "completed": "Completado", "late": "Vencido"
}


class RentalsView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f0f2f5")
        self.selected_id = None
        self.build()

    # ── Layout ────────────────────────────────────────────────────────────────

    def build(self):
        tk.Label(self, text="🔑 Rentas", font=("Helvetica", 18, "bold"),
                 bg="#f0f2f5", fg="#1a1a2e").pack(pady=(16, 6))

        # Filter bar
        filter_frame = tk.Frame(self, bg="#f0f2f5")
        filter_frame.pack(fill="x", padx=20, pady=4)
        tk.Label(filter_frame, text="Estado:", bg="#f0f2f5").pack(side="left")
        self.filter_status = ttk.Combobox(
            filter_frame,
            values=[STATUS_LABELS[s] for s in STATUSES],
            state="readonly", width=14
        )
        self.filter_status.set("Todos")
        self.filter_status.pack(side="left", padx=6)
        tk.Button(filter_frame, text="Filtrar", command=self.load_rentals,
                  bg="#4a90d9", fg="white", relief="flat", padx=8).pack(side="left")

        # Treeview
        tree_frame = tk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=6)

        self.tree = ttk.Treeview(tree_frame, columns=COLUMNS, show="headings", height=14)
        for col in COLUMNS:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=110, anchor="center")
        self.tree.column("ID", width=40)
        self.tree.column("Cliente", width=150)
        self.tree.column("Vehiculo", width=160)

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # Action buttons
        btn_frame = tk.Frame(self, bg="#f0f2f5")
        btn_frame.pack(pady=6)
        tk.Button(btn_frame, text="➕ Nueva Renta", command=self.open_form,
                  bg="#27ae60", fg="white", font=("Helvetica", 10),
                  relief="flat", padx=12, pady=6, cursor="hand2").pack(side="left", padx=6)
        tk.Button(btn_frame, text="✅ Completar Renta", command=self.complete,
                  bg="#2980b9", fg="white", font=("Helvetica", 10),
                  relief="flat", padx=12, pady=6, cursor="hand2").pack(side="left", padx=6)

        self.load_rentals()

    def load_rentals(self):
        self.tree.delete(*self.tree.get_children())
        # Map display label back to key
        reverse = {v: k for k, v in STATUS_LABELS.items()}
        key = reverse.get(self.filter_status.get(), "All")
        filters = {} if key == "All" else {"status": key}
        for r in get_all_rentals(filters or None):
            cost = f"${r['total_cost']:.2f}" if r["total_cost"] else "—"
            tag  = r["rental_status"]
            self.tree.insert("", "end", values=(
                r["id"], r["customer_name"], r["vehicle"],
                r["start_date"], r["end_date"], cost, r["rental_status"]
            ), tags=(tag,))
        self.tree.tag_configure("active",    foreground="#27ae60")
        self.tree.tag_configure("late",      foreground="#e74c3c")
        self.tree.tag_configure("completed", foreground="#aaaaaa")
        self.selected_id = None

    def on_select(self, event):
        sel = self.tree.selection()
        if sel:
            self.selected_id = self.tree.item(sel[0])["values"][0]

    def complete(self):
        if not self.selected_id:
            messagebox.showwarning("Sin seleccion", "Selecciona una renta primero.")
            return
        if messagebox.askyesno("Confirmar", "¿Marcar esta renta como completada?"):
            ok, msg = complete_rental(self.selected_id)
            if ok:
                messagebox.showinfo("Exito", msg)
                self.load_rentals()
            else:
                messagebox.showerror("Error", msg)

    def open_form(self):
        RentalForm(self, on_save=self.load_rentals)


# ── New Rental Form ───────────────────────────────────────────────────────────

class RentalForm(tk.Toplevel):
    """
    Guided rental form:
      1. Select customer + vehicle + dates
      2. Click "Calcular Costo"  → shows breakdown, enables Confirm
      3. Click "Confirmar Renta" → creates the rental
    """

    def __init__(self, parent, on_save):
        super().__init__(parent)
        self.title("Nueva Renta")
        self.resizable(False, False)
        self.configure(bg="#f0f2f5")
        self.on_save = on_save

        self.customers = get_all_customers()
        self.vehicles  = get_available_vehicles()
        self._cost_calculated = False
        self._days  = 0
        self._total = 0.0

        self._build()
        self.grab_set()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self):
        # ── Title bar ─────────────────────────────────────────────────────────
        tk.Label(self, text="🔑 Nueva Renta",
                 font=("Helvetica", 15, "bold"),
                 bg="#1a1a2e", fg="white",
                 padx=16, pady=10).pack(fill="x")

        body = tk.Frame(self, bg="#f0f2f5", padx=24, pady=16)
        body.pack()

        # ── Row helper ────────────────────────────────────────────────────────
        def row(label, widget, r):
            tk.Label(body, text=label, bg="#f0f2f5",
                     font=("Helvetica", 10), anchor="w",
                     width=22).grid(row=r, column=0, sticky="w", pady=5)
            widget.grid(row=r, column=1, sticky="w", pady=5, padx=4)

        # Customer
        self.customer_var = tk.StringVar()
        names = [f"{c['id']} — {c['full_name']}" for c in self.customers]
        self.customer_cb = ttk.Combobox(body, values=names,
                                        textvariable=self.customer_var,
                                        state="readonly", width=30)
        row("Cliente *", self.customer_cb, 0)
        self.customer_cb.bind("<<ComboboxSelected>>", self._on_field_change)

        # Vehicle
        self.vehicle_var = tk.StringVar()
        vnames = [f"{v['id']} — {v['brand']} {v['model']}  (${v['rate_per_day']:.2f}/día)"
                  for v in self.vehicles]
        self.vehicle_cb = ttk.Combobox(body, values=vnames,
                                       textvariable=self.vehicle_var,
                                       state="readonly", width=30)
        row("Vehículo *", self.vehicle_cb, 1)
        self.vehicle_cb.bind("<<ComboboxSelected>>", self._on_field_change)

        # Dates
        today = date.today().isoformat()
        self.start_picker = DatePickerButton(body, initial_date=today,
                                             on_change=self._on_date_change)
        row("Fecha de Inicio *", self.start_picker, 2)

        self.end_picker = DatePickerButton(body, initial_date=today,
                                           on_change=self._on_date_change)
        row("Fecha de Fin *", self.end_picker, 3)

        # ── Divider ───────────────────────────────────────────────────────────
        ttk.Separator(body, orient="horizontal").grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=10)

        # ── Cost breakdown panel ──────────────────────────────────────────────
        cost_panel = tk.Frame(body, bg="#eaf4ff", relief="solid", bd=1,
                              padx=12, pady=10)
        cost_panel.grid(row=5, column=0, columnspan=2, sticky="ew", pady=4)

        tk.Label(cost_panel, text="Desglose del Costo",
                 font=("Helvetica", 10, "bold"),
                 bg="#eaf4ff", fg="#1a1a2e").pack(anchor="w")

        self.cost_detail = tk.Label(cost_panel, text="— Selecciona vehículo y fechas —",
                                    font=("Helvetica", 10), bg="#eaf4ff", fg="#555555")
        self.cost_detail.pack(anchor="w", pady=2)

        self.total_label = tk.Label(cost_panel, text="",
                                    font=("Helvetica", 13, "bold"),
                                    bg="#eaf4ff", fg="#27ae60")
        self.total_label.pack(anchor="w")

        self.conversion_label = tk.Label(cost_panel, text="",
                                         font=("Helvetica", 9, "italic"),
                                         bg="#eaf4ff", fg="#8e44ad")
        self.conversion_label.pack(anchor="w")

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_row = tk.Frame(body, bg="#f0f2f5")
        btn_row.grid(row=6, column=0, columnspan=2, pady=14)

        self.calc_btn = tk.Button(
            btn_row, text="🧮 Calcular Costo",
            font=("Helvetica", 10, "bold"),
            bg="#e67e22", fg="white", relief="flat",
            padx=14, pady=7, cursor="hand2",
            command=self._calculate
        )
        self.calc_btn.pack(side="left", padx=6)

        self.confirm_btn = tk.Button(
            btn_row, text="✅ Confirmar Renta",
            font=("Helvetica", 10, "bold"),
            bg="#27ae60", fg="white", relief="flat",
            padx=14, pady=7, cursor="hand2",
            state="disabled",
            command=self._confirm
        )
        self.confirm_btn.pack(side="left", padx=6)

        tk.Button(btn_row, text="Cancelar",
                  font=("Helvetica", 10),
                  bg="#aaaaaa", fg="white", relief="flat",
                  padx=10, pady=7, cursor="hand2",
                  command=self.destroy).pack(side="left", padx=6)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_field_change(self, event=None):
        """Reset cost state when any field changes."""
        self._reset_cost()

    def _on_date_change(self, date_str):
        """Called by DatePickerButton on_change."""
        self._reset_cost()

    def _reset_cost(self):
        self._cost_calculated = False
        self.confirm_btn.config(state="disabled")
        self.cost_detail.config(text="— Selecciona vehículo y fechas —", fg="#555555")
        self.total_label.config(text="")
        self.conversion_label.config(text="")

    def _get_vehicle_id(self):
        txt = self.vehicle_var.get()
        if not txt:
            return None, None
        vid = int(txt.split("—")[0].strip())
        v = get_vehicle_by_id(vid)
        return vid, v

    def _calculate(self):
        """Validate inputs, calculate cost, show breakdown, enable Confirm."""
        if not self.customer_var.get():
            messagebox.showerror("Validación", "Selecciona un cliente.", parent=self)
            return
        vid, vehicle = self._get_vehicle_id()
        if not vid:
            messagebox.showerror("Validación", "Selecciona un vehículo.", parent=self)
            return

        start = self.start_picker.get()
        end   = self.end_picker.get()

        ok, days, total, msg = calculate_rental_cost(vid, start, end)
        if not ok:
            self.cost_detail.config(text=f"⚠ {msg}", fg="#e74c3c")
            self.total_label.config(text="")
            return

        # Check for matching reservation to preview conversion
        from database.rental_queries import check_vehicle_conflict
        from database.db import get_connection
        conn = get_connection()
        res_row = conn.execute("""
            SELECT id, customer_id FROM reservations
            WHERE vehicle_id = ?
              AND status = 'pending'
              AND NOT (end_date < ? OR start_date > ?)
            LIMIT 1
        """, (vid, start, end)).fetchone()
        conn.close()

        self._cost_calculated = True
        self._days  = days
        self._total = total

        self.cost_detail.config(
            text=f"{days} día(s)  ×  ${vehicle['rate_per_day']:.2f} / día",
            fg="#333333"
        )
        self.total_label.config(text=f"Total:  ${total:.2f}")

        if res_row:
            self.conversion_label.config(
                text=f"⚡ Se convertirá automáticamente la Reserva #{res_row['id']}"
            )
        else:
            self.conversion_label.config(text="")

        self.confirm_btn.config(state="normal")

    def _confirm(self):
        if not self._cost_calculated:
            return

        vid, vehicle = self._get_vehicle_id()
        customer_id  = int(self.customer_var.get().split("—")[0].strip())
        start = self.start_picker.get()
        end   = self.end_picker.get()

        ok, msg, converted = start_rental(
            customer_id, vid, start, end, vehicle["rate_per_day"]
        )

        if ok:
            messagebox.showinfo("Éxito", msg, parent=self)
            self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Error", msg, parent=self)
