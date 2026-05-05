import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from database.rental_queries import get_all_reservations, add_reservation, cancel_reservation
from database.customer_queries import get_all_customers
from database.vehicle_queries import get_available_vehicles
from utils.date_picker import DatePickerButton

COLUMNS = ("ID", "Cliente", "Vehículo", "Inicio", "Fin", "Estado")
STATUSES = ["All", "pending", "converted", "completed", "cancelled"]
STATUS_LABELS = {
    "All": "Todos", "pending": "Pendiente", "converted": "Convertida",
    "active": "Activa", "completed": "Completada", "cancelled": "Cancelada"
}
STATUS_COLORS = {
    "pending": "#8e44ad", "converted": "#2980b9",
    "active": "#27ae60", "completed": "#aaaaaa", "cancelled": "#e74c3c"
}


class ReservationsView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f0f2f5")
        self.selected_id = None
        self.build()

    def build(self):
        tk.Label(self, text="📅 Reservaciones", font=("Helvetica", 18, "bold"),
                 bg="#f0f2f5", fg="#1a1a2e").pack(pady=(16, 6))

        # Filter
        filter_frame = tk.Frame(self, bg="#f0f2f5")
        filter_frame.pack(fill="x", padx=20, pady=4)
        tk.Label(filter_frame, text="Estado:", bg="#f0f2f5").pack(side="left")
        self.filter_status = ttk.Combobox(
            filter_frame,
            values=[STATUS_LABELS.get(s, s) for s in STATUSES],
            state="readonly", width=14
        )
        self.filter_status.set("Todos")
        self.filter_status.pack(side="left", padx=6)
        tk.Button(filter_frame, text="Filtrar", command=self.load_reservations,
                  bg="#4a90d9", fg="white", relief="flat", padx=8).pack(side="left")

        # Treeview
        tree_frame = tk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=6)

        self.tree = ttk.Treeview(tree_frame, columns=COLUMNS, show="headings", height=14)
        for col in COLUMNS:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
        self.tree.column("ID", width=40)
        self.tree.column("Cliente", width=160)
        self.tree.column("Vehículo", width=160)

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # Buttons
        btn_frame = tk.Frame(self, bg="#f0f2f5")
        btn_frame.pack(pady=6)
        tk.Button(btn_frame, text="➕ Nueva Reserva", command=self.open_form,
                  bg="#27ae60", fg="white", font=("Helvetica", 10),
                  relief="flat", padx=12, pady=6, cursor="hand2").pack(side="left", padx=6)
        tk.Button(btn_frame, text="❌ Cancelar Reserva", command=self.cancel,
                  bg="#e74c3c", fg="white", font=("Helvetica", 10),
                  relief="flat", padx=12, pady=6, cursor="hand2").pack(side="left", padx=6)

        self.load_reservations()

    def load_reservations(self):
        self.tree.delete(*self.tree.get_children())
        reverse = {v: k for k, v in STATUS_LABELS.items()}
        key = reverse.get(self.filter_status.get(), "All")
        filters = {} if key == "All" else {"status": key}
        for r in get_all_reservations(filters or None):
            tag = r["status"]
            self.tree.insert("", "end", values=(
                r["id"], r["customer_name"], r["vehicle"],
                r["start_date"], r["end_date"], r["status"]
            ), tags=(tag,))
        for status, color in STATUS_COLORS.items():
            self.tree.tag_configure(status, foreground=color)
        self.selected_id = None

    def on_select(self, event):
        sel = self.tree.selection()
        if sel:
            self.selected_id = self.tree.item(sel[0])["values"][0]

    def cancel(self):
        if not self.selected_id:
            messagebox.showwarning("Sin selección", "Selecciona una reserva primero.")
            return
        if messagebox.askyesno("Confirmar", "¿Cancelar esta reserva?"):
            ok, msg = cancel_reservation(self.selected_id)
            if ok:
                messagebox.showinfo("Éxito", msg)
                self.load_reservations()
            else:
                messagebox.showerror("Error", msg)

    def open_form(self):
        ReservationForm(self, on_save=self.load_reservations)


class ReservationForm(tk.Toplevel):
    def __init__(self, parent, on_save):
        super().__init__(parent)
        self.title("Nueva Reservación")
        self.resizable(False, False)
        self.configure(bg="#f0f2f5")
        self.on_save = on_save
        self.customers = get_all_customers()
        self.vehicles  = get_available_vehicles()
        self._build()
        self.grab_set()

    def _build(self):
        tk.Label(self, text="📅 Nueva Reservación",
                 font=("Helvetica", 15, "bold"),
                 bg="#1a1a2e", fg="white",
                 padx=16, pady=10).pack(fill="x")

        body = tk.Frame(self, bg="#f0f2f5", padx=24, pady=16)
        body.pack()

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

        # Vehicle
        self.vehicle_var = tk.StringVar()
        vnames = [f"{v['id']} — {v['brand']} {v['model']}  (${v['rate_per_day']:.2f}/día)"
                  for v in self.vehicles]
        self.vehicle_cb = ttk.Combobox(body, values=vnames,
                                       textvariable=self.vehicle_var,
                                       state="readonly", width=30)
        row("Vehículo *", self.vehicle_cb, 1)

        # Date pickers
        today = date.today().isoformat()
        self.start_picker = DatePickerButton(body, initial_date=today)
        row("Fecha de Inicio *", self.start_picker, 2)

        self.end_picker = DatePickerButton(body, initial_date=today)
        row("Fecha de Fin *", self.end_picker, 3)

        # Info note
        note = tk.Label(body,
                        text="ℹ Al crear una renta, esta reserva\n   se convertirá automáticamente.",
                        font=("Helvetica", 9, "italic"),
                        bg="#fff8e1", fg="#7d6608",
                        relief="solid", bd=1, padx=8, pady=6)
        note.grid(row=4, column=0, columnspan=2, sticky="ew", pady=8)

        # Save button
        tk.Button(body, text="💾 Guardar Reserva", command=self._save,
                  bg="#27ae60", fg="white", font=("Helvetica", 10, "bold"),
                  relief="flat", padx=14, pady=7,
                  cursor="hand2").grid(row=5, column=0, columnspan=2, pady=10)

    def _save(self):
        if not self.customer_var.get() or not self.vehicle_var.get():
            messagebox.showerror("Validación", "Selecciona cliente y vehículo.", parent=self)
            return
        start = self.start_picker.get()
        end   = self.end_picker.get()
        if end <= start:
            messagebox.showerror("Validación",
                                 "La fecha de fin debe ser posterior al inicio.",
                                 parent=self)
            return
        customer_id = int(self.customer_var.get().split("—")[0].strip())
        vehicle_id  = int(self.vehicle_var.get().split("—")[0].strip())
        ok, msg = add_reservation(customer_id, vehicle_id, start, end)
        if ok:
            messagebox.showinfo("Éxito", msg, parent=self)
            self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Error", msg, parent=self)
