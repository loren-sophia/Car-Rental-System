import tkinter as tk
from tkinter import ttk, messagebox
from database.customer_queries import (
    get_all_customers, add_customer, update_customer,
    delete_customer, get_customer_by_id
)
from utils.validators import validate_not_empty, validate_email

COLUMNS = ("ID", "Full Name", "Phone", "Email", "License Number")


class CustomersView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f0f2f5")
        self.selected_id = None
        self.build()

    def build(self):
        tk.Label(self, text="👥 Customers", font=("Helvetica", 18, "bold"),
                 bg="#f0f2f5", fg="#1a1a2e").pack(pady=(16, 6))

        # Search bar
        search_frame = tk.Frame(self, bg="#f0f2f5")
        search_frame.pack(fill="x", padx=20, pady=4)
        tk.Label(search_frame, text="Search:", bg="#f0f2f5").pack(side="left")
        self.search_var = tk.Entry(search_frame, width=28)
        self.search_var.pack(side="left", padx=6)
        tk.Button(search_frame, text="Search", command=self.load_customers,
                  bg="#4a90d9", fg="white", relief="flat", padx=8).pack(side="left")
        tk.Button(search_frame, text="Clear", command=self.clear_search,
                  bg="#aaa", fg="white", relief="flat", padx=8).pack(side="left", padx=4)

        # Treeview
        tree_frame = tk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=6)

        self.tree = ttk.Treeview(tree_frame, columns=COLUMNS, show="headings", height=15)
        for col in COLUMNS:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=130, anchor="center")
        self.tree.column("ID", width=40)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # Buttons
        btn_frame = tk.Frame(self, bg="#f0f2f5")
        btn_frame.pack(pady=6)
        for label, cmd, color in [
            ("➕ Add", self.open_add_form, "#27ae60"),
            ("✏️ Edit", self.open_edit_form, "#e67e22"),
            ("🗑 Delete", self.delete_customer, "#e74c3c"),
        ]:
            tk.Button(btn_frame, text=label, command=cmd, bg=color, fg="white",
                      font=("Helvetica", 10), relief="flat", padx=12, pady=6,
                      cursor="hand2").pack(side="left", padx=6)

        self.load_customers()

    def clear_search(self):
        self.search_var.delete(0, tk.END)
        self.load_customers()

    def load_customers(self):
        self.tree.delete(*self.tree.get_children())
        search = self.search_var.get().strip() or None
        for c in get_all_customers(search):
            self.tree.insert("", "end", values=(
                c["id"], c["full_name"], c["phone"], c["email"] or "", c["license_number"]
            ))
        self.selected_id = None

    def on_select(self, event):
        sel = self.tree.selection()
        if sel:
            self.selected_id = self.tree.item(sel[0])["values"][0]

    def delete_customer(self):
        if not self.selected_id:
            messagebox.showwarning("No selection", "Please select a customer first.")
            return
        if messagebox.askyesno("Confirm", "Delete this customer?"):
            ok, msg = delete_customer(self.selected_id)
            if ok:
                messagebox.showinfo("Success", msg)
                self.load_customers()
            else:
                messagebox.showerror("Error", msg)

    def open_add_form(self):
        CustomerForm(self, title="Add Customer", on_save=self.load_customers)

    def open_edit_form(self):
        if not self.selected_id:
            messagebox.showwarning("No selection", "Please select a customer.")
            return
        customer = get_customer_by_id(self.selected_id)
        CustomerForm(self, title="Edit Customer", customer=customer, on_save=self.load_customers)


class CustomerForm(tk.Toplevel):
    def __init__(self, parent, title, on_save, customer=None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.on_save = on_save
        self.customer = customer
        self.configure(bg="#f0f2f5")
        self.build()
        self.grab_set()

    def build(self):
        frame = tk.Frame(self, bg="#f0f2f5", padx=24, pady=16)
        frame.pack()
        labels = ["Full Name", "Phone", "Email (optional)", "License Number"]
        self.entries = {}
        for i, label in enumerate(labels):
            tk.Label(frame, text=label + ":", bg="#f0f2f5").grid(row=i, column=0, sticky="w", pady=4)
            e = tk.Entry(frame, width=26)
            e.grid(row=i, column=1, pady=4, padx=8)
            self.entries[label] = e

        if self.customer:
            self.entries["Full Name"].insert(0, self.customer["full_name"])
            self.entries["Phone"].insert(0, self.customer["phone"])
            self.entries["Email (optional)"].insert(0, self.customer["email"] or "")
            self.entries["License Number"].insert(0, self.customer["license_number"])

        tk.Button(frame, text="💾 Save", command=self.save,
                  bg="#27ae60", fg="white", relief="flat", padx=12, pady=6,
                  cursor="hand2").grid(row=len(labels), column=0, columnspan=2, pady=12)

    def save(self):
        full_name = self.entries["Full Name"].get().strip()
        phone = self.entries["Phone"].get().strip()
        email = self.entries["Email (optional)"].get().strip()
        license_number = self.entries["License Number"].get().strip()

        ok, msg = validate_not_empty(("Full Name", full_name), ("Phone", phone), ("License Number", license_number))
        if not ok:
            messagebox.showerror("Validation", msg, parent=self); return

        ok, msg = validate_email(email)
        if not ok:
            messagebox.showerror("Validation", msg, parent=self); return

        if self.customer:
            result, msg2 = update_customer(self.customer["id"], full_name, phone, email, license_number)
        else:
            result, msg2 = add_customer(full_name, phone, email, license_number)

        if result:
            messagebox.showinfo("Success", msg2, parent=self)
            self.on_save()
            self.destroy()
        else:
            messagebox.showerror("Error", msg2, parent=self)
