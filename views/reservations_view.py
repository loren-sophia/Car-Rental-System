import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from database.rental_queries import get_all_reservations, add_reservation, cancel_reservation
from database.customer_queries import get_all_customers
from database.vehicle_queries import get_available_vehicles
from utils.date_picker import DatePickerButton

COLUMNS = ("ID", "Customer", "Vehicle", "Start", "End", "Status")

STATUSES = ["All", "pending", "converted", "completed", "cancelled"]

STATUS_LABELS = {
    "All": "All",
    "pending": "Pending",
    "converted": "Converted",
    "completed": "Completed",
    "cancelled": "Cancelled"
}

STATUS_COLORS = {
    "pending": "#7b1fa2",
    "converted": "#1565c0",
    "completed": "#757575",
    "cancelled": "#c62828"
}


class ReservationsView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#eef1f6")
        self.selected_id = None

        self.style = ttk.Style()
        self._configure_styles()

        self.build()

    # ── Styles ─────────────────────────────────────────────

    def _configure_styles(self):
        self.style.theme_use("clam")

        self.style.configure("Title.TLabel",
                             font=("Segoe UI", 20, "bold"),
                             background="#eef1f6",
                             foreground="#1a1a2e")

        self.style.configure("Subtitle.TLabel",
                             font=("Segoe UI", 10),
                             background="#eef1f6")

        self.style.configure("Primary.TButton",
                             font=("Segoe UI", 10, "bold"),
                             padding=6)

        self.style.configure("Treeview",
                             font=("Segoe UI", 10),
                             rowheight=30,
                             background="white",
                             fieldbackground="white")

        self.style.configure("Treeview.Heading",
                             font=("Segoe UI", 10, "bold"),
                             background="#4a90d9",
                             foreground="white")

    # ── Layout ─────────────────────────────────────────────

    def build(self):
        # Header
        header = tk.Frame(self, bg="#eef1f6")
        header.pack(fill="x", padx=20, pady=(15, 5))

        ttk.Label(header, text="📅 Reservations Management",
                  style="Title.TLabel").pack(side="left")

        ttk.Button(header, text="Refresh",
                   style="Primary.TButton",
                   command=self.load_reservations).pack(side="right")

        # ── Filter Card ─────────────────────────────
        filter_card = tk.Frame(self, bg="white", bd=1, relief="solid")
        filter_card.pack(fill="x", padx=20, pady=8)

        inner = tk.Frame(filter_card, bg="white")
        inner.pack(padx=10, pady=8, fill="x")

        ttk.Label(inner, text="Filter by status:",
                  style="Subtitle.TLabel").pack(side="left")

        self.filter_status = ttk.Combobox(
            inner,
            values=[STATUS_LABELS[s] for s in STATUSES],
            state="readonly",
            width=15
        )
        self.filter_status.set("All")
        self.filter_status.pack(side="left", padx=8)

        ttk.Button(inner, text="Apply",
                   style="Primary.TButton",
                   command=self.load_reservations).pack(side="left")

        # ── Table Card ─────────────────────────────
        table_card = tk.Frame(self, bg="white", bd=1, relief="solid")
        table_card.pack(fill="both", expand=True, padx=20, pady=10)

        inner = tk.Frame(table_card, bg="white")
        inner.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(inner, columns=COLUMNS, show="headings")

        for col in COLUMNS:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=120)

        self.tree.column("ID", width=50)
        self.tree.column("Customer", width=180)
        self.tree.column("Vehicle", width=200)

        self.tree.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(inner, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scroll.set)
        scroll.pack(side="right", fill="y")

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

    # ── Logic ─────────────────────────────────────────────

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
            messagebox.showwarning("No Selection", "Select a reservation first.")
            return

        if messagebox.askyesno("Confirm", "Cancel this reservation?"):
            ok, msg = cancel_reservation(self.selected_id)

            if ok:
                messagebox.showinfo("Success", msg)
                self.load_reservations()
            else:
                messagebox.showerror("Error", msg)

    def open_form(self):
        ReservationForm(self, on_save=self.load_reservations)


# ── FORM ─────────────────────────────────────────────

class ReservationForm(tk.Toplevel):
    def __init__(self, parent, on_save):
        super().__init__(parent)

        self.title("New Reservation")
        self.resizable(False, False)
        self.configure(bg="#f0f2f5")
        self.on_save = on_save
        self.customers = get_all_customers()
        self.vehicles = get_available_vehicles()

        self._build()
        self.grab_set()

    def _build(self):
        tk.Label(self, text="📅 New Reservation",
                 font=("Segoe UI", 15, "bold"),
                 bg="#1a1a2e", fg="white",
                 padx=16, pady=10).pack(fill="x")

        body = tk.Frame(self, bg="#eef1f6", padx=20, pady=15)
        body.pack()

        def row(label, widget, r):
            tk.Label(body, text=label, bg="#eef1f6",
                     font=("Segoe UI", 10),
                     width=20, anchor="w").grid(row=r, column=0, pady=6)
            widget.grid(row=r, column=1, pady=6)

        # Customer
        self.customer_var = tk.StringVar()
        names = [f"{c['id']} — {c['full_name']}" for c in self.customers]

        self.customer_cb = ttk.Combobox(body, values=names,
                                        textvariable=self.customer_var,
                                        state="readonly", width=30)
        row("Customer *", self.customer_cb, 0)

        # Vehicle
        self.vehicle_var = tk.StringVar()
        vnames = [f"{v['id']} — {v['brand']} {v['model']} (${v['rate_per_day']:.2f}/day)"
                  for v in self.vehicles]

        self.vehicle_cb = ttk.Combobox(body, values=vnames,
                                       textvariable=self.vehicle_var,
                                       state="readonly", width=30)
        row("Vehicle *", self.vehicle_cb, 1)

        # Dates
        today = date.today().isoformat()

        self.start_picker = DatePickerButton(body, initial_date=today)
        row("Start Date *", self.start_picker, 2)

        self.end_picker = DatePickerButton(body, initial_date=today)
        row("End Date *", self.end_picker, 3)

        # Info note
        note = tk.Label(body,
                        text="ℹ This reservation will be automatically converted\n   into a rental when confirmed.",
                        font=("Segoe UI", 9, "italic"),
                        bg="#fff8e1", fg="#7d6608",
                        relief="solid", bd=1, padx=8, pady=6)
        note.grid(row=4, column=0, columnspan=2, sticky="ew", pady=8)

        # Save button
        ttk.Button(body, text="Save Reservation",
                   command=self._save).grid(row=5, column=0, columnspan=2, pady=10)

    def _save(self):
        if not self.customer_var.get() or not self.vehicle_var.get():
            messagebox.showerror("Validation", "Select customer and vehicle.", parent=self)
            return

        start = self.start_picker.get()
        end = self.end_picker.get()

        if end <= start:
            messagebox.showerror("Validation",
                                 "End date must be after start date.",
                                 parent=self)
            return

        customer_id = int(self.customer_var.get().split("—")[0].strip())
        vehicle_id = int(self.vehicle_var.get().split("—")[0].strip())

        ok, msg = add_reservation(customer_id, vehicle_id, start, end)

        if ok:
            messagebox.showinfo("Success", msg, parent=self)
            self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Error", msg, parent=self)