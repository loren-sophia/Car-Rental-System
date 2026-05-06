import tkinter as tk
from tkinter import ttk
from database.report_queries import get_vehicles_by_status, get_rentals_by_month, get_top_customers


class ReportsView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#eef1f6")
        self.style = ttk.Style()
        self.configure_styles()
        self.build()

    def configure_styles(self):
        # Tema base
        self.style.theme_use("clam")

        # Notebook
        self.style.configure("TNotebook", background="#eef1f6", borderwidth=0)
        self.style.configure("TNotebook.Tab",
                             font=("Segoe UI", 10, "bold"),
                             padding=[12, 6])

        # Treeview (tabla)
        self.style.configure("Treeview",
                             font=("Segoe UI", 10),
                             rowheight=28,
                             background="white",
                             fieldbackground="white",
                             bordercolor="#d9d9d9")

        self.style.configure("Treeview.Heading",
                             font=("Segoe UI", 10, "bold"),
                             background="#4a90d9",
                             foreground="white")

        # Botón moderno
        self.style.configure("Primary.TButton",
                             font=("Segoe UI", 10, "bold"),
                             foreground="white",
                             background="#4a90d9",
                             padding=6)

    def build(self):
        # Header
        header = tk.Frame(self, bg="#eef1f6")
        header.pack(fill="x", pady=(15, 5), padx=20)

        tk.Label(header, text="📊 Reports Dashboard",
                 font=("Segoe UI", 20, "bold"),
                 bg="#eef1f6", fg="#1a1a2e").pack(side="left")

        ttk.Button(header, text="⟳ Refresh",
                   style="Primary.TButton",
                   command=self.refresh).pack(side="right")

        # Notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=10)

        self.tab_status = tk.Frame(self.notebook, bg="#eef1f6")
        self.tab_monthly = tk.Frame(self.notebook, bg="#eef1f6")
        self.tab_customers = tk.Frame(self.notebook, bg="#eef1f6")

        self.notebook.add(self.tab_status, text="Fleet Status")
        self.notebook.add(self.tab_monthly, text="Monthly Revenue")
        self.notebook.add(self.tab_customers, text="Top Customers")

        self.refresh()

    def create_card(self, parent):
        """Contenedor tipo tarjeta"""
        frame = tk.Frame(parent, bg="white", bd=0, highlightthickness=1,
                         highlightbackground="#dcdcdc")
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        return frame

    def create_table(self, parent, columns):
        tree = ttk.Treeview(parent, columns=columns, show="headings")

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=150)

        tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Scrollbar
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        return tree

    def refresh(self):
        self._build_status_tab()
        self._build_monthly_tab()
        self._build_customers_tab()

    # ── Tab 1 ─────────────────────────────────────────────

    def _build_status_tab(self):
        for w in self.tab_status.winfo_children():
            w.destroy()

        card = self.create_card(self.tab_status)

        tk.Label(card, text="Fleet Status Overview",
                 font=("Segoe UI", 14, "bold"),
                 bg="white").pack(anchor="w", padx=10, pady=(10, 0))

        cols = ("Status", "Count")
        tree = self.create_table(card, cols)

        STATUS_COLORS = {
            "available": "#27ae60",
            "rented": "#e67e22",
            "reserved": "#8e44ad",
            "maintenance": "#e74c3c",
        }

        for row in get_vehicles_by_status():
            tag = row["status"]
            tree.insert("", "end",
                        values=(row["status"].capitalize(), row["count"]),
                        tags=(tag,))
            tree.tag_configure(tag, foreground=STATUS_COLORS.get(tag, "#333"))

    # ── Tab 2 ─────────────────────────────────────────────

    def _build_monthly_tab(self):
        for w in self.tab_monthly.winfo_children():
            w.destroy()

        card = self.create_card(self.tab_monthly)

        tk.Label(card, text="Monthly Revenue Report",
                 font=("Segoe UI", 14, "bold"),
                 bg="white").pack(anchor="w", padx=10, pady=(10, 0))

        cols = ("Month", "Total Rentals", "Revenue")
        tree = self.create_table(card, cols)

        for row in get_rentals_by_month():
            tree.insert("", "end", values=(
                row["month"],
                row["total_rentals"],
                f"${row['revenue']:,.2f}"
            ))

    # ── Tab 3 ─────────────────────────────────────────────

    def _build_customers_tab(self):
        for w in self.tab_customers.winfo_children():
            w.destroy()

        card = self.create_card(self.tab_customers)

        tk.Label(card, text="Top Customers",
                 font=("Segoe UI", 14, "bold"),
                 bg="white").pack(anchor="w", padx=10, pady=(10, 0))

        cols = ("Customer", "Total Rentals", "Total Spent")
        tree = self.create_table(card, cols)

        for row in get_top_customers():
            tree.insert("", "end", values=(
                row["full_name"],
                row["total_rentals"],
                f"${row['total_spent']:,.2f}"
            ))