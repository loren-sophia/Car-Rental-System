import tkinter as tk
from tkinter import ttk, messagebox
from database.vehicle_queries import (
    get_all_vehicles, add_vehicle, update_vehicle,
    delete_vehicle, get_vehicle_by_id
)
from utils.validators import validate_not_empty, validate_year, validate_rate

TYPES = ["Sedan", "SUV", "Pickup", "Van", "Convertible", "Hatchback"]
STATUSES = ["available", "reserved", "rented", "maintenance"]
COLUMNS = ("ID", "Brand", "Model", "Year", "Type", "Rate/Day", "Status")


class VehiclesView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f0f2f5")
        self.selected_id = None
        self.build()

    # ── Layout ────────────────────────────────────────────────────────────────

    def build(self):
        tk.Label(self, text="🚗 Vehicles", font=("Helvetica", 18, "bold"),
                 bg="#f0f2f5", fg="#1a1a2e").pack(pady=(16, 6))

        # Filter bar
        filter_frame = tk.Frame(self, bg="#f0f2f5")
        filter_frame.pack(fill="x", padx=20, pady=4)

        tk.Label(filter_frame, text="Brand:", bg="#f0f2f5").pack(side="left")
        self.search_brand = tk.Entry(filter_frame, width=14)
        self.search_brand.pack(side="left", padx=4)

        tk.Label(filter_frame, text="Type:", bg="#f0f2f5").pack(side="left")
        self.filter_type = ttk.Combobox(filter_frame, values=["All"] + TYPES, width=12, state="readonly")
        self.filter_type.set("All")
        self.filter_type.pack(side="left", padx=4)

        tk.Label(filter_frame, text="Status:", bg="#f0f2f5").pack(side="left")
        self.filter_status = ttk.Combobox(filter_frame, values=["All"] + STATUSES, width=12, state="readonly")
        self.filter_status.set("All")
        self.filter_status.pack(side="left", padx=4)

        tk.Button(filter_frame, text="Search", command=self.load_vehicles,
                  bg="#4a90d9", fg="white", relief="flat", padx=8).pack(side="left", padx=6)
        tk.Button(filter_frame, text="Clear", command=self.clear_filters,
                  bg="#aaa", fg="white", relief="flat", padx=8).pack(side="left")

        # Treeview
        tree_frame = tk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=6)

        self.tree = ttk.Treeview(tree_frame, columns=COLUMNS, show="headings", height=14)
        for col in COLUMNS:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")
        self.tree.column("ID", width=40)
        self.tree.column("Brand", width=110)
        self.tree.column("Model", width=110)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # Action buttons
        btn_frame = tk.Frame(self, bg="#f0f2f5")
        btn_frame.pack(pady=6)
        for label, cmd, color in [
            ("➕ Add", self.open_add_form, "#27ae60"),
            ("✏️ Edit", self.open_edit_form, "#e67e22"),
            ("🗑 Delete", self.delete_vehicle, "#e74c3c"),
        ]:
            tk.Button(btn_frame, text=label, command=cmd, bg=color, fg="white",
                      font=("Helvetica", 10), relief="flat", padx=12, pady=6,
                      cursor="hand2").pack(side="left", padx=6)

        self.load_vehicles()

    def clear_filters(self):
        self.search_brand.delete(0, tk.END)
        self.filter_type.set("All")
        self.filter_status.set("All")
        self.load_vehicles()

    def load_vehicles(self):
        self.tree.delete(*self.tree.get_children())
        filters = {}
        if self.search_brand.get().strip():
            filters["brand"] = self.search_brand.get().strip()
        if self.filter_type.get() != "All":
            filters["vehicle_type"] = self.filter_type.get()
        if self.filter_status.get() != "All":
            filters["status"] = self.filter_status.get()
        for v in get_all_vehicles(filters or None):
            tag = v["status"]
            self.tree.insert("", "end", values=(
                v["id"], v["brand"], v["model"], v["year"],
                v["vehicle_type"], f"${v['rate_per_day']:.2f}", v["status"]
            ), tags=(tag,))
        self.tree.tag_configure("available", foreground="#27ae60")
        self.tree.tag_configure("rented", foreground="#e67e22")
        self.tree.tag_configure("reserved", foreground="#8e44ad")
        self.tree.tag_configure("maintenance", foreground="#e74c3c")
        self.selected_id = None

    def on_select(self, event):
        sel = self.tree.selection()
        if sel:
            self.selected_id = self.tree.item(sel[0])["values"][0]

    def delete_vehicle(self):
        if not self.selected_id:
            messagebox.showwarning("No selection", "Please select a vehicle first.")
            return
        if messagebox.askyesno("Confirm", "Delete this vehicle?"):
            ok, msg = delete_vehicle(self.selected_id)
            if ok:
                messagebox.showinfo("Success", msg)
                self.load_vehicles()
            else:
                messagebox.showerror("Error", msg)

    def open_add_form(self):
        VehicleForm(self, title="Add Vehicle", on_save=self.load_vehicles)

    def open_edit_form(self):
        if not self.selected_id:
            messagebox.showwarning("No selection", "Please select a vehicle first.")
            return
        vehicle = get_vehicle_by_id(self.selected_id)
        VehicleForm(self, title="Edit Vehicle", vehicle=vehicle, on_save=self.load_vehicles)


