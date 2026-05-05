import tkinter as tk
from tkinter import ttk
from database.report_queries import get_dashboard_stats


class DashboardView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f0f2f5")
        self.build()

    def build(self):
        # Title
        title = tk.Label(self, text="🚗  Car Rental Dashboard", font=("Helvetica", 20, "bold"),
                         bg="#f0f2f5", fg="#1a1a2e")
        title.pack(pady=(20, 10))

        # Refresh button
        btn = tk.Button(self, text="⟳ Refresh", command=self.refresh,
                        bg="#4a90d9", fg="white", font=("Helvetica", 10),
                        relief="flat", padx=10, pady=4, cursor="hand2")
        btn.pack(pady=(0, 16))

        self.cards_frame = tk.Frame(self, bg="#f0f2f5")
        self.cards_frame.pack(fill="both", expand=True, padx=30, pady=10)

        self.refresh()

    def refresh(self):
        for widget in self.cards_frame.winfo_children():
            widget.destroy()

        stats = get_dashboard_stats()

        cards = [
            ("🚙 Total Vehicles",       stats["total_vehicles"],         "#4a90d9"),
            ("✅ Available",             stats["available_vehicles"],      "#27ae60"),
            ("🔑 Rented",               stats["rented_vehicles"],         "#e67e22"),
            ("📅 Reserved",             stats["reserved_vehicles"],       "#8e44ad"),
            ("🔧 Maintenance",          stats["maintenance_vehicles"],    "#e74c3c"),
            ("👥 Customers",            stats["total_customers"],         "#2980b9"),
            ("📋 Active Rentals",       stats["active_rentals"],          "#16a085"),
            ("🗓 Pending Reservations", stats["pending_reservations"],    "#d35400"),
            ("💵 Total Revenue",        f"${stats['total_revenue']:,.2f}", "#1abc9c"),
        ]

        cols = 3
        for i, (label, value, color) in enumerate(cards):
            row, col = divmod(i, cols)
            card = tk.Frame(self.cards_frame, bg=color, bd=0, relief="flat",
                            padx=20, pady=16)
            card.grid(row=row, column=col, padx=12, pady=12, sticky="nsew")

            tk.Label(card, text=str(value), font=("Helvetica", 26, "bold"),
                     bg=color, fg="white").pack()
            tk.Label(card, text=label, font=("Helvetica", 11),
                     bg=color, fg="#dddddd").pack()

        for c in range(cols):
            self.cards_frame.columnconfigure(c, weight=1)
