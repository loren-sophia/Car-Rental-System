import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from database.rental_queries import (
    get_all_rentals, start_rental, complete_rental, calculate_rental_cost
)
from database.customer_queries import get_all_customers
from database.vehicle_queries import get_available_vehicles, get_vehicle_by_id
from utils.date_picker import DatePickerButton

COLUMNS = ("ID", "Customer", "Vehicle", "Start", "End", "Total Cost", "Status")
STATUSES = ["All", "active", "completed", "late"]

STATUS_LABELS = {
    "All": "All",
    "active": "Active",
    "completed": "Completed",
    "late": "Late"
}


class RentalsView(tk.Frame):
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

        ttk.Label(header, text="🔑 Rentals Management",
                  style="Title.TLabel").pack(side="left")

        ttk.Button(header, text="Refresh",
                   style="Primary.TButton",
                   command=self.load_rentals).pack(side="right")

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
                   command=self.load_rentals).pack(side="left")

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

    # ── Logic ─────────────────────────────────────────────

    def load_rentals(self):
        self.tree.delete(*self.tree.get_children())

        reverse = {v: k for k, v in STATUS_LABELS.items()}
        key = reverse.get(self.filter_status.get(), "All")
        filters = {} if key == "All" else {"status": key}

        for r in get_all_rentals(filters or None):
            cost = f"${r['total_cost']:.2f}" if r["total_cost"] else "—"
            tag = r["rental_status"]

            self.tree.insert("", "end", values=(
                r["id"], r["customer_name"], r["vehicle"],
                r["start_date"], r["end_date"], cost, r["rental_status"]
            ), tags=(tag,))

        self.tree.tag_configure("active", foreground="#2e7d32")
        self.tree.tag_configure("late", foreground="#c62828")
        self.tree.tag_configure("completed", foreground="#757575")

        self.selected_id = None

    def on_select(self, event):
        sel = self.tree.selection()
        if sel:
            self.selected_id = self.tree.item(sel[0])["values"][0]

    def complete(self):
        if not self.selected_id:
            messagebox.showwarning("No Selection", "Select a rental first.")
            return

        if messagebox.askyesno("Confirm", "Mark this rental as completed?"):
            ok, msg = complete_rental(self.selected_id)

            if ok:
                messagebox.showinfo("Success", msg)
                self.load_rentals()
            else:
                messagebox.showerror("Error", msg)

    def open_form(self):
        RentalForm(self, on_save=self.load_rentals)


# ── FORM ─────────────────────────────────────────────

class RentalForm(tk.Toplevel):
    def __init__(self, parent, on_save):
        super().__init__(parent)

        self.title("New Rental")
        self.resizable(False, False)
        self.configure(bg="#eef1f6")

        self.on_save = on_save

        self.customers = get_all_customers()
        self.vehicles = get_available_vehicles()

        self._cost_calculated = False

        self._build()
        self.grab_set()

    def _build(self):
        tk.Label(self, text="🔑 New Rental",
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

        # Cost panel
        cost_panel = tk.Frame(body, bg="white", bd=1, relief="solid", padx=10, pady=10)
        cost_panel.grid(row=4, column=0, columnspan=2, pady=10)

        self.total_label = tk.Label(cost_panel,
                                   font=("Segoe UI", 14, "bold"),
                                   fg="#2e7d32",
                                   bg="white")
        self.total_label.pack()

        # Buttons
        btns = tk.Frame(body, bg="#eef1f6")
        btns.grid(row=5, column=0, columnspan=2, pady=10)

        ttk.Button(btns, text="Calculate",
                   command=self._calculate).pack(side="left", padx=6)

        ttk.Button(btns, text="Confirm",
                   command=self._confirm).pack(side="left", padx=6)

    def _get_vehicle_id(self):
        txt = self.vehicle_var.get()
        if not txt:
            return None
        return int(txt.split("—")[0].strip())

    def _calculate(self):
        vid = self._get_vehicle_id()
        if not vid:
            return

        start = self.start_picker.get()
        end = self.end_picker.get()

        ok, days, total, _ = calculate_rental_cost(vid, start, end)

        if ok:
            self.total_label.config(text=f"Total: ${total:.2f}")
            self._cost_calculated = True

    def _confirm(self):
        if not self._cost_calculated:
            return

        vid = self._get_vehicle_id()
        customer_id = int(self.customer_var.get().split("—")[0].strip())

        start = self.start_picker.get()
        end = self.end_picker.get()

        vehicle = get_vehicle_by_id(vid)

        ok, msg, _ = start_rental(
            customer_id, vid, start, end, vehicle["rate_per_day"]
        )

        if ok:
            messagebox.showinfo("Success", msg)
            self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Error", msg)