# ── Form Modal ────────────────────────────────────────────────────────────────

class VehicleForm(tk.Toplevel):
    def __init__(self, parent, title, on_save, vehicle=None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.on_save = on_save
        self.vehicle = vehicle
        self.configure(bg="#f0f2f5")
        self.build()
        self.grab_set()

    def build(self):
        fields_frame = tk.Frame(self, bg="#f0f2f5", padx=24, pady=16)
        fields_frame.pack()

        labels = ["Brand", "Model", "Year", "Type", "Rate per Day", "Status"]
        self.entries = {}

        for i, label in enumerate(labels):
            tk.Label(fields_frame, text=label + ":", bg="#f0f2f5",
                     font=("Helvetica", 10)).grid(row=i, column=0, sticky="w", pady=4)
            if label == "Type":
                w = ttk.Combobox(fields_frame, values=TYPES, state="readonly", width=20)
                w.set(TYPES[0])
            elif label == "Status":
                w = ttk.Combobox(fields_frame, values=STATUSES, state="readonly", width=20)
                w.set("available")
            else:
                w = tk.Entry(fields_frame, width=22)
            w.grid(row=i, column=1, pady=4, padx=8)
            self.entries[label] = w

        if self.vehicle:
            self.entries["Brand"].insert(0, self.vehicle["brand"])
            self.entries["Model"].insert(0, self.vehicle["model"])
            self.entries["Year"].insert(0, self.vehicle["year"])
            self.entries["Type"].set(self.vehicle["vehicle_type"])
            self.entries["Rate per Day"].insert(0, self.vehicle["rate_per_day"])
            self.entries["Status"].set(self.vehicle["status"])

        tk.Button(fields_frame, text="💾 Save", command=self.save,
                  bg="#27ae60", fg="white", relief="flat", padx=12, pady=6,
                  cursor="hand2").grid(row=len(labels), column=0, columnspan=2, pady=12)

    def save(self):
        brand = self.entries["Brand"].get().strip()
        model = self.entries["Model"].get().strip()
        year_str = self.entries["Year"].get().strip()
        vtype = self.entries["Type"].get()
        rate_str = self.entries["Rate per Day"].get().strip()
        status = self.entries["Status"].get()

        ok, msg = validate_not_empty(("Brand", brand), ("Model", model))
        if not ok:
            messagebox.showerror("Validation", msg, parent=self); return

        ok, year = validate_year(year_str)
        if not ok:
            messagebox.showerror("Validation", msg, parent=self); return

        ok, rate = validate_rate(rate_str)
        if not ok:
            messagebox.showerror("Validation", rate, parent=self); return

        if self.vehicle:
            result, msg2 = update_vehicle(self.vehicle["id"], brand, model, year, vtype, rate, status)
        else:
            result, msg2 = add_vehicle(brand, model, year, vtype, rate, status)

        if result:
            messagebox.showinfo("Success", msg2, parent=self)
            self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Error", msg2, parent=self)
