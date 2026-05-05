import tkinter as tk
from tkinter import ttk
from database.report_queries import get_vehicles_by_status, get_rentals_by_month, get_top_customers


class ReportsView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f0f2f5")
        self.build()

    def build(self):
        tk.Label(self, text="📊 Reports", font=("Helvetica", 18, "bold"),
                 bg="#f0f2f5", fg="#1a1a2e").pack(pady=(16, 6))

        tk.Button(self, text="⟳ Refresh", command=self.refresh,
                  bg="#4a90d9", fg="white", font=("Helvetica", 10),
                  relief="flat", padx=10, pady=4, cursor="hand2").pack(pady=(0, 10))

        # Notebook for sub-reports
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=6)

        self.tab_status = tk.Frame(self.notebook, bg="#f0f2f5")
        self.tab_monthly = tk.Frame(self.notebook, bg="#f0f2f5")
        self.tab_customers = tk.Frame(self.notebook, bg="#f0f2f5")

        self.notebook.add(self.tab_status, text="Vehicles by Status")
        self.notebook.add(self.tab_monthly, text="Rentals by Month")
        self.notebook.add(self.tab_customers, text="Top Customers")

        self.refresh()

    def refresh(self):
        self._build_status_tab()
        self._build_monthly_tab()
        self._build_customers_tab()

    # ── Tab 1: Vehicles by Status ─────────────────────────────────────────────

    def _build_status_tab(self):
        for w in self.tab_status.winfo_children():
            w.destroy()

        tk.Label(self.tab_status, text="Fleet Status Summary",
                 font=("Helvetica", 13, "bold"), bg="#f0f2f5").pack(pady=10)

        cols = ("Status", "Count")
        tree = ttk.Treeview(self.tab_status, columns=cols, show="headings", height=8)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=200, anchor="center")
        tree.pack(padx=20, pady=6)

        STATUS_COLORS = {
            "available": "#27ae60",
            "rented": "#e67e22",
            "reserved": "#8e44ad",
            "maintenance": "#e74c3c",
        }
        for row in get_vehicles_by_status():
            tag = row["status"]
            tree.insert("", "end", values=(row["status"].capitalize(), row["count"]), tags=(tag,))
            tree.tag_configure(tag, foreground=STATUS_COLORS.get(row["status"], "#333"))

    # ── Tab 2: Rentals by Month ───────────────────────────────────────────────

    def _build_monthly_tab(self):
        for w in self.tab_monthly.winfo_children():
            w.destroy()

        tk.Label(self.tab_monthly, text="Rental Revenue by Month",
                 font=("Helvetica", 13, "bold"), bg="#f0f2f5").pack(pady=10)

        cols = ("Month", "Total Rentals", "Revenue")
        tree = ttk.Treeview(self.tab_monthly, columns=cols, show="headings", height=12)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=180, anchor="center")
        tree.pack(padx=20, pady=6)

        for row in get_rentals_by_month():
            tree.insert("", "end", values=(
                row["month"],
                row["total_rentals"],
                f"${row['revenue']:,.2f}"
            ))

    # ── Tab 3: Top Customers ──────────────────────────────────────────────────

    def _build_customers_tab(self):
        for w in self.tab_customers.winfo_children():
            w.destroy()

        tk.Label(self.tab_customers, text="Top Customers by Rentals",
                 font=("Helvetica", 13, "bold"), bg="#f0f2f5").pack(pady=10)

        cols = ("Customer", "Total Rentals", "Total Spent")
        tree = ttk.Treeview(self.tab_customers, columns=cols, show="headings", height=12)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=180, anchor="center")
        tree.pack(padx=20, pady=6)

        for row in get_top_customers():
            tree.insert("", "end", values=(
                row["full_name"],
                row["total_rentals"],
                f"${row['total_spent']:,.2f}"
            ))
